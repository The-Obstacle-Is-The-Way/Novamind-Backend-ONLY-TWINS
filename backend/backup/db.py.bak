"""
Database connection utilities for SQLAlchemy.

This module provides the database engine, session management,
and connection utilities for the application.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


# Create the SQLAlchemy engine
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    future=True,
    pool_pre_ping=True
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