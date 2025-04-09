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