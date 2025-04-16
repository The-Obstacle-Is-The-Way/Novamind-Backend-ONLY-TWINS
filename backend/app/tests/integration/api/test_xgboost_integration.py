"""
Integration tests for the XGBoost service API endpoints.

These tests verify the asynchronous interaction between the API routes
defined in xgboost.py and the mocked XGBoostInterface.
"""

import pytest
import uuid
# from httpx import AsyncClient # Use TestClient instead
from fastapi.testclient import TestClient # Import TestClient
from unittest.mock import AsyncMock
from fastapi import FastAPI, status
from typing import Iterator, Any

# Import the interface and service provider AND get_container
from app.core.services.ml.xgboost.interface import XGBoostInterface, ModelType
from app.infrastructure.di.container import get_service, get_container # Import get_container

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

# Import auth dependency for mocking
from app.presentation.api.dependencies.auth import verify_provider_access

# --- Test Fixtures ---

@pytest.fixture(scope="module") # Change scope to module
def mock_xgboost_service():
    """Fixture for a module-scoped AsyncMock XGBoost service interface.""" # Updated docstring
    mock_service = AsyncMock(spec=XGBoostInterface)
    # Configure mock return values
    mock_service.predict_risk.return_value = {"prediction_id": "risk-pred-123", "risk_score": 0.75, "confidence": 0.9, "risk_level": "high"}
    mock_service.predict_treatment_response.return_value = {"prediction_id": "treat-pred-456", "response_probability": 0.8, "confidence": 0.85}
    mock_service.predict_outcome.return_value = {"prediction_id": "outcome-pred-789", "outcome_prediction": "stable", "confidence": 0.92}
    mock_service.get_model_info.return_value = {"model_type": ModelType.RISK_RELAPSE.value, "version": "1.0", "description": "Mock Relapse Model", "features": ["feat1", "feat2"]}
    mock_service.get_feature_importance.return_value = {"prediction_id": "pred123", "feature_importance": {"feat1": 0.6, "feat2": 0.4}}
    mock_service.get_available_models.return_value = [{"model_type": ModelType.RISK_RELAPSE.value, "version": "1.0"}]
    # Ensure the mock has the is_initialized attribute/property expected by the interface
    mock_service.is_initialized = True
    return mock_service

@pytest.fixture(scope="module")
def test_app(mock_xgboost_service: AsyncMock) -> Iterator[FastAPI]: # Inject the actual mock service fixture
    """Fixture to create a test app with the XGBoostInterface dependency overridden."""
    from app.main import app  # Local import
    from app.core.services.ml.xgboost.interface import XGBoostInterface # Import the interface to override

    # Store original overrides if any (though unlikely for module scope)
    original_overrides = app.dependency_overrides.copy()

    # Override the XGBoostInterface dependency with the mock service
    app.dependency_overrides[XGBoostInterface] = lambda: mock_xgboost_service

    yield app # Provide the app with the override active

    # Restore original overrides after the module tests are done
    app.dependency_overrides = original_overrides

@pytest.fixture
def client(test_app):
    """Create a TestClient instance for testing."""
    # Use standard TestClient
    with TestClient(app=test_app) as test_client:
        yield test_client

# --- Async Integration Tests (using TestClient) ---

@pytest.mark.asyncio # Keep this marker for the test function itself
async def test_predict_risk_success(client: TestClient, mock_xgboost_service: AsyncMock, provider_token_headers: dict): # Inject headers
    """Test successful risk prediction via the async endpoint using TestClient."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        "risk_type": ModelType.RISK_RELAPSE.value,
        "clinical_data": {"feature1": 10, "feature2": 20.5},
        "time_frame_days": 90
    }
    expected_response_data = mock_xgboost_service.predict_risk.return_value

    # Await the headers fixture inside the async test
    auth_headers = await provider_token_headers
    # Call TestClient synchronously with awaited headers
    response = client.post("/api/v1/xgboost/predict/risk", json=request_data, headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
    assert response.json() == expected_response_data
    # Assert mock was awaited within the endpoint
    mock_xgboost_service.predict_risk.assert_awaited_once_with(
        patient_id=str(patient_id),
        risk_type=ModelType.RISK_RELAPSE.value,
        clinical_data=request_data["clinical_data"],
        time_frame_days=request_data["time_frame_days"]
    )

@pytest.mark.asyncio
async def test_predict_treatment_response_success(client: TestClient, mock_xgboost_service: AsyncMock, provider_token_headers: dict): # Inject headers
    """Test successful treatment response prediction using TestClient."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        "treatment_type": ModelType.TREATMENT_MEDICATION_SSRI.value,
        "treatment_details": {"medication": "sertraline", "dosage_mg": 100},
        "clinical_data": {"gad7": 12, "phq9": 14}
    }
    expected_response_data = mock_xgboost_service.predict_treatment_response.return_value

    # Await the headers fixture inside the async test
    auth_headers = await provider_token_headers
    # Call TestClient synchronously with awaited headers
    response = client.post("/api/v1/xgboost/predict/treatment-response", json=request_data, headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
    assert response.json() == expected_response_data
    mock_xgboost_service.predict_treatment_response.assert_awaited_once_with(
        patient_id=str(patient_id),
        treatment_type=ModelType.TREATMENT_MEDICATION_SSRI.value,
        treatment_details=request_data["treatment_details"],
        clinical_data=request_data["clinical_data"]
    )

@pytest.mark.asyncio
async def test_predict_outcome_success(client: TestClient, mock_xgboost_service: AsyncMock, provider_token_headers: dict): # Inject headers
    """Test successful outcome prediction using TestClient."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        "outcome_timeframe": {"weeks": 12},
        "clinical_data": {"baseline_severity": "moderate", "comorbidities": ["anxiety"]},
        "treatment_plan": {"therapy": "CBT", "medication": "none"}
    }
    expected_response_data = mock_xgboost_service.predict_outcome.return_value

    # Await the headers fixture inside the async test
    auth_headers = await provider_token_headers
    # Call TestClient synchronously with awaited headers
    response = client.post("/api/v1/xgboost/predict/outcome", json=request_data, headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
    assert response.json() == expected_response_data
    mock_xgboost_service.predict_outcome.assert_awaited_once_with(
        patient_id=str(patient_id),
        outcome_timeframe=request_data["outcome_timeframe"],
        clinical_data=request_data["clinical_data"],
        treatment_plan=request_data["treatment_plan"]
    )

@pytest.mark.asyncio
async def test_get_model_info_success(client: TestClient, mock_xgboost_service: AsyncMock, provider_token_headers: dict): # Inject headers
    """Test successful retrieval of model info using TestClient."""
    model_type = ModelType.RISK_RELAPSE.value
    expected_response_data = mock_xgboost_service.get_model_info.return_value

    # Await the headers fixture inside the async test
    auth_headers = await provider_token_headers
    # Call TestClient synchronously with awaited headers
    response = client.get(f"/api/v1/xgboost/models/{model_type}/info", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
    assert response.json() == expected_response_data
    mock_xgboost_service.get_model_info.assert_awaited_once_with(model_type=model_type)

@pytest.mark.asyncio
async def test_get_feature_importance_success(client: TestClient, mock_xgboost_service: AsyncMock, provider_token_headers: dict): # Inject headers
    """Test successful retrieval of feature importance using TestClient."""
    prediction_id = "pred123"
    patient_id = uuid.uuid4()
    model_type = ModelType.RISK_RELAPSE.value
    expected_response_data = mock_xgboost_service.get_feature_importance.return_value

    # Await the headers fixture inside the async test
    auth_headers = await provider_token_headers
    # Call TestClient synchronously with awaited headers
    response = client.get(
        f"/api/v1/xgboost/predictions/{prediction_id}/feature-importance",
        params={"patient_id": str(patient_id), "model_type": model_type},
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
    assert response.json() == expected_response_data
    mock_xgboost_service.get_feature_importance.assert_awaited_once_with(
        patient_id=str(patient_id),
        model_type=model_type,
        prediction_id=prediction_id
    )

# --- Error Handling Tests (Example using TestClient) ---

@pytest.mark.asyncio
async def test_predict_risk_validation_error(client: TestClient, mock_xgboost_service: AsyncMock, provider_token_headers: dict): # Inject headers
    """Test validation error during risk prediction using TestClient."""
    patient_id = uuid.uuid4()
    request_data = {
        "patient_id": str(patient_id),
        # Missing risk_type
        "clinical_data": {"feature1": 10},
        "time_frame_days": 90
    }
    # Await the headers fixture inside the async test
    auth_headers = await provider_token_headers
    # Call TestClient synchronously with awaited headers
    response = client.post("/api/v1/xgboost/predict/risk", json=request_data, headers=auth_headers)

    # FastAPI/Pydantic handles request validation before the service call
    # Authentication happens first, so we expect 401 if auth is required and missing/invalid.
    # If auth passes, *then* we'd expect 422 for validation.
    # Since this test *intends* to cause a 422 by sending bad data,
    # but auth is required, we need to ensure auth passes first.
    # The test should still assert 422 because the *purpose* is to test validation.
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, f"Response: {response.text}"
    mock_xgboost_service.predict_risk.assert_not_awaited() # Service method shouldn't be called

@pytest.mark.asyncio
async def test_get_model_info_not_found(client: TestClient, mock_xgboost_service: AsyncMock, provider_token_headers: dict): # Inject headers
    """Test model not found error when retrieving model info using TestClient."""
    model_type = "non-existent-model"
    mock_xgboost_service.get_model_info.side_effect = ModelNotFoundError(f"Model '{model_type}' not found.")

    # Await the headers fixture inside the async test
    auth_headers = await provider_token_headers
    # Call TestClient synchronously with awaited headers
    response = client.get(f"/api/v1/xgboost/models/{model_type}/info", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND, f"Response: {response.text}"
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
