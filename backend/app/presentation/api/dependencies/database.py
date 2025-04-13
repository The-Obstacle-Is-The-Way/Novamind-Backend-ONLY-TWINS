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
from app.core.config import get_settings
settings = get_settings()

from typing import Optional, Dict, Any # Ensure Optional is imported
from app.core.utils.logging import get_logger
from app.domain.exceptions import DatabaseError
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_instance

logger = get_logger(__name__)

async def get_db() -> dict:
    """
    Provide an async database session for endpoints.

    This dependency yields a SQLAlchemy async session obtained from the
    infrastructure layer's session factory and ensures proper handling.
    
    The return type is deliberately set to dict to prevent FastAPI
    from trying to use AsyncSession in response models.

    Yields:
        AsyncSession: A database session that should not be exposed in responses,
                     but disguised with a dict return type annotation.
    """
    async for session in get_session_from_config():
        # Wrap the session to prevent it being used directly in response models
        try:
            # Yield the actual session, but with misleading type annotation
            # to prevent FastAPI from trying to include it in response model generation
            yield session
        finally:
            # The context manager from get_session_from_config handles closing.
            pass
            pass