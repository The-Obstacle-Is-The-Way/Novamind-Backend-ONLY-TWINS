"""
Security infrastructure layer for the Novamind Digital Twin Platform.

This module serves as a bridge between the security core and application layers,
providing seamless integration with the clean architecture pattern.
"""

# PHI Security Components
from app.infrastructure.security.phi import LogSanitizer, PHIFormatter, PHIRedactionHandler

# Authentication Components
# Only import what's directly exported from auth/__init__.py
# from app.infrastructure.security.auth import TokenAuthorizationError, PermissionType, RolePermission, JWTAuthMiddleware, MFAService
from app.infrastructure.security.auth import MFAService 

# JWT Components
# Only import JWTService from the jwt package
# from app.infrastructure.security.jwt import (
#     TokenHandler, 
#     JWTService, 
#     JWTAuth,
#     create_access_token,
#     create_refresh_token,
#     verify_token,
#     get_current_user
# )
from app.infrastructure.security.jwt import JWTService

# Encryption Components
# Import BaseEncryptionService as EncryptionService for consistency elsewhere maybe?
# Or just import BaseEncryptionService directly.
# from app.infrastructure.security.encryption import EncryptionService, EncryptionHandler, KeyRotationManager
from app.infrastructure.security.encryption import BaseEncryptionService

# Password Components
# Import correct functions from password package
# from app.infrastructure.security.password import PasswordHandler, hash_data, secure_compare
from app.infrastructure.security.password import PasswordHandler, get_password_hash, verify_password

# RBAC Components
# Only import RBACService as Action and Resource are not exported from rbac/__init__
from app.infrastructure.security.rbac import RBACService

# Rate Limiting Components
# from app.infrastructure.security.rate_limiting import RateLimiter, EnhancedRateLimiter # Incorrect imports
from app.infrastructure.security.rate_limiting import DistributedRateLimiter # Import the correct class

# Audit Components  
from app.infrastructure.security.audit import AuditLogger

from .auth.authentication_service import AuthenticationService
from .auth.password_service import PasswordService
from .encryption.base_encryption_service import BaseEncryptionService
from .jwt.jwt_service import JWTService

# PHIMiddleware is now in presentation layer, remove export from here
# from app.presentation.middleware.phi_middleware import PHIMiddleware

__all__ = [
    "AuthenticationService",
    "PasswordService",
    "BaseEncryptionService",
    "JWTService",
#    "PHIMiddleware",
]