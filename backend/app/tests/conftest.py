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
import uuid
import time
from typing import Dict, Any, Callable
from app.infrastructure.security.jwt.jwt_service import JWTService
from dotenv import load_dotenv
from app.domain.entities.patient import Patient

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
        self.STATIC_DIR = Path(__file__).parent.parent / "static" # Adjust static/template paths relative to conftest location
        self.TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
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
    # Ensure app.config.settings is also mocked if it exists and is used directly
    sys.modules['app.config.settings'] = MagicMock(get_settings=lambda: settings, settings=settings)
    # Also mock app.core.config if that path is used
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
    Handles sys.path adjustment and marker registration.
    """
    # --- Add backend directory to sys.path --- 
    conftest_path = Path(__file__).resolve()
    backend_dir = conftest_path.parent.parent.parent 
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
        # Use print to stderr for reliable logging during early configuration
        print(f"[pytest_configure] Added to sys.path: {str(backend_dir)}", file=sys.stderr)
    # --- End sys.path modification ---

    # --- Register custom markers --- 
    # Core dependency markers
    config.addinivalue_line("markers", "standalone: Tests that have no external dependencies")
    config.addinivalue_line("markers", "venv_only: Tests that require Python packages but no external services")
    config.addinivalue_line("markers", "db_required: Tests that require database connections")
    
    # Additional classification markers
    config.addinivalue_line("markers", "network_required: Tests that require network connections")
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")
    config.addinivalue_line("markers", "security: Security-related tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    
    # Domain-specific markers
    config.addinivalue_line("markers", "ml: Machine learning related tests")
    config.addinivalue_line("markers", "phi: Protected Health Information related tests")
    # --- End marker registration ---

    # Apply the import patch (if still needed)
    with patch_imports():
        pass

# --- Session Setup Fixtures ---

@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load environment variables from .env.test before the test session starts."""
    # Assume .env.test is in the backend directory (parent of app/tests/)
    backend_dir = Path(__file__).parent.parent.parent
    dotenv_path = backend_dir / '.env.test'
    if dotenv_path.exists():
        # Load .env.test, overriding existing environment variables
        load_dotenv(dotenv_path=dotenv_path, override=True)
        logger = logging.getLogger(__name__)
        logger.info(f"[Session Setup] Loaded test environment variables from: {dotenv_path}")
    else:
        logger = logging.getLogger(__name__)
        logger.warning(f"[Session Setup] .env.test file not found at: {dotenv_path}")

@pytest.fixture(scope="session") # Removed autouse=True, handled by client fixture dependency
def test_environment(load_test_env): # Depends on env vars being loaded
    """Set specific test environment variables (can override .env.test)."""
    # These are set explicitly *after* .env.test is loaded
    os.environ["TESTING"] = "1"
    os.environ["ENVIRONMENT"] = "test"
    logger = logging.getLogger(__name__)
    logger.info("[Session Setup] TESTING=1 and ENVIRONMENT=test set.")
    yield
    # Teardown (optional, usually not needed for these vars)
    # os.environ.pop("TESTING", None)

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

# JWT Service Fixture
@pytest.fixture(scope="session")
def jwt_service(mock_settings: MockSettings) -> JWTService:
    """Provides a JWTService instance configured with the test secret key."""
    # Access the key correctly from the nested structure
    secret_key = mock_settings.security.JWT_SECRET_KEY
    if not secret_key:
        raise ValueError("Test JWT_SECRET_KEY is not set in MockSettings")
    return JWTService(secret_key=secret_key)

# Token Generation Fixture
@pytest.fixture(scope="function")
def generate_token(jwt_service: JWTService) -> Callable[[Dict[str, Any]], str]:
    """Provides an async function to generate JWT tokens for given payloads."""
    async def _generate(payload: Dict[str, Any]) -> str:
        # Ensure payload has essential claims like 'sub' and 'exp'
        if 'sub' not in payload:
            payload['sub'] = payload.get('id') or payload.get('username', str(uuid.uuid4()))
        if 'exp' not in payload:
            # Set a default expiration (e.g., 1 hour) for tests
            payload['exp'] = int(time.time()) + 3600
            
        token = await jwt_service.create_token(payload)
        return token
    return _generate

# User Payload Fixtures
@pytest.fixture(scope="function")
def mock_patient_payload() -> Dict[str, Any]:
    """Provides a sample patient user payload."""
    user_id = str(uuid.uuid4())
    return {
        "id": user_id,
        "username": f"test_patient_{user_id[:8]}",
        "role": "patient",
        "full_name": "Test Patient User"
        # 'sub' and 'exp' will be added by generate_token if missing
    }

@pytest.fixture(scope="function")
def mock_provider_payload() -> Dict[str, Any]:
    """Provides a sample provider user payload."""
    user_id = str(uuid.uuid4())
    return {
        "id": user_id,
        "username": f"test_provider_{user_id[:8]}",
        "role": "provider", # Use 'provider' based on auth checks
        "full_name": "Test Provider User"
        # 'sub' and 'exp' will be added by generate_token if missing
    }

# Token Header Fixtures (Using asyncio.run)
@pytest.fixture(scope="function")
def patient_token_headers(generate_token: Callable[[Dict[str, Any]], str], mock_patient_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates valid Authorization headers for a mock patient."""
    # Fixtures are synchronous, but generate_token returns an async function
    # We need to run the async function to get the token
    token = asyncio.run(generate_token(mock_patient_payload))
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def provider_token_headers(generate_token: Callable[[Dict[str, Any]], str], mock_provider_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates valid Authorization headers for a mock provider."""
    token = asyncio.run(generate_token(mock_provider_payload))
    return {"Authorization": f"Bearer {token}"}

# Add test_patient fixture
@pytest.fixture
def test_patient() -> Patient:
    """Provides a sample Patient domain object for testing."""
    # Make sure necessary fields are included based on Patient entity definition
    return Patient(
        id=str(uuid.uuid4()),
        first_name="TestPHI",
        last_name="Patient",
        date_of_birth="1990-01-01", # Example DOB
        gender="Other", # Example Gender
        # Add other required fields from Patient entity with valid test values
        # email="test.phi.patient@example.com", 
        # phone_number="555-0199",
        # address={ # Example address dict
        #     "street": "123 PHI Lane", 
        #     "city": "Testville", 
        #     "state": "TS", 
        #     "zip_code": "98765"
        # }
    )
