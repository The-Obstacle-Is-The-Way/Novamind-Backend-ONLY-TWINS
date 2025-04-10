"""
Global test fixtures and configurations for pytest.

This module provides test fixtures that are available to all test modules.
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variable
os.environ["TESTING"] = "1"

# Import DB dependencies after setting testing environment
from app.core.db import Base, get_session
from app.domain.entities.base import BaseEntity
from app.infrastructure.repositories.base import BaseRepository
from app.tests.fixtures.mock_db_fixture import MockAsyncSession


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sqlite_test_db_url() -> str:
    """Get a SQLite database URL for testing."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def test_engine(sqlite_test_db_url):
    """Create a test SQLAlchemy engine using SQLite."""
    engine = create_async_engine(
        sqlite_test_db_url,
        echo=False,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a test database session.
    
    This fixture provides an actual SQLite database session for integration tests
    that need to test real database operations.
    """
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        # Roll back all changes
        await session.rollback()


@pytest.fixture
def mock_db() -> MockAsyncSession:
    """
    Get a mock database session.
    
    This fixture provides a mocked SQLAlchemy session for unit tests,
    to avoid database connections and speed up testing.
    """
    return MockAsyncSession()


@pytest.fixture
def test_entity() -> BaseEntity:
    """Provide a base test entity for testing."""
    return BaseEntity()


@pytest.fixture
def test_repository(mock_db) -> BaseRepository:
    """Provide a base repository with a mock session for testing."""
    return BaseRepository(session=mock_db)


# Override the real session dependency with test session
@pytest.fixture
def override_get_session(test_db):
    """Override the get_session dependency for FastAPI testing."""
    async def _get_session():
        yield test_db
    
    return _get_session