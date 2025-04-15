# -*- coding: utf-8 -*-
"""
NOVAMIND Dependency Injection Container
=====================================
Implements a clean dependency injection pattern for the NOVAMIND platform.
Follows SOLID principles and Clean Architecture by centralizing dependency management.
"""

import inspect
from functools import lru_cache
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar, cast

from fastapi import Depends

# Defer service/repository imports to within get_container
from app.core.utils.logging import get_logger
from app.domain.interfaces.ml_service_interface import (
    BiometricCorrelationInterface,
    DigitalTwinServiceInterface,
    PharmacogenomicsInterface,
    SymptomForecastingInterface,
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


@lru_cache()
def get_container() -> DIContainer:
    """
    Get the global DI container with all service registrations.
    Uses lru_cache to ensure we only create a single container instance.

    Returns:
        Configured DIContainer instance
    """
    container = DIContainer()

    # --- Import implementations *inside* the function ---
    from app.application.services.digital_twin_service import DigitalTwinApplicationService
    from app.application.services.patient_service import PatientApplicationService
    # Import the repository classes that contain the ABCs (interfaces)
    from app.domain.repositories.digital_twin_repository import DigitalTwinRepository
    from app.domain.repositories.patient_repository import PatientRepository
    # TODO: Need concrete repository implementations if these are just ABCs
    # Assuming DigitalTwinRepository/PatientRepository are the ABCs/Interfaces for now
    from app.domain.services.digital_twin_service import DigitalTwinService
    from app.domain.services.patient_service import PatientService
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

    # Register ML services (Assuming concrete implementations exist/will be created)
    # TODO: Replace placeholders with actual ML service implementations/factories
    container.register(BiometricCorrelationInterface, lambda: None) # Placeholder
    container.register(DigitalTwinServiceInterface, lambda: None) # Placeholder
    container.register(PharmacogenomicsInterface, lambda: None) # Placeholder
    container.register(SymptomForecastingInterface, lambda: None) # Placeholder

    # Register domain services
    container.register_scoped(DigitalTwinService, DigitalTwinService)
    container.register_scoped(PatientService, PatientService) # Keep this

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
def get_service(service_type: Type[T]) -> Callable[[], T]:
    """
    Create a FastAPI dependency that resolves a service.

    Args:
        service_type: The type of service to resolve

    Returns:
        FastAPI dependency function that yields the resolved service
    """

    def _get_service() -> T:
        container = get_container()
        return container.resolve(service_type)

    return _get_service
