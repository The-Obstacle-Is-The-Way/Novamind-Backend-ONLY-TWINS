"""
Root conftest.py for Novamind Backend project.

This file ensures pytest markers are properly registered regardless of how tests are run.
"""

import pytest


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