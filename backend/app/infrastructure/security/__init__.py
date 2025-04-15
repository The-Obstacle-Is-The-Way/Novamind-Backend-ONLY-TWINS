"""
Security infrastructure layer for the Novamind Digital Twin Platform.

This module serves as a bridge between the security core and application layers,
providing seamless integration with the clean architecture pattern.
"""

# PHI Security Components
from app.infrastructure.security.phi import LogSanitizer, PHIFormatter, PHIRedactionHandler
from app.infrastructure.security.phi.enhanced_phi_middleware import EnhancedPHIMiddleware

# Authentication Components
from app.infrastructure.security.auth import TokenAuthorizationError, PermissionType, RolePermission, JWTAuthMiddleware, MFAService

# JWT Components
from app.infrastructure.security.jwt import (
    TokenHandler, 
    JWTService, 
    JWTAuth,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user
)

# Encryption Components
from app.infrastructure.security.encryption import EncryptionService, EncryptionHandler, KeyRotationManager

# Password Components
from app.infrastructure.security.password import PasswordHandler, hash_data, secure_compare

# RBAC Components
from app.infrastructure.security.rbac import RoleBasedAccessControl, RoleAccessManager, RoleManager

# Rate Limiting Components
from app.infrastructure.security.rate_limiting import RateLimiter, EnhancedRateLimiter

# Audit Components  
from app.infrastructure.security.audit import AuditService

from .auth.authentication_service import AuthenticationService
from .auth.password_service import PasswordService
from .encryption.encryption_service import EncryptionService
from .jwt.jwt_service import JWTService

# PHIMiddleware is now in presentation layer, remove export from here
# from app.presentation.middleware.phi_middleware import PHIMiddleware

__all__ = [
    "AuthenticationService",
    "PasswordService",
    "EncryptionService",
    "JWTService",
#    "PHIMiddleware",
]