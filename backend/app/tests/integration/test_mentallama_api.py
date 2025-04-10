# -*- coding: utf-8 -*-
"""
MentaLLaMA API Integration Tests.

This module contains integration tests for the MentaLLaMA API routes.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.ml import router as ml_router
from app.core.config.ml_settings import ml_settings
from app.core.exceptions import (
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)
from app.core.services.ml.interface import MentaLLaMAInterface, MLService


# Local app/client fixtures removed; tests will use the client fixture from conftest.py


# Mock services
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
        
        if model == "nonexistent-model":
            raise ModelNotFoundError("Model not found", model_name=model)
        
        return {
            "response_id": str(uuid.uuid4()),
            "model": model or "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": f"Mock response for: {prompt[:30]}...",
            "structured_data": {"raw_text": f"Mock response for: {prompt[:30]}..."},
            "confidence": "high",
            "processing_time": 0.5,
            "tokens_used": 100,
            "created_at": datetime.now().isoformat(),
            "metadata": {"task": task or "general_analysis"}
        }
    
    def depression_detection(
        self, 
        text: str, 
        model: str = None,
        include_rationale: bool = True,
        severity_assessment: bool = True,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock depression detection."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        if model == "nonexistent-model":
            raise ModelNotFoundError("Model not found", model_name=model)
        
        structured_data = {
            "depression_indicated": True,
            "severity": "moderate",
            "key_indicators": ["depressed mood", "fatigue", "sleep disturbance"]
        }
        
        if include_rationale:
            structured_data["rationale"] = "Mock rationale for depression detection"
        
        return {
            "response_id": str(uuid.uuid4()),
            "model": model or "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "Mock depression detection analysis",
            "structured_data": structured_data,
            "confidence": "high",
            "processing_time": 0.5,
            "tokens_used": 120,
            "created_at": datetime.now().isoformat()
        }
    
    def risk_assessment(
        self, 
        text: str, 
        model: str = None,
        include_key_phrases: bool = True,
        include_suggested_actions: bool = True,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock risk assessment."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        if model == "nonexistent-model":
            raise ModelNotFoundError("Model not found", model_name=model)
        
        structured_data = {
            "risk_level": "low",
            "key_indicators": ["concern about future", "minor sleep issues"],
            "rationale": "Mock rationale for risk assessment"
        }
        
        if include_suggested_actions:
            structured_data["suggested_actions"] = [
                "Regular follow-up", 
                "Monitor sleep patterns"
            ]
        
        return {
            "response_id": str(uuid.uuid4()),
            "model": model or "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "Mock risk assessment analysis",
            "structured_data": structured_data,
            "confidence": "high",
            "processing_time": 0.5,
            "tokens_used": 130,
            "created_at": datetime.now().isoformat()
        }
    
    def sentiment_analysis(
        self, 
        text: str, 
        model: str = None,
        include_emotion_distribution: bool = True,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock sentiment analysis."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        if model == "nonexistent-model":
            raise ModelNotFoundError("Model not found", model_name=model)
        
        structured_data = {
            "overall_sentiment": "mixed",
            "sentiment_score": 0.2,
            "key_phrases": ["looking forward", "feeling tired"]
        }
        
        if include_emotion_distribution:
            structured_data["emotion_distribution"] = {
                "joy": 0.3,
                "sadness": 0.2,
                "anger": 0.1,
                "fear": 0.1,
                "surprise": 0.1,
                "disgust": 0.0,
                "neutral": 0.2
            }
        
        return {
            "response_id": str(uuid.uuid4()),
            "model": model or "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "Mock sentiment analysis",
            "structured_data": structured_data,
            "confidence": "high",
            "processing_time": 0.5,
            "tokens_used": 110,
            "created_at": datetime.now().isoformat()
        }
    
    def wellness_dimensions(
        self, 
        text: str, 
        model: str = None,
        dimensions: Optional[List[str]] = None,
        include_recommendations: bool = True,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock wellness dimensions."""
        if not text:
            raise InvalidRequestError("Text cannot be empty")
        
        if model == "nonexistent-model":
            raise ModelNotFoundError("Model not found", model_name=model)
        
        dim_list = dimensions or ["emotional", "social", "physical", "intellectual"]
        
        structured_data = {
            "dimension_scores": {dim: 0.7 for dim in dim_list},
            "areas_of_strength": ["social connection", "intellectual engagement"],
            "areas_for_improvement": ["physical activity", "emotional regulation"]
        }
        
        if include_recommendations:
            structured_data["recommendations"] = [
                "Increase daily physical activity",
                "Practice mindfulness for emotional regulation"
            ]
        
        return {
            "response_id": str(uuid.uuid4()),
            "model": model or "mentallama-33b-lora",
            "provider": "aws-bedrock",
            "text": "Mock wellness dimensions analysis",
            "structured_data": structured_data,
            "confidence": "high",
            "processing_time": 0.5,
            "tokens_used": 140,
            "created_at": datetime.now().isoformat()
        }


# Mock authentication
@pytest.fixture
def mock_auth(client: TestClient): # Add client fixture dependency if needed by patch target
    """Mock authentication."""
    with patch("app.api.auth.dependencies.get_current_user") as mock:
        mock.return_value = {
            "user_id": "test-user",
            "email": "test@example.com",
            "roles": ["provider", "admin"]
        }
        yield mock


@pytest.fixture
def mock_services(client: TestClient): # Add client fixture dependency if needed by patch target
    """Mock ML services."""
    # Enable services in settings
    ml_settings.enable_mentallama = True
    ml_settings.enable_phi_detection = True
    ml_settings.enable_digital_twin = True
    
    with patch("app.api.routes.ml.get_mentalllama_service") as mock_mentalllama:
        mock_mentalllama.return_value = MockMentaLLaMAService()
        yield {
            "mentalllama": mock_mentalllama
        }


# Tests
def test_process_text(client: TestClient, mock_auth, mock_services):
    """Test process text endpoint."""
    request_data = {
        "prompt": "This is a test prompt for processing.",
        "task": "general_analysis",
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/api/v1/ml/process", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "response_id" in data
    assert data["model"] == "mentallama-33b-lora"
    assert data["provider"] == "aws-bedrock"
    assert "text" in data
    assert "structured_data" in data
    assert data["confidence"] == "high"
    assert "processing_time" in data
    assert data["tokens_used"] == 100
    assert "created_at" in data
    assert data["metadata"]["task"] == "general_analysis"


def test_process_text_with_missing_prompt(client: TestClient, mock_auth, mock_services):
    """Test process text endpoint with missing prompt."""
    request_data = {
        "prompt": "",  # Empty prompt
        "task": "general_analysis"
    }
    
    # Mock invalid request error
    mock_services["mentalllama"].return_value.process.side_effect = InvalidRequestError("Prompt cannot be empty")
    
    response = client.post("/api/v1/ml/process", json=request_data)
    
    assert response.status_code == 400
    assert "detail" in response.json()


def test_process_text_with_nonexistent_model(client: TestClient, mock_auth, mock_services):
    """Test process text endpoint with nonexistent model."""
    request_data = {
        "prompt": "This is a test prompt for processing.",
        "model": "nonexistent-model",
        "task": "general_analysis"
    }
    
    # Mock service to return model not found error
    mock_svc = MockMentaLLaMAService()
    mock_services["mentalllama"].return_value = mock_svc
    
    response = client.post("/api/v1/ml/process", json=request_data)
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_depression_detection(client: TestClient, mock_auth, mock_services):
    """Test depression detection endpoint."""
    request_data = {
        "text": "This is a test text for depression detection.",
        "include_rationale": True,
        "severity_assessment": True,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/api/v1/ml/depression-detection", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "response_id" in data
    assert data["model"] == "mentallama-33b-lora"
    assert data["provider"] == "aws-bedrock"
    assert "text" in data
    assert "structured_data" in data
    assert "depression_indicated" in data["structured_data"]
    assert "severity" in data["structured_data"]
    assert "key_indicators" in data["structured_data"]
    assert "rationale" in data["structured_data"]
    assert data["confidence"] == "high"
    assert "processing_time" in data
    assert data["tokens_used"] == 120
    assert "created_at" in data


def test_risk_assessment(client: TestClient, mock_auth, mock_services):
    """Test risk assessment endpoint."""
    request_data = {
        "text": "This is a test text for risk assessment.",
        "include_key_phrases": True,
        "include_suggested_actions": True,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/api/v1/ml/risk-assessment", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "response_id" in data
    assert data["model"] == "mentallama-33b-lora"
    assert data["provider"] == "aws-bedrock"
    assert "text" in data
    assert "structured_data" in data
    assert "risk_level" in data["structured_data"]
    assert "key_indicators" in data["structured_data"]
    assert "suggested_actions" in data["structured_data"]
    assert "rationale" in data["structured_data"]
    assert data["confidence"] == "high"
    assert "processing_time" in data
    assert data["tokens_used"] == 130
    assert "created_at" in data


def test_sentiment_analysis(client: TestClient, mock_auth, mock_services):
    """Test sentiment analysis endpoint."""
    request_data = {
        "text": "This is a test text for sentiment analysis.",
        "include_emotion_distribution": True,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/api/v1/ml/sentiment-analysis", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "response_id" in data
    assert data["model"] == "mentallama-33b-lora"
    assert data["provider"] == "aws-bedrock"
    assert "text" in data
    assert "structured_data" in data
    assert "overall_sentiment" in data["structured_data"]
    assert "sentiment_score" in data["structured_data"]
    assert "key_phrases" in data["structured_data"]
    assert "emotion_distribution" in data["structured_data"]
    assert data["confidence"] == "high"
    assert "processing_time" in data
    assert data["tokens_used"] == 110
    assert "created_at" in data


def test_wellness_dimensions(client: TestClient, mock_auth, mock_services):
    """Test wellness dimensions endpoint."""
    request_data = {
        "text": "This is a test text for wellness dimensions analysis.",
        "dimensions": ["emotional", "social", "physical", "intellectual"],
        "include_recommendations": True,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/api/v1/ml/wellness-dimensions", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "response_id" in data
    assert data["model"] == "mentallama-33b-lora"
    assert data["provider"] == "aws-bedrock"
    assert "text" in data
    assert "structured_data" in data
    assert "dimension_scores" in data["structured_data"]
    assert "areas_of_strength" in data["structured_data"]
    assert "areas_for_improvement" in data["structured_data"]
    assert "recommendations" in data["structured_data"]
    assert data["confidence"] == "high"
    assert "processing_time" in data
    assert data["tokens_used"] == 140
    assert "created_at" in data


def test_health_check(client: TestClient, mock_services):
    """Test health check endpoint."""
    response = client.get("/api/v1/ml/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "services" in data
    assert "mentalllama" in data["services"]
    assert data["services"]["mentalllama"]["enabled"] is True
    assert data["services"]["mentalllama"]["healthy"] is True


def test_service_unavailable(client: TestClient, mock_auth):
    """Test service unavailable error."""
    # Disable MentaLLaMA service
    ml_settings.enable_mentallama = False
    
    request_data = {
        "prompt": "This is a test prompt for processing.",
        "task": "general_analysis"
    }
    
    response = client.post("/api/v1/ml/process", json=request_data)
    
    assert response.status_code == 503
    assert "detail" in response.json()
    
    # Re-enable MentaLLaMA service after test
    ml_settings.enable_mentallama = True