"""
Response utilities for FastAPI endpoints.

This module provides tools to ensure proper response handling,
preventing database sessions and other non-serializable objects
from being exposed in API responses.
"""
from typing import Any, Dict, Optional, Type, TypeVar, cast

from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T', bound=BaseModel)

def prevent_session_exposure(response_model: Optional[Type[T]] = None) -> Dict[str, Any]:
    """
    FastAPI dependency that ensures no AsyncSession objects are exposed in responses.
    
    This is a placeholder for endpoints to make it clear that they're not 
    leaking database sessions. It doesn't actually do anything at runtime,
    but documents the intent.
    
    Returns:
        Empty dict as a placeholder
    """
    return {}

def ensure_serializable_response(data: Any) -> Any:
    """
    Ensure that the response data is serializable.
    
    This utility function checks if the response data contains any AsyncSession
    objects and removes them, to prevent FastAPI serialization errors.
    
    Args:
        data: The data to sanitize
        
    Returns:
        Sanitized data without any AsyncSession objects
    """
    if isinstance(data, dict):
        return {k: ensure_serializable_response(v) for k, v in data.items() 
                if not isinstance(v, AsyncSession)}
    elif isinstance(data, list):
        return [ensure_serializable_response(item) for item in data]
    elif hasattr(data, '__dict__'):
        # For objects, filter out AsyncSession attributes
        return {k: ensure_serializable_response(v) for k, v in data.__dict__.items() 
                if not isinstance(v, AsyncSession)}
    else:
        return data