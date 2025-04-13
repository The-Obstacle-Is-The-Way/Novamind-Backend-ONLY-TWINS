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
from app.core.services.ml.xgboost.interface import ModelType
from app.core.services.ml.xgboost.enums import RiskLevel, ResponseLevel
from app.core.services.ml.xgboost.exceptions import ()
XGBoostServiceError,
ConfigurationError,
ModelNotFoundError,
PredictionError,
ServiceConnectionError,

from app.api.routes.xgboost import get_current_user, router
from app.api.schemas.xgboost import ()
RiskPredictionRequest,
TreatmentResponseRequest,
OutcomePredictionRequest,



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
        # Set up mock methods with MagicMock for all methods
        self.predict_risk = MagicMock()
        self.predict_treatment_response = MagicMock()
        self.predict_outcome = MagicMock()
        self.get_feature_importance = MagicMock()
        self.simulate_digital_twin = MagicMock()
        self.get_model_info = MagicMock()

        def setup_success_responses(self):
        """Set up mock responses for successful API calls."""
        # Risk prediction response
        self.predict_risk.return_value = {
        "prediction_id": str(uuid.uuid4()),
        "patient_id": "patient-123",
        "prediction": {
        "risk_level": RiskLevel.HIGH,
        "confidence": 0.85,
        "factors": []
        "previous_suicide_attempt",
        "comorbid_depression",
        "family_history",
        ],
        },
        "prediction_timestamp": datetime.now().isoformat(),
        "model_version": "1.0.0",
        }

        # Treatment response prediction
        self.predict_treatment_response.return_value = {
        "prediction_id": str(uuid.uuid4()),
        "patient_id": "patient-123",
        "treatment_type": "ssri",
        "success_probability": 0.72,
        "confidence": 0.80,
        "expected_outcomes": {
        "response_time_days": 21,
        "remission_probability": 0.65,
        "side_effects_probability": 0.35,
        },
        "prediction_timestamp": datetime.now().isoformat(),
        "model_version": "1.0.0",
        }

        # Outcome prediction
        self.predict_outcome.return_value = {
        "prediction_id": str(uuid.uuid4()),
        "patient_id": "patient-123",
        "outcome_type": "remission",
        "probability": 0.68,
        "confidence": 0.75,
        "expected_timeframe": {
        "min_weeks": 8,
        "max_weeks": 16,
        "confidence_interval": "90%",
        },
        "prediction_timestamp": datetime.now().isoformat(),
        "model_version": "1.0.0",
        }

        # Feature importance
        self.get_feature_importance.return_value = {
        "model_id": "model-123",
        "model_type": "risk_prediction",
        "feature_importance": []
        {"feature": "previous_suicide_attempt", "importance": 0.35},
        {"feature": "phq9_score", "importance": 0.25},
        {"feature": "age", "importance": 0.15},
        {"feature": "gender", "importance": 0.10},
        {"feature": "treatment_history", "importance": 0.15},
        ],
        "timestamp": datetime.now().isoformat(),
        }

        # Digital twin simulation
        self.simulate_digital_twin.return_value = {
        "simulation_id": str(uuid.uuid4()),
        "patient_id": "patient-123",
        "baseline": {
        "risk_level": RiskLevel.HIGH,
        "phq9_score": 18,
        "gad7_score": 15,
        },
        "simulations": []
        {
        "treatment": "ssri",
        "predicted_outcomes": {
        "risk_level": RiskLevel.MEDIUM,
        "phq9_reduction": 8,
        "remission_probability": 0.65,
        },
        },
        {
        "treatment": "cbt",
        "predicted_outcomes": {
        "risk_level": RiskLevel.MEDIUM,
        "phq9_reduction": 6,
        "remission_probability": 0.55,
        },
        },
        {
        "treatment": "combined",
        "predicted_outcomes": {
        "risk_level": RiskLevel.LOW,
        "phq9_reduction": 12,
        "remission_probability": 0.80,
        },
        },
        ],
        "simulation_timestamp": datetime.now().isoformat(),
        "model_version": "1.0.0",
        }

        # Model info
        self.get_model_info.return_value = {
        "model_id": "model-123",
        "model_type": "risk_prediction",
        "version": "1.0.0",
        "trained_date": "2023-01-15",
        "performance_metrics": {
        "accuracy": 0.85,
        "precision": 0.82,
        "recall": 0.88,
        "f1_score": 0.85,
        "auc_roc": 0.90,
        },
        "feature_count": 25,
        "dataset_size": 10000,
        "last_evaluation_date": "2023-02-01",
        }

        def setup_error_responses(self):
        """Set up mock responses that raise exceptions for error testing."""
        self.predict_risk.side_effect = ModelNotFoundError()
        "Model for risk type 'nonexistent' not found"
        
        self.predict_treatment_response.side_effect = PredictionError()
        "Cannot predict response for treatment type 'ssri' with provided data"
        
        self.predict_outcome.side_effect = ServiceConnectionError()
        "Failed to connect to prediction service"
        
        self.get_feature_importance.side_effect = ConfigurationError()
        "Invalid configuration for feature importance analysis"
        
        self.simulate_digital_twin.side_effect = XGBoostServiceError()
        "Generic XGBoost service error during simulation"
        
        self.get_model_info.side_effect = ValueError("Invalid model parameters")


# Client fixture
@pytest.fixture
        def client():
"""Create a test client for testing API endpoints."""
app = FastAPI()
app.include_router(router)

# Override the security dependency to bypass authentication
    def override_get_current_user():
        return MockUser()

app.dependency_overrides[get_current_user] = override_get_current_user

#             return TestClient(app)


@pytest.fixture
        def mock_dependencies():
"""Set up dependency overrides for testing."""
    with patch("app.api.routes.xgboost.get_current_user", return_value=MockUser()):
        with patch("app.api.routes.xgboost._get_xgboost_service") as mock_get_service:
            service = MockXGBoostService()
            service.setup_success_responses()

            def get_service():
                return service

            mock_get_service.return_value = get_service
            yield service


@pytest.fixture
                def mock_error_dependencies():
"""Set up dependency overrides for error cases."""
    with patch("app.api.routes.xgboost.get_current_user", return_value=MockUser()):
        with patch("app.api.routes.xgboost._get_xgboost_service") as mock_get_service:
            service = MockXGBoostService()
            service.setup_error_responses()

            # Make the service callable to match the expected behavior
            def get_service():
                return service

            mock_get_service.return_value = get_service
            yield service


# === Test Cases ===

                def test_predict_risk_endpoint(client: TestClient, mock_dependencies):
"""Test the risk prediction endpoint with valid data."""
# Prepare request data
request_data = {
"patient_id": "patient-123",
"risk_type": "suicide",
"clinical_data": {
"phq9_score": 18,
"previous_attempt": True,
"family_history": True,
},
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/risk-prediction", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 200
data = response.json()
assert "prediction_id" in data
assert data["patient_id"] == "patient-123"
assert "prediction" in data
assert data["prediction"]["risk_level"] == RiskLevel.HIGH


    def test_predict_treatment_response_endpoint(client: TestClient, mock_dependencies):
"""Test the treatment response prediction endpoint with valid data."""
# Prepare request data
request_data = {
"patient_id": "patient-123",
"treatment_type": "ssri",
"treatment_details": {"medication": "fluoxetine", "dose_mg": 20},
"clinical_data": {
"phq9_score": 18,
"previous_ssri_response": True,
"comorbidities": ["anxiety", "insomnia"],
},
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/treatment-response", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 200
data = response.json()
assert "prediction_id" in data
assert data["patient_id"] == "patient-123"
assert data["treatment_type"] == "ssri"
assert "success_probability" in data
assert "expected_outcomes" in data


    def test_predict_outcome_endpoint(client: TestClient, mock_dependencies):
"""Test the outcome prediction endpoint with valid data."""
# Prepare request data
request_data = {
"patient_id": "patient-123",
"outcome_timeframe": {"weeks": 12},
"clinical_data": {"phq9_score": 15, "gad7_score": 12},
"treatment_plan": {
"medications": ["fluoxetine"],
"therapy_types": ["cbt"],
"duration_weeks": 12,
},
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/outcome-prediction", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 200
data = response.json()
assert "prediction_id" in data
assert data["patient_id"] == "patient-123"
assert "probability" in data
assert "expected_timeframe" in data


    def test_get_feature_importance_endpoint(client: TestClient, mock_dependencies):
"""Test the feature importance endpoint."""
# Prepare request data
request_data = {
"model_type": "risk_prediction",
"risk_type": "suicide",
"include_descriptions": True,
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/feature-importance", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 200
data = response.json()
assert "model_id" in data
assert data["model_type"] == "risk_prediction"
assert "feature_importance" in data
assert len(data["feature_importance"]) > 0


    def test_digital_twin_integration_endpoint(client: TestClient, mock_dependencies):
"""Test the digital twin integration endpoint."""
# Prepare request data
request_data = {
"patient_id": "patient-123",
"clinical_profile": {
"phq9_score": 18,
"gad7_score": 15,
"current_medications": [],
"comorbidities": ["anxiety", "insomnia"],
},
"treatment_options": ["ssri", "cbt", "combined"],
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/digital-twin", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 200
data = response.json()
assert "simulation_id" in data
assert data["patient_id"] == "patient-123"
assert "baseline" in data
assert "simulations" in data
assert len(data["simulations"]) == 3


    def test_model_info_endpoint(client: TestClient, mock_dependencies):
"""Test the model info endpoint."""
# Prepare request data
request_data = {"model_type": "risk-suicide"}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/model-info", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 200
data = response.json()
assert "model_id" in data
assert "version" in data
assert "performance_metrics" in data
assert "trained_date" in data


    def test_model_not_found_error(client: TestClient, mock_error_dependencies):
"""Test handling of ModelNotFoundError."""
# Prepare request data
request_data = {
"patient_id": "patient-123",
"risk_type": "nonexistent",  # This will trigger ModelNotFoundError
"clinical_data": {},
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/risk-prediction", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 404
data = response.json()
assert "detail" in data
assert any("nonexistent" in str(item) for item in data["detail"])


    def test_prediction_error(client: TestClient, mock_error_dependencies):
"""Test handling of PredictionError."""
# Prepare request data
request_data = {
"patient_id": "patient-123",
"treatment_type": "ssri",
"treatment_details": {"medication": "Escitalopram"},
"clinical_data": {},
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/treatment-response", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 422
data = response.json()
assert "detail" in data
assert any("ssri" in str(item) for item in data["detail"])


    def test_service_connection_error(client: TestClient, mock_error_dependencies):
"""Test handling of ServiceConnectionError."""
# Prepare request data
request_data = {
"patient_id": "patient-123",
"outcome_timeframe": {"weeks": 12},
"clinical_data": {"phq9_score": 15},
"treatment_plan": {},
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/outcome-prediction", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 503
data = response.json()
assert "detail" in data
assert "Failed to connect to prediction service" in data["detail"]


    def test_validation_error(client: TestClient):
"""Test handling of validation errors with missing required fields."""
# Prepare request data with missing required fields
request_data = {
"patient_id": "patient-123",
# Missing risk_type
"clinical_data": {},
}

# Make the request
response = client.post()
"/api/v1/ml/xgboost/risk-prediction", json=request_data
)  # Corrected path

# Verify response
assert response.status_code == 422  # Unprocessable Entity
data = response.json()
assert "detail" in data