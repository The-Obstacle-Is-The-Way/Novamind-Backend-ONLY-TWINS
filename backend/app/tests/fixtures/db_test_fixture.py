"""
Unified Database Test Fixtures

This module provides a complete set of pytest fixtures and utilities for
database testing, combining transaction management, dependency injection,
and test data generation capabilities into a single cohesive module.
"""

import os
import pytest
import pytest_asyncio
import asyncio
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator, Generator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.infrastructure.persistence.sqlalchemy.models.base import Base
from app.core.config import get_test_settings
from app.core.db import get_session


# Test database URL from environment or default to a test PostgreSQL DB
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
)

# Create a test engine with appropriate settings
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"server_settings": {"jit": "off"}}  # Disable JIT for tests
)

# Create a session factory for tests
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

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
        async def db_session(
                setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for a test.

    This fixture creates a new database session for each test
    and rolls back all changes when the test is complete.
    """
    # Connect to the database
    connection = await test_engine.connect()
    transaction = await connection.begin()

    # Create a session with the transaction
    session = TestSessionLocal()

    try:
        yield session
        finally:
            # Roll back any changes and close the session when the test is done
        await session.rollback()
        await session.close()
        await transaction.rollback()
        await connection.close()

        @pytest_asyncio.fixture
        async def db_transaction(
                db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with nested transaction rollback.

    This fixture allows for more granular transaction control within tests.
    """
    # Start a nested transaction
    transaction = await db_session.begin_nested()

    # Yield the session
    yield db_session

    # Rollback the transaction
    await transaction.rollback()

    @pytest_asyncio.fixture
    async def override_get_session(
            db_session: AsyncSession) -> AsyncGenerator[Callable, None]:
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
            def override_db_dependencies(
                    app, db_session: AsyncSession) -> None:
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
            async def clear_tables(
                    db_session: AsyncSession) -> AsyncGenerator[None, None]:
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

        async def seed_test_data(
                session: AsyncSession, fixture_data: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Seed test database with fixture data.

    Args:
        session: Database session
        fixture_data: Dictionary of table names to lists of row data
        """
    for table_name, rows in fixture_data.items():
        if not rows:
            continue

            # Create INSERT statement
            columns = ", ".join(rows[0].keys())
            placeholders = ", ".join(f":{col}" for col in rows[0].keys())

            # Insert each row
            for row in rows:
            query = text(
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})")
            await session.execute(query, row)

            # Commit changes
            await session.commit()

            class TestDataFactory:
    """Factory for generating test data for different domain entities."""

    @staticmethod
    def create_patient_data(count: int = 1) -> List[Dict[str, Any]]:
        """Create test patient data."""
        patients = []
        for i in range(1, count + 1):
            patients.append({
                "id": f"test-patient-{i}",
                "first_name": f"Test{i}",
                "last_name": f"Patient{i}",
                "date_of_birth": "1990-01-01",
                "gender": "other",
                "email": f"test{i}@example.com",
                "phone": f"555-000-{i:04d}",
                "address": f"123 Test St, Unit {i}, Testville, TS 12345",
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            })
            return patients

            @staticmethod
            def create_clinician_data(count: int = 1) -> List[Dict[str, Any]]:
        """Create test clinician data."""
        clinicians = []
        for i in range(1, count + 1):
            clinicians.append({
                "id": f"test-clinician-{i}",
                "first_name": f"Doctor{i}",
                "last_name": f"Test{i}",
                "title": "MD",
                "specialty": "Psychiatry",
                "email": f"doctor{i}@example.com",
                "phone": f"555-111-{i:04d}",
                "license_number": f"TEST-LIC-{i:04d}",
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            })
            return clinicians

            @staticmethod
            def create_user_data(count: int = 1) -> List[Dict[str, Any]]:
        """Create test user data."""
        users = []
        for i in range(1, count + 1):
            users.append({
                "id": f"test-user-{i}",
                "username": f"testuser{i}",
                "email": f"user{i}@example.com",
                "hashed_password": "hashed_test_password",
                "is_active": True,
                "role": "user" if i % 3 != 0 else "admin",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            })
            return users

            # Context manager for transaction-based testing

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
