"""
Database connection utilities for SQLAlchemy.

This module provides the database engine, session management,
and connection utilities for the application.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


# Determine if we're in a test environment
in_test_environment = os.environ.get("TESTING", "").lower() in ("true", "1", "yes")

# Create the SQLAlchemy engine
if in_test_environment:
    # Use SQLite with aiosqlite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        # SQLite-specific connect args
        connect_args={"check_same_thread": False}
    )
else:
    # Use PostgreSQL with asyncpg for production
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30
    )

# Create a session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_session() -> AsyncSession:
    """
    Get an asynchronous database session.
    
    This dependency will be used in FastAPI to provide database sessions
    to API endpoints. It ensures proper session cleanup after use.
    
    Returns:
        SQLAlchemy AsyncSession 
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()