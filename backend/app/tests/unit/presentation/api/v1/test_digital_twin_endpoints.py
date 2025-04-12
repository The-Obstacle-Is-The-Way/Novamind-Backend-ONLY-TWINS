# -*- coding: utf-8 -*-
"""
Unit tests for Digital Twin API endpoints.

Tests the API endpoints for Digital Twin functionality, including
the MentaLLaMA integration for clinical text processing.
"""

import json
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional # Added Optional

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Placeholder imports for exceptions if the original ones cause issues
# from app.core.exceptions.ml_exceptions import MentalLLaMAInferenceError, PhiDetectionError
@pytest.mark.db_required() # Assuming db_required is a valid marker
class MentalLLaMAInferenceError(Exception): pass
class PhiDetectionError(Exception): pass

from app.presentation.api.v1.endpoints.digital_twins import (
    get_digital_twin_service,
    router as digital_twins_router,
)
from app.presentation.api.v1.schemas.digital_twin_schemas import (
    ClinicalTextAnalysisResponse,
    ClinicalTextAnalysisRequest
)
# Assuming DigitalTwinService exists for mocking
from app.application.services.digital_twin_service import DigitalTwinService


@pytest.fixture
def app():
    """Create a FastAPI test application."""
    app_instance = FastAPI()
    app_instance.include_router(digital_twins_router)
    return app_instance


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    
    return TestClient(app)


@pytest.fixture
def mock_jwt_auth():
    """Mock the JWT authentication."""
    # Assuming get_current_user_id exists in the endpoint's dependencies
    try:
        from app.presentation.api.dependencies.auth import get_current_user_id
        with patch(
            "app.presentation.api.dependencies.auth.get_current_user_id",
            return_value=UUID("00000000-0000-0000-0000-000000000001")
        ) as mock_auth:
            yield mock_auth
    except ImportError:
        print("Warning: get_current_user_id dependency not found for mocking.")
        yield None # Yield None if dependency not found


@pytest.fixture
def mock_digital_twin_service():
    """Mock the digital twin service."""
    service_mock = MagicMock(spec=DigitalTwinService)

    # Setup mentallama_service mock as an attribute
    mentallama_mock = AsyncMock()
    mentallama_mock.summarize_clinical_document = AsyncMock()
    mentallama_mock.extract_clinical_entities = AsyncMock()
    mentallama_mock.analyze_clinical_text = AsyncMock()
    service_mock.mentallama_service = mentallama_mock # Attach the mock

    # Return the mock service
    return service_mock


@pytest.fixture(autouse=True) # Apply overrides automatically
def override_dependencies_auto(app, mock_digital_twin_service, mock_jwt_auth):
     """Override dependencies for the FastAPI app."""
     app.dependency_overrides[get_digital_twin_service] = lambda: mock_digital_twin_service
     # The mock_jwt_auth fixture already patches the dependency

     yield

     app.dependency_overrides = {}


class TestMentalLLaMAEndpoints:
    """Tests for MentaLLaMA-specific API endpoints."""

    def test_summarize_clinical_text_success(self, client, mock_digital_twin_service):
        """Test successful clinical text summarization."""
        # Setup the mock response
        mock_response_data = {
            "summary": "Patient shows signs of mild depression with sleep disturbance.",
            "summary_type": "comprehensive",
            "phi_detected": False,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_digital_twin_service.mentallama_service.summarize_clinical_document.return_value = mock_response_data

        # Prepare request data
        request_data = {
            "text": "Patient reports feeling sad for the past two weeks with difficulty sleeping.",
            "summary_type": "comprehensive",
            "target_length": 100,
        }

        # Make the request
        response = client.post("/clinical-text/summarize", json=request_data)

        # Check response
        assert response.status_code == 200
        response_json = response.json()
        assert "result" in response_json
        assert "summary" in response_json["result"]
        assert response_json["phi_detected"] is False

        # Verify mock was called correctly
        mock_digital_twin_service.mentallama_service.summarize_clinical_document.assert_called_once_with(
            text=request_data["text"],
            summary_type=request_data["summary_type"],
            target_length=request_data["target_length"],
        )

    def test_summarize_clinical_text_phi_detected(self, client, mock_digital_twin_service):
        """Test clinical text summarization when PHI is detected."""
        # Setup the mock response
        mock_response_data = {
            "summary": "Patient shows signs of mild depression with sleep disturbance.",
            "summary_type": "comprehensive",
            "phi_detected": True,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_digital_twin_service.mentallama_service.summarize_clinical_document.return_value = mock_response_data

        # Prepare request data
        request_data = {
            "text": "Patient John Doe reports feeling sad for the past two weeks with difficulty sleeping.",
            "summary_type": "comprehensive",
            "target_length": 100,
        }

        # Make the request
        response = client.post("/clinical-text/summarize", json=request_data)

        # Check response
        assert response.status_code == 200
        response_json = response.json()
        assert "result" in response_json
        assert "summary" in response_json["result"]
        assert response_json["phi_detected"] is True

    def test_summarize_clinical_text_phi_error(self, client, mock_digital_twin_service):
        """Test clinical text summarization when PHI detection fails."""
        # Setup the mock to raise an error
        mock_digital_twin_service.mentallama_service.summarize_clinical_document.side_effect = PhiDetectionError(
            "PHI detection service unavailable"
        )

        # Prepare request data
        request_data = {
            "text": "Patient reports feeling sad for the past two weeks with difficulty sleeping.",
            "summary_type": "comprehensive",
            "target_length": 100,
        }

        # Make the request
        response = client.post("/clinical-text/summarize", json=request_data)

        # Check response
        assert response.status_code == 400
        assert "PHI detection error" in response.json()["detail"]

    def test_summarize_clinical_text_inference_error(self, client, mock_digital_twin_service):
        """Test clinical text summarization when model inference fails."""
        # Setup the mock to raise an error
        mock_digital_twin_service.mentallama_service.summarize_clinical_document.side_effect = MentalLLaMAInferenceError(
            "Model inference failed"
        )

        # Prepare request data
        request_data = {
            "text": "Patient reports feeling sad for the past two weeks with difficulty sleeping.",
            "summary_type": "comprehensive",
            "target_length": 100,
        }

        # Make the request
        response = client.post("/clinical-text/summarize", json=request_data)

        # Check response
        assert response.status_code == 400
        assert "Model inference failed" in response.json()["detail"]

    def test_extract_clinical_entities_success(self, client, mock_digital_twin_service):
        """Test successful clinical entity extraction."""
        # Setup the mock response
        mock_response_data = {
            "entities": {
                "symptoms": ["sadness", "sleep disturbance"],
                "diagnoses": ["depression"],
            },
            "entity_types": ["symptoms", "diagnoses"],
            "phi_detected": False,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_digital_twin_service.mentallama_service.extract_clinical_entities.return_value = mock_response_data

        # Prepare request data
        request_data = {
            "text": "Patient reports feeling sad for the past two weeks with difficulty sleeping.",
            "entity_types": ["symptoms", "diagnoses"],
        }

        # Make the request
        response = client.post("/clinical-text/extract-entities", json=request_data)

        # Check response
        assert response.status_code == 200
        response_json = response.json()
        assert "result" in response_json
        assert "entities" in response_json["result"]
        assert "symptoms" in response_json["result"]["entities"]
        assert response_json["phi_detected"] is False

        # Verify mock was called correctly
        mock_digital_twin_service.mentallama_service.extract_clinical_entities.assert_called_once_with(
            text=request_data["text"],
            entity_types=request_data["entity_types"],
        )

    def test_extract_clinical_entities_phi_detected(self, client, mock_digital_twin_service):
        """Test clinical entity extraction when PHI is detected."""
        # Setup the mock response
        mock_response_data = {
            "entities": {
                "symptoms": ["sadness", "sleep disturbance"],
                "diagnoses": ["depression"],
            },
            "entity_types": ["symptoms", "diagnoses"],
            "phi_detected": True,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_digital_twin_service.mentallama_service.extract_clinical_entities.return_value = mock_response_data

        # Prepare request data
        request_data = {
            "text": "Patient John Doe reports feeling sad for the past two weeks with difficulty sleeping.",
            "entity_types": ["symptoms", "diagnoses"],
        }

        # Make the request
        response = client.post("/clinical-text/extract-entities", json=request_data)

        # Check response
        assert response.status_code == 200
        response_json = response.json()
        assert "result" in response_json
        assert "entities" in response_json["result"]
        assert response_json["phi_detected"] is True

    def test_extract_clinical_entities_error(self, client, mock_digital_twin_service):
        """Test clinical entity extraction when it fails."""
        # Setup the mock to raise an error
        mock_digital_twin_service.mentallama_service.extract_clinical_entities.side_effect = MentalLLaMAInferenceError(
            "Entity extraction failed"
        )

        # Prepare request data
        request_data = {
            "text": "Patient reports feeling sad for the past two weeks with difficulty sleeping.",
            "entity_types": ["symptoms", "diagnoses"],
        }

        # Make the request
        response = client.post("/clinical-text/extract-entities", json=request_data)

        # Check response
        assert response.status_code == 400
        assert "Entity extraction failed" in response.json()["detail"]