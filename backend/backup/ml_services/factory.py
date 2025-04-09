# -*- coding: utf-8 -*-
"""
ML Service Factory.

This module provides factory methods for creating ML service instances.
"""

from typing import Dict, Optional, Any, Literal

from app.core.exceptions import InvalidConfigurationError
from app.core.services.ml.interface import MentaLLaMAInterface, PHIDetectionInterface
from app.core.services.ml.mentalllama import MentaLLaMA
from app.core.services.ml.mock import MockMentaLLaMA, MockPHIDetection
from app.core.services.ml.phi_detection import AWSComprehendMedicalPHIDetection
from app.core.utils.logging import get_logger


# Create logger (no PHI logging)
logger = get_logger(__name__)


class MLServiceFactory:
    """
    Factory class for creating ML service instances.
    
    This class follows the Factory pattern to create instances of ML services
    based on configuration. It supports creating both real implementations
    and mock implementations for testing.
    """
    
    def __init__(self) -> None:
        """Initialize the ML service factory."""
        self._mental_llama_instances: Dict[str, MentaLLaMAInterface] = {}
        self._phi_detection_instances: Dict[str, PHIDetectionInterface] = {}
        self._config: Dict[str, Any] = {}
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the factory with configuration.
        
        Args:
            config: Configuration dictionary containing service configs
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        if not config:
            raise InvalidConfigurationError("ML service factory configuration is empty")
            
        self._config = config
        
        # Log initialization
        logger.info("ML service factory initialized with configuration")
    
    def create_phi_detection_service(
        self, 
        service_type: Literal["aws", "mock"] = "aws"
    ) -> PHIDetectionInterface:
        """
        Create a PHI detection service instance.
        
        Args:
            service_type: Type of service to create (aws or mock)
            
        Returns:
            PHI detection service instance
            
        Raises:
            InvalidConfigurationError: If service type is invalid
        """
        # Check if instance already exists for this service type
        if service_type in self._phi_detection_instances:
            return self._phi_detection_instances[service_type]
        
        # Create new instance based on service type
        phi_detection_service: PHIDetectionInterface
        
        if service_type == "aws":
            phi_detection_service = AWSComprehendMedicalPHIDetection()
            phi_config = self._config.get("phi_detection", {})
            phi_detection_service.initialize(phi_config)
            
        elif service_type == "mock":
            phi_detection_service = MockPHIDetection()
            phi_detection_service.initialize({})
            
        else:
            raise InvalidConfigurationError(f"Invalid PHI detection service type: {service_type}")
        
        # Store instance for reuse
        self._phi_detection_instances[service_type] = phi_detection_service
        
        return phi_detection_service
    
    def create_mentalllama_service(
        self, 
        service_type: Literal["aws", "mock"] = "aws",
        with_phi_detection: bool = True
    ) -> MentaLLaMAInterface:
        """
        Create a MentaLLaMA service instance.
        
        Args:
            service_type: Type of service to create (aws or mock)
            with_phi_detection: Whether to include PHI detection service
            
        Returns:
            MentaLLaMA service instance
            
        Raises:
            InvalidConfigurationError: If service type is invalid
        """
        # Create key for caching
        cache_key = f"{service_type}_{with_phi_detection}"
        
        # Check if instance already exists for this service type and PHI detection setting
        if cache_key in self._mental_llama_instances:
            return self._mental_llama_instances[cache_key]
        
        # Create PHI detection service if needed
        phi_detection_service = None
        if with_phi_detection:
            phi_detection_type = "mock" if service_type == "mock" else "aws"
            phi_detection_service = self.create_phi_detection_service(phi_detection_type)
        
        # Create new instance based on service type
        mentalllama_service: MentaLLaMAInterface
        
        if service_type == "aws":
            mentalllama_service = MentaLLaMA()
            ml_config = self._config.get("mentalllama", {})
            # Add PHI detection service to config if provided
            if phi_detection_service:
                ml_config["phi_detection_service"] = phi_detection_service
            mentalllama_service.initialize(ml_config)
            
        elif service_type == "mock":
            mentalllama_service = MockMentaLLaMA()
            mock_config = {"phi_detection_service": phi_detection_service} if phi_detection_service else {}
            mentalllama_service.initialize(mock_config)
            
        else:
            raise InvalidConfigurationError(f"Invalid MentaLLaMA service type: {service_type}")
        
        # Store instance for reuse
        self._mental_llama_instances[cache_key] = mentalllama_service
        
        return mentalllama_service
    
    def get_mentalllama_service(
        self, 
        service_type: Literal["aws", "mock"] = "aws",
        with_phi_detection: bool = True
    ) -> MentaLLaMAInterface:
        """
        Get a MentaLLaMA service instance, creating it if needed.
        
        Args:
            service_type: Type of service to get (aws or mock)
            with_phi_detection: Whether to include PHI detection service
            
        Returns:
            MentaLLaMA service instance
        """
        return self.create_mentalllama_service(service_type, with_phi_detection)
    
    def get_phi_detection_service(
        self, 
        service_type: Literal["aws", "mock"] = "aws"
    ) -> PHIDetectionInterface:
        """
        Get a PHI detection service instance, creating it if needed.
        
        Args:
            service_type: Type of service to get (aws or mock)
            
        Returns:
            PHI detection service instance
        """
        return self.create_phi_detection_service(service_type)
    
    def shutdown(self) -> None:
        """Shutdown all service instances and release resources."""
        # Shutdown MentaLLaMA services
        for service in self._mental_llama_instances.values():
            service.shutdown()
        
        # Shutdown PHI detection services
        for service in self._phi_detection_instances.values():
            service.shutdown()
        
        # Clear instances
        self._mental_llama_instances.clear()
        self._phi_detection_instances.clear()
        
        logger.info("ML service factory shut down")


class MLServiceCache:
    """
    Cache for ML service instances.
    
    Provides a unified caching mechanism for ML services to improve
    performance and manage resources efficiently. This class uses
    the Singleton pattern to ensure a single cache is shared across
    the application.
    """
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'MLServiceCache':
        """
        Get the singleton cache instance.
        
        Returns:
            The singleton MLServiceCache instance
        """
        if cls._instance is None:
            cls._instance = MLServiceCache()
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the ML service cache."""
        self._factory: Optional[MLServiceFactory] = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the cache with configuration.
        
        This method initializes the internal factory with the provided
        configuration.
        
        Args:
            config: Configuration dictionary containing service configs
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        # Create factory if it doesn't exist
        if not self._factory:
            self._factory = MLServiceFactory()
            
        # Initialize factory
        self._factory.initialize(config)
        
        logger.info("ML service cache initialized")
    
    def get_mentalllama_service(
        self, 
        service_type: Literal["aws", "mock"] = "aws",
        with_phi_detection: bool = True
    ) -> MentaLLaMAInterface:
        """
        Get a MentaLLaMA service instance from the cache.
        
        Args:
            service_type: Type of service to get (aws or mock)
            with_phi_detection: Whether to include PHI detection service
            
        Returns:
            MentaLLaMA service instance
            
        Raises:
            ServiceUnavailableError: If cache is not initialized
        """
        if not self._factory:
            raise InvalidConfigurationError("ML service cache not initialized")
            
        return self._factory.get_mentalllama_service(service_type, with_phi_detection)
    
    def get_phi_detection_service(
        self, 
        service_type: Literal["aws", "mock"] = "aws"
    ) -> PHIDetectionInterface:
        """
        Get a PHI detection service instance from the cache.
        
        Args:
            service_type: Type of service to get (aws or mock)
            
        Returns:
            PHI detection service instance
            
        Raises:
            ServiceUnavailableError: If cache is not initialized
        """
        if not self._factory:
            raise InvalidConfigurationError("ML service cache not initialized")
            
        return self._factory.get_phi_detection_service(service_type)
    
    def shutdown(self) -> None:
        """Shutdown all cached service instances and release resources."""
        if self._factory:
            self._factory.shutdown()
            self._factory = None
            
        logger.info("ML service cache shut down")