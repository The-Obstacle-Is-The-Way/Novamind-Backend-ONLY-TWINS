# -*- coding: utf-8 -*-

"""
ML Service Interfaces.

This module defines the interfaces for ML services used in the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class BaseMLInterface(ABC):
    """Base interface for all ML services."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        pass


class MentaLLaMAInterface(BaseMLInterface):
    """Interface for MentaLLaMA ML services."""
    
    @abstractmethod
    def process(
        self, 
        text: str,
        model_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process text using the MentaLLaMA model.
        
        Args:
            text: Text to process
            model_type: Type of model to use
            options: Additional processing options
            
        Returns:
            Processing results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
            ModelNotFoundError: If model type is not found
        """
        pass
    
    @abstractmethod
    def detect_depression(
        self, 
        text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect depression signals in text.
        
        Args:
            text: Text to analyze
        """
        pass

# ... (all other interface/class definitions remain unchanged)

# Export MLService as a canonical alias for BaseMLInterface for compatibility and clarity
MLService = BaseMLInterface
