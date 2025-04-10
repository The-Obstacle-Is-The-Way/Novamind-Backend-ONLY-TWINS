"""
Database session management for the Novamind Digital Twin Platform.

This module provides functions for creating database connections
and dependency injection for FastAPI endpoints.
"""
import os
from typing import Generator, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config.settings import settings


# Check if we're in test mode
is_test_mode = os.environ.get("TESTING") == "1"

# Create async SQLAlchemy engine with pooling configuration
if is_test_mode:
    # Use aiosqlite for testing to avoid requirement for actual PostgreSQL
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=settings.DEBUG,
        future=True,
    )
else:
    # Use actual PostgreSQL database for production/development
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=settings.DEBUG,
        future=True,
    )

# Create session factory for creating AsyncSession instances
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get a database session.
    
    Yields a new database session for each request, ensuring the session is
    properly closed after the request is completed, even if an exception occurs.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
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