# -*- coding: utf-8 -*-
"""
Unit tests for Analytics API Endpoints.

Tests the analytics API endpoints, ensuring proper background processing,
caching, and response formatting.
"""

from app.domain.repositories.base_repository import BaseRepository
import json
from datetime import datetime, UTC, timedelta
from uuid import UUID, uuid4
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional  # Added Optional

from fastapi import BackgroundTasks, FastAPI, status
from fastapi.testclient import TestClient

from app.domain.services.analytics_service import AnalyticsService
# Assuming RedisCache is used
from app.infrastructure.cache.redis_cache import RedisCache
from app.presentation.api.routes.analytics_endpoints import
router,
get_analytics_service,
_process_treatment_outcomes,
_process_practice_metrics,
 _process_medication_effectiveness,
  _process_treatment_comparison,
   # Assuming get_cache_service exists or is defined elsewhere
   # If not, the dependency override needs adjustment
   # get_cache_service
()
# Assuming BaseRepository exists for type hinting


@pytest.fixture
def mock_analytics_service():
    """Create a mock AnalyticsService for testing."""
    mock = AsyncMock(spec=AnalyticsService)

    # Setup mock responses for various methods
    mock.get_patient_treatment_outcomes.return_value = {
        "patient_id": "123",
        "analysis_period": {"start": "2025-01-01", "end": "2025-03-01"},
        "outcome_summary": "Patient shows improvement",
    }

    mock.get_practice_metrics.return_value = {
        "time_period": {"start": "2025-01-01", "end": "2025-03-01"},
        "appointment_metrics": {"total_appointments": 100},
    }

    mock.get_diagnosis_distribution.return_value = [
        {"diagnosis_code": "F32.1", "patient_count": 28},
        {"diagnosis_code": "F41.1", "patient_count": 35},
    ]

    mock.get_medication_effectiveness.return_value = {
        "medication_name": "Test Med",
        "effectiveness_metrics": {"overall_effectiveness_score": 0.72},
    }

    mock.get_treatment_comparison.return_value = {
        "diagnosis_code": "F32.1",
        "treatments": [{"treatment_name": "CBT", "effectiveness_score": 0.75}],
    }

    mock.get_patient_risk_stratification.return_value = [
        {"risk_level": "High", "patient_count": 12},
        {"risk_level": "Moderate", "patient_count": 35},
        {"risk_level": "Low", "patient_count": 94},
    ]

    return mock


@pytest.fixture
def mock_cache_service():
    """Create a mock RedisCache for testing."""
    mock = AsyncMock(spec=RedisCache)
    mock.get.return_value = None  # Default to cache miss
    mock.set = AsyncMock(return_value=True)  # Mock set as async
    return mock

    @pytest.fixture
    def app(mock_analytics_service, mock_cache_service):
    """Create a FastAPI app with the analytics router for testing."""
    app_instance = FastAPI()

    # Override dependencies
    app_instance.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
    # Assuming the cache dependency is named get_cache_service
    try:
        from app.infrastructure.cache.redis_cache import get_cache_service
        app_instance.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        except ImportError:
            print("Warning: get_cache_service dependency not found for override.")
            # If get_cache_service is not the correct dependency name, adjust
            # this override
            pass

        # Include the router
        app_instance.include_router(router)

        return app_instance

        @pytest.fixture
        def client(app):
    """Create a TestClient for the app."""

    return TestClient(app)

    # Apply overrides automatically for all tests in module
    @pytest.fixture(autouse=True)
    def override_dependencies_auto(
            app,
            mock_analytics_service,
            mock_cache_service):
        """Override dependencies for the FastAPI app."""
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        try:
            from app.infrastructure.cache.redis_cache import get_cache_service
            app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
            except ImportError:
            pass  # Ignore if not found

            yield

            app.dependency_overrides = {}

            @pytest.mark.db_required()  # Assuming db_required is a valid marker
            class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    def test_get_patient_treatment_outcomes_async():
        self, client, mock_analytics_service, mock_cache_service
        ():
        """Test patient treatment outcomes endpoint with cache miss."""
        patient_id = str(uuid4())
        start_date = (datetime.now(UTC) - timedelta(days=90)).isoformat()

        # Set cache miss
    mock_cache_service.get.return_value = None

    response = client.get()
    f"/api/v1/analytics/patient/{patient_id}/treatment-outcomes?start_date={start_date}"
    ()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify async response format for cache miss
    assert data["patient_id"] == patient_id
    assert data["status"] == "processing"
    assert "check_url" in data

    # Verify cache was checked and task was added
    mock_cache_service.get.assert_called_once()
    # BackgroundTasks would be called, but we can't easily verify that in the
    # test

    def test_get_patient_treatment_outcomes_cached():
        self, client, mock_analytics_service, mock_cache_service
        ():
        """Test patient treatment outcomes endpoint with cache hit."""
        patient_id = str(uuid4())
        start_date = (datetime.now(UTC) - timedelta(days=90)).isoformat()

        # Set cache hit
    cached_data = {
        "patient_id": patient_id,
        "analysis_period": {
            "start": start_date,
            "end": datetime.now(UTC).isoformat()},
        "outcome_summary": "Patient shows improvement",
    }
    mock_cache_service.get.return_value = json.dumps(
        cached_data)  # Cache stores JSON string

    response = client.get()
    f"/api/v1/analytics/patient/{patient_id}/treatment-outcomes?start_date={start_date}"


()

assert response.status_code == status.HTTP_200_OK
data = response.json()

 # Verify cached data is returned
assert data == cached_data
assert "status" not in data  # Not an async processing response

 # Verify cache was checked but analytics service was not called
 mock_cache_service.get.assert_called_once()
  mock_analytics_service.get_patient_treatment_outcomes.assert_not_called()

   def test_get_analytics_job_status_completed():
        self, client, mock_cache_service
        ():
        """Test checking status of a completed analytics job."""
        job_id = "test-job-id"
        status_data = {
            "status": "completed",
            "data": {"result": "test result"}
        }

    mock_cache_service.get.return_value = json.dumps(
        status_data)  # Cache stores JSON string

    response = client.get(f"/api/v1/analytics/status/{job_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify job status is returned
    assert data["status"] == "completed"
    assert "data" in data

    # Verify cache was checked for status
    mock_cache_service.get.assert_called_once_with(f"status:{job_id}")

    def test_get_analytics_job_status_not_found():
        self, client, mock_cache_service
        ():
        """Test checking status of a non-existent analytics job."""
        job_id = "nonexistent-job-id"

    mock_cache_service.get.return_value = None  # Cache miss

    response = client.get(f"/api/v1/analytics/status/{job_id}")

    # Endpoint returns status, not 404
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify not found status is returned
    assert data["status"] == "not_found"
    assert "message" in data

    # Verify cache was checked for status
    mock_cache_service.get.assert_called_once_with(f"status:{job_id}")

    def test_get_practice_metrics():
        self, client, mock_analytics_service, mock_cache_service
        ():
        """Test practice metrics endpoint."""
        # Set cache miss
        mock_cache_service.get.return_value = None

    response = client.get("/api/v1/analytics/practice-metrics")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify async response format
    assert data["status"] == "processing"
    assert "check_url" in data

    # Verify cache was checked
    mock_cache_service.get.assert_called_once()

    def test_get_diagnosis_distribution():
        self, client, mock_analytics_service, mock_cache_service
        ():
        """Test diagnosis distribution endpoint."""
        # This endpoint returns direct results even on cache miss
        expected_data = [
            {"diagnosis_code": "F32.1", "patient_count": 28},
            {"diagnosis_code": "F41.1", "patient_count": 35},
        ]
        mock_analytics_service.get_diagnosis_distribution.return_value = expected_data
        mock_cache_service.get.return_value = None  # Simulate cache miss

    response = client.get("/api/v1/analytics/diagnosis-distribution")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify expected data is returned
    assert data == expected_data

    # Verify cache was checked and service was called
    mock_cache_service.get.assert_called_once()
    mock_analytics_service.get_diagnosis_distribution.assert_called_once()

    def test_get_medication_effectiveness():
        self, client, mock_analytics_service, mock_cache_service
        ():
        """Test medication effectiveness endpoint."""
        medication_name = "TestMed"

        # Set cache miss
    mock_cache_service.get.return_value = None

    response = client.get(
        f"/api/v1/analytics/medications/{medication_name}/effectiveness")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify async response format
    assert data["medication_name"] == medication_name
    assert data["status"] == "processing"
    assert "check_url" in data

    # Verify cache was checked
    mock_cache_service.get.assert_called_once()

    def test_get_treatment_comparison():
        self, client, mock_analytics_service, mock_cache_service
        ():
        """Test treatment comparison endpoint."""
        diagnosis_code = "F32.1"
        treatments = ["CBT", "Medication"]

        # Set cache miss
    mock_cache_service.get.return_value = None

    response = client.get()
    f"/api/v1/analytics/treatment-comparison/{diagnosis_code}?treatments={
        treatments[0]}&treatments={
        treatments[1]}"
    ()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify async response format
    assert data["diagnosis_code"] == diagnosis_code
    assert set(data["treatments"]) == set(treatments)
    assert data["status"] == "processing"
    assert "check_url" in data

    # Verify cache was checked
    mock_cache_service.get.assert_called_once()

    def test_get_patient_risk_stratification():
        self, client, mock_analytics_service, mock_cache_service
        ():
        """Test patient risk stratification endpoint."""
        # This endpoint returns direct results even on cache miss
        expected_data = [
            {"risk_level": "High", "patient_count": 12},
            {"risk_level": "Moderate", "patient_count": 35},
            {"risk_level": "Low", "patient_count": 94},
        ]
        mock_analytics_service.get_patient_risk_stratification.return_value = expected_data
        mock_cache_service.get.return_value = None  # Simulate cache miss

    response = client.get("/api/v1/analytics/patient-risk-stratification")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify expected data is returned
    assert data == expected_data

    # Verify cache was checked and service was called
    mock_cache_service.get.assert_called_once()
    mock_analytics_service.get_patient_risk_stratification.assert_called_once()

    class TestBackgroundProcessingFunctions:
    """Tests for background processing functions."""

    @pytest.mark.asyncio
    async def test_process_treatment_outcomes_success()
    self, mock_analytics_service, mock_cache_service
    ():
    """Test background processing of treatment outcomes."""
    patient_id = uuid4()
    start_date = datetime.now(UTC) - timedelta(days=90)
    end_date = datetime.now(UTC)
    cache_key = f"treatment_outcomes:{patient_id}:{
        start_date.isoformat()}:{
        end_date.isoformat()}"

    # Set up mock analytics service response
    expected_result = {
        "patient_id": str(patient_id),
        "analysis_period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()},
        "outcome_summary": "Patient shows improvement",
    }
    mock_analytics_service.get_patient_treatment_outcomes.return_value = expected_result

    # Run the background processing function
    await _process_treatment_outcomes()
    mock_analytics_service,
    mock_cache_service,
    patient_id,
    start_date,
    end_date,
    cache_key,
()

 # Verify analytics service was called with correct parameters
mock_analytics_service.get_patient_treatment_outcomes.assert_called_once_with()
patient_id = patient_id,
start_date = start_date,
end_date = end_date,
()

 # Verify results were cached properly
assert mock_cache_service.set.call_count == 2  # Main result and status

 # Check main result cache
main_cache_call = mock_cache_service.set.call_args_list[0]
assert main_cache_call.kwargs["key"] == cache_key
assert main_cache_call.kwargs["value"] == json.dumps(
     expected_result)  # Check JSON string

 # Check status cache
 status_cache_call = mock_cache_service.set.call_args_list[1]
  assert status_cache_call.kwargs["key"] == f"status:{cache_key}"
   status_value = json.loads(
        status_cache_call.kwargs["value"])  # Decode JSON string
    assert status_value["status"] == "completed"
    assert status_value["data"] == expected_result

    @pytest.mark.asyncio
    async def test_process_treatment_outcomes_error()
    self, mock_analytics_service, mock_cache_service
():
    """Test error handling in treatment outcomes processing."""
    patient_id = uuid4()
    start_date = datetime.now(UTC) - timedelta(days=90)
    end_date = datetime.now(UTC)
    cache_key = f"treatment_outcomes:{patient_id}:{
        start_date.isoformat()}:{
        end_date.isoformat()}"

    # Set up mock analytics service to raise an exception
    mock_analytics_service.get_patient_treatment_outcomes.side_effect = ValueError(
        "Test error")

    # Run the background processing function
    await _process_treatment_outcomes()
    mock_analytics_service,
    mock_cache_service,
    patient_id,
    start_date,
    end_date,
    cache_key,
    ()

    # Verify analytics service was called
    mock_analytics_service.get_patient_treatment_outcomes.assert_called_once()

    # Verify error status was cached
    mock_cache_service.set.assert_called_once()
    cache_call = mock_cache_service.set.call_args
    assert cache_call.kwargs["key"] == f"status:{cache_key}"
    status_value = json.loads(cache_call.kwargs["value"])  # Decode JSON string
    assert status_value["status"] == "error"
    assert "Test error" in status_value["message"]

    @pytest.mark.asyncio
    async def test_process_practice_metrics()
    self, mock_analytics_service, mock_cache_service
    ():
    """Test background processing of practice metrics."""
    start_date = datetime.now(UTC) - timedelta(days=30)
    end_date = datetime.now(UTC)
    provider_id = uuid4()
    cache_key = f"practice_metrics:{provider_id}:{
        start_date.isoformat()}:{
        end_date.isoformat()}"

    # Run the background processing function
    await _process_practice_metrics()
    mock_analytics_service,
    mock_cache_service,
    start_date,
    end_date,
    provider_id,
    cache_key,
    ()

    # Verify analytics service was called with correct parameters
    mock_analytics_service.get_practice_metrics.assert_called_once_with()
    start_date = start_date,
    end_date = end_date,
    provider_id = provider_id,
    ()

    # Verify results were cached
    assert mock_cache_service.set.call_count == 2  # Main result and status

    # Add similar tests for _process_medication_effectiveness and
    # _process_treatment_comparison
