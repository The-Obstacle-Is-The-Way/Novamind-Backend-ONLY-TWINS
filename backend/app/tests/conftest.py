"""
Global pytest configuration and fixtures.

This module sets up global fixtures and configuration for all tests.
It also handles patching of problematic imports during test collection.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Add the app directory to the path
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Try to import our patching utility
try:
    from app.tests.helpers.patch_imports import patch_imports
except ImportError:
    # Use a dummy context manager if the import fails
    from contextlib import contextmanager

    @contextmanager
    def patch_imports():
        yield

# Mock the settings object
class MockSettings:
    def __init__(self):
        self.APP_NAME = "Novamind Test"
        self.APP_VERSION = "test-1.0.0"
        self.ENVIRONMENT = "test"
        self.DEBUG = True
        self.PROJECT_NAME = "Novamind Test"
        self.APP_DESCRIPTION = "Test environment for Novamind"
        self.VERSION = "test-1.0.0"
        self.BACKEND_CORS_ORIGINS = ["*"]
        self.API_V1_STR = "/api/v1"
        self.STATIC_DIR = app_dir / "static"
        self.TEMPLATES_DIR = app_dir / "templates"
        self.SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///./test.db"
        self.LOG_LEVEL = "DEBUG"
        self.ENABLE_ANALYTICS = False
        # API settings
        self.api = MagicMock(
            CORS_ORIGINS=["*"],
            ALLOWED_HOSTS=["*"],
            HOST="localhost",
            PORT=8000,
            API_V1_PREFIX="/api/v1"
        )
        # Security settings
        self.security = MagicMock(
            JWT_SECRET_KEY="test-secret-key",
            ENFORCE_HTTPS=False,
            SSL_KEY_PATH=None,
            SSL_CERT_PATH=None
        )
        # Logging settings
        self.logging = MagicMock(
            LOG_LEVEL="DEBUG"
        )

    def is_production(self):
        return False

# Provide mocked settings as a fixture
@pytest.fixture(scope="session", autouse=True)
def mock_settings():
    settings = MockSettings()
    # Mock get_settings to return our mock object
    sys.modules['app.core.config'] = MagicMock(get_settings=lambda: settings, settings=settings)
    return settings

# Use the patch_imports context manager during collection
def pytest_collection_modifyitems(config, items):
    """
    Pytest hook that runs after test collection but before test execution.

    We use this hook to patch problematic imports during test collection.
    """
    pass  # The patching is already done by pytest_configure


def pytest_configure(config):
    """
    Pytest hook that runs before test collection.

    We use this hook to patch problematic imports before any tests are imported.
    """
    # Apply the import patch
    with patch_imports():
        # This context manager will be active during the configure phase
        # which happens before collection
        pass


def pytest_sessionstart(session):
    """Set up the pytest session."""
    # Define custom markers
    config = session.config
    config.addinivalue_line(
        "markers",
        "ml: Mark test as a machine learning test")
    config.addinivalue_line("markers", "phi: Mark test as a PHI-related test")
    config.addinivalue_line(
        "markers",
        "integration: Mark test as integration test")
    config.addinivalue_line("markers", "unit: Mark test as unit test")
    config.addinivalue_line("markers", "security: Mark test as security test")
    config.addinivalue_line("markers", "api: Mark test as API test")

    # Define fixtures that can be shared across tests


@pytest.fixture(scope="session")
def test_environment():
    """Set up the test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["ENVIRONMENT"] = "test"
    yield
    os.environ.pop("TESTING", None)
    # Don't remove ENVIRONMENT as it might be set by the system
