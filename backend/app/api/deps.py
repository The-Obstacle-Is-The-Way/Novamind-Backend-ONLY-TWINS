"""
FastAPI dependency injection module.

This module re-exports all dependencies for API routes to use,
providing a single import point for route dependencies.
"""

from app.api.dependencies.auth import (
    oauth2_scheme,
    get_current_token_payload,
    get_current_user,
    get_current_active_clinician,
    get_current_active_admin,
    get_current_user_dict,
    get_optional_user
)

from app.api.dependencies.services import (
    get_sequence_repository,
    get_event_repository,
    get_xgboost_service,
    get_temporal_neurotransmitter_service
)

from app.api.dependencies.ml import (
    get_pat_factory,
    get_digital_twin_service,
    get_mentallama_service
)

from app.core.db import get_session
from app.infrastructure.repositories.user_repository import get_user_repository

# Re-export dependencies for ease of use
# Authentication & Authorization dependencies
get_current_user_id = get_current_user_dict

# Helper to get a more readable name for require_clinician_role
require_clinician_role = get_current_active_clinician

# Helper to get a more readable name for require_admin_role
require_admin_role = get_current_active_admin

__all__ = [
    # Auth dependencies
    "oauth2_scheme",
    "get_current_token_payload",
    "get_current_user",
    "get_current_user_id",
    "get_current_active_clinician",
    "get_current_active_admin",
    "get_current_user_dict",
    "get_optional_user",
    "require_clinician_role",
    "require_admin_role",
    
    # Service dependencies
    "get_sequence_repository",
    "get_event_repository",
    "get_xgboost_service",
    "get_temporal_neurotransmitter_service",
    
    # ML dependencies
    "get_pat_factory",
    "get_digital_twin_service",
    "get_mentallama_service",
    
    # Database dependencies
    "get_session",
    "get_user_repository",
]