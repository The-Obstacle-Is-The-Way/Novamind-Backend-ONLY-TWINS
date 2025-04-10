"""
PyTest configuration for Novamind Digital Twin Platform tests.

This module provides pytest fixtures and configuration for all tests,
including environment variable setup, database mocking, and other
test requirements.
"""

import os
import sys
import pytest
import logging
from typing import Dict, Any, Generator
from unittest import mock
from datetime import datetime, timedelta, UTC

# Directly set test environment variables
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["SECRET_KEY"] = "test-key-long-enough-for-testing-purposes-only"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/novamind_test"
os.environ["JWT_SECRET_KEY"] = "test-jwt-key-for-testing-only"

# First patch settings to avoid database connections
settings_patch = mock.patch("app.core.config.settings")
mock_settings = settings_patch.start()
mock_settings.DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/novamind_test"
mock_settings.ENVIRONMENT = "test"
mock_settings.SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/novamind_test"
mock_settings.DEBUG = True

# Import modules after patching
from app.core.services.ml.mock import MockMentaLLaMA, MockPHIDetection
from app.core.services.ml.mock_dt import MockDigitalTwinService


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """Set up test environment variables and configuration."""
    # This fixture runs automatically at the beginning of the test session
    # Environment variables were already set above
    pass


# Mock the database components
db_session_mock = mock.MagicMock()
get_db_mock = mock.MagicMock(return_value=db_session_mock)

# Create a mock Database class instance
mock_db_instance = mock.MagicMock()
mock_db_instance.session.return_value.__enter__.return_value = db_session_mock

# Patch database-related components
db_patcher = mock.patch("app.infrastructure.persistence.sqlalchemy.config.database.get_db_instance", 
                        return_value=mock_db_instance)
db_patcher.start()

# Patch the get_db_session function
session_patcher = mock.patch("app.infrastructure.persistence.sqlalchemy.config.database.get_db_session")
mock_session = session_patcher.start()
mock_session.return_value.__enter__.return_value = db_session_mock


@pytest.fixture(scope="function")
def test_settings():
    """Fixture to provide test settings."""
    return mock_settings


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


# Authentication test fixtures
@pytest.fixture(scope="function")
def test_user_id():
    """Test user ID for authentication fixtures."""
    return "test-user-123"


@pytest.fixture(scope="function")
def test_roles():
    """Test roles for authentication fixtures."""
    return ["clinician", "researcher"]


@pytest.fixture(scope="function")
def db():
    """
    Fixture to provide a mocked database session.
    
    Instead of connecting to a real database, we use a mock that can be
    configured as needed for individual tests.
    """
    # Return the pre-configured mock session
    return db_session_mock


# Mock database session for tests that need it but don't use the db fixture
@pytest.fixture(autouse=True)
def mock_db_session():
    """
    Fixture to mock database session for all tests.
    
    This helps tests that reference the database but don't explicitly use the db fixture.
    """
    with mock.patch("app.infrastructure.persistence.sqlalchemy.config.database.get_db_session") as mock_session:
        # Configure the mock to return itself when entering a context
        mock_session.return_value.__enter__.return_value = mock_session.return_value
        yield mock_session.return_value