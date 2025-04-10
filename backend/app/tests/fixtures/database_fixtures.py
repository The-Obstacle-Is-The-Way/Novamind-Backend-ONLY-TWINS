"""
Database fixtures for tests.

This module provides pytest fixtures for setting up and tearing down 
a test database environment, ensuring proper isolation between tests.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Any, Dict, List
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.infrastructure.persistence.sqlalchemy.models.base import Base
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_instance

# Test database URL from environment
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
)

# Create an async engine for the test database
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool  # Disable connection pooling for tests
)

# Create a sessionmaker for tests
AsyncTestSessionLocal = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False, 
    autocommit=False, 
    autoflush=False
)


@asynccontextmanager
async def get_test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async with AsyncTestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_test_db() -> None:
    """Create all tables in the test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def cleanup_test_db() -> None:
    """Drop all tables from the test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db(event_loop) -> None:
    """Set up the test database."""
    await init_test_db()
    yield
    await cleanup_test_db()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for a test.
    
    This fixture provides an isolated database session for each test,
    with automatic rollback to ensure test isolation.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    # Create a session with the transaction
    async_session = sessionmaker(
        connection, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    session = async_session()
    
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture(scope="function")
async def test_db_instance(db_session) -> Any:
    """
    Provide a database instance with the test session.
    
    This helps tests that need the database instance rather than a raw session.
    """
    db_instance = get_db_instance()
    # Replace the session factory with our test session
    original_session = db_instance.session
    db_instance.session = lambda: db_session
    
    yield db_instance
    
    # Restore the original session factory
    db_instance.session = original_session