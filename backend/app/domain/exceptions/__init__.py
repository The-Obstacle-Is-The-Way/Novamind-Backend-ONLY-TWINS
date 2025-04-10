"""
Domain Exceptions.

This module defines domain-specific exceptions that represent business rule violations
or domain errors. These exceptions should be used to communicate domain-specific errors
to the application layer.
"""

from typing import List, Optional

from app.core.exceptions.base_exceptions import (
    ApplicationError, 
    AuthenticationError, 
    AuthorizationError
)


class DomainError(ApplicationError):
    """Base class for all domain exceptions."""
    
    def __init__(self, message: str = "Domain error occurred"):
        super().__init__(message)


class EntityNotFoundError(DomainError):
    """Exception raised when an entity cannot be found."""
    
    def __init__(self, entity_type: str, entity_id: Optional[str] = None):
        message = f"{entity_type} not found"
        if entity_id:
            message = f"{message}: {entity_id}"
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(message)


class ValidationError(DomainError):
    """Exception raised when domain validation fails."""
    
    def __init__(self, message: str = "Validation error", errors: Optional[List[str]] = None):
        self.errors = errors or []
        if errors and len(errors) > 0:
            message = f"{message}: {', '.join(errors)}"
        super().__init__(message)


class BusinessRuleViolationError(DomainError):
    """Exception raised when a business rule is violated."""
    
    def __init__(self, rule: str, message: str = "Business rule violation"):
        self.rule = rule
        full_message = f"{message}: {rule}"
        super().__init__(full_message)


class InvalidStateError(DomainError):
    """Exception raised when an operation is performed on an entity in an invalid state."""
    
    def __init__(self, entity_type: str, current_state: str, required_state: str):
        self.entity_type = entity_type
        self.current_state = current_state
        self.required_state = required_state
        message = f"{entity_type} is in {current_state} state, but {required_state} is required"
        super().__init__(message)


class ConcurrencyError(DomainError):
    """Exception raised when a concurrency conflict occurs."""
    
    def __init__(self, entity_type: str, entity_id: Optional[str] = None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"Concurrency conflict for {entity_type}"
        if entity_id:
            message = f"{message}: {entity_id}"
        super().__init__(message)


class AuthorizationException(AuthorizationError):
    """
    Exception raised when a user is not authorized to perform an action.
    
    This exception is a synonym for AuthorizationError, provided for
    backward compatibility.
    """
    
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message)


class RepositoryError(DomainError):
    """
    Exception raised when an error occurs in a repository operation.
    
    This exception is used to wrap infrastructure errors into a domain-level
    exception without exposing implementation details.
    """
    
    def __init__(self, message: str = "Error accessing repository", original_exception: Optional[Exception] = None):
        self.original_exception = original_exception
        super().__init__(message)


class AppointmentConflictError(DomainError):
    """
    Exception raised when an appointment conflicts with an existing appointment.
    
    This is a domain-specific exception for the scheduling bounded context.
    """
    
    def __init__(self, appointment_id: Optional[str] = None, conflicting_id: Optional[str] = None):
        self.appointment_id = appointment_id
        self.conflicting_id = conflicting_id
        message = "Appointment conflicts with existing appointment"
        if appointment_id and conflicting_id:
            message = f"{message}: {appointment_id} conflicts with {conflicting_id}"
        elif appointment_id:
            message = f"{message} for {appointment_id}"
        super().__init__(message)


# Import and re-export model exceptions
from app.domain.exceptions.model_exceptions import (
    ModelError,
    ModelInferenceError,
    MentalLLaMAInferenceError,
    ModelNotFoundError,
    DigitalTwinModelError,
    SimulationError,
    ModelTrainingError,
    ModelValidationError
)

# Export all exceptions
__all__ = [
    'DomainError',
    'EntityNotFoundError',
    'ValidationError',
    'BusinessRuleViolationError',
    'InvalidStateError',
    'ConcurrencyError',
    'AuthorizationException',
    'RepositoryError',
    'AppointmentConflictError',
    'ModelError',
    'ModelInferenceError',
    'MentalLLaMAInferenceError',
    'ModelNotFoundError',
    'DigitalTwinModelError',
    'SimulationError',
    'ModelTrainingError',
    'ModelValidationError'
]