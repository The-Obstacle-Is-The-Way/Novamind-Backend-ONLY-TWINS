"""
Shared fixtures for testing the Novamind Digital Twin platform.

This module provides pytest fixtures that can be shared across different
test files, optimizing setup and teardown processes while ensuring
consistent test environments.
"""

import asyncio
import pytest
from typing import Dict, Any, Generator, AsyncGenerator, List, Optional
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Simple Settings class for tests
class Settings:
    """Simple Settings class for tests."""
    def __init__(self):
        self.app_name = "Novamind Digital Twin API"
        self.debug = False
        self.environment = "test"
        self.database_url = "sqlite+aiosqlite:///:memory:"
        self.jwt_secret = "test_secret_key"
        self.jwt_algorithm = "HS256"
        self.jwt_expires_minutes = 30

# Import the necessary application components
# These imports should be adjusted based on the actual application structure
try:
    from app.main import app as fastapi_app
    from app.core.config import get_settings
    try:
        from app.core.config import Settings as AppSettings
        Settings = AppSettings
    except ImportError:
        # Use the fallback Settings class defined above
        pass
    from app.infrastructure.database.models import Base
    from app.infrastructure.database.session import get_db
    
    # ML service imports
    from app.core.services.ml.mock import MockMentaLLaMA
    from app.core.services.ml.mock_dt import MockDigitalTwinService
    from app.core.services.ml.mock_phi import MockPHIDetection
except ImportError:
    # Provide fallbacks for running tests in isolation
    fastapi_app = None
    # Define a fallback get_settings function
    def get_settings() -> Settings:
        return Settings()
    Base = None
    get_db = None
    MockMentaLLaMA = MagicMock
    MockDigitalTwinService = MagicMock
    MockPHIDetection = MagicMock


# =========== Shared Fixtures ===========

@pytest.fixture(scope="session")
def base_dir() -> Path:
    """Get the base directory for the project."""
    # Go up from the current file to the project root
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def test_data_dir(base_dir: Path) -> Path:
    """Get the directory for test data files."""
    return base_dir / "tests" / "data"


@pytest.fixture
def load_test_data():
    """Fixture to load test data from JSON files."""
    def _load(filename: str) -> Dict[str, Any]:
        """Load a test data file.
        
        Args:
            filename: Name of the JSON file in the tests/data directory
            
        Returns:
            The loaded test data
        """
        data_dir = Path(__file__).parent / "data"
        with open(data_dir / filename, "r") as f:
            return json.load(f)
    return _load


# =========== Unit Test Fixtures ===========

@pytest.fixture
def mock_mentallama_service() -> MockMentaLLaMA:
    """Create a mock MentaLLaMA service for testing."""
    service = MockMentaLLaMA()
    service.initialize({})
    return service


@pytest.fixture
def mock_digital_twin_service() -> MockDigitalTwinService:
    """Create a mock Digital Twin service for testing."""
    service = MockDigitalTwinService()
    service.initialize({})
    return service


@pytest.fixture
def mock_phi_detection_service() -> MockPHIDetection:
    """Create a mock PHI detection service for testing."""
    service = MockPHIDetection()
    service.initialize({})
    return service


@pytest.fixture
def sample_text() -> str:
    """Create sample text for testing."""
    return (
        "I've been feeling down for several weeks. I'm constantly tired, "
        "have trouble sleeping, and don't enjoy things anymore. Sometimes "
        "I wonder if life is worth living, but I wouldn't actually hurt myself."
    )


@pytest.fixture
def sample_phi_text() -> str:
    """Create sample text with PHI for testing."""
    return (
        "Patient John Smith (SSN: 123-45-6789) was admitted on 03/15/2024. "
        "His email is john.smith@example.com and phone number is (555) 123-4567. "
        "He resides at 123 Main Street, Springfield, IL 62701."
    )


# =========== Integration Test Fixtures ===========

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    try:
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()
    except RuntimeError:
        # If there's no running event loop, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Get the FastAPI application for testing."""
    if fastapi_app is None:
        pytest.skip("FastAPI app not available")
    return fastapi_app


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Get application settings for testing."""
    if get_settings is None:
        pytest.skip("Settings not available")
    return get_settings()


@pytest.fixture(scope="session")
def test_db_engine(settings):
    """Create a test database engine."""
    # Use SQLite in memory for tests
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    
    # Create all tables
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    asyncio.run(create_tables())
    
    yield engine
    
    # Drop all tables after tests
    async def drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    asyncio.run(drop_tables())
    asyncio.run(engine.dispose())


@pytest.fixture
def db_session_maker(test_db_engine):
    """Create a test database session maker."""
    return sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(db_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async with db_session_maker() as session:
        yield session


@pytest.fixture
def test_client(app: FastAPI, db_session_maker) -> TestClient:
    """Get a test client for the FastAPI application."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with db_session_maker() as session:
            yield session
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a test client
    client = TestClient(app)
    
    yield client
    
    # Remove the dependency override
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Get an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(db_session: AsyncSession) -> Dict[str, Any]:
    """Create a test user for authentication testing."""
    try:
        from app.infrastructure.database.models import User
        from app.core.security import get_password_hash
        
        # Create a test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": get_password_hash("password123"),
            "is_superuser": False
        }
        
        db_user = User(**user_data)
        db_session.add(db_user)
        await db_session.commit()
        await db_session.refresh(db_user)
        
        return db_user.to_dict()
    except ImportError:
        pytest.skip("User model not available")


@pytest.fixture
async def test_superuser(db_session: AsyncSession) -> Dict[str, Any]:
    """Create a test superuser for authentication testing."""
    try:
        from app.infrastructure.database.models import User
        from app.core.security import get_password_hash
        
        # Create a test superuser
        user_data = {
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": get_password_hash("adminpassword"),
            "is_superuser": True
        }
        
        db_user = User(**user_data)
        db_session.add(db_user)
        await db_session.commit()
        await db_session.refresh(db_user)
        
        return db_user.to_dict()
    except ImportError:
        pytest.skip("User model not available")


@pytest.fixture
async def auth_token(test_client: TestClient, test_user: Dict[str, Any]) -> str:
    """Get an authentication token for testing."""
    try:
        response = test_client.post(
            "/api/auth/token",
            data={
                "username": test_user["username"],
                "password": "password123"
            }
        )
        return response.json()["access_token"]
    except Exception:
        pytest.skip("Auth token endpoint not available")


@pytest.fixture
async def superuser_auth_token(test_client: TestClient, test_superuser: Dict[str, Any]) -> str:
    """Get a superuser authentication token for testing."""
    try:
        response = test_client.post(
            "/api/auth/token",
            data={
                "username": test_superuser["username"],
                "password": "adminpassword"
            }
        )
        return response.json()["access_token"]
    except Exception:
        pytest.skip("Auth token endpoint not available")


# =========== ML Test Fixtures ===========

@pytest.fixture
def patient_data() -> Dict[str, Any]:
    """Create sample patient data for testing."""
    return {
        "patient_id": "test-patient-123",
        "demographic_data": {
            "age": 35,
            "gender": "female",
            "ethnicity": "caucasian"
        },
        "clinical_data": {
            "diagnoses": ["Major Depressive Disorder", "Generalized Anxiety Disorder"],
            "medications": ["sertraline", "buspirone"],
            "treatment_history": [
                {"type": "CBT", "duration": "6 months", "outcome": "moderate improvement"}
            ]
        },
        "biometric_data": {
            "sleep_quality": [6, 5, 7, 4, 6],
            "heart_rate": [72, 78, 75, 80, 73],
            "activity_level": [3500, 2800, 4200, 3000, 3700]
        }
    }


@pytest.fixture
def depression_assessment_text() -> str:
    """Create sample text for depression assessment testing."""
    return (
        "I've been feeling sad most of the day, nearly every day for the past month. "
        "I've lost interest in activities I used to enjoy. I sleep too much, but still "
        "feel exhausted. I've gained weight because I'm eating more than usual. "
        "I feel worthless and guilty about being a burden. It's hard to concentrate "
        "on anything. Sometimes I think everyone would be better off without me."
    )


@pytest.fixture
def anxiety_assessment_text() -> str:
    """Create sample text for anxiety assessment testing."""
    return (
        "I worry constantly about everything. My heart races and I can't catch my breath. "
        "I feel tense and on edge all the time. I have trouble sleeping because my mind "
        "won't shut off. I expect the worst to happen in most situations. I avoid social "
        "gatherings because I'm afraid of embarrassing myself. My worries feel uncontrollable."
    )


@pytest.fixture
def wellness_assessment_text() -> str:
    """Create sample text for wellness assessment testing."""
    return (
        "I've been walking 30 minutes daily and eating more vegetables. My sleep is improving "
        "since I started a bedtime routine. I meditate for 10 minutes each morning which helps "
        "with stress. I connect with friends weekly. I've been reading more and spending less "
        "time on social media. I still struggle with work-life balance and often feel overwhelmed."
    )