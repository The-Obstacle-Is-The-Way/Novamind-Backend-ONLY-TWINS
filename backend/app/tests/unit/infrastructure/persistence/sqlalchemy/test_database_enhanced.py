# -*- coding: utf-8 -*-
"""
Enhanced unit tests for the SQLAlchemy database configuration.

This test suite provides comprehensive coverage for the database layer,
ensuring secure connection management and proper session handling.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.persistence.sqlalchemy.config.database import (
    Database,
    Base,
    get_db_dependency,
    get_session,
    create_tables,
    get_engine,
    db
)


@pytest.mark.db_required
class TestDatabase:
    """Comprehensive tests for the Database class and database utilities."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create a mock settings object with database configuration."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.settings') as mock_settings:
            # Configure database settings
            mock_settings.database.POSTGRES_USER = "test_user"
            mock_settings.database.POSTGRES_PASSWORD = "test_password"
            mock_settings.database.POSTGRES_HOST = "localhost"
            mock_settings.database.POSTGRES_PORT = "5432"
            mock_settings.database.POSTGRES_DB = "test_db"
            mock_settings.database.SQLALCHEMY_POOL_SIZE = 5
            mock_settings.database.SQLALCHEMY_MAX_OVERFLOW = 10
            mock_settings.database.SQLALCHEMY_POOL_TIMEOUT = 30
            mock_settings.database.SQLALCHEMY_ECHO = False
            mock_settings.database.ECHO = False
            mock_settings.database.POOL_PRE_PING = True
            mock_settings.database.POOL_SIZE = 5
            mock_settings.database.MAX_OVERFLOW = 10
            mock_settings.database.POOL_RECYCLE = 3600
            mock_settings.database.DB_ENGINE = "postgresql+asyncpg"
            mock_settings.database.DB_USER = "test_user"
            mock_settings.database.DB_PASSWORD = "test_password"
            mock_settings.database.DB_HOST = "localhost"
            mock_settings.database.DB_PORT = "5432"
            mock_settings.database.DB_NAME = "test_db"
            mock_settings.database.URL = None
            yield mock_settings
    
    @pytest.fixture
    def mock_engine(self):
        """Create a mock SQLAlchemy engine."""
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()
        mock_engine.sync_engine = MagicMock()
        mock_engine.begin = AsyncMock()
        # Setup context manager for begin() method
        mock_engine.begin.return_value.__aenter__.return_value = MagicMock()
        mock_engine.begin.return_value.__aexit__.return_value = None
        return mock_engine
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        return mock_session
    
    @pytest.fixture
    def mock_session_maker(self, mock_session):
        """Create a mock session maker function."""
        mock_maker = MagicMock()
        mock_maker.return_value = mock_session
        return mock_maker
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_database_initialization(self, mock_settings):
        """Test database class initialization."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            
            # Initialize database
            db = Database()
            
            # Check that engine was created with correct URL and parameters
            mock_create_engine.assert_called_once()
            args, kwargs = mock_create_engine.call_args
            
            # Check DB URL construction
            assert args[0] == "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
            
            # Check engine setup
            assert kwargs["echo"] is False
            assert kwargs["pool_pre_ping"] is True
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_database_session_context_manager(self, mock_engine, mock_session_maker):
        """Test the database session context manager."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine',
                  return_value=mock_engine):
            with patch('sqlalchemy.ext.asyncio.async_sessionmaker', return_value=mock_session_maker):
                db = Database()
                async with db.session() as session:
                    # Session should be returned by the factory
                    assert session == mock_session_maker.return_value
                
                # Check session lifecycle methods were called
                mock_session_maker.return_value.commit.assert_called_once()
                mock_session_maker.return_value.close.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_database_dispose(self, mock_engine):
        """Test the database engine disposal."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine',
                  return_value=mock_engine):
            db = Database()
            
            # Dispose engine
            await db.dispose()
            
            # Check that engine was disposed
            mock_engine.dispose.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_get_db_dependency(self, mock_engine, mock_session_maker):
        """Test the get_db dependency injection function."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.Database') as MockDatabase:
            mock_db = MagicMock()
            MockDatabase.return_value = mock_db
            
            mock_session = MagicMock()
            
            # Setup the context manager behavior for session
            @asynccontextmanager
            async def mock_session_context():
                yield mock_session
            
            mock_db.session.return_value = mock_session_context()
            
            # Get dependency function
            db_dependency = get_db_dependency()
            
            # Test the dependency function
            db_gen = db_dependency()
            session = await db_gen.__anext__()
            
            # Check returned session
            assert session == mock_session
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_create_tables(self, mock_engine):
        """Test table creation function."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.get_engine',
                  return_value=mock_engine):
            with patch('sqlalchemy.ext.asyncio.AsyncEngine.begin') as mock_begin:
                # Mock the async context manager
                mock_connection = MagicMock()
                mock_begin.return_value.__aenter__.return_value = mock_connection
                mock_begin.return_value.__aexit__.return_value = None
            
                with patch('app.infrastructure.persistence.sqlalchemy.config.database.Base.metadata.create_all') as mock_create_all:
                    # Call create_tables
                    await create_tables()
                    
                    # Check table creation occurred
                    mock_create_all.assert_called_once_with(mock_connection)
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_get_engine(self):
        """Test engine creation utility function."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            
            # Initialize a new database singleton
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.db', MagicMock()) as mock_db:
                mock_db.engine = mock_engine
                
                # Get engine
                engine = get_engine()
                
                # Check returned engine
                assert engine == mock_engine
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_connection_error_handling(self, mock_settings):
        """Test error handling for database connection failures."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
            # Simulate connection error
            mock_create_engine.side_effect = SQLAlchemyError("Connection failed")
            
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.logger') as mock_logger:
                # Attempt to initialize database
                with pytest.raises(SQLAlchemyError):
                    db = Database()
                
                # Check error was logged
                mock_logger.error.assert_called_once()
                assert "Failed to initialize database engine" in mock_logger.error.call_args[0][0]
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_session_exception_handling(self, mock_engine, mock_session_maker):
        """Test session exception handling in the context manager."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine',
                  return_value=mock_engine):
            # Create a session that raises an exception
            mock_session = MagicMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Query failed"))
            
            with patch('sqlalchemy.ext.asyncio.async_sessionmaker', return_value=lambda: mock_session):
                db = Database()
                
                # Test session with exception
                with pytest.raises(SQLAlchemyError):
                    async with db.session() as session:
                        await session.execute("SELECT 1")
                
                # Verify rollback was called
                mock_session.rollback.assert_called_once()
                mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_pool_configuration(self, mock_settings):
        """Test database pool configuration."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
            # Initialize database
            db = Database()
            
            # Check engine configuration
            mock_create_engine.assert_called_once()
            kwargs = mock_create_engine.call_args[1]
            assert kwargs["pool_size"] == mock_settings.database.POOL_SIZE
            assert kwargs["max_overflow"] == mock_settings.database.MAX_OVERFLOW
            assert kwargs["pool_recycle"] == mock_settings.database.POOL_RECYCLE
            assert kwargs["echo"] == mock_settings.database.ECHO
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_test_mode_configuration(self, mock_settings):
        """Test database configuration in test mode."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
            # Set test mode
            mock_settings.database.URL = "sqlite+aiosqlite:///:memory:"
            
            # Initialize database
            db = Database()
            
            # Check engine configuration
            mock_create_engine.assert_called_once()
            args, kwargs = mock_create_engine.call_args
            
            # Should not have pool settings for SQLite
            assert "pool_size" not in kwargs
            assert "max_overflow" not in kwargs
            assert "pool_recycle" not in kwargs
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_get_session_generator(self, mock_engine, mock_session_maker):
        """Test the get_session generator function."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.db') as mock_db:
            mock_session = MagicMock()
            
            # Setup the context manager behavior for session
            @asynccontextmanager
            async def mock_session_context():
                yield mock_session
            
            mock_db.session.return_value = mock_session_context()
            
            # Use get_session
            session_gen = get_session()
            session = await session_gen.__anext__()
            
            # Check returned session
            assert session == mock_session


# Need to define asynccontextmanager for our test
class asynccontextmanager:
    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args, **kwargs):
        return _AsyncContextManager(self.func(*args, **kwargs))


class _AsyncContextManager:
    def __init__(self, gen):
        self.gen = gen
    
    async def __aenter__(self):
        try:
            return await self.gen.__anext__()
        except StopAsyncIteration:
            raise RuntimeError("Generator didn't yield")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                await self.gen.__anext__()
            except StopAsyncIteration:
                return
            else:
                raise RuntimeError("Generator didn't stop")
        else:
            try:
                await self.gen.athrow(exc_type, exc_val, exc_tb)
            except StopAsyncIteration:
                return True
            except BaseException as e:
                if e is not exc_val:
                    raise
                return False