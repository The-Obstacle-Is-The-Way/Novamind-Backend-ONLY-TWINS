"""
Database session management for the Novamind Digital Twin Platform.

This module provides functions for creating database connections
and dependency injection for FastAPI endpoints.
"""
import os
from typing import Generator, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging

# Import settings from the canonical location
from app.config.settings import get_settings

# Call the function to get the settings object
settings = get_settings()

# Create async SQLAlchemy engine using the DATABASE_URL from settings.
# The settings object will have the correct URL loaded based on the environment
# (e.g., from .env.test during testing, or .env/environment variables otherwise).

# Ensure DATABASE_URL is available before creating the engine
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in settings. Cannot create database engine.")

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,       # Use pool settings from config
    max_overflow=settings.DB_MAX_OVERFLOW, # Use pool settings from config
    echo=settings.DATABASE_ECHO,           # Use echo setting from config
    future=True,                           # Recommended for SQLAlchemy 2.0 async
    # Add SSL context if configured and if it's a PostgreSQL connection
    # Check if the URL indicates PostgreSQL before attempting SSL connect_args
    connect_args=(
        {
            "ssl": {
                "ca_certs": settings.DATABASE_SSL_CA,
                "ssl_mode": settings.DATABASE_SSL_MODE
                # "check_hostname": settings.DATABASE_SSL_VERIFY is not False # Add if needed
            } if settings.DATABASE_SSL_MODE else None
        }
        if settings.DATABASE_URL.startswith("postgresql")
        else {}
    )
)

# Create session factory for creating AsyncSession instances
session_local = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

logger = logging.getLogger(__name__)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get a database session.
    
    Yields a new database session for each request, ensuring the session is
    properly closed after the request is completed, even if an exception occurs.
    
    Yields:
        AsyncSession: Database session
    """
    async with session_local() as session:
        try:
            yield session
            # Session will be committed if no exception occurs
            await session.commit()
        except Exception:
            # Roll back session on exception
            await session.rollback()
            raise
        finally:
            # Close session regardless of outcome
            await session.close()