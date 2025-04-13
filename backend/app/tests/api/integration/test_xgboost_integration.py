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
from unittest.mock import patch

# Router import remains the same
from app.api.routes.xgboost import router
from app.core.services.ml.xgboost import (
    get_xgboost_service,
    MockXGBoostService,
    PredictionType,
    TreatmentCategory,
    RiskLevel,
)

# Remove module-level app/client creation
# app = FastAPI()
# app.include_router(router)
# client = TestClient(app)


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
            "id": "clinician-123", "name": "Dr. Smith"}
        mock_get_user.return_value = {"id": "user-123", "name": "Test User"}

        yield

        @pytest.fixture(autouse=True)
        def mock_service():

                    """Set up a real MockXGBoostService for integration testing."""
    # Import necessary modules
    from unittest.mock import MagicMock
    from datetime import datetime

    # Create a real mock service (not a MagicMock,
    mock_service= MockXGBoostService()

    # Configure the mock service
    mock_service.initialize(
        {
            "log_level": "INFO",
            "mock_delay_ms": 0,  # No delay for tests
            "risk_level_distribution": {
                "very_low": 5,
                "low": 20,
                "moderate": 50,  # Higher probability for moderate
                "high": 20,
                "very_high": 5,
            },
        }
    )

    # Mock the required methods
    # Override predict_risk to return a consistent result
    mock_service.predict_risk = MagicMock(
        return_value={
            "prediction_id": "pred-123",
            "patient_id": "patient-123",
            "risk_type": "relapse",
            "risk_level": "moderate",
            "risk_score": 0.65,
            "confidence": 0.8,
            "time_frame_days": 90,
            "timestamp": datetime.now().isoformat(),
        }
    )

    # Mock get_prediction to return a prediction by ID
    mock_service.get_prediction = MagicMock(
        return_value={
            "prediction_id": "pred-123",
            "patient_id": "patient-123",
            "risk_type": "relapse",
            "risk_level": "moderate",
            "risk_score": 0.65,
            "confidence": 0.8,
            "time_frame_days": 90,
            "timestamp": datetime.now().isoformat(),
            "risk_factors": {
                "contributing_factors": [
                    {"name": "high phq9_score", "weight": "high"},
                    {"name": "previous hospitalizations", "weight": "medium"},
                ],
                "protective_factors": [
                    {"name": "stable living situation", "weight": "medium"}
                ],
            },
            "supporting_evidence": [
                "Patient has shown symptoms of relapse in the past 30 days",
                "PHQ-9 score has increased by 5 points in the last assessment",
            ],
        }
    )

    # Mock validate_prediction
    mock_service.validate_prediction = MagicMock(
        return_value={
            "prediction_id": "pred-123",
            "status": "validated",
            "success": True,
        }
    )

    # Mock get_prediction_explanation
    mock_service.get_prediction_explanation = MagicMock(
        return_value={
            "prediction_id": "pred-123",
            "important_features": [
                {"name": "phq9_score", "importance": 0.45},
                {"name": "age", "importance": 0.30},
                {"name": "previous_hospitalizations", "importance": 0.25},
            ],
        }
    )

    # Mock integrate_with_digital_twin
    mock_service.integrate_with_digital_twin = MagicMock(
        return_value={
            "profile_id": "profile-123",
            "patient_id": "patient-123",
            "prediction_id": "pred-123",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }
    )

    # Mock predict_treatment_response
    mock_service.predict_treatment_response = MagicMock(
        return_value={
            "prediction_id": "pred-456",
            "patient_id": "patient-123",
            "treatment_type": "medication_ssri",
            "response_likelihood": "good",
            "efficacy_score": 0.75,
            "confidence": 0.8,
            "treatments_compared": 3,
            "prediction_horizon": "8_weeks",
            "results": [
                {"treatment": "medication_ssri", "score": 0.75},
                {"treatment": "therapy_cbt", "score": 0.65},
                {"treatment": "medication_snri", "score": 0.60},
            ],
            "recommendation": "medication_ssri is recommended as first-line treatment",
            "treatment_details": {"medication": "escitalopram", "dose_mg": 10},
            # Fix the side effect format to match the expected schema
            "side_effect_risk": {
                "common": [
                    {"name": "nausea", "severity": "mild", "likelihood": "common"},
                    {"name": "headache", "severity": "mild", "likelihood": "common"},
                    {
                        "name": "insomnia",
                        "severity": "moderate",
                        "likelihood": "common",
                    },
                ],
                "rare": [
                    {
                        "name": "serotonin syndrome",
                        "severity": "severe",
                        "likelihood": "rare",
                    }
                ],
            },
            "expected_outcome": {
                "symptom_improvement": "Moderate improvement expected",
                "time_to_response": "4-6 weeks",
                "sustained_response_likelihood": "moderate",
                "functional_improvement": "Some improvement in daily functioning expected",
            },
        }
    )

    # Mock get_models
    mock_service.get_models = MagicMock(
        return_value={
            "count": 3,
            "models": [
                {"model_id": "model-123", "type": "relapse-risk", "version": "1.0.0"},
                {"model_id": "model-456", "type": "suicide-risk", "version": "1.0.0"},
                {
                    "model_id": "model-789",
                    "type": "hospitalization-risk",
                    "version": "1.0.0",
                },
            ],
        }
    )

    # Mock get_model_info
    mock_service.get_model_info = MagicMock(
        return_value={
            "model_id": "model-123",
            "type": "relapse-risk",
            "version": "1.0.0",
            "description": "Relapse risk prediction model",
        }
    )

    # Mock get_model_features
    mock_service.get_model_features = MagicMock(
        return_value={
            "model_id": "model-123",
            "features": [
                {"name": "phq9_score", "importance": 0.45},
                {"name": "age", "importance": 0.30},
                {"name": "previous_hospitalizations", "importance": 0.25},
            ],
        }
    )

    # Mock healthcheck
    mock_service.healthcheck = MagicMock(
        return_value={
            "status": "healthy",
            "components": [
                {"name": "risk_models", "status": "healthy"},
                {"name": "treatment_models", "status": "healthy"},
                {"name": "outcome_models", "status": "healthy"},
            ],
        }
    )

    # Create a MagicMock for the _get_xgboost_service function
    from unittest.mock import MagicMock

    # Create a function that returns our mock service
    async def mock_get_service_factory():
             return mock_service

        # Create a MagicMock for the _get_xgboost_service function
        mock_get_service = MagicMock()
        mock_get_service.return_value = mock_get_service_factory

        # Patch the _get_xgboost_service function in the router
        with patch("app.api.routes.xgboost._get_xgboost_service", mock_get_service):
        yield mock_service

        @pytest.mark.db_required()class TestXGBoostIntegration:
    """Integration tests for the XGBoost API."""

    @pytest.mark.asyncio()
    async def test_risk_prediction_flow(
            self, client: TestClient, mock_service):
        """Test the complete risk prediction workflow."""
        # 1. Request risk prediction
        risk_request = {
            "patient_id": "patient-123",
            "profile_id": "profile-456",  # Assume a profile exists
            "features": {"age": 55, "bmi": 28.5, "genetic_marker_x": 0.8},
        }
        response = client.post(
            "/api/v1/ml/xgboost/risk-prediction",
            json=risk_request)
        assert response.status_code == 200
        assert "prediction_id" in response.json(,
        prediction_id= response.json()["prediction_id"]

        # 2. Retrieve the prediction
        response = client.get(
            f"/api/v1/ml/xgboost/predictions/{prediction_id}")
        assert response.status_code == 200
        prediction_data = response.json()
        assert prediction_data["prediction_id"] == prediction_id
        assert prediction_data["status"] == "pending_validation"
        assert prediction_data["risk_level"] in list(RiskLevel)

        # 3. Validate the prediction
        validation_request = {
            "status": "validated",
            "validator_notes": "Clinically confirmed after review",
        }
        response = client.post(
            f"/api/v1/ml/xgboost/predictions/{prediction_id}/validate",
            json=validation_request,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "validated"

        # 4. Get explanation for the prediction
        response = client.get(
            f"/api/v1/ml/xgboost/predictions/{prediction_id}/explanation?detail_level=detailed")
        assert response.status_code == 200
        explanation_data = response.json()
        assert "feature_importance" in explanation_data
        assert explanation_data["prediction_id"] == prediction_id

        # 5. Integrate with Digital Twin (using the same prediction ID,
        update_request= {
            "patient_id": "patient-123",
            "profile_id": "profile-456",  # Ensure profile ID matches
            "prediction_id": prediction_id,  # Use the ID from the prediction made
        }
        response = client.post(
            "/api/v1/ml/xgboost/digital-twin/integrate", json=update_request
        )
        assert response.status_code == 200
        assert response.json()[
            "message"] == "Prediction integrated successfully."
        assert response.json()["prediction_id"] == prediction_id

    @pytest.mark.asyncio()
    async def test_treatment_comparison_flow(
            self, client: TestClient, mock_service):
        """Test the treatment comparison workflow."""
        # 1. Request treatment comparison
        comparison_request = {
            "patient_id": "patient-789",
            "profile_id": "profile-abc",
            "features": {"age": 40, "prior_treatment_failures": 2, "severity_score": 7},
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

    @pytest.mark.asyncio()
    async def test_model_info_flow(self, client: TestClient, mock_service):
                 """Test the model information workflow."""
        # This test assumes a model has been loaded or is mockable
        # We'll use a placeholder model ID, assuming the mock service handles
        # it
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
        assert (
            len(features_data["features"]) > 0
        )  # Assuming mock provides some features

        @pytest.mark.asyncio()
        async def test_healthcheck(self, client: TestClient, mock_service):
                 """Test the healthcheck endpoint."""
        response = client.get("/api/v1/ml/xgboost/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
