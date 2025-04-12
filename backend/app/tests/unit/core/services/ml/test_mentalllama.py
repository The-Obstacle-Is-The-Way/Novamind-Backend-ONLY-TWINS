import json
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from botocore.exceptions import BotoCoreError

from app.core.config.settings import get_settings
from app.core.exceptions import InitializationError, ModelNotFoundError, ServiceUnavailableError
from app.core.services.ml.mentallama.bedrock_service import BedrockMentalLamaService

# Constants for testing
UTC = timezone.utc
SAMPLE_TEXT = "I've been feeling down lately and can't seem to find joy in activities."


@pytest.fixture
def mentalllama_service():
    """Create a BedrockMentalLamaService instance for testing."""
    service = BedrockMentalLamaService()
    service._bedrock_client = Mock()
    service._model_id = "anthropic.claude-instant-v1"
    return service


    @pytest.fixture
    def mock_bedrock_response():
    """Create a mock response from AWS Bedrock."""
    
    return {
        "body": {
            "read": MagicMock(return_value=json.dumps({))
                "completion": json.dumps({)
                    "model_type": "depression_detection",
                    "score": 0.85,
                    "confidence": 0.92,
                    "analysis": "The text indicates signs of depression.",
                    "recommendations": ["Consider consulting with a mental health professional."],
                    "timestamp": datetime.now(UTC).isoformat()
    (                })
    ((            }).encode())
        }
    }


@pytest.fixture
def mock_error_response():
    """Create a mock error response for AWS Bedrock."""
    mock = Mock()
    mock.side_effect = BotoCoreError()
    return mock


    class TestBedrockMentalLamaService:
    """Test cases for the BedrockMentalLamaService."""

    def test_initialization(self):
        """Test initialization of the service."""
        settings = get_settings()
        
        # Test with default settings
        service = BedrockMentalLamaService()
        assert service._region_name == settings.aws.region
        assert service._model_id == settings.aws.bedrock.anthropic_model_id
        
        # Test with custom settings
        custom_region = "us-west-2"
        custom_model = "anthropic.claude-v2"
        service = BedrockMentalLamaService(region_name=custom_region, model_id=custom_model)
        assert service._region_name == custom_region
        assert service._model_id == custom_model
        
        # Client should be None until initialized
        assert service._bedrock_client is None

        def test_initialize(self):
        """Test initialization of the AWS Bedrock client."""
        service = BedrockMentalLamaService()
        
        # Mock the boto3 client
        boto3_mock = Mock()
        client_mock = Mock()
        boto3_mock.client.return_value = client_mock
        
        with patch("boto3.client", return_value=client_mock):
        service.initialize()
        assert service._bedrock_client is not None
    
        def test_initialize_error(self):
        """Test handling of initialization errors."""
        service = BedrockMentalLamaService()
        
        # Mock the boto3 client to raise an exception
        with patch("boto3.client", side_effect=BotoCoreError()):
        with pytest.raises(InitializationError):
        service.initialize()
    
        def test_is_initialized(self):
        """Test checking if the service is initialized."""
        service = BedrockMentalLamaService()
        assert not service.is_initialized()
        
        service._bedrock_client = Mock()
        assert service.is_initialized()

        def test_detect_depression(self, mentalllama_service, mock_bedrock_response):
        """Test depression detection with valid input."""
        with patch.object()
            mentalllama_service._bedrock_client,
            "invoke_model",
            return_value=mock_bedrock_response
        (        ):
        result = mentalllama_service.detect_depression("I'm feeling sad today")
            
    assert result["model_type"] == "depression_detection"
    assert result["score"] > 0
    assert "analysis" in result
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)
    
    def test_detect_depression_with_phi(self, mentalllama_service, mock_bedrock_response):
        """Test depression detection with PHI data."""
        
        with patch.object()
        mentalllama_service._bedrock_client,
        "invoke_model",
        return_value=mock_bedrock_response
        (    ):
    result = mentalllama_service.detect_depression("My name is John Doe and I'm feeling sad")
            
    assert result["model_type"] == "depression_detection"
            # Ensure PHI is not logged or stored
    assert "John Doe" not in str(result)
    
    def test_detect_depression_error(self, mentalllama_service, mock_error_response):
        """Test handling of errors during depression detection."""
        
        with patch.object()
        mentalllama_service._bedrock_client,
        "invoke_model"
        (    ), pytest.raises(ServiceUnavailableError):
    mentalllama_service.detect_depression("I'm feeling sad today")
    
    def test_health_check(self, mentalllama_service):
        """Test health check functionality."""
        
        with patch.object()
        mentalllama_service._bedrock_client,
        "describe_model",
        return_value={"modelDetails": {"status": "InService"}}
        (    ):
    status = mentalllama_service.health_check()
    assert status["status"] == "healthy"
    assert "latency_ms" in status
    
    def test_health_check_error(self, mentalllama_service):
        """Test health check with errors."""
        
        with patch.object()
        mentalllama_service._bedrock_client,
        "describe_model",
        side_effect=BotoCoreError()
        (    ):
    status = mentalllama_service.health_check()
    assert status["status"] == "unhealthy"
    assert "error" in status
    
    def test_model_not_found(self, mentalllama_service):
        """Test handling of model not found errors."""
        
        # Test when model doesn't exist
        with patch.object()
        mentalllama_service._bedrock_client,
        "describe_model",
        side_effect=ModelNotFoundError("Model not found")
        (    ):
    status = mentalllama_service.health_check()
    assert status["status"] == "unhealthy"
    assert "Model not found" in status["error"]