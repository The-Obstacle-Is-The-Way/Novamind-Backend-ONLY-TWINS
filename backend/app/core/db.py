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
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
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
            yield session
        finally:
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