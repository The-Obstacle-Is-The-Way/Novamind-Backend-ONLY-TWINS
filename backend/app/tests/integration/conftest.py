"""
Test fixtures for integration tests.

This file contains pytest fixtures that are available to all integration tests.
These fixtures may connect to external services and databases, and should be
designed to manage test setup/teardown properly to avoid test pollution.
"""

import os
import pytest
import asyncio
from typing import Dict, Generator, Any

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import app-specific modules
from app.main import app
from app.infrastructure.persistence.sqlalchemy.models.base import Base
from app.core.config import get_settings
from app.core.security import create_access_token
from app.api.dependencies import get_db


# ------ Database Fixtures ------ #

@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Get the test database URL from environment or use a default."""
    return os.environ.get(
        "TEST_DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/novamind_test"
    )


@pytest.fixture(scope="session")
def engine(test_database_url: str):
    """Create a SQLAlchemy engine connected to the test database."""
    engine = create_engine(test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a fresh database session for a test."""
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Clean up by dropping all tables
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def async_engine():
    """Create an async SQLAlchemy engine for tests."""
    async_url = os.environ.get(
        "TEST_ASYNC_DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/novamind_test"
    )
    engine = create_async_engine(async_url)
    yield engine


@pytest.fixture
async def async_db_session(async_engine):
    """Create a fresh async database session for a test."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ------ API Testing Fixtures ------ #

@pytest.fixture
def test_client(db_session) -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient fixture."""
    # Override the dependency to use the test db session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


# ------ Authentication Fixtures ------ #

@pytest.fixture
def test_user() -> Dict[str, Any]:
    """Create a test user for authentication."""
    return {
        "id": "6a3e9438-b246-4b0d-9809-fa3d65fda25a",
        "email": "test@example.com",
        "username": "test_user",
        "full_name": "Test User",
        "role": "user",
        "is_active": True,
        "hashed_password": "$2b$12$rZJu5c7CYYYMldIcXTN6qeDLqRTJw0U5LS.9JG7n4YQQzTZyJ0xbu"  # password: 'password'
    }


@pytest.fixture
def test_admin_user() -> Dict[str, Any]:
    """Create a test admin user for authentication."""
    return {
        "id": "7b4f9549-c357-5c1e-0910-gb4e76geb36b",
        "email": "admin@example.com",
        "username": "admin_user",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True,
        "hashed_password": "$2b$12$rZJu5c7CYYYMldIcXTN6qeDLqRTJw0U5LS.9JG7n4YQQzTZyJ0xbu"  # password: 'password'
    }


@pytest.fixture
def token_headers(test_user) -> Dict[str, str]:
    """Generate authentication token headers for a test user."""
    access_token = create_access_token(
        data={"sub": test_user["email"]}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_token_headers(test_admin_user) -> Dict[str, str]:
    """Generate authentication token headers for a test admin user."""
    access_token = create_access_token(
        data={"sub": test_admin_user["email"]}
    )
    return {"Authorization": f"Bearer {access_token}"}


# ------ Data Fixtures ------ #

@pytest.fixture
def test_patients():
    """Create test patient data."""
    return [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "John Doe",
            "date_of_birth": "1990-01-01",
            "medical_record_number": "MRN12345"
        },
        {
            "id": "223e4567-e89b-12d3-a456-426614174001",
            "name": "Jane Smith",
            "date_of_birth": "1985-05-15",
            "medical_record_number": "MRN67890"
        }
    ]


@pytest.fixture
def create_test_patients(db_session, test_patients):
    """Add test patients to the database."""
    from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel
    
    for patient_data in test_patients:
        patient = PatientModel(**patient_data)
        db_session.add(patient)
    
    db_session.commit()


# ------ External Service Mocks ------ #

@pytest.fixture
def mock_external_api(requests_mock):
    """Set up mocks for external APIs."""
    # Example: Mock an external health record system
    requests_mock.get(
        "https://external-ehr-api.example.com/patients/123", 
        json={
            "id": "123",
            "name": "External Patient",
            "records": [
                {"date": "2023-01-15", "diagnosis": "F41.1", "notes": "Anxiety disorder"}
            ]
        }
    )
    return requests_mock


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()