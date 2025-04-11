"""
Integration Test Configuration and Fixtures

This file contains test fixtures for integration tests that require external services
such as databases, API connections, etc.
"""

import pytest
import os
from typing import Generator, Dict, Any


@pytest.fixture
def mock_database() -> Generator[Dict[str, Any], None, None]:
    """
    Provides a mock database connection for integration tests.
    
    This uses a temporary in-memory database to avoid affecting
    production data while still testing database interaction code.
    
    Yields:
        Dict[str, Any]: Mock database connection object
    """
    # Create mock database connection
    mock_db = {
        "connected": True,
        "name": "test_db",
        "collections": {}
    }
    
    # Set up before test
    yield mock_db
    
    # Clean up after test
    mock_db["connected"] = False


@pytest.fixture
def integration_fixture():
    """Fixture for integration tests only."""
    return "integration_fixture"


@pytest.fixture
def mock_api_endpoint():
    """
    Mock API endpoint for testing HTTP interactions.
    """
    return "http://mock-api.novamind-test.local"