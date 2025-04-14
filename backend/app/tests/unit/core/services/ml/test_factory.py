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


@pytest.mark.db_required()
class TestMLServiceFactory:
    """Test suite for ML Service Factory."""

    @pytest.fixture
    def factory(self):
        """Create a factory instance with test configuration."""
        test_config = {
            "mentalllama": {
                "model_ids": {
                    "depression_detection": "anthropic.claude-v2:1"
                },
                "aws_region": "us-east-1"
            },
            "phi_detection": {
                "aws_region": "us-east-1"
            }
        }
        factory = MLServiceFactory()
        factory.initialize(test_config)
        return factory

    def test_initialization(self):
        """Test factory initialization with valid configuration."""
        factory = MLServiceFactory()
        test_config = {
            "mentalllama": {
                "model_ids": {
                    "depression_detection": "anthropic.claude-v2:1"
                }
            }
        }
        factory.initialize(test_config)
        assert factory._config is not None
        assert "mentalllama" in factory._config

    def test_initialization_empty_config(self):
        """Test factory initialization with empty configuration."""
        factory = MLServiceFactory()

        with pytest.raises(InvalidConfigurationError):
            factory.initialize({})

        with pytest.raises(InvalidConfigurationError):
            factory.initialize(None)

    def test_create_phi_detection_service_aws(self, factory):
        """Test creating AWS PHI detection service."""
        with patch("app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize") as mock_initialize:
            service = factory.create_phi_detection_service("aws")
            assert isinstance(service, AWSComprehendMedicalPHIDetection)
            mock_initialize.assert_called_once()

    def test_create_phi_detection_service_mock(self, factory):
        """Test creating mock PHI detection service."""
        with patch("app.core.services.ml.mock.MockPHIDetection.initialize") as mock_initialize:
            service = factory.create_phi_detection_service("mock")
            assert isinstance(service, MockPHIDetection)
            mock_initialize.assert_called_once()

    def test_create_phi_detection_service_invalid(self, factory):
        """Test creating PHI detection service with invalid type."""
        with pytest.raises(InvalidConfigurationError):
            factory.create_phi_detection_service("invalid")

    def test_create_mentalllama_service_aws(self, factory):
        """Test creating AWS MentaLLaMA service."""
        with patch("app.core.services.ml.mentalllama.MentaLLaMA.initialize") as mock_initialize, \
             patch("app.core.services.ml.factory.MLServiceFactory.create_phi_detection_service", return_value=MagicMock()) as mock_create_phi:
            service = factory.create_mentalllama_service("aws", True)
            assert isinstance(service, MentaLLaMA)
            mock_initialize.assert_called_once()
            mock_create_phi.assert_called_once_with("aws")

    def test_create_mentalllama_service_mock(self, factory):
        """Test creating mock MentaLLaMA service."""
        with patch("app.core.services.ml.mock.MockMentaLLaMA.initialize") as mock_initialize, \
             patch("app.core.services.ml.factory.MLServiceFactory.create_phi_detection_service", return_value=MagicMock()) as mock_create_phi:
            service = factory.create_mentalllama_service("mock", True)
            assert isinstance(service, MockMentaLLaMA)
            mock_initialize.assert_called_once()
            mock_create_phi.assert_called_once_with("mock")

    def test_create_mentalllama_service_without_phi(self, factory):
        """Test creating MentaLLaMA service without PHI detection."""
        with patch("app.core.services.ml.mentalllama.MentaLLaMA.initialize") as mock_initialize, \
             patch("app.core.services.ml.factory.MLServiceFactory.create_phi_detection_service") as mock_create_phi:
            service = factory.create_mentalllama_service("aws", False)
            assert isinstance(service, MentaLLaMA)
            mock_initialize.assert_called_once()
            mock_create_phi.assert_not_called()

    def test_create_mentalllama_service_invalid(self, factory):
        """Test creating MentaLLaMA service with invalid type."""
        with pytest.raises(InvalidConfigurationError):
            factory.create_mentalllama_service("invalid", True)

    def test_service_caching(self, factory):
        """Test that services are cached and reused."""
        with patch("app.core.services.ml.mentalllama.MentaLLaMA.initialize") as mock_mentalllama_init, \
             patch("app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize") as mock_phi_init:

            service1_mentalllama = factory.get_mentalllama_service("aws")
            service2_mentalllama = factory.get_mentalllama_service("aws")

            service1_phi = factory.get_phi_detection_service("aws")
            service2_phi = factory.get_phi_detection_service("aws")

            assert service1_mentalllama is service2_mentalllama
            assert service1_phi is service2_phi

            mock_mentalllama_init.assert_called_once()
            mock_phi_init.assert_called_once()

    def test_shutdown(self, factory):
        """Test factory shutdown."""
        with patch("app.core.services.ml.mentalllama.MentaLLaMA.initialize"), \
             patch("app.core.services.ml.mentalllama.MentaLLaMA.shutdown") as mock_mentalllama_shutdown, \
             patch("app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize"), \
             patch("app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.shutdown") as mock_phi_shutdown:

            factory.get_mentalllama_service("aws")
            factory.get_phi_detection_service("aws")

            factory.shutdown()

            mock_mentalllama_shutdown.assert_called_once()
            mock_phi_shutdown.assert_called_once()

            assert len(factory._mental_llama_instances) == 0
            assert len(factory._phi_detection_instances) == 0
