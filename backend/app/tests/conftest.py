# -*- coding: utf-8 -*-
"""
Global pytest configuration file (conftest.py) for backend tests.

Defines shared fixtures, hooks, and configuration for the entire test suite.
"""

import os
from dotenv import load_dotenv, find_dotenv
import sys
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import create_application # Restore import
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_dependency, Base, Database
from app.config.settings import get_settings, Settings
from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI, Request, Depends
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
from httpx import AsyncClient # ADDED
from app.tests.security.utils.base_security_test import BaseSecurityTest 
# AuthenticationService might be needed if testing it directly
from app.infrastructure.security.auth.authentication_service import AuthenticationService # For mocking
# Import UserModel and Role enum - CORRECTED PATHS & CLASS NAME
from app.infrastructure.models.user_model import UserModel # CORRECTED Class name
from app.domain.enums.role import Role # Corrected Role path
# Import provider functions to override
from app.presentation.dependencies.auth import get_authentication_service
from app.infrastructure.security.jwt.jwt_service import get_jwt_service

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
    """Mock settings class to override production settings during tests."""
    def __init__(self):
        """Initialize mock settings with test-specific values."""
        # Basic Info
        self.PROJECT_NAME = "NovaMind Test"
        self.API_V1_STR = "/api/v1"
        self.ENVIRONMENT = "test"
        self.TESTING = True
        self.LOG_LEVEL = "DEBUG" # Enable detailed logging for tests

        # Security
        # Use a fixed, known secret key for reproducible JWT generation in tests
        # WRAPPED in SecretStr to match expected type
        self.SECRET_KEY = SecretStr(os.getenv(
            "TEST_SECRET_KEY",
            "a_very_secure_and_long_test_secret_key_for_pytest_runs_1234567890_abcdefghijklmnopqrstuvwxyz"
        ))
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.ALGORITHM = "HS256"
        self.BACKEND_CORS_ORIGINS = ["*"] # Allow all for testing, or configure specific test origins
        self.PASSWORD_HASHING_SCHEMES = ["bcrypt"]
        self.PASSWORD_SALT_ROUNDS = 4 # Use lower rounds for faster tests

        # Database (using test-specific settings from .env.test)
        self.DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test_db.sqlite")
        self.DATABASE_ECHO = os.getenv("TEST_DATABASE_ECHO", "False").lower() in ('true', '1', 't')

        # ADDED: Redis settings for testing
        self.REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1") # Default to DB 1 for tests
        self.CACHE_EXPIRATION_SECONDS = 60 # Example cache time for tests

        # MFA Settings (provide sensible defaults for testing)
        self.MFA_SECRET_KEY = SecretStr(os.getenv("TEST_MFA_SECRET_KEY", "test_mfa_secret_for_pytest_runs_123"))
        self.MFA_ISSUER_NAME = "NovaMind Test Platform"

        # PHI Detection Settings (can be mocked or use defaults)
        # Assuming a nested structure based on previous examples
        class MockMLSettings:
            class MockPhiDetectionSettings:
                model_path: str = "mock/phi/model/path"
                confidence_threshold: float = 0.85
                redaction_strategy: str = "replace"
                phi_patterns_file: str = "app/infrastructure/security/phi/phi_patterns.yaml"
                default_redaction_format: str = "[{category}]"
                parallel_processing: bool = False # Keep false for simpler testing?
            phi_detection = MockPhiDetectionSettings()
        self.ml = MockMLSettings()

        # Add other necessary mock settings as needed by the application components
        self.AUDIT_LOG_FILE = "./test_audit.log"
        self.EXTERNAL_AUDIT_ENABLED = False

        # Rate Limiting (Example defaults)
        self.RATE_LIMIT_TIMES = 500 # Allow generous limits for testing
        self.RATE_LIMIT_SECONDS = 60

    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

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

    async def async_mock_verify_token(token: str) -> TokenPayload:
        # Verify the token based on the simple strings
        # Raise specific exceptions for invalid/missing tokens
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
            # Import here or ensure it's available in the scope
            from app.domain.exceptions import InvalidTokenError
            raise InvalidTokenError("Mocked invalid token")

    # Mock verify_token, not decode_token
    mock_service.verify_token = AsyncMock(side_effect=async_mock_verify_token)
    # Remove or comment out the old decode_token mock if it exists
    # mock_service.decode_token = AsyncMock(side_effect=async_mock_decode_token) # Remove/Comment this

    # Mock create_access_token to return predictable strings used in verify mock
    async def async_mock_create_token(subject: str, roles: Optional[List[str]] = None) -> str:
         if "patient" in (roles or []):
             return "patient_token_string"
         elif "provider" in (roles or []):
             return "provider_token_string"
         return "generic_token_string"

    mock_service.create_access_token = AsyncMock(side_effect=async_mock_create_token)

    return mock_service

@pytest.fixture(scope="function")
def mock_auth_service_for_client(
    mock_patient_payload: Dict[str, Any], # Inject payloads
    mock_provider_payload: Dict[str, Any]
) -> AuthenticationService:
    """Provides a mocked AuthenticationService that returns valid UserModel objects."""
    mock_service = AsyncMock(spec=AuthenticationService)

    # Define a mock get_user_by_id that returns valid UserModel instances
    async def mock_get_user_by_id(user_id: str):
        # Use payload data to construct realistic UserModel objects
        
        # Handle patient user
        if user_id == mock_patient_payload.get("sub"): 
            try:
                patient_uuid = uuid.UUID(mock_patient_payload["id"]) 
                # Create UserModel instance, matching its attributes
                return UserModel(
                    id=patient_uuid, 
                    email=f"{user_id}@test.novamind.com", 
                    first_name="MockPatient", # Add required fields
                    last_name="User",
                    roles=[Role.PATIENT.value], # Use Role enum VALUE (string)
                    is_active=True,
                    hashed_password="mock_hashed_password" 
                )
            except Exception as e:
                logger.error(f"Error creating mock patient UserModel for ID {user_id}: {e}")
                return None 
        
        # Handle provider user
        elif user_id == mock_provider_payload.get("sub"): 
            try:
                provider_uuid = uuid.UUID(mock_provider_payload["id"])
                 # Create UserModel instance
                return UserModel(
                    id=provider_uuid, 
                    email=f"{user_id}@test.novamind.com", 
                    first_name="MockProvider", # Add required fields
                    last_name="User",
                    roles=[Role.PROVIDER.value], # Use Role enum VALUE
                    is_active=True,
                    hashed_password="mock_hashed_password" 
                )
            except Exception as e:
                logger.error(f"Error creating mock provider UserModel for ID {user_id}: {e}")
                return None 

        # Handle the hardcoded admin user (used by mock_jwt_service_for_client verify)
        # Note: The mock_jwt_service currently verifies using "patient_token_string" or "provider_token_string" 
        # and doesn't seem to directly use "uuid-admin-123". 
        # Let's refine this part if needed based on future errors.
        # For now, returning None for other IDs is likely sufficient.
        
        # Simulate user not found for other IDs
        else:
            logger.warning(f"Mock get_user_by_id called with unexpected ID: {user_id}")
            return None

    mock_service.get_user_by_id = AsyncMock(side_effect=mock_get_user_by_id)
    return mock_service


# Fixture providing the MOCKED AuthenticationService instance
@pytest.fixture(scope="function")
def mock_auth_service_override(
    mock_patient_payload: Dict[str, Any], 
    mock_provider_payload: Dict[str, Any]
) -> AuthenticationService:
    """Provides the MOCKED AuthenticationService instance to be used in overrides."""
    mock_service = AsyncMock(spec=AuthenticationService)

    async def mock_get_user_by_id(user_id: str):
        # Simplified logic based on previous edits
        if user_id == mock_patient_payload.get("sub"): 
            try:
                return UserModel(
                    id=uuid.UUID(mock_patient_payload["id"]),
                    email=f"{user_id}@test.novamind.com", 
                    first_name="MockPatient", last_name="User",
                    roles=[Role.PATIENT.value], is_active=True,
                    hashed_password="mock_hashed_password" 
                )
            except Exception: return None
        elif user_id == mock_provider_payload.get("sub"): 
            try:
                return UserModel(
                    id=uuid.UUID(mock_provider_payload["id"]),
                    email=f"{user_id}@test.novamind.com", 
                    first_name="MockProvider", last_name="User",
                    roles=[Role.PROVIDER.value], is_active=True,
                    hashed_password="mock_hashed_password" 
                )
            except Exception: return None
        else:
            return None
            
    mock_service.get_user_by_id = AsyncMock(side_effect=mock_get_user_by_id)
    return mock_service

# Fixture providing the MOCKED JWTService instance
@pytest.fixture(scope="function")
def mock_jwt_service_override(
    mock_settings,
    mock_patient_payload: Dict[str, Any],
    mock_provider_payload: Dict[str, Any]
) -> JWTService:
    """Provides the MOCKED JWTService instance to be used in overrides."""
    # This is the same logic as the old mock_jwt_service_for_client
    mock_service = AsyncMock(spec=JWTService)
    patient_payload = mock_patient_payload 
    provider_payload = mock_provider_payload 

    async def async_mock_verify_token(token: str) -> TokenPayload:
        if token == "patient_token_string":
            return TokenPayload(
                sub=patient_payload.get('sub'), exp=patient_payload.get('exp'),
                iat=int(time.time()), jti=f"jti_{patient_payload.get('sub')}",
                scope="access_token", roles=patient_payload.get('roles'),
                user_id=patient_payload.get('id')
            )
        elif token == "provider_token_string":
            return TokenPayload(
                 sub=provider_payload.get('sub'), exp=provider_payload.get('exp'),
                 iat=int(time.time()), jti=f"jti_{provider_payload.get('sub')}",
                 scope="access_token", roles=provider_payload.get('roles'),
                 user_id=provider_payload.get('id')
             )
        else:
            from app.domain.exceptions import InvalidTokenError
            raise InvalidTokenError("Mocked invalid token")
            
    mock_service.verify_token = AsyncMock(side_effect=async_mock_verify_token)

    async def async_mock_create_token(subject: str, roles: Optional[List[str]] = None) -> str:
         if Role.PATIENT.value in (roles or []): return "patient_token_string"
         elif Role.PROVIDER.value in (roles or []): return "provider_token_string"
         return "generic_token_string"
         
    mock_service.create_access_token = AsyncMock(side_effect=async_mock_create_token)
    return mock_service


# Final client fixture structure with direct TYPE overrides
@pytest_asyncio.fixture(scope="function") 
async def client(
    # Non-default arguments FIRST
    app: FastAPI, 
    mock_settings: MockSettings, 
    test_environment, 
    # Default arguments (using Depends) LAST
    mock_auth_service_instance: AuthenticationService = Depends(mock_auth_service_override),
    mock_jwt_service_instance: JWTService = Depends(mock_jwt_service_override)
) -> AsyncGenerator[AsyncClient, None]: 
    """Provides an httpx.AsyncClient with overridden service dependencies.
    Overrides the specific service classes (AuthenticationService, JWTService).
    """
    logger.info("[Fixture client - async] ENTERING - Applying direct service type overrides")

    # Override service TYPES directly
    app.dependency_overrides[get_settings] = lambda: mock_settings
    # Override AuthenticationService type to return the mock instance
    app.dependency_overrides[AuthenticationService] = lambda: mock_auth_service_instance
    # Override JWTService type to return the mock instance
    app.dependency_overrides[JWTService] = lambda: mock_jwt_service_instance
    
    logger.info(f"[Fixture client - async] Overrode get_settings provider.")
    logger.info(f"[Fixture client - async] Overrode AuthenticationService type with mock: {id(mock_auth_service_instance)}")
    logger.info(f"[Fixture client - async] Overrode JWTService type with mock: {id(mock_jwt_service_instance)}")

    get_settings.cache_clear()
    logger.info("--- [Fixture: client] Cleared get_settings cache before AsyncClient creation.")

    async with AsyncClient(app=app, base_url="http://test") as async_client:
        logger.info("--- [Fixture: client] httpx.AsyncClient created.")
        yield async_client
        logger.info("--- [Fixture: client] httpx.AsyncClient context exiting.")

    logger.info("[Fixture client - async] EXITING")
    app.dependency_overrides = {} 

# --- Database Fixtures (Independent of client) ---
# If you need direct DB access in tests *not* using the client, define separate fixtures.

# Fixture for JWTService (can be used directly by tests if needed)
@pytest_asyncio.fixture(scope="function") # CHANGED decorator
async def jwt_service(mock_settings: MockSettings) -> AsyncGenerator[JWTService, None]: # Keep AsyncGenerator here for yield
    """Provides a JWTService instance explicitly configured with mock settings for test setup."""
    # Explicitly pass mock_settings for test fixture usage, overriding the Depends default for this call.
    # The instance used by middleware during requests will still use Depends().
    service = JWTService(settings=mock_settings)
    logger.debug(f"[jwt_service fixture] Instantiated JWTService {id(service)} EXPLICITLY using settings {id(mock_settings)}") # Now logger is defined
    
    # Yield the service instance
    yield service

# Fixture to generate tokens using the real JWTService (configured with mock settings)
@pytest_asyncio.fixture(scope="function") # CHANGED decorator
async def generate_token(jwt_service: JWTService) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, str]]: # CHANGED: jwt_service type hint, assuming it's resolved
    """Provides a function to generate access tokens using the resolved jwt_service fixture."""
    # REMOVED: actual_jwt_service = await anext(jwt_service) - Assuming pytest_asyncio handles resolution

    async def _generate(payload: Dict[str, Any]) -> str: # Inner function remains async
        """Generates a token using the resolved jwt_service instance."""
        # Ensure payload has essential claims like 'sub' and 'exp'
        subject = payload.get('sub')
        roles = payload.get('roles')

        if not subject:
            raise ValueError("Payload must contain 'sub' key for token generation")

        # Call the method on the resolved service instance (injected by pytest_asyncio)
        return await jwt_service.create_access_token(subject=subject, roles=roles) # Use jwt_service directly

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

@pytest_asyncio.fixture(scope="function") # CHANGED decorator
async def patient_token_headers(generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_patient_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates auth headers with a valid patient token."""
    # generate_token is now the resolved _generate function injected by pytest_asyncio
    token = await generate_token(mock_patient_payload) # Call and await the generator function
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture(scope="function") # CHANGED decorator
async def provider_token_headers(generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_provider_payload: Dict[str, Any]) -> Dict[str, str]:
    """Generates auth headers with a valid provider token."""
    # generate_token is now the resolved _generate function injected by pytest_asyncio
    token = await generate_token(mock_provider_payload) # Call and await the generator function
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
