"""Unit tests for enhanced database operations and connection management."""
import pytest
from unittest.mock import patch, MagicMock, Mock
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from contextlib import contextmanager
import logging
import time

# Import modules to test
from app.infrastructure.persistence.sqlalchemy.database import (
    get_engine,
    get_session,
    create_database,
    Base,
    init_models,
    dispose_engine,
    SessionLocal,
    engine_factory,
    database_health_check
)


@pytest.fixture
def mock_engine():
    """Mock SQLAlchemy engine."""
    engine = Mock(spec=Engine)
    engine.dispose = Mock()
    engine.connect().close = Mock()
    return engine


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session."""
    session = Mock(spec=Session)
    session.commit = Mock()
    session.close = Mock()
    session.query = Mock(return_value=MagicMock())
    return session


@pytest.fixture
def mock_session_local(mock_session):
    """Mock session factory that returns the mock session."""
    @contextmanager
    def _session_cm():
        try:
            yield mock_session
        finally:
            mock_session.close()
    
    return _session_cm


class TestDatabaseConnection:
    """Test suite for database connection handling."""
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.create_engine')
    def test_get_engine(self, mock_create_engine):
        """Test getting SQLAlchemy engine with correct parameters."""
        # Setup mock
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Call function
        result = get_engine("postgresql://user:pass@localhost/db")
        
        # Assertions
        assert result == mock_engine
        mock_create_engine.assert_called_once()
        # Check some of the parameters
        call_args = mock_create_engine.call_args[0][0]
        assert call_args == "postgresql://user:pass@localhost/db"
        
        # Get keyword arguments
        kwargs = mock_create_engine.call_args[1]
        assert 'pool_pre_ping' in kwargs
        assert kwargs['pool_pre_ping'] is True
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.sessionmaker')
    def test_get_session(self, mock_sessionmaker):
        """Test session creation with correct parameters."""
        # Setup
        mock_engine = Mock()
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory
        
        # Call function
        result = get_session(mock_engine)
        
        # Assertions
        assert result == mock_session_factory
        mock_sessionmaker.assert_called_once_with(
            autocommit=False, 
            autoflush=False, 
            bind=mock_engine
        )


class TestDatabaseInitialization:
    """Test suite for database initialization functions."""
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.get_engine')
    def test_create_database(self, mock_get_engine):
        """Test database creation function."""
        # Setup
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine
        
        # Call function
        result = create_database("postgresql://user:pass@localhost/db")
        
        # Assertions
        assert result == mock_engine
        mock_get_engine.assert_called_once_with("postgresql://user:pass@localhost/db")
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.Base')
    def test_init_models(self, mock_base):
        """Test model initialization."""
        # Setup
        mock_engine = Mock()
        
        # Call function
        init_models(mock_engine)
        
        # Assertions
        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)
    
    def test_dispose_engine(self, mock_engine):
        """Test engine disposal."""
        # Call function
        dispose_engine(mock_engine)
        
        # Assertions
        mock_engine.dispose.assert_called_once()


class TestSessionHandling:
    """Test suite for session handling."""
    
    def test_session_local_context_manager(self, mock_session, mock_engine):
        """Test that SessionLocal works as a context manager."""
        # Patch the global SessionLocal to use our mock
        with patch('app.infrastructure.persistence.sqlalchemy.database.SessionLocal') as mock_session_local:
            mock_session_local.return_value = mock_session
            
            # Use as context manager
            with SessionLocal() as session:
                # Do something with session
                session.query()
            
            # Verify session was closed
            mock_session.close.assert_called_once()
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.get_session')
    @patch('app.infrastructure.persistence.sqlalchemy.database.create_database')
    def test_engine_factory(self, mock_create_database, mock_get_session):
        """Test engine factory function."""
        # Setup
        mock_engine = Mock()
        mock_session_factory = Mock()
        mock_create_database.return_value = mock_engine
        mock_get_session.return_value = mock_session_factory
        
        # Call function
        engine, session = engine_factory("postgresql://user:pass@localhost/db")
        
        # Assertions
        assert engine == mock_engine
        assert session == mock_session_factory
        mock_create_database.assert_called_once_with("postgresql://user:pass@localhost/db")
        mock_get_session.assert_called_once_with(mock_engine)


class TestDatabaseHealthCheck:
    """Test suite for database health check functionality."""
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.engine')
    def test_health_check_success(self, mock_engine):
        """Test successful health check."""
        # Setup
        mock_connection = Mock()
        mock_engine.connect.return_value = mock_connection
        mock_connection.execute.return_value = [{"result": 1}]
        
        # Call function
        result = database_health_check()
        
        # Assertions
        assert result is True
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.engine')
    def test_health_check_failure(self, mock_engine):
        """Test failed health check with exception."""
        # Setup - make connect raise an exception
        mock_engine.connect.side_effect = Exception("Database error")
        
        # Call function
        result = database_health_check()
        
        # Assertions
        assert result is False
        mock_engine.connect.assert_called_once()
    
    @patch('app.infrastructure.persistence.sqlalchemy.database.time.sleep')
    @patch('app.infrastructure.persistence.sqlalchemy.database.engine')
    def test_health_check_with_retry(self, mock_engine, mock_sleep):
        """Test health check with retry mechanism."""
        # Setup - first attempt fails, second succeeds
        mock_connection = Mock()
        mock_engine.connect.side_effect = [
            Exception("Database error"),  # First call fails
            mock_connection  # Second call succeeds
        ]
        mock_connection.execute.return_value = [{"result": 1}]
        
        # Call function with retry
        result = database_health_check(retry=True, max_retries=2, retry_delay=1)
        
        # Assertions
        assert result is True
        assert mock_engine.connect.call_count == 2
        mock_sleep.assert_called_once_with(1)
        mock_connection.close.assert_called_once()