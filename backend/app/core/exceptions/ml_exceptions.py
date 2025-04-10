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


class MentalLLaMAInferenceError(MentaLLaMAServiceError):
    """Exception raised for errors during MentalLLaMA inference."""
    
    def __init__(self, message: str = "Error during MentalLLaMA inference", *args, **kwargs):
        """
        Initialize MentalLLaMA inference error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class DigitalTwinError(MLServiceError):
    """Exception raised for errors in Digital Twin service."""
    
    def __init__(self, message: str = "Error in Digital Twin service", *args, **kwargs):
        """
        Initialize Digital Twin service error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class DigitalTwinInferenceError(DigitalTwinError):
    """Exception raised for errors during Digital Twin inference."""
    
    def __init__(self, message: str = "Error during Digital Twin inference", *args, **kwargs):
        """
        Initialize Digital Twin inference error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class DigitalTwinSessionError(DigitalTwinError):
    """Exception raised for errors with Digital Twin sessions."""
    
    def __init__(self, message: str = "Error with Digital Twin session", session_id: str = None, *args, **kwargs):
        """
        Initialize Digital Twin session error.
        
        Args:
            message: Error message
            session_id: ID of the session with the error
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        if session_id:
            message = f"{message} (Session ID: {session_id})"
        self.session_id = session_id
        super().__init__(message, *args, **kwargs)


class SimulationError(DigitalTwinError):
    """Exception raised for errors during digital twin simulation."""
    
    def __init__(self, message: str = "Error in digital twin simulation", *args, **kwargs):
        """
        Initialize simulation error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)


class DigitalTwinConfigError(DigitalTwinError):
    """Exception raised for configuration errors in Digital Twin service."""
    
    def __init__(self, message: str = "Digital Twin configuration error", *args, **kwargs):
        """
        Initialize Digital Twin configuration error.
        
        Args:
            message: Error message
            args: Additional positional arguments
            kwargs: Additional keyword arguments
        """
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