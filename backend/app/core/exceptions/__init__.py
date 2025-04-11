# -*- coding: utf-8 -*-
"""
Core exceptions package.

This package contains all exceptions used throughout the application.
"""

from app.core.exceptions.base_exceptions import (
    ApplicationError,
    AuthenticationException,
    AuthorizationException,
    BaseException,
    BusinessRuleException,
    ConfigurationError,
    DatabaseException,
    ExternalServiceException,
    InitializationError,
    InvalidConfigurationError,
    ResourceNotFoundException,
    ResourceNotFoundError,
    SecurityException,
    ValidationException,
)

from app.core.exceptions.ml_exceptions import (
    InvalidRequestError,
    MLServiceError,
    ModelNotFoundError,
    ServiceUnavailableError,
    PHIDetectionError,
    MentalLLaMAServiceError,
    MentalLLaMAInferenceError,
    XGBoostServiceError,
    DigitalTwinError,
)

__all__ = [
    "ApplicationError",
    "AuthenticationException",
    "AuthorizationException",
    "BaseException",
    "BusinessRuleException",
    "ConfigurationError",
    "DatabaseException",
    "DigitalTwinError",
    "ExternalServiceException",
    "InitializationError",
    "InvalidConfigurationError",
    "InvalidRequestError",
    "MLServiceError",
    "MentalLLaMAInferenceError",
    "MentalLLaMAServiceError",
    "ModelNotFoundError",
    "PHIDetectionError",
    "ResourceNotFoundException",
    "ResourceNotFoundError",
    "SecurityException",
    "ServiceUnavailableError",
    "ValidationException",
    "XGBoostServiceError",
]