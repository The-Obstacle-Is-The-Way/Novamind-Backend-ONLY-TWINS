"""
Authentication components for the Novamind Digital Twin Backend.

This module provides authentication services, middleware, and handlers
for user authentication, MFA, and session management.
"""

from app.infrastructure.security.auth.auth import TokenAuthorizationError, PermissionType, RolePermission, AuthorizationScope
from app.infrastructure.security.auth.auth_middleware import JWTAuthMiddleware
from app.infrastructure.security.auth.mfa_service import MFAService 