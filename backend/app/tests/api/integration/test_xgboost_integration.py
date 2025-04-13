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
from app.core.services.ml.xgboost import (
    get_xgboost_service,
    MockXGBoostService,
    PredictionType,
    TreatmentCategory,
    RiskLevel,
)


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

    return test_client


# Override dependencies for testing
@pytest.fixture(autouse=True)
def mock_auth_dependencies():
    """Mock authentication dependencies for all tests."""
    with patch(
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
    # Create a real mock service instance
    service = MockXGBoostService()
    
    # Override the get_xgboost_service dependency
    with patch("app.api.routes.xgboost.get_xgboost_service") as mock_get_service:
        mock_get_service.return_value = service
        yield service


@pytest.mark.integration
class TestXGBoostIntegration:
    """Integration tests for XGBoost API endpoints."""

    @pytest.mark.asyncio
    async def test_risk_prediction_flow(self, client: TestClient, mock_service):
        """Test the risk prediction workflow."""
        # 1. Submit a risk prediction request
        risk_request = {
            "patient_id": "patient-123",
            "prediction_type": PredictionType.RELAPSE_RISK,
            "clinical_features": {
                "age": 40,
                "prior_episodes": 2,
                "severity_score": 7,
                "medication_adherence": 0.8,
            },
            "timeframe_days": 90,
        }
        response = client.post(
            "/api/v1/ml/xgboost/risk-prediction", json=risk_request
        )
        
        assert response.status_code == 200
        prediction_data = response.json()
        assert "prediction_id" in prediction_data
        assert "risk_score" in prediction_data
        assert "risk_level" in prediction_data
        assert "confidence" in prediction_data
        
        # 2. Retrieve the prediction by ID
        prediction_id = prediction_data["prediction_id"]
        response = client.get(f"/api/v1/ml/xgboost/predictions/{prediction_id}")
        
        assert response.status_code == 200
        retrieved_data = response.json()
        assert retrieved_data["prediction_id"] == prediction_id
        assert retrieved_data["risk_score"] == prediction_data["risk_score"]
        
        # 3. Get explanation for the prediction
        response = client.get(f"/api/v1/ml/xgboost/predictions/{prediction_id}/explanation")
        
        assert response.status_code == 200
        explanation_data = response.json()
        assert "feature_importance" in explanation_data
        assert len(explanation_data["feature_importance"]) > 0
        assert "top_factors" in explanation_data

    @pytest.mark.asyncio
    async def test_treatment_response_prediction(self, client: TestClient, mock_service):
        """Test the treatment response prediction workflow."""
        # Submit a treatment response prediction request
        treatment_request = {
            "patient_id": "patient-123",
            "treatment_id": "ssri_fluoxetine",
            "treatment_category": TreatmentCategory.SSRI,
            "clinical_features": {
                "age": 40,
                "prior_treatment_failures": 2,
                "severity_score": 7,
                "anxiety_comorbidity": True,
            },
            "dosage_mg": 20,
            "duration_weeks": 8,
        }
        response = client.post(
            "/api/v1/ml/xgboost/treatment-response", json=treatment_request
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert "prediction_id" in response_data
        assert "response_probability" in response_data
        assert "expected_improvement" in response_data
        assert "confidence" in response_data
        assert "timeframe_weeks" in response_data

    @pytest.mark.asyncio
    async def test_treatment_comparison(self, client: TestClient, mock_service):
        """Test the treatment comparison workflow."""
        # Submit a treatment comparison request
        comparison_request = {
            "patient_id": "patient-123",
            "clinical_features": {"age": 40, "prior_treatment_failures": 2, "severity_score": 7},
            "treatment_options": [
                {"treatment_id": "ssri_a", "category": TreatmentCategory.SSRI},
                {"treatment_id": "snri_b", "category": TreatmentCategory.SNRI},
            ],
        }
        response = client.post(
            "/api/v1/ml/xgboost/treatment-response", json=comparison_request
        )
        
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