# -*- coding: utf-8 -*-
"""
SQLAlchemy database connection configuration.

This module provides async database session factory and connection pooling
for the SQLAlchemy ORM, configured according to the application settings.
"""

from typing import Optional, Callable, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from fastapi import Depends

from app.core.config import Settings
from app.core.utils.logging import get_logger
from app.infrastructure.persistence.sqlalchemy.config.base import Base


logger = get_logger(__name__)


class Database:
    """
    Database connection manager.
    
    This class manages a SQLAlchemy async engine and session factory,
    providing controlled access to database sessions.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the database with main application settings.
        
        Args:
            settings: Application settings object from app.core.config
        """
        self.settings = settings
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()
        
    def _create_engine(self):
        """
        Create the SQLAlchemy async engine using the main settings.
        
        Returns:
            SQLAlchemy async engine
        """
        # Use the assembled connection string directly from main settings
        connection_url = str(self.settings.SQLALCHEMY_DATABASE_URI)
        
        # Pooling configuration (using example defaults, ideally read from settings)
        # TODO: Consider adding POOL_SIZE, POOL_MAX_OVERFLOW etc. to main Settings
        pooling_args = {
            "poolclass": QueuePool,
            "pool_size": 5, 
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True
        }
            
        # Create engine
        return create_async_engine(
            connection_url,
            # Use ENVIRONMENT from main settings to control echo
            echo=self.settings.ENVIRONMENT == "development", 
            future=True,
            **pooling_args
        )
        
    def _create_session_factory(self):
        """
        Create the session factory for this engine.
        
        Returns:
            Async session factory
        """
        return async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
            class_=AsyncSession
        )
        
    @asynccontextmanager
    async def session(self):
        """
        Create a new session as an async context manager.
        
        Yields:
            SQLAlchemy AsyncSession
        """
        session = self.session_factory()
        try:
            yield session
        finally:
            await session.close()
            
    async def create_all(self):
        """Create all tables defined in the models."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def dispose(self):
        """Dispose the engine and all connections."""
        await self.engine.dispose()
        

# Global database instance
_db_instance = None


def get_db_instance() -> Database:
    """
    Get the database singleton instance.
    
    This function returns the global database instance, initializing it
    with main application settings if not already initialized.
    
    Returns:
        Database singleton instance
    """
    global _db_instance
    
    if _db_instance is None:
        from app.core.config import get_settings
        
        # Get the main application settings instance
        main_settings = get_settings()
        
        # Initialize Database with the main settings object
        _db_instance = Database(main_settings)
        logger.info("Database instance initialized using main application settings")
        
    return _db_instance


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session from the session factory.
    
    This function is used as a FastAPI dependency for database access
    in endpoint handlers.
    
    Yields:
        An async database session
    """
    db = get_db_instance()
    async with db.session() as session:
        yield session


def get_db_dependency() -> Callable:
    """
    Get the database dependency function.
    
    This function is used to provide the database dependency in FastAPI.
    It's also used for dependency overriding in tests.
    
    Returns:
        Database dependency function
    """
    return get_db_session


async def close_db_connections() -> None:
    """
    Close all database connections.
    
    This function should be called during application shutdown.
    """
    if _db_instance is not None:
        await _db_instance.dispose()
        logger.info("Database connections closed")
