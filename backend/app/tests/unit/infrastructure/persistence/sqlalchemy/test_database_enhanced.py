"""Unit tests for enhanced database functionality in SQLAlchemy."""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.persistence.sqlalchemy.config.database import Database
from app.core.config.settings import Settings


class TestDatabase:
    """Test suite for Database class functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = MagicMock(spec=Settings)
        
        # Configure database settings
    settings.POSTGRES_USER = "test_user"
    settings.POSTGRES_PASSWORD = "test_password"
    settings.POSTGRES_SERVER = "localhost"
    settings.POSTGRES_PORT = "5432"
    settings.POSTGRES_DB = "test_db"
    settings.DB_ECHO = False
    settings.DB_POOL_SIZE = 5
    settings.DB_MAX_OVERFLOW = 10
    settings.DB_POOL_PRE_PING = True
    settings.SQLALCHEMY_DATABASE_URI = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
        
#     return settings # FIXME: return outside function
    
    @pytest.fixture
    def mock_engine(self):
        """Create a mock SQLAlchemy engine."""
        engine = MagicMock(spec=AsyncEngine)
        
        # Mock async execution context
    async_context = AsyncMock()
    engine.begin.return_value = async_context
    engine.connect.return_value = async_context
        
#     return engine # FIXME: return outside function
    
    @pytest.fixture
    def mock_session_maker(self):
        """Create a mock SQLAlchemy session maker."""
        session = AsyncMock()
        session_maker = MagicMock()
        session_maker.return_value = session
        
        # Ensure session methods are mocked properly
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
        
#     return session_maker # FIXME: return outside function
    
    def test_initialization(self, mock_settings):
        """Test Database initialization with settings."""
        with patch('app.core.config.settings.get_settings', return_value=mock_settings):
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
                # Initialize database
                db = Database()
                
                # Check engine initialization
    mock_create_engine.assert_called_once()
                
                # Verify URL and parameters for engine creation
    args, kwargs = mock_create_engine.call_args
                
                # Check DB URL construction
    assert args[0] == "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
                
                # Check engine setup
    assert kwargs["echo"] is False
    assert kwargs["pool_pre_ping"] is True
    
    @pytest.mark.asyncio()
    async def test_database_session_context_manager(self, mock_engine, mock_session_maker):
    """Test the database session context manager."""
    with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine',
    return_value=mock_engine):
    with patch('sqlalchemy.ext.asyncio.async_sessionmaker',
    return_value=mock_session_maker):
    db = Database()
    async with db.session() as session:
                    # Session should be returned by the factory
    assert session == mock_session_maker.return_value
                # Check session lifecycle methods were called
    mock_session_maker.return_value.commit.assert_called_once()
    mock_session_maker.return_value.close.assert_called_once()
    
    def test_get_engine(self):
        """Test getting the engine from the Database instance."""
        # Patch the engine creation used by Database.__init__
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
        mock_engine_instance = MagicMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine_instance
            
            # Reset the global instance to force re-initialization with mock
    from app.infrastructure.persistence.sqlalchemy.config import database
    database._db_instance = None
            
            # Get the database instance (which will now use the mocked engine)
    db_instance = database.get_db_instance()
            
            # Get engine from the instance
    engine = db_instance.engine
            
            # Check returned engine
    assert engine == mock_engine_instance
    mock_create_engine.assert_called_once()  # Ensure engine was created
    
    @pytest.mark.asyncio()
    async def test_connection_error_handling(self, mock_settings):
    """Test error handling for database connection failures."""
    with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
            # Simulate connection error
    mock_create_engine.side_effect = SQLAlchemyError("Connection failed")
            
            # Reset the global instance
    from app.infrastructure.persistence.sqlalchemy.config import database
    database._db_instance = None
            
            # Attempt to get database instance should raise the error
    with pytest.raises(SQLAlchemyError, match="Connection failed"):
    database.get_db_instance()
    
    @pytest.mark.asyncio()
    async def test_session_error_handling(self, mock_engine, mock_session_maker):
    """Test error handling within session context manager."""
    with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine',
    return_value=mock_engine):
    with patch('sqlalchemy.ext.asyncio.async_sessionmaker',
    return_value=mock_session_maker):
    db = Database()
                
                # Configure session to raise exception
    mock_session_maker.return_value.commit.side_effect = SQLAlchemyError("Transaction failed")
                
                # Session should handle the error and propagate it
    with pytest.raises(SQLAlchemyError, match="Transaction failed"):
    async with db.session() as session:
    pass  # This will attempt to commit and raise error
                
                # Should rollback on exception
    mock_session_maker.return_value.rollback.assert_called_once()
    mock_session_maker.return_value.close.assert_called_once()