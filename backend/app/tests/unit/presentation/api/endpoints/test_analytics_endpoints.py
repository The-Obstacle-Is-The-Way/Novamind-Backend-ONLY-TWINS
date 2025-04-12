# -*- coding: utf-8 -*-
"""
Unit tests for Analytics API endpoints.

This module contains unit tests for the analytics endpoints,
ensuring that they correctly handle events, validate data,
and process in a HIPAA-compliant manner.
"""

import json
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional # Added Optional

from fastapi import BackgroundTasks, FastAPI, status
from fastapi.testclient import TestClient

from app.domain.services.analytics_service import AnalyticsService
from app.infrastructure.cache.redis_cache import RedisCache # Assuming RedisCache is used
from app.presentation.api.endpoints.analytics_endpoints import (
    router,
    get_analytics_service,
    _process_treatment_outcomes,
    _process_practice_metrics,
    _process_medication_effectiveness,
    _process_treatment_comparison,
    AnalyticsEvent # Import AnalyticsEvent
    # Assuming get_cache_service exists or is defined elsewhere
    # If not, the dependency override needs adjustment
    # get_cache_service
)
# Assuming BaseRepository exists for type hinting
from app.domain.repositories.base_repository import BaseRepository


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
    mock.set = AsyncMock(return_value=True) # Mock set as async
    mock.increment = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
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
         # If get_cache_service is not the correct dependency name, adjust this override
         pass


    # Include the router
    app_instance.include_router(router)

    return app_instance


@pytest.fixture
def client(app):
    """Create a TestClient for the app."""
    
    return TestClient(app)


@pytest.fixture
def mock_background_tasks():
    """Create a mock background tasks."""
    mock = MagicMock(spec=BackgroundTasks)
    mock.add_task = MagicMock()
    return mock


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    # Assuming user object has an 'id' attribute
    user = MagicMock()
    user.id = "test-user-123" # Use string ID for consistency if needed
    user.email = "test@example.com"
    user.role = "provider" # Assuming role attribute exists
    return user


@pytest.fixture(autouse=True) # Apply overrides automatically for all tests in module
def override_dependencies_auto(app, mock_analytics_service, mock_cache_service, mock_user):
     """Override dependencies for the FastAPI app."""
     app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
     try:
         from app.infrastructure.cache.redis_cache import get_cache_service
         app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
     except ImportError:
         pass # Ignore if not found

     # Override auth dependencies (assuming these exist)
     try:
         from app.presentation.api.dependencies.auth import get_current_user as auth_get_user
         app.dependency_overrides[auth_get_user] = lambda: mock_user
     except ImportError:
         print("Warning: get_current_user dependency not found for override.")
         pass # Ignore if auth dependency doesn't exist

     # Override rate limiter if needed (example)
     try:
         from app.presentation.api.dependencies.rate_limiter import RateLimitDependency
         app.dependency_overrides[RateLimitDependency] = lambda *args, **kwargs: lambda: None
     except ImportError:
         pass

     yield

     app.dependency_overrides = {}


@pytest.mark.db_required() # Assuming db_required is a valid marker
class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    @pytest.mark.asyncio
    async def test_record_analytics_event(self, client, mock_cache_service, mock_background_tasks, mock_user):
        """Test the record_analytics_event endpoint."""
        # Arrange
        event_data = {
            "event_type": "page_view",
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": "test-session",
            "user_id": None,  # Should be populated from authenticated user
            "client_info": {"browser": "Chrome", "os": "Windows"},
            "data": {"page": "/dashboard", "referrer": "/login"}
        }

        # Mock phi detector to avoid real PHI detection logic
        with patch('app.infrastructure.ml.phi_detection.PHIDetectionService') as mock_phi_detector:
            # Configure mock PHI detector
            mock_instance = mock_phi_detector.return_value
            mock_instance.ensure_initialized = MagicMock(return_value=None)
            mock_instance.contains_phi = MagicMock(return_value=False)

            # Act
            # Patch BackgroundTasks directly where it's used in the endpoint function
            with patch('app.presentation.api.endpoints.analytics_endpoints.BackgroundTasks', return_value=mock_background_tasks):
                 response = client.post("/analytics/events", json=event_data)

            # Assert
            assert response.status_code == status.HTTP_202_ACCEPTED
            response_data = response.json()
            assert response_data["status"] == "success"
            assert "event_id" in response_data["data"]

            # Verify the event was enhanced with user info
            mock_background_tasks.add_task.assert_called_once()
            args, _ = mock_background_tasks.add_task.call_args
            process_func, event, user_id = args # Unpack arguments passed to add_task
            assert isinstance(event, AnalyticsEvent) # Check type
            assert event.user_id == mock_user.id # Check user ID from mock

            # Verify cache was updated
            mock_cache_service.increment.assert_called_once()
            mock_cache_service.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_analytics_batch(self, client, mock_cache_service, mock_background_tasks, mock_user):
        """Test the record_analytics_batch endpoint."""
        # Arrange
        batch_data = {
            "events": [
                {
                    "event_type": "page_view",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "session_id": "test-session",
                    "user_id": None,
                    "client_info": {"browser": "Chrome", "os": "Windows"},
                    "data": {"page": "/dashboard", "referrer": "/login"}
                },
                {
                    "event_type": "button_click",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "session_id": "test-session",
                    "user_id": None,
                    "client_info": {"browser": "Chrome", "os": "Windows"},
                    "data": {"button_id": "submit", "page": "/form"}
                }
            ]
        }

        # Mock phi detector
        with patch('app.infrastructure.ml.phi_detection.PHIDetectionService') as mock_phi_detector:
            mock_instance = mock_phi_detector.return_value
            mock_instance.ensure_initialized = MagicMock(return_value=None)
            mock_instance.contains_phi = MagicMock(return_value=False)

            # Act
            with patch('app.presentation.api.endpoints.analytics_endpoints.BackgroundTasks', return_value=mock_background_tasks):
                response = client.post("/analytics/events/batch", json=batch_data)

            # Assert
            assert response.status_code == status.HTTP_202_ACCEPTED
            response_data = response.json()
            assert response_data["status"] == "success"
            assert response_data["data"]["batch_size"] == 2

            # Verify background task was called with the batch
            mock_background_tasks.add_task.assert_called_once()
            args, _ = mock_background_tasks.add_task.call_args
            process_func, events, user_id = args # Unpack arguments

            # Verify events were enhanced with user info
            assert isinstance(events, list)
            for event in events:
                 assert isinstance(event, AnalyticsEvent)
                 assert event.user_id == mock_user.id

            # Verify cache was updated (called twice for 2 events)
            assert mock_cache_service.increment.call_count == 2
            assert mock_cache_service.expire.call_count == 1 # Expire called once for the batch key

    @pytest.mark.asyncio
    async def test_phi_detection_in_analytics_event(self, client, mock_cache_service, mock_background_tasks, mock_user):
        """Test PHI detection in analytics events."""
        # Arrange
        event_data = {
            "event_type": "form_submit",
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": "test-session",
            "user_id": None,
            "client_info": {"browser": "Chrome", "os": "Windows"},
            "data": {
                "form_id": "patient_info",
                "fields": {
                    "name": "John Doe",  # This should be detected as PHI
                    "age": 45
                }
            }
        }

        # Mock phi detector to simulate PHI detection
        with patch('app.infrastructure.ml.phi_detection.PHIDetectionService') as mock_phi_detector:
            # Configure mock PHI detector to detect PHI
            mock_instance = mock_phi_detector.return_value
            mock_instance.ensure_initialized = MagicMock(return_value=None)
            mock_instance.contains_phi = MagicMock(return_value=True)
            # Simulate redaction by replacing the name
            redacted_data_str = json.dumps(event_data["data"]).replace("John Doe", "[REDACTED]")
            mock_instance.redact_phi = MagicMock(return_value=redacted_data_str)

            # Act
            with patch('app.presentation.api.endpoints.analytics_endpoints.BackgroundTasks', return_value=mock_background_tasks):
                response = client.post("/analytics/events", json=event_data)

            # Assert
            assert response.status_code == status.HTTP_202_ACCEPTED

            # Verify PHI detection was called
            mock_instance.contains_phi.assert_called_once()

            # Verify redaction was called because PHI was detected
            mock_instance.redact_phi.assert_called_once()

            # Check that the background task received the redacted data
            mock_background_tasks.add_task.assert_called_once()
            args, _ = mock_background_tasks.add_task.call_args
            _, event, _ = args
            assert isinstance(event.data, str) # Data should now be the redacted JSON string
            assert "John Doe" not in event.data
            assert "[REDACTED]" in event.data


    @pytest.mark.asyncio
    async def test_get_analytics_dashboard(self, client, mock_cache_service, mock_user):
        """Test the get_analytics_dashboard endpoint."""
        # Arrange
        # Mock dashboard data that would be cached
        mock_dashboard_data = {
            "event_count": 1250,
            "unique_users": 120,
            "top_events": [
                {"event_type": "page_view", "count": 800},
                {"event_type": "button_click", "count": 350},
                {"event_type": "form_submit", "count": 100}
            ],
            "hourly_breakdown": [
                {"hour": 0, "count": 20},
                {"hour": 1, "count": 15},
                # ... (add more hours if needed)
                {"hour": 23, "count": 45}
            ]
        }

        # Test cached response
        mock_cache_service.get.return_value = json.dumps(mock_dashboard_data) # Cache stores JSON

        # Act
        response = client.get("/analytics/dashboard?timeframe=daily")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"] == mock_dashboard_data

        # Verify cache was checked
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_not_called()

        # Test non-cached response
        mock_cache_service.get.reset_mock()
        mock_cache_service.set.reset_mock() # Reset set mock as well
        mock_cache_service.get.return_value = None

        # Act
        response = client.get("/analytics/dashboard?timeframe=weekly")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "success"
        # The endpoint generates default data if cache misses, check for expected keys
        assert "event_count" in response_data["data"]
        assert "unique_users" in response_data["data"]
        assert "top_events" in response_data["data"]

        # Verify cache was checked and data was cached
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()