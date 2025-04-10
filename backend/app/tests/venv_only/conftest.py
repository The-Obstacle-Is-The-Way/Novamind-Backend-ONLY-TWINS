"""
Configuration for venv_only tests.

These tests require Python packages but no external services like databases or APIs.
They sit between standalone tests (no dependencies) and integration tests (external services).
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

def pytest_configure(config):
    """Configure pytest environment for venv_only tests."""
    # Ensure we're running in test mode
    os.environ["TESTING"] = "1"
    os.environ["TEST_TYPE"] = "venv_only"
    
    # Add backend to path if not already there
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

@pytest.fixture
def mock_db_session():
    """Mock database session that prevents actual database operations."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    session.add.return_value = None
    session.commit.return_value = None
    session.close.return_value = None
    return session

@pytest.fixture(autouse=True)
def no_database_access():
    """Prevent actual database connections."""
    import sqlalchemy
    original_create_engine = sqlalchemy.create_engine
    
    def mock_create_engine(*args, **kwargs):
        raise RuntimeError("Database connections are not allowed in venv_only tests")
    
    sqlalchemy.create_engine = mock_create_engine
    yield
    sqlalchemy.create_engine = original_create_engine

@pytest.fixture(autouse=True)
def no_network_access():
    """Prevent actual network requests."""
    import socket
    original_socket = socket.socket
    
    def mock_socket(*args, **kwargs):
        mock = MagicMock()
        mock.connect = lambda *_, **__: exec('raise RuntimeError("Network connections are not allowed in venv_only tests")')
        return mock
    
    socket.socket = mock_socket
    yield
    socket.socket = original_socket
