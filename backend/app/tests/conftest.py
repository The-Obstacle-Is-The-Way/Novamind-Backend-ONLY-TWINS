"""
Test Configuration for Novamind Digital Twin Platform.

This module provides pytest fixtures for testing both unit and integration tests.
It includes configurations for both standalone testing and database-dependent testing.
"""
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.tests.fixtures.mock_db_fixture import MockAsyncSession


# Determine if we're in test mode and what type of tests we're running
is_test_mode = os.environ.get("TESTING") == "1"
test_type = os.environ.get("TEST_TYPE", "unit")  # 'unit' or 'integration'


# Create different database configurations based on test type
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture for database session in tests.
    
    This fixture provides different session implementations based on test type:
    - For unit tests: Returns a MockAsyncSession
    - For integration tests: Returns a real AsyncSession with in-memory SQLite
    
    Yields:
        AsyncSession: Database session for testing
    """
    if test_type == "unit":
        # For unit tests, use a mock session
        mock_session = MockAsyncSession()
        yield mock_session
    else:
        # For integration tests, use an actual in-memory database
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True,
        )
        
        # Create tables if needed (would need to import metadata from models)
        # async with engine.begin() as conn:
        #     await conn.run_sync(Base.metadata.create_all)
        
        # Create session factory
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        # Create and yield session
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
        
        # Clean up (drop tables)
        # async with engine.begin() as conn:
        #     await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_user() -> Dict[str, Any]:
    """
    Fixture that provides a test user for authentication testing.
    
    Returns:
        Dict[str, Any]: A dictionary representing a test user
    """
    return {
        "id": "test-user-id-12345",
        "username": "test_user",
        "email": "test_user@example.com",
        "roles": ["user"]
    }


@pytest.fixture
def admin_user() -> Dict[str, Any]:
    """
    Fixture that provides an admin user for authorization testing.
    
    Returns:
        Dict[str, Any]: A dictionary representing an admin user
    """
    return {
        "id": "admin-user-id-67890",
        "username": "admin_user",
        "email": "admin@example.com",
        "roles": ["admin", "user"]
    }


@pytest.fixture
def clinician_user() -> Dict[str, Any]:
    """
    Fixture that provides a clinician user for authorization testing.
    
    Returns:
        Dict[str, Any]: A dictionary representing a clinician user
    """
    return {
        "id": "clinician-user-id-54321",
        "username": "clinician_user",
        "email": "clinician@example.com",
        "roles": ["clinician", "user"]
    }


@pytest.fixture
def mock_auth_service() -> MagicMock:
    """
    Fixture that provides a mock authentication service.
    
    Returns:
        MagicMock: A configured mock authentication service
    """
    mock = MagicMock()
    mock.authenticate.return_value = True
    mock.get_user_by_id.return_value = {
        "id": "test-user-id-12345",
        "username": "test_user",
        "email": "test_user@example.com",
        "roles": ["user"]
    }
    return mock