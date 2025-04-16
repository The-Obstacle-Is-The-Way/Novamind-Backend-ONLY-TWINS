"""
Test suite for enhanced log sanitizer implementation.

These tests verify HIPAA-compliant PHI sanitization in logs.
"""

import pytest
import re
import json
import logging
import io
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock, Mock

from app.infrastructure.security.phi.log_sanitizer import (
    LogSanitizer,
    LogSanitizerConfig,
    PHIFormatter,
    get_sanitized_logger
)
from app.infrastructure.security.phi.phi_service import PHIService

class TestPHIPattern:
    """Test suite for PHIPattern class."""

    def test_phi_pattern_matches_regex(self):
        """Test regex pattern matching."""
        pattern = PHIPattern(
            name="SSN",
            pattern=r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            type=PatternType.REGEX,
            priority=10,
        )

        # Should match
        assert pattern.matches("SSN: 123-45-6789")
        assert pattern.matches("123-45-6789")
        assert pattern.matches("SSN is 123 45 6789")

        # Should not match
        assert not pattern.matches("12-345-678")
        assert not pattern.matches("Not an SSN")
        assert not pattern.matches("")
        assert not pattern.matches(None)

    @pytest.mark.standalone()
    def test_phi_pattern_matches_exact(self):
        """Test exact pattern matching."""
        pattern = PHIPattern(
            name="Sensitive Key",
            pattern="patient_id",
            type=PatternType.EXACT,
            priority=10,
        )

        # Should match
        assert pattern.matches("patient_id")

        # Should not match
        assert not pattern.matches("patient_identifier")
        assert not pattern.matches("id")
        assert not pattern.matches("PATIENT_ID")  # Case sensitive
        assert not pattern.matches("")
        assert not pattern.matches(None)

    def test_phi_pattern_matches_fuzzy(self):
        """Test fuzzy pattern matching."""
        pattern = PHIPattern(
            name="Medical Term",
            pattern="diagnosis",
            type=PatternType.FUZZY,
            priority=10,
        )

        # Should match (with fuzzy logic)
        assert pattern.matches("diagnoses")
        assert pattern.matches("diagnostic")
        assert pattern.matches("diagnosis")

        # Should not match
        assert not pattern.matches("dia")  # Too short/different
        assert not pattern.matches("")
        assert not pattern.matches(None)

class TestRedactionStrategies:
    """Test suite for redaction strategies."""

    def test_full_redaction(self):
        """Test full redaction strategy."""
        strategy = FullRedactionStrategy()

        assert strategy.redact("123-45-6789") == "[REDACTED]"
        assert strategy.redact("John Doe") == "[REDACTED]"
        assert strategy.redact("") == "[REDACTED]"
        assert strategy.redact(None) == "[REDACTED]"

    def test_partial_redaction(self):
        """Test partial redaction strategy."""
        strategy = PartialRedactionStrategy()

        # Test with SSN-like pattern
        ssn = "123-45-6789"
        redacted_ssn = strategy.redact(ssn)
        # First few and last few chars should be preserved
        assert ssn[:2] in redacted_ssn
        assert ssn[-2:] in redacted_ssn
        assert "***" in redacted_ssn

        # Test with name
        name = "John Doe"
        redacted_name = strategy.redact(name)
        assert name[0] in redacted_name  # First char preserved
        assert name[-1] in redacted_name  # Last char preserved
        assert "***" in redacted_name

        # Test with short string
        assert strategy.redact("a") == "a"  # Too short to redact

        # Test with empty/None
        assert strategy.redact("") == ""
        assert strategy.redact(None) == ""

    def test_hash_redaction(self):
        """Test hash redaction strategy."""
        strategy = HashRedactionStrategy()

        val1 = "123-45-6789"
        val2 = "123-45-6789"  # Same as val1
        val3 = "987-65-4321"  # Different

        hash1 = strategy.redact(val1)
        hash2 = strategy.redact(val2)
        hash3 = strategy.redact(val3)

        # Same input should produce same hash
        assert hash1 == hash2
        # Different input should produce different hash
        assert hash1 != hash3
        # Hash should be a hex string
        assert re.match(r"^[0-9a-f]+$", hash1)

        # Test with empty/None
        assert strategy.redact("") == ""
        assert strategy.redact(None) == ""

class TestRedactionStrategyFactory:
    """Test suite for redaction strategy factory."""

    def test_strategy_factory(self):
        """Test RedactionStrategyFactory creates correct strategies."""
        factory = RedactionStrategyFactory()

        full = RedactionStrategyFactory.create_strategy(RedactionMode.FULL, SanitizerConfig())
        partial = RedactionStrategyFactory.create_strategy(RedactionMode.PARTIAL, SanitizerConfig())
        hash_strategy = RedactionStrategyFactory.create_strategy(RedactionMode.HASH, SanitizerConfig())

        assert isinstance(full, FullRedactionStrategy)
        assert isinstance(partial, PartialRedactionStrategy)
        assert isinstance(hash_strategy, HashRedactionStrategy)

        # Test with invalid mode should default to FULL
        default = RedactionStrategyFactory.create_strategy("INVALID", SanitizerConfig())
        assert isinstance(default, FullRedactionStrategy)

class TestSanitizerConfig:
    """Test the SanitizerConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SanitizerConfig()

        # Default modes should be set
        assert config.redaction_mode == RedactionMode.FULL
        # Should have some default patterns (sensitive field names)
        assert len(config.sensitive_field_names) > 0

        # Load built-in patterns - This method doesn't exist
        # config.load_builtin_patterns()
        # assert len(config.patterns) > 0

    def test_custom_config(self):
        """Test creating a config with custom settings."""
        custom_patterns = [
            PHIPattern(
                name="SSN",
                pattern=r"\d{3}-\d{2}-\d{4}",
                type=PatternType.REGEX,
                priority=10,
            ),
            PHIPattern(
                name="Name",
                pattern=r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
                type=PatternType.REGEX,
                priority=5,
            ),
        ]

        config = SanitizerConfig(
            redaction_mode=RedactionMode.PARTIAL,
        )

        assert config.redaction_mode == RedactionMode.PARTIAL

class TestPatternRepository:
    """Test suite for PatternRepository class."""

    def test_pattern_repository(self):
        """Test PatternRepository functionality."""
        repo = PatternRepository()

        # Add a pattern
        pattern1 = PHIPattern(
            name="TestSSN",  # Use unique name
            pattern=r"\d{3}-\d{2}-\d{4}",
            type=PatternType.REGEX,
            priority=10,
        )
        repo.add_pattern(pattern1)

        # Add another pattern
        pattern2 = PHIPattern(
            name="TestName",  # Use unique name
            pattern=r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
            type=PatternType.REGEX,
            priority=5,
        )
        repo.add_pattern(pattern2)

        # Default patterns (8) + added patterns (2) = 10
        assert len(repo.get_patterns()) == 10

        # Get by name (using unique test names)
        assert repo.get_pattern_by_name("TestSSN") == pattern1
        assert repo.get_pattern_by_name("TestName") == pattern2
        assert repo.get_pattern_by_name("Nonexistent") is None

        # Remove pattern (using unique test name)
        repo.remove_pattern("TestSSN") # Remove the test's SSN pattern
        # Default patterns (8) + remaining test pattern (1) = 9
        assert len(repo.get_patterns()) == 9
        assert repo.get_pattern_by_name("TestSSN") is None # Test SSN removed

class TestLogSanitizer:
    """Test the LogSanitizer class."""

    def test_sanitize_text(self):
        """Test sanitizing plain text."""
        # Config to recognize 'John' and 'Doe' based on case (sensitive_field_names isn't regex)
        # But default patterns include 'name' which might catch it
        config = SanitizerConfig(sensitive_field_names=["name", "John", "Doe"]) 
        # repository = PatternRepository(config) # LogSanitizer creates its own
        # Add a simple name pattern for testing
        # repository.add_pattern(PHIPattern(name="Name", pattern=r"\b[A-Z][a-z]+\b", type=PatternType.REGEX))
        
        sanitizer = LogSanitizer(config=config)
        text = "User John Doe logged in."
        sanitized_text = sanitizer.sanitize(text)
        # Expect redaction based on sensitive field names / built-in patterns
        # When context_key is None (plain string), label comes from pattern name 'NAME'
        assert sanitized_text == "User [REDACTED:NAME] [REDACTED:NAME] logged in." # Use pattern name 'NAME'

        # Test with a different redaction mode via config
        config_partial = SanitizerConfig(redaction_mode=RedactionMode.PARTIAL, partial_redaction_length=1, sensitive_field_names=["name", "John", "Doe"]) 
        sanitizer_partial = LogSanitizer(config=config_partial)
        sanitized_text_partial = sanitizer_partial.sanitize(text)
        # Assuming partial redaction shows first letter: J*** D**
        # Note: Exact output depends on PartialRedactionStrategy implementation detail
        # This assertion might need adjustment based on the strategy's behavior.
        assert "J***" in sanitized_text_partial # Check based on 'John'
        assert "D**" in sanitized_text_partial # Check based on 'Doe'
        assert "logged in" in sanitized_text_partial

    def test_sanitize_object(self):
        """Test sanitizing dictionary objects."""
        config = SanitizerConfig(sensitive_field_names=["name", "ssn"]) 
        # repository = PatternRepository(config) # LogSanitizer creates its own
        # repository.add_pattern(PHIPattern(name="SSN", pattern=r"\d{3}-\d{2}-\d{4}", type=PatternType.REGEX))
        
        sanitizer = LogSanitizer(config=config)
        data = {
            "user": {
                "name": "Alice Smith",
                "id": 123
            },
            "details": {
                "ssn": "123-45-6789", # This should be caught by built-in SSN pattern
                "unrelated": "value"
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        sanitized_data = sanitizer.sanitize(data)
        
        # Assertions check the dictionary content directly
        assert isinstance(sanitized_data, dict)
        assert sanitized_data['user']['name'] == '[REDACTED:name]' # Label from sensitive_field_names
        assert sanitized_data['user']['id'] == 123
        assert sanitized_data['details']['ssn'] == '[REDACTED:ssn]' # Label from sensitive_field_names
        assert sanitized_data['details']['unrelated'] == 'value'
        assert sanitized_data['timestamp'] == '2024-01-01T12:00:00Z'
        
        # Test case insensitivity for keys if configured
        config_insensitive = SanitizerConfig(sensitive_field_names=["name"], sensitive_keys_case_sensitive=False)
        sanitizer_insensitive = LogSanitizer(config=config_insensitive)
        data_upper = {"NAME": "Bob Jones"}
        sanitized_upper = sanitizer_insensitive.sanitize(data_upper)
        assert isinstance(sanitized_upper, dict)
        assert sanitized_upper['NAME'] == '[REDACTED:name]' # Key remains uppercase, label uses config name

    def test_sanitize_with_different_modes(self):
        """Test sanitization using different redaction modes per pattern."""
        # Config needs sensitive names for this test to work without explicit patterns
        config = SanitizerConfig(sensitive_field_names=["ssn", "John", "Doe", "name"])
        # repository = PatternRepository(config) # LogSanitizer creates its own
        
        # Define patterns with specific redaction modes if needed (though typically mode is global via config)
        # PHIPattern itself does *not* define the redaction mode.
        # The mode comes from SanitizerConfig or potentially overrides later.
        # ssn_pattern = PHIPattern(
        #     name="SSN", 
        #     pattern=r"\d{3}-\d{2}-\d{4}", 
        #     type=PatternType.REGEX
        #     # redaction_mode=RedactionMode.HASH # Incorrect: PHIPattern doesn't take mode
        # )
        # name_pattern = PHIPattern(
        #     name="Name", 
        #     pattern=r"\b[A-Z][a-z]+\b", 
        #     type=PatternType.REGEX
        #     # redaction_mode=RedactionMode.PARTIAL # Incorrect
        # )
        
        # repository.add_pattern(ssn_pattern)
        # repository.add_pattern(name_pattern)
        
        sanitizer = LogSanitizer(config=config)
        text = "SSN 123-45-6789 belongs to John Doe."
        
        # Default: Full Redaction
        sanitized_full = sanitizer.sanitize(text)
        assert sanitized_full == "SSN [REDACTED:SSN] belongs to [REDACTED:name] [REDACTED:name]." # Relies on built-in SSN and name patterns/logic

        # Test Partial Redaction via config
        config_partial = SanitizerConfig(redaction_mode=RedactionMode.PARTIAL, sensitive_field_names=["ssn", "John", "Doe", "name"]) 
        sanitizer_partial = LogSanitizer(config=config_partial)
        sanitized_partial = sanitizer_partial.sanitize(text)
        # Exact output depends on partial strategy, check for presence of redaction marker
        # And that original sensitive terms are gone
        assert config_partial.redaction_marker in sanitized_partial
        assert "123-45-6789" not in sanitized_partial
        assert "John" not in sanitized_partial
        assert "Doe" not in sanitized_partial

        # Test Hash Redaction via config
        config_hash = SanitizerConfig(redaction_mode=RedactionMode.HASH, sensitive_field_names=["ssn", "John", "Doe", "name"]) 
        sanitizer_hash = LogSanitizer(config=config_hash)
        sanitized_hash = sanitizer_hash.sanitize(text)
        # Hash output is deterministic but complex to predict here, check marker
        # And that original sensitive terms are gone
        assert config_hash.redaction_marker in sanitized_hash 
        assert "123-45-6789" not in sanitized_hash
        assert "John Doe" not in sanitized_hash
        assert "John" not in sanitized_hash
        assert "Doe" not in sanitized_hash

class TestPHIFormatter:
    """Test suite for PHIFormatter class."""

    def test_format_with_sanitizer(self):
        """Test formatting with sanitizer."""
        # Create a mock sanitizer
        mock_sanitizer = MagicMock(spec=LogSanitizer)
        mock_sanitizer.sanitize.side_effect = (
            lambda x: "[CLEANED]" if isinstance(x, str) and "PHI" in x else x
        )

        formatter = PHIFormatter(sanitizer=mock_sanitizer)

        # Test with PHI in message
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Message with PHI data",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "Message with [CLEANED] data" in formatted

        # Test with PHI in args
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Message with %s",
            args=("PHI data",),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "Message with [CLEANED]" in formatted

class TestPHIRedactionHandler:
    """Test suite for PHIRedactionHandler class."""

    def test_emit_with_sanitizer(self):
        """Test emit with sanitizer."""
        # Create a mock handler
        mock_handler = MagicMock(spec=logging.Handler)

        # Create a mock sanitizer
        mock_sanitizer = MagicMock(spec=LogSanitizer)
        mock_sanitizer.sanitize.side_effect = (
            lambda x: "[SANITIZED]" if "PHI" in str(x) else x
        )

        # Create the PHI redaction handler
        phi_handler = PHIRedactionHandler(handler=mock_handler, sanitizer=mock_sanitizer)

        # Test with PHI in message
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Message with PHI data",
            args=(),
            exc_info=None,
        )

        phi_handler.emit(record)

        # Assert that the mock handler's emit was called with a sanitized
        # record
        assert mock_handler.emit.called
        sanitized_record = mock_handler.emit.call_args[0][0]
        assert "PHI" not in sanitized_record.msg
        assert "[SANITIZED]" in sanitized_record.msg

class TestSanitizedLogger:
    """Tests for the get_sanitized_logger utility."""

    def setup_method(self):
        self.logger = get_sanitized_logger("test_sanitized_logger")
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.formatter = logging.Formatter('%(message)s')
        self.handler.setFormatter(self.formatter)
        
        # Add handler only if not already present
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            self.logger.addHandler(self.handler)

    def teardown_method(self):
        self.logger.removeHandler(self.handler)

    def test_sanitized_logger_logs_non_phi(self):
        message = "This is a normal log message."
        self.logger.info(message)
        log_output = self.stream.getvalue().strip()
        assert message in log_output

    def test_sanitized_logger_redacts_phi(self):
        phi_message = "Patient John Doe (DOB: 1990-01-01) needs follow-up."
        self.logger.warning(phi_message)
        log_output = self.stream.getvalue().strip()
        assert "John Doe" not in log_output
        assert "1990-01-01" not in log_output
        assert "[NAME REDACTED]" in log_output
        assert "[DOB REDACTED]" in log_output

# Example of running tests if the file is executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])
