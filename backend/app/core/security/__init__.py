"""
Security package for the Novamind Digital Twin Platform.

This package provides security-related functionality including:
1. Authentication and authorization
2. Role-based access control
3. JWT token management
4. Password hashing and verification
5. HIPAA compliant PHI protection
"""

from app.core.security.roles import Role
from app.core.security.auth import (
    get_current_user,
    get_current_user_id,
    has_role,
    has_permission,
)

__all__ = [
    "Role",
    "get_current_user",
    "get_current_user_id",
    "has_role",
    "has_permission",
]