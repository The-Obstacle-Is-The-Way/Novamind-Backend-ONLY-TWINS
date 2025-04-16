"""
Integration tests for the XGBoost service API.

These tests verify that the API routes and the underlying service work together correctly.
Tests use the MockXGBoostService to avoid external dependencies while ensuring
the entire API flow functions as expected.
"""

import json
import pytest

# Import FastAPI and TestClient
from fastapi import FastAPI, status, Depends
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Import the actual router
from app.presentation.api.v1.endpoints.xgboost import router as xgboost_router

# Import the service interface and mock implementation
from app.core.services.ml.xgboost.interface import XGBoostInterface, ModelType
from app.core.services.ml.xgboost.mock import MockXGBoostService # Correct path
from app.presentation.api.v1.schemas.xgboost_schemas import (
    RiskPredictionRequest, TreatmentResponseRequest
)

# --- Authentication Mocking (Keep as is or adapt to project structure) ---
# Assuming a simple bearer token check for these tests
# In a real scenario, use a more robust mock matching your auth system
async def mock_verify_provider_access():
    """Mock dependency to bypass actual auth checks."""
    return {"sub": "test-clinician", "role": "clinician"} # Example user payload

# Fixture for the mock service instance
@pytest.fixture
def mock_service() -> MockXGBoostService:
    """Provides an instance of the MockXGBoostService."""
    return MockXGBoostService()

# Refactored test client fixture
@pytest.fixture
def client(mock_service: MockXGBoostService):
    """Create a FastAPI test client with the XGBoost router and mock service."""
    app = FastAPI()

    # Override the XGBoostInterface service in DI container to return mock_service
    from app.infrastructure.di.container import get_container
    from app.core.services.ml.xgboost.interface import XGBoostInterface
    container = get_container()
    container.override(XGBoostInterface, lambda: mock_service)

    # Override authentication dependency to bypass auth checks in integration tests
    from app.presentation.api.dependencies.auth import verify_provider_access
    app.dependency_overrides[verify_provider_access] = mock_verify_provider_access

    # Include the router
    app.include_router(xgboost_router, prefix="/api/v1/xgboost")

    # Create and return the TestClient
    return TestClient(app)


@pytest.mark.integration
class TestXGBoostIntegration:
    """Integration tests for XGBoost API endpoints."""

    # Note: These tests will fail until the actual router is included in the client fixture
    # and the paths match the implemented router. <-- This is now addressed.

    @pytest.mark.asyncio
    async def test_risk_prediction_flow(self, client: TestClient, mock_service: MockXGBoostService): # Inject mock_service
        """Test the risk prediction workflow."""
        # Configure mock return value
        mock_service.predict_risk = MagicMock(return_value={
            "prediction_id": "pred_risk_123",
            "risk_score": 0.75,
            "risk_level": "high", # Use actual enum value string if defined
            "confidence": 0.9,
            "details": "Mock prediction details"
        })

        # 1. Submit a risk prediction request
        risk_request = {
            "patient_id": "patient-123",
            "risk_type": "relapse", # Ensure this matches schema enum/string
            "patient_data": {
                "age": 40,
                "prior_episodes": 2,
                "severity_score": 7,
                "medication_adherence": 0.8,
            },
            "clinical_data": {
                "age": 40,
                "prior_episodes": 2,
                "severity_score": 7,
                "medication_adherence": 0.8,
            },
            "time_frame_days": 90,
        }
        # Use the correct path including the prefix defined in client fixture
        response = client.post(
            "/api/v1/xgboost/predict/risk", json=risk_request
        )

        assert response.status_code == 200
        prediction_data = response.json()
        assert prediction_data["prediction_id"] == "pred_risk_123"
        assert prediction_data["risk_score"] == 0.75
        assert prediction_data["risk_level"] == "high"
        assert prediction_data["confidence"] == 0.9

        # Verify the mock service was called correctly
        mock_service.predict_risk.assert_called_once_with(
            patient_id="patient-123",
            risk_type="relapse",
            clinical_data=risk_request["clinical_data"],
            time_frame_days=90
        )

        # # 2. Retrieve the prediction by ID (Requires a GET endpoint in the router)
        # prediction_id = prediction_data["prediction_id"]
        # # Configure mock for GET endpoint if it exists
        # mock_service.get_prediction_details = MagicMock(return_value=prediction_data) # Example
        # response = client.get(f"/api/v1/xgboost/predictions/{prediction_id}") # Adjust path
        # assert response.status_code == 200
        # retrieved_data = response.json()
        # assert retrieved_data["prediction_id"] == prediction_id
        # assert retrieved_data["risk_score"] == prediction_data["risk_score"]

        # # 3. Get explanation for the prediction (Requires explanation endpoint)
        # # Configure mock for explanation endpoint if it exists
        # mock_service.get_feature_importance = MagicMock(return_value={
        #     "feature_importance": [{"feature": "age", "importance": 0.5}],
        #     "top_factors": ["age > 35"]
        # }) # Example
        # response = client.get(f"/api/v1/xgboost/predictions/{prediction_id}/feature-importance?patient_id=patient-123&model_type=risk-relapse") # Adjust path and params
        # assert response.status_code == 200
        # explanation_data = response.json()
        # assert "feature_importance" in explanation_data
        # assert len(explanation_data["feature_importance"]) > 0
        # assert "top_factors" in explanation_data
        # pass # Placeholder removed, assertions uncommented


    @pytest.mark.asyncio
    async def test_treatment_response_prediction(self, client: TestClient, mock_service: MockXGBoostService): # Inject mock_service
        """Test the treatment response prediction workflow."""
        # Configure mock return value
        mock_service.predict_treatment_response = MagicMock(return_value={
            "prediction_id": "pred_treat_456",
            "response_probability": 0.65,
            "expected_improvement": 0.3,
            "confidence": 0.85,
            "timeframe_weeks": 8,
            "details": "Mock treatment response prediction"
        })

        # Submit a treatment response prediction request
        treatment_request = {
            "patient_id": "patient-123",
            "treatment_type": "medication_ssri", # Ensure matches schema/enum
            "treatment_details": {
                "medication_name": "fluoxetine",
                "dosage_mg": 20
            },
            "clinical_data": {
                "age": 40,
                "prior_treatment_failures": 2,
                "severity_score": 7,
                "anxiety_comorbidity": True,
            },
            # Add any other required fields based on TreatmentResponseRequest schema
        }
        # Use the correct path
        response = client.post(
            "/api/v1/xgboost/predict/treatment-response", json=treatment_request
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["prediction_id"] == "pred_treat_456"
        assert response_data["response_probability"] == 0.65
        assert response_data["expected_improvement"] == 0.3
        assert response_data["confidence"] == 0.85
        assert response_data["timeframe_weeks"] == 8

        # Verify the mock service was called correctly
        mock_service.predict_treatment_response.assert_called_once_with(
            patient_id="patient-123",
            treatment_type="medication_ssri",
            treatment_details=treatment_request["treatment_details"],
            clinical_data=treatment_request["clinical_data"]
            # Add other expected args based on service method signature
        )
        # pass # Placeholder removed

    # --- Add tests for other endpoints (outcome, model info, etc.) ---
    # Example for model info (assuming endpoint exists in router)
    # @pytest.mark.asyncio
    # async def test_model_info_flow(self, client: TestClient, mock_service: MockXGBoostService):
    #     """Test the model information workflow."""
    #     model_type = "risk-relapse"
    #     mock_service.get_model_info = MagicMock(return_value={
    #         "model_type": model_type,
    #         "version": "1.2.0",
    #         "training_date": datetime.now().isoformat(),
    #         "performance_metrics": {"auc": 0.85}
    #     })
    #     response = client.get(f"/api/v1/xgboost/models/{model_type}/info")
    #     assert response.status_code == 200
    #     model_data = response.json()
    #     assert model_data["model_type"] == model_type
    #     assert model_data["version"] == "1.2.0"
    #     mock_service.get_model_info.assert_called_once_with(model_type=model_type)

    # --- Add healthcheck test if endpoint exists ---
    # @pytest.mark.asyncio
    # async def test_healthcheck(self, client: TestClient):
    #     """Test the healthcheck endpoint."""
    #     # Assuming healthcheck endpoint exists at /api/v1/xgboost/health
    #     response = client.get("/api/v1/xgboost/health")
    #     assert response.status_code == 200
    #     assert response.json() == {"status": "ok"} # Or match actual response
