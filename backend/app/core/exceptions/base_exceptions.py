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