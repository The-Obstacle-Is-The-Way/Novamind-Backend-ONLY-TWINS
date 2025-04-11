# -*- coding: utf-8 -*-
"""
Unit tests for MentaLLaMA Service.

This module contains tests for the MentaLLaMA service implementation,
verifying its functionality, error handling, and HIPAA compliance.
"""

import json
import time
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock, ANY

import pytest
from app.core.services.ml.mentalllama import MentaLLaMA as MentaLLaMAService
from app.core.exceptions import ServiceUnavailableError, ModelNotFoundError, InvalidRequestError

class TestMentaLLaMAService:
    """Test suite for MentaLLaMA service."""

    @pytest.fixture
    def service(self):
        """Create a MentaLLaMA service instance for testing."""
        return MentaLLaMAService()

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return {
            "provider": "internal",
            "endpoint": "http://localhost:8080",
            "api_key": "test-api-key",
            "model_path": "./models",
            "batch_size": 1,
            "device": "cpu",
            "phi_detection": {
                "enabled": True,
                "sensitivity": 0.8,
                "redact_mode": "token"
            }
        }

    def test_initialization(self, service, mock_config):
        """Test service initialization."""
        # Patch the setup client methods to avoid actual client creation
        with patch.object(service, '_setup_client'), \
             patch.object(service, '_load_models'):
            
            # Initialize the service
            service.initialize(mock_config)
            
            # Check if initialization was successful
            assert service._initialized is True
            assert service._config == mock_config
            assert service._provider == "internal"

    def test_initialization_failure(self, service, mock_config):
        """Test service initialization failure."""
        # Mock _setup_client to raise an exception
        with patch.object(service, '_setup_client', side_effect=Exception("Setup failed")), \
             patch.object(service, '_load_models'):
            
            # Initialize the service should raise ServiceUnavailableError
            with pytest.raises(ServiceUnavailableError) as exc_info:
                service.initialize(mock_config)
            
            # Check exception message
            assert "initialization failed" in str(exc_info.value)
            assert service._initialized is False

    def test_is_healthy(self, service):
        """Test health check method."""
        # Not initialized
        assert service.is_healthy() is False
        
        # Initialize but no client
        service._initialized = True
        service._client = None
        assert service.is_healthy() is False
        
        # Initialize and has client
        service._client = {"type": "internal"}
        assert service.is_healthy() is True

    def test_shutdown(self, service):
        """Test shutdown method."""
        # Set up service for shutdown
        service._initialized = True
        service._client = {"type": "internal"}
        
        # Perform shutdown
        service.shutdown()
        
        # Check if shutdown was successful
        assert service._initialized is False
        assert service._client is None

    @patch('app.core.services.ml.mentalllama.json')
    @patch('app.core.services.ml.mentalllama.sanitize_text')
    @patch('app.core.services.ml.mentalllama.uuid.uuid4')
    @patch('app.core.services.ml.mentalllama.datetime')
    def test_process_method(self, mock_datetime, mock_uuid, mock_sanitize, mock_json, service, mock_config):
        """Test process method for task execution."""
        # Set up mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        mock_now = datetime(2025, 3, 28, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.now.return_value.isoformat.return_value = mock_now.isoformat()
        mock_sanitize.return_value = "Sanitized prompt"
        
        # Initialize service
        with patch.object(service, '_setup_client'), \
             patch.object(service, '_load_models'):
            service.initialize(mock_config)
        
        # Set up models dictionary
        service._models = {
            "mentallama-33b-lora": {
                "max_tokens": 8192,
                "capabilities": ["depression_detection", "risk_assessment"],
                "version": "v1.0",
                "description": "Test model"
            }
        }
        
        # Mock _process_with_provider
        with patch.object(service, '_process_with_provider', return_value="Model response text"), \
             patch.object(service, '_post_process_response') as mock_post_process, \
             patch.object(service, '_estimate_tokens_used', return_value=100):
            
            # Set up post-process mock
            mock_post_process.return_value = {
                "text": "Processed model response",
                "structured_data": {"key": "value"},
                "confidence": "high",
                "metadata": {"version": "v1.0"}
            }
            
            # Call the process method
            result = service.process(
                prompt="Test prompt",
                model="mentallama-33b-lora",
                task="depression_detection",
                context={"patient_history": "Brief history"},
                max_tokens=100,
                temperature=0.7
            )
            
            # Check result structure
            assert result["response_id"] == "12345678-1234-5678-1234-567812345678"
            assert result["model"] == "mentallama-33b-lora"
            assert result["task"] == "depression_detection"
            assert result["provider"] == "internal"
            assert result["text"] == "Processed model response"
            assert result["structured_data"] == {"key": "value"}
            assert result["tokens_used"] == 100
            assert result["created_at"] == mock_now.isoformat()
            assert result["confidence"] == "high"
            assert "metadata" in result
            
            # Check that sanitize_text was called
            mock_sanitize.assert_called_once_with("Test prompt")
            
            # Check that process_with_provider was called with correct args
            service._process_with_provider.assert_called_once_with(
                "Sanitized prompt", 
                "mentallama-33b-lora", 
                "depression_detection", 
                {"patient_history": "Brief history"},
                100, 
                0.7
            )

    def test_process_service_not_initialized(self, service):
        """Test process method when service is not initialized."""
        with pytest.raises(ServiceUnavailableError) as exc_info:
            service.process(
                prompt="Test prompt",
                model="mentallama-33b-lora",
                task="depression_detection"
            )
        
        assert "not initialized" in str(exc_info.value)

    def test_process_model_not_found(self, service):
        """Test process method with non-existent model."""
        # Initialize service
        service._initialized = True
        service._models = {
            "mentallama-33b-lora": {
                "capabilities": ["depression_detection"],
                "version": "v1.0"
            }
        }
        
        with pytest.raises(ModelNotFoundError) as exc_info:
            service.process(
                prompt="Test prompt",
                model="non-existent-model",
                task="depression_detection"
            )
        
        assert "not found" in str(exc_info.value)

    def test_process_unsupported_task(self, service):
        """Test process method with unsupported task."""
        # Initialize service
        service._initialized = True
        service._models = {
            "mentallama-33b-lora": {
                "capabilities": ["depression_detection"],
                "version": "v1.0"
            }
        }
        
        with pytest.raises(InvalidRequestError) as exc_info:
            service.process(
                prompt="Test prompt",
                model="mentallama-33b-lora",
                task="unsupported_task"
            )
        
        assert "not support task" in str(exc_info.value)

    @patch('app.core.services.ml.mentalllama.sanitize_text')
    def test_sanitize_input(self, mock_sanitize, service):
        """Test PHI sanitization function."""
        mock_sanitize.return_value = "Sanitized text without PHI"
        
        result = service._sanitize_input("Original text with PHI")
        
        assert result == "Sanitized text without PHI"
        mock_sanitize.assert_called_once_with("Original text with PHI")

    def test_post_process_response_depression_detection(self, service):
        """Test post-processing for depression detection task."""
        # Mock extraction methods
        with patch.object(service, '_extract_severity', return_value="moderate"), \
             patch.object(service, '_extract_indicators', return_value=["indicator1", "indicator2"]), \
             patch.object(service, '_extract_rationale', return_value="Rationale text"):
            
            response = "Depression detection results"
            base_result = {
                "text": response,
                "structured_data": {},
                "confidence": "high",
                "metadata": {"version": "v1.0"}
            }
            
            result = service._process_depression_detection(response, base_result)
            
            assert result["text"] == response
            assert "structured_data" in result
            assert result["structured_data"]["severity"] == "moderate"
            assert len(result["structured_data"]["key_indicators"]) == 2

    def test_post_process_response_risk_assessment(self, service):
        """Test post-processing for risk assessment task."""
        # Mock extraction methods
        with patch.object(service, '_extract_risk_level', return_value="low"), \
             patch.object(service, '_extract_indicators', return_value=["indicator1"]), \
             patch.object(service, '_extract_actions', return_value=["action1"]), \
             patch.object(service, '_extract_rationale', return_value="Rationale text"):
            
            response = "Risk assessment results"
            base_result = {
                "text": response,
                "structured_data": {},
                "confidence": "high",
                "metadata": {"version": "v1.0"}
            }
            
            result = service._process_risk_assessment(response, base_result)
            
            assert result["text"] == response
            assert "structured_data" in result
            assert result["structured_data"]["risk_level"] == "low"
            assert len(result["structured_data"]["key_indicators"]) == 1
            assert len(result["structured_data"]["suggested_actions"]) == 1

    def test_create_task_prompt(self, service):
        """Test task prompt creation."""
        user_prompt = "User provided text for analysis"
        context = {"patient_history": "Patient history text"}
        
        # Test depression detection prompt
        depression_prompt = service._create_task_prompt(
            user_prompt, "depression_detection", context
        )
        assert "MentaLLaMA" in depression_prompt
        assert "depression" in depression_prompt.lower()
        assert user_prompt in depression_prompt
        assert "Patient history text" in depression_prompt
        
        # Test risk assessment prompt
        risk_prompt = service._create_task_prompt(
            user_prompt, "risk_assessment", context
        )
        assert "MentaLLaMA" in risk_prompt
        assert "risk assessment" in risk_prompt.lower()
        assert user_prompt in risk_prompt
        
        # Test with no context
        no_context_prompt = service._create_task_prompt(
            user_prompt, "depression_detection"
        )
        assert "MentaLLaMA" in no_context_prompt
        assert user_prompt in no_context_prompt

    @patch('app.core.services.ml.mentalllama.sanitize_text')
    def test_task_specific_methods(self, mock_sanitize, service):
        """Test the specialized task-specific methods."""
        # Set up mocks
        mock_sanitize.return_value = "Sanitized text"
        
        # Mock the process method
        with patch.object(service, 'process') as mock_process:
            mock_process.return_value = {"result": "success"}
            
            # Test depression_detection method
            result = service.depression_detection(
                text="Test text",
                model="mentallama-33b-lora",
                include_rationale=True,
                severity_assessment=True
            )
            mock_process.assert_called_with(
                prompt="Test text",
                model="mentallama-33b-lora",
                task="depression_detection",
                context={"include_rationale": True, "severity_assessment": True},
                **{}
            )
            assert result == {"result": "success"}
            
            # Test risk_assessment method
            result = service.risk_assessment(
                text="Test text",
                model="mentallama-33b-lora",
                include_key_phrases=True,
                include_suggested_actions=True
            )
            mock_process.assert_called_with(
                prompt="Test text",
                model="mentallama-33b-lora",
                task="risk_assessment",
                context={"include_key_phrases": True, "include_suggested_actions": True},
                **{}
            )
            assert result == {"result": "success"}
            
            # Test sentiment_analysis method
            result = service.sentiment_analysis(
                text="Test text",
                model="mentallama-33b-lora",
                include_emotion_distribution=True
            )
            mock_process.assert_called_with(
                prompt="Test text",
                model="mentallama-33b-lora",
                task="sentiment_analysis",
                context={"include_emotion_distribution": True},
                **{}
            )
            assert result == {"result": "success"}
            
            # Test wellness_dimensions method with dimensions
            dimensions = ["emotional", "social", "physical"]
            result = service.wellness_dimensions(
                text="Test text",
                model="mentallama-33b-lora",
                dimensions=dimensions,
                include_recommendations=True
            )
            mock_process.assert_called_with(
                prompt="Test text",
                model="mentallama-33b-lora",
                task="wellness_dimensions",
                context={"dimensions": dimensions, "include_recommendations": True},
                **{}
            )
            assert result == {"result": "success"}

    @patch('app.core.services.ml.mentalllama.boto3')
    def test_setup_aws_client(self, mock_boto3, service):
        """Test AWS Bedrock client setup."""
        # Set up mock session and client
        mock_session = MagicMock()
        mock_bedrock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_bedrock_client
        mock_boto3.client.return_value = mock_bedrock_client
        
        # Set config
        service._config = {
            "aws_region": "us-east-1",
            "aws_profile": "default",
            "timeout": 60
        }
        
        # Call the method
        service._setup_aws_client()
        
        # Verify session and client creation
        mock_boto3.Session.assert_called_once_with(profile_name="default")
        mock_session.client.assert_called_once()
        assert service._client["type"] == "aws-bedrock"
        assert service._client["client"] == mock_bedrock_client
        assert service._client["region"] == "us-east-1"
        
        # Test without profile
        service._config = {
            "aws_region": "us-east-1",
            "timeout": 60
        }
        service._setup_aws_client()
        mock_boto3.client.assert_called_once()

    @patch('app.core.services.ml.mentalllama.boto3')
    def test_setup_aws_client_error(self, mock_boto3, service):
        """Test AWS Bedrock client setup with errors."""
        # Test ImportError
        mock_boto3.side_effect = ImportError("boto3 not installed")
        
        service._config = {
            "aws_region": "us-east-1",
            "timeout": 60
        }
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_aws_client()
        
        assert "AWS SDK not installed" in str(exc_info.value)
        
        # Test other exceptions
        mock_boto3.side_effect = Exception("AWS client error")
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_aws_client()
        
        assert "AWS client initialization failed" in str(exc_info.value)

    @patch('app.core.services.ml.mentalllama.OpenAI')
    def test_setup_openai_client(self, mock_openai, service):
        """Test OpenAI client setup."""
        # Set up mock OpenAI client
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client
        
        # Set config
        service._config = {
            "openai_api_key": "test-api-key",
            "openai_org_id": "test-org",
            "timeout": 60
        }
        
        # Call the method
        service._setup_openai_client()
        
        # Verify client creation
        mock_openai.assert_called_once_with(
            api_key="test-api-key",
            timeout=60,
            organization="test-org"
        )
        assert service._client["type"] == "openai"
        assert service._client["client"] == mock_openai_client

    @patch('app.core.services.ml.mentalllama.OpenAI')
    def test_setup_openai_client_error(self, mock_openai, service):
        """Test OpenAI client setup with errors."""
        # Test ImportError
        mock_openai.side_effect = ImportError("openai not installed")
        
        service._config = {
            "openai_api_key": "test-api-key",
            "timeout": 60
        }
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_openai_client()
        
        assert "OpenAI SDK not installed" in str(exc_info.value)
        
        # Test other exceptions
        mock_openai.side_effect = Exception("OpenAI client error")
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_openai_client()
        
        assert "OpenAI client initialization failed" in str(exc_info.value)

    def test_process_with_provider(self, service):
        """Test provider selection in process method."""
        service._provider = "internal"
        
        # Mock the specific provider methods
        with patch.object(service, '_process_with_internal', return_value="Internal result") as mock_internal, \
             patch.object(service, '_process_with_aws') as mock_aws, \
             patch.object(service, '_process_with_openai') as mock_openai, \
             patch.object(service, '_process_with_anthropic') as mock_anthropic:
            
            result = service._process_with_provider(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            
            assert result == "Internal result"
            mock_internal.assert_called_once_with(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            mock_aws.assert_not_called()
            mock_openai.assert_not_called()
            mock_anthropic.assert_not_called()
            
            # Test AWS provider
            service._provider = "aws-bedrock"
            mock_aws.return_value = "AWS result"
            
            result = service._process_with_provider(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            
            assert result == "AWS result"
            mock_aws.assert_called_once_with(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            
            # Test OpenAI provider
            service._provider = "openai"
            mock_openai.return_value = "OpenAI result"
            
            result = service._process_with_provider(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            
            assert result == "OpenAI result"
            mock_openai.assert_called_once_with(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            
            # Test Anthropic provider
            service._provider = "anthropic"
            mock_anthropic.return_value = "Anthropic result"
            
            result = service._process_with_provider(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            
            assert result == "Anthropic result"
            mock_anthropic.assert_called_once_with(
                "prompt", "model", "task", {"context": "data"}, 100, 0.7
            )
            
            # Test unknown provider
            service._provider = "unknown"
            
            with pytest.raises(ServiceUnavailableError) as exc_info:
                service._process_with_provider(
                    "prompt", "model", "task", {"context": "data"}, 100, 0.7
                )
            
            assert "Unsupported provider" in str(exc_info.value)

    def test_estimate_tokens_used(self, service):
        """Test token estimation method."""
        # Test with empty prompt
        assert service._estimate_tokens_used("", 0) == 0
        
        # Test with short prompt and no response
        assert service._estimate_tokens_used("Short prompt", 0) == 3
        
        # Test with longer prompt and some response tokens
        assert service._estimate_tokens_used("This is a longer prompt that should be tokenized.", 10) == 19
