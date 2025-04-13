# -*- coding: utf-8 -*-
"""
Unit tests for the biometric alert API endpoints.

These tests verify that the biometric alert API endpoints correctly handle
requests and responses, including validation, error handling, and authentication.
"""

from app.domain.repositories.base_repository import BaseRepository
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional  # Added Optional

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.domain.entities.digital_twin.biometric_alert import BiometricAlert, AlertStatus, AlertPriority
from app.domain.exceptions import EntityNotFoundError, RepositoryError
# Assuming the router and dependency are correctly defined in this path
from app.presentation.api.routes.biometric_alerts import router, get_alert_repository
from app.presentation.api.schemas.biometric_alert import (
AlertStatusUpdateSchema,
BiometricAlertCreateSchema,
AlertPriorityEnum,
AlertStatusEnum
)
# Assuming BaseRepository exists for type hinting


@pytest.fixture
def app():

            """Create a FastAPI app with the biometric alerts router."""
    app_instance = FastAPI()
    app_instance.include_router(router)
    return app_instance@pytest.fixture
    def client(app):

            """Create a test client for the FastAPI app."""

        return TestClient(app)@pytest.fixture
        def mock_repository():

            """Create a mock biometric alert repository."""
        # Use AsyncMock for async repository methods
        repository = AsyncMock(spec=BaseRepository)  # Use a base spec if available
        repository.save = AsyncMock()
        repository.get_by_id = AsyncMock()
        repository.get_by_patient_id = AsyncMock()
        repository.get_active_alerts = AsyncMock()
        repository.update_status = AsyncMock()
        repository.delete = AsyncMock()
        repository.count_by_patient = AsyncMock()  # Assuming this method exists
        return repository@pytest.fixture
        def mock_current_user():

            """Create a mock current user."""
        # Assuming user object has an 'id' attribute
        user = MagicMock()
        user.id = uuid4()
        return user@pytest.fixture
        def mock_current_provider():

            """Create a mock current provider."""
        # Assuming provider object has an 'id' attribute
        provider = MagicMock()
        provider.id = uuid4()
        return provider@pytest.fixture
        def sample_alert_data():

            """Create sample data for creating a biometric alert."""

        return {
        "patient_id": str(uuid4()),
        "alert_type": "elevated_heart_rate",
        "description": "Heart rate exceeded threshold",
        "priority": "warning",  # Use string value from enum
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
def sample_alert(sample_alert_data):  # Use sample_alert_data to build sample_alert
    """Create a sample biometric alert."""
    patient_uuid = UUID(sample_alert_data["patient_id"],
    rule_uuid= UUID(sample_alert_data["rule_id"])
    return BiometricAlert(,
    patient_id= patient_uuid,
    alert_type = sample_alert_data["alert_type"],
    description = sample_alert_data["description"],
    priority = AlertPriority.WARNING,  # Use Enum member
    data_points = sample_alert_data["data_points"],
    rule_id = rule_uuid,
    alert_id = uuid4(),
    created_at = datetime.now(UTC),
    updated_at = datetime.now(UTC),
    status = AlertStatus.NEW  # Use Enum member


()


# Apply overrides automatically for all tests in module
@pytest.fixture(autouse=True)
def override_dependencies(
        app,
        mock_repository,
        mock_current_user,
        mock_current_provider):
            """Override dependencies for the FastAPI app."""
            # Override repository dependency
            app.dependency_overrides[get_alert_repository] = lambda: mock_repository

            # Override auth dependencies (assuming these exist)
            try:
                from app.presentation.api.dependencies.auth import get_current_user as auth_get_user
                app.dependency_overrides[auth_get_user] = lambda: mock_current_user
                except ImportError:
            print("Warning: get_current_user dependency not found for override.")
            pass  # Ignore if auth dependency doesn't exist

            try:
                from app.presentation.api.dependencies.auth import get_current_provider as auth_get_provider
                app.dependency_overrides[auth_get_provider] = lambda: mock_current_provider
                except ImportError:
                print("Warning: get_current_provider dependency not found for override.")
                pass  # Ignore if auth dependency doesn't exist

                yield  # Allow tests to run with overrides

                # Clean up overrides after tests
                app.dependency_overrides = {}

                @pytest.mark.db_required()  # Assuming db_required is a valid markerclass TestCreateAlert:
                """Tests for the create_alert endpoint."""

                @pytest.mark.asyncio
                async def test_create_alert_success(
                self,
                client,
                mock_repository,
                sample_alert_data,
                sample_alert):
                """Test creating a biometric alert successfully."""
                # Setup
                mock_repository.save.return_value = sample_alert

                # Execute
                response = client.post("/biometric-alerts/", json=sample_alert_data)

                # Verify
                assert response.status_code == status.HTTP_201_CREATED
                response_data = response.json()
                assert response_data["alert_id"] == str(sample_alert.alert_id)
                assert response_data["patient_id"] == str(sample_alert.patient_id)
                assert response_data["alert_type"] == sample_alert.alert_type
                assert response_data["priority"] == sample_alert.priority.value

                # Verify repository was called
                mock_repository.save.assert_called_once()
                # Optionally check the saved object
                saved_alert = mock_repository.save.call_args[0][0]
                assert isinstance(saved_alert, BiometricAlert)
                assert saved_alert.patient_id == UUID(sample_alert_data["patient_id"])

                @pytest.mark.asyncio
                async def test_create_alert_validation_error(self, client):
                    """Test validation error when creating a biometric alert with invalid data."""
                    # Setup - missing required fields
                    invalid_data = {
                    "patient_id": str(uuid4()),
                    "alert_type": "elevated_heart_rate"
                    # Missing other required fields like description, priority,
                    # data_points
        }

        # Execute
    response = client.post("/biometric-alerts/", json=invalid_data)

    # Verify
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_alert_repository_error(
            self, client, mock_repository, sample_alert_data):
                """Test error handling when the repository raises an error."""
                # Setup
                mock_repository.save.side_effect = RepositoryError("Database error")

                # Execute
                response = client.post("/biometric-alerts/", json=sample_alert_data)

                # Verify
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Error creating biometric alert" in response.json()["detail"]class TestGetPatientAlerts:
                    """Tests for the get_patient_alerts endpoint."""

                    @pytest.mark.asyncio
                    async def test_get_patient_alerts_success(
                    self, client, mock_repository, sample_alert):
                """Test retrieving biometric alerts for a patient successfully."""
                # Setup
                patient_id = uuid4()
                sample_alert.patient_id = patient_id  # Ensure sample alert matches patient_id
                mock_repository.get_by_patient_id.return_value = [sample_alert]
                mock_repository.count_by_patient.return_value = 1

                # Execute
                response = client.get(f"/biometric-alerts/patient/{patient_id}")

                # Verify
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["total"] == 1
                assert response_data["page"] == 1
                assert len(response_data["items"]) == 1
                assert response_data["items"][0]["alert_id"] == str(
                sample_alert.alert_id)

                # Verify repository was called with correct parameters
                mock_repository.get_by_patient_id.assert_called_once()
                call_args, call_kwargs = mock_repository.get_by_patient_id.call_args
                assert call_kwargs["patient_id"] == patient_id
                assert call_kwargs["limit"] == 20  # Default page size
                assert call_kwargs["offset"] == 0  # First page

                @pytest.mark.asyncio
                async def test_get_patient_alerts_with_filters(
                self, client, mock_repository, sample_alert):
                    """Test retrieving biometric alerts for a patient with filters."""
                    # Setup
                    patient_id = uuid4()
                    sample_alert.patient_id = patient_id
                    sample_alert.status = AlertStatus.NEW  # Ensure status matches filter
                    mock_repository.get_by_patient_id.return_value = [sample_alert]
                    mock_repository.count_by_patient.return_value = 1

                    # Execute - with status filter and pagination
                    response = client.get()
                    f"/biometric-alerts/patient/{patient_id}?status=new&page=2&page_size=10"
                    ()

                    # Verify
                    assert response.status_code == status.HTTP_200_OK

                    # Verify repository was called with correct parameters
                    mock_repository.get_by_patient_id.assert_called_once()
                    call_args, call_kwargs = mock_repository.get_by_patient_id.call_args
                    assert call_kwargs["patient_id"] == patient_id
                    assert call_kwargs["status"] == AlertStatus.NEW
                    assert call_kwargs["limit"] == 10  # Custom page size
                    assert call_kwargs["offset"] == 10  # Second page with page_size=10

                    @pytest.mark.asyncio
                    async def test_get_patient_alerts_repository_error(
                    self, client, mock_repository):
                        """Test error handling when the repository raises an error."""
                        # Setup
                        patient_id = uuid4()
                        mock_repository.get_by_patient_id.side_effect = RepositoryError(
                        "Database error")

                        # Execute
                        response = client.get(f"/biometric-alerts/patient/{patient_id}")

                        # Verify
                        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                        assert "Error retrieving biometric alerts" in response.json()["detail"]class TestGetActiveAlerts:
                        """Tests for the get_active_alerts endpoint."""

                        @pytest.mark.asyncio
                        async def test_get_active_alerts_success(
                        self, client, mock_repository, sample_alert):
                """Test retrieving active biometric alerts successfully."""
                # Setup
                mock_repository.get_active_alerts.return_value = (
                [sample_alert], 1)  # Return tuple (items, total)

                # Execute
                response = client.get("/biometric-alerts/active")

                # Verify
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["total"] == 1
                assert response_data["page"] == 1
                assert len(response_data["items"]) == 1
                assert response_data["items"][0]["alert_id"] == str(
                sample_alert.alert_id)

                # Verify repository was called with correct parameters
                mock_repository.get_active_alerts.assert_called_once()
                call_args, call_kwargs = mock_repository.get_active_alerts.call_args
                assert call_kwargs["priority"] is None  # No priority filter
                assert call_kwargs["limit"] == 20  # Default page size
                assert call_kwargs["offset"] == 0  # First page

                @pytest.mark.asyncio
                async def test_get_active_alerts_with_priority_filter(
                self, client, mock_repository, sample_alert):
                    """Test retrieving active biometric alerts with priority filter."""
                    # Setup
                    sample_alert.priority = AlertPriority.URGENT  # Ensure priority matches filter
                    mock_repository.get_active_alerts.return_value = ([sample_alert], 1)

                    # Execute - with priority filter and pagination
                    response = client.get()
                    "/biometric-alerts/active?priority=urgent&page=2&page_size=10"
                    ()

                    # Verify
                    assert response.status_code == status.HTTP_200_OK

                    # Verify repository was called with correct parameters
                    mock_repository.get_active_alerts.assert_called_once()
                    call_args, call_kwargs = mock_repository.get_active_alerts.call_args
                    assert call_kwargs["priority"] == AlertPriority.URGENT
                    assert call_kwargs["limit"] == 10  # Custom page size
                    assert call_kwargs["offset"] == 10  # Second page with page_size=10

                    @pytest.mark.asyncio
                    async def test_get_active_alerts_repository_error(
                    self, client, mock_repository):
                        """Test error handling when the repository raises an error."""
                        # Setup
                        mock_repository.get_active_alerts.side_effect = RepositoryError(
                        "Database error")

                        # Execute
                        response = client.get("/biometric-alerts/active")

                        # Verify
                        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                        assert "Error retrieving active alerts" in response.json()["detail"]class TestGetAlert:
                        """Tests for the get_alert endpoint."""

                        @pytest.mark.asyncio
                        async def test_get_alert_success(
                        self, client, mock_repository, sample_alert):
                """Test retrieving a specific biometric alert successfully."""
                # Setup
                alert_id = sample_alert.alert_id
                mock_repository.get_by_id.return_value = sample_alert

                # Execute
                response = client.get(f"/biometric-alerts/{alert_id}")

                # Verify
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["alert_id"] == str(sample_alert.alert_id)
                assert response_data["patient_id"] == str(sample_alert.patient_id)
                assert response_data["alert_type"] == sample_alert.alert_type

                # Verify repository was called with correct parameters
                mock_repository.get_by_id.assert_called_once_with(alert_id)

                @pytest.mark.asyncio
                async def test_get_alert_not_found(self, client, mock_repository):
                    """Test error handling when the alert doesn't exist."""
                    # Setup
                    alert_id = uuid4()
                    mock_repository.get_by_id.return_value = None

                    # Execute
                    response = client.get(f"/biometric-alerts/{alert_id}")

                    # Verify
                    assert response.status_code == status.HTTP_404_NOT_FOUND
                    assert f"Biometric alert with ID {alert_id} not found" in response.json()[
                    "detail"]

                    @pytest.mark.asyncio
                    async def test_get_alert_repository_error(
                    self, client, mock_repository):
                    """Test error handling when the repository raises an error."""
                    # Setup
                    alert_id = uuid4()
                    mock_repository.get_by_id.side_effect = RepositoryError(
                    "Database error")

                    # Execute
                    response = client.get(f"/biometric-alerts/{alert_id}")

                    # Verify
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Error retrieving biometric alert" in response.json()["detail"]class TestUpdateAlertStatus:
                        """Tests for the update_alert_status endpoint."""

                        @pytest.mark.asyncio
                        async def test_update_alert_status_success(
                        self,
                        client,
                        mock_repository,
                        sample_alert,
                        mock_current_provider):
                """Test updating the status of a biometric alert successfully."""
                # Setup
                alert_id = sample_alert.alert_id
                # Simulate the updated alert being returned
                updated_alert = sample_alert.copy(
                update={
                "status": AlertStatus.ACKNOWLEDGED,
                "updated_at": datetime.now(UTC)})
                mock_repository.update_status.return_value = updated_alert

                # Status update data
                status_update = {
                "status": "acknowledged",  # Use string value from enum
                "notes": "Reviewing this alert"
        }

        # Execute
    response = client.patch(
        f"/biometric-alerts/{alert_id}/status",
        json=status_update)

    # Verify
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["alert_id"] == str(sample_alert.alert_id)
    # Check against schema enum
    assert response_data["status"] == AlertStatusEnum.ACKNOWLEDGED

    # Verify repository was called with correct parameters
    mock_repository.update_status.assert_called_once()
    call_args, call_kwargs = mock_repository.update_status.call_args
    assert call_kwargs["alert_id"] == alert_id
    assert call_kwargs["status"] == AlertStatus.ACKNOWLEDGED  # Use domain enum
    assert call_kwargs["notes"] == "Reviewing this alert"
    # Assuming provider acknowledges
    assert call_kwargs["user_id"] == mock_current_provider.id

    @pytest.mark.asyncio
    async def test_update_alert_status_not_found(
            self, client, mock_repository):
                """Test error handling when the alert doesn't exist."""
                # Setup
                alert_id = uuid4()
                mock_repository.update_status.side_effect = EntityNotFoundError(
                f"Biometric alert with ID {alert_id} not found")

                # Status update data
                status_update = {
                "status": "acknowledged"
        }

        # Execute
    response = client.patch(
        f"/biometric-alerts/{alert_id}/status",
        json=status_update)

    # Verify
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert f"Biometric alert with ID {alert_id} not found" in response.json()[
        "detail"]

    @pytest.mark.asyncio
    async def test_update_alert_status_repository_error(
            self, client, mock_repository):
                """Test error handling when the repository raises an error."""
                # Setup
                alert_id = uuid4()
                mock_repository.update_status.side_effect = RepositoryError(
                "Database error")

                # Status update data
                status_update = {
                "status": "acknowledged"
        }

        # Execute
    response = client.patch(
        f"/biometric-alerts/{alert_id}/status",
        json=status_update)

    # Verify
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error updating biometric alert status" in response.json()["detail"]class TestDeleteAlert:
        """Tests for the delete_alert endpoint."""

        @pytest.mark.asyncio
        async def test_delete_alert_success(
            self, client, mock_repository, sample_alert):
                """Test deleting a biometric alert successfully."""
                # Setup
                alert_id = sample_alert.alert_id
                mock_repository.get_by_id.return_value = sample_alert  # Need to find it first
                mock_repository.delete.return_value = True

                # Execute
                response = client.delete(f"/biometric-alerts/{alert_id}")

                # Verify
                assert response.status_code == status.HTTP_204_NO_CONTENT
                assert response.content == b''  # No content in response

                # Verify repository was called with correct parameters
                mock_repository.get_by_id.assert_called_once_with(alert_id)
                mock_repository.delete.assert_called_once_with(alert_id)

                @pytest.mark.asyncio
                async def test_delete_alert_not_found(self, client, mock_repository):
                    """Test error handling when the alert doesn't exist."""
                    # Setup
                    alert_id = uuid4()
                    mock_repository.get_by_id.return_value = None  # Simulate not found

                    # Execute
                    response = client.delete(f"/biometric-alerts/{alert_id}")

                    # Verify
                    assert response.status_code == status.HTTP_404_NOT_FOUND
                    assert f"Biometric alert with ID {alert_id} not found" in response.json()[
                    "detail"]
                    # Delete should not be called if not found
                    mock_repository.delete.assert_not_called()

                    @pytest.mark.asyncio
                    async def test_delete_alert_repository_error(
                    self, client, mock_repository):
                    """Test error handling when the repository raises an error during delete."""
                    # Setup
                    alert_id = uuid4()
                    mock_repository.get_by_id.return_value = MagicMock()  # Simulate found
                    mock_repository.delete.side_effect = RepositoryError("Database error")

                    # Execute
                    response = client.delete(f"/biometric-alerts/{alert_id}")

                    # Verify
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Error deleting biometric alert" in response.json()["detail"]
