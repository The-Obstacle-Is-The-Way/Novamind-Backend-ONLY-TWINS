"""
Unit tests for XGBoost API routes.

This module contains tests for the XGBoost API endpoints, validating:
- Request validation
- Authentication and authorization
- Response structure
- Error handling
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.xgboost import router
from app.core.services.ml.xgboost import (
    PredictionType,
    TreatmentCategory,
    RiskLevel,
    ResponseLevel,
    ValidationStatus,
    ModelNotFoundError,
    PredictionNotFoundError,
    PatientNotFoundError,
    InvalidFeatureError,
    PredictionError
)


# Test fixtures
@pytest.fixture
def app():
    """Create test FastAPI app with XGBoost router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_xgboost_service():
    """Create mock XGBoost service."""
    mock_service = MagicMock()
    
    # Set up common mock behavior
    mock_service.healthcheck.return_value = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "model_service": {"status": "healthy"},
            "database": {"status": "healthy"},
            "storage": {"status": "healthy"}
        },
        "models": {
            "risk_relapse": "active",
            "treatment_response_medication": "active"
        }
    }
    
    return mock_service


@pytest.fixture
def mock_auth():
    """Mock authentication dependencies."""
    def get_current_clinician():
        return {"id": "clinician-123", "role": "psychiatrist"}
    
    async def verify_patient_access(clinician_id, patient_id):
        if patient_id == "unauthorized-patient":
            raise PermissionError("Unauthorized access to patient")
        return True
    
    return {
        "get_current_clinician": get_current_clinician,
        "verify_patient_access": verify_patient_access
    }


# Sample data
@pytest.fixture
def sample_risk_prediction_request():
    """Sample risk prediction request data."""
    return {
        "patient_id": "patient-123",
        "risk_type": "risk_relapse",
        "features": {
            "age": 42,
            "gender": "female",
            "diagnosis": "major_depressive_disorder",
            "phq9_score": 18,
            "previous_hospitalizations": 1,
            "medication_adherence": 0.85
        },
        "time_frame_days": 90
    }


@pytest.fixture
def sample_treatment_prediction_request():
    """Sample treatment prediction request data."""
    return {
        "patient_id": "patient-123",
        "treatment_category": "medication_ssri",
        "treatment_details": {
            "medication": "escitalopram",
            "dosage": 10,
            "unit": "mg",
            "frequency": "daily"
        },
        "features": {
            "age": 42,
            "gender": "female",
            "diagnosis": "major_depressive_disorder",
            "previous_treatments": [
                {"medication": "fluoxetine", "response": "partial"}
            ],
            "genotype": {"cyp2d6": "normal_metabolizer"}
        }
    }


@pytest.fixture
def sample_risk_prediction():
    """Sample risk prediction result."""
    return {
        "prediction_id": str(uuid4()),
        "patient_id": "patient-123",
        "model_id": "model-456",
        "prediction_type": "risk_relapse",
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.85,
        "features_used": ["age", "phq9_score", "previous_hospitalizations"],
        "explanation": "High risk due to recent history and elevated symptoms",
        "validation_status": "pending",
        "risk_level": "high",
        "risk_score": 0.78,
        "time_frame_days": 90,
        "contributing_factors": [
            {"name": "phq9_score", "impact": 0.6, "description": "Elevated depression score"}
        ]
    }


@pytest.fixture
def sample_treatment_prediction():
    """Sample treatment prediction result."""
    return {
        "prediction_id": str(uuid4()),
        "patient_id": "patient-123",
        "model_id": "model-789",
        "prediction_type": "treatment_response_medication",
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.92,
        "features_used": ["age", "previous_treatments", "genotype"],
        "explanation": "Likely to respond well based on history and genetic profile",
        "validation_status": "pending",
        "treatment_category": "medication_ssri",
        "treatment_details": {"medication": "escitalopram", "dosage": 10},
        "response_level": "good",
        "response_score": 0.82,
        "time_to_response_days": 21,
        "suggested_adjustments": []
    }


# Tests
@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_healthcheck(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service
):
    """Test healthcheck endpoint."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    
    # Execute
    response = client.get("/api/v1/xgboost/healthcheck")
    
    # Verify
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    mock_xgboost_service.healthcheck.assert_called_once()


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_predict_risk(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth,
    sample_risk_prediction_request,
    sample_risk_prediction
):
    """Test risk prediction endpoint."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    mock_verify_access.return_value = True
    
    # Configure mock service
    mock_service = mock_xgboost_service
    mock_risk_prediction = MagicMock()
    mock_risk_prediction.to_dict.return_value = sample_risk_prediction
    mock_service.predict_risk.return_value = mock_risk_prediction
    
    # Execute
    response = client.post(
        "/api/v1/xgboost/predict/risk",
        json=sample_risk_prediction_request
    )
    
    # Verify
    assert response.status_code == 201
    
    # Verify service was called with correct parameters
    mock_service.predict_risk.assert_called_once_with(
        patient_id=sample_risk_prediction_request["patient_id"],
        risk_type=PredictionType(sample_risk_prediction_request["risk_type"]),
        features=sample_risk_prediction_request["features"],
        time_frame_days=sample_risk_prediction_request["time_frame_days"]
    )
    
    # Verify response content
    result = response.json()
    assert result["prediction_id"] == sample_risk_prediction["prediction_id"]
    assert result["risk_level"] == sample_risk_prediction["risk_level"]
    assert result["confidence"] == sample_risk_prediction["confidence"]


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_predict_treatment_response(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth,
    sample_treatment_prediction_request,
    sample_treatment_prediction
):
    """Test treatment prediction endpoint."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    mock_verify_access.return_value = True
    
    # Configure mock service
    mock_service = mock_xgboost_service
    mock_treatment_prediction = MagicMock()
    mock_treatment_prediction.to_dict.return_value = sample_treatment_prediction
    mock_service.predict_treatment_response.return_value = mock_treatment_prediction
    
    # Execute
    response = client.post(
        "/api/v1/xgboost/predict/treatment",
        json=sample_treatment_prediction_request
    )
    
    # Verify
    assert response.status_code == 201
    
    # Verify service was called with correct parameters
    mock_service.predict_treatment_response.assert_called_once_with(
        patient_id=sample_treatment_prediction_request["patient_id"],
        treatment_category=TreatmentCategory(sample_treatment_prediction_request["treatment_category"]),
        treatment_details=sample_treatment_prediction_request["treatment_details"],
        features=sample_treatment_prediction_request["features"]
    )
    
    # Verify response content
    result = response.json()
    assert result["prediction_id"] == sample_treatment_prediction["prediction_id"]
    assert result["response_level"] == sample_treatment_prediction["response_level"]
    assert result["confidence"] == sample_treatment_prediction["confidence"]


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_get_prediction(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth,
    sample_risk_prediction
):
    """Test get prediction endpoint."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    mock_verify_access.return_value = True
    
    # Configure mock service
    prediction_id = sample_risk_prediction["prediction_id"]
    mock_prediction = MagicMock()
    mock_prediction.to_dict.return_value = sample_risk_prediction
    mock_prediction.patient_id = sample_risk_prediction["patient_id"]
    mock_xgboost_service.get_prediction.return_value = mock_prediction
    
    # Execute
    response = client.get(f"/api/v1/xgboost/predictions/{prediction_id}")
    
    # Verify
    assert response.status_code == 200
    mock_xgboost_service.get_prediction.assert_called_once_with(prediction_id)
    
    # Verify response content
    result = response.json()
    assert result["prediction_id"] == prediction_id
    assert result["patient_id"] == sample_risk_prediction["patient_id"]


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_get_prediction_not_found(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth
):
    """Test get prediction with non-existent ID."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    
    # Configure mock service to raise exception
    mock_xgboost_service.get_prediction.side_effect = PredictionNotFoundError("Prediction not found")
    
    # Execute
    response = client.get("/api/v1/xgboost/predictions/non-existent-id")
    
    # Verify
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_validate_prediction(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth,
    sample_risk_prediction
):
    """Test prediction validation endpoint."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    mock_verify_access.return_value = True
    
    # Configure mock service
    prediction_id = sample_risk_prediction["prediction_id"]
    mock_prediction = MagicMock()
    mock_prediction.patient_id = sample_risk_prediction["patient_id"]
    mock_xgboost_service.get_prediction.return_value = mock_prediction
    mock_xgboost_service.validate_prediction.return_value = True
    
    # Request data
    validation_request = {
        "status": "validated",
        "validator_notes": "Clinically confirmed"
    }
    
    # Execute
    response = client.post(
        f"/api/v1/xgboost/predictions/{prediction_id}/validate",
        json=validation_request
    )
    
    # Verify
    assert response.status_code == 200
    
    # Verify service was called with correct parameters
    mock_xgboost_service.validate_prediction.assert_called_once_with(
        prediction_id=prediction_id,
        status=ValidationStatus.VALIDATED,
        validator_notes=validation_request["validator_notes"]
    )


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_unauthorized_patient_access(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth
):
    """Test unauthorized patient access."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    
    # Configure mock to raise permission error
    error_msg = "Unauthorized access to patient"
    mock_verify_access.side_effect = PermissionError(error_msg)
    
    # Unauthorized request
    request_data = {
        "patient_id": "unauthorized-patient",
        "risk_type": "risk_relapse",
        "features": {"age": 42},
        "time_frame_days": 90
    }
    
    # Execute
    response = client.post(
        "/api/v1/xgboost/predict/risk",
        json=request_data
    )
    
    # Verify
    assert response.status_code == 403
    assert "unauthorized" in response.json()["detail"].lower()


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_invalid_feature_error(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth,
    sample_risk_prediction_request
):
    """Test invalid feature error handling."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    mock_verify_access.return_value = True
    
    # Configure mock to raise invalid feature error
    error_msg = "Required feature 'phq9_score' is missing"
    mock_xgboost_service.predict_risk.side_effect = InvalidFeatureError(error_msg)
    
    # Execute
    response = client.post(
        "/api/v1/xgboost/predict/risk",
        json=sample_risk_prediction_request
    )
    
    # Verify
    assert response.status_code == 400
    assert "invalid features" in response.json()["detail"].lower()
    assert "phq9_score" in response.json()["detail"].lower()


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_model_get_feature_importance(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth
):
    """Test model feature importance endpoint."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    
    # Configure mock service
    model_id = "model-123"
    feature_importance = [
        MagicMock(to_dict=lambda: {
            "feature_id": "feature-1",
            "feature_name": "PHQ-9 Score",
            "importance": 0.85,
            "category": "clinical"
        }),
        MagicMock(to_dict=lambda: {
            "feature_id": "feature-2",
            "feature_name": "Previous Hospitalizations",
            "importance": 0.65,
            "category": "clinical"
        })
    ]
    mock_xgboost_service.get_feature_importance.return_value = feature_importance
    
    # Execute
    response = client.get(f"/api/v1/xgboost/models/{model_id}/feature_importance")
    
    # Verify
    assert response.status_code == 200
    mock_xgboost_service.get_feature_importance.assert_called_once_with(model_id=model_id)
    
    # Verify response content
    result = response.json()
    assert len(result) == 2
    assert result[0]["feature_name"] == "PHQ-9 Score"
    assert result[1]["feature_name"] == "Previous Hospitalizations"


@patch("app.api.routes.xgboost.get_xgboost_service")
@patch("app.api.routes.xgboost.get_current_clinician")
@patch("app.api.routes.xgboost.verify_patient_access")
def test_compare_treatments(
    mock_verify_access,
    mock_get_clinician,
    mock_get_service,
    client,
    mock_xgboost_service,
    mock_auth
):
    """Test treatment comparison endpoint."""
    # Setup
    mock_get_service.return_value = mock_xgboost_service
    mock_get_clinician.return_value = mock_auth["get_current_clinician"]()
    mock_verify_access.return_value = True
    
    # Sample request data
    request_data = {
        "patient_id": "patient-123",
        "treatment_options": [
            {
                "category": "medication_ssri",
                "details": {"medication": "escitalopram", "dosage": 10}
            },
            {
                "category": "therapy_cbt",
                "details": {"frequency": "weekly", "duration_weeks": 12}
            }
        ],
        "features": {
            "age": 42,
            "diagnosis": "major_depressive_disorder"
        }
    }
    
    # Configure mock service
    comparison_result = {
        "patient_id": "patient-123",
        "timestamp": datetime.now().isoformat(),
        "treatments_compared": 2,
        "results": [
            {
                "treatment_category": "medication_ssri",
                "treatment_details": {"medication": "escitalopram"},
                "response_level": "good",
                "response_score": 0.82,
                "time_to_response_days": 21,
                "confidence": 0.92,
                "suggested_adjustments": [],
                "prediction_id": str(uuid4()),
                "relative_efficacy": 100.0
            },
            {
                "treatment_category": "therapy_cbt",
                "treatment_details": {"frequency": "weekly"},
                "response_level": "moderate",
                "response_score": 0.65,
                "time_to_response_days": 42,
                "confidence": 0.85,
                "suggested_adjustments": [],
                "prediction_id": str(uuid4()),
                "relative_efficacy": 79.3
            }
        ],
        "recommendation": {
            "recommended_treatment": "medication_ssri",
            "reasoning": "Higher predicted response and faster time to response",
            "confidence": 0.9
        }
    }
    mock_xgboost_service.compare_treatments.return_value = comparison_result
    
    # Execute
    response = client.post(
        "/api/v1/xgboost/compare/treatments",
        json=request_data
    )
    
    # Verify
    assert response.status_code == 200
    
    # Verify service was called with correct parameters
    mock_xgboost_service.compare_treatments.assert_called_once()
    call_args = mock_xgboost_service.compare_treatments.call_args[1]
    assert call_args["patient_id"] == request_data["patient_id"]
    assert len(call_args["treatment_options"]) == 2
    
    # Verify response content
    result = response.json()
    assert result["patient_id"] == comparison_result["patient_id"]
    assert result["treatments_compared"] == 2
    assert result["recommendation"]["recommended_treatment"] == "medication_ssri"