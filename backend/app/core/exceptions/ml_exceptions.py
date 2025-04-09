# -*- coding: utf-8 -*-
"""
Machine Learning Service Exceptions.

This module defines exceptions raised by machine learning services.
"""

from app.core.exceptions.base_exceptions import ApplicationError


class MLServiceError(ApplicationError):
    """Base exception for ML service errors."""
    
    def __init__(self, message: str = "ML service error", *args, **kwargs):
        """
        Initialize ML service error.
        
        Args:
            message: Error message
        """
        super().__init__(message, *args, **kwargs)


class PHIDetectionError(MLServiceError):
    """Exception raised for errors in PHI detection."""
    
    def __init__(self, message: str = "Error in PHI detection", *args, **kwargs):
        """
        Initialize PHI detection error.
        
        Args:
            message: Error message
        """
        super().__init__(message, *args, **kwargs)


class MentaLLaMAServiceError(MLServiceError):
    """Exception raised for errors in MentaLLaMA service."""
    
    def __init__(self, message: str = "Error in MentaLLaMA service", *args, **kwargs):
        """
        Initialize MentaLLaMA service error.
        
        Args:
            message: Error message
        """
        super().__init__(message, *args, **kwargs)


class XGBoostServiceError(MLServiceError):
    """Exception raised for errors in XGBoost service."""
    
    def __init__(self, message: str = "Error in XGBoost service", *args, **kwargs):
        """
        Initialize XGBoost service error.
        
        Args:
            message: Error message
        """
        super().__init__(message, *args, **kwargs)


class InvalidRequestError(MLServiceError):
    """Exception raised for invalid request parameters or inputs."""
    
    def __init__(self, message: str = "Invalid request parameters", parameter: str = None, *args, **kwargs):
        """
        Initialize invalid request error.
        
        Args:
            message: Error message
            parameter: The specific parameter that is invalid
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        self.parameter = parameter
        if parameter:
            message = f"{message}: {parameter}"
        super().__init__(message, *args, **kwargs)


class ModelNotFoundError(MLServiceError):
    """Exception raised when a requested ML model cannot be found."""
    
    def __init__(self, model_id: str = None, *args, **kwargs):
        """
        Initialize model not found error.
        
        Args:
            model_id: ID of the model that was not found
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        message = "ML model not found"
        if model_id:
            message = f"{message}: {model_id}"
        self.model_id = model_id
        super().__init__(message, *args, **kwargs)


class ServiceUnavailableError(MLServiceError):
    """Exception raised when an ML service is unavailable or uninitialized."""
    
    def __init__(self, service_name: str = None, reason: str = None, *args, **kwargs):
        """
        Initialize service unavailable error.
        
        Args:
            service_name: Name of the service that is unavailable
            reason: Reason for service unavailability
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        message = "ML service unavailable"
        if service_name:
            message = f"{service_name} service unavailable"
        if reason:
            message = f"{message}: {reason}"
        self.service_name = service_name
        self.reason = reason
        super().__init__(message, *args, **kwargs)