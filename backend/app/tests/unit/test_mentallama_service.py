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
        service._initialized = True 
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
    def test_process_method(
        self,
        mock_datetime,
        mock_uuid,
        mock_sanitize,
        mock_json,
        service,
        mock_config
    ):
        """Test process method for task execution."""
        # Set up mocks
        mock_uuid_val = uuid.UUID('12345678-1234-5678-1234-567812345678')
        mock_uuid.return_value = mock_uuid_val
        mock_now = datetime(2025, 3, 28, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        # Assuming UTC is used, adjust if necessary
        mock_datetime.now.return_value.isoformat.return_value = mock_now.isoformat() + '+00:00'
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
            assert result["response_id"] == str(mock_uuid_val)
            assert result["model"] == "mentallama-33b-lora"
            assert result["task"] == "depression_detection"
            assert result["provider"] == "internal"
            assert result["text"] == "Processed model response"
            assert result["structured_data"] == {"key": "value"}
            assert result["tokens_used"] == 100
            assert result["created_at"] == mock_now.isoformat() + '+00:00'
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
        # Initialize service first
        with patch.object(service, '_setup_client'), \
             patch.object(service, '_load_models'):
            service.initialize({"provider": "internal"}) # Minimal config
            service._models = {"existing-model": {}} # Mock models exist

        with pytest.raises(ModelNotFoundError) as exc_info:
            service.process(
                prompt="Test prompt",
                model="non-existent-model",
                task="any_task"
            )
        assert "Model 'non-existent-model' not found" in str(exc_info.value)

    def test_process_unsupported_task(self, service):
        """Test process method with unsupported task."""
        # Initialize service first
        with patch.object(service, '_setup_client'), \
             patch.object(service, '_load_models'):
            service.initialize({"provider": "internal"}) # Minimal config
            # Mock model supports 'depression_detection' only
            service._models = {
                "mentallama-33b-lora": {
                    "capabilities": ["depression_detection"]
                }
            }

        with pytest.raises(InvalidRequestError) as exc_info:
            service.process(
                prompt="Test prompt",
                model="mentallama-33b-lora",
                task="unsupported_task"
            )
        assert "Task 'unsupported_task' not supported" in str(exc_info.value)

    @patch('app.core.services.ml.mentalllama.sanitize_text')
    def test_sanitize_input(self, mock_sanitize, service):
        """Test PHI sanitization function."""
        # Setup service with PHI detection enabled
        mock_config = {
            "provider": "internal",
            "phi_detection": {
                "enabled": True,
                "sensitivity": 0.8,
                "redact_mode": "token"
            }
        }
        with patch.object(service, '_setup_client'), \
             patch.object(service, '_load_models'):
            service.initialize(mock_config)

        # Mock the PHI detection service
        service._phi_detector = MagicMock()
        service._phi_detector.detect_phi.return_value = (
            "Sanitized text with [REDACTED]",
            [{"Type": "NAME", "Score": 0.9, "BeginOffset": 5, "EndOffset": 10}]
        )

        # Call sanitize input
        sanitized_prompt, phi_detected = service._sanitize_input("Hello John Doe")

        # Verify results
        assert sanitized_prompt == "Sanitized text with [REDACTED]"
        assert phi_detected is True
        service._phi_detector.detect_phi.assert_called_once_with("Hello John Doe", 0.8, "token")

    # ... Add more tests for post-processing, prompt creation, etc. ...

    def test_post_process_response_depression_detection(self, service):
        """Test post-processing for depression detection task."""
        response = "Some response text about depression."
        base_result = {"model": "test-model", "task": "depression_detection"}
        # Assume _extract_depression_level exists and works
        with patch.object(service, '_extract_depression_level', return_value="moderate"):
            result = service._post_process_response(response, base_result)

        assert result["text"] == response
        assert "structured_data" in result
        assert result["structured_data"]["depression_level"] == "moderate"

    def test_post_process_response_risk_assessment(self, service):
        """Test post-processing for risk assessment task."""
        response = "Some response text about risk."
        base_result = {"model": "test-model", "task": "risk_assessment"}
        # Mock extraction methods
        with patch.object(service, '_extract_risk_level', return_value="low"), \
             patch.object(service, '_extract_risk_factors', return_value=["factor1", "factor2"]):
            result = service._post_process_response(response, base_result)

        assert result["text"] == response
        assert "structured_data" in result
        assert result["structured_data"]["risk_level"] == "low"
        assert result["structured_data"]["risk_factors"] == ["factor1", "factor2"]

    # Add similar tests for other tasks: anxiety, bipolar, suicide, substance_use

    def test_create_task_prompt(self, service):
        """Test task prompt creation."""
        user_prompt = "User provided text for analysis"
        context = {"patient_history": "Patient history text"}

        # Test depression detection prompt
        depression_prompt = service._create_task_prompt(
            task="depression_detection",
            user_prompt=user_prompt,
            context=context
        )
        assert "Analyze the following text for signs of depression" in depression_prompt
        assert user_prompt in depression_prompt
        assert context["patient_history"] in depression_prompt

        # Test risk assessment prompt
        risk_prompt = service._create_task_prompt(
            task="risk_assessment",
            user_prompt=user_prompt,
            context=context
        )
        assert "Assess the suicide risk level based on the text" in risk_prompt
        assert user_prompt in risk_prompt
        assert context["patient_history"] in risk_prompt

    # Add more tests for other task prompts

    @patch('app.core.services.ml.mentalllama.sanitize_text') # Mock sanitize for simplicity
    def test_task_specific_methods(self, mock_sanitize, service):
        """Test the specialized task-specific methods."""
        mock_config = {"provider": "internal"}
        with patch.object(service, '_setup_client'), \
             patch.object(service, '_load_models'):
            service.initialize(mock_config)
            service._models = {
                "test-model": {
                    "capabilities": [
                        "depression_detection", "risk_assessment", "anxiety_detection",
                        "bipolar_disorder_detection", "suicide_risk_assessment",
                        "substance_use_disorder_detection"
                    ]
                }
            }

        prompt = "Test prompt for analysis."
        model = "test-model"
        context = {"patient_id": "123"}
        mock_sanitize.return_value = prompt # Assume sanitize returns original

        # Mock the generic process method to check args
        with patch.object(service, 'process') as mock_process:
            # Test depression_detection
            service.depression_detection(prompt, model, context)
            mock_process.assert_called_with(
                prompt=prompt, model=model, task='depression_detection', context=context,
                max_tokens=None, temperature=None
            )

            # Test risk_assessment
            service.risk_assessment(prompt, model, context)
            mock_process.assert_called_with(
                prompt=prompt, model=model, task='risk_assessment', context=context,
                max_tokens=None, temperature=None
            )

            # Test anxiety_detection
            service.anxiety_detection(prompt, model, context)
            mock_process.assert_called_with(
                prompt=prompt, model=model, task='anxiety_detection', context=context,
                max_tokens=None, temperature=None
            )

            # Test bipolar_disorder_detection
            service.bipolar_disorder_detection(prompt, model, context)
            mock_process.assert_called_with(
                prompt=prompt, model=model, task='bipolar_disorder_detection', context=context,
                max_tokens=None, temperature=None
            )

            # Test suicide_risk_assessment
            service.suicide_risk_assessment(prompt, model, context)
            mock_process.assert_called_with(
                prompt=prompt, model=model, task='suicide_risk_assessment', context=context,
                max_tokens=None, temperature=None
            )

            # Test substance_use_disorder_detection
            service.substance_use_disorder_detection(prompt, model, context)
            mock_process.assert_called_with(
                prompt=prompt, model=model, task='substance_use_disorder_detection', context=context,
                max_tokens=None, temperature=None
            )

    @patch('app.core.services.ml.mentalllama.boto3')
    def test_setup_aws_client(self, mock_boto3, service):
        """Test AWS Bedrock client setup."""
        mock_session = MagicMock()
        mock_bedrock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_bedrock_client

        service._config = {
            "aws_region": "us-east-1",
            "aws_access_key_id": "test_key_id",
            "aws_secret_access_key": "test_secret_key"
        }

        # Call the method
        service._setup_aws_client()

        # Verify session and client creation
        mock_boto3.Session.assert_called_once_with(
            region_name="us-east-1",
            aws_access_key_id="test_key_id",
            aws_secret_access_key="test_secret_key"
        )
        mock_session.client.assert_called_once_with('bedrock-runtime')
        assert service._client is mock_bedrock_client
        assert service._aws_session is mock_session

    @patch('app.core.services.ml.mentalllama.boto3')
    def test_setup_aws_client_error(self, mock_boto3, service):
        """Test AWS Bedrock client setup with errors."""
        # Test ImportError
        mock_boto3.side_effect = ImportError("boto3 not installed")

        service._config = {
            "aws_region": "us-east-1",
            "aws_access_key_id": "test_key_id",
            "aws_secret_access_key": "test_secret_key"
        }

        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_aws_client()
        assert "boto3 is required" in str(exc_info.value)

        # Reset side effect for next test
        mock_boto3.side_effect = None

        # Test general exception during client creation
        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.side_effect = Exception("AWS client error")

        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_aws_client()
        assert "Failed to create AWS Bedrock client" in str(exc_info.value)

    @patch('app.core.services.ml.mentalllama.openai')
    def test_setup_openai_client(self, mock_openai, service):
        """Test OpenAI client setup."""
        mock_openai_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_openai_client

        service._config = {
            "openai_api_key": "test-api-key",
            "openai_organization": "test-org-id"
        }

        # Call the method
        service._setup_openai_client()

        # Verify client creation
        mock_openai.OpenAI.assert_called_once_with(
            api_key="test-api-key",
            organization="test-org-id"
        )
        assert service._client is mock_openai_client

    @patch('app.core.services.ml.mentalllama.openai')
    def test_setup_openai_client_error(self, mock_openai, service):
        """Test OpenAI client setup with errors."""
        # Test ImportError
        mock_openai.side_effect = ImportError("openai not installed")

        service._config = {
            "openai_api_key": "test-api-key",
        }

        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_openai_client()
        assert "openai library is required" in str(exc_info.value)

        # Reset side effect for next test
        mock_openai.side_effect = None

        # Test general exception during client creation
        mock_openai.OpenAI.side_effect = Exception("OpenAI client error")

        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._setup_openai_client()
        assert "Failed to create OpenAI client" in str(exc_info.value)

    def test_process_with_provider(self, service):
        """Test provider selection in process method."""
        # --- Test Internal Provider ---
        service._provider = "internal"
        service._client = MagicMock()
        service._client.generate.return_value = "Internal response"
        service._models = {"test-model": {"some_detail": True}}

        result = service._process_with_provider("prompt", "test-model", "task", {}, 100, 0.7)
        assert result == "Internal response"
        service._client.generate.assert_called_once_with(
            prompt="prompt", model="test-model", task="task", context={},
            max_tokens=100, temperature=0.7, model_details=service._models["test-model"]
        )

        # --- Test AWS Provider ---
        service._provider = "aws"
        service._client = MagicMock()
        # Mock the specific invoke_model method
        mock_response = {"body": MagicMock()}
        mock_response["body"].read.return_value = json.dumps({"completion": "AWS response"}).encode('utf-8')
        service._client.invoke_model.return_value = mock_response
        service._models = {"test-model": {"aws_model_id": "amazon.titan-text-express-v1"}}

        result = service._process_with_provider("prompt", "test-model", "task", {}, 100, 0.7)
        assert result == "AWS response"
        expected_body = json.dumps({
            "inputText": "prompt",
            "textGenerationConfig": {
                "maxTokenCount": 100,
                "temperature": 0.7,
                "stopSequences": []
            }
        })
        service._client.invoke_model.assert_called_once_with(
            modelId="amazon.titan-text-express-v1",
            contentType='application/json',
            accept='application/json',
            body=expected_body
        )

        # --- Test OpenAI Provider ---
        service._provider = "openai"
        service._client = MagicMock()
        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [MagicMock(message=MagicMock(content="OpenAI response"))]
        service._client.chat.completions.create.return_value = mock_chat_completion
        service._models = {"test-model": {"openai_model_id": "gpt-4"}}

        result = service._process_with_provider("prompt", "test-model", "task", {}, 100, 0.7)
        assert result == "OpenAI response"
        service._client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "prompt"}],
            max_tokens=100,
            temperature=0.7
        )

        # --- Test Unknown Provider ---
        service._provider = "unknown"
        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._process_with_provider("prompt", "test-model", "task", {}, 100, 0.7)
        assert "Unknown provider 'unknown'" in str(exc_info.value)
