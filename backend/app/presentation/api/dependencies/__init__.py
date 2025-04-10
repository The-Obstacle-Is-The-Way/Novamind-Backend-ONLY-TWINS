# -*- coding: utf-8 -*-
"""API Dependency Injection Modules."""

from .services import get_digital_twin_service, get_cache_service, get_pat_service # Added get_pat_service
from .database import get_db
from .auth import get_current_user

__all__ = [
    "get_digital_twin_service",
    "get_cache_service",
    "get_db",
    "get_current_user",
    "get_pat_service", # Added get_pat_service
]