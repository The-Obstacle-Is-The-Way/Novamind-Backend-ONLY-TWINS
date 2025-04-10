# -*- coding: utf-8 -*-
"""
Unit tests for ML Service Factory.

This module tests the ML Service Factory implementation to ensure it correctly
creates and manages ML service instances.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import InvalidConfigurationError
from app.core.services.ml.factory import MLServiceFactory
from app.core.services.ml.mentalllama import MentaLLaMA
from app.core.services.ml.mock import MockMentaLLaMA, MockPHIDetection
from app.core.services.ml.phi_detection import AWSComprehendMedicalPHIDetection


@pytest.mark.venv_only
class TestMLServiceFactory:
    """Test suite for ML Service Factory."""
    
    @pytest.fixture
    def factory(self):
        """Create a factory instance with test configuration."""
        factory = MLServiceFactory()
        factory.initialize({
            "mentalllama": {
                "model_ids": {
                    "depression_detection": "anthropic.claude-v2:1"
                },
                "aws_region": "us-east-1"
            },
            "phi_detection": {
                "aws_region": "us-east-1"
            }
        })
        return factory
    
    @pytest.mark.venv_only
def test_initialization(self):
        """Test factory initialization with valid configuration."""
        factory = MLServiceFactory()
        factory.initialize({
            "mentalllama": {
                "model_ids": {
                    "depression_detection": "anthropic.claude-v2:1"
                }
            }
        })
        
        assert factory._config is not None
        assert "mentalllama" in factory._config
    
    @pytest.mark.venv_only
def test_initialization_empty_config(self):
        """Test factory initialization with empty configuration."""
        factory = MLServiceFactory()
        
        with pytest.raises(InvalidConfigurationError):
            factory.initialize({})
        
        with pytest.raises(InvalidConfigurationError):
            factory.initialize(None)
    
    @pytest.mark.venv_only
def test_create_phi_detection_service_aws(self, factory):
        """Test creating AWS PHI detection service."""
        with patch(
            "app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize"
        ) as mock_initialize:
            service = factory.create_phi_detection_service("aws")
            
            assert isinstance(service, AWSComprehendMedicalPHIDetection)
            mock_initialize.assert_called_once()
    
    @pytest.mark.venv_only
def test_create_phi_detection_service_mock(self, factory):
        """Test creating mock PHI detection service."""
        with patch(
            "app.core.services.ml.mock.MockPHIDetection.initialize"
        ) as mock_initialize:
            service = factory.create_phi_detection_service("mock")
            
            assert isinstance(service, MockPHIDetection)
            mock_initialize.assert_called_once()
    
    @pytest.mark.venv_only
def test_create_phi_detection_service_invalid(self, factory):
        """Test creating PHI detection service with invalid type."""
        with pytest.raises(InvalidConfigurationError):
            factory.create_phi_detection_service("invalid")
    
    @pytest.mark.venv_only
def test_create_mentalllama_service_aws(self, factory):
        """Test creating AWS MentaLLaMA service."""
        with patch(
            "app.core.services.ml.mentalllama.MentaLLaMA.initialize"
        ) as mock_initialize, patch(
            "app.core.services.ml.factory.MLServiceFactory.create_phi_detection_service",
            return_value=MagicMock()
        ) as mock_create_phi:
            service = factory.create_mentalllama_service("aws", True)
            
            assert isinstance(service, MentaLLaMA)
            mock_initialize.assert_called_once()
            mock_create_phi.assert_called_once_with("aws")
    
    @pytest.mark.venv_only
def test_create_mentalllama_service_mock(self, factory):
        """Test creating mock MentaLLaMA service."""
        with patch(
            "app.core.services.ml.mock.MockMentaLLaMA.initialize"
        ) as mock_initialize, patch(
            "app.core.services.ml.factory.MLServiceFactory.create_phi_detection_service",
            return_value=MagicMock()
        ) as mock_create_phi:
            service = factory.create_mentalllama_service("mock", True)
            
            assert isinstance(service, MockMentaLLaMA)
            mock_initialize.assert_called_once()
            mock_create_phi.assert_called_once_with("mock")
    
    @pytest.mark.venv_only
def test_create_mentalllama_service_without_phi(self, factory):
        """Test creating MentaLLaMA service without PHI detection."""
        with patch(
            "app.core.services.ml.mentalllama.MentaLLaMA.initialize"
        ) as mock_initialize, patch(
            "app.core.services.ml.factory.MLServiceFactory.create_phi_detection_service"
        ) as mock_create_phi:
            service = factory.create_mentalllama_service("aws", False)
            
            assert isinstance(service, MentaLLaMA)
            mock_initialize.assert_called_once()
            mock_create_phi.assert_not_called()
    
    @pytest.mark.venv_only
def test_create_mentalllama_service_invalid(self, factory):
        """Test creating MentaLLaMA service with invalid type."""
        with pytest.raises(InvalidConfigurationError):
            factory.create_mentalllama_service("invalid")
    
    @pytest.mark.venv_only
def test_service_caching(self, factory):
        """Test that services are cached and reused."""
        with patch(
            "app.core.services.ml.mentalllama.MentaLLaMA.initialize"
        ) as mock_initialize, patch(
            "app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize"
        ):
            # Create services
            service1 = factory.get_mentalllama_service("aws")
            service2 = factory.get_mentalllama_service("aws")
            
            # Verify same instance is returned
            assert service1 is service2
            # Initialize should only be called once
            mock_initialize.assert_called_once()
    
    @pytest.mark.venv_only
def test_shutdown(self, factory):
        """Test factory shutdown."""
        with patch(
            "app.core.services.ml.mentalllama.MentaLLaMA.initialize"
        ), patch(
            "app.core.services.ml.mentalllama.MentaLLaMA.shutdown"
        ) as mock_mentalllama_shutdown, patch(
            "app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize"
        ), patch(
            "app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.shutdown"
        ) as mock_phi_shutdown:
            # Create services
            factory.get_mentalllama_service("aws")
            factory.get_phi_detection_service("aws")
            
            # Shutdown factory
            factory.shutdown()
            
            # Verify shutdown was called on all services
            mock_mentalllama_shutdown.assert_called_once()
            mock_phi_shutdown.assert_called_once()
            
            # Verify instances were cleared
            assert len(factory._mental_llama_instances) == 0
            assert len(factory._phi_detection_instances) == 0