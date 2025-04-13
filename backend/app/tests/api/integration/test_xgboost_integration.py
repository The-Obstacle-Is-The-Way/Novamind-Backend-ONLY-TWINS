"""
Integration tests for the XGBoost service API.

These tests verify that the API routes and the underlying service work together correctly.
Tests use the MockXGBoostService to avoid external dependencies while ensuring
the entire API flow functions as expected.
"""

import json
import pytest

# Import FastAPI and TestClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

# Router import remains the same
from app.api.routes.xgboost import router
from app.core.services.ml.xgboost import ()
get_xgboost_service,
MockXGBoostService,
PredictionType,
TreatmentCategory,
RiskLevel,



# Create a test client fixture
@pytest.fixture
def client():
    """Create a FastAPI test client."""
    # Create a FastAPI app
    app = FastAPI()

    # Include the router
    app.include_router(router)

    # Create a test client with authentication headers
    from fastapi.testclient import TestClient

    test_client = TestClient(app)

    # Add a valid JWT token to all requests
    # This is a dummy token that will be accepted by our mocked authentication
    test_client.headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjbGluaWNpYW4tMTIzIiwicm9sZSI6ImNsaW5pY2lhbiJ9.fake-signature"
    }

#     return test_client


# Override dependencies for testing
@pytest.fixture(autouse=True)
def mock_auth_dependencies():
    """Mock authentication dependencies for all tests."""
    with patch()
    "app.api.dependencies.auth.get_current_active_clinician"
    ) as mock_get_clinician, patch(
    "app.api.dependencies.auth.get_current_user"
    ) as mock_get_user:
        # Set up mock returns
        mock_get_clinician.return_value = {
        "id": "clinician-123", "name": "Dr. Smith"
        }
        mock_get_user.return_value = {"id": "user-123", "name": "Test User"}

        yield


@pytest.fixture
def mock_service():
    """Set up a real MockXGBoostService for integration testing."""
    # Create a real mock service (not a MagicMock)
    mock_service = MockXGBoostService()

    # Configure the mock service
    mock_service.initialize({)
    "log_level": "INFO",
    "mock_delay_ms": 0,  # No delay for tests
    "risk_level_distribution": {
    "low": 0.7,
    "medium": 0.2,
    "high": 0.1,
    },
    # Configure mock responses based on known test values
    "known_responses": {
    # Patient 123 will always get high risk
    "patient-123": {
    "risk_level": "high",
    "confidence": 0.92,
    "factors": []
    "medication_non_compliance",
    "comorbid_anxiety",
    "family_history"
                
    },
    # Patient 456 will always get low risk
    "patient-456": {
    "risk_level": "low",
    "confidence": 0.89,
    "factors": []
    },
    },
    # Configure success rates for treatments
    "treatment_responses": {
    "therapy_cbt": {
    "patient-123": 0.35,  # CBT not very effective for high risk
    "patient-456": 0.85,  # CBT very effective for low risk
    },
    "medication_ssri": {
    "patient-123": 0.75,  # SSRI effective for high risk
    "patient-456": 0.65,  # SSRI somewhat effective for low risk
    },
    "combined_therapy": {
    "patient-123": 0.9,   # Combined most effective for high risk
    "patient-456": 0.75,  # Combined effective for low risk
    }
    }
    }

    # Set up mocks for the service methods
    # Helper to add a prediction timestamp
    def with_timestamp(response):
        if isinstance(response, dict):
            response["prediction_timestamp"] = datetime.now().isoformat()
            return response
            
    # Create mocks for each service method
    # Return real data from the mock service, just add timestamps
    # Use side_effect to call the real methods
    mock_service.predict_risk = MagicMock(side_effect=lambda patient_id, **kwargs:)
    with_timestamp(mock_service._predict_risk_internal(patient_id

    mock_service.predict_treatment_response = MagicMock()
    return_value={
    "prediction_id": "pred-456",
    "patient_id": "patient-123",
    "treatment_type": "medication_ssri",
    "success_probability": 0.75,
    "confidence": 0.88,
    "expected_outcomes": {
    "response_time_days": 14,
    "remission_probability": 0.65,
    "side_effects_probability": 0.35
    },
    "prediction_timestamp": datetime.now().isoformat(),
    "model_version": "0.1.0"
    }
    

    # Set up tracking mocks
    mock_service.track_prediction_feedback = MagicMock(return_value=True)
    mock_service.track_treatment_outcome = MagicMock(return_value=True)
    mock_service.get_prediction_history = MagicMock(return_value=[)]
    {
    "prediction_id": "pred-123",
    "patient_id": "patient-123",
    "type": "risk",
    "prediction": {
    "risk_level": "high",
    "confidence": 0.92,
    "factors": ["medication_non_compliance"]
    },
    "timestamp": "2023-01-01T10:00:00",
    "model_version": "0.1.0"
    },
    {
    "prediction_id": "pred-456",
    "patient_id": "patient-123",
    "type": "treatment",
    "prediction": {
    "treatment_type": "medication_ssri",
    "success_probability": 0.75
    },
    "timestamp": "2023-01-02T10:00:00",
    "model_version": "0.1.0"
    }
    
            
    # Return the configured mock service
#         return mock_service


@pytest.fixture
def mock_get_service_factory(mock_service):
    """Create a factory for the service."""
    
    # Patch the get_xgboost_service function
    with patch("app.api.routes.xgboost.get_xgboost_service", return_value=mock_service):
        yield


class TestXGBoostIntegration:
    """Integration tests for the XGBoost API."""

    def test_risk_prediction_flow(self, client: TestClient, mock_service):
        """Test the complete risk prediction workflow."""
        # 1. Make a risk prediction request
        risk_request = {
        "patient_id": "patient-123",
        "clinical_features": {
        "age": 45,
        "gender": "female",
        "previous_episodes": 2,
        "medication_history": ["fluoxetine", "sertraline"],
        "current_phq9_score": 18
        }
        }
        
        response = client.post()
        "/api/v1/ml/xgboost/risk-prediction",
        json=risk_request
        assert response.status_code == 200
        assert "prediction_id" in response.json()
        prediction_id = response.json()["prediction_id"]

        # 2. Retrieve the prediction
        response = client.get()
        f"/api/v1/ml/xgboost/prediction/{prediction_id}"
        
        assert response.status_code == 200
        assert response.json()["prediction_id"] == prediction_id
        assert response.json()["prediction"]["risk_level"] == "high"  # For patient-123
        
        # 3. Submit feedback on the prediction
        feedback_request = {
        "prediction_id": prediction_id,
        "actual_outcome": "high",
        "clinician_notes": "Patient showed severe symptoms exactly as predicted",
        "accuracy_rating": 5  # 1-5 scale
        }
        
        response = client.post()
        f"/api/v1/ml/xgboost/feedback",
        json=feedback_request
        
        assert response.status_code == 200
        assert response.json()["success"] == True
        
        # 4. Get treatment recommendations
        treatment_request = {
        "patient_id": "patient-123",
        "clinical_features": {
        "age": 45,
        "gender": "female",
        "previous_episodes": 2,
        "medication_history": ["fluoxetine", "sertraline"],
        "current_phq9_score": 18,
        "comorbidities": ["anxiety", "insomnia"],
        "previous_treatments": ["therapy_cbt"]
        },
        "treatment_options": ["medication_ssri", "therapy_cbt", "combined_therapy"]
        }
        
        response = client.post()
        "/api/v1/ml/xgboost/treatment-prediction",
        json=treatment_request
        
        assert response.status_code == 200
        assert "predictions" in response.json()
        assert len(response.json()["predictions"]) == 3  # One for each treatment option
        
        # 5. Track treatment outcome
        outcome_request = {
        "patient_id": "patient-123",
        "treatment_type": "medication_ssri",
        "outcome": "successful",
        "outcome_details": {
        "phq9_reduction": 10,
        "remission_achieved": True,
        "time_to_response_days": 21,
        "side_effects": ["nausea", "insomnia"],
        "side_effects_severity": "mild"
        },
        "clinician_notes": "Patient responded well to sertraline after 3 weeks"
        }
        
        response = client.post()
        "/api/v1/ml/xgboost/treatment-outcome",
        json=outcome_request
        
        assert response.status_code == 200
        assert response.json()["success"] == True
        
        # 6. Get prediction history
        response = client.get()
        f"/api/v1/ml/xgboost/prediction-history/patient-123"
        
        assert response.status_code == 200
        assert "predictions" in response.json()
        assert len(response.json()["predictions"]) > 0

        def test_batch_risk_prediction(self, client: TestClient, mock_service):
        """Test batch risk prediction functionality."""
        # Create a batch request with multiple patients
        batch_request = {
        "patients": []
        {
        "patient_id": "patient-123",
        "clinical_features": {
        "age": 45,
        "gender": "female",
        "previous_episodes": 2,
        "current_phq9_score": 18
        }
        },
        {
        "patient_id": "patient-456",
        "clinical_features": {
        "age": 32,
        "gender": "male",
        "previous_episodes": 0,
        "current_phq9_score": 8
        }
        }
            
        }
        
        response = client.post()
        "/api/v1/ml/xgboost/batch-risk-prediction",
        json=batch_request
        
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        
        # Check that patient-123 got high risk (based on our mock setup)
        patient_123_result = next(r for r in results if r["patient_id"] == "patient-123")
        assert patient_123_result["prediction"]["risk_level"] == "high"
        
        # Check that patient-456 got low risk (based on our mock setup)
        patient_456_result = next(r for r in results if r["patient_id"] == "patient-456")
        assert patient_456_result["prediction"]["risk_level"] == "low"
    
        def test_treatment_comparison(self, client: TestClient, mock_service):
        """Test treatment comparison functionality."""
        # Create a comparison request
        comparison_request = {
        "patient_id": "patient-123",
        "clinical_features": {"age": 40, "prior_treatment_failures": 2, "severity_score": 7},
        "treatment_options": []
        {"treatment_id": "ssri_a", "category": TreatmentCategory.SSRI},
        {"treatment_id": "snri_b", "category": TreatmentCategory.SNRI},
        ],
        }
        response = client.post()
        "/api/v1/ml/xgboost/treatment-response", json=comparison_request
        
        assert response.status_code == 200
        comparison_data = response.json()
        assert "comparison_id" in comparison_data
        assert len(comparison_data["results"]) == 2
        assert comparison_data["results"][0]["treatment_id"] == "ssri_a"

    @pytest.mark.asyncio
    async def test_model_info_flow(self, client: TestClient, mock_service):
        """Test the model information workflow."""
        # This test assumes a model has been loaded or is mockable
        # We'll use a placeholder model ID, assuming the mock service handles it
        model_id = "mock-model-123"

        # 1. Get model details
        response = client.get(f"/api/v1/ml/xgboost/models/{model_id}")
        assert response.status_code == 200
        model_data = response.json()
        assert model_data["model_id"] == model_id
        assert "model_type" in model_data
        assert "trained_date" in model_data

        # 2. Get model features
        response = client.get(f"/api/v1/ml/xgboost/models/{model_id}/features")
        assert response.status_code == 200
        features_data = response.json()
        assert isinstance(features_data["features"], list)
        assert len(features_data["features"]) > 0  # Assuming mock provides some features

    @pytest.mark.asyncio
    async def test_healthcheck(self, client: TestClient, mock_service):
        """Test the healthcheck endpoint."""
        response = client.get("/api/v1/ml/xgboost/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}