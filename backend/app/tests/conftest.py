import os
from dotenv import load_dotenv, find_dotenv

# Load test environment variables BEFORE application imports
# Construct the path relative to this conftest.py file
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env.test')
found = load_dotenv(dotenv_path=dotenv_path)
if not found:
    print(f"Warning: .env.test file not found at {dotenv_path}. Ensure it exists.")

"""
Global pytest configuration and fixtures.

This module sets up global fixtures and configuration for all tests.
It also handles patching of problematic imports during test collection.
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import create_application # Restore import
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_dependency, Base, Database
from app.config.settings import get_settings, Settings
from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI, Request
import uuid
import time
from typing import Dict, Any, Callable, Generator, Coroutine, List, Optional, AsyncGenerator
from pydantic import SecretStr # Import SecretStr
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload
from app.infrastructure.security.auth.authentication_service import AuthenticationService
from app.presentation.middleware.authentication_middleware import AuthenticationMiddleware
from app.domain.entities.patient import Patient
from app.domain.entities.base_entity import BaseEntity  # Assuming BaseEntity exists
# Add necessary SQLAlchemy imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # <-- Add AsyncSession here
from sqlalchemy.orm import sessionmaker

# Try to import our patching utility
try:
    from app.tests.helpers.patch_imports import patch_imports
except ImportError:
    # Use a dummy context manager if the import fails
    from contextlib import contextmanager

    @contextmanager
    def patch_imports():
        yield

# Import the logger setup function
from app.infrastructure.logging.logger import get_logger

# Instantiate the logger for this module
logger = get_logger(__name__)

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
        self.DATABASE_URL = "sqlite+aiosqlite:///./test.db" # Renamed attribute
        self.DB_POOL_SIZE = 5
        self.DB_MAX_OVERFLOW = 10
        self.DATABASE_ECHO = False
        self.LOG_LEVEL = "DEBUG"
        self.ENABLE_ANALYTICS = False

        # --- Directly add JWT settings expected by JWTService --- 
        # Use SecretStr to match the real Settings class
        self.SECRET_KEY = SecretStr("test-secret-key-longer-than-32-chars-for-sure") 
        self.ALGORITHM = "HS256" # Direct access
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Direct access
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7 # Direct access
        # --- End Direct JWT Settings ---
        
        # --- Mocked ML Settings --- 
        self.ml = MagicMock()
        self.ml.models_path = "/test/models"
        self.ml.cache_path = "/test/cache"
        self.ml.storage_path = "/test/storage"
        
        # Mock nested settings - adjust attributes as needed for tests
        self.ml.mentallama = MagicMock(
            provider="mock",
            openai_api_key=None,
            model_mappings={"default": "mock-model"}
        )
        self.ml.pat = MagicMock(
            model_path="/test/models/pat/mock-pat",
            cache_dir="/test/cache/pat",
            use_gpu=False
        )
        self.ml.xgboost = MagicMock(
            treatment_response_model_path="/test/models/xgboost/mock-treat.xgb",
            outcome_prediction_model_path="/test/models/xgboost/mock-outcome.xgb",
            risk_prediction_model_path="/test/models/xgboost/mock-risk.xgb"
        )
        self.ml.lstm = MagicMock(
            biometric_correlation_model_path="/test/models/lstm/mock-biometric.pkl"
        )
        self.ml.phi_detection = MagicMock(
            patterns_file="/test/config/mock-phi-patterns.yaml",
            default_redaction_format="[MOCK_PHI]"
        )
        # --- End Mocked ML Settings ---

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
    # sys.modules['app.config.settings'] = MagicMock(get_settings=lambda: settings, settings=settings) # REMOVE sys.modules patch
    # Also mock app.core.config if that path is used
    # sys.modules['app.core.config'] = MagicMock(get_settings=lambda: settings, settings=settings) # REMOVE sys.modules patch
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
    # --- Add backend directory to sys.path (DISABLED - Relying on pytest.ini pythonpath = .) ---
    # conftest_path = Path(__file__).resolve()
    # backend_dir = conftest_path.parent.parent.parent 
    # if str(backend_dir) not in sys.path:
    #     sys.path.insert(0, str(backend_dir))
    #     # Use print to stderr for reliable logging during early configuration
    #     print(f"[pytest_configure] Added to sys.path: {str(backend_dir)}", file=sys.stderr)
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

    # Apply the import patch (if still needed) - DISABLED FOR NOW
    # with patch_imports():
    #     pass

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
@pytest.fixture(scope="function")
async def client(
    mock_settings: MockSettings, # Inject mock_settings
    test_environment, 
    # Use the MOCK jwt service fixture for the client's app override
    mock_jwt_service_for_client: JWTService, # Corrected dependency
    app: FastAPI # Inject the app fixture
) -> Generator[TestClient, None, None]:
    """Provides an async TestClient instance with JWT dependency overridden by a MOCKED service."""
    logger.info("[Fixture client - async] ENTERING - Overriding JWT with MOCKED service")

    # --- Dependency Overrides --- 
    
    # Override settings using get_settings
    # This is the primary way settings should be accessed in the app
    app.dependency_overrides[get_settings] = lambda: mock_settings
    logger.info(f"[Fixture client - async] Overrode get_settings with mock_settings: {id(mock_settings)}")

    # Override the JWT service provider function
    # Ensure the import path is correct
    try:
        # Correct import path for get_jwt_service
        from app.infrastructure.security.jwt.jwt_service import get_jwt_service 
        # Override with the *resolved* mock_jwt_service_for_client instance from the fixture
        app.dependency_overrides[get_jwt_service] = lambda: mock_jwt_service_for_client # Use the corrected fixture
        logger.info(f"[Fixture client - async] Overrode get_jwt_service with MOCKED service: {id(mock_jwt_service_for_client)}")
    except ImportError:
        logger.error("Could not import get_jwt_service from app.infrastructure.security.jwt.jwt_service to override.")
        # Optionally re-raise or handle differently if this import MUST succeed
        raise

    # Optional: Override specific repository implementations if needed for tests
    # Example (adjust import paths and classes as needed):
    # try:
    #     from app.infrastructure.persistence.sqlalchemy.repositories import get_patient_repository
    #     app.dependency_overrides[get_patient_repository] = lambda: mock_patient_repository
    # except ImportError:
    #     logger.error("Could not import get_patient_repository to override.")

    # --- Include Routers ---
    # Example: app.include_router(...)

    # --- Yield TestClient ---
    # TestClient is used directly within the async fixture context
    get_settings.cache_clear() 
    logger.info("--- [Fixture: client] Cleared get_settings cache.")
    
    with TestClient(app) as c:
        logger.info("--- [Fixture: client] TestClient created.")
        yield c
    
    # Optional: Clear cache again after test if needed, though clearing before should suffice
    # get_settings.cache_clear()
    # logger.info("--- [Fixture: client] Cleared get_settings cache post-yield.")
    logger.info("[Fixture client - async] EXITING")
    # Restore original dependencies (handled by pytest fixture teardown)


# --- Database Fixtures (Independent of client) ---
# If you need direct DB access in tests *not* using the client, define separate fixtures.

# Fixture for JWTService (can be used directly by tests if needed)
@pytest.fixture(scope="function") # Keep function scope
async def jwt_service(mock_settings: MockSettings) -> AsyncGenerator[JWTService, None]:
    """Provides a JWTService instance explicitly configured with mock settings for test setup."""
    # Explicitly pass mock_settings for test fixture usage, overriding the Depends default for this call.
    # The instance used by middleware during requests will still use Depends().
    service = JWTService(settings=mock_settings)
    logger.debug(f"[jwt_service fixture] Instantiated JWTService {id(service)} EXPLICITLY using settings {id(mock_settings)}") # Now logger is defined
    
    # Yield the service instance
    yield service

# Fixture to generate tokens using the real JWTService (configured with mock settings)
@pytest.fixture(scope="function") # Ensure function scope
async def generate_token(jwt_service: AsyncGenerator[JWTService, None]) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, str]]:
    """Provides a function to generate access tokens using the jwt_service fixture."""
    # Consume the async generator to get the actual JWTService instance
    actual_jwt_service = await anext(jwt_service)

    async def _generate(payload: Dict[str, Any]) -> str: # Inner function remains async
        """Generates a token using the resolved jwt_service instance."""
        # Ensure payload has essential claims like 'sub' and 'exp'
        subject = payload.get('sub')
        roles = payload.get('roles')

        if not subject:
            raise ValueError("Payload must contain 'sub' key for token generation")

        # Call the method on the resolved service instance
        return await actual_jwt_service.create_access_token(subject=subject, roles=roles) # Use actual_jwt_service

    return _generate # Return the inner async function

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

@pytest.fixture(scope="function") # Ensure function scope
async def patient_token_headers(generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_patient_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates auth headers with a valid patient token."""
    token_generator = await generate_token # Await the fixture to get the generator function
    token = await token_generator(mock_patient_payload) # Call and await the generator function
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function") # Ensure function scope
async def provider_token_headers(generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_provider_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates auth headers with a valid provider token."""
    token_generator = await generate_token # Await the fixture to get the generator function
    token = await token_generator(mock_provider_payload) # Call and await the generator function
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

# Commenting out potentially conflicting session-scoped app fixture
# @pytest.fixture(scope="session")
# async def test_app() -> AsyncGenerator[FastAPI, None]:
#     """
#     Create a test application instance with potentially overridden settings.
#     """
#     # Ensure a valid SECRET_KEY for testing by patching get_settings
#     test_secret_key = "a_very_secure_and_long_test_secret_key_for_pytest_runs_12345"
#     
#     # Create a test settings instance with the valid key
#     # Load other settings from the default mechanism (.env.test or .env)
#     base_settings = get_settings() # Load base settings first
#     # Override the secret key
#     base_settings.SECRET_KEY = test_secret_key 
#     
#     # Patch get_settings to return our modified settings during app creation
#     with patch('app.config.settings.get_settings', return_value=base_settings):
#         app_instance = create_application()
#     
#     # Apply other overrides if necessary (e.g., for database session)
#     # app_instance.dependency_overrides[get_db] = override_get_db
#     yield app_instance

# ... potentially other global fixtures ...

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine(mock_settings: MockSettings):
    """Yields an SQLAlchemy engine scoped for the entire test session."""
    engine = create_async_engine(mock_settings.DATABASE_URL, echo=mock_settings.DATABASE_ECHO)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session", autouse=True)
async def setup_database(db_engine):
    """Creates and drops database tables for the test session."""
    async with db_engine.begin() as conn:
        # Drop existing tables (optional, for clean slate)
        # await conn.run_sync(Base.metadata.drop_all) 
        # Create new tables
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Optional: Drop tables after session if needed, careful with parallel tests
    # async with db_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function") # Function scope for transaction isolation
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yields an SQLAlchemy session with transaction rollback for each test."""
    async_session_factory = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        # Begin a nested transaction (if supported, helps with rollback)
        # await session.begin_nested() # Use if needed and supported
        try:
            yield session
            await session.commit() # Commit if test passes without exception
        except Exception:
            await session.rollback() # Rollback on any test exception
            raise # Re-raise the exception
        finally:
            await session.close()


# --- FastAPI Application and Client Fixtures ---

@pytest.fixture(scope="function") # Change scope to function if app state needs reset
def app(mock_settings: MockSettings, db_session: AsyncSession) -> FastAPI: # Inject db_session here
    """Creates a FastAPI application instance for testing."""
    
    # Override the database dependency *before* creating the application
    # This ensures the test client uses the test database session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Create the application *after* setting up the override
    application = create_application()
    application.dependency_overrides[get_db_dependency] = override_get_db

    return application
