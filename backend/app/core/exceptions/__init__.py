# -*- coding: utf-8 -*-
"""
Core Exceptions Package.

This package defines exceptions used throughout the application.
"""

# Import specific exception modules
from app.core.exceptions.auth_exceptions import *
from app.core.exceptions.base_exceptions import *
from app.core.exceptions.ml_exceptions import *

# Export all exception classes
__all__ = [
    # Auth exceptions
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    "InvalidTokenError",
    
    # Base exceptions
    "ApplicationError",
    "ValidationError",
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "ConfigurationError",
    "InvalidConfigurationError",
    
    # ML exceptions
    "MLServiceError",
    "PHIDetectionError",
    "MentaLLaMAServiceError",
    "XGBoostServiceError",
    "InvalidRequestError",
    "ModelNotFoundError",
    "ServiceUnavailableError"
]