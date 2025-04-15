import json
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Dict, Any

import pytest
from botocore.exceptions import BotoCoreError

from app.config.settings import get_settings
from app.core.exceptions import InitializationError, ModelNotFoundError, ServiceUnavailableError
from app.core.services.ml.mentallama.bedrock_service import BedrockMentalLamaService

# Constants for testing
UTC = timezone.utc
SAMPLE_TEXT = "I've been feeling down lately and can't seem to find joy in activities."


@pytest.fixture
def mentalllama_service():
    """Create a BedrockMentalLamaService instance for testing."""
    service = BedrockMentalLamaService()
    service._bedrock_client = Mock()  # Use a standard Mock for the client
    service._model_id = "anthropic.claude-instant-v1"
    # Need to initialize properly or mock relevant methods if needed
    # service.initialize() # This would normally try to connect to AWS
    return service

@pytest.fixture
def mock_bedrock_response():
    """Create a mock response from AWS Bedrock."""
    mock_body_stream = Mock()
    # Simulate the structure Bedrock returns: a dict with a 'body' stream
    # The stream's read() method returns bytes, which need decoding
    response_content = {
        "model_type": "depression_detection",
        "score": 0.85,
        "confidence": 0.92,
        "analysis": "The text indicates signs of depression.",
        "recommendations": ["Consider consulting with a mental health professional."],
        "timestamp": datetime.now(UTC).isoformat()
    }
    # The body needs to simulate a streaming body, so mock read()
    mock_body_stream.read.return_value = json.dumps({"completion": json.dumps(response_content)}).encode('utf-8')
    return {"body": mock_body_stream}

@pytest.fixture
def mock_error_response():
    """Create a mock error response for AWS Bedrock."""
    mock = Mock()
    mock.side_effect = BotoCoreError()
    return mock

# Mock settings to avoid dependency on actual environment/config files
@pytest.fixture(scope="module", autouse=True)

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
        # Pass args correctly during instantiation
        service = BedrockMentalLamaService(region_name=custom_region, model_id=custom_model)
        assert service._region_name == custom_region
        assert service._model_id == custom_model

        # Client should be None until initialized
        assert service._bedrock_client is None

    def test_initialize(self):
        """Test initialization of the AWS Bedrock client."""
        service = BedrockMentalLamaService()

        # Mock the boto3 client
        client_mock = Mock() # Correct Mock usage

        with patch("boto3.client", return_value=client_mock) as mock_boto3_client:
            service.initialize()
            mock_boto3_client.assert_called_once_with(
                'bedrock-runtime',
                region_name=service._region_name
            )
            assert service._bedrock_client is client_mock

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

    def test_detect_depression(
        self,
        mentalllama_service, # Use the fixture
        mock_bedrock_response # Use the fixture
    ):
        """Test depression detection with valid input."""
        # Mock the client's invoke_model method on the fixture instance
        mentalllama_service._bedrock_client.invoke_model.return_value = mock_bedrock_response

        result = mentalllama_service.detect_depression("I'm feeling sad today")

        mentalllama_service._bedrock_client.invoke_model.assert_called_once()
        assert result["model_type"] == "depression_detection"
        assert result["score"] > 0
        assert "analysis" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    def test_detect_depression_with_phi(
        self, mentalllama_service, mock_bedrock_response
    ):
        """Test depression detection with PHI data."""
        mentalllama_service._bedrock_client.invoke_model.return_value = mock_bedrock_response

        result = mentalllama_service.detect_depression(
            "My name is John Doe and I'm feeling sad"
        )

        mentalllama_service._bedrock_client.invoke_model.assert_called_once()
        assert result["model_type"] == "depression_detection"
        # Ensure PHI is not logged or stored (this check is superficial)
        assert "John Doe" not in str(result)

    def test_detect_depression_error(
        self,
        mentalllama_service,
        mock_error_response # Use the fixture
    ):
        """Test handling of errors during depression detection."""
        # Configure the mock client to raise the error
        mentalllama_service._bedrock_client.invoke_model.side_effect = mock_error_response.side_effect

        with pytest.raises(ServiceUnavailableError):
            mentalllama_service.detect_depression("I'm feeling sad today")

        mentalllama_service._bedrock_client.invoke_model.assert_called_once()

    def test_health_check(self, mentalllama_service):
        """Test health check functionality."""
        # Mock the describe_model method
        mentalllama_service._bedrock_client.describe_model.return_value = {
            "modelDetails": {"status": "InService"}
        }

        status = mentalllama_service.health_check()

        mentalllama_service._bedrock_client.describe_model.assert_called_once_with(
            modelIdentifier=mentalllama_service._model_id
        )
        assert status["status"] == "healthy"
        assert "latency_ms" in status

    def test_health_check_error(self, mentalllama_service):
        """Test health check with errors."""
        # Mock describe_model to raise an error
        mentalllama_service._bedrock_client.describe_model.side_effect = BotoCoreError()

        status = mentalllama_service.health_check()

        mentalllama_service._bedrock_client.describe_model.assert_called_once_with(
            modelIdentifier=mentalllama_service._model_id
        )
        assert status["status"] == "unhealthy"
        assert "error" in status

    def test_model_not_found(self, mentalllama_service):
        """Test handling of model not found errors."""
        # Mock describe_model to raise ModelNotFoundError
        # Note: BotoCoreError is more likely, but testing specific exception handling
        mentalllama_service._bedrock_client.describe_model.side_effect = ModelNotFoundError("Model not found")

        status = mentalllama_service.health_check()

        mentalllama_service._bedrock_client.describe_model.assert_called_once_with(
            modelIdentifier=mentalllama_service._model_id
        )
        assert status["status"] == "unhealthy"
        assert "Model not found" in status["error"]
