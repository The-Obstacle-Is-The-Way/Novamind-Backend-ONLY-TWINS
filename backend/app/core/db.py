"""
Database connection utilities for SQLAlchemy.

This module provides the database engine, session management,
and connection utilities for the application.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings
import os

# Create the declarative base model
Base = declarative_base()

# Determine if we're in test mode
is_test = os.environ.get("TESTING", "0").lower() in ("1", "true", "yes")

# Create the SQLAlchemy engine with appropriate driver based on environment
database_url = settings.SQLALCHEMY_DATABASE_URI

# Ensure async driver is used
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
elif database_url.startswith('sqlite://'):
    database_url = database_url.replace('sqlite://', 'sqlite+aiosqlite://', 1)

# Create the engine with proper async URL
engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_session() -> AsyncSession:
    """
    Get a database session for use in a FastAPI dependency.
    
    This creates a new session for each request and closes it when the request is complete.
    
    Returns:
        AsyncSession: An asynchronous SQLAlchemy session
    """
    async with AsyncSessionLocal() as session:
        try:
            # Make sure the session isn't exposed directly in response models
            yield session
        finally:
            # Clean up session resources
            await session.close()


async def init_db() -> None:
    """
    Initialize the database with all defined models.
    
    This is called at application startup to create any missing tables.
    """
    async with engine.begin() as conn:
        # Only create tables in development mode, not in production
        if settings.ENVIRONMENT == "development" or is_test:
            await conn.run_sync(Base.metadata.create_all)