"""
Integration tests for the XGBoost service API.

These tests verify that the API routes and the underlying service work together correctly.
Tests use the MockXGBoostService to avoid external dependencies while ensuring
the entire API flow functions as expected.
"""

import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import FastAPI

from app.core.services.ml.xgboost import (
    get_xgboost_service,
    MockXGBoostService,
    PredictionType,
    TreatmentCategory,
    RiskLevel,
)
from fastapi import status

from app.core.services.ml.xgboost.interface import XGBoostInterface
from app.infrastructure.di.container import get_service # Use generic service provider
from app.presentation.api.v1.schemas.xgboost import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    TreatmentResponseRequest,
    TreatmentResponseResponse,
    OutcomePredictionRequest,
    OutcomePredictionResponse,
    ModelInfoRequest,
    ModelInfoResponse,
    FeatureImportanceRequest,
    FeatureImportanceResponse,
)
from app.presentation.api.v1.endpoints.xgboost import router as xgboost_router # Import the actual router

# Override dependencies for testing
@pytest.fixture
def mock_xgboost_service():
    """Fixture for a mock XGBoost service."""
    mock_service = AsyncMock(spec=XGBoostInterface)
    mock_service.predict_risk.return_value = {"risk_score": 0.75, "confidence": 0.9}
    mock_service.predict_treatment_response.return_value = {"response_probability": 0.8, "confidence": 0.85}
    mock_service.predict_outcome.return_value = {"outcome_prediction": "stable", "confidence": 0.92}
    mock_service.get_model_info.return_value = {"model_type": "test", "version": "1.0", "description": "Mock Model", "features": ["feat1", "feat2"]}
    mock_service.get_feature_importance.return_value = {"prediction_id": "pred123", "feature_importance": {"feat1": 0.6, "feat2": 0.4}}
    return mock_service

@pytest.fixture(scope="function") # Function scope if test isolation is needed
def test_app(mock_xgboost_service):
    """Creates a FastAPI test app instance with the mock XGBoost service."""
    app = FastAPI(title="Test XGBoost API")

    # Apply the dependency override for the XGBoostInterface
    app.dependency_overrides[get_service(XGBoostInterface)] = lambda: mock_xgboost_service

    # Placeholder router for testing setup (REMOVE THIS)
    # from fastapi import APIRouter
    # test_router = APIRouter()
    # @test_router.get("/test")
    # async def read_test():
    #     return {"msg": "Test Router"}
    # app.include_router(test_router, prefix="/api/v1/xgboost") # Include the placeholder router

    # Include the actual XGBoost router
    app.include_router(xgboost_router, prefix="/api/v1/xgboost") # Correct prefix

    return app

@pytest.fixture
def client(test_app):
    """Create a test client instance."""
    return TestClient(test_app)

@pytest.fixture(autouse=True)
def mock_auth_dependencies():
    """Mock authentication dependencies for all tests."""
    with patch("app.api.dependencies.auth.get_current_clinician") as mock_get_clinician, patch(
        "app.api.dependencies.auth.verify_patient_access"
    ) as mock_verify_access:
        # Set up mock returns
        mock_get_clinician.return_value = {"id": "clinician-123", "name": "Dr. Smith"}
        mock_verify_access.return_value = None

        yield

@pytest.fixture(autouse=True)
def mock_service():
    """Set up a real MockXGBoostService for integration testing."""
    # Create a real mock service (not a MagicMock,)
    mock_service = MockXGBoostService()
    mock_risk_level = RiskLevel.MODERATE
    mock_risk_score = 0.45
    mock_confidence = 0.85

    # Patch the factory function to return our configured mock service
    with patch("app.api.routes.xgboost.get_xgboost_service") as mock_get_service:
        mock_get_service.return_value = mock_service
        yield mock_service

@pytest.mark.db_required()
class TestXGBoostIntegration:
    """Integration tests for the XGBoost API."""

    def test_risk_prediction_flow(self, client: TestClient, mock_service):
        """Test the complete risk prediction workflow."""
        # Step 1: Generate a risk prediction
        risk_request = {
            "patient_id": "patient-123",
            "risk_type": "risk_relapse",
            "features": {
                "age": 45,
                "phq9_score": 15,
                "previous_hospitalizations": 1
            },
            "time_frame_days": 90,
        }

        response = client.post("/api/v1/xgboost/predict/risk", json=risk_request)
        assert response.status_code == 201

        # Save prediction ID for later steps
        prediction_id = response.json()["prediction_id"]
        assert prediction_id is not None

        # Step 2: Retrieve the prediction by ID
        response = client.get(f"/api/v1/xgboost/predictions/{prediction_id}")
        assert response.status_code == 200
        assert response.json()["prediction_id"] == prediction_id
        assert response.json()["patient_id"] == "patient-123"
        assert response.json()["risk_level"] == "moderate"

        # Step 3: Validate the prediction
        validation_request = {
            "status": "validated",
            "validator_notes": "Clinically confirmed after review",
        }

        response = client.post(
            f"/api/v1/xgboost/predictions/{prediction_id}/validate",
            json=validation_request
        )
        assert response.status_code == 200
        assert response.json()["status"] == "validated"
        assert response.json()["success"] is True

        # Step 4: Generate explanation for the prediction
        response = client.get(
            f"/api/v1/xgboost/predictions/{prediction_id}/explanation?detail_level=detailed"
        )
        assert response.status_code == 200
        assert response.json()["prediction_id"] == prediction_id
        assert "important_features" in response.json()

        # Step 5: Update digital twin with the prediction
        update_request = {
            "patient_id": "patient-123",
            "prediction_ids": [prediction_id]
        }

        response = client.post(
            "/api/v1/xgboost/digital-twin/update",
            json=update_request
        )
        assert response.status_code == 200
        assert response.json()["digital_twin_updated"] is True
        assert response.json()["prediction_count"] == 1

    def test_treatment_comparison_flow(self, client: TestClient, mock_service):
        """Test the treatment comparison workflow."""
        # Step 1: Compare multiple treatment options
        comparison_request = {
            "patient_id": "patient-123",
            "treatment_options": [
                {
                    "category": "medication_ssri",
                    "details": {"medication": "escitalopram", "dosage": 10},
                },
                {
                    "category": "therapy_cbt",
                    "details": {"frequency": "weekly", "duration_weeks": 12},
                },
                {
                    "category": "medication_snri",
                    "details": {"medication": "venlafaxine", "dosage": 75},
                },
            ],
            "features": {
                "age": 45,
                "phq9_score": 15,
                "diagnosis": "major_depressive_disorder",
            },
        }

        response = client.post(
            "/api/v1/xgboost/compare/treatments", json=comparison_request
        )
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-123"
        assert response.json()["treatments_compared"] == 3
        assert len(response.json()["results"]) == 3
        assert "recommendation" in response.json()

    def test_model_info_flow(self, client: TestClient, mock_service):
        """Test the model information workflow."""
        # Step 1: Get available models
        response = client.get("/api/v1/xgboost/models")

        assert response.status_code == 200
        assert response.json()["count"] > 0
        assert len(response.json()["models"]) > 0

        # Save model ID for next step
        model_id = response.json()["models"][0]["model_id"]

        # Step 2: Get detailed model info
        response = client.get(f"/api/v1/xgboost/models/{model_id}")

        assert response.status_code == 200
        assert response.json()["model_id"] == model_id

        # Step 3: Get feature importance
        response = client.get(f"/api/v1/xgboost/models/{model_id}/features")

        assert response.status_code == 200
        assert response.json()["model_id"] == model_id
        assert "features" in response.json()

    def test_healthcheck(self, client: TestClient, mock_service):
        """Test the healthcheck endpoint."""
        response = client.get("/api/v1/xgboost/healthcheck")

        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in response.json()
