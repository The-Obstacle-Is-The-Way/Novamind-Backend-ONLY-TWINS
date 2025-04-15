"""
Global pytest configuration and fixtures.

This module sets up global fixtures and configuration for all tests.
It also handles patching of problematic imports during test collection.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import create_application # Restore import
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_dependency, Base, Database
from app.config.settings import get_settings
from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI, Request
import uuid
import time
from typing import Dict, Any, Callable, Generator, Coroutine, List, Optional
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload
from app.infrastructure.security.auth.authentication_service import AuthenticationService
from app.presentation.middleware.authentication_middleware import AuthenticationMiddleware
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

        # --- Directly add JWT settings expected by JWTService ---
        self.SECRET_KEY = "test-secret-key-longer-than-32-chars-for-sure" # Direct access
        self.ALGORITHM = "HS256" # Direct access
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Direct access
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7 # Direct access
        # --- End Direct JWT Settings ---

        # API settings (can remain nested if only used elsewhere)
        self.api = MagicMock(
            CORS_ORIGINS=["*"],
            ALLOWED_HOSTS=["*"],
            HOST="localhost",
            PORT=8000,
            API_V1_PREFIX="/api/v1"
        )
        # Security settings (can remain nested, JWT keys duplicated above)
        self.security = MagicMock(
            JWT_SECRET_KEY=self.SECRET_KEY, # Keep nested consistent if needed
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
    logger = logging.getLogger(__name__) # Define logger here
    if dotenv_path.exists():
        # Load .env.test, overriding existing environment variables
        load_dotenv(dotenv_path=dotenv_path, override=True)
        logger.info(f"[Session Setup] Loaded test environment variables from: {dotenv_path}")
    else:
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

# --- Mocks for Authentication in client fixture ---
# These can be simple function-scoped fixtures or defined within client

@pytest.fixture(scope="function")
def mock_jwt_service_for_client(
    mock_settings,
    mock_patient_payload: Dict[str, Any], # Inject patient payload fixture
    mock_provider_payload: Dict[str, Any] # Inject provider payload fixture
) -> JWTService:
    """Provides a mocked JWTService instance for the client fixture."""
    mock_service = AsyncMock(spec=JWTService)

    # Use the injected fixtures directly
    # patient_payload = mock_patient_payload() # Remove direct call
    # provider_payload = mock_provider_payload() # Remove direct call
    patient_payload = mock_patient_payload # Use injected argument
    provider_payload = mock_provider_payload # Use injected argument

    async def async_mock_decode_token(token: str) -> TokenPayload:
        # Map simple token strings to payloads for test simplicity
        # The token strings here MUST match those returned by the mocked create_access_token below
        if token == "patient_token_string":
            return TokenPayload(
                sub=patient_payload['sub'],
                exp=patient_payload['exp'],
                iat=int(time.time()),
                jti=f"jti_{patient_payload['sub']}",
                scope="access_token",
                roles=patient_payload['roles'],
                user_id=patient_payload.get('id', patient_payload['sub'])
            )
        elif token == "provider_token_string":
            return TokenPayload(
                 sub=provider_payload['sub'],
                 exp=provider_payload['exp'],
                 iat=int(time.time()),
                 jti=f"jti_{provider_payload['sub']}",
                 scope="access_token",
                 roles=provider_payload['roles'],
                 user_id=provider_payload.get('id', provider_payload['sub'])
             )
        else:
            from app.domain.exceptions import InvalidTokenError
            raise InvalidTokenError("Mocked invalid token")

    mock_service.decode_token = AsyncMock(side_effect=async_mock_decode_token)

    # Mock create_access_token to return predictable strings used in decode mock
    async def async_mock_create_token(subject: str, roles: Optional[List[str]] = None) -> str:
         if "patient" in (roles or []):
             return "patient_token_string"
         elif "provider" in (roles or []):
             return "provider_token_string"
         return "generic_token_string"

    mock_service.create_access_token = AsyncMock(side_effect=async_mock_create_token)

    return mock_service

@pytest.fixture(scope="function")
def mock_auth_service_for_client() -> AuthenticationService:
    """Provides a mocked AuthenticationService for the client fixture."""
    mock_service = AsyncMock(spec=AuthenticationService)

    # Define a mock get_user_by_id based on payloads
    async def mock_get_user_by_id(user_id: str):
        mock_user = MagicMock()
        mock_user.id = user_id
        # Determine roles based on user_id prefix or other convention
        if user_id.startswith("test_patient"):
            mock_user.roles = ["patient"]
        elif user_id.startswith("test_provider"):
            mock_user.roles = ["provider"]
        # Add other roles if needed
        else:
            mock_user.roles = [] # Default or handle unknown
        # Simulate user found
        return mock_user
        # Return None # Simulate user not found if needed for specific tests

    mock_service.get_user_by_id = AsyncMock(side_effect=mock_get_user_by_id)
    # Mock other methods if they are called by middleware or dependencies
    # e.g., mock_service.validate_credentials = AsyncMock(...)
    return mock_service


# Restore the client fixture
@pytest.fixture(scope="function") # Use function scope for isolation
def client(
    mock_settings,
    test_environment,
    mock_jwt_service_for_client: JWTService, # Inject JWT mock
    mock_auth_service_for_client: AuthenticationService # Inject Auth mock
) -> Generator[TestClient, None, None]:
    """
    Create a TestClient instance for testing API endpoints.

    This fixture ensures the application is created *after* settings are mocked,
    uses an isolated in-memory SQLite database, adds AuthenticationMiddleware with
    mocked services, and overrides dependencies for testing.
    """
    settings = mock_settings
    logger = logging.getLogger(__name__)
    logger.info("--- [Client Fixture Start] ---")
    logger.info(f"[Client Fixture] ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
    logger.info(f"[Client Fixture] Using settings object: {settings}")
    logger.info(f"[Client Fixture] Settings URI: {settings.SQLALCHEMY_DATABASE_URI}")
    env_uri_override = os.getenv("SQLALCHEMY_DATABASE_URI")
    logger.info(f"[Client Fixture] Env Var Override URI: {env_uri_override}")
    logger.info("[Client Fixture] Instantiating Database...")

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
    app_instance = create_application() # Renamed to avoid confusion

    # --- Define Custom Test Lifespan ---
    @asynccontextmanager
    async def test_lifespan(app_param: FastAPI): # Changed variable name
        # Startup: Use the pre-configured test_db for setup
        logger.info("--- [Test Lifespan Start] ---\n")
        logger.info(f"[Test Lifespan] Using engine: {test_db.engine}")
        async with test_db.engine.begin() as conn:
             await conn.run_sync(Base.metadata.drop_all)
             await conn.run_sync(Base.metadata.create_all)
        logger.info("--- [Test Lifespan] Database tables created ---\n")
        yield
        # Shutdown: Use the pre-configured test_db for teardown
        logger.info("--- [Test Lifespan Shutdown] ---\n")
        await test_db.dispose()
        logger.info("--- [Test Lifespan] Engine disposed ---\n")

    # Assign the custom lifespan to the app instance *before* TestClient uses it
    app_instance.router.lifespan_context = test_lifespan

    # --- Add Authentication Middleware with Mocks ---
    # Ensure this happens *before* dependency overrides if middleware uses them
    # Note: Order matters if middleware registration affects dependency injection
    app_instance.add_middleware(
        AuthenticationMiddleware,
        auth_service=mock_auth_service_for_client, # Provide mocked auth service
        jwt_service=mock_jwt_service_for_client    # Provide mocked jwt service
    )
    logger.info("[Client Fixture] AuthenticationMiddleware added with mocks.")
    # --- End Authentication Middleware ---


    # Override the database session dependency
    @asynccontextmanager
    async def override_get_db():
        async with test_db.session() as session:
            yield session

    app_instance.dependency_overrides[get_db_dependency()] = override_get_db
    logger.info("[Client Fixture] Database dependency overridden.")

    # --- Override Auth Dependencies ---
    app_instance.dependency_overrides[get_jwt_service] = lambda: mock_jwt_service_for_client
    # Remove override for non-existent get_auth_service
    # app_instance.dependency_overrides[get_auth_service] = lambda: mock_auth_service_for_client
    logger.info("[Client Fixture] JWT dependency overridden.")
    # --- End Auth Dependencies ---


    # --- Prevent asyncpg from using ambient PG vars ---
    pg_vars = ["PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE", "DATABASE_URL"]
    original_pg_vars = {var: os.environ.get(var) for var in pg_vars}
    for var in pg_vars:
        if var in os.environ:
            del os.environ[var]
    # --- End PG Vars Handling ---


    # Create TestClient with the fully configured app
    logger.info("[Client Fixture] Creating TestClient...")
    with TestClient(app_instance) as test_client:
        logger.info("--- [Client Fixture] Yielding TestClient ---")
        yield test_client
        logger.info("--- [Client Fixture] Teardown Start ---")

    # --- Restore PG Vars ---
    for var, value in original_pg_vars.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ: # If it was set to None originally, ensure it's removed
             del os.environ[var]
    # --- End PG Vars Restore ---

    logger.info("--- [Client Fixture End] ---")


# --- Database Fixtures (Independent of client) ---
# If you need direct DB access in tests *not* using the client, define separate fixtures.

# Fixture for JWTService (can be used directly by tests if needed)
@pytest.fixture(scope="function")
async def jwt_service(mock_settings: MockSettings) -> JWTService:
    """Provides a real JWTService instance configured with mock settings."""
    # Use the mocked settings to initialize a real service instance
    return JWTService(settings=mock_settings)


# Fixture to generate tokens using the real JWTService (configured with mock settings)
@pytest.fixture(scope="function")
async def generate_token(jwt_service: JWTService) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, str]]:
    """Provides a function to generate access tokens using the jwt_service fixture."""

    async def _generate(payload: Dict[str, Any]) -> str:
        """Generates a token using the jwt_service."""
        # Ensure payload has essential claims like 'sub' and 'exp'
        # The payload fixtures (mock_patient_payload, etc.) should provide these
        subject = payload.get('sub')
        roles = payload.get('roles') # Get roles if present

        if not subject:
            raise ValueError("Payload must contain 'sub' key for token generation")

        # Call the actual service method - adjust signature if needed
        # Assuming create_access_token takes subject and optional roles
        return await jwt_service.create_access_token(subject=subject, roles=roles)

    return _generate

@pytest.fixture(scope="function")
def mock_patient_payload() -> Dict[str, Any]:
    """Provides a sample patient payload for token generation."""
    user_id = f"test_patient_{uuid.uuid4().hex[:8]}"
    return {
        "id": user_id,
        "sub": user_id, # Added 'sub' key
        "roles": ["patient"],
        "exp": int(time.time()) + 1800 # 30 minutes expiry
    }


@pytest.fixture(scope="function")
def mock_provider_payload() -> Dict[str, Any]:
    """Provides a sample provider payload for token generation."""
    user_id = f"test_provider_{uuid.uuid4().hex[:8]}"
    return {
        "id": user_id,
        "sub": user_id, # Add 'sub' consistently
        "roles": ["provider"],
        "exp": int(time.time()) + 1800
    }

# --- Fixtures for Token Headers ---
# These now use the generate_token fixture which uses the *real* JWTService
# but configured with the mock settings (test secret key).
# The client fixture uses a *mocked* JWTService for decoding.
# This setup ensures tests can generate valid tokens (using the test key)
# and the TestClient interacts with an app that uses mocks for validation.

@pytest.fixture(scope="function")
async def patient_token_headers(generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_patient_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates auth headers with a valid patient token."""
    token = await generate_token(mock_patient_payload)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
async def provider_token_headers(generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_provider_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates auth headers with a valid provider token."""
    token = await generate_token(mock_provider_payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_patient() -> Patient:
    """Provides a sample Patient domain object for testing."""
    # Updated to match the Patient dataclass fields
    return Patient(
        id=str(uuid.uuid4()),
        name="Test Patient Name", # Use 'name' field
        date_of_birth="1990-01-01",
        gender="Other",
        email="test.patient.fixture@example.com", # Optional, added for completeness
        phone="555-TEST", # Optional, added for completeness
        # insurance_number="INS-TEST-123", # Example if needed
        # medical_history=["Tested Positive"], # Example if needed
    )

# ... potentially other global fixtures ...
