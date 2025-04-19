"""
Alias module for XGBoost DI dependencies used by integration tests.
"""

from fastapi import Depends
from app.infrastructure.di.container import get_service
from app.core.services.ml.xgboost.interface import XGBoostInterface
from app.presentation.api.dependencies.auth import get_current_user, verify_provider_access

def get_xgboost_service(
    service: XGBoostInterface = Depends(get_service)
) -> XGBoostInterface:
    """Dependency override for XGBoost service. Uses DI container via get_service."""
    return service

__all__ = ["get_xgboost_service", "get_current_user", "verify_provider_access"]