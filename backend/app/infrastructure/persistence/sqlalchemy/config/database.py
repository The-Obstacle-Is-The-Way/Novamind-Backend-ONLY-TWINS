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

from app.core.database_settings import DatabaseSettings
from app.core.utils.logging import get_logger
from app.infrastructure.persistence.sqlalchemy.config.base import Base


logger = get_logger(__name__)


class Database:
    """
    Database connection manager.
    
    This class manages a SQLAlchemy async engine and session factory,
    providing controlled access to database sessions.
    """
    
    def __init__(self, settings: DatabaseSettings):
        """
        Initialize the database with settings.
        
        Args:
            settings: Database connection settings
        """
        self.settings = settings
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()
        
    def _create_engine(self):
        """
        Create the SQLAlchemy async engine.
        
        Returns:
            SQLAlchemy async engine
        """
        connection_url = self.settings.get_connection_string()
        
        # Determine pooling configuration
        pooling_args = {}
        if self.settings.DISABLE_POOLING:
            pooling_args["poolclass"] = NullPool
        else:
            pooling_args.update({
                "poolclass": QueuePool,
                "pool_size": self.settings.POOL_SIZE,
                "max_overflow": self.settings.POOL_MAX_OVERFLOW,
                "pool_timeout": self.settings.POOL_TIMEOUT,
                "pool_recycle": self.settings.POOL_RECYCLE,
                "pool_pre_ping": True
            })
            
        # Create engine
        return create_async_engine(
            connection_url,
            echo=self.settings.ECHO_SQL,
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
    with settings from environment if not already initialized.
    
    Returns:
        Database singleton instance
    """
    global _db_instance
    
    if _db_instance is None:
        from app.core.config import get_app_settings
        
        # Load database settings from app settings
        db_settings = DatabaseSettings(
            HOST=get_app_settings().POSTGRES_SERVER,
            PORT=get_app_settings().POSTGRES_PORT,
            USERNAME=get_app_settings().POSTGRES_USER,
            PASSWORD=get_app_settings().POSTGRES_PASSWORD,
            DATABASE=get_app_settings().POSTGRES_DB,
            ECHO_SQL=get_app_settings().DEBUG,
            # Additional settings can be loaded here
        )
        
        _db_instance = Database(db_settings)
        logger.info("Database instance initialized")
        
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
