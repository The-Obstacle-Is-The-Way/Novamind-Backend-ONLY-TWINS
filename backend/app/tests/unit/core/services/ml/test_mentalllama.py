# -*- coding: utf-8 -*-
"""
Unit tests for MentaLLaMA service.

This module tests the MentaLLaMA service implementation with a focus on
depression detection functionality.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import (
    InvalidConfigurationError,  
    InvalidRequestError,  
    ModelNotFoundError,  
    ServiceUnavailableError,  
)
from app.core.services.ml.mentalllama import MentaLLaMA


@pytest.mark.db_required
class TestMentaLLaMA:
    """Test suite for MentaLLaMA service."""

    @pytest.fixture
    def mock_phi_detection(self):
        """Create a mock PHI detection service."""
        mock = MagicMock()
        mock.is_healthy.return_value = True
        mock.detect_phi.return_value = {"has_phi": False}
        mock.redact_phi.return_value = {"redacted_text": "Redacted text"}
        return mock

    @pytest.fixture
    def mock_bedrock_response(self):
        """Create a mock Bedrock response."""
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "completion": json.dumps({
                "depression_signals": {
                    "severity": "mild",
                    "confidence": 0.7,
                    "key_indicators": [
                        {
                            "type": "linguistic",
                            "description": "Negative self-talk",
                            "evidence": "I'm feeling down today"
                        }
                    ]
                },
                "analysis": {
                    "summary": "Mild depression indicators",
                    "warning_signs": ["Negative self-talk"],
                    "protective_factors": ["Social support"],
                    "limitations": ["Limited context"]
                },
                "recommendations": {
                    "suggested_assessments": ["PHQ-9"],
                    "discussion_points": ["Explore coping strategies"]
                }
            })
        })
        return {"body": mock_body}

    @pytest.fixture
    def mentalllama_service(self, mock_phi_detection):
        """Create a MentaLLaMA service instance with mocked dependencies."""
        service = MentaLLaMA(phi_detection_service=mock_phi_detection)
        with patch("boto3.client") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.return_value = mock_client
            service.initialize({
                "model_ids": {
                    "depression_detection": "anthropic.claude-v2:1"
                }
            })
        return service

    def test_initialization(self, mock_phi_detection):
        """Test service initialization with valid configuration."""
        service = MentaLLaMA(phi_detection_service=mock_phi_detection)
        
        with patch("boto3.client") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.return_value = mock_client
            
            service.initialize({
                "model_ids": {
                    "depression_detection": "anthropic.claude-v2:1"
                },
                "aws_region": "us-east-1",
                "aws_access_key_id": "test_key",
                "aws_secret_access_key": "test_secret"
            })
            
            assert service.is_healthy()
            mock_boto3.assert_called_once()

    def test_initialization_missing_model_ids(self, mock_phi_detection):
        """Test service initialization with missing model IDs."""
        service = MentaLLaMA(phi_detection_service=mock_phi_detection)
        
        with patch("boto3.client"), pytest.raises(InvalidConfigurationError):
            service.initialize({})
            
        assert not service.is_healthy()

    def test_initialization_boto_error(self, mock_phi_detection):
        """Test service initialization with Boto error."""
        service = MentaLLaMA(phi_detection_service=mock_phi_detection)
        
        with patch("boto3.client") as mock_boto3:
            mock_boto3.side_effect = ClientError(
                {"Error": {"Code": "InvalidClientTokenId", "Message": "Invalid token"}},
                "CreateClient"
            )
            
            with pytest.raises(InvalidConfigurationError):
                service.initialize({
                    "model_ids": {
                        "depression_detection": "anthropic.claude-v2:1"
                    }
                })
                
        assert not service.is_healthy()

    def test_detect_depression(self, mentalllama_service, mock_bedrock_response):
        """Test depression detection with valid input."""
        with patch.object(:
            mentalllama_service._bedrock_client,
            "invoke_model",
            return_value=mock_bedrock_response
        ):
            result = mentalllama_service.detect_depression("I'm feeling sad today")
            
            assert result["model_type"] == "depression_detection"
            assert "depression_signals" in result
            assert result["depression_signals"]["severity"] == "mild"
            assert result["depression_signals"]["confidence"] == 0.7
            assert len(result["depression_signals"]["key_indicators"]) == 1
            assert "analysis" in result
            assert "recommendations" in result

    def test_detect_depression_empty_text(self, mentalllama_service):
        """Test depression detection with empty text."""
        with pytest.raises(InvalidRequestError):
            mentalllama_service.detect_depression("")

    def test_detect_depression_service_not_initialized(self):
        """Test depression detection with uninitialized service."""
        service = MentaLLaMA()
        
        with pytest.raises(ServiceUnavailableError):
            service.detect_depression("I'm feeling sad today")

    def test_detect_depression_with_phi(self, mentalllama_service, mock_bedrock_response):
        """Test depression detection with PHI in text."""
        # Configure PHI detection mock to detect PHI
        mentalllama_service._phi_detection_service.detect_phi.return_value = {"has_phi": True}
        
        with patch.object(:
            mentalllama_service._bedrock_client,
            "invoke_model",
            return_value=mock_bedrock_response
        ):
            result = mentalllama_service.detect_depression("My name is John Doe and I'm feeling sad")
            
            # Verify PHI detection and redaction was called
            mentalllama_service._phi_detection_service.detect_phi.assert_called_once()
            mentalllama_service._phi_detection_service.redact_phi.assert_called_once()
            
            # Verify result still contains proper depression detection data
            assert "depression_signals" in result
            assert result["depression_signals"]["severity"] == "mild"

    def test_detect_depression_bedrock_error(self, mentalllama_service):
        """Test depression detection with Bedrock error."""
        with patch.object(:
            mentalllama_service._bedrock_client,
            "invoke_model",
            side_effect=ClientError(
                {"Error": {"Code": "InternalServerError", "Message": "Internal error"}},
                "InvokeModel"
            )
        ), pytest.raises(ServiceUnavailableError):
            mentalllama_service.detect_depression("I'm feeling sad today")

    def test_detect_depression_invalid_json_response(self, mentalllama_service):
        """Test depression detection with invalid JSON response."""
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "completion": "This is not a valid JSON response"
        })
        
        with patch.object(:
            mentalllama_service._bedrock_client,
            "invoke_model",
            return_value=mock_response
        ):
            result = mentalllama_service.detect_depression("I'm feeling sad today")
            
            # Verify fallback behavior for invalid JSON
            assert "depression_signals" in result
            assert result["depression_signals"]["severity"] == "unknown"
            assert result["depression_signals"]["confidence"] == 0.0
            assert len(result["depression_signals"]["key_indicators"]) == 0