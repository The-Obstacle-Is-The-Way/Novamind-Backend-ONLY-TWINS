# -*- coding: utf-8 -*-
"""
Custom exceptions for the Novamind HIPAA-compliant psychiatry platform.

This module defines domain-specific exceptions that represent various error
conditions in the application's business logic. These exceptions are designed
to be caught and handled appropriately at the application boundaries.
"""


class ValidationError(Exception):
    """
    Exception raised when entity validation fails.
    
    This exception is raised when an entity fails to meet its validation
    requirements, such as required fields, format constraints, or business rules.
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialize a new ValidationError.
        
        Args:
            message: Description of the validation error
        """
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(Exception):
    """
    Exception raised when an entity cannot be found.
    
    This exception is raised when an attempt is made to retrieve an entity
    that does not exist in the system.
    """
    
    def __init__(self, entity_type: str, entity_id: str) -> None:
        """
        Initialize a new EntityNotFoundError.
        
        Args:
            entity_type: Type of entity that was not found
            entity_id: Identifier of the entity that was not found
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(self.message)


class UnauthorizedAccessError(Exception):
    """
    Exception raised when an unauthorized access attempt is made.
    
    This exception is raised when a user attempts to access a resource
    or perform an operation they are not authorized for.
    """
    
    def __init__(self, message: str = "Unauthorized access") -> None:
        """
        Initialize a new UnauthorizedAccessError.
        
        Args:
            message: Description of the unauthorized access attempt
        """
        self.message = message
        super().__init__(self.message)


class AppointmentConflictError(Exception):
    """
    Exception raised when there is a conflict in appointment scheduling.
    
    This exception is raised when an attempt is made to schedule an appointment
    that conflicts with an existing appointment.
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialize a new AppointmentConflictError.
        
        Args:
            message: Description of the appointment conflict
        """
        self.message = message
        super().__init__(self.message)


class BiometricIntegrationError(Exception):
    """
    Exception raised when there is an error in biometric data integration.
    
    This exception is raised when an error occurs during the integration
    of biometric data into a patient's digital twin.
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialize a new BiometricIntegrationError.
        
        Args:
            message: Description of the biometric integration error
        """
        self.message = message
        super().__init__(self.message)


class DeviceConnectionError(Exception):
    """
    Exception raised when there is an error connecting to a biometric device.
    
    This exception is raised when an error occurs while attempting to connect
    to or communicate with a biometric monitoring device.
    """
    
    def __init__(self, device_id: str, message: str) -> None:
        """
        Initialize a new DeviceConnectionError.
        
        Args:
            device_id: Identifier of the device that failed to connect
            message: Description of the connection error
        """
        self.device_id = device_id
        self.message = f"Error connecting to device {device_id}: {message}"
        super().__init__(self.message)


class DataProcessingError(Exception):
    """
    Exception raised when there is an error processing data.
    
    This exception is raised when an error occurs during the processing
    of data, such as parsing, transformation, or analysis.
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialize a new DataProcessingError.
        
        Args:
            message: Description of the data processing error
        """
        self.message = message
        super().__init__(self.message)


class ConfigurationError(Exception):
    """
    Exception raised when there is an error in the application configuration.
    
    This exception is raised when the application configuration is invalid
    or missing required settings.
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialize a new ConfigurationError.
        
        Args:
            message: Description of the configuration error
        """
        self.message = message
        super().__init__(self.message)


class ExternalServiceError(Exception):
    """
    Exception raised when there is an error communicating with an external service.
    
    This exception is raised when an error occurs while communicating with
    an external service, such as a third-party API or service.
    """
    
    def __init__(self, service_name: str, message: str) -> None:
        """
        Initialize a new ExternalServiceError.
        
        Args:
            service_name: Name of the external service
            message: Description of the error
        """
        self.service_name = service_name
        self.message = f"Error communicating with {service_name}: {message}"
        super().__init__(self.message)
