"""
Root conftest.py for Novamind Backend project.

This file ensures pytest markers are properly registered regardless of how tests are run.
"""

import pytest
import os
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load environment variables from .env.test before the test session starts."""
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env.test')
    # Load .env.test, overriding existing environment variables only if OVERRIDE=true
    # Set override=True to ensure .env.test values take precedence during tests
    load_dotenv(dotenv_path=dotenv_path, override=True)
    print(f"Loaded test environment variables from: {dotenv_path}")


# Register custom markers to avoid "unknown mark" warnings
def pytest_configure(config):
    """Register custom markers to prevent warnings."""
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
    
    # Domain-specific markers from warning messages
    config.addinivalue_line("markers", "ml: Machine learning related tests")
    config.addinivalue_line("markers", "phi: Protected Health Information related tests")