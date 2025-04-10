"""
Test script for the logger module.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.logging.logger import get_logger, format_log_message

class TestLogger:
    """Test cases for the logger module."""
    
    def test_get_logger(self):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
    
    def test_format_log_message(self):
        """Test that format_log_message correctly formats log messages."""
        # Test basic message formatting
        formatted_message = format_log_message(
            message="Test message",
            source="test_logger",
            additional_data={"test_key": "test_value"}
        )
        
        # Verify the structure of the formatted message
        assert "Test message" in formatted_message
        assert "test_logger" in formatted_message
        assert "test_key" in formatted_message
        assert "test_value" in formatted_message
        
    @patch('app.infrastructure.logging.logger.logging')
    def test_logger_sanitizes_phi(self, mock_logging):
        """Test that the logger sanitizes PHI in log messages."""
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        
        logger = get_logger("test_phi_logger")
        
        # Log a message containing PHI
        logger.info("Patient John Doe (DOB: 01/01/1980) has a new medication")
        
        # Verify that PHI was sanitized in the logged message
        args, _ = mock_logger.info.call_args
        logged_message = args[0]
        assert "John Doe" not in logged_message
        assert "01/01/1980" not in logged_message
        assert "[REDACTED]" in logged_message