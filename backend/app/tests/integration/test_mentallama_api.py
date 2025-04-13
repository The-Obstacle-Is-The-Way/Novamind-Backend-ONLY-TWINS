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
from app.core.exceptions import ()
InvalidRequestError,  
ModelNotFoundError,  
ServiceUnavailableError,  

from app.core.services.ml.interface import MentaLLaMAInterface # Removed non-existent MLService


# Local app/client fixtures removed; tests will use the client fixture from conftest.py


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
    
        def process()
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
#                 return {
"response_id": str(uuid.uuid4()),
"model": model or "mentallama-33b",
"provider": "aws-bedrock",
"text": "This is a mock response from MentaLLaMA.",
"confidence": "high",
"processing_time": 0.5,
"tokens_used": 50,
"created_at": datetime.now().isoformat(),
}
    
def analyze_text()
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
#                 return {
"response_id": str(uuid.uuid4()),
"model": "mentallama-33b",
"provider": "aws-bedrock",
"text": "This is a mock analysis response.",
"structured_data": {
"sentiment": "neutral",
"entities": [{"type": "symptom", "text": "depression", "confidence": 0.9}],
"keywords": ["mood", "sleep", "anxiety"],
"categories": ["mental health", "depression"],
},
"confidence": "high",
"processing_time": 0.5,
"tokens_used": 75,
"created_at": datetime.now().isoformat(),
}
    
def detect_mental_health_conditions()
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
#                 return {
"response_id": str(uuid.uuid4()),
"model": "mentallama-33b-lora",
"provider": "aws-bedrock",
"text": "Analysis indicates potential depression and anxiety.",
"structured_data": {
"conditions": []
{
"condition": "Depression",
"confidence": 0.85,
"evidence": ["low mood", "sleep disturbance"],
},
{
"condition": "Anxiety",
"confidence": 0.75,
"evidence": ["worry", "restlessness"],
}
                
},
"confidence": "high",
"processing_time": 0.6,
"tokens_used": 90,
"created_at": datetime.now().isoformat(),
}
    
def generate_therapeutic_response()
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
#                 return {
"response_id": str(uuid.uuid4()),
"model": "mentallama-33b-lora",
"provider": "aws-bedrock",
"text": "I understand you're feeling down. Let's explore some coping strategies.",
"structured_data": {
"therapeutic_approach": "CBT",
"techniques": ["validation", "reframing", "behavioral activation"],
"follow_up_questions": ["How have you been sleeping?", "What activities bring you joy?"],
},
"confidence": "high",
"processing_time": 0.7,
"tokens_used": 100,
"created_at": datetime.now().isoformat(),
}
    
def assess_suicide_risk()
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
#                 return {
"response_id": str(uuid.uuid4()),
"model": "mentallama-33b-lora",
"provider": "aws-bedrock",
"text": "Risk assessment indicates low immediate risk but presence of risk factors.",
"structured_data": {
"risk_level": "low",
"risk_factors": ["hopelessness", "isolation"],
"protective_factors": ["future plans", "social support"],
"recommendations": ["regular check-ins", "safety planning"],
"immediate_action_required": False,
},
"confidence": "high",
"processing_time": 0.8,
"tokens_used": 120,
"created_at": datetime.now().isoformat(),
}
    
def analyze_wellness_dimensions()
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
        raise InvalidRequestError("Dimensions cannot be empty")
        
        # Return mock response
#                 return {
"response_id": str(uuid.uuid4()),
"model": "mentallama-33b-lora",
"provider": "aws-bedrock",
"text": "Analysis of wellness dimensions complete.",
"structured_data": {
"dimension_scores": {dim: round(0.5 + 0.1 * i, 1) for i, dim in enumerate(dimensions)},
"areas_of_strength": [dimensions[0]],
"areas_for_improvement": [dimensions[-1]],
"recommendations": ["daily exercise", "mindfulness practice"] if include_recommendations else [],
},
"confidence": "high",
"processing_time": 0.9,
"tokens_used": 140,
"created_at": datetime.now().isoformat(),
}


@pytest.fixture
            def mock_services():
"""Fixture to provide mock services for testing."""
# Create mock service
mock_service = MockMentaLLaMAService()
    
# Patch the get_mentallama_service function
    with patch("app.api.routes.ml.get_mentallama_service", return_value=mock_service):
        yield mock_service


@pytest.fixture
        def mock_auth():
"""Fixture to mock authentication middleware."""
    with patch("app.api.routes.ml.verify_api_key", return_value=True):
        yield


@pytest.mark.integration()
class TestMentaLLaMAAPI:
    """Integration tests for MentaLLaMA API endpoints."""
    
    def test_process_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the process endpoint."""
        request_data = {
        "prompt": "This is a test prompt for processing.",
        "model": "mentallama-33b",
        "task": "general_analysis",
        "max_tokens": 100,
        "temperature": 0.7
        }
        
        response = client.post("/api/v1/ml/process", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "response_id" in data
        assert data["model"] == "mentallama-33b"
        assert data["provider"] == "aws-bedrock"
        assert "text" in data
        assert data["confidence"] == "high"
        assert "processing_time" in data
        assert data["tokens_used"] == 50
        assert "created_at" in data
    
        def test_process_invalid_model(self, client: TestClient, mock_services, mock_auth):
        """Test process endpoint with invalid model."""
        request_data = {
        "prompt": "This is a test prompt for processing.",
        "model": "nonexistent-model",
        "task": "general_analysis"
        }
        
        response = client.post("/api/v1/ml/process", json=request_data)
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
        def test_process_empty_prompt(self, client: TestClient, mock_services, mock_auth):
        """Test process endpoint with empty prompt."""
        request_data = {
        "prompt": "",
        "model": "mentallama-33b",
        "task": "general_analysis"
        }
        
        response = client.post("/api/v1/ml/process", json=request_data)
        
        assert response.status_code == 400
        assert "detail" in response.json()
    
        def test_analyze_text_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the analyze_text endpoint."""
        request_data = {
        "text": "I've been feeling down lately and having trouble sleeping.",
        "analysis_type": "comprehensive",
        "max_tokens": 100,
        "temperature": 0.7
        }
        
        response = client.post("/api/v1/ml/analyze-text", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "response_id" in data
        assert data["model"] == "mentallama-33b"
        assert data["provider"] == "aws-bedrock"
        assert "text" in data
        assert "structured_data" in data
        assert "sentiment" in data["structured_data"]
        assert "entities" in data["structured_data"]
        assert "keywords" in data["structured_data"]
        assert "categories" in data["structured_data"]
        assert data["confidence"] == "high"
        assert "processing_time" in data
        assert data["tokens_used"] == 75
        assert "created_at" in data
    
        def test_detect_conditions_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the detect_conditions endpoint."""
        request_data = {
        "text": "I've been feeling down lately and having trouble sleeping.",
        "max_tokens": 100,
        "temperature": 0.7
        }
        
        response = client.post("/api/v1/ml/detect-conditions", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "response_id" in data
        assert data["model"] == "mentallama-33b-lora"
        assert data["provider"] == "aws-bedrock"
        assert "text" in data
        assert "structured_data" in data
        assert "conditions" in data["structured_data"]
        assert len(data["structured_data"]["conditions"]) > 0
        assert "condition" in data["structured_data"]["conditions"][0]
        assert "confidence" in data["structured_data"]["conditions"][0]
        assert "evidence" in data["structured_data"]["conditions"][0]
        assert data["confidence"] == "high"
        assert "processing_time" in data
        assert data["tokens_used"] == 90
        assert "created_at" in data
    
        def test_therapeutic_response_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the therapeutic_response endpoint."""
        request_data = {
        "text": "I've been feeling down lately and having trouble sleeping.",
        "context": {"previous_sessions": 2},
        "max_tokens": 100,
        "temperature": 0.7
        }
        
        response = client.post("/api/v1/ml/therapeutic-response", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "response_id" in data
        assert data["model"] == "mentallama-33b-lora"
        assert data["provider"] == "aws-bedrock"
        assert "text" in data
        assert "structured_data" in data
        assert "therapeutic_approach" in data["structured_data"]
        assert "techniques" in data["structured_data"]
        assert "follow_up_questions" in data["structured_data"]
        assert data["confidence"] == "high"
        assert "processing_time" in data
        assert data["tokens_used"] == 100
        assert "created_at" in data
    
        def test_suicide_risk_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the suicide_risk endpoint."""
        request_data = {
        "text": "I've been feeling down lately and having trouble sleeping.",
        "context": {"previous_assessments": []},
        "max_tokens": 100,
        "temperature": 0.7
        }
        
        response = client.post("/api/v1/ml/suicide-risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "response_id" in data
        assert data["model"] == "mentallama-33b-lora"
        assert data["provider"] == "aws-bedrock"
        assert "text" in data
        assert "structured_data" in data
        assert "risk_level" in data["structured_data"]
        assert "risk_factors" in data["structured_data"]
        assert "protective_factors" in data["structured_data"]
        assert "recommendations" in data["structured_data"]
        assert "immediate_action_required" in data["structured_data"]
        assert data["confidence"] == "high"
        assert "processing_time" in data
        assert data["tokens_used"] == 120
        assert "created_at" in data
    
        def test_wellness_dimensions_endpoint(self, client: TestClient, mock_services, mock_auth):
        """Test the wellness_dimensions endpoint."""
        request_data = {
        "text": "I've been feeling down lately and having trouble sleeping.",
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
    
        def test_health_check(self, client: TestClient, mock_services):
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
    
        def test_service_unavailable(self, client: TestClient, mock_auth):
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