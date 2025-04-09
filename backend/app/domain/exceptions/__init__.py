"""
Domain-specific exceptions package for the Novamind concierge psychiatry platform.

This package provides direct access to the exception classes needed by other modules.
"""


# Define exception classes directly in the __init__.py file to avoid circular imports
class DomainException(Exception):
    """Base exception class for all domain-specific exceptions."""

    def __init__(self, message: str = "Domain error occurred"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(DomainException):
    """
    Raised when authentication fails due to invalid credentials or tokens.

    This exception is typically thrown during JWT validation or login attempts
    with incorrect credentials.
    """

    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """
    Raised when an authentication token has expired.

    This is a specific type of authentication error indicating that
    the user needs to refresh their token or log in again.
    """

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class ValidationError(DomainException):
    """
    Raised when input data fails validation rules.

    This exception is used for domain-level validation errors, such as
    invalid biometric rule conditions, invalid parameter values, or
    other constraint violations in the domain model.
    """

    def __init__(self, message: str = "Validation error occurred"):
        super().__init__(message)


class ValidationException(ValidationError):
    """
    Alternative name for ValidationError that is used for backward compatibility.
    
    This exception serves the same purpose as ValidationError and is provided to
    maintain compatibility with existing code that expects a ValidationException class.
    """
    
    def __init__(self, message: str = "Validation error occurred"):
        super().__init__(message)


class BiometricIntegrationError(DomainException):
    """
    Raised when there's an error processing biometric data.

    This exception is used for errors related to biometric data processing,
    such as invalid data formats, integration issues with biometric devices,
    or errors in the biometric data pipeline.
    """

    def __init__(self, message: str = "Error processing biometric data"):
        super().__init__(message)


class ModelInferenceError(DomainException):
    """
    Raised when there's an error during model inference or prediction.
    
    This exception is used for errors related to ML model inference,
    such as incompatible input data, model loading failures, or
    unexpected errors during prediction.
    """
    
    def __init__(self, message: str = "Error during model inference"):
        super().__init__(message)


class EntityNotFoundError(DomainException):
    """
    Raised when an entity cannot be found by its identifier.
    
    This exception is used when attempting to retrieve an entity by ID
    from a repository or data source and the entity does not exist.
    """
    
    def __init__(self, message: str = "Entity not found", entity_type: str = None, entity_id: str = None):
        if entity_type and entity_id:
            message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message)


class UnauthorizedAccessError(DomainException):
    """
    Raised when a user attempts to access a resource they're not authorized for.
    
    This exception is used for authorization failures, such as attempting
    to access a patient record without the proper role or permissions.
    """
    
    def __init__(self, message: str = "Unauthorized access to resource"):
        super().__init__(message)


class AuthorizationError(DomainException):
    """
    Raised when there's an error with the authorization process.
    
    This exception is used for errors in the authorization workflow,
    such as invalid role assignments or permission structures.
    """
    
    def __init__(self, message: str = "Authorization error occurred"):
        super().__init__(message)


class MentalLLaMAInferenceError(ModelInferenceError):
    """
    Raised when there's an error during MentalLLaMA model inference.
    
    This is a specific subclass of ModelInferenceError used for errors
    related to the MentalLLaMA natural language processing model.
    """
    
    def __init__(self, message: str = "Error during MentalLLaMA inference"):
        super().__init__(message)


class AuthenticationException(AuthenticationError):
    """
    Alternative name for AuthenticationError for backward compatibility.
    
    This exception serves the same purpose as AuthenticationError and is provided
    to maintain compatibility with existing code.
    """
    
    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(message)