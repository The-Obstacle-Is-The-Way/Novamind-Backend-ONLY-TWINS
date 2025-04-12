"""
Domain exceptions for the Novamind Digital Twin Platform.

This module defines domain-specific exceptions that represent business rule violations
and other domain-related errors, following clean architecture principles.
"""

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


class PHISecurityError(DomainError):
    """
    Exception raised for PHI security violations.
    
    This exception is used when Protected Health Information (PHI)
    is accessed or modified in a way that violates HIPAA security rules.
    """
    pass