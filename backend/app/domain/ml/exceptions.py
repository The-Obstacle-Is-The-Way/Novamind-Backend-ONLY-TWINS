"""
Exceptions for ML and inference operations.

This module contains custom exception classes for machine learning operations,
particularly related to the MentalLLaMA inference system.
"""
from typing import Dict, Any, Optional


class MentalLLaMABaseException(Exception):
    """Base exception for all MentalLLaMA-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception with a message and optional details.
        
        Args:
            message: The error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MentalLLaMAConnectionError(MentalLLaMABaseException):
    """Exception raised when connection to MentalLLaMA service fails."""
    
    def __init__(self, message: str, endpoint: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the connection error.
        
        Args:
            message: The error message
            endpoint: The API endpoint that failed
            details: Optional dictionary with additional error context
        """
        self.endpoint = endpoint
        super().__init__(message, details)


class MentalLLaMAAuthenticationError(MentalLLaMABaseException):
    """Exception raised when authentication with MentalLLaMA service fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the authentication error.
        
        Args:
            message: The error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message, details)


class MentalLLaMAInferenceError(MentalLLaMABaseException):
    """Exception raised when inference with MentalLLaMA model fails."""
    
    def __init__(self, 
                 message: str, 
                 model_name: str, 
                 inference_parameters: Optional[Dict[str, Any]] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize the inference error.
        
        Args:
            message: The error message
            model_name: The name of the model that failed
            inference_parameters: The parameters used for inference
            details: Optional dictionary with additional error context
        """
        self.model_name = model_name
        self.inference_parameters = inference_parameters or {}
        
        # Merge inference parameters into details
        combined_details = details or {}
        combined_details["model_name"] = model_name
        combined_details["inference_parameters"] = self.inference_parameters
        
        super().__init__(message, combined_details)


class MentalLLaMAValidationError(MentalLLaMABaseException):
    """Exception raised when input validation for MentalLLaMA fails."""
    
    def __init__(self, message: str, validation_errors: Dict[str, str], details: Optional[Dict[str, Any]] = None):
        """
        Initialize the validation error.
        
        Args:
            message: The error message
            validation_errors: Dictionary mapping field names to error messages
            details: Optional dictionary with additional error context
        """
        self.validation_errors = validation_errors
        
        # Merge validation errors into details
        combined_details = details or {}
        combined_details["validation_errors"] = validation_errors
        
        super().__init__(message, combined_details)


class MentalLLaMAQuotaExceededError(MentalLLaMABaseException):
    """Exception raised when API usage quota is exceeded."""
    
    def __init__(self, message: str, quota_limit: int, quota_used: int, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the quota exceeded error.
        
        Args:
            message: The error message
            quota_limit: The maximum allowed API calls
            quota_used: The current number of API calls made
            details: Optional dictionary with additional error context
        """
        self.quota_limit = quota_limit
        self.quota_used = quota_used
        
        # Merge quota information into details
        combined_details = details or {}
        combined_details["quota_limit"] = quota_limit
        combined_details["quota_used"] = quota_used
        combined_details["quota_remaining"] = max(0, quota_limit - quota_used)
        
        super().__init__(message, combined_details)