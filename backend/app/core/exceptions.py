# -*- coding: utf-8 -*-
"""
Exception Definitions.

This module provides custom exceptions for the application.
"""

from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(self, message: str, **kwargs):
        """
        Initialize base exception.
        
        Args:
            message: Error message
            **kwargs: Additional context
        """
        self.message = message
        self.details = kwargs
        super().__init__(message)


class ResourceNotFoundException(BaseAppException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        """
        Initialize resource not found exception.
        
        Args:
            message: Error message
            resource_type: Type of resource that was not found
            **kwargs: Additional context
        """
        super().__init__(message, resource_type=resource_type, **kwargs)


class InfrastructureException(BaseAppException):
    """Exception raised when there is an infrastructure-related error."""
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None, 
        is_transient: bool = False, 
        **kwargs
    ):
        """
        Initialize infrastructure exception.
        
        Args:
            message: Error message
            service_name: Name of the service that failed
            is_transient: Whether the error is transient and can be retried
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            service_name=service_name, 
            is_transient=is_transient, 
            **kwargs
        )


class BusinessRuleException(BaseAppException):
    """Exception raised when a business rule is violated."""
    
    def __init__(self, message: str, rule_name: Optional[str] = None, **kwargs):
        """
        Initialize business rule exception.
        
        Args:
            message: Error message
            rule_name: Name of the business rule that was violated
            **kwargs: Additional context
        """
        super().__init__(message, rule_name=rule_name, **kwargs)


class ValidationException(BaseAppException):
    """Exception raised when validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field_name: Optional[str] = None, 
        validation_error: Optional[Any] = None, 
        **kwargs
    ):
        """
        Initialize validation exception.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            validation_error: The validation error
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            field_name=field_name, 
            validation_error=validation_error, 
            **kwargs
        )


class AuthenticationException(BaseAppException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str, user_id: Optional[str] = None, **kwargs):
        """
        Initialize authentication exception.
        
        Args:
            message: Error message
            user_id: ID of the user that failed authentication
            **kwargs: Additional context
        """
        super().__init__(message, user_id=user_id, **kwargs)


class AuthorizationException(BaseAppException):
    """Exception raised when authorization fails."""
    
    def __init__(
        self, 
        message: str, 
        user_id: Optional[str] = None, 
        resource: Optional[str] = None, 
        permission: Optional[str] = None, 
        **kwargs
    ):
        """
        Initialize authorization exception.
        
        Args:
            message: Error message
            user_id: ID of the user that failed authorization
            resource: Resource that the user tried to access
            permission: Permission that the user does not have
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            user_id=user_id, 
            resource=resource, 
            permission=permission, 
            **kwargs
        )


class ConfigurationException(BaseAppException):
    """Exception raised when there is a configuration error."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None, 
        **kwargs
    ):
        """
        Initialize configuration exception.
        
        Args:
            message: Error message
            config_key: Key of the configuration that has an error
            **kwargs: Additional context
        """
        super().__init__(message, config_key=config_key, **kwargs)


class ExternalServiceException(BaseAppException):
    """Exception raised when an external service fails."""
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None, 
        error_code: Optional[str] = None, 
        is_transient: bool = False, 
        **kwargs
    ):
        """
        Initialize external service exception.
        
        Args:
            message: Error message
            service_name: Name of the external service that failed
            error_code: Error code returned by the external service
            is_transient: Whether the error is transient and can be retried
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            service_name=service_name, 
            error_code=error_code, 
            is_transient=is_transient, 
            **kwargs
        )


# ML-specific exceptions
class ModelNotFoundError(ResourceNotFoundException):
    """Exception raised when a requested ML model is not found."""
    
    def __init__(self, message: str, model_name: Optional[str] = None, **kwargs):
        """
        Initialize model not found error.
        
        Args:
            message: Error message
            model_name: Name of the model that was not found
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            resource_type="model", 
            model_name=model_name, 
            **kwargs
        )


class ServiceUnavailableError(InfrastructureException):
    """Exception raised when an ML service is unavailable."""
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None, 
        is_transient: bool = False, 
        **kwargs
    ):
        """
        Initialize service unavailable error.
        
        Args:
            message: Error message
            service_name: Name of the service that is unavailable
            is_transient: Whether the error is transient and can be retried
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            service_name=service_name, 
            is_transient=is_transient, 
            **kwargs
        )


class InvalidRequestError(ValidationException):
    """Exception raised when an ML request is invalid."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None, 
        **kwargs
    ):
        """
        Initialize invalid request error.
        
        Args:
            message: Error message
            details: Details about the invalid request
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            validation_error=details, 
            **kwargs
        )


class HIPAAComplianceError(BusinessRuleException):
    """Exception raised when a request or operation violates HIPAA compliance."""
    
    def __init__(
        self, 
        message: str, 
        violation_type: Optional[str] = None, 
        **kwargs
    ):
        """
        Initialize HIPAA compliance error.
        
        Args:
            message: Error message
            violation_type: Type of HIPAA violation
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            rule_name="hipaa_compliance", 
            violation_type=violation_type, 
            **kwargs
        )


class InvalidConfigurationError(ConfigurationException):
    """Exception raised when ML service configuration is invalid."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None, 
        **kwargs
    ):
        """
        Initialize invalid configuration error.
        
        Args:
            message: Error message
            config_key: Key of the configuration that is invalid
            **kwargs: Additional context
        """
        super().__init__(
            message, 
            config_key=config_key, 
            **kwargs
        )


class MentalLLaMAInferenceError(ExternalServiceException):
    """Exception raised when an inference error occurs with MentalLLaMA models."""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        input_data: Optional[Any] = None,
        error_details: Optional[Dict[str, Any]] = None,
        is_transient: bool = False,
        **kwargs
    ):
        """
        Initialize MentalLLaMA inference error.
        
        Args:
            message: Error message
            model_name: Name of the MentalLLaMA model that failed
            input_data: Input data that caused the error (sanitized of PHI)
            error_details: Detailed error information from the inference engine
            is_transient: Whether the error is transient and can be retried
            **kwargs: Additional context
        """
        super().__init__(
            message,
            service_name="MentalLLaMA",
            error_code=error_details.get("code") if error_details else None,
            is_transient=is_transient,
            model_name=model_name,
            input_shape=str(type(input_data)) if input_data is not None else None,
            error_details=error_details,
            **kwargs
        )