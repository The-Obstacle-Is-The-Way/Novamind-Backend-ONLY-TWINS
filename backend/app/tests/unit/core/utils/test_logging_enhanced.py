# -*- coding: utf-8 -*-
"""
Enhanced unit tests for the HIPAA-compliant logging utility.

This test suite provides comprehensive coverage for the logging module,
focusing on HIPAA compliance, PHI protection, and proper audit trails.
"""

import logging
import os
import json
import tempfile
import time
import asyncio
import pytest
from unittest.mock import patch, MagicMock, mock_open, call

from app.core.utils.logging import get_logger # Corrected import, removed HIPAACompliantLogger, audit_log


class TestHIPAACompliantLogger:
    """Comprehensive tests for the HIPAACompliantLogger class."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create a mock settings object."""
        with patch('app.core.utils.logging.settings') as mock_settings:
            # Configure default settings
            mock_settings.DEBUG = True
            mock_settings.logging.LOG_TO_CONSOLE = True
            mock_settings.logging.LOG_TO_FILE = True
            mock_settings.logging.LOG_FILE_PATH = "test.log"
            mock_settings.logging.ENABLE_AUDIT_LOGGING = True
            mock_settings.logging.LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            yield mock_settings
    
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file."""
        fd, path = tempfile.mkstemp()
        try:
            os.close(fd)
            yield path
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_logger_initialization(self, mock_settings):
        """Test logger initialization with various configurations."""
        # Test with default settings
        logger = HIPAACompliantLogger("test_logger")
        assert logger.logger.level == logging.DEBUG
        assert len(logger.logger.handlers) >= 1
        
        # Test with file logging disabled
        mock_settings.logging.LOG_TO_FILE = False
        logger = HIPAACompliantLogger("test_logger")
        assert any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) 
                  for h in logger.logger.handlers)
        
        # Test with console logging disabled
        mock_settings.logging.LOG_TO_FILE = True
        mock_settings.logging.LOG_TO_CONSOLE = False
        logger = HIPAACompliantLogger("test_logger")
        assert any(isinstance(h, logging.FileHandler) for h in logger.logger.handlers)
        assert not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) 
                      for h in logger.logger.handlers)
    
    def test_get_formatter(self):
        """Test the formatter creation."""
        logger = HIPAACompliantLogger("test_logger")
        formatter = logger._get_formatter()
        assert isinstance(formatter, logging.Formatter)
        assert formatter._fmt == '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def test_mask_phi(self):
        """Test PHI masking in log messages."""
        logger = HIPAACompliantLogger("test_logger")
        
        # Test email masking
        email_msg = "Contact us at patient@example.com"
        masked_email = logger._mask_phi(email_msg)
        assert "patient@example.com" not in masked_email
        
        # Test SSN masking
        ssn_msg = "Patient SSN: 123-45-6789"
        masked_ssn = logger._mask_phi(ssn_msg)
        assert "123-45-6789" not in masked_ssn
        
        # Test phone masking
        phone_msg = "Call at (555) 123-4567"
        masked_phone = logger._mask_phi(phone_msg)
        assert "(555) 123-4567" not in masked_phone
    
    def test_logging_methods(self, mock_settings, temp_log_file):
        """Test all logging level methods."""
        mock_settings.logging.LOG_FILE_PATH = temp_log_file
        
        with patch.object(HIPAACompliantLogger, '_log') as mock_log:
            logger = HIPAACompliantLogger("test_logger")
            
            # Test debug method
            logger.debug("Debug message", {"key": "value"})
            mock_log.assert_called_with(logging.DEBUG, "Debug message", {"key": "value"})
            
            # Test info method
            logger.info("Info message", {"key": "value"})
            mock_log.assert_called_with(logging.INFO, "Info message", {"key": "value"})
            
            # Test warning method
            logger.warning("Warning message", {"key": "value"})
            mock_log.assert_called_with(logging.WARNING, "Warning message", {"key": "value"})
            
            # Test error method
            logger.error("Error message", {"key": "value"})
            mock_log.assert_called_with(logging.ERROR, "Error message", {"key": "value"})
            
            # Test critical method
            logger.critical("Critical message", {"key": "value"})
            mock_log.assert_called_with(logging.CRITICAL, "Critical message", {"key": "value"})
    
    def test_create_audit_log(self):
        """Test audit log creation."""
        logger = HIPAACompliantLogger("test_logger")
        
        # Basic audit log
        audit_log = logger._create_audit_log(
            logging.INFO, 
            "Test message",
            {"user": "test_user"}
        )
        
        assert audit_log["level"] == "INFO"
        assert audit_log["message"] == "Test message"
        assert audit_log["source"] == "test_logger"
        assert "timestamp" in audit_log
        assert audit_log["extra"]["user"] == "test_user"
        
        # Audit log with PHI
        phi_audit_log = logger._create_audit_log(
            logging.INFO,
            "Patient email: john@example.com",
            {"ssn": "123-45-6789"}
        )
        
        assert "john@example.com" not in phi_audit_log["message"]
        assert "123-45-6789" not in phi_audit_log["extra"]["ssn"]
    
    def test_store_audit_log(self, mock_settings, temp_log_file):
        """Test audit log storage."""
        mock_settings.logging.ENABLE_AUDIT_LOGGING = True
        
        # Create a mock for _store_audit_log
        with patch.object(HIPAACompliantLogger, '_store_audit_log') as mock_store:
            logger = HIPAACompliantLogger("test_logger")
            
            # Create and store an audit log
            audit_data = {
                "timestamp": "2025-03-27T12:00:00",
                "level": "INFO",
                "message": "Test audit log",
                "source": "test_logger"
            }
            
            logger._store_audit_log(audit_data)
            mock_store.assert_called_once_with(audit_data)
    
    def test_log_method(self, mock_settings):
        """Test the base _log method."""
        with patch.object(HIPAACompliantLogger, '_create_audit_log') as mock_create_audit:
            with patch.object(HIPAACompliantLogger, '_store_audit_log') as mock_store_audit:
                logger = HIPAACompliantLogger("test_logger")
                
                # Mock the underlying logger
                logger.logger = MagicMock()
                
                # Test _log method
                logger._log(logging.INFO, "Test message", {"extra": "value"})
                
                # Verify audit log was created
                mock_create_audit.assert_called_once_with(
                    logging.INFO, "Test message", {"extra": "value"}
                )
                
                # Verify logger was called
                logger.logger.log.assert_called_once()
                
                # Verify audit log was stored
                mock_store_audit.assert_called_once()
    
    def test_integration_with_file(self, mock_settings, temp_log_file):
        """Test integration with file logging."""
        mock_settings.logging.LOG_FILE_PATH = temp_log_file
        mock_settings.logging.LOG_TO_FILE = True
        mock_settings.logging.LOG_TO_CONSOLE = False
        
        logger = HIPAACompliantLogger("test_logger")
        
        # Log a test message
        test_message = "Test message for file logging"
        logger.info(test_message)
        
        # Verify the message was written to the file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
            assert test_message in log_content


class TestAuditLogDecorator:
    """Tests for the audit_log decorator."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        mock = MagicMock(spec=HIPAACompliantLogger)
        with patch('app.core.utils.logging.HIPAACompliantLogger', return_value=mock):
            yield mock
    
    def test_sync_function_success(self, mock_logger):
        """Test the decorator on a synchronous function that succeeds."""
        # Define a sync function with the decorator
        @audit_log("test_event")
        def test_function(a, b):
            return a + b
        
        # Call the decorated function
        result = test_function(2, 3)
        
        # Verify the result
        assert result == 5
        
        # Verify logging
        mock_logger.info.assert_called_once()
        assert "test_event completed successfully" in mock_logger.info.call_args[0][0]
    
    def test_sync_function_error(self, mock_logger):
        """Test the decorator on a synchronous function that fails."""
        # Define a sync function that raises an exception
        @audit_log("test_event")
        def failing_function():
            raise ValueError("Test error")
        
        # Call the decorated function and expect an exception
        with pytest.raises(ValueError):
            failing_function()
        
        # Verify error logging
        mock_logger.error.assert_called_once()
        assert "test_event failed" in mock_logger.error.call_args[0][0]
        assert "Test error" in str(mock_logger.error.call_args[0][1])
    
    @pytest.mark.asyncio
    async def test_async_function_success(self, mock_logger):
        """Test the decorator on an asynchronous function that succeeds."""
        # Define an async function with the decorator
        @audit_log("test_async_event")
        async def test_async_function(a, b):
            await asyncio.sleep(0.01)  # Simulate async work
            return a + b
        
        # Call the decorated async function
        result = await test_async_function(2, 3)
        
        # Verify the result
        assert result == 5
        
        # Verify logging
        mock_logger.info.assert_called_once()
        assert "test_async_event completed successfully" in mock_logger.info.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_async_function_error(self, mock_logger):
        """Test the decorator on an asynchronous function that fails."""
        # Define an async function that raises an exception
        @audit_log("test_async_event")
        async def failing_async_function():
            await asyncio.sleep(0.01)  # Simulate async work
            raise ValueError("Async test error")
        
        # Call the decorated async function and expect an exception
        with pytest.raises(ValueError):
            await failing_async_function()
        
        # Verify error logging
        mock_logger.error.assert_called_once()
        assert "test_async_event failed" in mock_logger.error.call_args[0][0]
        assert "Async test error" in str(mock_logger.error.call_args[0][1])