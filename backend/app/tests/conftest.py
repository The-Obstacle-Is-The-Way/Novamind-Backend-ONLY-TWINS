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