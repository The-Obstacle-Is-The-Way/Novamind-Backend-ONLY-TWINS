# -*- coding: utf-8 -*-
"""
Unit tests for Digital Twin API endpoints.

Tests the API endpoints for Digital Twin functionality, including
the MentaLLaMA integration for clinical text processing.
"""

import json
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional # Added Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Depends, status # Added Depends, status
from fastapi.testclient import TestClient
from pydantic import parse_obj_as

# Placeholder imports for exceptions if the original ones cause issues
@pytest.mark.db_required() # Assuming db_required is a valid marker
class MentalLLaMAInferenceError(Exception): pass
class PhiDetectionError(Exception): pass
class ModelInferenceError(Exception): pass # Added placeholder
class ValidationError(Exception): pass # Added placeholder

from app.presentation.api.v1.endpoints.digital_twins import (
    router as digital_twins_router,
    get_digital_twin_service,
    # Assuming get_current_user_id is imported/defined correctly for dependency injection
    # If not, it needs to be imported or mocked appropriately
    # get_current_user_id
)
from app.presentation.api.v1.schemas.digital_twin_schemas import (
    PersonalizedInsightResponse,
    BiometricCorrelationResponse,
    MedicationResponsePredictionResponse,
    TreatmentPlanResponse,
    ClinicalTextAnalysisRequest, # Added missing import
    ClinicalTextAnalysisResponse # Added missing import
)
# Assuming DigitalTwinIntegrationService exists for mocking
from app.infrastructure.ml.digital_twin_integration_service import DigitalTwinIntegrationService


@pytest.fixture
def mock_digital_twin_service():
    """Create a mock DigitalTwinIntegrationService."""
    service = AsyncMock(spec=DigitalTwinIntegrationService)

    # Mock methods
    service.get_digital_twin_status = AsyncMock()
    service.generate_comprehensive_patient_insights = AsyncMock()
    service.update_digital_twin = AsyncMock()

    # Mock nested services
    service.mentallama_service = AsyncMock()
    service.mentallama_service.summarize_clinical_document = AsyncMock()
    service.mentallama_service.extract_clinical_entities = AsyncMock()
    service.mentallama_service.analyze_clinical_text = AsyncMock()

    service.symptom_forecasting_service = AsyncMock()
    service.symptom_forecasting_service.forecast_symptoms = AsyncMock()

    service.biometric_correlation_service = AsyncMock()
    service.biometric_correlation_service.analyze_correlations = AsyncMock()

    service.pharmacogenomics_service = AsyncMock()
    service.pharmacogenomics_service.predict_medication_responses = AsyncMock()
    service.pharmacogenomics_service.recommend_treatment_plan = AsyncMock()

    return service

@pytest.fixture
def mock_current_user_id():
    """Fixture for a mock user ID."""
    
    return UUID("00000000-0000-0000-0000-000000000001")

@pytest.fixture
def app(mock_digital_twin_service, mock_current_user_id):
    """Create a FastAPI test application."""
    app_instance = FastAPI()

    # Override dependencies
    app_instance.dependency_overrides[get_digital_twin_service] = lambda: mock_digital_twin_service
    # Assuming get_current_user_id is the correct dependency name
    try:
        # Attempt to import the actual dependency function if it exists
    from app.presentation.api.dependencies.auth import get_current_user_id as auth_get_user_id
    app_instance.dependency_overrides[auth_get_user_id] = lambda: mock_current_user_id
    except ImportError:
        # Fallback if the exact path is different or doesn't exist
    print("Warning: Auth dependency get_current_user_id not found at expected path.")
        # You might need to adjust the path based on your project structure
        # For now, we assume the endpoint directly uses a variable or another mechanism
    pass


    # Include router
    app_instance.include_router(digital_twins_router)

    return app_instance


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    
    return TestClient(app)


@pytest.fixture
def sample_patient_id():
    """Create a sample patient ID."""
    
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_status_response(sample_patient_id):
    """Create a sample digital twin status response."""
    
    return {
    "patient_id": str(sample_patient_id),
    "status": "partial",
    "completeness": 60,
    "components": {
    "symptom_forecasting": {
    "has_model": True,
    "last_updated": datetime.now(UTC).isoformat()
    },
    "biometric_correlation": {
    "has_model": True,
    "last_updated": datetime.now(UTC).isoformat()
    },
    "pharmacogenomics": {
    "service_available": True,
    "service_info": {
    "version": "1.0.0"
    }
    }
    },
    "last_checked": datetime.now(UTC).isoformat()
    }


@pytest.fixture
def sample_insights_response(sample_patient_id):
    """Create a sample patient insights response."""
    # Using the structure from PersonalizedInsightResponse schema
    return {
        "patient_id": str(sample_patient_id),
        "generated_at": datetime.now(UTC).isoformat(),
        "symptom_forecasting": {
            "trending_symptoms": [
                {
                    "symptom": "anxiety",
                    "trend": "increasing",
                    "confidence": 0.85,
                    "insight_text": "Anxiety levels have been trending upward over the past week"
                }
            ],
            "risk_alerts": [
                {
                    "symptom": "insomnia",
                    "risk_level": "moderate",
                    "alert_text": "Sleep disruption patterns indicate potential insomnia risk",
                    "importance": 0.75
                }
            ]
        },
        "biometric_correlation": {
            "strong_correlations": [
                {
                    "biometric_type": "heart_rate",
                    "mental_health_indicator": "anxiety",
                    "correlation_strength": 0.82,
                    "direction": "positive",
                    "insight_text": "Elevated heart rate strongly correlates with reported anxiety",
                    "p_value": 0.01
                }
            ]
        },
        "pharmacogenomics": {
             "medication_responses": { # Assuming this structure based on schema
                "predictions": [
                    {
                        "medication": "sertraline",
                        "predicted_response": "positive",
                        "confidence": 0.78
                    }
                ]
            }
        },
        "integrated_recommendations": [
            {
                "source": "integrated",
                "type": "biometric_symptom",
                "recommendation": "Monitor heart rate as it correlates with anxiety levels",
                "importance": 0.85
            }
        ]
    }


@pytest.fixture
def sample_forecast_response(sample_patient_id):
    """Create a sample symptom forecast response."""
    # Assuming a schema similar to SymptomForecastResponse exists
    return {
        "patient_id": str(sample_patient_id),
        "forecast_days": 30,
        "generated_at": datetime.now(UTC).isoformat(),
        "forecast_points": [
            {
                "date": (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d"),
                "symptom": "anxiety",
                "severity": 6.2,
                "confidence_low": 5.5,
                "confidence_high": 6.9
            }
        ],
         "trending_symptoms": [ # Added based on PersonalizedInsightResponse structure
            {
                "symptom": "anxiety",
                "trend": "increasing",
                "confidence": 0.85,
                "insight_text": "Anxiety levels have been trending upward over the past week"
            }
        ],
        "risk_alerts": [ # Added based on PersonalizedInsightResponse structure
            {
                "symptom": "insomnia",
                "risk_level": "moderate",
                "alert_text": "Sleep disruption patterns indicate potential insomnia risk",
                "importance": 0.75
            }
        ]
    }

@pytest.fixture
def sample_correlation_response(sample_patient_id):
    """Create a sample biometric correlation response."""
    
    return {
    "patient_id": str(sample_patient_id),
    "window_days": 30,
    "generated_at": datetime.now(UTC).isoformat(),
    "strong_correlations": [
    {
    "biometric_type": "heart_rate",
    "mental_health_indicator": "anxiety",
    "correlation_strength": 0.82,
    "direction": "positive",
    "insight_text": "Elevated heart rate strongly correlates with reported anxiety",
    "p_value": 0.01
    }
    ],
    "anomalies": [
    {
    "data_type": "sleep_quality",
    "description": "Unusual sleep pattern detected",
    "severity": 0.65,
    "detected_at": datetime.now(UTC).isoformat()
    }
    ],
    "data_quality": {
    "completeness": 0.85,
    "consistency": 0.92
    }
    }

@pytest.fixture
def sample_medication_response(sample_patient_id):
    """Create a sample medication response prediction."""
     
    return {
    "patient_id": str(sample_patient_id),
    "generated_at": datetime.now(UTC).isoformat(),
    "predictions": [
    {
    "medication": "sertraline",
    "predicted_response": "positive",
    "confidence": 0.78,
    "potential_side_effects": ["nausea", "insomnia"],
    "genetic_factors": [
    {
    "gene": "CYP2D6",
    "variant": "*4/*4",
    "impact": "reduced metabolism"
    }
    ]
    }
    ],
    "insights": [
    {
    "insight_text": "Based on genetic profile, patient may respond well to SSRIs",
    "importance": 0.85
    }
    ]
    }

@pytest.fixture
def sample_treatment_plan(sample_patient_id):
    """Create a sample treatment plan response."""
    
    return {
    "patient_id": str(sample_patient_id),
    "diagnosis": "Major Depressive Disorder",
    "generated_at": datetime.now(UTC).isoformat(),
    "recommendations": {
    "medications": [
    {
    "type": "medication",
    "recommendation_text": "Consider starting sertraline 50mg daily",
    "importance": 0.9,
    "evidence_level": "A",
    "genetic_basis": [
    {
    "gene": "CYP2D6",
    "variant": "*4/*4",
    "impact": "reduced metabolism"
    }
    ]
    }
    ],
    "therapy": [
    {
    "type": "therapy",
    "recommendation_text": "Cognitive Behavioral Therapy, 1 session per week",
    "importance": 0.85,
    "evidence_level": "A",
    "genetic_basis": None
    }
    ],
    "lifestyle": [
    {
    "type": "lifestyle",
    "recommendation_text": "Daily 30-minute moderate exercise",
    "importance": 0.7,
    "evidence_level": "B",
    "genetic_basis": None
    }
    ],
    "summary": [ # Added summary based on schema
    {
    "type": "summary",
    "recommendation_text": "Combined medication and therapy approach recommended",
    "importance": 0.95,
    "evidence_level": "A",
    "genetic_basis": None
    }
    ]
    },
    "personalization_factors": [
    {
    "factor": "genetic_profile",
    "impact": "high",
    "description": "Genetic variants suggest good response to SSRIs"
    },
    {
    "factor": "biometric_data",
    "impact": "medium",
    "description": "Sleep patterns suggest need for sleep hygiene intervention"
    }
    ]
    }


@pytest.mark.db_required() # Assuming db_required is a valid marker
class TestDigitalTwinEndpoints:
    """Tests for the Digital Twin API endpoints."""

    def test_get_digital_twin_status(self, client, mock_digital_twin_service, sample_patient_id, sample_status_response):
        """Test that get_digital_twin_status returns the correct response."""
        # Setup
        mock_digital_twin_service.get_digital_twin_status.return_value = sample_status_response

        # Execute
    response = client.get(f"/digital-twins/patients/{sample_patient_id}/status")

        # Verify
    assert response.status_code == 200
    assert response.json() == sample_status_response
    mock_digital_twin_service.get_digital_twin_status.assert_called_once_with(sample_patient_id)

    def test_get_patient_insights(self, client, mock_digital_twin_service, sample_patient_id, sample_insights_response):
        """Test that get_patient_insights returns the correct response."""
        # Setup
        mock_digital_twin_service.generate_comprehensive_patient_insights.return_value = sample_insights_response

        # Execute
    response = client.get(f"/digital-twins/patients/{sample_patient_id}/insights")

        # Verify
    assert response.status_code == 200
    assert response.json() == sample_insights_response
        # Check if the mock was called (adjust arguments if needed based on actual implementation)
    mock_digital_twin_service.generate_comprehensive_patient_insights.assert_called_once()


    def test_update_digital_twin(self, client, mock_digital_twin_service, sample_patient_id, sample_status_response):
        """Test that update_digital_twin returns the correct response."""
        # Setup
        mock_digital_twin_service.update_digital_twin.return_value = {"status": "success"} # Assume simple success message
        mock_digital_twin_service.get_digital_twin_status.return_value = sample_status_response # Status after update

    update_data = {
    "symptom_history": [
    {
    "symptom": "anxiety",
    "severity": 7,
    "timestamp": datetime.now(UTC).isoformat()
    }
    ]
    }

        # Execute
    response = client.post(
    f"/digital-twins/patients/{sample_patient_id}/update",
    json=update_data
    )

        # Verify
    assert response.status_code == 200
        # The endpoint returns the status after update
    assert response.json() == sample_status_response
    mock_digital_twin_service.update_digital_twin.assert_called_once()
    mock_digital_twin_service.get_digital_twin_status.assert_called_once_with(sample_patient_id)

    def test_get_symptom_forecast(self, client, mock_digital_twin_service, sample_patient_id, sample_forecast_response):
        """Test that get_symptom_forecast returns the correct response."""
        # Setup
        mock_digital_twin_service.symptom_forecasting_service.forecast_symptoms.return_value = sample_forecast_response

        # Execute
    response = client.get(f"/digital-twins/patients/{sample_patient_id}/symptom-forecast")

        # Verify
    assert response.status_code == 200
    assert response.json() == sample_forecast_response
    mock_digital_twin_service.symptom_forecasting_service.forecast_symptoms.assert_called_once()

    def test_get_biometric_correlations(self, client, mock_digital_twin_service, sample_patient_id, sample_correlation_response):
        """Test that get_biometric_correlations returns the correct response."""
        # Setup
        mock_digital_twin_service.biometric_correlation_service.analyze_correlations.return_value = sample_correlation_response

        # Execute
    response = client.get(f"/digital-twins/patients/{sample_patient_id}/biometric-correlations")

        # Verify
    assert response.status_code == 200
    assert response.json() == sample_correlation_response
    mock_digital_twin_service.biometric_correlation_service.analyze_correlations.assert_called_once()

    def test_predict_medication_response(self, client, mock_digital_twin_service, sample_patient_id, sample_medication_response):
        """Test that predict_medication_response returns the correct response."""
        # Setup
        mock_digital_twin_service.pharmacogenomics_service.predict_medication_responses.return_value = sample_medication_response

    request_data = {
    "medications": ["sertraline", "fluoxetine", "escitalopram"]
    }

        # Execute
    response = client.post(
    f"/digital-twins/patients/{sample_patient_id}/medication-response",
    json=request_data
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == sample_medication_response
    mock_digital_twin_service.pharmacogenomics_service.predict_medication_responses.assert_called_once()

    def test_generate_treatment_plan(self, client, mock_digital_twin_service, sample_patient_id, sample_treatment_plan):
        """Test that generate_treatment_plan returns the correct response."""
        # Setup
        mock_digital_twin_service.pharmacogenomics_service.recommend_treatment_plan.return_value = sample_treatment_plan

    request_data = {
    "diagnosis": "Major Depressive Disorder",
    "treatment_goals": ["Reduce depressive symptoms", "Improve sleep quality"],
    "treatment_constraints": ["History of adverse reaction to fluoxetine"]
    }

        # Execute
    response = client.post(
    f"/digital-twins/patients/{sample_patient_id}/treatment-plan",
    json=request_data
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == sample_treatment_plan
    mock_digital_twin_service.pharmacogenomics_service.recommend_treatment_plan.assert_called_once()

    def test_error_handling(self, client, mock_digital_twin_service, sample_patient_id):
        """Test that errors are properly handled and don't leak PHI."""
        # Setup
        error_message = "Error processing patient data"
        mock_digital_twin_service.get_digital_twin_status.side_effect = ModelInferenceError(error_message)

        # Execute
    response = client.get(f"/digital-twins/patients/{sample_patient_id}/status")

        # Verify
    assert response.status_code == 400 # Assuming ModelInferenceError maps to 400
    assert response.json()["detail"] == error_message

        # Ensure no PHI is leaked in the error
    assert str(sample_patient_id) not in response.text # Check raw text

    def test_hipaa_compliance_in_responses(self, client, mock_digital_twin_service, sample_patient_id, sample_insights_response):
        """Test that responses maintain HIPAA compliance by not including unnecessary PHI."""
        # Setup
        mock_digital_twin_service.generate_comprehensive_patient_insights.return_value = sample_insights_response

        # Execute
    response = client.get(f"/digital-twins/patients/{sample_patient_id}/insights")

        # Verify
    assert response.status_code == 200
    response_data = response.json()

        # Check that only necessary PHI is included
    assert "patient_id" in response_data  # This is necessary for identification

        # Check that detailed PHI is not included (assuming these are not part of the schema)
    assert "medical_record_number" not in response_data
    assert "social_security_number" not in response_data
    assert "date_of_birth" not in response_data
    assert "address" not in response_data

        # Check that biometric data is properly anonymized (if included)
        # This depends heavily on the actual structure of sample_insights_response
        # and whether it includes detailed biometric points.
        # If it does, add assertions here to check for absence of direct identifiers.
        # Example:
        # if "biometric_data" in response_data:
        #     for data_point in response_data["biometric_data"]:
        #         assert "patient_name" not in data_point
        #         assert "patient_identifier" not in data_point