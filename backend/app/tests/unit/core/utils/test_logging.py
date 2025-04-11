# -*- coding: utf-8 -*-
"""
Unit tests for the HIPAA-compliant logging utility.
"""

import logging
import os
import json
import pytest
from unittest.mock import patch, MagicMock

from app.core.utils.logging import get_logger, log_execution_time, log_method_calls # Corrected imports, removed HIPAACompliantLogger, PHIRedactor, log_function_call


@pytest.mark.db_required()
class TestPHIRedactor:
    """Tests for the PHI redaction functionality."""
    
    def test_redact_email(self):
        """Test redaction of email addresses."""
        redactor = PHIRedactor()
        text = "Please contact john.doe@example.com for more information."
        redacted = redactor.redact(text)
        assert "john.doe@example.com" not in redacted
        assert "[REDACTED:email]" in redacted
    
    def test_redact_ssn(self):
        """Test redaction of Social Security Numbers."""
        redactor = PHIRedactor()
        text = "Patient SSN: 123-45-6789"
        redacted = redactor.redact(text)
        assert "123-45-6789" not in redacted
        assert "[REDACTED:ssn]" in redacted
    
    def test_redact_phone(self):
        """Test redaction of phone numbers."""
        redactor = PHIRedactor()
        text = "Call me at (555) 123-4567"
        redacted = redactor.redact(text)
        assert "(555) 123-4567" not in redacted
        assert "[REDACTED:phone]" in redacted
    
    def test_redact_multiple_phi(self):
        """Test redaction of multiple PHI elements in a single text."""
        redactor = PHIRedactor()
        text = "Patient John Doe (SSN: 123-45-6789) can be reached at john.doe@example.com or (555) 123-4567."
        redacted = redactor.redact(text)
        assert "123-45-6789" not in redacted
        assert "john.doe@example.com" not in redacted
        assert "(555) 123-4567" not in redacted
        assert "[REDACTED:ssn]" in redacted
        assert "[REDACTED:email]" in redacted
        assert "[REDACTED:phone]" in redacted
    
    def test_redact_with_custom_patterns(self):
        """Test redaction with custom patterns."""
        custom_patterns = {
            'patient_id': r'P\d{6}',
            'custom_code': r'CODE-[A-Z]{3}-\d{4}'
        }
        redactor = PHIRedactor(patterns=custom_patterns)
        text = "Patient P123456 has CODE-ABC-1234"
        redacted = redactor.redact(text)
        assert "P123456" not in redacted
        assert "CODE-ABC-1234" not in redacted
        assert "[REDACTED:patient_id]" in redacted
        assert "[REDACTED:custom_code]" in redacted


class TestHIPAACompliantLogger:
    """Tests for the HIPAA-compliant logger."""
    
    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file."""
        log_file = tmp_path / "test.log"
        return str(log_file)
    
    @pytest.fixture
    def temp_audit_file(self, tmp_path):
        """Create a temporary audit log file."""
        audit_file = tmp_path / "audit.log"
        return str(audit_file)
    
    def test_logger_initialization(self, temp_log_file):
        """Test logger initialization."""
        logger = HIPAACompliantLogger(
            name="test_logger",
            log_level="DEBUG",
            enable_console=True,
            enable_file=True,
            log_file=temp_log_file
        )
        
        assert logger.name  ==  "test_logger"
        assert logger.log_level  ==  "DEBUG"
        assert logger.enable_console is True
        assert logger.enable_file is True
        assert logger.log_file  ==  temp_log_file
        assert isinstance(logger.logger, logging.Logger)
        assert isinstance(logger.redactor, PHIRedactor)
    
    def test_logging_with_phi_redaction(self, temp_log_file):
        """Test logging with PHI redaction."""
        with patch('app.core.utils.logging.settings') as mock_settings:
            mock_settings.security.ENABLE_PHI_REDACTION = True
            mock_settings.logging.LOG_FORMAT = "%(message)s"
            
            logger = HIPAACompliantLogger(
                name="test_logger",
                log_level="DEBUG",
                enable_console=False,
                enable_file=True,
                log_file=temp_log_file
            )
            
            # Log message with PHI
            logger.info("Patient email: john.doe@example.com")
            
            # Check log file content
            with open(temp_log_file, 'r') as f:
                log_content = f.read()
                assert "john.doe@example.com" not in log_content
                assert "[REDACTED:email]" in log_content
    
    def test_audit_logging(self, temp_audit_file):
        """Test audit logging functionality."""
        with patch('app.core.utils.logging.settings') as mock_settings:
            mock_settings.security.ENABLE_PHI_REDACTION = True
            mock_settings.logging.LOG_FORMAT = "%(message)s"
            
            logger = HIPAACompliantLogger(
                name="test_logger",
                enable_audit=True,
                audit_file=temp_audit_file
            )
            
            # Create audit log entry
            logger.audit(
                action="view",
                user_id="user123",
                resource_type="patient",
                resource_id="patient456",
                details={"reason": "clinical review"},
                status="success"
            )
            
            # Check audit log content
            with open(temp_audit_file, 'r') as f:
                audit_content = f.read()
                audit_data = json.loads(audit_content.strip())
                
                assert audit_data["action"] == "view"
                assert audit_data["user_id"] == "user123"
                assert audit_data["resource_type"] == "patient"
                assert audit_data["resource_id"] == "patient456"
                assert audit_data["details"]["reason"] == "clinical review"
                assert audit_data["status"] == "success"
    
    def test_log_function_call_decorator(self):
        """Test the log_function_call decorator."""
        mock_logger = MagicMock(spec=HIPAACompliantLogger)
        
        @log_function_call(logger=mock_logger)
    def test_function(a, b):
            return a + b
        
        result = test_function(1, 2)
        
        assert result  ==  3
        assert mock_logger.debug.call_count  ==  2
        mock_logger.debug.assert _any_call("Calling test_function")
        # Second call contains execution time which we can't predict exactly
        assert "test_function completed in" in mock_logger.debug.call_args_list[1][0][0]
    
    def test_log_function_call_with_exception(self):
        """Test the log_function_call decorator with exception."""
        mock_logger = MagicMock(spec=HIPAACompliantLogger)
        
        @log_function_call(logger=mock_logger)
    def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        assert mock_logger.debug.call_count  ==  1
        assert mock_logger.error.call_count  ==  1
        mock_logger.debug.assert _called_with("Calling failing_function")
        assert "failing_function failed after" in mock_logger.error.call_args[0][0]
        assert "Test error" in mock_logger.error.call_args[0][0]
