# -*- coding: utf-8 -*-
"""
Database Dependencies for FastAPI.

This module provides dependency functions for database sessions
to be injected into FastAPI endpoints.
"""

from typing import Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.sqlalchemy.config.database import create_async_session
from app.core.config import get_app_settings


async def get_db_session() -> Generator[AsyncSession, None, None]:
    """
    Provide an async database session for endpoints.
    
    This dependency yields a SQLAlchemy async session that automatically
    handles commit/rollback and session closing based on the request lifecycle.
    
    Yields:
        AsyncSession: A database session with transaction handling
    """
    session = create_async_session(get_app_settings())
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()