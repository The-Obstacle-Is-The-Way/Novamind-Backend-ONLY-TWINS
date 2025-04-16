"""
Integration tests for the XGBoost service API endpoints.

These tests verify the asynchronous interaction between the API routes
defined in xgboost.py and the mocked XGBoostInterface.
"""

import pytest
import uuid
from httpx import AsyncClient # Use AsyncClient for async tests
from unittest.mock import AsyncMock # Use AsyncMock for async service
from fastapi import FastAPI, status

# Import the interface and service provider
from app.core.services.ml.xgboost.interface import XGBoostInterface, ModelType
from app.infrastructure.di.container import get_service

# Import Schemas (assuming structure from previous context)
from app.presentation.api.schemas.xgboost import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    TreatmentResponseRequest,
    TreatmentResponseResponse,
    OutcomePredictionRequest,
    OutcomePredictionResponse,
    # ModelInfoRequest, # GET request doesn't use a request body schema
    ModelInfoResponse,
    # FeatureImportanceRequest, # GET request doesn't use a request body schema
    FeatureImportanceResponse,
)
# Import Exceptions (assuming structure from previous context)
from app.core.services.ml.xgboost.exceptions import (
    XGBoostServiceError,
    ValidationError,
    ModelNotFoundError,
    PredictionError,
    ResourceNotFoundError
)

# Import the actual router we are testing
from app.presentation.api.v1.endpoints.xgboost import router as xgboost_router

# --- Async Test Fixtures ---

@pytest.fixture
def mock_xgboost_service():
    """Fixture for an AsyncMock XGBoost service interface."""
    mock_service = AsyncMock(spec=XGBoostInterface)
    # Configure mock return values for the async methods
    mock_service.predict_risk.return_value = {"prediction_id": "risk-pred-123", "risk_score": 0.75, "confidence": 0.9, "risk_level": "high"}
    mock_service.predict_treatment_response.return_value = {"prediction_id": "treat-pred-456", "response_probability": 0.8, "confidence": 0.85}
    mock_service.predict_outcome.return_value = {"prediction_id": "outcome-pred-789", "outcome_prediction": "stable", "confidence": 0.92}
    mock_service.get_model_info.return_value = {"model_type": ModelType.RISK_RELAPSE.value, "version": "1.0", "description": "Mock Relapse Model", "features": ["feat1", "feat2"]}
    mock_service.get_feature_importance.return_value = {"prediction_id": "pred123", "feature_importance": {"feat1": 0.6, "feat2": 0.4}}
    # Mock availability check if needed
    mock_service.get_available_models.return_value = [{"model_type": ModelType.RISK_RELAPSE.value, "version": "1.0"}]
    return mock_service

@pytest.fixture(scope="function")
def test_app(mock_xgboost_service):
    """Creates a FastAPI test app instance with the mock XGBoost service dependency overridden."""
    app = FastAPI(title="Test Async XGBoost API")

    # Apply the dependency override for the asynchronous XGBoostInterface
    app.dependency_overrides[get_service(XGBoostInterface)] = lambda: mock_xgboost_service

    # Include the actual XGBoost router with the correct prefix
    app.include_router(xgboost_router, prefix="/api/v1/xgboost")

    # TODO: Add mock authentication override if needed for verify_provider_access
    # from app.presentation.api.dependencies.auth import verify_provider_access
    # async def mock_verify_provider_access(): return None # Simple mock
    # app.dependency_overrides[verify_provider_access] = mock_verify_provider_access

    return app

@pytest.fixture
async def client(test_app):
    """Create an httpx AsyncClient instance for testing the async app."""
    async with AsyncClient(app=test_app, base_url="http://test") as async_client:
        yield async_client

# --- Async Integration Tests ---

@pytest.mark.asyncio
async def test_predict_risk_success(client: AsyncClient, mock_xgboost_service: AsyncMock):
    """Test successful risk prediction via the async endpoint."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        "risk_type": ModelType.RISK_RELAPSE.value, # Use valid enum value
        "clinical_data": {"feature1": 10, "feature2": 20.5},
        "time_frame_days": 90
    }
    expected_response_data = mock_xgboost_service.predict_risk.return_value

    response = await client.post("/api/v1/xgboost/predict/risk", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response_data
    mock_xgboost_service.predict_risk.assert_awaited_once_with(
        patient_id=str(patient_id),
        risk_type=ModelType.RISK_RELAPSE.value,
        clinical_data=request_data["clinical_data"],
        time_frame_days=request_data["time_frame_days"]
    )

@pytest.mark.asyncio
async def test_predict_treatment_response_success(client: AsyncClient, mock_xgboost_service: AsyncMock):
    """Test successful treatment response prediction via the async endpoint."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        "treatment_type": ModelType.TREATMENT_MEDICATION_SSRI.value,
        "treatment_details": {"medication": "sertraline", "dosage_mg": 100},
        "clinical_data": {"gad7": 12, "phq9": 14}
    }
    expected_response_data = mock_xgboost_service.predict_treatment_response.return_value

    response = await client.post("/api/v1/xgboost/predict/treatment-response", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response_data
    mock_xgboost_service.predict_treatment_response.assert_awaited_once_with(
        patient_id=str(patient_id),
        treatment_type=ModelType.TREATMENT_MEDICATION_SSRI.value,
        treatment_details=request_data["treatment_details"],
        clinical_data=request_data["clinical_data"]
    )

@pytest.mark.asyncio
async def test_predict_outcome_success(client: AsyncClient, mock_xgboost_service: AsyncMock):
    """Test successful outcome prediction via the async endpoint."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        "outcome_timeframe": {"weeks": 12},
        "clinical_data": {"baseline_severity": "moderate", "comorbidities": ["anxiety"]},
        "treatment_plan": {"therapy": "CBT", "medication": "none"}
    }
    expected_response_data = mock_xgboost_service.predict_outcome.return_value

    response = await client.post("/api/v1/xgboost/predict/outcome", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response_data
    mock_xgboost_service.predict_outcome.assert_awaited_once_with(
        patient_id=str(patient_id),
        outcome_timeframe=request_data["outcome_timeframe"],
        clinical_data=request_data["clinical_data"],
        treatment_plan=request_data["treatment_plan"]
    )

@pytest.mark.asyncio
async def test_get_model_info_success(client: AsyncClient, mock_xgboost_service: AsyncMock):
    """Test successful retrieval of model info via the async endpoint."""
    model_type = ModelType.RISK_RELAPSE.value
    expected_response_data = mock_xgboost_service.get_model_info.return_value

    response = await client.get(f"/api/v1/xgboost/models/{model_type}/info")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response_data
    mock_xgboost_service.get_model_info.assert_awaited_once_with(model_type=model_type)

@pytest.mark.asyncio
async def test_get_feature_importance_success(client: AsyncClient, mock_xgboost_service: AsyncMock):
    """Test successful retrieval of feature importance via the async endpoint."""
    prediction_id = "pred123"
    patient_id = uuid.uuid4()
    model_type = ModelType.RISK_RELAPSE.value
    expected_response_data = mock_xgboost_service.get_feature_importance.return_value

    response = await client.get(
        f"/api/v1/xgboost/predictions/{prediction_id}/feature-importance",
        params={"patient_id": str(patient_id), "model_type": model_type}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response_data
    mock_xgboost_service.get_feature_importance.assert_awaited_once_with(
        patient_id=str(patient_id),
        model_type=model_type,
        prediction_id=prediction_id
    )

# --- Error Handling Tests (Example) ---

@pytest.mark.asyncio
async def test_predict_risk_validation_error(client: AsyncClient, mock_xgboost_service: AsyncMock):
    """Test validation error during risk prediction."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        # Missing risk_type
        "clinical_data": {"feature1": 10},
        "time_frame_days": 90
    }
    # Mock service to raise ValidationError (adjust if needed based on actual exception raised)
    # mock_xgboost_service.predict_risk.side_effect = ValidationError("Missing required field: risk_type")

    response = await client.post("/api/v1/xgboost/predict/risk", json=request_data)

    # FastAPI/Pydantic handles request validation before the service call
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # assert "risk_type" in response.json()["detail"][0]["loc"] # Check specific error field
    # mock_xgboost_service.predict_risk.assert_not_awaited() # Service method shouldn't be called

@pytest.mark.asyncio
async def test_get_model_info_not_found(client: AsyncClient, mock_xgboost_service: AsyncMock):
    """Test model not found error when retrieving model info."""
    model_type = "non-existent-model"
    mock_xgboost_service.get_model_info.side_effect = ModelNotFoundError(f"Model '{model_type}' not found.")

    response = await client.get(f"/api/v1/xgboost/models/{model_type}/info")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert model_type in response.json()["detail"]
    mock_xgboost_service.get_model_info.assert_awaited_once_with(model_type=model_type)

# --- Commented out original synchronous tests and fixtures ---
# import json
# from datetime import datetime, timedelta
# from fastapi.testclient import TestClient
# from unittest.mock import patch, MagicMock

# from app.core.services.ml.xgboost import (
#     get_xgboost_service,
#     MockXGBoostService,
#     PredictionType,
#     TreatmentCategory,
#     RiskLevel,
# )

# # Override dependencies for testing
# # @pytest.fixture
# # def mock_xgboost_service():
# #     """Fixture for a mock XGBoost service."""
# #     # Changed to AsyncMock
# #     mock_service = AsyncMock(spec=XGBoostInterface)
# #     mock_service.predict_risk.return_value = {"risk_score": 0.75, "confidence": 0.9}
# #     mock_service.predict_treatment_response.return_value = {"response_probability": 0.8, "confidence": 0.85}
# #     mock_service.predict_outcome.return_value = {"outcome_prediction": "stable", "confidence": 0.92}
# #     mock_service.get_model_info.return_value = {"model_type": "test", "version": "1.0", "description": "Mock Model", "features": ["feat1", "feat2"]}
# #     mock_service.get_feature_importance.return_value = {"prediction_id": "pred123", "feature_importance": {"feat1": 0.6, "feat2": 0.4}}
# #     return mock_service

# # @pytest.fixture(scope="function") # Function scope if test isolation is needed
# # def test_app(mock_xgboost_service):
# #     """Creates a FastAPI test app instance with the mock XGBoost service."""
# #     app = FastAPI(title="Test XGBoost API")
# #
# #     # Apply the dependency override for the XGBoostInterface
# #     app.dependency_overrides[get_service(XGBoostInterface)] = lambda: mock_xgboost_service
# #
# #     # Include the actual XGBoost router
# #     app.include_router(xgboost_router, prefix="/api/v1/xgboost") # Correct prefix
# #
# #     return app

# # @pytest.fixture
# # def client(test_app):
# #     """Create a test client instance."""
# #     # Changed to use AsyncClient eventually, kept TestClient here for commenting out
# #     return TestClient(test_app)

# # @pytest.fixture(autouse=True)
# # def mock_auth_dependencies():
# #     """Mock authentication dependencies for all tests."""
# #     with patch("app.api.dependencies.auth.get_current_clinician") as mock_get_clinician, patch(
# #         "app.api.dependencies.auth.verify_patient_access"
# #     ) as mock_verify_access:
# #         # Set up mock returns
# #         mock_get_clinician.return_value = {"id": "clinician-123", "name": "Dr. Smith"}
# #         mock_verify_access.return_value = None
# #
# #         yield

# # @pytest.fixture(autouse=True)
# # def mock_service():
# #     """Set up a real MockXGBoostService for integration testing."""
# #     # Create a real mock service (not a MagicMock,)
# #     mock_service = MockXGBoostService()
# #     mock_risk_level = RiskLevel.MODERATE
# #     mock_risk_score = 0.45
# #     mock_confidence = 0.85
# #
# #     # Patch the factory function to return our configured mock service
# #     with patch("app.api.routes.xgboost.get_xgboost_service") as mock_get_service:
# #         mock_get_service.return_value = mock_service
# #         yield mock_service

# # @pytest.mark.db_required() # Assuming this marker is still relevant
# # class TestXGBoostIntegrationSync: # Renamed to avoid conflict if kept
# #     """Integration tests for the XGBoost API (Original Synchronous - Commented Out)."""
# #
# #     def test_risk_prediction_flow(self, client: TestClient, mock_service):
# #         pass # Commented out
# #
# #     def test_treatment_comparison_flow(self, client: TestClient, mock_service):
# #         pass # Commented out
# #
# #     def test_model_info_flow(self, client: TestClient, mock_service):
# #         pass # Commented out
# #
# #     def test_healthcheck(self, client: TestClient, mock_service):
# #         pass # Commented out
