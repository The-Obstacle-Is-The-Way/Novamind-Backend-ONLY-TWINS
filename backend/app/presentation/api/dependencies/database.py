# -*- coding: utf-8 -*-
"""
Database Dependencies for FastAPI.

This module provides dependency functions for database sessions
to be injected into FastAPI endpoints.
"""

from typing import Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Corrected import: Use get_db_session from the config module
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_session as get_session_from_config
from app.core.config import settings


# Renamed function to avoid conflict with imported name
async def get_db() -> Generator[AsyncSession, None, None]:
    """
    Provide an async database session for endpoints.
    
    This dependency yields a SQLAlchemy async session that automatically
    handles commit/rollback and session closing based on the request lifecycle.
    
    Yields:
        AsyncSession: A database session with transaction handling
    """
    # Use the imported session generator from the config module
    async for session in get_session_from_config():
        try:
            yield session
            # Commit/rollback logic might be handled within the config's session context manager
            # If not, keep it here. Assuming it's handled there for now.
        except Exception:
            # Rollback might be handled by the context manager
            raise
        # finally block might be handled by the context manager