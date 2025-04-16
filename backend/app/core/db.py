"""
Database connection utilities for SQLAlchemy.

This module provides the database engine, session management,
and connection utilities for the application.
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
import os
import logging

# Use the new canonical config location
from app.config.settings import get_settings, Settings

logger = logging.getLogger(__name__)

# Create the declarative base model
Base = declarative_base()

# --- Engine and Session Factory Creation (Deferred) ---

# Global variable to hold the engine once created
_engine: Optional[AsyncEngine] = None

def get_engine(settings: Optional[Settings] = None) -> AsyncEngine:
    """Gets or creates the SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        if settings is None:
            settings = get_settings()
        
        database_url = settings.DATABASE_URL
        if database_url is None:
            raise ValueError(
                "DATABASE_URL is not configured. "
                "Please check environment variables or .env file."
            )
        
        # Ensure the URL is a string and has the async driver
        db_url_str = str(database_url)
        if db_url_str.startswith('postgresql://'):
            db_url_str = db_url_str.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif db_url_str.startswith('sqlite://'):
             # Ensure aiosqlite is used for async SQLite
             if not db_url_str.startswith('sqlite+aiosqlite://'):
                 db_url_str = db_url_str.replace('sqlite://', 'sqlite+aiosqlite://', 1)

        logger.info(f"Creating database engine for URL: {db_url_str[:db_url_str.find(':')]}:***") # Log safely
        try:
            _engine = create_async_engine(
                db_url_str,
                echo=settings.DATABASE_ECHO,
                future=True,
                pool_pre_ping=True,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW
            )
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}", exc_info=True)
            raise
    return _engine

# Global variable for session factory
_async_session_local: Optional[sessionmaker] = None

def get_session_local(engine: Optional[AsyncEngine] = None) -> sessionmaker:
    """Gets or creates the async session factory."""
    global _async_session_local
    if _async_session_local is None:
        if engine is None:
             engine = get_engine() # Get engine using current settings
             
        _async_session_local = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
    return _async_session_local

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a transactional scope around a series of operations.
    Ensures session is created using the current engine/settings.
    """
    session_factory = get_session_local() # Get the factory
    async with session_factory() as session:
        try:
            yield session
            # For transactional behavior, uncomment commit/rollback
            # await session.commit() 
        except Exception:
            # await session.rollback()
            logger.error("Session rollback due to exception", exc_info=True)
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """
    Initialize the database with all defined models.
    Ensures engine is created before running metadata commands.
    """
    settings = get_settings()
    # Determine if we're in test mode
    is_test = os.environ.get("TESTING", "0").lower() in ("1", "true", "yes") or settings.ENVIRONMENT == "test"
    
    engine = get_engine(settings) # Get engine using current settings
    
    async with engine.begin() as conn:
        logger.info("Initializing database...")
        # Conditional table creation based on environment
        if settings.ENVIRONMENT == "development" or is_test:
            logger.info("Dropping all tables (dev/test environment)...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Creating all tables (dev/test environment)...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created.")
        else:
             logger.info("Skipping table creation/deletion in non-dev/test environment.")

async def dispose_engine() -> None:
    """Dispose of the engine, closing connection pools."""
    global _engine
    if _engine:
        logger.info("Disposing database engine.")
        await _engine.dispose()
        _engine = None # Reset global engine
        logger.info("Database engine disposed.")
    else:
        logger.info("Database engine already disposed or never created.")