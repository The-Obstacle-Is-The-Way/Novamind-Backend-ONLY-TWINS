# -*- coding: utf-8 -*-
"""
Unit tests for the SQLAlchemy implementation of the BiometricAlertRepository.

These tests verify that the repository correctly interacts with the database
and properly maps between domain entities and database models.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.entities.digital_twin.biometric_alert import BiometricAlert, AlertPriority, AlertStatus
from app.domain.exceptions import EntityNotFoundError, RepositoryError
from app.infrastructure.persistence.sqlalchemy.models.biometric_alert_model import BiometricAlertModel
from app.infrastructure.persistence.sqlalchemy.repositories.biometric_alert_repository import SQLAlchemyBiometricAlertRepository


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
        rule_id=sample_rule_id,
        created_at=datetime(2025, 3, 27, 12, 0, 0),
        updated_at=datetime(2025, 3, 27, 12, 0, 0)
    )


@pytest.fixture
def sample_alert_model(sample_alert):
    """Create a sample biometric alert model."""
    return BiometricAlertModel(
        alert_id=str(sample_alert.alert_id),
        patient_id=str(sample_alert.patient_id),
        alert_type=sample_alert.alert_type,
        description=sample_alert.description,
        priority=sample_alert.priority,
        data_points=sample_alert.data_points,
        rule_id=str(sample_alert.rule_id),
        created_at=sample_alert.created_at,
        updated_at=sample_alert.updated_at,
        status=sample_alert.status,
        acknowledged_by=None,
        acknowledged_at=None,
        resolved_by=None,
        resolved_at=None,
        resolution_notes=None,
        metadata={}
    )


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = MagicMock(spec=Session)
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.rollback = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


class TestSQLAlchemyBiometricAlertRepository:
    """Tests for the SQLAlchemy implementation of the BiometricAlertRepository."""
    
    def test_init(self, mock_session):
        """Test initializing the repository."""
        # Act
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        
        # Assert
        assert repository.session == mock_session
    
    async def test_save_new_alert(self, mock_session, sample_alert, sample_alert_model):
        """Test saving a new biometric alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().first.return_value = None
        
        # Mock the _map_to_model method
        with patch.object(repository, '_map_to_model', return_value=sample_alert_model) as mock_map_to_model:
            # Mock the _map_to_entity method
            with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
                # Act
                result = await repository.save(sample_alert)
                
                # Assert
                mock_map_to_model.assert_called_once_with(sample_alert)
                mock_session.add.assert_called_once_with(sample_alert_model)
                mock_session.commit.assert_called_once()
                mock_session.refresh.assert_called_once_with(sample_alert_model)
                mock_map_to_entity.assert_called_once_with(sample_alert_model)
                assert result == sample_alert
    
    async def test_save_existing_alert(self, mock_session, sample_alert, sample_alert_model):
        """Test updating an existing biometric alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().first.return_value = sample_alert_model
        
        # Mock the _update_model method
        with patch.object(repository, '_update_model') as mock_update_model:
            # Mock the _map_to_entity method
            with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
                # Act
                result = await repository.save(sample_alert)
                
                # Assert
                mock_update_model.assert_called_once_with(sample_alert_model, sample_alert)
                mock_session.commit.assert_called_once()
                mock_session.refresh.assert_called_once_with(sample_alert_model)
                mock_map_to_entity.assert_called_once_with(sample_alert_model)
                assert result == sample_alert
    
    async def test_save_error(self, mock_session, sample_alert):
        """Test handling an error when saving an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.save(sample_alert)
        
        assert "Error saving biometric alert" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
    
    async def test_get_by_id(self, mock_session, sample_alert_id, sample_alert, sample_alert_model):
        """Test retrieving an alert by ID."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().first.return_value = sample_alert_model
        
        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
            result = await repository.get_by_id(sample_alert_id)
            
            # Assert
            mock_session.query.assert_called_with(BiometricAlertModel)
            mock_map_to_entity.assert_called_once_with(sample_alert_model)
            assert result == sample_alert
    
    async def test_get_by_id_not_found(self, mock_session, sample_alert_id):
        """Test retrieving a non-existent alert by ID."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().first.return_value = None
        
        # Act
        result = await repository.get_by_id(sample_alert_id)
        
        # Assert
        assert result is None
    
    async def test_get_by_id_error(self, mock_session, sample_alert_id):
        """Test handling an error when retrieving an alert by ID."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.get_by_id(sample_alert_id)
        
        assert "Error retrieving biometric alert" in str(exc_info.value)
    
    async def test_get_by_patient_id(self, mock_session, sample_patient_id, sample_alert, sample_alert_model):
        """Test retrieving alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().order_by().limit().offset().all.return_value = [sample_alert_model]
        
        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
            result = await repository.get_by_patient_id(sample_patient_id)
            
            # Assert
            mock_session.query.assert_called_with(BiometricAlertModel)
            mock_map_to_entity.assert_called_once_with(sample_alert_model)
            assert result == [sample_alert]
    
    async def test_get_by_patient_id_with_filters(self, mock_session, sample_patient_id, sample_alert, sample_alert_model):
        """Test retrieving alerts for a patient with filters."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().order_by().limit().offset().all.return_value = [sample_alert_model]
        
        status = AlertStatus.NEW
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 3, 31)
        limit = 10
        offset = 20
        
        # Mock the _apply_filters method
        with patch.object(repository, '_apply_filters', return_value=mock_session) as mock_apply_filters:
            # Mock the _map_to_entity method
            with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
                # Act
                result = await repository.get_by_patient_id(
                    patient_id=sample_patient_id,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset
                )
                
                # Assert
                mock_session.query.assert_called_with(BiometricAlertModel)
                mock_apply_filters.assert_called_once_with(mock_session, status, start_date, end_date)
                mock_map_to_entity.assert_called_once_with(sample_alert_model)
                assert result == [sample_alert]
    
    async def test_get_by_patient_id_error(self, mock_session, sample_patient_id):
        """Test handling an error when retrieving alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.get_by_patient_id(sample_patient_id)
        
        assert "Error retrieving biometric alerts" in str(exc_info.value)
    
    async def test_get_active_alerts(self, mock_session, sample_alert, sample_alert_model):
        """Test retrieving active alerts."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().order_by().limit().offset().all.return_value = [sample_alert_model]
        
        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
            result = await repository.get_active_alerts()
            
            # Assert
            mock_session.query.assert_called_with(BiometricAlertModel)
            mock_map_to_entity.assert_called_once_with(sample_alert_model)
            assert result == [sample_alert]
    
    async def test_get_active_alerts_with_priority(self, mock_session, sample_alert, sample_alert_model):
        """Test retrieving active alerts with priority filter."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().filter().order_by().limit().offset().all.return_value = [sample_alert_model]
        
        priority = AlertPriority.URGENT
        
        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
            result = await repository.get_active_alerts(priority=priority)
            
            # Assert
            mock_session.query.assert_called_with(BiometricAlertModel)
            mock_map_to_entity.assert_called_once_with(sample_alert_model)
            assert result == [sample_alert]
    
    async def test_get_active_alerts_error(self, mock_session):
        """Test handling an error when retrieving active alerts."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.get_active_alerts()
        
        assert "Error retrieving active alerts" in str(exc_info.value)
    
    async def test_update_status(self, mock_session, sample_alert_id, sample_provider_id, sample_alert, sample_alert_model):
        """Test updating the status of an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().first.return_value = sample_alert_model
        
        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Mock the save method
            with patch.object(repository, 'save', return_value=sample_alert) as mock_save:
                # Act
                result = await repository.update_status(
                    alert_id=sample_alert_id,
                    status=AlertStatus.ACKNOWLEDGED,
                    provider_id=sample_provider_id
                )
                
                # Assert
                mock_session.query.assert_called_with(BiometricAlertModel)
                mock_map_to_entity.assert_called_once_with(sample_alert_model)
                mock_save.assert_called_once()
                assert result == sample_alert
    
    async def test_update_status_not_found(self, mock_session, sample_alert_id, sample_provider_id):
        """Test updating the status of a non-existent alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().first.return_value = None
        
        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await repository.update_status(
                alert_id=sample_alert_id,
                status=AlertStatus.ACKNOWLEDGED,
                provider_id=sample_provider_id
            )
        
        assert f"Biometric alert with ID {sample_alert_id} not found" in str(exc_info.value)
    
    async def test_update_status_error(self, mock_session, sample_alert_id, sample_provider_id):
        """Test handling an error when updating the status of an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.update_status(
                alert_id=sample_alert_id,
                status=AlertStatus.ACKNOWLEDGED,
                provider_id=sample_provider_id
            )
        
        assert "Error updating alert status" in str(exc_info.value)
    
    async def test_delete(self, mock_session, sample_alert_id):
        """Test deleting an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().delete.return_value = 1
        
        # Act
        result = await repository.delete(sample_alert_id)
        
        # Assert
        mock_session.query.assert_called_with(BiometricAlertModel)
        mock_session.commit.assert_called_once()
        assert result is True
    
    async def test_delete_not_found(self, mock_session, sample_alert_id):
        """Test deleting a non-existent alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().delete.return_value = 0
        
        # Act
        result = await repository.delete(sample_alert_id)
        
        # Assert
        mock_session.query.assert_called_with(BiometricAlertModel)
        mock_session.commit.assert_called_once()
        assert result is False
    
    async def test_delete_error(self, mock_session, sample_alert_id):
        """Test handling an error when deleting an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().delete.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.delete(sample_alert_id)
        
        assert "Error deleting biometric alert" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
    
    async def test_count_by_patient(self, mock_session, sample_patient_id):
        """Test counting alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().scalar.return_value = 5
        
        # Act
        result = await repository.count_by_patient(sample_patient_id)
        
        # Assert
        assert result == 5
    
    async def test_count_by_patient_with_filters(self, mock_session, sample_patient_id):
        """Test counting alerts for a patient with filters."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query().filter().scalar.return_value = 3
        
        status = AlertStatus.NEW
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 3, 31)
        
        # Mock the _apply_filters method
        with patch.object(repository, '_apply_filters', return_value=mock_session) as mock_apply_filters:
            # Act
            result = await repository.count_by_patient(
                patient_id=sample_patient_id,
                status=status,
                start_date=start_date,
                end_date=end_date
            )
            
            # Assert
            mock_apply_filters.assert_called_once_with(mock_session, status, start_date, end_date)
            assert result == 3
    
    async def test_count_by_patient_error(self, mock_session, sample_patient_id):
        """Test handling an error when counting alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.count_by_patient(sample_patient_id)
        
        assert "Error counting biometric alerts" in str(exc_info.value)
    
    def test_apply_filters(self, mock_session):
        """Test applying filters to a query."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        status = AlertStatus.NEW
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 3, 31)
        
        # Act
        result = repository._apply_filters(mock_session, status, start_date, end_date)
        
        # Assert
        assert result == mock_session
        mock_session.filter.assert_called()
    
    def test_map_to_entity(self, sample_alert_model, sample_alert):
        """Test mapping a model to an entity."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(MagicMock())
        
        # Act
        result = repository._map_to_entity(sample_alert_model)
        
        # Assert
        assert isinstance(result, BiometricAlert)
        assert str(result.alert_id) == sample_alert_model.alert_id
        assert str(result.patient_id) == sample_alert_model.patient_id
        assert result.alert_type == sample_alert_model.alert_type
        assert result.description == sample_alert_model.description
        assert result.priority == sample_alert_model.priority
        assert result.data_points == sample_alert_model.data_points
        assert str(result.rule_id) == sample_alert_model.rule_id
        assert result.created_at == sample_alert_model.created_at
        assert result.updated_at == sample_alert_model.updated_at
        assert result.status == sample_alert_model.status
    
    def test_map_to_model(self, sample_alert):
        """Test mapping an entity to a model."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(MagicMock())
        
        # Act
        result = repository._map_to_model(sample_alert)
        
        # Assert
        assert isinstance(result, BiometricAlertModel)
        assert result.alert_id == str(sample_alert.alert_id)
        assert result.patient_id == str(sample_alert.patient_id)
        assert result.alert_type == sample_alert.alert_type
        assert result.description == sample_alert.description
        assert result.priority == sample_alert.priority
        assert result.data_points == sample_alert.data_points
        assert result.rule_id == str(sample_alert.rule_id)
        assert result.created_at == sample_alert.created_at
        assert result.updated_at == sample_alert.updated_at
        assert result.status == sample_alert.status
    
    def test_update_model(self, sample_alert_model, sample_alert):
        """Test updating a model with entity values."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(MagicMock())
        
        # Update some values in the entity
        updated_alert = sample_alert
        updated_alert.description = "Updated description"
        updated_alert.priority = AlertPriority.URGENT
        updated_alert.status = AlertStatus.ACKNOWLEDGED
        
        # Act
        repository._update_model(sample_alert_model, updated_alert)
        
        # Assert
        assert sample_alert_model.description == "Updated description"
        assert sample_alert_model.priority == AlertPriority.URGENT
        assert sample_alert_model.status == AlertStatus.ACKNOWLEDGED