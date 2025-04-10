# -*- coding: utf-8 -*-
"""
Base Exception Classes.

This module defines base exceptions used throughout the application.
"""


class ApplicationError(Exception):
    """Base class for all application-specific exceptions."""
    
    def __init__(self, message: str = "An application error occurred", *args, **kwargs):
        """
        Initialize application error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        self.message = message
        super().__init__(message, *args)


class ValidationError(ApplicationError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str = "Data validation error", errors: dict = None, *args, **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            errors: Dictionary of field errors
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        self.errors = errors or {}
        super().__init__(message, *args, **kwargs)


class ResourceNotFoundError(ApplicationError):
    """Exception raised when a resource cannot be found."""
    
    def __init__(self, resource_type: str = "Resource", resource_id: str = None, *args, **kwargs):
        """
        Initialize resource not found error.
        
        Args:
            resource_type: Type of resource that was not found
            resource_id: ID of resource that was not found
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, *args, **kwargs)


class ResourceAlreadyExistsError(ApplicationError):
    """Exception raised when attempting to create a resource that already exists."""
    
    def __init__(self, resource_type: str = "Resource", resource_id: str = None, *args, **kwargs):
        """
        Initialize resource already exists error.
        
        Args:
            resource_type: Type of resource that already exists
            resource_id: ID of resource that already exists
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        message = f"{resource_type} already exists"
        if resource_id:
            message += f": {resource_id}"
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, *args, **kwargs)


class ConfigurationError(ApplicationError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str = "Configuration error", *args, **kwargs):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class InvalidConfigurationError(ConfigurationError):
    """Exception raised for invalid configuration settings."""
    
    def __init__(self, message: str = "Invalid configuration setting", setting: str = None, *args, **kwargs):
        """
        Initialize invalid configuration error.
        
        Args:
            message: Error message
            setting: The specific configuration setting that is invalid
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        if setting:
            message = f"{message}: {setting}"
        self.setting = setting
        super().__init__(message, *args, **kwargs)


class AuthenticationError(ApplicationError):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", *args, **kwargs):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class AuthorizationError(ApplicationError):
    """Exception raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed", required_permissions: list = None, *args, **kwargs):
        """
        Initialize authorization error.
        
        Args:
            message: Error message
            required_permissions: List of permissions required for the operation
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        self.required_permissions = required_permissions
        super().__init__(message, *args, **kwargs)


class TokenError(AuthenticationError):
    """Base class for token-related errors."""
    
    def __init__(self, message: str = "Token error", *args, **kwargs):
        """
        Initialize token error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class TokenExpiredError(TokenError):
    """Exception raised when a token has expired."""
    
    def __init__(self, message: str = "Token has expired", *args, **kwargs):
        """
        Initialize token expired error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class InvalidTokenError(TokenError):
    """Exception raised when a token is invalid."""
    
    def __init__(self, message: str = "Invalid token", *args, **kwargs):
        """
        Initialize invalid token error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class ServiceError(ApplicationError):
    """Base class for service-related errors."""
    
    def __init__(self, message: str = "Service error", service_name: str = None, *args, **kwargs):
        """
        Initialize service error.
        
        Args:
            message: Error message
            service_name: Name of the service that encountered an error
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        if service_name:
            message = f"{service_name} service error: {message}"
        self.service_name = service_name
        super().__init__(message, *args, **kwargs)


class ExternalServiceError(ServiceError):
    """Exception raised when an external service encounters an error."""
    
    def __init__(self, message: str = "External service error", service_name: str = None, *args, **kwargs):
        """
        Initialize external service error.
        
        Args:
            message: Error message
            service_name: Name of the external service that encountered an error
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, service_name, *args, **kwargs)


class DatabaseError(ServiceError):
    """Exception raised for database errors."""
    
    def __init__(self, message: str = "Database error", *args, **kwargs):
        """
        Initialize database error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, "Database", *args, **kwargs)


class CacheError(ServiceError):
    """Exception raised for cache errors."""
    
    def __init__(self, message: str = "Cache error", *args, **kwargs):
        """
        Initialize cache error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, "Cache", *args, **kwargs)


class NotImplementedFeatureError(ApplicationError):
    """Exception raised when a feature is not implemented."""
    
    def __init__(self, feature: str = "Feature", *args, **kwargs):
        """
        Initialize not implemented feature error.
        
        Args:
            feature: Name of the feature that is not implemented
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        message = f"{feature} is not implemented"
        self.feature = feature
        super().__init__(message, *args, **kwargs)


class EncryptionError(ApplicationError):
    """Exception raised for encryption/decryption errors."""
    
    def __init__(self, message: str = "Encryption error", *args, **kwargs):
        """
        Initialize encryption error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)