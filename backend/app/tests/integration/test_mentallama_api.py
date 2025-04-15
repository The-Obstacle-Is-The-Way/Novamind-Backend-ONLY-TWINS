# -*- coding: utf-8 -*-
"""
MentaLLaMA API Integration Tests.

This module contains integration tests for the MentaLLaMA API routes, following
clean architecture principles with precise, mathematically elegant implementations.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config.ml_settings import ml_settings
from app.core.exceptions import (
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError
)

from app.core.services.ml.interface import MentaLLaMAInterface
from app.infrastructure.ml.mentallama.service import MentalLlamaService


# Mock services
@pytest.mark.db_required()
class MockMentaLLaMAService(MentaLLaMAInterface):
    """Mock MentaLLaMA service for testing."""
    
    def __init__(self):
        """Initialize mock service."""
        self.initialized = True
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Mock initialization."""
        self.initialized = True
    
    def is_healthy(self) -> bool:
        """Mock health check."""
        return self.initialized
    
    def shutdown(self) -> None:
        """Mock shutdown."""
        self.initialized = False
    
    def process(
        self,
        prompt: str,
        model: str = None,
        task: str = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock process method."""
        if not prompt:
            raise InvalidRequestError("Prompt cannot be empty")
        
        if model and model not in ["mentallama-7b", "mentallama-33b", "mentallama-33b-lora"]:
            raise ModelNotFoundError(f"Model {model} not found")
        
        # Return mock response
        return {
            "response_id": str(uuid.uuid4()),
            "model": model or "mentallama-33b",
            "provider": "aws-bedrock",
            "text": "This is a mock response from MentaLLaMA.",
            "confidence": "high",
            "processing_time": 0.5,
            "tokens_used": 50,
            "created_at": datetime.now().isoformat()
        }
    
    def analyze_text(
        self,
        text: str,
        analysis_type: str = "comprehensive",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock text analysis method."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        # Return mock response
        return {
            "response_id": str(uuid.uuid4()),
            "model": "mentallama-33b",
            "provider": "aws-bedrock",
            "text": "This is a mock analysis response.",
            "structured_data": {
                "sentiment": "neutral",
                "entities": [{"type": "symptom", "text": "depression", "confidence": 0.9}],
                "keywords": ["mood", "sleep", "anxiety"],
                "categories": ["mental health", "depression"]
            },
            "confidence": "high",
            "processing_time": 0.5,
            "tokens_used": 75,
            "created_at": datetime.now().isoformat()
        }
    
    def detect_mental_health_conditions(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock condition detection method."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        # Return mock response
        return {
            "response_id": str(uuid.uuid4()),
            "model": "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "Analysis indicates potential depression and anxiety.",
            "structured_data": {
                "conditions": [
                    {
                        "condition": "Depression",
                        "confidence": 0.85,
                        "evidence": ["low mood", "sleep disturbance"]
                    },
                    {
                        "condition": "Anxiety",
                        "confidence": 0.75,
                        "evidence": ["worry", "restlessness"]
                    }
                ]
            },
            "confidence": "high",
            "processing_time": 0.6,
            "tokens_used": 90,
            "created_at": datetime.now().isoformat()
        }
    
    def generate_therapeutic_response(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock therapeutic response generation."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        # Return mock response
        return {
            "response_id": str(uuid.uuid4()),
            "model": "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "I understand you're feeling down. Let's explore some coping strategies.",
            "structured_data": {
                "therapeutic_approach": "CBT",
                "techniques": ["validation", "reframing", "behavioral activation"],
                "follow_up_questions": ["How have you been sleeping?", "What activities bring you joy?"]
            },
            "confidence": "high",
            "processing_time": 0.7,
            "tokens_used": 100,
            "created_at": datetime.now().isoformat()
        }
    
    def assess_suicide_risk(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock suicide risk assessment."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        # Return mock response
        return {
            "response_id": str(uuid.uuid4()),
            "model": "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "Risk assessment indicates low immediate risk but presence of risk factors.",
            "structured_data": {
                "risk_level": "low",
                "risk_factors": ["hopelessness", "isolation"],
                "protective_factors": ["future plans", "social support"],
                "recommendations": ["regular check-ins", "safety planning"],
                "immediate_action_required": False
            },
            "confidence": "high",
            "processing_time": 0.8,
            "tokens_used": 120,
            "created_at": datetime.now().isoformat()
        }
    
    def analyze_wellness_dimensions(
        self,
        text: str,
        dimensions: List[str],
        include_recommendations: bool = False,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock wellness dimensions analysis."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        if not dimensions:
            raise InvalidRequestError("At least one dimension must be specified")
            
        # Return mock response
        return {
            "response_id": str(uuid.uuid4()),
            "model": "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "Wellness analysis complete across specified dimensions.",
            "structured_data": {
                "dimensions": {
                    dim: {
                        "score": round(0.5 + 0.4 * (i/len(dimensions)), 2), 
                        "insights": [f"Sample insight for {dim}"],
                        "recommendations": [f"Sample recommendation for {dim}"] if include_recommendations else []
                    }
                    for i, dim in enumerate(dimensions)
                }
            },
            "confidence": "high",
            "processing_time": 0.8,
            "tokens_used": 120,
            "created_at": datetime.now().isoformat()
        }


@pytest.fixture
def mock_services():
    """Fixture to provide mock services for testing."""
    # Create mock service
    mock_service = MockMentaLLaMAService()
    
    # Patch the get_mentallama_service function
    with patch("app.core.services.ml.factory.get_mentallama_service", return_value=mock_service):
        yield mock_service


@pytest.fixture
def mock_auth():
    """Fixture to mock authentication middleware."""
    with patch("app.api.routes.ml.verify_api_key", return_value=True):
        yield


@pytest.mark.integration()
class TestMentaLLaMAAPI:
    """Integration tests for MentaLLaMA API endpoints.
    
    This test suite verifies the correctness and robustness of the MentaLLaMA API
    with mathematically precise validation of inputs, outputs, and error cases.
    """
    
    def test_process_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the process endpoint."""
        # Prepare test data
        payload = {
            "prompt": "Tell me about depression",
            "model": "mentallama-33b",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/process",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "mentallama-33b"
        assert "text" in data
        assert data["provider"] == "aws-bedrock"
    
    def test_process_invalid_model(self, client: TestClient, mock_services, mock_auth):
        """Test process endpoint with invalid model."""
        # Prepare test data
        payload = {
            "prompt": "Tell me about anxiety",
            "model": "invalid-model",
            "max_tokens": 100
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/process",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_process_empty_prompt(self, client: TestClient, mock_services, mock_auth):
        """Test process endpoint with empty prompt."""
        # Prepare test data
        payload = {
            "prompt": "",
            "model": "mentallama-33b"
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/process",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
    
    def test_analyze_text_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the analyze_text endpoint."""
        # Prepare test data
        payload = {
            "text": "I've been feeling sad and tired lately, and I'm not sleeping well.",
            "analysis_type": "comprehensive"
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/analyze",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "structured_data" in data
        assert "sentiment" in data["structured_data"]
        assert "entities" in data["structured_data"]
    
    def test_detect_conditions_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the detect_mental_health_conditions endpoint."""
        # Prepare test data
        payload = {
            "text": "I worry constantly and can't sleep. I've lost interest in activities I used to enjoy."
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/detect_conditions",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "structured_data" in data
        assert "conditions" in data["structured_data"]
        conditions = data["structured_data"]["conditions"]
        assert len(conditions) > 0
        assert "condition" in conditions[0]
        assert "confidence" in conditions[0]
    
    def test_therapeutic_response_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the generate_therapeutic_response endpoint."""
        # Prepare test data
        payload = {
            "text": "I feel very alone and hopeless.",
            "context": {
                "patient_history": "Previous diagnosis of depression",
                "therapy_approach": "CBT"
            }
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/therapeutic_response",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "structured_data" in data
        assert "therapeutic_approach" in data["structured_data"]
        assert "techniques" in data["structured_data"]
    
    def test_suicide_risk_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the assess_suicide_risk endpoint."""
        # Prepare test data
        payload = {
            "text": "I don't see any point in going on. Nothing will ever get better.",
            "context": {
                "previous_attempts": False,
                "support_network": "Limited"
            }
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/suicide_risk",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "structured_data" in data
        assert "risk_level" in data["structured_data"]
        assert "risk_factors" in data["structured_data"]
        assert "protective_factors" in data["structured_data"]
        assert "recommendations" in data["structured_data"]
        assert "immediate_action_required" in data["structured_data"]
    
    def test_wellness_dimensions_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the analyze_wellness_dimensions endpoint."""
        # Prepare test data
        payload = {
            "text": "I've been exercising regularly but feel socially isolated. Work is stressful.",
            "dimensions": ["physical", "social", "occupational", "emotional"],
            "include_recommendations": True
        }
        
        # Call API
        response = client.post(
            f"{ml_settings.api_prefix}/wellness_dimensions",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "structured_data" in data
        assert "dimensions" in data["structured_data"]
        dimensions = data["structured_data"]["dimensions"]
        assert "physical" in dimensions
        assert "score" in dimensions["physical"]
        assert "recommendations" in dimensions["physical"]
    
    def test_health_check(self, client: TestClient, mock_services):
        """Test the health check endpoint."""
        # Call API
        response = client.get(f"{ml_settings.api_prefix}/health")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == ml_settings.version
    
    def test_service_unavailable(self, client: TestClient, mock_auth):
        """Test behavior when service is unavailable."""
        # Mock service unavailable
        with patch("app.core.services.ml.factory.get_mentallama_service", 
                   side_effect=ServiceUnavailableError("Service unavailable")):
            
            # Call API
            response = client.post(
                f"{ml_settings.api_prefix}/process",
                json={"prompt": "Test prompt"},
                headers={"X-API-Key": "test_key"}
            )
            
            # Verify response
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "unavailable" in data["detail"].lower()
