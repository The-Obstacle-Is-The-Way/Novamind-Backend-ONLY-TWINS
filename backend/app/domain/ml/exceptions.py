"""
Machine Learning exceptions for the Novamind Digital Twin Backend.

This module defines domain-level exceptions related to ML operations,
particularly for the MentalLLaMA model interactions.
"""
from typing import Any


class MentalLLaMABaseException(Exception):
    """
    Base exception for all MentalLLaMA model errors.
    
    This serves as the parent class for all MentalLLaMA-related
    exceptions, providing consistent error handling and reporting.
    """
    def __init__(
        self, 
        message: str,
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        """Human-readable string representation of the error."""
        return self.message


class MentalLLaMAConnectionError(MentalLLaMABaseException):
    """
    Exception raised when connection to MentalLLaMA service fails.
    
    This could be due to network issues, service unavailability, or
    other connection-related problems.
    """
    def __init__(
        self, 
        message: str,
        endpoint: str | None = None,
        details: dict[str, Any] | None = None
    ):
        self.endpoint = endpoint
        combined_details = details or {}
        if endpoint:
            combined_details["endpoint"] = endpoint
        super().__init__(message, combined_details)


class MentalLLaMAAuthenticationError(MentalLLaMABaseException):
    """
    Exception raised when authentication with MentalLLaMA fails.
    
    This could be due to invalid API keys, expired credentials, or 
    insufficient permissions.
    """
    def __init__(
        self, 
        message: str,
        details: dict[str, Any] | None = None
    ):
        super().__init__(message, details)


class MentalLLaMAInferenceError(MentalLLaMABaseException):
    """
    Exception raised when MentalLLaMA inference process fails.
    
    This could be due to model-specific issues, invalid inputs, or
    unexpected errors during the inference process.
    """
    def __init__(
        self, 
        message: str,
        model_name: str | None = None,
        inference_parameters: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None
    ):
        self.model_name = model_name
        self.inference_parameters = inference_parameters or {}
        
        combined_details = details or {}
        if model_name:
            combined_details["model_name"] = model_name
        if inference_parameters:
            combined_details["inference_parameters"] = inference_parameters
            
        super().__init__(message, combined_details)


class MentalLLaMAValidationError(MentalLLaMABaseException):
    """
    Exception raised when input validation for MentalLLaMA fails.
    
    This could be due to invalid input formats, missing required fields,
    or input values outside of acceptable ranges.
    """
    def __init__(
        self, 
        message: str,
        validation_errors: dict[str, str] | None = None,
        details: dict[str, Any] | None = None
    ):
        self.validation_errors = validation_errors or {}
        
        combined_details = details or {}
        if validation_errors:
            combined_details["validation_errors"] = validation_errors
            
        super().__init__(message, combined_details)


class MentalLLaMAQuotaExceededError(MentalLLaMABaseException):
    """
    Exception raised when API usage quota is exceeded.
    
    This occurs when the user has exceeded their allocated usage limits
    for the MentalLLaMA service.
    """
    def __init__(
        self, 
        message: str,
        quota_limit: int | None = None,
        quota_used: int | None = None,
        details: dict[str, Any] | None = None
    ):
        self.quota_limit = quota_limit
        self.quota_used = quota_used
        
        combined_details = details or {}
        if quota_limit is not None:
            combined_details["quota_limit"] = quota_limit
        if quota_used is not None:
            combined_details["quota_used"] = quota_used
            combined_details["quota_remaining"] = max(0, quota_limit - quota_used) if quota_limit is not None else 0
            
        super().__init__(message, combined_details)