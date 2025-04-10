"""
Pytest fixtures for the Novamind Digital Twin Backend.

This module provides fixtures that can be used across all test modules,
organized by dependency level.
"""
import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

# SQLAlchemy imports for DB fixtures
try:
    from sqlalchemy import event, text
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    # These imports might fail in standalone test environment
    pass


# Constants
BACKEND_DIR = Path(__file__).parent.parent.parent
TEST_DIR = BACKEND_DIR / "app" / "tests"


# ===============================================================
# STANDALONE FIXTURES (no external dependencies)
# ===============================================================

@pytest.fixture
def sample_data() -> dict[str, Any]:
    """
    Provide sample test data that doesn't require any external dependencies.
    
    This fixture is usable by standalone tests.
    """
    return {
        "id": "test-id-12345",
        "name": "Test Name",
        "value": 42,
        "date": datetime.now().isoformat(),
        "attributes": ["attr1", "attr2", "attr3"],
        "metadata": {
            "created_by": "test",
            "version": "1.0.0"
        }
    }


# ===============================================================
# VENV-DEPENDENT FIXTURES (require Python packages but no external services)
# ===============================================================

@pytest.fixture
def mock_logger():
    """
    Provide a mock logger for testing.
    
    This fixture is usable by venv-dependent tests.
    """
    class MockLogger:
        def __init__(self):
            self.logs = {
                "debug": [],
                "info": [],
                "warning": [],
                "error": [],
                "critical": []
            }
            
        def debug(self, msg, *args, **kwargs):
            self.logs["debug"].append(msg)
            
        def info(self, msg, *args, **kwargs):
            self.logs["info"].append(msg)
            
        def warning(self, msg, *args, **kwargs):
            self.logs["warning"].append(msg)
            
        def error(self, msg, *args, **kwargs):
            self.logs["error"].append(msg)
            
        def critical(self, msg, *args, **kwargs):
            self.logs["critical"].append(msg)
            
        def reset(self):
            for level in self.logs:
                self.logs[level] = []
    
    return MockLogger()


# ===============================================================
# DB-DEPENDENT FIXTURES (require database connections)
# ===============================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.
    
    This is required for async tests using pytest-asyncio.
    """
    try:
        loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()
    except ImportError:
        # Skip in standalone environment
        yield None


@pytest.fixture(scope="session")
async def db_engine() -> AsyncEngine | None:
    """
    Create a database engine for testing.
    
    This fixture is only usable by db-dependent tests.
    """
    try:
        # Get test database URL from environment or use default
        db_url = os.environ.get(
            "TEST_DATABASE_URL", 
            "postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
        )
        
        # Create engine
        engine = create_async_engine(
            db_url,
            echo=False,
            future=True
        )
        
        yield engine
        
        # Close engine
        await engine.dispose()
    except (ImportError, NameError):
        # Skip in standalone environment
        yield None


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession | None, None]:
    """
    Create a database session for testing.
    
    This fixture is only usable by db-dependent tests.
    """
    if db_engine is None:
        # Skip in standalone environment
        yield None
        return
        
    try:
        # Create session
        async_session = sessionmaker(
            db_engine, 
            expire_on_commit=False, 
            class_=AsyncSession
        )
        
        async with async_session() as session:
            # Start transaction
            async with session.begin():
                # Create all tables - this assumes models are imported
                # and metadata is available
                from app.infrastructure.persistence.sqlalchemy.models.patient import metadata
                async with db_engine.begin() as conn:
                    await conn.run_sync(metadata.create_all)
                
                yield session
                
                # Rollback transaction
                await session.rollback()
                
                # Clean up tables
                async with db_engine.begin() as conn:
                    await conn.run_sync(metadata.drop_all)
    except (ImportError, NameError):
        # Skip in standalone environment
        yield None


@pytest.fixture
async def redis_client():
    """
    Create a Redis client for testing.
    
    This fixture is only usable by db-dependent tests.
    """
    try:
        import redis.asyncio as redis
        
        # Get test Redis URL from environment or use default
        redis_url = os.environ.get(
            "TEST_REDIS_URL", 
            "redis://localhost:16379/0"
        )
        
        # Create client
        client = redis.from_url(redis_url)
        
        # Clear database
        await client.flushdb()
        
        yield client
        
        # Clear database and close
        await client.flushdb()
        await client.close()
    except ImportError:
        # Skip in standalone environment
        yield None

# ===============================================================
# API / APP FIXTURES (require FastAPI app instance)
# ===============================================================

# Keep necessary imports here
try:
    from fastapi import FastAPI, Depends
    from fastapi.testclient import TestClient
    # sqlalchemy.ext.asyncio.AsyncSession is needed for override_get_db type hint
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    FastAPI = None
    TestClient = None
    AsyncSession = None
    Depends = None # Add placeholder for Depends if FastAPI fails

# Define placeholders for potentially missing imports (used in override_get_db and app fixture)
# These will be populated *inside* the app fixture if imports succeed there
_main_app_module = None
_get_db_module = None
# Removed duplicate/incorrectly indented placeholders

# Define the override function for the database dependency
# Ensure db_session fixture is defined before this
async def override_get_db(session: AsyncSession = Depends(db_session)) -> AsyncGenerator[AsyncSession, None]:
    """Override for get_db that uses the test session fixture."""
    if session is None:
        pytest.skip("Database session not available for this test environment.")
    yield session



@pytest.fixture(scope="session")
def app(event_loop) -> FastAPI | None:
    """
    Create a FastAPI app instance for the test session with dependency overrides.
    Import the app and apply overrides *inside* the fixture.
    """
    # --- Move imports inside the fixture ---
    global _main_app_module, _get_db_module # Use internal placeholders
    try:
        # Import the main app instance HERE
        from app.main import app as _main_app_module
        # Import the production get_db dependency HERE
        from app.presentation.api.dependencies.database import get_db as _get_db_module
    except ImportError:
        pytest.skip("FastAPI or DB dependencies not available for app fixture.")
        return None
    # --- End moved imports ---

    if _main_app_module is None or _get_db_module is None or override_get_db is None:
         pytest.skip("FastAPI or DB dependencies not available for app fixture.")
         return None

    # Apply the dependency override BEFORE the app is yielded
    _main_app_module.dependency_overrides[_get_db_module] = override_get_db
    yield _main_app_module # Yield the app instance

    # Clear overrides after the test session finishes with the app
    _main_app_module.dependency_overrides.clear()


# Correct indentation for client fixture
@pytest.fixture()
def client(app: FastAPI) -> TestClient | None:
    """
    Get a TestClient instance for the app.
    """
    if app is None:
        pytest.skip("FastAPI app fixture not available for client fixture.")
        return None # Should not be reached if skipped

    with TestClient(app) as test_client:
        yield test_client