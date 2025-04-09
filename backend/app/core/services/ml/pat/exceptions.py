"""
Exception classes for the PAT service.

This module defines custom exceptions for the PAT service to provide
clear error handling and appropriate HTTP status code mapping.
"""

from typing import Optional


class PATError(Exception):
    """Base exception class for all PAT service errors."""
    
    def __init__(self, message: str, status_code: int = 500) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InitializationError(PATError):
    """Exception raised when service initialization fails."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 500)


class ValidationError(PATError):
    """Exception raised when input validation fails."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 400)


class AnalysisError(PATError):
    """Exception raised when actigraphy analysis fails."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 500)


class EmbeddingError(PATError):
    """Exception raised when embedding generation fails."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 500)


class ResourceNotFoundError(PATError):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 404)


class AuthorizationError(PATError):
    """Exception raised when an operation is not authorized."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 403)


class IntegrationError(PATError):
    """Exception raised when integration with another service fails."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 500)


class ConfigurationError(PATError):
    """Exception raised when service configuration is invalid."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 500)


class StorageError(PATError):
    """Exception raised when storage operations (S3, DynamoDB) fail."""
    
    def __init__(self, message: str) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, 500)