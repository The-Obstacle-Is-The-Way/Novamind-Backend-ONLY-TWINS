# -*- coding: utf-8 -*-
"""
Unit tests for the BiometricAlertAuditService.

These tests verify that the BiometricAlertAuditService correctly
maintains an audit trail for biometric alerts.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.domain.entities.digital_twin.biometric_alert import BiometricAlert, AlertPriority, AlertStatus
from app.domain.services.biometric_alert_audit_service import BiometricAlertAuditService


class TestBiometricAlertAuditService:
    """Tests for the BiometricAlertAuditService."""
    
    @pytest.fixture
    def mock_alert_repository(self):
        """Create a mock BiometricAlertRepository."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.update_status = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create a mock audit logger."""
        logger = AsyncMock()
        logger.log_event = AsyncMock()
        logger.search_events = AsyncMock()
        return logger
    
    @pytest.fixture
    def audit_service(self, mock_alert_repository, mock_audit_logger):
        """Create a BiometricAlertAuditService with mock dependencies."""
        return BiometricAlertAuditService(
            mock_alert_repository,
            mock_audit_logger
        )
    
    @pytest.fixture
    def sample_patient_id(self):
        """Create a sample patient ID."""
        return UUID('12345678-1234-5678-1234-567812345678')
    
    @pytest.fixture
    def sample_provider_id(self):
        """Create a sample provider ID."""
        return UUID('87654321-8765-4321-8765-432187654321')
    
    @pytest.fixture
    def sample_rule_id(self):
        """Create a sample rule ID."""
        return UUID('11111111-2222-3333-4444-555555555555')
    
    @pytest.fixture
    def sample_alert_id(self):
        """Create a sample alert ID."""
        return UUID('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
    
    @pytest.fixture
    def sample_alert(self, sample_patient_id, sample_rule_id, sample_alert_id):
        """Create a sample BiometricAlert."""
        return BiometricAlert(
            alert_id=sample_alert_id,
            patient_id=sample_patient_id,
            alert_type="elevated_heart_rate",
            description="Heart rate is significantly elevated",
            priority=AlertPriority.URGENT,
            data_points=[
                {
                    "data_type": "heart_rate",
                    "value": 130,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "smartwatch"
                }
            ],
            rule_id=sample_rule_id
        )
    
    async def test_notify_alert_creates_audit_record(
        self, audit_service, mock_audit_logger, sample_alert
    ):
        """Test that notify_alert creates an audit record for a new alert."""
        # Execute
        await audit_service.notify_alert(sample_alert)
        
        # Verify
        assert mock_audit_logger.log_event.call_count == 1
        log_args = mock_audit_logger.log_event.call_args[1]
        
        assert log_args["event_type"] == "alert_generated"
        assert log_args["resource_type"] == "biometric_alert"
        assert log_args["resource_id"] == str(sample_alert.alert_id)
        assert log_args["patient_id"] == str(sample_alert.patient_id)
        assert "alert" in log_args["data"]
        
        # Verify PHI sanitization
        alert_data = log_args["data"]["alert"]
        assert "alert_id" in alert_data
        assert "alert_type" in alert_data
        assert "priority" in alert_data
        assert "status" in alert_data
        assert "created_at" in alert_data
        assert "updated_at" in alert_data
        # Ensure no PHI is included
        assert "data_points" not in alert_data
    
    async def test_record_alert_acknowledgment(
        self, audit_service, mock_alert_repository, mock_audit_logger,
        sample_alert, sample_alert_id, sample_provider_id
    ):
        """Test that record_alert_acknowledgment updates the alert status and creates an audit record."""
        # Setup
        mock_alert_repository.get_by_id.return_value = sample_alert
        mock_alert_repository.update_status.return_value = sample_alert
        
        # Execute
        await audit_service.record_alert_acknowledgment(
            sample_alert_id,
            sample_provider_id,
            "Acknowledged by Dr. Smith"
        )
        
        # Verify
        mock_alert_repository.get_by_id.assert_called_once_with(sample_alert_id)
        mock_alert_repository.update_status.assert_called_once_with(
            sample_alert_id,
            AlertStatus.ACKNOWLEDGED,
            sample_provider_id,
            "Acknowledged by Dr. Smith"
        )
        
        assert mock_audit_logger.log_event.call_count == 1
        log_args = mock_audit_logger.log_event.call_args[1]
        
        assert log_args["event_type"] == "alert_acknowledged"
        assert log_args["resource_type"] == "biometric_alert"
        assert log_args["resource_id"] == str(sample_alert_id)
        assert log_args["actor_id"] == str(sample_provider_id)
        assert log_args["patient_id"] == str(sample_alert.patient_id)
        assert log_args["notes"] == "Acknowledged by Dr. Smith"
    
    async def test_record_alert_resolution(
        self, audit_service, mock_alert_repository, mock_audit_logger,
        sample_alert, sample_alert_id, sample_provider_id
    ):
        """Test that record_alert_resolution updates the alert status and creates an audit record."""
        # Setup
        mock_alert_repository.get_by_id.return_value = sample_alert
        mock_alert_repository.update_status.return_value = sample_alert
        
        # Execute
        await audit_service.record_alert_resolution(
            sample_alert_id,
            sample_provider_id,
            "Patient contacted and advised to rest",
            "patient_contacted"
        )
        
        # Verify
        mock_alert_repository.get_by_id.assert_called_once_with(sample_alert_id)
        mock_alert_repository.update_status.assert_called_once_with(
            sample_alert_id,
            AlertStatus.RESOLVED,
            sample_provider_id,
            "Patient contacted and advised to rest"
        )
        
        assert mock_audit_logger.log_event.call_count == 1
        log_args = mock_audit_logger.log_event.call_args[1]
        
        assert log_args["event_type"] == "alert_resolved"
        assert log_args["resource_type"] == "biometric_alert"
        assert log_args["resource_id"] == str(sample_alert_id)
        assert log_args["actor_id"] == str(sample_provider_id)
        assert log_args["patient_id"] == str(sample_alert.patient_id)
        assert log_args["notes"] == "Patient contacted and advised to rest"
        assert log_args["data"]["resolution_action"] == "patient_contacted"
    
    async def test_record_alert_dismissal(
        self, audit_service, mock_alert_repository, mock_audit_logger,
        sample_alert, sample_alert_id, sample_provider_id
    ):
        """Test that record_alert_dismissal updates the alert status and creates an audit record."""
        # Setup
        mock_alert_repository.get_by_id.return_value = sample_alert
        mock_alert_repository.update_status.return_value = sample_alert
        
        # Execute
        await audit_service.record_alert_dismissal(
            sample_alert_id,
            sample_provider_id,
            "False positive due to device error"
        )
        
        # Verify
        mock_alert_repository.get_by_id.assert_called_once_with(sample_alert_id)
        mock_alert_repository.update_status.assert_called_once_with(
            sample_alert_id,
            AlertStatus.DISMISSED,
            sample_provider_id,
            "Dismissed: False positive due to device error"
        )
        
        assert mock_audit_logger.log_event.call_count == 1
        log_args = mock_audit_logger.log_event.call_args[1]
        
        assert log_args["event_type"] == "alert_dismissed"
        assert log_args["resource_type"] == "biometric_alert"
        assert log_args["resource_id"] == str(sample_alert_id)
        assert log_args["actor_id"] == str(sample_provider_id)
        assert log_args["patient_id"] == str(sample_alert.patient_id)
        assert log_args["notes"] == "False positive due to device error"
        assert log_args["data"]["dismissal_reason"] == "False positive due to device error"
    
    async def test_create_alert_audit_record_sanitizes_phi(
        self, audit_service, mock_audit_logger, sample_alert, sample_provider_id
    ):
        """Test that _create_alert_audit_record properly sanitizes PHI."""
        # Execute
        await audit_service._create_alert_audit_record(
            sample_alert,
            "test_event",
            "Test event description",
            sample_provider_id,
            "Test notes",
            {"additional": "data"}
        )
        
        # Verify
        assert mock_audit_logger.log_event.call_count == 1
        log_args = mock_audit_logger.log_event.call_args[1]
        
        assert log_args["event_type"] == "test_event"
        assert log_args["event_description"] == "Test event description"
        assert log_args["resource_type"] == "biometric_alert"
        assert log_args["resource_id"] == str(sample_alert.alert_id)
        assert log_args["actor_id"] == str(sample_provider_id)
        assert log_args["patient_id"] == str(sample_alert.patient_id)
        assert log_args["notes"] == "Test notes"
        
        # Verify sanitized alert data
        alert_data = log_args["data"]["alert"]
        assert "alert_id" in alert_data
        assert "alert_type" in alert_data
        assert "priority" in alert_data
        assert "status" in alert_data
        
        # Ensure no PHI is included
        assert "data_points" not in alert_data
        
        # Verify additional data is included
        assert log_args["data"]["additional"] == "data"
    
    async def test_search_audit_trail(
        self, audit_service, mock_audit_logger, sample_patient_id, 
        sample_alert_id, sample_provider_id
    ):
        """Test that search_audit_trail correctly builds search criteria."""
        # Setup
        mock_audit_logger.search_events.return_value = []
        start_date = datetime.utcnow()
        end_date = datetime.utcnow()
        
        # Execute
        await audit_service.search_audit_trail(
            patient_id=sample_patient_id,
            alert_id=sample_alert_id,
            provider_id=sample_provider_id,
            event_type="alert_resolved",
            start_date=start_date,
            end_date=end_date,
            limit=50,
            offset=10
        )
        
        # Verify
        assert mock_audit_logger.search_events.call_count == 1
        search_args = mock_audit_logger.search_events.call_args[1]
        
        criteria = search_args["criteria"]
        assert criteria["patient_id"] == str(sample_patient_id)
        assert criteria["resource_id"] == str(sample_alert_id)
        assert criteria["resource_type"] == "biometric_alert"
        assert criteria["actor_id"] == str(sample_provider_id)
        assert criteria["event_type"] == "alert_resolved"
        assert criteria["start_date"] == start_date
        assert criteria["end_date"] == end_date
        
        assert search_args["limit"] == 50
        assert search_args["offset"] == 10
    
    async def test_no_audit_record_for_nonexistent_alert(
        self, audit_service, mock_alert_repository, mock_audit_logger,
        sample_alert_id, sample_provider_id
    ):
        """Test that no audit record is created for a nonexistent alert."""
        # Setup
        mock_alert_repository.get_by_id.return_value = None
        
        # Execute
        await audit_service.record_alert_acknowledgment(
            sample_alert_id,
            sample_provider_id,
            "Acknowledged by Dr. Smith"
        )
        
        # Verify
        mock_alert_repository.get_by_id.assert_called_once_with(sample_alert_id)
        mock_alert_repository.update_status.assert_not_called()
        mock_audit_logger.log_event.assert_not_called()