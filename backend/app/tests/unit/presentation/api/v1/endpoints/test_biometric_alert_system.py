# -*- coding: utf-8 -*-
"""
Unit tests for the biometric alert system API endpoints.

These tests verify that the API endpoints correctly handle requests,
validate input, and return appropriate responses.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.domain.entities.digital_twin.biometric_alert import AlertPriority, AlertStatus, BiometricAlert
from app.domain.exceptions import EntityNotFoundError, RepositoryError
from app.presentation.api.v1.endpoints.biometric_alert_system import router


@pytest.fixture
def sample_patient_id():
    """Create a sample patient ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_provider_id():
    """Create a sample provider ID."""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_alert_id():
    """Create a sample alert ID."""
    return UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def sample_rule_id():
    """Create a sample rule ID."""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def sample_data_points():
    """Create sample biometric data points."""
    timestamp = datetime(2025, 3, 27, 12, 0, 0).isoformat()
    return [
        {
            "data_type": "heart_rate",
            "value": 120.0,
            "timestamp": timestamp,
            "source": "apple_watch"
        }
    ]


@pytest.fixture
def sample_alert(sample_patient_id, sample_alert_id, sample_rule_id, sample_data_points):
    """Create a sample biometric alert."""
    return BiometricAlert(
        patient_id=sample_patient_id,
        alert_id=sample_alert_id,
        alert_type="elevated_heart_rate",
        description="Heart rate exceeded threshold",
        priority=AlertPriority.WARNING,
        data_points=sample_data_points,
        rule_id=sample_rule_id
    )


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
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
    user = MagicMock()
    user.id = UUID("00000000-0000-0000-0000-000000000001")
    user.username = "test_provider"
    user.roles = ["provider"]
    return user


@pytest.fixture
def mock_current_provider():
    """Create a mock current provider."""
    provider = MagicMock()
    provider.id = UUID("00000000-0000-0000-0000-000000000001")
    provider.username = "test_provider"
    provider.roles = ["provider"]
    return provider


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestBiometricAlertSystemEndpoints:
    """Tests for the biometric alert system API endpoints."""
    
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_create_alert(self, mock_get_current_provider, mock_get_alert_repository, 
                               mock_repository, mock_current_provider, sample_alert):
        """Test creating a new biometric alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import create_alert
        from app.presentation.api.schemas.biometric_alert import BiometricAlertCreateSchema
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.save.return_value = sample_alert
        
        alert_data = BiometricAlertCreateSchema(
            patient_id=sample_alert.patient_id,
            alert_type=sample_alert.alert_type,
            description=sample_alert.description,
            priority=sample_alert.priority,
            data_points=sample_alert.data_points,
            rule_id=sample_alert.rule_id
        )
        
        # Act
        response = await create_alert(
            alert_data=alert_data,
            repository=mock_repository,
            current_user=mock_current_provider
        )
        
        # Assert
        assert response == sample_alert
        mock_repository.save.assert_called_once()
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_create_alert_repository_error(self, mock_get_current_provider, mock_get_alert_repository, 
                                               mock_repository, mock_current_provider, sample_alert):
        """Test handling repository error when creating an alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import create_alert
        from app.presentation.api.schemas.biometric_alert import BiometricAlertCreateSchema
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.save.side_effect = RepositoryError("Database error")
        
        alert_data = BiometricAlertCreateSchema(
            patient_id=sample_alert.patient_id,
            alert_type=sample_alert.alert_type,
            description=sample_alert.description,
            priority=sample_alert.priority,
            data_points=sample_alert.data_points,
            rule_id=sample_alert.rule_id
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_alert(
                alert_data=alert_data,
                repository=mock_repository,
                current_user=mock_current_provider
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error creating biometric alert" in exc_info.value.detail
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_user")
    async def test_get_patient_alerts(self, mock_get_current_user, mock_get_alert_repository, 
                                     mock_repository, mock_current_user, sample_patient_id, sample_alert):
        """Test getting alerts for a patient."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import get_patient_alerts
        
        mock_get_current_user.return_value = mock_current_user
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_patient_id.return_value = [sample_alert]
        mock_repository.count_by_patient.return_value = 1
        
        # Act
        response = await get_patient_alerts(
            patient_id=sample_patient_id,
            repository=mock_repository,
            current_user=mock_current_user
        )
        
        # Assert
        assert response.items == [sample_alert]
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 20
        mock_repository.get_by_patient_id.assert_called_once_with(
            patient_id=sample_patient_id,
            status=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0
        )
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_user")
    async def test_get_patient_alerts_with_filters(self, mock_get_current_user, mock_get_alert_repository, 
                                                 mock_repository, mock_current_user, sample_patient_id, sample_alert):
        """Test getting alerts for a patient with filters."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import get_patient_alerts
        from app.presentation.api.schemas.biometric_alert import AlertStatusEnum
        
        mock_get_current_user.return_value = mock_current_user
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_patient_id.return_value = [sample_alert]
        mock_repository.count_by_patient.return_value = 1
        
        status_filter = AlertStatusEnum.NEW
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 3, 31)
        page = 2
        page_size = 10
        
        # Act
        response = await get_patient_alerts(
            patient_id=sample_patient_id,
            status_filter=status_filter,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            repository=mock_repository,
            current_user=mock_current_user
        )
        
        # Assert
        assert response.items == [sample_alert]
        assert response.total == 1
        assert response.page == page
        assert response.page_size == page_size
        mock_repository.get_by_patient_id.assert_called_once_with(
            patient_id=sample_patient_id,
            status=AlertStatus.NEW,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=10  # (page-1) * page_size
        )
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_user")
    async def test_get_patient_alerts_repository_error(self, mock_get_current_user, mock_get_alert_repository, 
                                                     mock_repository, mock_current_user, sample_patient_id):
        """Test handling repository error when getting patient alerts."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import get_patient_alerts
        
        mock_get_current_user.return_value = mock_current_user
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_patient_id.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_patient_alerts(
                patient_id=sample_patient_id,
                repository=mock_repository,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error retrieving biometric alerts" in exc_info.value.detail
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_get_active_alerts(self, mock_get_current_provider, mock_get_alert_repository, 
                                    mock_repository, mock_current_provider, sample_alert):
        """Test getting active alerts."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import get_active_alerts
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_active_alerts.return_value = [sample_alert]
        
        # Act
        response = await get_active_alerts(
            repository=mock_repository,
            current_user=mock_current_provider
        )
        
        # Assert
        assert response.items == [sample_alert]
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 20
        mock_repository.get_active_alerts.assert_called_once_with(
            priority=None,
            limit=20,
            offset=0
        )
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_get_active_alerts_with_priority(self, mock_get_current_provider, mock_get_alert_repository, 
                                                 mock_repository, mock_current_provider, sample_alert):
        """Test getting active alerts with priority filter."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import get_active_alerts
        from app.presentation.api.schemas.biometric_alert import AlertPriorityEnum
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_active_alerts.return_value = [sample_alert]
        
        priority = AlertPriorityEnum.URGENT
        
        # Act
        response = await get_active_alerts(
            priority=priority,
            repository=mock_repository,
            current_user=mock_current_provider
        )
        
        # Assert
        assert response.items == [sample_alert]
        mock_repository.get_active_alerts.assert_called_once_with(
            priority=AlertPriority.URGENT,
            limit=20,
            offset=0
        )
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_user")
    async def test_get_alert(self, mock_get_current_user, mock_get_alert_repository, 
                            mock_repository, mock_current_user, sample_alert_id, sample_alert):
        """Test getting a specific alert by ID."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import get_alert
        
        mock_get_current_user.return_value = mock_current_user
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_id.return_value = sample_alert
        
        # Act
        response = await get_alert(
            alert_id=sample_alert_id,
            repository=mock_repository,
            current_user=mock_current_user
        )
        
        # Assert
        assert response == sample_alert
        mock_repository.get_by_id.assert_called_once_with(sample_alert_id)
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_user")
    async def test_get_alert_not_found(self, mock_get_current_user, mock_get_alert_repository, 
                                      mock_repository, mock_current_user, sample_alert_id):
        """Test getting a non-existent alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import get_alert
        
        mock_get_current_user.return_value = mock_current_user
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_alert(
                alert_id=sample_alert_id,
                repository=mock_repository,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert f"Biometric alert with ID {sample_alert_id} not found" in exc_info.value.detail
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_update_alert_status(self, mock_get_current_provider, mock_get_alert_repository, 
                                      mock_repository, mock_current_provider, sample_alert_id, sample_alert):
        """Test updating the status of an alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import update_alert_status
        from app.presentation.api.schemas.biometric_alert import AlertStatusUpdateSchema, AlertStatusEnum
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        
        # Create a resolved alert
        resolved_alert = sample_alert
        resolved_alert.status = AlertStatus.RESOLVED
        resolved_alert.resolved_by = mock_current_provider.id
        resolved_alert.resolved_at = datetime.utcnow()
        resolved_alert.resolution_notes = "Issue resolved"
        
        mock_repository.update_status.return_value = resolved_alert
        
        status_update = AlertStatusUpdateSchema(
            status=AlertStatusEnum.RESOLVED,
            notes="Issue resolved"
        )
        
        # Act
        response = await update_alert_status(
            alert_id=sample_alert_id,
            status_update=status_update,
            repository=mock_repository,
            current_user=mock_current_provider
        )
        
        # Assert
        assert response == resolved_alert
        mock_repository.update_status.assert_called_once_with(
            alert_id=sample_alert_id,
            status=AlertStatus.RESOLVED,
            provider_id=mock_current_provider.id,
            notes="Issue resolved"
        )
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_update_alert_status_not_found(self, mock_get_current_provider, mock_get_alert_repository, 
                                               mock_repository, mock_current_provider, sample_alert_id):
        """Test updating the status of a non-existent alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import update_alert_status
        from app.presentation.api.schemas.biometric_alert import AlertStatusUpdateSchema, AlertStatusEnum
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.update_status.side_effect = EntityNotFoundError(f"Biometric alert with ID {sample_alert_id} not found")
        
        status_update = AlertStatusUpdateSchema(
            status=AlertStatusEnum.RESOLVED,
            notes="Issue resolved"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_alert_status(
                alert_id=sample_alert_id,
                status_update=status_update,
                repository=mock_repository,
                current_user=mock_current_provider
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert f"Biometric alert with ID {sample_alert_id} not found" in exc_info.value.detail
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_delete_alert(self, mock_get_current_provider, mock_get_alert_repository, 
                               mock_repository, mock_current_provider, sample_alert_id, sample_alert):
        """Test deleting an alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import delete_alert
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_id.return_value = sample_alert
        mock_repository.delete.return_value = True
        
        # Act
        await delete_alert(
            alert_id=sample_alert_id,
            repository=mock_repository,
            current_user=mock_current_provider
        )
        
        # Assert
        mock_repository.get_by_id.assert_called_once_with(sample_alert_id)
        mock_repository.delete.assert_called_once_with(sample_alert_id)
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_delete_alert_not_found(self, mock_get_current_provider, mock_get_alert_repository, 
                                         mock_repository, mock_current_provider, sample_alert_id):
        """Test deleting a non-existent alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import delete_alert
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_alert(
                alert_id=sample_alert_id,
                repository=mock_repository,
                current_user=mock_current_provider
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert f"Biometric alert with ID {sample_alert_id} not found" in exc_info.value.detail
        
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_alert_repository")
    @patch("app.presentation.api.v1.endpoints.biometric_alert_system.get_current_provider")
    async def test_delete_alert_failure(self, mock_get_current_provider, mock_get_alert_repository, 
                                       mock_repository, mock_current_provider, sample_alert_id, sample_alert):
        """Test handling a failure when deleting an alert."""
        # Arrange
        from app.presentation.api.v1.endpoints.biometric_alert_system import delete_alert
        
        mock_get_current_provider.return_value = mock_current_provider
        mock_get_alert_repository.return_value = mock_repository
        mock_repository.get_by_id.return_value = sample_alert
        mock_repository.delete.return_value = False
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_alert(
                alert_id=sample_alert_id,
                repository=mock_repository,
                current_user=mock_current_provider
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert f"Failed to delete biometric alert with ID {sample_alert_id}" in exc_info.value.detail