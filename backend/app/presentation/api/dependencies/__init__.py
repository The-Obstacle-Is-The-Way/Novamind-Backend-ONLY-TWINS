# -*- coding: utf-8 -*-
"""API Dependency Injection Modules."""

from fastapi import Depends # Add Depends import

from app.infrastructure.di.container import get_service # Import get_service
from app.domain.repositories.biometric_alert_repository import BiometricAlertRepository # Import repository type

from .services import get_digital_twin_service, get_cache_service, get_pat_service # Added get_pat_service
from .database import get_db
from .auth import get_current_user

# Define repository dependency getter
def get_alert_repository() -> BiometricAlertRepository:
    """Dependency function to get biometric alert repository."""
    # Use Depends(get_service(...)) pattern
    return Depends(get_service(BiometricAlertRepository))

__all__ = [
    "get_digital_twin_service",
    "get_cache_service",
    "get_db",
    "get_current_user",
    "get_pat_service", # Added get_pat_service
    "get_alert_repository", # Export the new getter
]