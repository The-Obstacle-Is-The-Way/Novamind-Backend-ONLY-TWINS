"""
Domain Model Exceptions.

This module defines domain-specific exceptions related to the ML models
and inference processes within the domain layer. These exceptions represent
errors that occur within the domain's machine learning components.
"""

from typing import Optional, List, Dict, Any

from app.domain.exceptions import DomainError


class ModelError(DomainError):
    """Base class for all model-related domain exceptions."""
    
    def __init__(self, message: str = "Model error occurred"):
        """
        Initialize model error.
        
        Args:
            message: Error message
        """
        super().__init__(message)


class ModelNotFoundError(ModelError):
    """Exception raised when a requested model cannot be found."""
    
    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize model not found error.
        
        Args:
            model_id: ID of the model that was not found
        """
        message = "Model not found"
        if model_id:
            message = f"{message}: {model_id}"
        self.model_id = model_id
        super().__init__(message)


class ModelInferenceError(ModelError):
    """Exception raised when an error occurs during model inference."""
    
    def __init__(self, message: str = "Error during model inference", 
                 model_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize model inference error.
        
        Args:
            message: Error message
            model_id: ID of the model that caused the error
            details: Additional error details
        """
        if model_id:
            message = f"{message} (model: {model_id})"
        self.model_id = model_id
        self.details = details or {}
        super().__init__(message)


class MentalLLaMAInferenceError(ModelInferenceError):
    """
    Exception raised when there's an error during MentalLLaMA model inference.
    
    This is a specific subclass of ModelInferenceError used for errors
    related to the MentalLLaMA natural language processing model.
    """
    
    def __init__(self, message: str = "Error during MentalLLaMA inference",
                 model_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize MentalLLaMA inference error.
        
        Args:
            message: Error message
            model_id: ID of the model that caused the error
            details: Additional error details
        """
        super().__init__(message, model_id, details)


class DigitalTwinModelError(ModelError):
    """Exception raised for digital twin model-specific errors."""
    
    def __init__(self, message: str = "Digital twin model error",
                 patient_id: Optional[str] = None):
        """
        Initialize digital twin model error.
        
        Args:
            message: Error message
            patient_id: ID of the patient associated with the digital twin
        """
        if patient_id:
            message = f"{message} for patient {patient_id}"
        self.patient_id = patient_id
        super().__init__(message)


class SimulationError(DigitalTwinModelError):
    """Exception raised when an error occurs during patient simulation."""
    
    def __init__(self, message: str = "Error during patient simulation",
                 patient_id: Optional[str] = None,
                 simulation_parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize simulation error.
        
        Args:
            message: Error message
            patient_id: ID of the patient being simulated
            simulation_parameters: Parameters used in the failed simulation
        """
        self.simulation_parameters = simulation_parameters or {}
        super().__init__(message, patient_id)


class ModelTrainingError(ModelError):
    """Exception raised when an error occurs during model training."""
    
    def __init__(self, message: str = "Error during model training",
                 model_type: Optional[str] = None,
                 training_params: Optional[Dict[str, Any]] = None):
        """
        Initialize model training error.
        
        Args:
            message: Error message
            model_type: Type of model being trained
            training_params: Parameters used in the failed training
        """
        if model_type:
            message = f"{message} for {model_type} model"
        self.model_type = model_type
        self.training_params = training_params or {}
        super().__init__(message)


class ModelValidationError(ModelError):
    """Exception raised when model validation fails."""
    
    def __init__(self, message: str = "Model validation failed",
                 model_id: Optional[str] = None,
                 validation_metrics: Optional[Dict[str, Any]] = None):
        """
        Initialize model validation error.
        
        Args:
            message: Error message
            model_id: ID of the model that failed validation
            validation_metrics: Metrics from the failed validation
        """
        if model_id:
            message = f"{message} for model {model_id}"
        self.model_id = model_id
        self.validation_metrics = validation_metrics or {}
        super().__init__(message)