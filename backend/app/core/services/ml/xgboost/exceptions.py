"""
Domain-specific exceptions for the XGBoost service.

This module defines custom exceptions for the XGBoost service
that provide richer error information and better error handling.
"""

from typing import List, Optional, Any


class XGBoostServiceError(Exception):
    """Base class for all XGBoost service exceptions."""
    
    def __init__(self, message: str, **kwargs):
        """
        Initialize a new XGBoost service exception.
        
        Args:
            message: Error message
            **kwargs: Additional error context
        """
        super().__init__(message)
        self.message = message
        
        # Store additional context
        for key, value in kwargs.items():
            setattr(self, key, value)


class ValidationError(XGBoostServiceError):
    """
    Raised when validation of parameters fails.
    
    This exception is raised when a method parameter fails validation,
    such as an invalid risk type or missing required field.
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        """
        Initialize a new validation error.
        
        Args:
            message: Error message
            field: Name of the field that failed validation
            value: Value that failed validation
            **kwargs: Additional error context
        """
        super().__init__(message, field=field, value=value, **kwargs)


class DataPrivacyError(XGBoostServiceError):
    """
    Raised when PHI is detected in input data.
    
    This exception is raised when protected health information (PHI)
    is detected in input data, to prevent accidental PHI leakage.
    """
    
    def __init__(self, message: str, pattern_types: Optional[List[str]] = None, **kwargs):
        """
        Initialize a new data privacy error.
        
        Args:
            message: Error message
            pattern_types: Types of PHI patterns detected
            **kwargs: Additional error context
        """
        super().__init__(message, pattern_types=pattern_types or [], **kwargs)


class ResourceNotFoundError(XGBoostServiceError):
    """
    Raised when a requested resource is not found.
    
    This exception is raised when a resource such as a prediction
    or profile is not found in the system.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a new resource not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource not found
            resource_id: ID of resource not found
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )


class ModelNotFoundError(ResourceNotFoundError):
    """
    Raised when a requested model is not found.
    
    This exception is raised when a model type is not supported
    or not found in the system.
    """
    
    def __init__(self, message: str, model_type: Optional[str] = None, **kwargs):
        """
        Initialize a new model not found error.
        
        Args:
            message: Error message
            model_type: Type of model not found
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            resource_type="model",
            resource_id=model_type,
            model_type=model_type,
            **kwargs
        )


class PredictionError(XGBoostServiceError):
    """
    Raised when prediction fails.
    
    This exception is raised when a prediction fails due to model error,
    input data error, or other prediction-related issues.
    """
    
    def __init__(self, message: str, model_type: Optional[str] = None, **kwargs):
        """
        Initialize a new prediction error.
        
        Args:
            message: Error message
            model_type: Type of model that failed
            **kwargs: Additional error context
        """
        super().__init__(message, model_type=model_type, **kwargs)


class ServiceConnectionError(XGBoostServiceError):
    """
    Raised when connection to a service fails.
    
    This exception is raised when a connection to a required service
    such as SageMaker, DynamoDB, or Lambda fails.
    """
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        error_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a new service connection error.
        
        Args:
            message: Error message
            service: Name of the service that failed
            error_type: Type of connection error
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            service=service,
            error_type=error_type,
            **kwargs
        )


class ConfigurationError(XGBoostServiceError):
    """
    Raised when configuration is invalid.
    
    This exception is raised when configuration of the service
    is missing required fields or contains invalid values.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        details: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a new configuration error.
        
        Args:
            message: Error message
            field: Name of the field with invalid configuration
            value: Invalid value
            details: Additional error details
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            field=field,
            value=value,
            details=details,
            **kwargs
        )


class ThrottlingError(ServiceConnectionError):
    """
    Raised when a service request is throttled.
    
    This exception indicates that the service limit has been exceeded
    and the request should be retried later.
    """
    
    def __init__(
        self,
        message: str = "Request throttled by service",
        service: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize a new throttling error.
        
        Args:
            message: Error message
            service: Name of the service that throttled the request
            retry_after: Suggested delay in seconds before retrying
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            service=service,
            error_type="Throttling",
            retry_after=retry_after,
            **kwargs
        )