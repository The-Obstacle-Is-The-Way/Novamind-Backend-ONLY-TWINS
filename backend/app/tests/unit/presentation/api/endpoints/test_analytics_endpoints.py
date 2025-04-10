# -*- coding: utf-8 -*-
"""
Unit tests for Analytics API endpoints.

This module contains unit tests for the analytics endpoints,
ensuring that they correctly handle events, validate data,
and process in a HIPAA-compliant manner.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.presentation.api.endpoints.analytics_endpoints import router, AnalyticsEvent


@pytest.fixture
@pytest.mark.db_required
def test_client():
    """Create a test client for the analytics endpoints."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_cache():
    """Create a mock cache service."""
    mock = AsyncMock()
    mock.increment = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_background_tasks():
    """Create a mock background tasks."""
    mock = MagicMock()
    mock.add_task = MagicMock()
    return mock


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return {"sub": "test-user-123", "email": "test@example.com", "role": "provider"}


@pytest.mark.asyncio
async @pytest.mark.db_required
def test_record_analytics_event(test_client, mock_cache, mock_background_tasks, mock_user):
    """Test the record_analytics_event endpoint."""
    # Arrange
    event_data = {
        "event_type": "page_view",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test-session",
        "user_id": None,  # Should be populated from authenticated user
        "client_info": {"browser": "Chrome", "os": "Windows"},
        "data": {"page": "/dashboard", "referrer": "/login"}
    }
    
    # Override dependencies
    app = test_client.app
    app.dependency_overrides = {
        "app.presentation.api.dependencies.auth.get_current_user": lambda: mock_user,
        "app.presentation.api.dependencies.services.get_cache_service": lambda: mock_cache,
        "app.presentation.api.dependencies.rate_limiter.RateLimitDependency": lambda *args, **kwargs: lambda: None
    }
    
    # Mock phi detector to avoid real PHI detection logic
    with patch('app.infrastructure.ml.phi_detection.PHIDetectionService') as mock_phi_detector:
        # Configure mock PHI detector
        mock_instance = mock_phi_detector.return_value
        mock_instance.ensure_initialized = MagicMock(return_value=None)
        mock_instance.contains_phi = MagicMock(return_value=False)
        
        # Act
        with patch('fastapi.BackgroundTasks', return_value=mock_background_tasks):
            response = test_client.post("/analytics/events", json=event_data)
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        response_data = response.json()
        assert response_data["status"] == "success"
        assert "event_id" in response_data["data"]
        
        # Verify the event was enhanced with user info
        mock_background_tasks.add_task.assert_called_once()
        args, _ = mock_background_tasks.add_task.call_args
        process_func, event, user_id = args
        assert event.user_id == mock_user["sub"]
        
        # Verify cache was updated
        mock_cache.increment.assert_called_once()
        mock_cache.expire.assert_called_once()


@pytest.mark.asyncio
async @pytest.mark.db_required
def test_record_analytics_batch(test_client, mock_cache, mock_background_tasks, mock_user):
    """Test the record_analytics_batch endpoint."""
    # Arrange
    batch_data = {
        "events": [
            {
                "event_type": "page_view",
                "timestamp": datetime.now().isoformat(),
                "session_id": "test-session",
                "user_id": None,
                "client_info": {"browser": "Chrome", "os": "Windows"},
                "data": {"page": "/dashboard", "referrer": "/login"}
            },
            {
                "event_type": "button_click",
                "timestamp": datetime.now().isoformat(),
                "session_id": "test-session",
                "user_id": None,
                "client_info": {"browser": "Chrome", "os": "Windows"},
                "data": {"button_id": "submit", "page": "/form"}
            }
        ]
    }
    
    # Override dependencies
    app = test_client.app
    app.dependency_overrides = {
        "app.presentation.api.dependencies.auth.get_current_user": lambda: mock_user,
        "app.presentation.api.dependencies.services.get_cache_service": lambda: mock_cache,
        "app.presentation.api.dependencies.rate_limiter.RateLimitDependency": lambda *args, **kwargs: lambda: None
    }
    
    # Mock phi detector to avoid real PHI detection logic
    with patch('app.infrastructure.ml.phi_detection.PHIDetectionService') as mock_phi_detector:
        # Configure mock PHI detector
        mock_instance = mock_phi_detector.return_value
        mock_instance.ensure_initialized = MagicMock(return_value=None)
        mock_instance.contains_phi = MagicMock(return_value=False)
        
        # Act
        with patch('fastapi.BackgroundTasks', return_value=mock_background_tasks):
            response = test_client.post("/analytics/events/batch", json=batch_data)
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"]["batch_size"] == 2
        
        # Verify background task was called with the batch
        mock_background_tasks.add_task.assert_called_once()
        args, _ = mock_background_tasks.add_task.call_args
        process_func, events, user_id = args
        
        # Verify events were enhanced with user info
        for event in events:
            assert event.user_id == mock_user["sub"]
        
        # Verify cache was updated (called twice for 2 events)
        assert mock_cache.increment.call_count == 2
        assert mock_cache.expire.call_count == 1


@pytest.mark.asyncio
async @pytest.mark.db_required
def test_phi_detection_in_analytics_event(test_client, mock_cache, mock_background_tasks, mock_user):
    """Test PHI detection in analytics events."""
    # Arrange
    event_data = {
        "event_type": "form_submit",
        "timestamp": datetime.now().isoformat(),
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
    
    # Override dependencies
    app = test_client.app
    app.dependency_overrides = {
        "app.presentation.api.dependencies.auth.get_current_user": lambda: mock_user,
        "app.presentation.api.dependencies.services.get_cache_service": lambda: mock_cache,
        "app.presentation.api.dependencies.rate_limiter.RateLimitDependency": lambda *args, **kwargs: lambda: None
    }
    
    # Mock phi detector to simulate PHI detection
    with patch('app.infrastructure.ml.phi_detection.PHIDetectionService') as mock_phi_detector:
        # Configure mock PHI detector to detect PHI
        mock_instance = mock_phi_detector.return_value
        mock_instance.ensure_initialized = MagicMock(return_value=None)
        mock_instance.contains_phi = MagicMock(return_value=True)
        mock_instance.redact_phi = MagicMock(
            return_value=str(event_data["data"]).replace("John Doe", "[REDACTED]")
        )
        
        # Act
        with patch('fastapi.BackgroundTasks', return_value=mock_background_tasks):
            response = test_client.post("/analytics/events", json=event_data)
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Verify PHI detection was called
        mock_instance.contains_phi.assert_called_once()
        
        # We expect the validator to have detected PHI and attempted redaction
        mock_instance.redact_phi.assert_called_once()


@pytest.mark.asyncio
async @pytest.mark.db_required
def test_get_analytics_dashboard(test_client, mock_cache, mock_user):
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
            {"hour": 23, "count": 45}
        ]
    }
    
    # Override dependencies
    app = test_client.app
    app.dependency_overrides = {
        "app.presentation.api.dependencies.auth.get_current_user": lambda: mock_user,
        "app.presentation.api.dependencies.services.get_cache_service": lambda: mock_cache,
        "app.presentation.api.dependencies.rate_limiter.RateLimitDependency": lambda *args, **kwargs: lambda: None
    }
    
    # Test cached response
    mock_cache.get.return_value = mock_dashboard_data
    
    # Act
    response = test_client.get("/analytics/dashboard?timeframe=daily")
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["data"] == mock_dashboard_data
    
    # Verify cache was checked
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_not_called()
    
    # Test non-cached response
    mock_cache.get.reset_mock()
    mock_cache.get.return_value = None
    
    # Act
    response = test_client.get("/analytics/dashboard?timeframe=weekly")
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "event_count" in response_data["data"]
    
    # Verify cache was checked and data was cached
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_called_once()