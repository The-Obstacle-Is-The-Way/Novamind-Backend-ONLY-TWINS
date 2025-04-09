"""
Factory for creating PAT service instances.

This module provides a factory for creating different implementations
of the Patient Activity Tracking (PAT) service.
"""

from typing import Any, Dict, Optional, Type

from app.core.services.ml.pat.base import PATBase
from app.core.services.ml.pat.bedrock import BedrockPAT
from app.core.services.ml.pat.exceptions import ConfigurationError
from app.core.services.ml.pat.mock import MockPAT


class PATFactory:
    """Factory for creating PAT service instances with caching."""
    
    # Cache for PAT service instances
    _instance_cache = {}
    
    @classmethod
    def get_pat_service(cls, config: Dict[str, Any]) -> PATBase:
        """Get a PAT service instance based on configuration.
        
        This method creates or retrieves a PAT service instance based on
        the provided configuration. Instances are cached by a hash of
        their configuration to prevent duplicate instances with the
        same configuration.
        
        Args:
            config: Configuration parameters for the PAT service
                - provider: The PAT provider to use (e.g., "mock", "bedrock")
                - Other provider-specific configuration parameters
                
        Returns:
            A configured PAT service instance
            
        Raises:
            ValueError: If the specified provider is not supported
        """
        # Default to "mock" provider if not specified
        provider = config.get("provider", "mock").lower()
        
        # Generate a cache key based on the configuration
        # Sort the items to ensure consistent keys regardless of dict order
        cache_key = provider + "-" + str(hash(frozenset(config.items())))
        
        # Check if we already have an instance with this configuration
        if cache_key in cls._instance_cache:
            return cls._instance_cache[cache_key]
        
        # Create a new instance based on the provider
        if provider == "mock":
            service = MockPAT()
        elif provider == "bedrock":
            service = BedrockPAT()
        else:
            raise ValueError(f"Unknown PAT provider: {provider}")
        
        # Initialize the service with the configuration
        service.initialize(config)
        
        # Cache the instance
        cls._instance_cache[cache_key] = service
        
        return service