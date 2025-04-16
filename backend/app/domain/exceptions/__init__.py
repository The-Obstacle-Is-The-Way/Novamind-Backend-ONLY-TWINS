"""
Domain exceptions for the Novamind Digital Twin Platform.

This module defines domain-specific exceptions that represent business rule violations
and other domain-related errors, following clean architecture principles.
"""

class EntityNotFoundError(Exception):
    """Exception raised when a requested entity is not found in the domain layer."""
    pass

class DomainError(Exception):
    """Base exception for all domain-related errors."""
    pass


class RepositoryError(DomainError):
    """
    Exception raised for errors in repository operations.
    
    This exception is used for data access errors, transaction failures,
    and other persistence-related issues.
    """
    pass


class ValidationError(DomainError):
    """
    Exception raised for validation errors in domain entities.
    
    This exception is used when domain entity validation fails,
    indicating that business rules have been violated.
    """
    pass


class AuthorizationError(DomainError):
    """
    Exception raised for authorization errors.
    
    This exception is used when an operation is attempted without
    the required permissions or authentication.
    """
    pass


class AuthenticationError(AuthorizationError):
    """Exception raised for authentication failures (e.g., invalid credentials, token)."""
    pass


class InvalidTokenError(AuthenticationError):
    """Exception raised when an authentication token is invalid or malformed."""
    pass


class MissingTokenError(AuthenticationError):
    """Exception raised when an authentication token is missing from the request."""
    pass


class TokenExpiredError(AuthenticationError):
    """Exception raised when an authentication token has expired."""
    pass


class PHISecurityError(DomainError):
    """
    Exception raised for PHI security violations.
    
    This exception is used when Protected Health Information (PHI)
    is accessed or modified in a way that violates HIPAA security rules.
    """
    pass


class InvalidAppointmentStateError(ValidationError):
    """Exception raised for invalid appointment state transitions."""
    pass


class InvalidAppointmentTimeError(ValidationError):
    """Exception raised for invalid appointment times (e.g., past date)."""
    pass