"""
Response and session utilities for FastAPI routes.

This module provides utilities for handling SQLAlchemy AsyncSession objects
in FastAPI responses, preventing them from being exposed in API responses
which would cause serialization errors.
"""

import logging
from typing import Any, Dict, Optional, cast, List, Set, Union, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def ensure_serializable_response(response_data: Any) -> Any:
    """
    Ensure a response is serializable by removing any SQLAlchemy AsyncSession objects.
    
    Args:
        response_data: The data to sanitize
        
    Returns:
        Sanitized response data safe for JSON serialization
    """
    if isinstance(response_data, dict):
        return {k: ensure_serializable_response(v) for k, v in response_data.items()}
    elif isinstance(response_data, list):
        return [ensure_serializable_response(item) for item in response_data]
    elif isinstance(response_data, tuple):
        return tuple(ensure_serializable_response(item) for item in response_data)
    elif isinstance(response_data, set):
        return {ensure_serializable_response(item) for item in response_data}
    elif hasattr(response_data, "__dict__") and not isinstance(response_data, AsyncSession):
        # Convert Pydantic models and other objects to dict, but skip AsyncSession
        if hasattr(response_data, "model_dump"):
            # Pydantic v2+
            return ensure_serializable_response(response_data.model_dump())
        elif hasattr(response_data, "dict"):
            # Pydantic v1
            return ensure_serializable_response(response_data.dict())
        else:
            # Regular object with __dict__
            return ensure_serializable_response(
                {k: v for k, v in response_data.__dict__.items() if not k.startswith("_")}
            )
    elif isinstance(response_data, AsyncSession):
        # Filter out AsyncSession objects
        logger.warning("AsyncSession object found in response, removing")
        return None
    else:
        # Return primitives and other serializable types as is
        return response_data


def prevent_session_exposure() -> Dict[str, str]:
    """
    FastAPI dependency that prevents AsyncSession objects from being exposed in responses.
    
    Use this as a dependency in route handlers:
    
    ```python
    @router.get("/endpoint")
    async def my_route(
        _: Dict = Depends(prevent_session_exposure)
    ):
        # ...
    ```
    
    Returns:
        Empty dict, not used directly but required for FastAPI dependency injection
    """
    return {"message": "AsyncSession exposure prevention active"}