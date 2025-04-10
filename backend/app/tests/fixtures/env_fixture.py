"""
Test environment variable fixtures.

This module provides utilities for setting up and managing environment variables
required for testing. It ensures a consistent test environment and proper 
isolation between tests.
"""

import os
import pytest
from typing import Dict, Any, Generator, Optional
from unittest import mock


class TestEnvironment:
    """
    Test environment manager for setting up required environment variables.
    
    This class provides methods for setting up a consistent testing environment
    with appropriate environment variables for various test scenarios.
    """
    
    # Default environment variables for tests
    DEFAULT_TEST_ENV = {
        # Database settings
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test",
        
        # Security settings
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        
        # Encryption settings
        "PHI_ENCRYPTION_KEY": "testkeyfortestingonly12345678901234",
        "PHI_ENCRYPTION_ALGORITHM": "AES-256-CBC",
        
        # Audit settings
        "AUDIT_LOG_FILE": "test_audit.log",
        "AUDIT_LOG_LEVEL": "INFO",
        "EXTERNAL_AUDIT_ENABLED": "False",
        
        # Service settings
        "ML_SERVICE_BASE_URL": "http://localhost:8001",
        "ML_MODEL_CACHE_ENABLED": "False",
        "PHI_DETECTION_LEVEL": "moderate",
        
        # Environment
        "ENVIRONMENT": "test",
        "DEBUG": "True",
        
        # API settings
        "API_V1_PREFIX": "/api/v1",
        "BACKEND_CORS_ORIGINS": "http://localhost,http://localhost:8000",
        
        # Auth settings
        "OAUTH2_TOKEN_URL": "/api/v1/auth/token",
        "OAUTH2_REFRESH_URL": "/api/v1/auth/refresh",
    }
    
    @classmethod
    def setup_test_environment(cls, custom_env: Optional[Dict[str, str]] = None) -> None:
        """
        Set up the testing environment with required environment variables.
        
        Args:
            custom_env: Custom environment variables to add or override
        """
        # Start with default environment
        env_vars = cls.DEFAULT_TEST_ENV.copy()
        
        # Override with custom environment if provided
        if custom_env:
            env_vars.update(custom_env)
        
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
    
    @classmethod
    def reset_environment(cls, original_env: Dict[str, str]) -> None:
        """
        Reset environment variables to their original state.
        
        Args:
            original_env: Original environment variables
        """
        # Clear the environment variables we set
        for key in cls.DEFAULT_TEST_ENV:
            if key in os.environ:
                del os.environ[key]
        
        # Restore the original environment
        for key, value in original_env.items():
            os.environ[key] = value


@pytest.fixture
def test_env() -> Generator[None, None, None]:
    """
    Set up test environment variables for a test function.
    
    This fixture sets up the test environment before each test function and
    restores the original environment after the test.
    """
    # Save the original environment
    original_env = {k: v for k, v in os.environ.items()}
    
    # Set up the test environment
    TestEnvironment.setup_test_environment()
    
    # Run the test
    yield
    
    # Reset the environment
    TestEnvironment.reset_environment(original_env)


@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """
    Mock environment variables.
    
    This fixture provides a way to mock environment variables during a test
    without actually changing the real environment variables.
    """
    # Default mocked environment variables
    mocked_vars = TestEnvironment.DEFAULT_TEST_ENV.copy()
    
    # Create patchers for os.environ.get
    patcher = mock.patch("os.environ.get", lambda k, d=None: mocked_vars.get(k, d))
    getenv_patcher = mock.patch("os.getenv", lambda k, d=None: mocked_vars.get(k, d))
    
    # Start patchers
    patcher.start()
    getenv_patcher.start()
    
    # Yield mocked variables to allow modification
    yield mocked_vars
    
    # Stop patchers
    patcher.stop()
    getenv_patcher.stop()