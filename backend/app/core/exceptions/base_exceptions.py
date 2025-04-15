# -*- coding: utf-8 -*-
"""
Base exceptions for the application.

This module defines the foundational exception classes that form the basis of the
application's exception hierarchy.
"""

from typing import Any, Dict, List, Optional, Union


class BaseException(Exception):
    """
    Base exception for all application exceptions.

    Attributes:
        message: A human-readable error message
        detail: Additional information about the error
        code: An error code for machine processing
    """

    def __init__(
        self,
        message: str,
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: Optional[str] = None,
    ):
        self.message = message
        self.detail = detail
        self.code = code
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message} - {self.detail}"
        return self.message


class ValidationException(BaseException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str = "Validation error",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "VALIDATION_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class ResourceNotFoundException(BaseException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "RESOURCE_NOT_FOUND",
    ):
        super().__init__(message=message, detail=detail, code=code)


class ResourceNotFoundError(BaseException):
    """
    Exception raised when a requested resource is not found.
    
    This is an alias for ResourceNotFoundException for backward compatibility.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "RESOURCE_NOT_FOUND",
    ):
        super().__init__(message=message, detail=detail, code=code)
        
        if " not found" not in message:
            self.message = f"{message} not found"


class AuthenticationException(BaseException):
    """Exception raised for authentication errors."""

    def __init__(
        self,
        message: str = "Authentication failed",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "AUTHENTICATION_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class AuthorizationException(BaseException):
    """Exception raised for authorization errors."""

    def __init__(
        self,
        message: str = "Not authorized",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "AUTHORIZATION_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class BusinessRuleException(BaseException):
    """Exception raised when a business rule is violated."""

    def __init__(
        self,
        message: str = "Business rule violation",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "BUSINESS_RULE_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class InitializationError(BaseException):
    """Exception raised when a service or component fails to initialize."""

    def __init__(
        self,
        message: str = "Failed to initialize",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "INITIALIZATION_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class ConfigurationError(BaseException):
    """Exception raised for configuration errors."""

    def __init__(
        self,
        message: str = "Configuration error",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "CONFIGURATION_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class ExternalServiceException(BaseException):
    """Exception raised when an external service call fails."""

    def __init__(
        self,
        message: str = "External service error",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "EXTERNAL_SERVICE_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class DatabaseException(BaseException):
    """Exception raised for database errors."""

    def __init__(
        self,
        message: str = "Database error",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "DATABASE_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class SecurityException(BaseException):
    """Exception raised for security-related errors."""

    def __init__(
        self,
        message: str = "Security error",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "SECURITY_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class ApplicationError(BaseException):
    """Base class for application-specific errors."""

    def __init__(
        self,
        message: str = "Application error",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "APPLICATION_ERROR",
    ):
        super().__init__(message=message, detail=detail, code=code)


class InvalidConfigurationError(BaseException):
    """Exception raised when configuration is invalid."""

    def __init__(
        self,
        message: str = "Invalid configuration",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        code: str = "INVALID_CONFIGURATION",
    ):
        super().__init__(message=message, detail=detail, code=code)


# --- Exceptions moved from standalone exceptions.py --- 

class HIPAAComplianceError(BusinessRuleException):
    """Exception raised for HIPAA compliance violations."""

    def __init__(
        self, 
        message: str = "HIPAA compliance violation",
        detail: Optional[Union[str, List[str], Dict[str, Any]]] = None,
        violation_type: Optional[str] = None,
        code: str = "HIPAA_COMPLIANCE_ERROR",
        **kwargs # Added to capture potential extra args from old definition
    ):
        # Pass relevant info to base, handle potential extra args if needed
        super().__init__(message=message, detail=detail, code=code)
        self.violation_type = violation_type # Store specific info

# Note: MentalLLaMAInferenceError was in exceptions.py but seems ML-specific.
# It likely belongs in ml_exceptions.py rather than base_exceptions.py.
# We will handle that separately if import errors for it persist.