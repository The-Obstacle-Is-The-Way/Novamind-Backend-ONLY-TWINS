"""
PyTest configuration for Novamind Digital Twin Platform tests.

This module provides pytest fixtures and configuration for all tests,
including environment variable setup, database fixtures, and authentication
support for test integration.
"""

import os
import sys
import pytest
import pytest_asyncio
import logging
from typing import Dict, Any, Generator, Optional
from unittest import mock
from datetime import datetime, timedelta, UTC
from pathlib import Path
from dotenv import load_dotenv

# Load test environment variables from .env.test file
env_path = Path(__file__).parent.parent.parent / '.env.test'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to direct environment variables if file doesn't exist
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["SECRET_KEY"] = "test-key-long-enough-for-testing-purposes-only"
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:15432/novamind_test"
    os.environ["JWT_SECRET_KEY"] = "test-jwt-key-for-testing-only"

# Import fixtures
pytest_plugins = [
    "app.tests.fixtures.auth_fixtures",
    "app.tests.fixtures.db_fixtures",
]

# Import modules after environment setup
from app.core.services.ml.mock import MockMentaLLaMA, MockPHIDetection
from app.core.services.ml.mock_dt import MockDigitalTwinService
from app.core.utils.phi_sanitizer import PHISanitizer


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """Set up test environment variables and configuration."""
    # This fixture runs automatically at the beginning of the test session
    # Environment variables were already loaded above
    pass


@pytest.fixture(scope="function")
def test_settings():
    """Fixture to provide test settings."""
    from app.core.config import get_test_settings
    return get_test_settings()


@pytest.fixture(scope="function")
def mock_phi_detection():
    """Fixture to provide a mock PHI detection service."""
    service = MockPHIDetection()
    service.initialize({})
    return service


@pytest.fixture(scope="function")
def mock_mentalllama():
    """Fixture to provide a mock MentaLLaMA service."""
    service = MockMentaLLaMA()
    service.initialize({})
    return service


@pytest.fixture(scope="function")
def mock_digital_twin():
    """Fixture to provide a mock Digital Twin service."""
    service = MockDigitalTwinService()
    service.initialize({})
    return service


@pytest.fixture(scope="function")
def sample_patient_data() -> Dict[str, Any]:
    """Fixture to provide sample patient data for tests."""
    return {
        "id": "test-patient-123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1985-05-15",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "address": {
            "street": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701"
        },
        "medical_record_number": "MRN123456",
        "insurance": {
            "provider": "Test Health Insurance",
            "policy_number": "POL987654321",
            "group_number": "GRP12345"
        }
    }


@pytest.fixture(scope="function")
def sample_phi_text() -> str:
    """Fixture to provide sample text containing PHI."""
    return (
        "Patient John Smith (SSN: 123-45-6789) was admitted on 03/15/2024. "
        "His email is john.smith@example.com and phone number is (555) 123-4567. "
        "Patient lives at 123 Main St, Springfield, IL 62701."
    )


@pytest.fixture(scope="function")
def sample_non_phi_text() -> str:
    """Fixture to provide sample text without PHI."""
    return (
        "The patient reported feeling better after the treatment. "
        "Symptoms have decreased in severity and frequency. "
        "Regular exercise and medication adherence are recommended."
    )


@pytest.fixture(scope="function")
def sample_insights_response() -> Dict[str, Any]:
    """Fixture to provide sample patient insights response."""
    return {
        "patient_id": "test-patient-123",
        "generated_at": datetime.now(UTC).isoformat(),
        "insights": [
            {
                "category": "mood",
                "summary": "Patient shows improving mood trends over the past month",
                "confidence": 0.85,
                "data_points": 28,
                "trend": "improving",
                "details": "Morning mood scores increased by 15% on average"
            },
            {
                "category": "sleep",
                "summary": "Sleep quality remains inconsistent with periodic insomnia",
                "confidence": 0.78,
                "data_points": 24,
                "trend": "stable",
                "details": "Average sleep duration: 6.5 hours, with 2-3 disruptions per week"
            }
        ],
        "recommendations": [
            {
                "type": "behavioral",
                "text": "Continue daily mindfulness practice with emphasis on evening routine",
                "priority": "high"
            },
            {
                "type": "clinical",
                "text": "Consider sleep hygiene discussion at next appointment",
                "priority": "medium"
            }
        ]
    }


@pytest.fixture(scope="function")
def sample_forecast_response() -> Dict[str, Any]:
    """Fixture to provide sample symptom forecast response."""
    return {
        "patient_id": "test-patient-123",
        "forecast_days": 30,
        "generated_at": datetime.now(UTC).isoformat(),
        "forecast_points": [
            {
                "date": (datetime.now(UTC) + timedelta(days=i)).strftime("%Y-%m-%d"),
                "symptom": "anxiety",
                "severity": (7.0 - (i * 0.2)),
                "confidence": 0.8 - (i * 0.01)
            } for i in range(10)
        ]
    }


@pytest.fixture(scope="function")
def phi_sanitizer():
    """Fixture to provide PHI sanitizer."""
    return PHISanitizer()


@pytest.fixture(scope="function")
def mock_async_db():
    """
    Fixture to provide a mocked async database session.
    
    This is for tests that need to mock the database but don't use 
    the real database fixtures.
    """
    # Create an async mock session
    mock_session = mock.AsyncMock()
    
    # Mock common SQLAlchemy methods
    mock_session.execute.return_value.scalars.return_value.first.return_value = None
    mock_session.execute.return_value.scalars.return_value.all.return_value = []
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    
    # Return the mock session
    yield mock_session