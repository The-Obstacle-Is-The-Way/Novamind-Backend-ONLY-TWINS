# -*- coding: utf-8 -*-
"""
Unit tests for the biometric alert API endpoints.

These tests verify that the biometric alert API endpoints correctly handle
requests and responses, including validation, error handling, and authentication.
"""

from datetime import datetime, UTC, UTC, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.domain.entities.digital_twin.biometric_alert import BiometricAlert, AlertStatus, AlertPriority
from app.domain.exceptions import EntityNotFoundError, RepositoryError
from app.presentation.api.routes.biometric_alerts import router, get_alert_repository
from app.presentation.api.schemas.biometric_alert import (
    AlertStatusUpdateSchema,  
    BiometricAlertCreateSchema,  
    AlertPriorityEnum,  
    AlertStatusEnum
)


@pytest.fixture
def app():
    """Create a FastAPI app with the biometric alerts router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_repository():
    """Create a mock biometric alert repository."""
    repository = AsyncMock()
    repository.save = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.get_by_patient_id = AsyncMock()
    repository.get_active_alerts = AsyncMock()
    repository.update_status = AsyncMock()
    repository.delete = AsyncMock()
    repository.count_by_patient = AsyncMock()
    return repository


@pytest.fixture
def mock_current_user():
    """Create a mock current user."""
    return MagicMock(id=uuid4())


@pytest.fixture
def mock_current_provider():
    """Create a mock current provider."""
    return MagicMock(id=uuid4())


@pytest.fixture
def sample_alert_data():
    """Create sample data for creating a biometric alert."""
    return {
        "patient_id": str(uuid4()),
        "alert_type": "elevated_heart_rate",
        "description": "Heart rate exceeded threshold",
        "priority": "warning",
        "data_points": [
            {
                "data_type": "heart_rate",
                "value": 120.0,
                "timestamp": datetime.now(UTC).isoformat(),
                "source": "apple_watch"
            }
        ],
        "rule_id": str(uuid4()),
        "metadata": {"activity": "resting"}
    }


@pytest.fixture
def sample_alert():
    """Create a sample biometric alert."""
    return BiometricAlert(
        patient_id=uuid4(),
        alert_type="elevated_heart_rate",
        description="Heart rate exceeded threshold",
        priority=AlertPriority.WARNING,
        data_points=[
            {
                "data_type": "heart_rate",
                "value": 120.0,
                "timestamp": datetime.now(UTC).isoformat(),
                "source": "apple_watch"
            }
        ],
        rule_id=uuid4(),
        alert_id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        status=AlertStatus.NEW
    )


@pytest.fixture
def override_get_repository(app, mock_repository):
    """Override the get_alert_repository dependency."""
    app.dependency_overrides[get_alert_repository] = lambda: mock_repository
    return mock_repository


@pytest.fixture
def override_auth(app, mock_current_user, mock_current_provider):
    """Override the authentication dependencies."""
    from app.presentation.api.dependencies.auth import get_current_user, get_current_provider
    
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_current_provider] = lambda: mock_current_provider
    
    return mock_current_user, mock_current_provider


@pytest.mark.db_required
class TestCreateAlert:
    """Tests for the create_alert endpoint."""
    
    async def test_create_alert_success(self, client, override_get_repository, override_auth, sample_alert_data, sample_alert):
        """Test creating a biometric alert successfully."""
        # Setup
        mock_repository = override_get_repository
        mock_repository.save.return_value = sample_alert
        
        # Execute
        response = client.post("/biometric-alerts/", json=sample_alert_data)
        
        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["alert_id"] == str(sample_alert.alert_id)
        assert response.json()["patient_id"] == str(sample_alert.patient_id)
        assert response.json()["alert_type"] == sample_alert.alert_type
        assert response.json()["priority"] == sample_alert.priority.value
        
        # Verify repository was called
        mock_repository.save.assert_called_once()
    
    async def test_create_alert_validation_error(self, client, override_get_repository, override_auth):
        """Test validation error when creating a biometric alert with invalid data."""
        # Setup - missing required fields
        invalid_data = {
            "patient_id": str(uuid4()),
            "alert_type": "elevated_heart_rate"
            # Missing other required fields
        }
        
        # Execute
        response = client.post("/biometric-alerts/", json=invalid_data)
        
        # Verify
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_create_alert_repository_error(self, client, override_get_repository, override_auth, sample_alert_data):
        """Test error handling when the repository raises an error."""
        # Setup
        mock_repository = override_get_repository
        mock_repository.save.side_effect = RepositoryError("Database error")
        
        # Execute
        response = client.post("/biometric-alerts/", json=sample_alert_data)
        
        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error creating biometric alert" in response.json()["detail"]


class TestGetPatientAlerts:
    """Tests for the get_patient_alerts endpoint."""
    
    async def test_get_patient_alerts_success(self, client, override_get_repository, override_auth, sample_alert):
        """Test retrieving biometric alerts for a patient successfully."""
        # Setup
        patient_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.get_by_patient_id.return_value = [sample_alert]
        mock_repository.count_by_patient.return_value = 1
        
        # Execute
        response = client.get(f"/biometric-alerts/patient/{patient_id}")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1
        assert response.json()["page"] == 1
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["alert_id"] == str(sample_alert.alert_id)
        
        # Verify repository was called with correct parameters
        mock_repository.get_by_patient_id.assert_called_once()
        call_args = mock_repository.get_by_patient_id.call_args[1]
        assert call_args["patient_id"] == patient_id
        assert call_args["limit"] == 20  # Default page size
        assert call_args["offset"] == 0  # First page
    
    async def test_get_patient_alerts_with_filters(self, client, override_get_repository, override_auth, sample_alert):
        """Test retrieving biometric alerts for a patient with filters."""
        # Setup
        patient_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.get_by_patient_id.return_value = [sample_alert]
        mock_repository.count_by_patient.return_value = 1
        
        # Execute - with status filter
        response = client.get(
            f"/biometric-alerts/patient/{patient_id}?status=new&page=2&page_size=10"
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        
        # Verify repository was called with correct parameters
        mock_repository.get_by_patient_id.assert_called_once()
        call_args = mock_repository.get_by_patient_id.call_args[1]
        assert call_args["patient_id"] == patient_id
        assert call_args["status"] == AlertStatus.NEW
        assert call_args["limit"] == 10  # Custom page size
        assert call_args["offset"] == 10  # Second page with page_size=10
    
    async def test_get_patient_alerts_repository_error(self, client, override_get_repository, override_auth):
        """Test error handling when the repository raises an error."""
        # Setup
        patient_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.get_by_patient_id.side_effect = RepositoryError("Database error")
        
        # Execute
        response = client.get(f"/biometric-alerts/patient/{patient_id}")
        
        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error retrieving biometric alerts" in response.json()["detail"]


class TestGetActiveAlerts:
    """Tests for the get_active_alerts endpoint."""
    
    async def test_get_active_alerts_success(self, client, override_get_repository, override_auth, sample_alert):
        """Test retrieving active biometric alerts successfully."""
        # Setup
        mock_repository = override_get_repository
        mock_repository.get_active_alerts.return_value = [sample_alert]
        
        # Execute
        response = client.get("/biometric-alerts/active")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1
        assert response.json()["page"] == 1
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["alert_id"] == str(sample_alert.alert_id)
        
        # Verify repository was called with correct parameters
        mock_repository.get_active_alerts.assert_called_once()
        call_args = mock_repository.get_active_alerts.call_args[1]
        assert call_args["priority"] is None  # No priority filter
        assert call_args["limit"] == 20  # Default page size
        assert call_args["offset"] == 0  # First page
    
    async def test_get_active_alerts_with_priority_filter(self, client, override_get_repository, override_auth, sample_alert):
        """Test retrieving active biometric alerts with priority filter."""
        # Setup
        mock_repository = override_get_repository
        mock_repository.get_active_alerts.return_value = [sample_alert]
        
        # Execute - with priority filter
        response = client.get(
            "/biometric-alerts/active?priority=urgent&page=2&page_size=10"
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        
        # Verify repository was called with correct parameters
        mock_repository.get_active_alerts.assert_called_once()
        call_args = mock_repository.get_active_alerts.call_args[1]
        assert call_args["priority"] == AlertPriority.URGENT
        assert call_args["limit"] == 10  # Custom page size
        assert call_args["offset"] == 10  # Second page with page_size=10
    
    async def test_get_active_alerts_repository_error(self, client, override_get_repository, override_auth):
        """Test error handling when the repository raises an error."""
        # Setup
        mock_repository = override_get_repository
        mock_repository.get_active_alerts.side_effect = RepositoryError("Database error")
        
        # Execute
        response = client.get("/biometric-alerts/active")
        
        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error retrieving active alerts" in response.json()["detail"]


class TestGetAlert:
    """Tests for the get_alert endpoint."""
    
    async def test_get_alert_success(self, client, override_get_repository, override_auth, sample_alert):
        """Test retrieving a specific biometric alert successfully."""
        # Setup
        alert_id = sample_alert.alert_id
        mock_repository = override_get_repository
        mock_repository.get_by_id.return_value = sample_alert
        
        # Execute
        response = client.get(f"/biometric-alerts/{alert_id}")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["alert_id"] == str(sample_alert.alert_id)
        assert response.json()["patient_id"] == str(sample_alert.patient_id)
        assert response.json()["alert_type"] == sample_alert.alert_type
        
        # Verify repository was called with correct parameters
        mock_repository.get_by_id.assert_called_once_with(alert_id)
    
    async def test_get_alert_not_found(self, client, override_get_repository, override_auth):
        """Test error handling when the alert doesn't exist."""
        # Setup
        alert_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.get_by_id.return_value = None
        
        # Execute
        response = client.get(f"/biometric-alerts/{alert_id}")
        
        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert f"Biometric alert with ID {alert_id} not found" in response.json()["detail"]
    
    async def test_get_alert_repository_error(self, client, override_get_repository, override_auth):
        """Test error handling when the repository raises an error."""
        # Setup
        alert_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.get_by_id.side_effect = RepositoryError("Database error")
        
        # Execute
        response = client.get(f"/biometric-alerts/{alert_id}")
        
        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error retrieving biometric alert" in response.json()["detail"]


class TestUpdateAlertStatus:
    """Tests for the update_alert_status endpoint."""
    
    async def test_update_alert_status_success(self, client, override_get_repository, override_auth, sample_alert):
        """Test updating the status of a biometric alert successfully."""
        # Setup
        alert_id = sample_alert.alert_id
        mock_repository = override_get_repository
        mock_repository.update_status.return_value = sample_alert
        
        # Status update data
        status_update = {
            "status": "acknowledged",
            "notes": "Reviewing this alert"
        }
        
        # Execute
        response = client.patch(f"/biometric-alerts/{alert_id}/status", json=status_update)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["alert_id"] == str(sample_alert.alert_id)
        
        # Verify repository was called with correct parameters
        mock_repository.update_status.assert_called_once()
        call_args = mock_repository.update_status.call_args[1]
        assert call_args["alert_id"] == alert_id
        assert call_args["status"] == AlertStatus.ACKNOWLEDGED
        assert call_args["notes"] == "Reviewing this alert"
    
    async def test_update_alert_status_not_found(self, client, override_get_repository, override_auth):
        """Test error handling when the alert doesn't exist."""
        # Setup
        alert_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.update_status.side_effect = EntityNotFoundError(f"Biometric alert with ID {alert_id} not found")
        
        # Status update data
        status_update = {
            "status": "acknowledged"
        }
        
        # Execute
        response = client.patch(f"/biometric-alerts/{alert_id}/status", json=status_update)
        
        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert f"Biometric alert with ID {alert_id} not found" in response.json()["detail"]
    
    async def test_update_alert_status_repository_error(self, client, override_get_repository, override_auth):
        """Test error handling when the repository raises an error."""
        # Setup
        alert_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.update_status.side_effect = RepositoryError("Database error")
        
        # Status update data
        status_update = {
            "status": "acknowledged"
        }
        
        # Execute
        response = client.patch(f"/biometric-alerts/{alert_id}/status", json=status_update)
        
        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error updating biometric alert status" in response.json()["detail"]


class TestDeleteAlert:
    """Tests for the delete_alert endpoint."""
    
    async def test_delete_alert_success(self, client, override_get_repository, override_auth, sample_alert):
        """Test deleting a biometric alert successfully."""
        # Setup
        alert_id = sample_alert.alert_id
        mock_repository = override_get_repository
        mock_repository.get_by_id.return_value = sample_alert
        mock_repository.delete.return_value = True
        
        # Execute
        response = client.delete(f"/biometric-alerts/{alert_id}")
        
        # Verify
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''  # No content in response
        
        # Verify repository was called with correct parameters
        mock_repository.get_by_id.assert_called_once_with(alert_id)
        mock_repository.delete.assert_called_once_with(alert_id)
    
    async def test_delete_alert_not_found(self, client, override_get_repository, override_auth):
        """Test error handling when the alert doesn't exist."""
        # Setup
        alert_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.get_by_id.return_value = None
        
        # Execute
        response = client.delete(f"/biometric-alerts/{alert_id}")
        
        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert f"Biometric alert with ID {alert_id} not found" in response.json()["detail"]
    
    async def test_delete_alert_repository_error(self, client, override_get_repository, override_auth):
        """Test error handling when the repository raises an error."""
        # Setup
        alert_id = uuid4()
        mock_repository = override_get_repository
        mock_repository.get_by_id.side_effect = RepositoryError("Database error")
        
        # Execute
        response = client.delete(f"/biometric-alerts/{alert_id}")
        
        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error deleting biometric alert" in response.json()["detail"]