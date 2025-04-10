# -*- coding: utf-8 -*-
"""
Database Dependencies for FastAPI.

This module provides dependency functions for database sessions
to be injected into FastAPI endpoints.
"""

from typing import Generator, AsyncGenerator # Ensure AsyncGenerator is imported

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Corrected import: Use get_db_session from the config module
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_session as get_session_from_config
from app.core.config import settings


# Renamed function to avoid conflict with imported name
from typing import Optional # Ensure Optional is imported

async def get_db() -> AsyncGenerator[AsyncSession, None]: # Yield AsyncSession directly
    """
    Provide an async database session for endpoints.

    This dependency yields a SQLAlchemy async session obtained from the
    infrastructure layer's session factory and ensures proper handling.

    Yields:
        AsyncSession: A database session.
    """
    async for session in get_session_from_config():
        yield session
        # The context manager from get_session_from_config handles closing.
        break # Ensure we only yield once per request cycle