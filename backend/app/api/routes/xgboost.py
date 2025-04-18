"""
Alias module for XGBoost DI dependencies used by integration tests.
"""

from app.infrastructure.di.container import get_service
from app.presentation.api.dependencies.auth import get_current_user, verify_provider_access

def get_xgboost_service():
    """Dependency override for XGBoost service."""
    return get_service("xgboost")

__all__ = ["get_xgboost_service", "get_current_user", "verify_provider_access"]