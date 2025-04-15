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
from fastapi.testclient import TestClient
from app.main import create_application
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_dependency, Base, Database
from app.config.settings import get_settings
from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI

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


# Add/Replace the client fixture
@pytest.fixture(scope="function") # Use function scope for isolation
def client(mock_settings, test_environment) -> TestClient:
    """
    Create a TestClient instance for testing API endpoints.

    This fixture ensures the application is created *after* settings are mocked
    and uses an isolated in-memory SQLite database for each test function.
    Dependencies:
        - mock_settings: Ensures settings are mocked.
        - test_environment: Ensures ENVIRONMENT=test is set.
    """
    # settings = get_settings() # Already mocked via mock_settings fixture dependency
    settings = mock_settings # Use the fixture directly for clarity

    # --- DIAGNOSTIC LOGGING ---
    logger = logging.getLogger(__name__)
    logger.info("--- [Client Fixture Start] ---")
    logger.info(f"[Client Fixture] ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
    logger.info(f"[Client Fixture] Using settings object: {settings}")
    logger.info(f"[Client Fixture] Settings URI: {settings.SQLALCHEMY_DATABASE_URI}")
    env_uri_override = os.getenv("SQLALCHEMY_DATABASE_URI")
    logger.info(f"[Client Fixture] Env Var Override URI: {env_uri_override}")
    logger.info("[Client Fixture] Instantiating Database...")
    # --- END DIAGNOSTIC LOGGING ---

    # Create a *new* Database instance using the mocked settings for isolation
    # Ensure the URI from settings is used
    test_db = Database(settings=settings)

    # Define an async function to handle DB setup
    async def setup_db():
        async with test_db.engine.begin() as conn:
            # Using run_sync for synchronous execution needed by create_all/drop_all
            await conn.run_sync(Base.metadata.drop_all) # Ensure clean state
            await conn.run_sync(Base.metadata.create_all) # Create tables for this test

    # Run the async setup function synchronously
    asyncio.run(setup_db())

    # Create the app instance *inside* the fixture AFTER settings mock
    # DO NOT assign the lifespan here yet
    app_without_lifespan = create_application()

    # --- Define Custom Test Lifespan ---
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        # Startup: Use the pre-configured test_db for setup
        logger.info("--- [Test Lifespan Start] ---")
        logger.info(f"[Test Lifespan] Using engine: {test_db.engine}")
        async with test_db.engine.begin() as conn:
             await conn.run_sync(Base.metadata.drop_all) 
             await conn.run_sync(Base.metadata.create_all)
        logger.info("--- [Test Lifespan] Database tables created ---")
        yield
        # Shutdown: Use the pre-configured test_db for teardown
        logger.info("--- [Test Lifespan Shutdown] ---")
        await test_db.dispose()
        logger.info("--- [Test Lifespan] Engine disposed ---")

    # Assign the custom lifespan to the app instance *before* TestClient uses it
    app_without_lifespan.router.lifespan_context = test_lifespan
    app = app_without_lifespan # Assign the app with the custom lifespan

    # Override the database session dependency (still useful for tests)
    @asynccontextmanager
    async def override_get_db():
        async with test_db.session() as session:
            yield session

    app.dependency_overrides[get_db_dependency()] = override_get_db

    # --- Prevent asyncpg from using ambient PG vars ---
    pg_vars = ["PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE", "DATABASE_URL"]
    original_pg_vars = {var: os.environ.get(var) for var in pg_vars}
    for var in pg_vars:
        if var in os.environ:
            del os.environ[var]
            logger.info(f"[Client Fixture] Unset environment variable: {var}")
    # --- End PG var prevention ---

    # Create and yield the TestClient
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # --- Restore original PG vars ---
        for var, value in original_pg_vars.items():
            if value is not None:
                os.environ[var] = value
                logger.info(f"[Client Fixture] Restored environment variable: {var}")
            elif var in os.environ:
                # If it wasn't set originally, ensure it remains unset
                del os.environ[var]
        # --- End PG var restoration ---

        # Clean up: Dispose the engine after the test function completes
        # This is now handled by the test_lifespan, so remove the explicit dispose call here.
        # async def dispose_db():
        #     await test_db.dispose()
        # asyncio.run(dispose_db())
