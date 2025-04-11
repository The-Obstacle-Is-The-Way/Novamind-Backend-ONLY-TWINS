"""
Standalone Test Configuration and Fixtures

This file contains test fixtures for standalone tests that don't require
any external dependencies (database, network, services, etc.).
"""

import pytest


@pytest.fixture
def standalone_fixture():
    """Fixture for standalone tests only."""
    return "standalone_fixture"