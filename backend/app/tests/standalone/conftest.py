"""
Configuration for Standalone Tests

This module provides pytest fixtures and configuration specifically for standalone tests.
Standalone tests should have no external dependencies like databases or network services.

Principles:
- Keep tests isolated
- Mock all external dependencies
- Ensure deterministic test results 
- Tests should run quickly
- No PHI or sensitive data in test fixtures
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch


def pytest_configure(config):
    """Configure pytest environment for standalone tests."""
    # Ensure we're running in test mode
    os.environ["TESTING"] = "1"
    os.environ["TEST_TYPE"] = "standalone"
    
    # Add backend to path if not already there
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)


@pytest.fixture
def mock_logger():
    """Fixture to mock a logger."""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def mock_session():
    """
    Fixture to mock a database session.
    
    This avoids any actual database connections in standalone tests.
    """
    session = MagicMock()
    session.query = MagicMock(return_value=session)
    session.filter = MagicMock(return_value=session)
    session.filter_by = MagicMock(return_value=session)
    session.all = MagicMock(return_value=[])
    session.first = MagicMock(return_value=None)
    session.add = MagicMock()
    session.delete = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.execute = MagicMock()
    return session


@pytest.fixture
def mock_repository():
    """
    Fixture to mock a repository.
    
    This avoids any actual database interactions in standalone tests.
    """
    repo = MagicMock()
    repo.get_by_id = MagicMock(return_value=None)
    repo.get_all = MagicMock(return_value=[])
    repo.create = MagicMock()
    repo.update = MagicMock()
    repo.delete = MagicMock()
    return repo


@pytest.fixture(autouse=True)
def disable_network_calls():
    """
    Fixture to disable network calls.
    
    This prevents any actual network requests in standalone tests.
    """
    with patch("socket.socket") as mock_socket:
        mock_socket.connect = MagicMock(side_effect=Exception("Network calls are not allowed in standalone tests"))
        yield


@pytest.fixture(autouse=True)
def disable_database_access():
    """
    Fixture to disable database access.
    
    This prevents any actual database connections in standalone tests.
    """
    # Mock SQLAlchemy session
    with patch("sqlalchemy.create_engine") as mock_create_engine:
        mock_create_engine.side_effect = Exception("Database connections are not allowed in standalone tests")
        yield


# Optional but recommended: Add specific test skipping for non-standalone tests
def pytest_collection_modifyitems(config, items):
    """Skip tests that are not marked as standalone."""
    # If we're running the standalone test suite, ensure all tests have the standalone marker
    if os.environ.get("TEST_TYPE") == "standalone":
        for item in items:
            if "standalone" not in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Test is not marked as standalone"))