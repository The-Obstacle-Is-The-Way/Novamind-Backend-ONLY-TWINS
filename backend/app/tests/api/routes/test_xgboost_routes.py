"""
Unit tests for XGBoost service API endpoints.

These tests verify the functionality of the XGBoost service API endpoints,
including input validation, error handling, and response formatting.
All tests use the MockXGBoostService to avoid external dependencies.
"""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.api.routes.xgboost import router
from app.core.services.ml.xgboost import (
    MockXGBoostService,
    PredictionType,
    TreatmentCategory,
    ValidationStatus,
    RiskLevel,
    ResponseLevel,
    ModelNotFoundError,
    PredictionNotFoundError,
    PatientNotFoundError,
    InvalidFeatureError,
    PredictionError
)


# Create a FastAPI test app with the XGBoost router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# Mock authentication
@pytest.fixture
def mock_auth():
    """Fixture to mock authentication for API endpoints."""
    with patch("app.api.dependencies.auth.get_current_clinician") as mock_auth:
        mock_auth.return_value = {"id": "clinician-123", "name": "Dr. Smith"}
        yield mock_auth


@pytest.fixture
def mock_patient_access():
    """Fixture to mock patient access verification."""
    with patch("app.api.dependencies.auth.verify_patient_access") as mock_access:
        mock_access.return_value = None
        yield mock_access


@pytest.fixture
def mock_xgboost_service():
    """Fixture to provide a mock XGBoost service for tests."""
    service = MockXGBoostService()
    
    with patch("app.api.routes.xgboost.get_xgboost_service") as mock_get_service:
        mock_get_service.return_value = service
        yield service


@pytest.mark.db_required
class TestHealthcheck:
    """Tests for the healthcheck endpoint."""

    @pytest.mark.db_required
def test_healthcheck_success(self, mock_xgboost_service):
        """Test successful healthcheck."""
        mock_xgboost_service.healthcheck.return_value = {
            "status": "healthy",
            "timestamp": "2025-03-29T12:00:00Z",
            "components": {"database": {"status": "healthy"}},
            "models": {"risk_relapse": "active"}
        }
        
        response = client.get("/api/v1/xgboost/healthcheck")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "components" in response.json()
        assert "models" in response.json()
        assert mock_xgboost_service.healthcheck.called

    @pytest.mark.db_required
def test_healthcheck_failure(self, mock_xgboost_service):
        """Test healthcheck with service error."""
        mock_xgboost_service.healthcheck.side_effect = Exception("Service unavailable")
        
        response = client.get("/api/v1/xgboost/healthcheck")
        
        assert response.status_code == 500
        assert "Service health check failed" in response.json()["detail"]


@pytest.mark.db_required
class TestRiskPrediction:
    """Tests for the risk prediction endpoint."""

    @pytest.mark.db_required
def test_predict_risk_success(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test successful risk prediction generation."""
        # Setup mock return value
        mock_xgboost_service.predict_risk.return_value.to_dict.return_value = {
            "prediction_id": "pred-123",
            "patient_id": "patient-456",
            "model_id": "model-789",
            "prediction_type": "risk_relapse",
            "timestamp": "2025-03-29T12:00:00Z",
            "confidence": 0.85,
            "risk_level": "high",
            "risk_score": 0.75,
            "time_frame_days": 90,
            "features_used": ["age", "phq9_score"],
            "explanation": "High risk based on recent symptoms",
            "validation_status": "pending",
            "contributing_factors": [{"name": "phq9_score", "impact": 0.8}]
        }
        
        # Test data
        test_data = {
            "patient_id": "patient-456",
            "risk_type": "risk_relapse",
            "features": {
                "age": 35,
                "phq9_score": 18
            },
            "time_frame_days": 90
        }
        
        response = client.post(
            "/api/v1/xgboost/predict/risk",
            json=test_data
        )
        
        assert response.status_code == 201
        assert response.json()["prediction_id"] == "pred-123"
        assert response.json()["risk_level"] == "high"
        assert response.json()["patient_id"] == "patient-456"
        
        # Verify the service was called with correct parameters
        mock_xgboost_service.predict_risk.assert_called_once()
        args, kwargs = mock_xgboost_service.predict_risk.call_args
        assert kwargs["patient_id"] == "patient-456"
        assert kwargs["risk_type"].value == "risk_relapse"
        assert "phq9_score" in kwargs["features"]

    @pytest.mark.db_required
def test_predict_risk_invalid_features(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test risk prediction with invalid features."""
        mock_xgboost_service.predict_risk.side_effect = InvalidFeatureError("Missing required feature: phq9_score")
        
        test_data = {
            "patient_id": "patient-456",
            "risk_type": "risk_relapse",
            "features": {
                "age": 35
                # Missing phq9_score
            }
        }
        
        response = client.post(
            "/api/v1/xgboost/predict/risk",
            json=test_data
        )
        
        assert response.status_code == 400
        assert "Invalid features" in response.json()["detail"]

    @pytest.mark.db_required
def test_predict_risk_model_not_found(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test risk prediction with non-existent model."""
        mock_xgboost_service.predict_risk.side_effect = ModelNotFoundError("No model available for risk_relapse")
        
        test_data = {
            "patient_id": "patient-456",
            "risk_type": "risk_relapse",
            "features": {
                "age": 35,
                "phq9_score": 18
            }
        }
        
        response = client.post(
            "/api/v1/xgboost/predict/risk",
            json=test_data
        )
        
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]

    @pytest.mark.db_required
def test_predict_risk_prediction_error(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test risk prediction with service error."""
        mock_xgboost_service.predict_risk.side_effect = PredictionError("Failed to generate prediction")
        
        test_data = {
            "patient_id": "patient-456",
            "risk_type": "risk_relapse",
            "features": {
                "age": 35,
                "phq9_score": 18
            }
        }
        
        response = client.post(
            "/api/v1/xgboost/predict/risk",
            json=test_data
        )
        
        assert response.status_code == 500
        assert "Prediction failed" in response.json()["detail"]

    @pytest.mark.db_required
def test_predict_risk_validation_error(self, mock_auth, mock_patient_access):
        """Test risk prediction with invalid input data."""
        test_data = {
            "patient_id": "patient-456",
            "risk_type": "invalid_type",  # Invalid risk type
            "features": {
                "age": 35,
                "phq9_score": 18
            }
        }
        
        response = client.post(
            "/api/v1/xgboost/predict/risk",
            json=test_data
        )
        
        assert response.status_code == 422  # Validation error
        assert "value is not a valid enumeration member" in response.json()["detail"][0]["msg"]


@pytest.mark.db_required
class TestTreatmentPrediction:
    """Tests for the treatment prediction endpoint."""

    @pytest.mark.db_required
def test_predict_treatment_success(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test successful treatment prediction generation."""
        # Setup mock return value
        mock_xgboost_service.predict_treatment_response.return_value.to_dict.return_value = {
            "prediction_id": "pred-123",
            "patient_id": "patient-456",
            "model_id": "model-789",
            "prediction_type": "treatment_response_medication",
            "timestamp": "2025-03-29T12:00:00Z",
            "confidence": 0.85,
            "response_level": "good",
            "response_score": 0.75,
            "time_to_response_days": 21,
            "features_used": ["age", "genotype"],
            "explanation": "Good response expected based on patient profile",
            "validation_status": "pending",
            "treatment_category": "medication_ssri",
            "treatment_details": {"medication": "escitalopram", "dosage": 10},
            "suggested_adjustments": []
        }
        
        # Test data
        test_data = {
            "patient_id": "patient-456",
            "treatment_category": "medication_ssri",
            "treatment_details": {
                "medication": "escitalopram",
                "dosage": 10
            },
            "features": {
                "age": 35,
                "genotype": "CYP2D6-normal"
            }
        }
        
        response = client.post(
            "/api/v1/xgboost/predict/treatment",
            json=test_data
        )
        
        assert response.status_code == 201
        assert response.json()["prediction_id"] == "pred-123"
        assert response.json()["response_level"] == "good"
        assert response.json()["treatment_category"] == "medication_ssri"
        
        # Verify the service was called with correct parameters
        mock_xgboost_service.predict_treatment_response.assert_called_once()
        args, kwargs = mock_xgboost_service.predict_treatment_response.call_args
        assert kwargs["patient_id"] == "patient-456"
        assert kwargs["treatment_category"].value == "medication_ssri"
        assert kwargs["treatment_details"]["medication"] == "escitalopram"


@pytest.mark.db_required
class TestGetPrediction:
    """Tests for the get prediction endpoint."""

    @pytest.mark.db_required
def test_get_prediction_success(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test successfully retrieving a prediction."""
        # Setup mock return value
        mock_prediction = MagicMock()
        mock_prediction.patient_id = "patient-456"
        mock_prediction.to_dict.return_value = {
            "prediction_id": "pred-123",
            "patient_id": "patient-456",
            "model_id": "model-789",
            "prediction_type": "risk_relapse",
            "timestamp": "2025-03-29T12:00:00Z",
            "confidence": 0.85,
            "risk_level": "high",
            "risk_score": 0.75,
            "time_frame_days": 90,
            "features_used": ["age", "phq9_score"],
            "explanation": "High risk based on recent symptoms",
            "validation_status": "pending",
            "contributing_factors": [{"name": "phq9_score", "impact": 0.8}]
        }
        mock_xgboost_service.get_prediction.return_value = mock_prediction
        
        response = client.get("/api/v1/xgboost/predictions/pred-123")
        
        assert response.status_code == 200
        assert response.json()["prediction_id"] == "pred-123"
        assert response.json()["patient_id"] == "patient-456"
        
        # Verify the service was called with correct parameters
        mock_xgboost_service.get_prediction.assert_called_once_with("pred-123")

    @pytest.mark.db_required
def test_get_prediction_not_found(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test retrieving a non-existent prediction."""
        mock_xgboost_service.get_prediction.side_effect = PredictionNotFoundError("Prediction pred-123 not found")
        
        response = client.get("/api/v1/xgboost/predictions/pred-123")
        
        assert response.status_code == 404
        assert "Prediction not found" in response.json()["detail"]


@pytest.mark.db_required
class TestValidatePrediction:
    """Tests for the prediction validation endpoint."""

    @pytest.mark.db_required
def test_validate_prediction_success(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test successfully validating a prediction."""
        # Setup mocks
        mock_prediction = MagicMock()
        mock_prediction.patient_id = "patient-456"
        mock_xgboost_service.get_prediction.return_value = mock_prediction
        mock_xgboost_service.validate_prediction.return_value = True
        
        test_data = {
            "status": "validated",
            "validator_notes": "Clinically confirmed"
        }
        
        response = client.post(
            "/api/v1/xgboost/predictions/pred-123/validate",
            json=test_data
        )
        
        assert response.status_code == 200
        assert response.json()["prediction_id"] == "pred-123"
        assert response.json()["status"] == "validated"
        assert response.json()["success"] is True
        
        # Verify the service was called with correct parameters
        mock_xgboost_service.validate_prediction.assert_called_once()
        args, kwargs = mock_xgboost_service.validate_prediction.call_args
        assert kwargs["prediction_id"] == "pred-123"
        assert kwargs["status"].value == "validated"
        assert kwargs["validator_notes"] == "Clinically confirmed"

    @pytest.mark.db_required
def test_validate_prediction_not_found(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test validating a non-existent prediction."""
        mock_xgboost_service.get_prediction.side_effect = PredictionNotFoundError("Prediction pred-123 not found")
        
        test_data = {
            "status": "validated",
            "validator_notes": "Clinically confirmed"
        }
        
        response = client.post(
            "/api/v1/xgboost/predictions/pred-123/validate",
            json=test_data
        )
        
        assert response.status_code == 404
        assert "Prediction not found" in response.json()["detail"]


@pytest.mark.db_required
class TestCompareTreatments:
    """Tests for the treatment comparison endpoint."""

    @pytest.mark.db_required
def test_compare_treatments_success(self, mock_auth, mock_patient_access, mock_xgboost_service):
        """Test successfully comparing treatments."""
        # Setup mock return value
        mock_xgboost_service.compare_treatments.return_value = {
            "patient_id": "patient-456",
            "timestamp": "2025-03-29T12:00:00Z",
            "treatments_compared": 2,
            "results": [
                {
                    "treatment_category": "medication_ssri",
                    "treatment_details": {"medication": "escitalopram"},
                    "response_level": "good",
                    "response_score": 0.75,
                    "time_to_response_days": 21,
                    "confidence": 0.85,
                    "suggested_adjustments": [],
                    "prediction_id": "pred-123",
                    "relative_efficacy": 100.0
                },
                {
                    "treatment_category": "therapy_cbt",
                    "treatment_details": {"frequency": "weekly"},
                    "response_level": "moderate",
                    "response_score": 0.60,
                    "time_to_response_days": 42,
                    "confidence": 0.80,
                    "suggested_adjustments": [],
                    "prediction_id": "pred-124",
                    "relative_efficacy": 80.0
                }
            ],
            "recommendation": {
                "recommended_treatment": "medication_ssri",
                "reasoning": "Higher predicted response",
                "confidence": 0.85
            }
        }
        
        # Test data
        test_data = {
            "patient_id": "patient-456",
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
                "age": 35,
                "diagnosis": "major_depressive_disorder"
            }
        }
        
        response = client.post(
            "/api/v1/xgboost/compare/treatments",
            json=test_data
        )
        
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-456"
        assert response.json()["treatments_compared"] == 2
        assert len(response.json()["results"]) == 2
        assert response.json()["recommendation"]["recommended_treatment"] == "medication_ssri"
        
        # Verify the service was called with correct parameters
        mock_xgboost_service.compare_treatments.assert_called_once()
        args, kwargs = mock_xgboost_service.compare_treatments.call_args
        assert kwargs["patient_id"] == "patient-456"
        assert len(kwargs["treatment_options"]) == 2
        assert kwargs["treatment_options"][0]["category"] == "medication_ssri"

    @pytest.mark.db_required
def test_compare_treatments_insufficient_options(self, mock_auth, mock_patient_access):
        """Test comparing treatments with less than 2 options."""
        # Test data with only one treatment option
        test_data = {
            "patient_id": "patient-456",
            "treatment_options": [
                {
                    "category": "medication_ssri",
                    "details": {"medication": "escitalopram", "dosage": 10}
                }
            ],
            "features": {
                "age": 35,
                "diagnosis": "major_depressive_disorder"
            }
        }
        
        response = client.post(
            "/api/v1/xgboost/compare/treatments",
            json=test_data
        )
        
        assert response.status_code == 422  # Validation error
        assert "ensure this value has at least 2 items" in response.json()["detail"][0]["msg"]