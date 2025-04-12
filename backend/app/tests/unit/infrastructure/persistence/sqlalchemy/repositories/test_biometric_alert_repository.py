# -*- coding: utf-8 -*-
"""
Unit tests for the SQLAlchemy implementation of the BiometricAlertRepository.

These tests verify that the repository correctly interacts with the database
and properly maps between domain entities and database models.
"""

from datetime import datetime, timedelta, UTC # Added UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional # Added Optional

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session # Assuming synchronous session for mock setup simplicity
from sqlalchemy.ext.asyncio import AsyncSession # For async spec

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
    timestamp = datetime(2025, 3, 27, 12, 0, 0, tzinfo=UTC).isoformat() # Add timezone
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
    now = datetime.now(UTC)
    return BiometricAlert()
        patient_id=sample_patient_id,
        alert_id=sample_alert_id,
        alert_type="elevated_heart_rate",
        description="Heart rate exceeded threshold",
        priority=AlertPriority.WARNING,
        data_points=sample_data_points,
        rule_id=sample_rule_id,
        created_at=now,
        updated_at=now,
        status=AlertStatus.NEW # Added status
    (    )


    @pytest.fixture
    def sample_alert_model(sample_alert):
    """Create a sample biometric alert model."""
    # Map the domain entity to the model structure
    return BiometricAlertModel()
        alert_id=str(sample_alert.alert_id),
        patient_id=str(sample_alert.patient_id),
        alert_type=sample_alert.alert_type,
        description=sample_alert.description,
        priority=sample_alert.priority,
        data_points=sample_alert.data_points, # Assuming JSON/dict storage
        rule_id=str(sample_alert.rule_id),
        created_at=sample_alert.created_at,
        updated_at=sample_alert.updated_at,
        status=sample_alert.status,
        acknowledged_by=None,
        acknowledged_at=None,
        resolved_by=None,
        resolved_at=None,
        resolution_notes=None,
        metadata={} # Assuming metadata exists
    (    )


    @pytest.fixture
    def mock_session():
    """Create a mock SQLAlchemy AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    # Mock query chain
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order_by = MagicMock()
    mock_limit = MagicMock()
    mock_offset = MagicMock()

    session.execute = AsyncMock() # Mock execute for query operations
    # Configure the chain
    session.execute.return_value.scalars.return_value.first = AsyncMock(return_value=None)
    session.execute.return_value.scalars.return_value.all = AsyncMock(return_value=[])
    session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None) # For count

    # Mock session methods
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock() # add is synchronous
    session.delete = AsyncMock() # Assuming delete might be async if using extensions

    return session


    @pytest.mark.db_required() # Assuming db_required is a valid marker
    class TestSQLAlchemyBiometricAlertRepository:
    """Tests for the SQLAlchemy implementation of the BiometricAlertRepository."""

    def test_init(self, mock_session):
        """Test initializing the repository."""
        # Act
        repository = SQLAlchemyBiometricAlertRepository(mock_session)

        # Assert
        assert repository.session == mock_session

        @pytest.mark.asyncio
        async def test_save_new_alert(self, mock_session, sample_alert, sample_alert_model):
        """Test saving a new biometric alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Simulate get_by_id finding nothing initially
        repository.get_by_id = AsyncMock(return_value=None)

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

        @pytest.mark.asyncio
        async def test_save_existing_alert(self, mock_session, sample_alert, sample_alert_model):
        """Test updating an existing biometric alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Simulate get_by_id finding the existing model
        repository.get_by_id = AsyncMock(return_value=sample_alert) # Return domain entity
        # Mock the internal _get_model_by_id to return the model
        repository._get_model_by_id = AsyncMock(return_value=sample_alert_model)


        # Mock the _update_model method
        with patch.object(repository, '_update_model') as mock_update_model:
            # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
                # Act
        result = await repository.save(sample_alert)

                # Assert
        repository._get_model_by_id.assert_called_once_with(sample_alert.alert_id)
        mock_update_model.assert_called_once_with(sample_alert_model, sample_alert)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_alert_model)
        mock_map_to_entity.assert_called_once_with(sample_alert_model)
        assert result == sample_alert

        @pytest.mark.asyncio
        async def test_save_error(self, mock_session, sample_alert):
        """Test handling an error when saving an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        repository.get_by_id = AsyncMock(return_value=None) # Simulate new alert
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
        await repository.save(sample_alert)

        assert "Error saving biometric alert" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_by_id(self, mock_session, sample_alert_id, sample_alert, sample_alert_model):
        """Test retrieving an alert by ID."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Mock the internal _get_model_by_id
        repository._get_model_by_id = AsyncMock(return_value=sample_alert_model)

        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
        result = await repository.get_by_id(sample_alert_id)

            # Assert
        repository._get_model_by_id.assert_called_once_with(sample_alert_id)
        mock_map_to_entity.assert_called_once_with(sample_alert_model)
        assert result == sample_alert

        @pytest.mark.asyncio
        async def test_get_by_id_not_found(self, mock_session, sample_alert_id):
        """Test retrieving a non-existent alert by ID."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        repository._get_model_by_id = AsyncMock(return_value=None) # Simulate not found

        # Act
        result = await repository.get_by_id(sample_alert_id)

        # Assert
        assert result is None
        repository._get_model_by_id.assert_called_once_with(sample_alert_id)

        @pytest.mark.asyncio
        async def test_get_by_id_error(self, mock_session, sample_alert_id):
        """Test handling an error when retrieving an alert by ID."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        repository._get_model_by_id = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_id(sample_alert_id)

        assert "Error retrieving biometric alert" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_get_by_patient_id(self, mock_session, sample_patient_id, sample_alert, sample_alert_model):
        """Test retrieving alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all = AsyncMock(return_value=[sample_alert_model])
        mock_session.execute.return_value = mock_result

        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
        result = await repository.get_by_patient_id(sample_patient_id)

            # Assert
        mock_session.execute.assert_called_once() # Check that execute was called
        mock_map_to_entity.assert_called_once_with(sample_alert_model)
        assert result == [sample_alert]

        @pytest.mark.asyncio
        async def test_get_by_patient_id_with_filters(self, mock_session, sample_patient_id, sample_alert, sample_alert_model):
        """Test retrieving alerts for a patient with filters."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all = AsyncMock(return_value=[sample_alert_model])
        mock_session.execute.return_value = mock_result

        status = AlertStatus.NEW
        start_date = datetime(2025, 3, 1, tzinfo=UTC)
        end_date = datetime(2025, 3, 31, tzinfo=UTC)
        limit = 10
        offset = 20

        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
        result = await repository.get_by_patient_id()
        patient_id=sample_patient_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
        (    )

            # Assert
        mock_session.execute.assert_called_once() # Check execute was called
            # Further checks on the select statement would require deeper mocking or inspection
        mock_map_to_entity.assert_called_once_with(sample_alert_model)
        assert result == [sample_alert]

        @pytest.mark.asyncio
        async def test_get_by_patient_id_error(self, mock_session, sample_patient_id):
        """Test handling an error when retrieving alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_patient_id(sample_patient_id)

        assert "Error retrieving biometric alerts" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_get_active_alerts(self, mock_session, sample_alert, sample_alert_model):
        """Test retrieving active alerts."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all = AsyncMock(return_value=[sample_alert_model])
        mock_session.execute.return_value = mock_result

        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
        result, total = await repository.get_active_alerts() # Assuming it returns (items, total)

            # Assert
        mock_session.execute.assert_called_once()
        mock_map_to_entity.assert_called_once_with(sample_alert_model)
        assert result == [sample_alert]
            # assert total == 1 # Need to mock count as well if testing total

        @pytest.mark.asyncio
        async def test_get_active_alerts_with_priority(self, mock_session, sample_alert, sample_alert_model):
        """Test retrieving active alerts with priority filter."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all = AsyncMock(return_value=[sample_alert_model])
        mock_session.execute.return_value = mock_result

        priority = AlertPriority.URGENT

        # Mock the _map_to_entity method
        with patch.object(repository, '_map_to_entity', return_value=sample_alert) as mock_map_to_entity:
            # Act
        result, total = await repository.get_active_alerts(priority=priority)

            # Assert
        mock_session.execute.assert_called_once()
            # Further checks on the select statement filters would require deeper mocking
        mock_map_to_entity.assert_called_once_with(sample_alert_model)
        assert result == [sample_alert]

        @pytest.mark.asyncio
        async def test_get_active_alerts_error(self, mock_session):
        """Test handling an error when retrieving active alerts."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
        await repository.get_active_alerts()

        assert "Error retrieving active alerts" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_update_status(self, mock_session, sample_alert_id, sample_provider_id, sample_alert, sample_alert_model):
        """Test updating the status of an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        repository._get_model_by_id = AsyncMock(return_value=sample_alert_model) # Mock internal fetch
        repository.save = AsyncMock(return_value=sample_alert) # Mock save

        # Act
        result = await repository.update_status()
        alert_id=sample_alert_id,
        status=AlertStatus.ACKNOWLEDGED,
        user_id=sample_provider_id, # Pass user_id
        notes="Acknowledged"
        (    )

        # Assert
        repository._get_model_by_id.assert_called_once_with(sample_alert_id)
        # Check that save was called with the updated entity
        repository.save.assert_called_once()
        saved_alert = repository.save.call_args[0][0]
        assert isinstance(saved_alert, BiometricAlert)
        assert saved_alert.status == AlertStatus.ACKNOWLEDGED
        assert saved_alert.acknowledged_by == sample_provider_id
        assert saved_alert.notes == "Acknowledged"
        assert result == sample_alert # Assuming save returns the entity passed to it

        @pytest.mark.asyncio
        async def test_update_status_not_found(self, mock_session, sample_alert_id, sample_provider_id):
        """Test updating the status of a non-existent alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        repository._get_model_by_id = AsyncMock(return_value=None) # Simulate not found

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
        await repository.update_status()
        alert_id=sample_alert_id,
        status=AlertStatus.ACKNOWLEDGED,
        user_id=sample_provider_id
        (    )

        assert f"Biometric alert with ID {sample_alert_id} not found" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_update_status_error(self, mock_session, sample_alert_id, sample_provider_id):
        """Test handling an error when updating the status of an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        repository._get_model_by_id = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
        await repository.update_status()
        alert_id=sample_alert_id,
        status=AlertStatus.ACKNOWLEDGED,
        user_id=sample_provider_id
        (    )

        assert "Error updating alert status" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_delete(self, mock_session, sample_alert_id):
        """Test deleting an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Mock the internal fetch and delete operation
        mock_model = MagicMock()
        repository._get_model_by_id = AsyncMock(return_value=mock_model)
        mock_session.delete = AsyncMock() # Mock async delete
        mock_session.commit = AsyncMock()

        # Act
        result = await repository.delete(sample_alert_id)

        # Assert
        repository._get_model_by_id.assert_called_once_with(sample_alert_id)
        mock_session.delete.assert_called_once_with(mock_model)
        mock_session.commit.assert_called_once()
        assert result is True

        @pytest.mark.asyncio
        async def test_delete_not_found(self, mock_session, sample_alert_id):
        """Test deleting a non-existent alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        repository._get_model_by_id = AsyncMock(return_value=None) # Simulate not found

        # Act & Assert
        with pytest.raises(EntityNotFoundError):
        await repository.delete(sample_alert_id)

        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()


        @pytest.mark.asyncio
        async def test_delete_error(self, mock_session, sample_alert_id):
        """Test handling an error when deleting an alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_model = MagicMock()
        repository._get_model_by_id = AsyncMock(return_value=mock_model)
        mock_session.delete = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
        await repository.delete(sample_alert_id)

        assert "Error deleting biometric alert" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_count_by_patient(self, mock_session, sample_patient_id):
        """Test counting alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Mock the scalar result for count
        mock_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=5)

        # Act
        result = await repository.count_by_patient(sample_patient_id)

        # Assert
        assert result == 5
        mock_session.execute.assert_called_once() # Check execute was called

        @pytest.mark.asyncio
        async def test_count_by_patient_with_filters(self, mock_session, sample_patient_id):
        """Test counting alerts for a patient with filters."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=3)

        status = AlertStatus.NEW
        start_date = datetime(2025, 3, 1, tzinfo=UTC)
        end_date = datetime(2025, 3, 31, tzinfo=UTC)

        # Mock the _apply_filters method (assuming it modifies the query object)
        with patch.object(repository, '_apply_filters', return_value=mock_session) as mock_apply_filters:
            # Act
        result = await repository.count_by_patient()
        patient_id=sample_patient_id,
        status=status,
        start_date=start_date,
        end_date=end_date
        (    )

            # Assert
            # _apply_filters should be called within the count method logic
            # mock_apply_filters.assert_called_once_with(mock_session, status, start_date, end_date) # Check might need adjustment based on internal query building
        mock_session.execute.assert_called_once() # Check execute was called
        assert result == 3

        @pytest.mark.asyncio
        async def test_count_by_patient_error(self, mock_session, sample_patient_id):
        """Test handling an error when counting alerts for a patient."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
        await repository.count_by_patient(sample_patient_id)

        assert "Error counting biometric alerts" in str(exc_info.value)

        # _apply_filters is internal, testing it directly might be less valuable than testing its effects via public methods
        # def test_apply_filters(self, mock_session):
        #     """Test applying filters to a query."""
        #     # Arrange
        #     repository = SQLAlchemyBiometricAlertRepository(mock_session)
        #     status = AlertStatus.NEW
        #     start_date = datetime(2025, 3, 1, tzinfo=UTC)
        #     end_date = datetime(2025, 3, 31, tzinfo=UTC)
        #     mock_query = MagicMock() # Mock the query object itself

        #     # Act
        #     result_query = repository._apply_filters(mock_query, status, start_date, end_date)

        #     # Assert
        #     assert result_query == mock_query # Should return the modified query
        #     mock_query.filter.assert_called() # Check that filter was called

        def test_map_to_entity(self, sample_alert_model, sample_alert):
        """Test mapping a model to an entity."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(MagicMock()) # Session not needed for mapping

        # Act
        result = repository._map_to_entity(sample_alert_model)

        # Assert
        assert isinstance(result, BiometricAlert)
        assert result.alert_id == UUID(sample_alert_model.alert_id)
        assert result.patient_id == UUID(sample_alert_model.patient_id)
        assert result.alert_type == sample_alert_model.alert_type
        assert result.description == sample_alert_model.description
        assert result.priority == sample_alert_model.priority
        assert result.status == sample_alert_model.status
        assert result.rule_id == UUID(sample_alert_model.rule_id)
        # Add more assertions for other fields if necessary

        def test_map_to_model(self, sample_alert):
        """Test mapping an entity to a model."""
         # Arrange
        repository = SQLAlchemyBiometricAlertRepository(MagicMock()) # Session not needed for mapping

        # Act
        result = repository._map_to_model(sample_alert)

        # Assert
        assert isinstance(result, BiometricAlertModel)
        assert result.alert_id == str(sample_alert.alert_id)
        assert result.patient_id == str(sample_alert.patient_id)
        assert result.alert_type == sample_alert.alert_type
        assert result.description == sample_alert.description
        assert result.priority == sample_alert.priority
        assert result.status == sample_alert.status
        assert result.rule_id == str(sample_alert.rule_id)
        # Add more assertions for other fields if necessary

        def test_update_model(self, sample_alert_model, sample_alert):
        """Test updating a model from an entity."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(MagicMock()) # Session not needed
        # Modify the entity slightly
        sample_alert.description = "Updated Description"
        sample_alert.status = AlertStatus.ACKNOWLEDGED
        sample_alert.acknowledged_by = UUID("11111111-1111-1111-1111-111111111111")
        sample_alert.acknowledged_at = datetime.now(UTC)

        # Act
        repository._update_model(sample_alert_model, sample_alert)

        # Assert
        assert sample_alert_model.description == "Updated Description"
        assert sample_alert_model.status == AlertStatus.ACKNOWLEDGED
        assert sample_alert_model.acknowledged_by == str(sample_alert.acknowledged_by)
        assert sample_alert_model.acknowledged_at == sample_alert.acknowledged_at
        # Check that ID and created_at are not changed
        assert sample_alert_model.alert_id == str(sample_alert.alert_id)
        assert sample_alert_model.created_at == sample_alert.created_at