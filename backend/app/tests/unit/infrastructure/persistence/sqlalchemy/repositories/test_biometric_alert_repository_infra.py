# -*- coding: utf-8 -*-
"""
Unit tests for the SQLAlchemy implementation of the BiometricAlertRepository.

These tests verify that the repository correctly interacts with the database
and properly maps between domain entities and database models.
"""

from datetime import datetime, timedelta, timezone # Corrected import
# from app.domain.utils.datetime_utils import UTC # Removed redundant import
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4 # Corrected import
from typing import List, Dict, Any, Optional

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Correct import for BiometricAlert and enums
from app.domain.services.biometric_event_processor import BiometricAlert, AlertPriority
from app.presentation.api.schemas.biometric_alert import AlertStatusEnum as AlertStatus
from app.domain.exceptions import EntityNotFoundError, RepositoryError
from app.infrastructure.persistence.sqlalchemy.models.biometric_alert_model import BiometricAlertModel
from app.infrastructure.persistence.sqlalchemy.repositories.biometric_alert_repository import SQLAlchemyBiometricAlertRepository

# --- Fixture Definitions --- Start Reconstruction ---

@pytest.fixture
def sample_patient_id() -> UUID:
    """Create a sample patient ID."""
    return UUID("12345678-1234-5678-1234-567812345678")

@pytest.fixture
def sample_provider_id() -> UUID:
    """Create a sample provider ID."""
    return UUID("00000000-0000-0000-0000-000000000001")

@pytest.fixture
def sample_alert_id() -> UUID:
    """Create a sample alert ID."""
    return UUID("00000000-0000-0000-0000-000000000003")

@pytest.fixture
def sample_rule_id() -> UUID:
    """Create a sample rule ID."""
    return UUID("00000000-0000-0000-0000-000000000002")

@pytest.fixture
def sample_data_points() -> List[Dict[str, Any]]:
    """Create sample biometric data points."""
    timestamp_dt = datetime(2025, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
    timestamp_iso = timestamp_dt.isoformat()
    return [
        {
            "data_type": "heart_rate",
            "value": 120.0,
            "timestamp": timestamp_iso,
            "source": "apple_watch"
        }
    ]

@pytest.fixture
def sample_alert(
    sample_patient_id: UUID,
    sample_alert_id: UUID,
    sample_rule_id: UUID,
    sample_data_points: List[Dict[str, Any]]
) -> BiometricAlert:
    """Create a sample biometric alert domain entity."""
    now = datetime.now(timezone.utc)
    return BiometricAlert(
        patient_id=sample_patient_id,
        alert_id=sample_alert_id,
        alert_type="elevated_heart_rate",
        description="Heart rate exceeded threshold",
        priority=AlertPriority.WARNING,
        data_points=sample_data_points,
        rule_id=sample_rule_id,
        created_at=now,
        updated_at=now,
        status=AlertStatus.NEW
    )

@pytest.fixture
def sample_alert_model(sample_alert: BiometricAlert) -> BiometricAlertModel:
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
def mock_session() -> AsyncMock:
    """Create a mock SQLAlchemy AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    # Mock query chain methods needed by the repository
    session.execute = AsyncMock()
    mock_scalars_result = AsyncMock()
    mock_scalars_result.first = AsyncMock(return_value=None)
    mock_scalars_result.all = AsyncMock(return_value=[])
    session.execute.return_value.scalars = AsyncMock(return_value=mock_scalars_result)
    session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)
    session.execute.return_value.scalar = AsyncMock(return_value=0) # For count

    # Mock session methods
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock() # add is often synchronous in usage
    session.delete = AsyncMock()
    session.flush = AsyncMock() # Add flush if used

    return session

# --- Test Class --- Start Reconstruction ---

# Assuming db_required marker is defined in conftest.py
@pytest.mark.db_required # Corrected decorator placement
class TestSQLAlchemyBiometricAlertRepository:
    """Tests for the SQLAlchemy implementation of the BiometricAlertRepository."""

    def test_init(self, mock_session: AsyncMock):
        """Test initializing the repository."""
        # Act
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Assert
        assert repository.session == mock_session

    @pytest.mark.asyncio
    async def test_save_new_alert(self, mock_session: AsyncMock, sample_alert: BiometricAlert, sample_alert_model: BiometricAlertModel):
        """Test saving a new biometric alert."""
        # Arrange
        repository = SQLAlchemyBiometricAlertRepository(mock_session)
        # Simulate get_by_id finding nothing initially
        # Patch the internal method directly for this test
        repository._get_model_by_id = AsyncMock(return_value=None)

        # Mock the mappers (can be done with patch if complex, direct assignment if simple)
        # Assume _map_to_model and _map_to_entity work correctly for unit test focus
        # If testing the mappers themselves, use separate tests.
        
        # Act
        # We need to ensure the mock session's refresh gets called with the model
        # And that add is called before commit
        async def refresh_effect(model_instance):
            # Simulate adding attributes that might happen during DB flush/commit
            pass 
        mock_session.refresh.side_effect = refresh_effect
        
        result = await repository.save(sample_alert)

        # Assert
        mock_session.add.assert_called_once() # Check model instance was added
        added_model = mock_session.add.call_args[0][0]
        assert isinstance(added_model, BiometricAlertModel)
        assert added_model.alert_id == str(sample_alert.alert_id)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(added_model) # Check refresh target
        # Assert the result is the original domain entity (as per repository pattern)
        assert result == sample_alert

    # --- Continue with other test methods, ensuring correct syntax and indentation ---
    # ... (rest of the file needs similar verification and correction) ...
