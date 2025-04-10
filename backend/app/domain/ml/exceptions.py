"""
Machine Learning exceptions for the Novamind Digital Twin Backend.

This module defines domain-level exceptions related to ML operations,
particularly for the MentalLLaMA model interactions.
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MentalLLaMABaseException(Exception):
    """
    Base exception for all MentalLLaMA model errors.
    
    This serves as the parent class for all MentalLLaMA-related
    exceptions, providing consistent error handling and reporting.
    """
    message: str
    model_id: Optional[str] = None
    request_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """Human-readable string representation of the error."""
        base_msg = f"MentalLLaMA Error: {self.message}"
        
        if self.model_id:
            base_msg += f" (Model: {self.model_id})"
            
        if self.request_id:
            base_msg += f" [Request ID: {self.request_id}]"
            
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base_msg += f" - Details: {details_str}"
            
        return base_msg


@dataclass
class MentalLLaMAConnectionError(MentalLLaMABaseException):
    """
    Exception raised when connection to MentalLLaMA service fails.
    
    This could be due to network issues, service unavailability, or
    other connection-related problems.
    """
    def __init__(
        self, 
        message: str = "Failed to connect to MentalLLaMA service", 
        **kwargs
    ):
        super().__init__(message=message, **kwargs)


@dataclass
class MentalLLaMAAuthenticationError(MentalLLaMABaseException):
    """
    Exception raised when authentication with MentalLLaMA fails.
    
    This could be due to invalid API keys, expired credentials, or 
    insufficient permissions.
    """
    def __init__(
        self, 
        message: str = "Authentication failed for MentalLLaMA service", 
        **kwargs
    ):
        super().__init__(message=message, **kwargs)


@dataclass
class MentalLLaMAInferenceError(MentalLLaMABaseException):
    """
    Exception raised when MentalLLaMA inference process fails.
    
    This could be due to model-specific issues, invalid inputs, or
    unexpected errors during the inference process.
    """
    prompt: Optional[str] = None
    error_code: Optional[str] = None
    response_json: Optional[Dict[str, Any]] = None
    
    def __init__(
        self, 
        message: str = "Error during MentalLLaMA model inference", 
        **kwargs
    ):
        super().__init__(message=message, **kwargs)


@dataclass
class MentalLLaMAValidationError(MentalLLaMABaseException):
    """
    Exception raised when input validation for MentalLLaMA fails.
    
    This could be due to invalid input formats, missing required fields,
    or input values outside of acceptable ranges.
    """
    validation_errors: Dict[str, str] = field(default_factory=dict)
    
    def __init__(
        self, 
        message: str = "Validation error for MentalLLaMA input", 
        **kwargs
    ):
        super().__init__(message=message, **kwargs)


@dataclass
class MentalLLaMAQuotaExceededError(MentalLLaMABaseException):
    """
    Exception raised when API usage quota is exceeded.
    
    This occurs when the user has exceeded their allocated usage limits
    for the MentalLLaMA service.
    """
    quota_limit: Optional[int] = None
    current_usage: Optional[int] = None
    reset_time: Optional[str] = None
    
    def __init__(
        self, 
        message: str = "MentalLLaMA API usage quota exceeded", 
        **kwargs
    ):
        super().__init__(message=message, **kwargs)