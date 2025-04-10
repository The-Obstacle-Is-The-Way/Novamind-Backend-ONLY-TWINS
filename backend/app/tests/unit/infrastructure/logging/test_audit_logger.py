# -*- coding: utf-8 -*-
"""Unit tests for Audit Logger functionality.

This module tests the audit logger which creates and maintains HIPAA-compliant
audit trails of all system access and operations affecting PHI.
"""

import pytest
import json
import datetime
import tempfile
import os
from unittest.mock import patch, MagicMock, call
import logging

from app.infrastructure.logging.audit_logger import (
    AuditLogger,
    AuditConfig,
    AuditLevel,
    AuditEvent,
    EventType,
    AuditLogDestination,
    LoggingHandler,
    CloudWatchHandler,
    SecureFileHandler,
    SplunkHandler,
    PHIAccessInfo,
    UserContext
)


@pytest.fixture
def audit_config():
    """Create an audit logger configuration for testing."""
    return AuditConfig(
        enabled=True,
        log_level=AuditLevel.INFO,
        include_request_body=False,
        include_response_body=False,
        include_stack_trace=True,
        include_phi_access_reason=True,
        log_retention_days=365,
        destinations=[AuditLogDestination.FILE, AuditLogDestination.CONSOLE],
        file_path="audit.log",
        phi_access_log_separately=True,
        phi_access_log_path="phi_access.log",
        structured_logging=True,
        encrypt_logs=True,
        rotation_size_mb=10,
        rotation_time_hours=24,
        backup_count=30,
        timestamp_format="%Y-%m-%dT%H:%M:%S.%fZ"
    )


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    # Clean up after the test
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def audit_logger(audit_config, temp_log_file):
    """Create an audit logger for testing."""
    # Override the file path to use the temporary file
    config = audit_config
    config.file_path = temp_log_file
    config.phi_access_log_path = temp_log_file + ".phi"
    
    # Create the logger with mocked handlers
    logger = AuditLogger(config=config)
    logger.file_handler = MagicMock(spec=SecureFileHandler)
    logger.console_handler = MagicMock(spec=logging.StreamHandler)
    logger.cloudwatch_handler = None
    logger.splunk_handler = None
    
    # Mock the log sanitizer
    logger.log_sanitizer = MagicMock()
    logger.log_sanitizer.sanitize.side_effect = lambda x: x  # Identity function for testing
    logger.log_sanitizer.sanitize_structured_log.side_effect = lambda x: x
    
    return logger


@pytest.fixture
def user_context():
    """Create a sample user context for testing."""
    return UserContext(
        user_id="user123",
        username="dr.smith",
        roles=["psychiatrist"],
        ip_address="192.168.1.1",
        session_id="session-abc-123",
        device_info="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
    )


@pytest.mark.db_required
class TestAuditLogger:
    """Test suite for the audit logger."""
    
    @pytest.mark.db_required
def test_log_authentication(self, audit_logger, user_context):
        """Test logging of authentication events."""
        # Log a successful authentication
        audit_logger.log_authentication(
            user_id=user_context.user_id,
            username=user_context.username,
            roles=user_context.roles,
            ip_address=user_context.ip_address,
            device_info=user_context.device_info,
            status="success"
        )
        
        # Verify the log was sanitized and sent to the file handler
        audit_logger.log_sanitizer.sanitize_structured_log.assert_called_once()
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record from the emit call
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        
        # Verify the log record contains the expected information
        log_data = json.loads(log_record.getMessage())
        assert log_data["event_type"] == "AUTHENTICATION"
        assert log_data["status"] == "success"
        assert log_data["user_id"] == user_context.user_id
        assert log_data["username"] == user_context.username
        assert log_data["roles"] == user_context.roles
        assert log_data["ip_address"] == user_context.ip_address
        assert log_data["device_info"] == user_context.device_info
        assert "timestamp" in log_data
    
    @pytest.mark.db_required
def test_log_authentication_failure(self, audit_logger):
        """Test logging of failed authentication attempts."""
        # Log a failed authentication
        audit_logger.log_authentication_failure(
            username="invalid_user",
            ip_address="192.168.1.100",
            device_info="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6)",
            reason="Invalid credentials",
            attempt_count=3,
            status="failure"
        )
        
        # Verify the log was sent to the file handler
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record from the emit call
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        
        # Verify the log record contains the expected information
        log_data = json.loads(log_record.getMessage())
        assert log_data["event_type"] == "AUTHENTICATION"
        assert log_data["status"] == "failure"
        assert log_data["username"] == "invalid_user"
        assert log_data["reason"] == "Invalid credentials"
        assert log_data["attempt_count"] == 3
        assert log_data["ip_address"] == "192.168.1.100"
        assert "timestamp" in log_data
    
    @pytest.mark.db_required
def test_log_phi_access(self, audit_logger, user_context):
        """Test logging of PHI access events."""
        # Create PHI access information
        phi_access = PHIAccessInfo(
            resource_type="patient_record",
            resource_id="PT12345",
            action="read",
            reason="scheduled_appointment",
            patient_id="PT12345"
        )
        
        # Log PHI access
        audit_logger.log_phi_access(
            user_context=user_context,
            phi_access=phi_access
        )
        
        # For PHI access, logs should go to both regular and PHI-specific handlers
        assert audit_logger.file_handler.emit.call_count == 1
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify PHI access log contains required information
        assert log_data["event_type"] == "PHI_ACCESS"
        assert log_data["user_id"] == user_context.user_id
        assert log_data["roles"] == user_context.roles
        assert log_data["resource_type"] == phi_access.resource_type
        assert log_data["resource_id"] == phi_access.resource_id
        assert log_data["action"] == phi_access.action
        assert log_data["reason"] == phi_access.reason
        assert log_data["patient_id"] == phi_access.patient_id
        assert "timestamp" in log_data
        
        # Verify the user context is properly logged
        assert log_data["username"] == user_context.username
        assert log_data["ip_address"] == user_context.ip_address
        assert log_data["session_id"] == user_context.session_id
    
    @pytest.mark.db_required
def test_log_data_modification(self, audit_logger, user_context):
        """Test logging of data modification events."""
        # Log a data modification event
        audit_logger.log_data_modification(
            user_context=user_context,
            resource_type="medication",
            resource_id="MED67890",
            action="update",
            patient_id="PT12345",
            changes={
                "dosage": {"old": "50mg", "new": "75mg"},
                "frequency": {"old": "daily", "new": "twice daily"}
            }
        )
        
        # Verify the log was sent to the file handler
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify the data modification log contains the expected information
        assert log_data["event_type"] == "DATA_MODIFICATION"
        assert log_data["user_id"] == user_context.user_id
        assert log_data["username"] == user_context.username
        assert log_data["resource_type"] == "medication"
        assert log_data["resource_id"] == "MED67890"
        assert log_data["action"] == "update"
        assert log_data["patient_id"] == "PT12345"
        assert log_data["changes"]["dosage"]["old"] == "50mg"
        assert log_data["changes"]["dosage"]["new"] == "75mg"
        assert log_data["changes"]["frequency"]["old"] == "daily"
        assert log_data["changes"]["frequency"]["new"] == "twice daily"
        assert "timestamp" in log_data
    
    @pytest.mark.db_required
def test_log_phi_violation(self, audit_logger, user_context):
        """Test logging of PHI policy violations."""
        # Log a PHI violation event
        audit_logger.log_phi_violation(
            user_context=user_context,
            violation_type="unauthorized_access",
            resource_type="clinical_note",
            resource_id="CN98765",
            patient_id="PT12345",
            details="Attempted to access clinical note without proper authorization",
            severity="high",
            path="/api/clinical-notes/CN98765",
            phi_fields=["diagnosis", "notes"],
            remediation_action="access_denied"
        )
        
        # Verify the log was sent to the file handler
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify the PHI violation log contains the expected information
        assert log_data["event_type"] == "PHI_VIOLATION"
        assert log_data["user_id"] == user_context.user_id
        assert log_data["username"] == user_context.username
        assert log_data["violation_type"] == "unauthorized_access"
        assert log_data["resource_type"] == "clinical_note"
        assert log_data["resource_id"] == "CN98765"
        assert log_data["patient_id"] == "PT12345"
        assert "unauthorized" in log_data["details"].lower()
        assert log_data["severity"] == "high"
        assert log_data["path"] == "/api/clinical-notes/CN98765"
        assert "diagnosis" in log_data["phi_fields"]
        assert "notes" in log_data["phi_fields"]
        assert log_data["remediation_action"] == "access_denied"
        assert "timestamp" in log_data
    
    @pytest.mark.db_required
def test_log_system_event(self, audit_logger):
        """Test logging of general system events."""
        # Log a system event
        audit_logger.log_system_event(
            event_type="SYSTEM_STARTUP",
            component="api_server",
            message="API server started successfully",
            level=AuditLevel.INFO,
            details={
                "version": "1.5.2",
                "environment": "production",
                "node_id": "node-east-001"
            }
        )
        
        # Verify the log was sent to the file handler
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify the system event log contains the expected information
        assert log_data["event_type"] == "SYSTEM_STARTUP"
        assert log_data["component"] == "api_server"
        assert log_data["message"] == "API server started successfully"
        assert log_data["level"] == "INFO"
        assert log_data["details"]["version"] == "1.5.2"
        assert log_data["details"]["environment"] == "production"
        assert log_data["details"]["node_id"] == "node-east-001"
        assert "timestamp" in log_data
    
    @pytest.mark.db_required
def test_phi_redaction(self, audit_logger, user_context):
        """Test proper redaction of PHI in audit logs."""
        # Setup a log event with PHI
        phi_data = {
            "event_type": "DATA_ACCESS",
            "user_id": user_context.user_id,
            "resource_type": "patient_record",
            "resource_id": "PT12345",
            "patient": {
                "name": "John Smith",  # PHI
                "email": "john.smith@example.com",  # PHI
                "ssn": "123-45-6789",  # PHI
                "medical_record": {
                    "diagnosis": "F41.1",
                    "symptoms": "Exhibits symptoms of anxiety and sleeplessness"
                }
            }
        }
        
        # Configure the log sanitizer mock to simulate PHI redaction
        def mock_sanitize(data):
            if isinstance(data, dict) and "patient" in data:
                sanitized = data.copy()
                sanitized["patient"] = sanitized["patient"].copy()
                if "name" in sanitized["patient"]:
                    sanitized["patient"]["name"] = "[REDACTED]"
                if "email" in sanitized["patient"]:
                    sanitized["patient"]["email"] = "[REDACTED]"
                if "ssn" in sanitized["patient"]:
                    sanitized["patient"]["ssn"] = "[REDACTED]"
                return sanitized
            return data
        
        audit_logger.log_sanitizer.sanitize_structured_log.side_effect = mock_sanitize
        
        # Create a custom log method for this test
        audit_logger.log_custom_event("DATA_ACCESS", phi_data)
        
        # Verify the log was sanitized before being sent to handlers
        audit_logger.log_sanitizer.sanitize_structured_log.assert_called_once()
        
        # Get the sanitized log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify PHI was redacted
        assert log_data["patient"]["name"] == "[REDACTED]"
        assert log_data["patient"]["email"] == "[REDACTED]"
        assert log_data["patient"]["ssn"] == "[REDACTED]"
        
        # But non-PHI medical info should remain
        assert log_data["patient"]["medical_record"]["diagnosis"] == "F41.1"
    
    @pytest.mark.db_required
def test_log_to_multiple_destinations(self, audit_logger, user_context):
        """Test logging to multiple destinations."""
        # Add a mock CloudWatch handler
        cloud_handler = MagicMock(spec=CloudWatchHandler)
        audit_logger.cloudwatch_handler = cloud_handler
        
        # Log an event that should go to all handlers
        audit_logger.log_authentication(
            user_id=user_context.user_id,
            username=user_context.username,
            roles=user_context.roles,
            ip_address=user_context.ip_address,
            status="success"
        )
        
        # Verify the log was sent to all handlers
        audit_logger.file_handler.emit.assert_called_once()
        audit_logger.console_handler.emit.assert_called_once()
        cloud_handler.emit.assert_called_once()
        
        # Check all handlers received the same log record
        file_record = audit_logger.file_handler.emit.call_args[0][0]
        console_record = audit_logger.console_handler.emit.call_args[0][0]
        cloud_record = cloud_handler.emit.call_args[0][0]
        
        assert file_record.getMessage() == console_record.getMessage()
        assert file_record.getMessage() == cloud_record.getMessage()
    
    @pytest.mark.db_required
def test_log_level_filtering(self, audit_logger):
        """Test that logs are filtered based on configured log level."""
        # Set log level to WARNING
        audit_logger.config.log_level = AuditLevel.WARNING
        
        # Log an INFO event (should be filtered out)
        audit_logger.log_system_event(
            event_type="CONFIG_CHANGE",
            component="api_server",
            message="Configuration refreshed",
            level=AuditLevel.INFO
        )
        
        # Verify no log was emitted
        audit_logger.file_handler.emit.assert_not_called()
        
        # Log a WARNING event (should pass through)
        audit_logger.log_system_event(
            event_type="DISK_SPACE_LOW",
            component="storage",
            message="Server disk space below 20%",
            level=AuditLevel.WARNING
        )
        
        # Verify the warning log was emitted
        audit_logger.file_handler.emit.assert_called_once()
    
    @pytest.mark.db_required
def test_include_stack_trace(self, audit_logger):
        """Test inclusion of stack trace in error logs."""
        # Configure to include stack trace
        audit_logger.config.include_stack_trace = True
        
        # Generate an exception
        try:
            raise ValueError("Test exception for stack trace logging")
        except ValueError as e:
            # Log the error with exception
            audit_logger.log_system_event(
                event_type="SYSTEM_ERROR",
                component="test_module",
                message=str(e),
                level=AuditLevel.ERROR,
                exception=e
            )
        
        # Verify the log was emitted
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify stack trace was included
        assert "stack_trace" in log_data
        assert "Traceback" in log_data["stack_trace"]
        assert "ValueError: Test exception" in log_data["stack_trace"]
    
    @pytest.mark.db_required
def test_structured_logging_format(self, audit_logger, user_context):
        """Test that logs are properly structured in JSON format."""
        # Log an event that produces structured output
        audit_logger.log_authentication(
            user_id=user_context.user_id,
            username=user_context.username,
            roles=user_context.roles,
            ip_address=user_context.ip_address,
            status="success"
        )
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_message = log_record.getMessage()
        
        # Verify it's valid JSON
        log_data = json.loads(log_message)
        
        # Verify structure matches the expected schema
        assert "event_type" in log_data
        assert "timestamp" in log_data
        assert "user_id" in log_data
        assert "username" in log_data
        assert "roles" in log_data
        assert "ip_address" in log_data
        assert "status" in log_data
        
        # Verify timestamp format
        timestamp = log_data["timestamp"]
        # Should be ISO 8601 format
        assert timestamp.endswith("Z")
        datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    
    @pytest.mark.db_required
def test_request_response_logging(self, audit_logger, user_context):
        """Test configurable inclusion of request/response bodies."""
        # Set up request and response data
        request_data = {
            "method": "POST",
            "path": "/api/patients",
            "query_params": {"include_history": "true"},
            "headers": {"Content-Type": "application/json"},
            "body": {"name": "John Smith", "dob": "1980-05-15"}
        }
        
        response_data = {
            "status_code": 201,
            "headers": {"Content-Type": "application/json"},
            "body": {"id": "PT12345", "status": "created"}
        }
        
        # Test with bodies excluded (default)
        audit_logger.config.include_request_body = False
        audit_logger.config.include_response_body = False
        
        audit_logger.log_api_request(
            user_context=user_context,
            request=request_data,
            response=response_data,
            duration_ms=152
        )
        
        # Get the log without bodies
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify bodies are excluded
        assert "body" not in log_data["request"]
        assert "body" not in log_data["response"]
        assert log_data["request"]["method"] == "POST"
        assert log_data["request"]["path"] == "/api/patients"
        assert log_data["response"]["status_code"] == 201
        
        # Reset mock
        audit_logger.file_handler.reset_mock()
        
        # Test with bodies included
        audit_logger.config.include_request_body = True
        audit_logger.config.include_response_body = True
        
        audit_logger.log_api_request(
            user_context=user_context,
            request=request_data,
            response=response_data,
            duration_ms=152
        )
        
        # Get the log with bodies
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify bodies are included
        assert "body" in log_data["request"]
        assert "body" in log_data["response"]
        assert log_data["request"]["body"] == request_data["body"]
        assert log_data["response"]["body"] == response_data["body"]
    
    @pytest.mark.db_required
def test_log_search_export(self, audit_logger):
        """Test exporting and searching audit logs."""
        # Mock log entries in the internal store
        mock_entries = [
            {
                "event_type": "AUTHENTICATION",
                "timestamp": "2025-03-27T10:00:00.000Z",
                "user_id": "user123",
                "status": "success"
            },
            {
                "event_type": "PHI_ACCESS",
                "timestamp": "2025-03-27T10:15:00.000Z",
                "user_id": "user123",
                "resource_type": "patient_record",
                "resource_id": "PT12345"
            },
            {
                "event_type": "DATA_MODIFICATION",
                "timestamp": "2025-03-27T11:30:00.000Z",
                "user_id": "user456",
                "resource_type": "medication",
                "resource_id": "MED67890"
            }
        ]
        
        # Mock the search method
        with patch.object(audit_logger, 'search_logs', return_value=mock_entries):
            # Search for specific user's logs
            results = audit_logger.search_logs(
                start_time="2025-03-27T09:00:00.000Z",
                end_time="2025-03-27T12:00:00.000Z",
                user_id="user123"
            )
            
            # Verify search results
            assert len(results) == 2
            assert all(entry["user_id"] == "user123" for entry in results)
            
            # Export search results
            with patch('builtins.open', MagicMock()):
                exported_file = audit_logger.export_logs(
                    logs=results,
                    format="json",
                    output_path="exported_logs.json"
                )
                assert exported_file == "exported_logs.json"
    
    @pytest.mark.db_required
def test_phi_access_reason_required(self, audit_logger, user_context):
        """Test enforcement of PHI access reason when configured."""
        # Configure to require PHI access reason
        audit_logger.config.include_phi_access_reason = True
        
        # Log PHI access without a reason (should fail)
        phi_access_no_reason = PHIAccessInfo(
            resource_type="patient_record",
            resource_id="PT12345",
            action="read",
            reason=None,  # Missing reason
            patient_id="PT12345"
        )
        
        with pytest.raises(ValueError, match="PHI access reason is required"):
            audit_logger.log_phi_access(
                user_context=user_context,
                phi_access=phi_access_no_reason
            )
        
        # Log PHI access with a reason (should succeed)
        phi_access_with_reason = PHIAccessInfo(
            resource_type="patient_record",
            resource_id="PT12345",
            action="read",
            reason="scheduled_appointment",
            patient_id="PT12345"
        )
        
        audit_logger.log_phi_access(
            user_context=user_context,
            phi_access=phi_access_with_reason
        )
        
        # Verify the log was emitted
        audit_logger.file_handler.emit.assert_called_once()
    
    @pytest.mark.db_required
def test_custom_audit_event(self, audit_logger):
        """Test creating and logging custom audit events."""
        # Create a custom event
        custom_event = AuditEvent(
            event_type=EventType.CUSTOM,
            timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            level=AuditLevel.INFO,
            message="Custom audit event for testing",
            details={
                "custom_field_1": "value1",
                "custom_field_2": 42,
                "custom_field_3": {"nested": "data"}
            }
        )
        
        # Log the custom event
        audit_logger.log_event(custom_event)
        
        # Verify the log was emitted
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify the custom event data
        assert log_data["event_type"] == "CUSTOM"
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Custom audit event for testing"
        assert log_data["details"]["custom_field_1"] == "value1"
        assert log_data["details"]["custom_field_2"] == 42
        assert log_data["details"]["custom_field_3"]["nested"] == "data"
    
    @pytest.mark.db_required
def test_log_anonymization(self, audit_logger, user_context):
        """Test anonymization of identifying information in logs when needed."""
        # Configure a mock anonymization function
        def mock_anonymize(field, value):
            if field == "patient_id":
                return f"ANON_{value[-3:]}"  # Return only last 3 chars with prefix
            if field == "user_id":
                return f"ANON_USER_{value[-2:]}"  # Return only last 2 chars with prefix
            return value
        
        # Set anonymizer in the logger
        audit_logger.anonymize_field = mock_anonymize
        
        # Log PHI access with fields that should be anonymized
        phi_access = PHIAccessInfo(
            resource_type="patient_record",
            resource_id="PT12345",
            action="read",
            reason="scheduled_appointment",
            patient_id="PT12345"
        )
        
        # Enable anonymization
        audit_logger.config.anonymize_patient_ids = True
        audit_logger.config.anonymize_user_ids = True
        
        # Log the event
        audit_logger.log_phi_access(
            user_context=user_context,
            phi_access=phi_access
        )
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify fields were anonymized
        assert log_data["patient_id"] == "ANON_345"  # Anonymized patient ID
        assert log_data["user_id"] == "ANON_USER_23"  # Anonymized user ID
    
    @pytest.mark.db_required
def test_log_rotation(self, audit_logger, temp_log_file):
        """Test log rotation functionality."""
        # Configure a real file handler for this test
        real_file_handler = SecureFileHandler(
            filename=temp_log_file,
            max_bytes=1024,  # Small size to trigger rotation
            backup_count=3,
            encoding="utf-8"
        )
        
        # Mock the internal handler methods
        real_file_handler.doRollover = MagicMock()
        real_file_handler.shouldRollover = MagicMock(return_value=True)  # Force rotation
        
        # Replace the mock handler with our test handler
        audit_logger.file_handler = real_file_handler
        
        # Generate enough logs to trigger rotation
        for i in range(5):
            audit_logger.log_system_event(
                event_type="TEST_EVENT",
                component="test",
                message=f"Test message {i}",
                level=AuditLevel.INFO,
                details={"iteration": i}
            )
        
        # Verify rotation was called
        real_file_handler.doRollover.assert_called()
    
    @pytest.mark.db_required
def test_batch_logging(self, audit_logger):
        """Test efficient batch logging of multiple events."""
        # Create multiple events
        events = [
            {
                "event_type": "AUTHENTICATION",
                "user_id": "user1",
                "status": "success"
            },
            {
                "event_type": "AUTHENTICATION",
                "user_id": "user2",
                "status": "success"
            },
            {
                "event_type": "AUTHENTICATION",
                "user_id": "user3",
                "status": "failure",
                "reason": "Invalid password"
            }
        ]
        
        # Log events in batch
        audit_logger.log_batch(events)
        
        # Verify each event was logged
        assert audit_logger.file_handler.emit.call_count == len(events)
    
    @pytest.mark.db_required
def test_request_id_correlation(self, audit_logger, user_context):
        """Test correlation of logs across a single request with request ID."""
        # Set a request ID for correlation
        request_id = "req-abc-123-xyz-789"
        
        # Log multiple events with the same request ID
        audit_logger.log_authentication(
            user_id=user_context.user_id,
            username=user_context.username,
            roles=user_context.roles,
            ip_address=user_context.ip_address,
            status="success",
            request_id=request_id
        )
        
        audit_logger.log_phi_access(
            user_context=user_context,
            phi_access=PHIAccessInfo(
                resource_type="patient_record",
                resource_id="PT12345",
                action="read",
                reason="scheduled_appointment",
                patient_id="PT12345"
            ),
            request_id=request_id
        )
        
        # Verify both logs include the same request ID
        assert audit_logger.file_handler.emit.call_count == 2
        
        log_record1 = audit_logger.file_handler.emit.call_args_list[0][0][0]
        log_data1 = json.loads(log_record1.getMessage())
        
        log_record2 = audit_logger.file_handler.emit.call_args_list[1][0][0]
        log_data2 = json.loads(log_record2.getMessage())
        
        assert log_data1["request_id"] == request_id
        assert log_data2["request_id"] == request_id
        assert log_data1["request_id"] == log_data2["request_id"]
    
    @pytest.mark.db_required
def test_performance_logging(self, audit_logger):
        """Test performance metrics in logs."""
        # Log a performance event
        audit_logger.log_performance(
            component="database",
            operation="query",
            duration_ms=120,
            success=True,
            endpoint="/api/patients",
            method="GET",
            details={
                "query_type": "patient_search",
                "result_count": 25,
                "cache_hit": False
            }
        )
        
        # Verify the log was emitted
        audit_logger.file_handler.emit.assert_called_once()
        
        # Get the log record
        log_record = audit_logger.file_handler.emit.call_args[0][0]
        log_data = json.loads(log_record.getMessage())
        
        # Verify performance metrics
        assert log_data["event_type"] == "PERFORMANCE"
        assert log_data["component"] == "database"
        assert log_data["operation"] == "query"
        assert log_data["duration_ms"] == 120
        assert log_data["success"] is True
        assert log_data["endpoint"] == "/api/patients"
        assert log_data["method"] == "GET"
        assert log_data["details"]["query_type"] == "patient_search"
        assert log_data["details"]["result_count"] == 25