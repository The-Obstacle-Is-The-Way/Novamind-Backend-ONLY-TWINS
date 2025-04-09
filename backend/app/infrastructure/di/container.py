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

from app.application.services.digital_twin_service import DigitalTwinApplicationService
from app.application.services.patient_service import PatientApplicationService
from app.core.utils.logging import HIPAACompliantLogger
from app.domain.interfaces.ml_service_interface import MLServiceInterface
from app.domain.repositories.digital_twin_repository import (
    DigitalTwinRepositoryInterface,
)
from app.domain.repositories.patient_repository import PatientRepositoryInterface
from app.domain.services.digital_twin_service import DigitalTwinService
from app.domain.services.patient_service import PatientService
from app.infrastructure.ml.digital_twin_integration_service import (
    DigitalTwinIntegrationService,
)
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_dependency
from app.infrastructure.persistence.sqlalchemy.repositories.digital_twin_repository import (
    DigitalTwinRepository,
)
from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import (
    PatientRepository,
)
from app.infrastructure.persistence.sqlalchemy.repositories.user_repository import (
    UserRepository,
)
from app.infrastructure.security.jwt.token_handler import JWTHandler
from app.infrastructure.security.password.password_handler import PasswordHandler

# Initialize logger
logger = HIPAACompliantLogger(__name__)

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

    # Register database dependency
    db_dependency = get_db_dependency()

    # Register repositories
    container.register(
        DigitalTwinRepositoryInterface,
        lambda: DigitalTwinRepository(next(db_dependency())),
    )
    container.register(
        PatientRepositoryInterface, lambda: PatientRepository(next(db_dependency()))
    )

    # Register ML services
    container.register_instance(MLServiceInterface, DigitalTwinIntegrationService())

    # Register domain services
    container.register_scoped(DigitalTwinService, DigitalTwinService)
    container.register_scoped(PatientService, PatientService)

    # Register application services
    container.register_scoped(
        DigitalTwinApplicationService, DigitalTwinApplicationService
    )
    container.register_scoped(PatientApplicationService, PatientApplicationService)

    # Register security services
    container.register_instance(JWTHandler, JWTHandler())
    container.register_instance(PasswordHandler, PasswordHandler())

    logger.info("Dependency Injection Container configured with all services")
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
