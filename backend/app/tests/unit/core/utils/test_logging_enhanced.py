"""Unit tests for enhanced logging functionality."""
import pytest
from unittest.mock import patch, MagicMock, call
import logging
import json
import os
import time
from datetime import datetime
import tempfile

from app.core.utils.logging import (
    setup_logging,
    PHISanitizingFilter,
    StructuredJsonFormatter,
    get_logger,
    audit_log,
    log_phi_detection,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
)


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock(spec=logging.Logger)
    return logger

@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    fd, path = tempfile.mkstemp(suffix=".log")
    os.close(fd)
    yield path
    # Cleanup
    try:
        os.remove(path)
    except OSError:
        pass


class TestLoggingSetup:
    """Test suite for logging setup."""

    @patch("app.core.utils.logging.logging")
    def test_setup_logging_basic(self, mock_logging):
        """Test basic logging setup."""
        # Setup
        mock_dict_config = mock_logging.config.dictConfig

        # Call function
        setup_logging(level="INFO")

        # Verify logging was configured
        mock_dict_config.assert_called_once()

        # Get the config passed to dictConfig
        config = mock_dict_config.call_args[0][0]

        # Check basic configs
        assert config["version"] == 1
        assert config["disable_existing_loggers"] is False
        assert "handlers" in config
        assert "loggers" in config
        assert "root" in config
        assert config["root"]["level"] == "INFO"

    @patch("app.core.utils.logging.logging")
    def test_setup_logging_with_file(self, mock_logging, temp_log_file):
        """Test logging setup with file output."""
        # Setup
        mock_dict_config = mock_logging.config.dictConfig

        # Call function with file
        setup_logging(level="DEBUG", log_file=temp_log_file)

        # Verify logging was configured
        mock_dict_config.assert_called_once()

        # Get the config passed to dictConfig
        config = mock_dict_config.call_args[0][0]

        # Check file handler configuration
        assert "file" in config["handlers"]
        assert config["handlers"]["file"]["filename"] == temp_log_file

    @patch("app.core.utils.logging.logging")
    def test_setup_logging_with_phi_filter(self, mock_logging):
        """Test logging setup with PHI filtering enabled."""
        # Setup
        mock_dict_config = mock_logging.config.dictConfig

        # Call function with PHI filtering
        setup_logging(level="INFO", use_phi_filter=True)

        # Verify logging was configured
        mock_dict_config.assert_called_once()

        # Get the config passed to dictConfig
        config = mock_dict_config.call_args[0][0]

        # Check PHI filter configuration
        assert "filters" in config
        assert "phi_filter" in config["filters"]
        assert "()" in config["filters"]["phi_filter"]
        assert config["filters"]["phi_filter"]["()"] == "app.core.utils.logging.PHISanitizingFilter"
        
        # Check filter is applied to handlers
        for handler_name, handler_config in config["handlers"].items():
            if "filters" in handler_config:
                assert "phi_filter" in handler_config["filters"]

class TestPHISanitizingFilter:
    """Test suite for PHI sanitizing filter."""

    def test_filter_with_phi(self):
        """Test that the filter sanitizes PHI in log records."""
        # Create a filter
        phi_filter = PHISanitizingFilter()

        # Create a log record with potential PHI
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Patient John Doe (DOB: 01/15/1980) with SSN 123-45-6789",
            args=(),
            exc_info=None
        )
        
        # Apply filter
        result = phi_filter.filter(record)

        # Check filter passed the record
        assert result is True

        # Check message was sanitized
        assert "Patient" in record.msg
        assert "John Doe" not in record.msg
        assert "[REDACTED]" in record.msg
        assert "123-45-6789" not in record.msg

    def test_filter_without_phi(self):
        """Test that the filter doesn't modify messages without PHI."""
        # Create a filter
        phi_filter = PHISanitizingFilter()

        # Create a log record without PHI
        original_msg = "Application started successfully"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=original_msg,
            args=(),
            exc_info=None
        )
        
        # Apply filter
        result = phi_filter.filter(record)

        # Check filter passed the record
        assert result is True

        # Check message was not modified
        assert record.msg == original_msg

    def test_filter_with_phi_patterns(self):
        """Test that the filter detects specific PHI patterns."""
        # Create a filter
        phi_filter = PHISanitizingFilter()

        # Test with various PHI patterns
        test_cases = [
            ("Email: john.doe@example.com", "john.doe@example.com"),  # Email
            ("Phone: 555-123-4567", "555-123-4567"),  # Phone number
            ("DOB: 01/15/1980", "01/15/1980"),  # Date of birth
            ("SSN: 123-45-6789", "123-45-6789"),  # SSN
            ("Address: 123 Main St, Anytown, US 12345", "123 Main St"),  # Address
            ("MRN: MRN12345678", "MRN12345678"),  # Medical record number
            ("ID: ABC-12345-XYZ", "ABC-12345-XYZ"),  # ID number
        ]
        
        for message, phi in test_cases:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=message,
                args=(),
                exc_info=None
            )
            

            # Apply filter
            phi_filter.filter(record)

            # Check PHI was redacted
            assert phi not in record.msg
            assert "[REDACTED]" in record.msg


class TestStructuredJsonFormatter:
    """Test suite for structured JSON formatter."""

    def test_format_basic_record(self):
        """Test formatting a basic log record."""
        # Create formatter
        formatter = StructuredJsonFormatter()

        # Create a simple log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/app/main.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Format the record
        formatted = formatter.format(record)

        # Parse the JSON
        log_entry = json.loads(formatted)

        # Check required fields
        assert log_entry["level"] == "INFO"
        assert log_entry["logger"] == "test_logger"
        assert log_entry["message"] == "Test message"
        assert "timestamp" in log_entry
        assert "location" in log_entry
        assert log_entry["location"]["file"] == "main.py"
        assert log_entry["location"]["line"] == 42

    def test_format_with_exception(self):


        """Test formatting a record with exception information."""
        # Create formatter
        formatter = StructuredJsonFormatter()

        # Create exception info
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = pytest.importorskip("sys").exc_info()

            # Create log record with exception
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/app/main.py",
                lineno=42,
                msg="Exception occurred",
                args=(),
                exc_info=exc_info
            )

            # Format the record
            formatted = formatter.format(record)

        # Parse the JSON
        log_entry = json.loads(formatted)

        # Check exception info
        assert "exception" in log_entry
        assert log_entry["exception"]["type"] == "ValueError"
        assert log_entry["exception"]["message"] == "Test exception"
        assert "traceback" in log_entry["exception"]

    def test_format_with_extra_fields(self):


        """Test formatting a record with extra context fields."""
        # Create formatter
        formatter = StructuredJsonFormatter()

        # Create a log record with extra
        record = logging.LogRecord()
        name="test_logger",
        level=logging.INFO,
        pathname="/app/main.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None,
        

        # Add extra fields
        record.correlation_id = "abc-123"
        record.user_id = "user-456"
        record.request_path = "/api/resource"

        # Format the record
        formatted = formatter.format(record)

        # Parse the JSON
        log_entry = json.loads(formatted)

        # Check extra fields
        assert log_entry["correlation_id"] == "abc-123"
        assert log_entry["user_id"] == "user-456"
        assert log_entry["request_path"] == "/api/resource"


class TestCorrelationId:
    """Test suite for correlation ID functionality."""

    def test_get_correlation_id_default(self):
        """Test getting correlation ID when none set."""
        # Clear any existing correlation ID
        clear_correlation_id()

        # Get correlation ID
        correlation_id = get_correlation_id()

        # Should generate a new one
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0

    def test_set_and_get_correlation_id(self):
        """Test setting and getting a correlation ID."""
        # Set a specific correlation ID
        test_id = "test-correlation-123"
        set_correlation_id(test_id)

        # Get it back
        correlation_id = get_correlation_id()

        # Should match what we set
        assert correlation_id == test_id

    def test_clear_correlation_id(self):


        """Test clearing correlation ID."""
        # Set a correlation ID
        set_correlation_id("test-correlation-123")

        # Clear it
        clear_correlation_id()

        # Get a new one - should be different
        new_id = get_correlation_id()
        assert new_id != "test-correlation-123"


class TestAuditLogging:
    """Test suite for audit logging functionality."""

    @patch("app.core.utils.logging.logging.getLogger")
    def test_audit_log(self, mock_get_logger):

        """Test audit logging function."""
        # Setup mock logger
        mock_audit_logger = MagicMock()
        mock_get_logger.return_value = mock_audit_logger

        # Call audit log
        audit_log(
            action="viewed_patient_record",
            resource_id="patient-123",
            user_id="doctor-456",
            details={"access_reason": "scheduled_appointment"}
        )
        

        # Verify logger was called
        mock_get_logger.assert_called_once_with("audit")
        mock_audit_logger.info.assert_called_once()

        # Check log message
        log_call = mock_audit_logger.info.call_args[0][0]
        assert "viewed_patient_record" in log_call
        assert "patient-123" in log_call
        assert "doctor-456" in log_call

    @patch("app.core.utils.logging.logging.getLogger")
    def test_log_phi_detection(self, mock_get_logger):
        """Test PHI detection logging function."""
        # Setup mock logger
        mock_phi_logger = MagicMock()
        mock_get_logger.return_value = mock_phi_logger

        # Call PHI detection log
        log_phi_detection()
        source="api_request",
        sensitivity_score=0.85,
        detected_entities=["NAME", "SSN"],
        sanitized=True,
        request_path="/api/patients",
        user_id="doctor-456",
        

        # Verify logger was called
        mock_get_logger.assert_called_once_with("phi")
        mock_phi_logger.warning.assert_called_once()

        # Check log message
        log_call = mock_phi_logger.warning.call_args[0][0]
        assert "PHI detected" in log_call
        assert "api_request" in log_call
        assert "0.85" in log_call


class TestGetLogger:
    """Test suite for the get_logger function."""

    @patch("app.core.utils.logging.logging.getLogger")
    def test_get_logger_basic(self, mock_get_logger):

        """Test getting a basic logger."""
        # Setup mock
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Get logger
        logger = get_logger("test_module")

        # Verify correct logger was requested
        mock_get_logger.assert_called_once_with("app.test_module")

        # Should return the logger from getLogger
        assert logger == mock_logger

    @patch("app.core.utils.logging.logging.getLogger")
    def test_get_logger_with_correlation(self, mock_get_logger):
        """Test that logger adds correlation ID filter."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Set a correlation ID
        test_id = "test-correlation-456"
        set_correlation_id(test_id)

        # Get logger
        logger = get_logger("test_module")

        # Verify logger was configured with the context filter
        assert mock_logger.addFilter.called
