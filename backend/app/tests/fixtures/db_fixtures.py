# -*- coding: utf-8 -*-
"""
Database fixtures for tests.

This module provides pytest fixtures for database-related testing,
ensuring proper database setup, teardown, and transaction management.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional, Callable, Generator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

from app.core.config import get_test_settings
from app.core.db import Base, get_session
from app.core.db.session import create_database_engine

# Get database settings from environment or use defaults
settings = get_test_settings()
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
)

# Create a test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"server_settings": {"jit": "off"}}  # Disable JIT for tests
)

# Create a sessionmaker for test sessions
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest_asyncio.fixture(scope="session")
async def setup_database() -> AsyncGenerator[None, None]:
    """
    Set up the test database once per test session.

    This fixture creates all tables defined in SQLAlchemy models,
    then drops them when the test session is complete.
    """
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Clean up after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Close the engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for a test.

    This fixture creates a new database session for each test 
    and rolls back all changes when the test is complete.
    """
    # Connect to the database
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        # Roll back any changes and close the session when the test is done
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture
async def override_get_session(db_session: AsyncSession) -> AsyncGenerator[Callable, None]:
    """
    Override the get_session dependency for testing.
    
    This fixture ensures that FastAPI endpoints use our test database
    session for dependency injection.
    """
    async def get_test_session():
        try:
            yield db_session
        finally:
            pass
    
    # Return the factory function
    yield get_test_session


@pytest.fixture
def override_db_dependencies(app, db_session: AsyncSession) -> None:
    """
    Override all database-related dependencies in the FastAPI app.
    
    This fixture overrides database dependencies with test versions
    that use our test database session.
    """
    # Store original dependencies
    original_deps = {
        "get_session": get_session
    }
    
    # Create test dependency
    async def get_test_session():
        try:
            yield db_session
        finally:
            pass
    
    # Override dependencies in the app
    app.dependency_overrides[get_session] = get_test_session
    
    yield
    
    # Remove overrides and restore original dependencies
    for dep in original_deps:
        if dep in app.dependency_overrides:
            del app.dependency_overrides[dep]


@pytest_asyncio.fixture
async def clear_tables(db_session: AsyncSession) -> AsyncGenerator[None, None]:
    """
    Clear all data from tables between tests.
    
    This fixture truncates all tables to ensure tests don't affect each other.
    """
    yield
    
    # Get a list of all tables
    table_names = [table.name for table in Base.metadata.sorted_tables]
    
    # Clear all tables after the test
    for table_name in table_names:
        await db_session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
    
    await db_session.commit()


# Transactional fixture for using with nested transactions
class TransactionalTestContext:
    """Context manager for transaction-based testing."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self):
        # Start a nested transaction
        self.transaction = await self.session.begin_nested()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Roll back the nested transaction
        if exc_type is not None:
            await self.transaction.rollback()
        else:
            await self.transaction.commit()


@pytest.fixture
def transactional_test(db_session: AsyncSession) -> Callable:
    """
    Create a function to run tests in a nested transaction.
    
    This can be used within a test to create a savepoint and rollback 
    after a portion of the test is complete.
    """
    def _transactional_test():
        return TransactionalTestContext(db_session)
    
    return _transactional_test