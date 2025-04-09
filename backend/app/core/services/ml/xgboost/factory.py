"""
Factory module for creating XGBoost service instances.

This module implements the Factory pattern for creating instances of the XGBoost service.
It allows switching between different implementations (AWS, mock, etc.) based on
configuration.
"""

import logging
from typing import Dict, Type, Optional

from app.core.services.ml.xgboost.interface import XGBoostInterface
from app.core.services.ml.xgboost.exceptions import ConfigurationError


# Registry of available implementations
_implementations: Dict[str, Type[XGBoostInterface]] = {}

# Module logger
logger = logging.getLogger(__name__)


def register_implementation(name: str, implementation_class: Type[XGBoostInterface]) -> None:
    """
    Register an implementation with the factory.
    
    Args:
        name: Name to register the implementation under
        implementation_class: Implementation class to register
        
    Raises:
        ValueError: If the name is already registered
    """
    if name in _implementations:
        raise ValueError(f"Implementation '{name}' already registered")
    
    _implementations[name] = implementation_class
    logger.debug(f"Registered XGBoost implementation: {name}")


def create_xgboost_service(implementation_name: str) -> XGBoostInterface:
    """
    Create a new XGBoost service instance.
    
    Args:
        implementation_name: Name of the implementation to create
        
    Returns:
        A new XGBoost service instance
        
    Raises:
        ConfigurationError: If the implementation is not found
    """
    # Convert to lowercase for case-insensitive matching
    name = implementation_name.lower()
    
    # Check if implementation exists
    if name not in _implementations:
        available_implementations = ", ".join(_implementations.keys())
        raise ConfigurationError(
            f"XGBoost implementation '{name}' not found",
            field="implementation",
            value=name,
            details=f"Available implementations: {available_implementations}"
        )
    
    # Create the service instance
    implementation_class = _implementations[name]
    logger.debug(f"Creating XGBoost service: {name}")
    
    return implementation_class()


# Register default implementations
def _register_defaults() -> None:
    """Register default implementations."""
    from app.core.services.ml.xgboost.aws import AWSXGBoostService
    from app.core.services.ml.xgboost.mock import MockXGBoostService
    
    register_implementation("aws", AWSXGBoostService)
    register_implementation("mock", MockXGBoostService)


# Register defaults on module import
_register_defaults()