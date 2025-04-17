# -*- coding: utf-8 -*-
"""
NOVAMIND Dependency Injection Container
=====================================
Implements a clean dependency injection pattern for the NOVAMIND platform.
Follows SOLID principles and Clean Architecture by centralizing dependency management.
"""

import inspect
import importlib # Added for dynamic imports
from functools import lru_cache
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar, cast, Union # Added Union

from fastapi import Depends

# Defer service/repository imports to within get_container
from app.core.utils.logging import get_logger
# Corrected import path for XGBoostInterface
from app.core.services.ml.xgboost.interface import XGBoostInterface
from app.domain.interfaces.ml_service_interface import (
    BiometricCorrelationInterface,
    DigitalTwinServiceInterface,
    PharmacogenomicsInterface,
    SymptomForecastingInterface,
    # XGBoostInterface, # Removed from here
)

# Remove top-level repository interface imports as they don't exist with these names
# from app.domain.repositories.digital_twin_repository import IDigitalTwinRepository
# from app.domain.repositories.patient_repository import IPatientRepository


# Initialize logger using the utility function
logger = get_logger(__name__)

# Type variable for DI registrations
T = TypeVar("T")


class DIContainer:
    """
    Dependency Injection Container for managing service dependencies.
    Implements the Service Locator pattern in a clean, type-safe way.
    """

    def __init__(self):
        """Initialize the container with empty registrations."""
        self._registrations: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}
        logger.debug("Dependency Injection Container initialized")

    def register(
        self, interface_type: Type[T], implementation_factory: Callable[[], T]
    ) -> None:
        """
        Register a service implementation factory for an interface.

        Args:
            interface_type: The interface or abstract type
            implementation_factory: Factory function creating the implementation
        """
        key = self._get_key(interface_type)
        self._registrations[key] = implementation_factory
        logger.debug(f"Registered factory for {key}")

    def register_scoped(
        self, interface_type: Type[T], implementation_type: Type[T]
    ) -> None:
        """
        Register a scoped service (instance per request/scope).

        Args:
            interface_type: The interface or abstract type
            implementation_type: The concrete implementation class
        """
        key = self._get_key(interface_type)
        # Store the type itself; instantiation happens on resolution
        self._registrations[key] = implementation_type
        logger.debug(f"Registered scoped service for {key}")

    def register_instance(self, interface_type: Type[T], instance: T) -> None:
        """
        Register a singleton instance for an interface.

        Args:
            interface_type: The interface or abstract type
            instance: The singleton instance
        """
        key = self._get_key(interface_type)
        self._instances[key] = instance
        logger.debug(f"Registered instance for {key}")

    def resolve(self, interface_type: Union[Type[T], str]) -> T:
        """
        Resolve a dependency by its interface type.

        Args:
            interface_type: The interface type to resolve

        Returns:
            An instance of the registered implementation

        Raises:
            TypeError: If the type is not registered
            Exception: If instantiation fails
        """
        key = self._get_key(interface_type)

        # Check singletons first
        if key in self._instances:
            logger.debug(f"Resolving instance for {key}")
            return cast(T, self._instances[key])

        # Check registrations (factories or scoped types)
        if key in self._registrations:
            registration = self._registrations[key]
            # If it's a factory function
            if callable(registration) and not isinstance(registration, type):
                logger.debug(f"Resolving factory for {key}")
                try:
                    instance = registration()
                    return cast(T, instance)
                except Exception as e:
                    logger.error(f"Error instantiating {key} from factory: {e}", exc_info=True)
                    raise Exception(f"Error resolving {key}: {e}") from e
            # If it's a type (scoped registration)
            elif isinstance(registration, type):
                logger.debug(f"Resolving scoped type {key}")
                try:
                    # Perform dependency injection for the implementation's __init__
                    instance = self._create_instance_with_dependencies(registration)
                    return cast(T, instance)
                except Exception as e:
                    logger.error(f"Error instantiating scoped {key}: {e}", exc_info=True)
                    raise Exception(f"Error resolving scoped {key}: {e}") from e

        logger.error(f"Type {interface_type} not registered in DI container.")
        raise TypeError(f"Type {interface_type} not registered.")

    def _create_instance_with_dependencies(self, implementation_type: Type[T]) -> T:
        """Instantiate a class, injecting its dependencies from the container."""
        signature = inspect.signature(implementation_type.__init__)
        dependencies: Dict[str, Any] = {}

        for name, param in signature.parameters.items():
            if name == 'self':
                continue
            if param.annotation is inspect.Parameter.empty:
                logger.warning(
                    f"Dependency '{name}' for {implementation_type.__name__} has no type hint. Cannot inject."
                )
                # Or raise an error if strict injection is required
                # raise TypeError(f"Missing type hint for dependency '{name}' in {implementation_type.__name__}")
                continue

            # Resolve dependency based on type hint
            try:
                dependencies[name] = self.resolve(param.annotation)
            except TypeError as e:
                # If dependency not found, re-raise with more context
                logger.error(
                    f"Failed to resolve dependency '{name}: {param.annotation.__name__}' for {implementation_type.__name__}",
                    exc_info=True
                )
                raise TypeError(
                    f"Cannot instantiate {implementation_type.__name__}: Dependency '{name}' ({param.annotation.__name__}) not registered."
                ) from e
            except Exception as e:
                 logger.error(
                    f"Unexpected error resolving dependency '{name}: {param.annotation.__name__}' for {implementation_type.__name__}",
                    exc_info=True
                )
                 raise

        logger.debug(f"Injecting dependencies {list(dependencies.keys())} into {implementation_type.__name__}")
        return implementation_type(**dependencies)

    def _get_key(self, interface_type: Union[Type[T], str]) -> str: # Accept string
        """Generate a unique key for registration/resolution."""
        if isinstance(interface_type, str):
            # If it's a string path, use it directly as the key
            # We assume the registration also used this string path
            return interface_type
        elif inspect.isclass(interface_type):
            return f"{interface_type.__module__}.{interface_type.__name__}"
        else:
            # Handle unexpected types
            raise TypeError(f"Unsupported type for DI key: {type(interface_type)}")

    def override(self, interface_type: Union[Type[T], str], implementation_factory: Callable[[], T]) -> None: # Accept string
        """
        Override an existing registration, useful for testing.

        Args:
            interface_type: The interface type to override.
            implementation_factory: The new factory function.
        """
        key = self._get_key(interface_type)
        if key not in self._registrations and key not in self._instances:
             logger.warning(f"Attempting to override non-existent registration for {key}. Registering instead.")
        self._registrations[key] = implementation_factory
        if key in self._instances:
            del self._instances[key] # Remove old singleton if overriding with factory
        logger.info(f"Overrode registration for {key}")

    def clear(self) -> None:
        """Clear all registrations and instances."""
        self._registrations.clear()
        self._instances.clear()
        logger.info("DI Container cleared.")


class Container(DIContainer):
    """Minimal Container class for import compatibility."""
    pass
    def __init__(self):
        """Initialize the container with empty registrations."""
        self._registrations: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}
        logger.debug("Dependency Injection Container initialized")

    def register(
        self, interface_type: Type[T], implementation_factory: Callable[[], T]
    ) -> None:
        """
        Register a service implementation factory for an interface.

        Args:
            interface_type: The interface or abstract type
            implementation_factory: Factory function creating the implementation
        """
        type_name = self._get_type_name(interface_type)
        self._registrations[type_name] = implementation_factory
        logger.debug(f"Registered implementation for {type_name}")

    def register_instance(self, interface_type: Type[T], instance: T) -> None:
        """
        Register a singleton instance for an interface.

        Args:
            interface_type: The interface or abstract type
            instance: The implementation instance
        """
        type_name = self._get_type_name(interface_type)
        self._instances[type_name] = instance
        logger.debug(f"Registered singleton instance for {type_name}")

    def register_scoped(
        self, interface_type: Type[T], implementation_type: Type[T]
    ) -> None:
        """
        Register a scoped service that's created once per scope.

        Args:
            interface_type: The interface or abstract type
            implementation_type: The implementation type
        """

        def factory():
            # Get constructor dependencies
            deps = self._resolve_dependencies(implementation_type)
            return implementation_type(**deps)

        self.register(interface_type, factory)

    def resolve(self, interface_type: Type[T]) -> T:
        """
        Resolve an implementation for the given interface.

        Args:
            interface_type: The interface to resolve

        Returns:
            Implementation of the specified interface

        Raises:
            KeyError: If no implementation is registered for the interface
        """
        type_name = self._get_type_name(interface_type)

        # Check for singleton instances first
        if type_name in self._instances:
            return cast(T, self._instances[type_name])

        # Then check for factory registrations
        if type_name in self._registrations:
            instance = self._registrations[type_name]()
            return cast(T, instance)

        raise KeyError(f"No implementation registered for {type_name}")

    def _get_type_name(self, type_obj: Type) -> str:
        """Get a unique string identifier for a type."""
        if hasattr(type_obj, "__module__") and hasattr(type_obj, "__name__"):
            return f"{type_obj.__module__}.{type_obj.__name__}"
        return str(type_obj)

    def _resolve_dependencies(self, implementation_type: Type[T]) -> Dict[str, Any]:
        """
        Resolve constructor dependencies for a type.

        Args:
            implementation_type: The type to resolve dependencies for

        Returns:
            Dictionary of parameter name to resolved dependency
        """
        if not hasattr(implementation_type, "__init__"):
            return {}

        signature = inspect.signature(implementation_type.__init__)
        deps = {}

        for param_name, param in signature.parameters.items():
            # Skip self parameter
            if param_name == "self":
                continue

            # Skip parameters with default values
            if param.default is not inspect.Parameter.empty:
                continue

            # Get the parameter type hint
            if param.annotation is inspect.Parameter.empty:
                continue

            try:
                deps[param_name] = self.resolve(param.annotation)
            except KeyError:
                logger.warning(
                    f"Could not resolve dependency {param_name} of type {param.annotation}"
                )

        return deps


# Restore lru_cache
@lru_cache()
def get_container() -> DIContainer:
    """
    Get the singleton DI container instance and configure it.
    Uses lru_cache to ensure only one instance is created and configured.
    """
    container = DIContainer()

    # --- Import implementations *inside* the function ---
    from app.application.services.digital_twin_service import DigitalTwinApplicationService
    from app.application.services.patient_service import PatientApplicationService
    # Import the repository classes that contain the ABCs (interfaces)
    from app.domain.repositories.digital_twin_repository import DigitalTwinRepository
    from app.domain.repositories.patient_repository import PatientRepository
    # Import necessary repositories for AnalyticsService
    from app.domain.repositories.temporal_repository import EventRepository
    from app.domain.repositories.appointment_repository import IAppointmentRepository
    from app.domain.repositories.clinical_note_repository import ClinicalNoteRepository
    from app.domain.repositories.medication_repository import MedicationRepository
    # TODO: Need concrete repository implementations if these are just ABCs
    # Assuming DigitalTwinRepository/PatientRepository are the ABCs/Interfaces for now
    from app.domain.services.digital_twin_service import DigitalTwinService
    from app.domain.services.patient_service import PatientService
    from app.domain.services.analytics_service import AnalyticsService # Import AnalyticsService
    from app.core.services.ml.xgboost.aws import AWSXGBoostService
    # --- End deferred imports ---

    # Register repositories
    # Register the ABC itself. We need a CONCRETE factory later.
    container.register(
        DigitalTwinRepository, # Register the ABC (which serves as interface)
        lambda: None # Placeholder factory - NEEDS CONCRETE IMPLEMENTATION
    )
    container.register(
        PatientRepository, # Register the ABC (which serves as interface)
        lambda: None # Placeholder factory - NEEDS CONCRETE IMPLEMENTATION
    )

    # Register required repository dependencies for AnalyticsService
    # TODO: Replace placeholders with actual concrete repository factories/implementations
    container.register(EventRepository, lambda: None) # Placeholder
    container.register(IAppointmentRepository, lambda: None) # Placeholder
    container.register(ClinicalNoteRepository, lambda: None) # Placeholder
    container.register(MedicationRepository, lambda: None) # Placeholder

    # Register ML services (Assuming concrete implementations exist/will be created)
    # TODO: Replace placeholders with actual ML service implementations/factories
    container.register(BiometricCorrelationInterface, lambda: None) # Placeholder
    container.register(DigitalTwinServiceInterface, lambda: None) # Placeholder
    container.register(PharmacogenomicsInterface, lambda: None) # Placeholder
    container.register(SymptomForecastingInterface, lambda: None) # Placeholder
    container.register(
        XGBoostInterface, 
        lambda: AWSXGBoostService() # Basic factory, might need config
    ) 

    # Register domain services
    container.register_scoped(DigitalTwinService, DigitalTwinService)
    container.register_scoped(PatientService, PatientService) # Keep this
    container.register_scoped(AnalyticsService, AnalyticsService) # Register AnalyticsService

    # Register application services
    container.register_scoped(
        DigitalTwinApplicationService, DigitalTwinApplicationService
    )
    container.register_scoped(PatientApplicationService, PatientApplicationService)

    # Register security services (Assuming concrete implementations exist)
    # container.register_instance(JWTHandler, JWTHandler()) # Placeholder
    # container.register_instance(PasswordHandler, PasswordHandler()) # Placeholder

    logger.info("Dependency Injection Container configured with services")
    return container


# Convenience function for FastAPI dependency injection
def get_service(service_type: Union[Type[T], str] = XGBoostInterface) -> Callable[[], T]: # Accept string or default to XGBoostInterface
    """Factory function to get a service instance for FastAPI Depends."""
    container = get_container()

    def _get_service() -> T:
        if isinstance(service_type, str):
            # Dynamically import if a string path is provided
            try:
                module_path, class_name = service_type.rsplit('.', 1)
                module = importlib.import_module(module_path)
                actual_type = getattr(module, class_name)
                # Resolve using the actual type now
                return container.resolve(actual_type)
            except (ImportError, AttributeError, ValueError) as e:
                logger.error(f"Failed to dynamically import or resolve service from path '{service_type}': {e}", exc_info=True)
                raise TypeError(f"Could not resolve service from path '{service_type}'") from e
        elif inspect.isclass(service_type):
            return container.resolve(service_type)
        else:
            raise TypeError(f"Unsupported service type for get_service: {type(service_type)}")

    return _get_service
