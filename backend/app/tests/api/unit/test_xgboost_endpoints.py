"""
Unit tests for XGBoost API endpoints.

This module tests the XGBoost API endpoints to ensure they correctly
handle requests, interact with the XGBoost service, and return
appropriate responses.
"""

import json
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes.xgboost import router
from app.core.services.ml.xgboost import (
    ModelType,
    RiskLevel,
    ResponseLevel,
    XGBoostBaseError,
    ConfigurationError,
    ModelNotFoundError,
    PredictionError,
    ServiceConnectionError
)
from app.api.schemas.xgboost import (
    RiskPredictionRequest,
    TreatmentResponseRequest,
    OutcomePredictionRequest
)


# Module-level app/client creation removed; tests will use the client fixture


# Mock user for authentication
class MockUser:
    def __init__(self, id="test-user-id", role="clinician"):
        self.id = id
        self.role = role
        self.username = "test.user@novamind.com"


# Mock XGBoost service
class MockXGBoostService:
    def __init__(self):
        # Set up mock methods with AsyncMock for async methods
        self.predict_risk_async = AsyncMock()
        self.predict_treatment_response_async = AsyncMock()
        self.predict_outcome_async = AsyncMock()
        self.get_feature_importance = MagicMock()
        self.simulate_digital_twin = MagicMock()
        self.get_model_info = MagicMock()
        
    def setup_success_responses(self):
        """Set up mock responses for successful API calls."""
        # Risk prediction response
        self.predict_risk_async.return_value = MagicMock(
            prediction_id=str(uuid.uuid4()),
            patient_id="patient-123",
            model_type=ModelType.RISK_SUICIDE,
            model_version="1.0.0",
            risk_level=RiskLevel.MODERATE,
            risk_score=0.65,
            confidence=0.82,
            timestamp=datetime.now(),
            contributing_factors=[
                {"feature": "phq9_score", "importance": 0.4, "description": "PHQ-9 score indicates moderate depression"}
            ],
            explanation="Moderate suicide risk based on clinical assessment"
        )
        
        # Treatment response prediction
        self.predict_treatment_response_async.return_value = MagicMock(
            prediction_id=str(uuid.uuid4()),
            patient_id="patient-123",
            model_type=ModelType.TREATMENT_RESPONSE_MEDICATION,
            model_version="1.0.0",
            response_level=ResponseLevel.GOOD,
            response_score=0.75,
            confidence=0.85,
            timestamp=datetime.now(),
            treatment_type="medication",
            treatment_details={"medication": "Escitalopram", "dosage": "10mg"},
            suggested_adjustments=[{"type": "dosage", "action": "increase", "value": "15mg"}],
            explanation="Good response expected based on medication history"
        )
        
        # Outcome prediction
        self.predict_outcome_async.return_value = MagicMock(
            prediction_id=str(uuid.uuid4()),
            patient_id="patient-123",
            model_type=ModelType.OUTCOME_SHORT_TERM,
            model_version="1.0.0",
            outcome_score=0.72,
            confidence=0.80,
            timestamp=datetime.now(),
            domain_predictions={
                "depression": 0.65,
                "anxiety": 0.70,
                "functioning": 0.80
            },
            timeframe_weeks=12,
            explanation="Positive outcome expected within 12 weeks"
        )
        
        # Feature importance
        self.get_feature_importance.return_value = [
            MagicMock(
                feature_name="phq9_score",
                importance_value=0.35,
                category="clinical",
                description="Patient Health Questionnaire score"
            ),
            MagicMock(
                feature_name="medication_adherence",
                importance_value=0.25,
                category="treatment",
                description="Adherence to prescribed medication"
            )
        ]
        
        # Digital twin simulation
        self.simulate_digital_twin.return_value = {
            "simulation_id": str(uuid.uuid4()),
            "final_state": {
                "phq9_score": 8,
                "gad7_score": 6
            },
            "trajectories": {
                "depression": [15, 12, 10, 8],
                "anxiety": [12, 10, 8, 6]
            }
        }
        
        # Model info
        self.get_model_info.return_value = {
            "model_type": "risk_suicide",
            "model_version": "1.0.0",
            "training_date": "2025-01-01T00:00:00Z",
            "accuracy_metrics": {
                "accuracy": 0.92,
                "precision": 0.94,
                "recall": 0.90,
                "f1_score": 0.92,
                "auc_roc": 0.95,
                "calibration_error": 0.03
            },
            "feature_requirements": [
                "phq9_score", "gad7_score", "age", "gender", "previous_attempts"
            ]
        }
    
    def setup_error_responses(self):
        """Set up mock responses for error cases."""
        self.predict_risk_async.side_effect = ModelNotFoundError(
            "Model not found: risk_nonexistent",
            model_type="risk_nonexistent"
        )
        self.predict_treatment_response_async.side_effect = PredictionError(
            "Prediction failed: insufficient data",
            model_type=ModelType.TREATMENT_RESPONSE_MEDICATION,
            cause="Missing required features"
        )
        self.predict_outcome_async.side_effect = ServiceConnectionError(
            "Failed to connect to prediction service",
            service_name="SageMaker",
            cause="Timeout"
        )


# Mock dependency overrides
@pytest.fixture
def mock_dependencies():
    """Set up dependency overrides for testing."""
    with patch("app.api.routes.xgboost.get_current_clinician", return_value=MockUser()):
        with patch("app.api.routes.xgboost.get_xgboost_service") as mock_get_service:
            service = MockXGBoostService()
            service.setup_success_responses()
            mock_get_service.return_value = service
            yield service


# Mock error dependency overrides
@pytest.fixture
def mock_error_dependencies():
    """Set up dependency overrides for error cases."""
    with patch("app.api.routes.xgboost.get_current_clinician", return_value=MockUser()):
        with patch("app.api.routes.xgboost.get_xgboost_service") as mock_get_service:
            service = MockXGBoostService()
            service.setup_error_responses()
            mock_get_service.return_value = service
            yield service


# === Test Cases ===

def test_predict_risk_endpoint(client: TestClient, mock_dependencies):
    """Test the risk prediction endpoint with valid data."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "risk_type": "suicide",
        "clinical_data": {
            "phq9_score": 15,
            "gad7_score": 12,
            "medication_adherence": 0.8
        },
        "demographic_data": {
            "age": 35,
            "gender": "female"
        }
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/risk-prediction", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "patient-123"
    assert data["risk_type"] == "risk_suicide"
    assert "risk_level" in data
    assert "risk_score" in data
    assert "confidence" in data
    assert "features" in data
    assert "explanations" in data
    
    # Verify service was called with correct arguments
    mock_dependencies.predict_risk_async.assert_called_once()
    call_args = mock_dependencies.predict_risk_async.call_args[1]
    assert call_args["patient_id"] == "patient-123"
    assert call_args["model_type"] == ModelType.RISK_SUICIDE
    
    # Verify features were combined correctly
    assert "phq9_score" in call_args["features"]
    assert "age" in call_args["features"]


def test_predict_treatment_response_endpoint(client: TestClient, mock_dependencies):
    """Test the treatment response prediction endpoint with valid data."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "treatment_type": "ssri",
        "treatment_details": {
            "medication": "Escitalopram",
            "dosage": "10mg daily"
        },
        "clinical_data": {
            "phq9_score": 15,
            "gad7_score": 12
        },
        "genetic_data": ["CYP2D6*1/*2", "SLC6A4 L/L"]
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/treatment-response", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "patient-123"
    assert data["treatment_type"] == "medication"
    assert "response_level" in data
    assert "response_score" in data
    assert "confidence" in data
    assert "adjustments" in data
    
    # Verify service was called with correct arguments
    mock_dependencies.predict_treatment_response_async.assert_called_once()
    call_args = mock_dependencies.predict_treatment_response_async.call_args[1]
    assert call_args["patient_id"] == "patient-123"
    assert call_args["model_type"] == ModelType.TREATMENT_RESPONSE_MEDICATION
    assert call_args["treatment_type"] == "ssri"
    assert call_args["treatment_details"]["medication"] == "Escitalopram"
    
    # Verify features were handled correctly
    assert "phq9_score" in call_args["patient_features"]
    assert "genetic_markers" in call_args["patient_features"]


def test_predict_outcome_endpoint(client: TestClient, mock_dependencies):
    """Test the outcome prediction endpoint with valid data."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "outcome_timeframe": {
            "weeks": 12
        },
        "clinical_data": {
            "phq9_score": 15,
            "gad7_score": 12
        },
        "treatment_plan": {
            "interventions": ["SSRI medication", "CBT therapy"],
            "duration_weeks": 12
        },
        "social_determinants": {
            "support_network": "strong",
            "housing_stability": "stable"
        }
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/outcome-prediction", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "patient-123"
    assert "overall_outcome_score" in data
    assert "confidence" in data
    assert "domains" in data
    assert "recommendations" in data
    
    # Verify service was called with correct arguments
    mock_dependencies.predict_outcome_async.assert_called_once()
    call_args = mock_dependencies.predict_outcome_async.call_args[1]
    assert call_args["patient_id"] == "patient-123"
    assert call_args["model_type"] == ModelType.OUTCOME_SHORT_TERM
    assert call_args["timeframe_weeks"] == 12
    
    # Verify features were combined correctly
    assert "phq9_score" in call_args["patient_features"]
    assert "support_network" in call_args["patient_features"]


def test_get_feature_importance_endpoint(client: TestClient, mock_dependencies):
    """Test the feature importance endpoint."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "model_type": "risk-suicide",
        "prediction_id": "pred-123"
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/feature-importance", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "patient-123"
    assert data["model_type"] == "risk-suicide"
    assert "feature_importance" in data
    assert "visualization" in data
    
    # Verify service was called with correct arguments
    mock_dependencies.get_feature_importance.assert_called_once()
    call_args = mock_dependencies.get_feature_importance.call_args[1]
    assert call_args["model_type"] == ModelType.RISK_SUICIDE


def test_digital_twin_integration_endpoint(client: TestClient, mock_dependencies):
    """Test the digital twin integration endpoint."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "profile_id": "profile-123",
        "prediction_id": "pred-123"
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/digital-twin", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "patient-123"
    assert data["profile_id"] == "profile-123"
    assert data["prediction_id"] == "pred-123"
    assert "status" in data
    assert "visualization_url" in data
    
    # Verify service was called
    mock_dependencies.simulate_digital_twin.assert_called_once()


def test_model_info_endpoint(client: TestClient, mock_dependencies):
    """Test the model info endpoint."""
    # Prepare request data
    request_data = {
        "model_type": "risk-suicide"
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/model-info", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["model_type"] == "risk-suicide"
    assert "version" in data
    assert "performance_metrics" in data
    assert "features" in data
    
    # Verify service was called with correct arguments
    mock_dependencies.get_model_info.assert_called_once()
    call_args = mock_dependencies.get_model_info.call_args[1]
    assert call_args["model_type"] == ModelType.RISK_SUICIDE


# === Error Handling Tests ===

def test_model_not_found_error(client: TestClient, mock_error_dependencies):
    """Test handling of ModelNotFoundError."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "risk_type": "nonexistent",
        "clinical_data": {
            "phq9_score": 15
        }
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/risk-prediction", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_type"] == "not_found"


def test_prediction_error(client: TestClient, mock_error_dependencies):
    """Test handling of PredictionError."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "treatment_type": "ssri",
        "treatment_details": {
            "medication": "Escitalopram"
        },
        "clinical_data": {}
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/treatment-response", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_type"] == "prediction_error"


def test_service_connection_error(client: TestClient, mock_error_dependencies):
    """Test handling of ServiceConnectionError."""
    # Prepare request data
    request_data = {
        "patient_id": "patient-123",
        "outcome_timeframe": {
            "weeks": 12
        },
        "clinical_data": {
            "phq9_score": 15
        },
        "treatment_plan": {}
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/outcome-prediction", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_type"] == "service_unavailable"


def test_validation_error(client: TestClient):
    """Test handling of validation errors with missing required fields."""
    # Prepare request data with missing required fields
    request_data = {
        "patient_id": "patient-123",
        # Missing risk_type
        "clinical_data": {}
    }
    
    # Make the request
    response = client.post("/api/v1/xgboost/risk-prediction", json=request_data) # Corrected path
    
    # Verify response
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "detail" in data