"""
Factory for creating PAT service instances.

This module provides a factory for creating PAT service instances,
allowing for easy switching between different implementations (mock, AWS, etc.)
based on configuration.
"""

import logging
from typing import Any, Dict, Optional

# Use the canonical config location
# from app.core.config import get_settings
from app.config.settings import get_settings

settings = get_settings()
from app.core.services.ml.pat.exceptions import InitializationError
from app.core.services.ml.pat.pat_interface import PATInterface
from app.core.services.ml.pat.mock import MockPATService

# Conditionally import the AWS implementation
try:
    from app.core.services.ml.pat.aws import AWSPATService
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

# Set up logging with no PHI
logger = logging.getLogger(__name__)


class PATServiceFactory:
    """Factory for creating PAT service instances.
    
    This factory follows the Factory Method pattern to create
    different implementations of the PATInterface based on
    configuration or runtime needs.
    """
    
    def __init__(self) -> None:
        """Initialize the PAT service factory."""
        self._service_types = {
            "mock": self._create_mock_service
        }
        
        # Add AWS implementation if available
        if AWS_AVAILABLE:
            self._service_types["aws"] = self._create_aws_service
    
    def create_service(self, service_type: Optional[str] = None) -> PATInterface:
        """Create a PAT service instance.
        
        Args:
            service_type: Type of service to create ("mock", "aws", etc.)
                          If None, uses settings.PAT_SERVICE_TYPE
        
        Returns:
            An uninitialized PAT service instance
            
        Raises:
            InitializationError: If service_type is invalid
        """
        # Use settings if service_type not provided
        if service_type is None:
            service_type = settings.PAT_SERVICE_TYPE
        
        # Create service instance
        if service_type in self._service_types:
            logger.info(f"Creating PAT service of type: {service_type}")
            return self._service_types[service_type]()
        else:
            available_types = list(self._service_types.keys())
            raise InitializationError(
                f"Invalid PAT service type: {service_type}. "
                f"Available types: {available_types}"
            )
    
    def _create_mock_service(self) -> PATInterface:
        """Create a mock PAT service.
        
        Returns:
            An uninitialized mock PAT service
        """
        return MockPATService()
    
    def _create_aws_service(self) -> PATInterface:
        """Create an AWS PAT service.
        
        Returns:
            An uninitialized AWS PAT service
            
        Raises:
            InitializationError: If AWS implementation not available
        """
        if not AWS_AVAILABLE:
            raise InitializationError(
                "AWS PAT service implementation not available. "
                "Check that boto3 is installed and AWS credentials are configured."
            )
        
        return AWSPATService()