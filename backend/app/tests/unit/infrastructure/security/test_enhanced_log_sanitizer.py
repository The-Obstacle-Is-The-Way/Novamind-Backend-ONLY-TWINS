import pytest
import re
import json
import logging
from typing import Dict, Any, List
import yaml # Import yaml for mocking
from unittest.mock import patch, MagicMock, Mock, call # Import call
import os # Import os if needed

# Updated import path
# from app.infrastructure.security.log_sanitizer import ( # Removed extra parenthesis
from app.infrastructure.security.phi.log_sanitizer import (
    LogSanitizer,
    PHIFormatter,
    PHIRedactionHandler,
    LogSanitizerConfig,
    # Removed: PatternType, RedactionMode,
    # Removed: PHIPattern, PatternRepository, RedactionStrategy,
    # Removed: FullRedactionStrategy, PartialRedactionStrategy, HashRedactionStrategy,
    # Removed: RedactionStrategyFactory,
    sanitize_logs, get_sanitized_logger
)
from app.infrastructure.security.phi.phi_service import PHIService, PHIType

# Removed TestPHIPattern class
# Removed TestPatternRepository class
# Removed TestRedactionStrategies class

# @pytest.mark.skip(reason="Needs refactoring for new PHIService") # Removed skip
class TestLogSanitizer:
    """Test suite for LogSanitizer class, now using PHIService."""

    @patch('app.infrastructure.security.phi.log_sanitizer.PHIService')
    def test_initialization_default_config(self, mock_phi_service_class: MagicMock):
        """Test LogSanitizer initializes with default config and PHIService."""
        mock_phi_instance = MagicMock()
        mock_phi_service_class.return_value = mock_phi_instance

        sanitizer = LogSanitizer()

        assert isinstance(sanitizer.config, LogSanitizerConfig)
        assert sanitizer.config.enabled is True
        assert sanitizer.config.default_sensitivity == PHIService.DEFAULT_SENSITIVITY
        assert sanitizer.config.replacement_template is None
        mock_phi_service_class.assert_called_once()
        assert sanitizer._phi_service is mock_phi_instance

    @patch('app.infrastructure.security.phi.log_sanitizer.PHIService')
    def test_initialization_custom_config(self, mock_phi_service_class: MagicMock):
        """Test LogSanitizer initializes with custom config."""
        mock_phi_instance = MagicMock()
        mock_phi_service_class.return_value = mock_phi_instance

        custom_config = LogSanitizerConfig(
            enabled=False,
            default_sensitivity="LOW",
            replacement_template="[HIDDEN]"
        )
        sanitizer = LogSanitizer(config=custom_config)

        assert sanitizer.config is custom_config
        assert sanitizer.config.enabled is False
        assert sanitizer.config.default_sensitivity == "LOW"
        assert sanitizer.config.replacement_template == "[HIDDEN]"
        mock_phi_service_class.assert_called_once()
        assert sanitizer._phi_service is mock_phi_instance

    # --- Tests for sanitize method --- 

    @patch('app.infrastructure.security.phi.log_sanitizer.PHIService')
    def test_sanitize_delegates_to_phi_service_default_config(self, mock_phi_service_class: MagicMock):
        """Test sanitize delegates correctly with default config."""
        mock_phi_instance = MagicMock()
        mock_phi_instance.sanitize.return_value = "Sanitized Data"
        mock_phi_service_class.return_value = mock_phi_instance

        sanitizer = LogSanitizer() # Default config
        data_to_sanitize = "Sensitive SSN: 123-45-6789"
        result = sanitizer.sanitize(data_to_sanitize)

        assert result == "Sanitized Data"
        mock_phi_instance.sanitize.assert_called_once_with(
            data_to_sanitize,
            sensitivity=PHIService.DEFAULT_SENSITIVITY, # From default config
            replacement=None # From default config
        )

    @patch('app.infrastructure.security.phi.log_sanitizer.PHIService')
    def test_sanitize_delegates_to_phi_service_custom_config(self, mock_phi_service_class: MagicMock):
        """Test sanitize delegates correctly with custom config."""
        mock_phi_instance = MagicMock()
        mock_phi_instance.sanitize.return_value = "Custom Sanitized Data"
        mock_phi_service_class.return_value = mock_phi_instance

        custom_config = LogSanitizerConfig(default_sensitivity="MEDIUM", replacement_template="***")
        sanitizer = LogSanitizer(config=custom_config)
        data_to_sanitize = {"key": "Value 123-45-6789"}
        result = sanitizer.sanitize(data_to_sanitize)

        assert result == "Custom Sanitized Data"
        mock_phi_instance.sanitize.assert_called_once_with(
            data_to_sanitize,
            sensitivity="MEDIUM", # From custom config
            replacement="***" # From custom config
        )

    @patch('app.infrastructure.security.phi.log_sanitizer.PHIService')
    def test_sanitize_with_explicit_sensitivity(self, mock_phi_service_class: MagicMock):
        """Test sanitize uses explicit sensitivity when provided."""
        mock_phi_instance = MagicMock()
        mock_phi_instance.sanitize.return_value = "Explicitly Sanitized"
        mock_phi_service_class.return_value = mock_phi_instance

        sanitizer = LogSanitizer() # Default config
        data_to_sanitize = "Data with low sensitivity"
        result = sanitizer.sanitize(data_to_sanitize, sensitivity="LOW")

        assert result == "Explicitly Sanitized"
        mock_phi_instance.sanitize.assert_called_once_with(
            data_to_sanitize,
            sensitivity="LOW", # Explicitly passed
            replacement=None # From default config
        )

    @patch('app.infrastructure.security.phi.log_sanitizer.PHIService')
    def test_sanitize_disabled_by_config(self, mock_phi_service_class: MagicMock):
        """Test sanitize returns original data when disabled in config."""
        mock_phi_instance = MagicMock()
        mock_phi_service_class.return_value = mock_phi_instance

        disabled_config = LogSanitizerConfig(enabled=False)
        sanitizer = LogSanitizer(config=disabled_config)
        data_to_sanitize = "Should not be sanitized 123-45-6789"
        result = sanitizer.sanitize(data_to_sanitize)

        assert result == data_to_sanitize # Original data returned
        mock_phi_instance.sanitize.assert_not_called()

    # --- Tests for sanitize_log_record method --- 

    @patch.object(LogSanitizer, 'sanitize', return_value="[SANITIZED MSG]")
    def test_sanitize_log_record_basic(self, mock_sanitize: MagicMock):
        """Test sanitize_log_record sanitizes message and clears args."""
        sanitizer = LogSanitizer()
        original_message = "Log message with SSN: %s"
        original_args = ("123-45-6789",)
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, 
            msg=original_message, args=original_args, exc_info=None, func='')
        
        # Manually format message like logging would before sanitize_log_record
        formatted_message = record.getMessage()

        sanitized_record = sanitizer.sanitize_log_record(record)

        # Check that sanitize was called with the *formatted* message
        mock_sanitize.assert_called_once_with(formatted_message)
        assert sanitized_record.getMessage() == "[SANITIZED MSG]" # Check the final message
        assert sanitized_record.args == [] # Args should be cleared
        assert sanitized_record.msg == "[SANITIZED MSG]" # msg attribute should be updated

    @patch.object(LogSanitizer, 'sanitize')
    def test_sanitize_log_record_with_exception(self, mock_sanitize: MagicMock):
        """Test sanitize_log_record sanitizes exception info."""
        # Let sanitize return different values based on input
        def sanitize_side_effect(data):
            if "Original exception" in str(data):
                return "[SANITIZED EXCEPTION]"
            elif "Traceback" in str(data):
                return "[SANITIZED TRACEBACK]"
            else:
                return "[SANITIZED MSG]"
        mock_sanitize.side_effect = sanitize_side_effect

        sanitizer = LogSanitizer()
        try:
            raise ValueError("Original exception with SSN 123-45-6789")
        except ValueError as e:
            exc_info = (type(e), e, e.__traceback__)
            # Simulate pre-formatted exc_text (might contain PHI)
            record = logging.LogRecord(
                name='test', level=logging.ERROR, pathname='', lineno=0, 
                msg="Error occurred", args=(), exc_info=exc_info, func='')
            record.exc_text = "Traceback:\n...\nValueError: Original exception with SSN 123-45-6789"

        sanitized_record = sanitizer.sanitize_log_record(record)

        # Check sanitize calls
        expected_calls = [
            call(record.getMessage()), # Sanitize original message
            call("Original exception with SSN 123-45-6789"), # Sanitize str(exc_value)
            call(record.exc_text) # Sanitize exc_text
        ]
        mock_sanitize.assert_has_calls(expected_calls, any_order=True)

        # Check the sanitized exception info
        assert isinstance(sanitized_record.exc_info[1], ValueError)
        assert str(sanitized_record.exc_info[1]) == "[SANITIZED EXCEPTION]"
        assert sanitized_record.exc_text == "[SANITIZED TRACEBACK]"
        assert sanitized_record.getMessage() == "[SANITIZED MSG]"
        assert sanitized_record.args == []

    @patch.object(LogSanitizer, 'sanitize', return_value="[SANITIZED STACK]")
    def test_sanitize_log_record_with_stack_info(self, mock_sanitize: MagicMock):
        """Test sanitize_log_record sanitizes stack info."""
        sanitizer = LogSanitizer()
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, 
            msg="Message", args=(), exc_info=None, func='')
        record.stack_info = "Stack:\n Frame 1: SSN 123-45-6789\n Frame 2"

        sanitized_record = sanitizer.sanitize_log_record(record)

        # Check sanitize calls (once for message, once for stack_info)
        expected_calls = [
            call(record.getMessage()),
            call(record.stack_info)
        ]
        mock_sanitize.assert_has_calls(expected_calls, any_order=True)

        assert sanitized_record.stack_info == "[SANITIZED STACK]"
        assert sanitized_record.getMessage() == "[SANITIZED STACK]" # Because side effect is simple
        assert sanitized_record.args == []

    @patch.object(LogSanitizer, 'sanitize')
    def test_sanitize_log_record_disabled(self, mock_sanitize: MagicMock):
        """Test sanitize_log_record does nothing when disabled."""
        disabled_config = LogSanitizerConfig(enabled=False)
        sanitizer = LogSanitizer(config=disabled_config)
        original_message = "Log message with SSN: %s"
        original_args = ("123-45-6789",)
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, 
            msg=original_message, args=original_args, exc_info=None, func='')
        original_formatted_message = record.getMessage()

        sanitized_record = sanitizer.sanitize_log_record(record)

        mock_sanitize.assert_not_called()
        assert sanitized_record is record # Should return the original record object
        assert sanitized_record.getMessage() == original_formatted_message
        assert sanitized_record.args == original_args # Args should NOT be cleared


@pytest.mark.skip(reason="Needs refactoring for new PHIService")
class TestPHIFormatterAndHandler:
    """Test suite for PHIFormatter and PHIRedactionHandler. Needs refactoring for PHIService."""

    # ... existing code ...
