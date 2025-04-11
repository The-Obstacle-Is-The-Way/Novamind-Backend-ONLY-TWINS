"""
Exception classes for the Patient Assessment Tool (PAT) service module.

This module defines custom exceptions that are raised by the PAT service
to provide clean error handling and meaningful error messages.
"""

from typing import Optional, Any, Dict, List


class PATServiceError(Exception):
    """Base class for all PAT service exceptions."""
    
    def __init__(self, message: str, **kwargs):
        """
        Initialize a new PAT service exception.
        
        Args:
            message: Error message
            **kwargs: Additional error context
        """
        self.message = message
        self.details = kwargs
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            **self.details
        }


class ValidationError(PATServiceError):
    """Exception raised when validation of input data fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        """
        Initialize a validation error.
        
        Args:
            message: Error message
            field: Name of the field that failed validation
            value: Value that failed validation
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            field=field,
            value=value,
            **kwargs
        )


class InitializationError(PATServiceError):
    """Exception raised when initialization of a service or component fails."""
    
    def __init__(self, message: str, component: Optional[str] = None, cause: Optional[str] = None, **kwargs):
        """
        Initialize an initialization error.
        
        Args:
            message: Error message
            component: Name of the component that failed to initialize
            cause: Cause of the failure
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            component=component,
            cause=cause,
            **kwargs
        )


class AnalysisError(PATServiceError):
    """Exception raised when analysis of patient data fails."""
    
    def __init__(self, message: str, analysis_type: Optional[str] = None, cause: Optional[str] = None, **kwargs):
        """
        Initialize an analysis error.
        
        Args:
            message: Error message
            analysis_type: Type of analysis that failed
            cause: Cause of the failure
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            analysis_type=analysis_type,
            cause=cause,
            **kwargs
        )


class DataPrivacyError(PATServiceError):
    """Exception raised when PHI is detected in data."""
    
    def __init__(self, message: str, field: Optional[str] = None, phi_type: Optional[str] = None, **kwargs):
        """
        Initialize a data privacy error.
        
        Args:
            message: Error message
            field: Name of the field containing PHI
            phi_type: Type of PHI detected
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            field=field,
            phi_type=phi_type,
            **kwargs
        )


class ResourceNotFoundError(PATServiceError):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, **kwargs):
        """
        Initialize a resource not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource that was not found
            resource_id: ID of the resource that was not found
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )


class AnalysisNotFoundError(ResourceNotFoundError):
    """Exception raised when a requested analysis is not found."""
    
    def __init__(self, message: str, analysis_id: Optional[str] = None, patient_id: Optional[str] = None, **kwargs):
        """
        Initialize an analysis not found error.
        
        Args:
            message: Error message
            analysis_id: ID of the analysis that was not found
            patient_id: ID of the patient associated with the analysis
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            resource_type="analysis",
            resource_id=analysis_id,
            patient_id=patient_id,
            **kwargs
        )


class ServiceConnectionError(PATServiceError):
    """Exception raised when a connection to an external service fails."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, cause: Optional[str] = None, **kwargs):
        """
        Initialize a service connection error.
        
        Args:
            message: Error message
            service_name: Name of the service that failed
            cause: Cause of the failure
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            service_name=service_name,
            cause=cause,
            **kwargs
        )


class ConfigurationError(PATServiceError):
    """Exception raised when there is a configuration error."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        """
        Initialize a configuration error.
        
        Args:
            message: Error message
            field: Name of the field with an error
            value: Value that caused the error
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            field=field,
            value=value,
            **kwargs
        )


class IntegrationError(PATServiceError):
    """Exception raised when integration with another system fails."""
    
    def __init__(self, message: str, system_name: Optional[str] = None, cause: Optional[str] = None, **kwargs):
        """
        Initialize an integration error.
        
        Args:
            message: Error message
            system_name: Name of the system that failed to integrate
            cause: Cause of the failure
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            system_name=system_name,
            cause=cause,
            **kwargs
        )


class AuthorizationError(PATServiceError):
    """Exception raised when an operation is not authorized."""
    
    def __init__(self, message: str, user_id: Optional[str] = None, resource_id: Optional[str] = None, action: Optional[str] = None, **kwargs):
        """
        Initialize an authorization error.
        
        Args:
            message: Error message
            user_id: ID of the user who attempted the operation
            resource_id: ID of the resource that was accessed
            action: Type of action that was attempted
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            user_id=user_id,
            resource_id=resource_id,
            action=action,
            **kwargs
        )


class EmbeddingError(PATServiceError):
    """Exception raised when embedding generation fails."""
    
    def __init__(self, message: str, model_id: Optional[str] = None, data_type: Optional[str] = None, cause: Optional[str] = None, **kwargs):
        """
        Initialize an embedding error.
        
        Args:
            message: Error message
            model_id: ID of the embedding model
            data_type: Type of data being embedded
            cause: Cause of the failure
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            model_id=model_id,
            data_type=data_type,
            cause=cause,
            **kwargs
        )