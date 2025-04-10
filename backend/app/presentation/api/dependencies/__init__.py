# -*- coding: utf-8 -*-
"""API Dependency Injection Modules."""

from .services import get_digital_twin_service, get_cache_service
from .database import get_db
from .auth import get_current_user # Removed get_current_provider

__all__ = [
    "get_digital_twin_service",
    "get_cache_service",
    "get_db",
    "get_current_user",
    # Removed get_current_provider
]