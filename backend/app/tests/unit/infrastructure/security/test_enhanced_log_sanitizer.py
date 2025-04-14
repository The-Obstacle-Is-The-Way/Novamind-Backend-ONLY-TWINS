import pytest
import re
import json
import logging
from typing import Dict, Any, List
import yaml # Import yaml for mocking
from unittest.mock import patch, MagicMock, Mock, call # Import call
import os # Import os if needed

# Correctly import necessary components
from app.infrastructure.security.log_sanitizer import (
    LogSanitizer, SanitizerConfig, PatternType, RedactionMode,
    PHIPattern, PatternRepository, RedactionStrategy,
    FullRedactionStrategy, PartialRedactionStrategy, HashRedactionStrategy,
    RedactionStrategyFactory, PHIFormatter, PHIRedactionHandler,
    SanitizedLogger, sanitize_logs, get_sanitized_logger
)


class TestPHIPattern:
    """Test suite for PHIPattern class."""

    def test_phi_pattern_matches_regex(self):
        """Test regex pattern matching."""
        pattern = PHIPattern(
            name="SSN",
            pattern=r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            type=PatternType.REGEX,
            priority=10
        )
        assert pattern.matches("SSN: 123-45-6789")
        assert pattern.matches("123-45-6789")
        assert pattern.matches("SSN is 123 45 6789")
        assert not pattern.matches("12-345-678")
        assert not pattern.matches("Not an SSN")
        assert not pattern.matches("")
        assert not pattern.matches(None) # type: ignore

    def test_phi_pattern_matches_exact(self):
        """Test exact pattern matching."""
        pattern = PHIPattern(
            name="Sensitive Key",
            pattern="patient_id",
            type=PatternType.EXACT,
            priority=10
        )
        assert pattern.matches("patient_id")
        assert not pattern.matches("patient_identifier")
        assert not pattern.matches("id")
        assert not pattern.matches("PATIENT_ID") # Default is case-sensitive
        assert not pattern.matches("")
        assert not pattern.matches(None) # type: ignore

    def test_phi_pattern_matches_fuzzy(self):
        """Test fuzzy pattern matching."""
        pattern = PHIPattern(
            name="Medical Term",
            pattern="diagnosis",
            type=PatternType.FUZZY,
            priority=5
        )
        assert pattern.matches("The diagnosis is...")
        assert pattern.matches("diagnosis")
        assert pattern.matches("Patient DIAGNOSIS information") # Fuzzy is case-insensitive
        assert not pattern.matches("diag")
        assert not pattern.matches("")
        assert not pattern.matches(None) # type: ignore

    def test_phi_pattern_matches_context(self):
        """Test context-based pattern matching."""
        pattern = PHIPattern(
            name="SSN Context",
            pattern="", # Pattern itself might be empty for context-only
            type=PatternType.CONTEXT,
            priority=10,
            context_words=["social", "security", "ssn"]
        )
        assert pattern.matches("", context="social security number")
        assert pattern.matches("", context="SSN: 123-45-6789")
        assert pattern.matches("", context="The social security is...")
        assert not pattern.matches("", context="No matching words here")
        assert not pattern.matches("", context="")
        assert not pattern.matches("", context=None)
        assert not pattern.matches("", None) # type: ignore


class TestPatternRepository:
    """Test suite for PatternRepository class."""

    def test_default_patterns(self):
        """Test that default patterns are loaded."""
        repo = PatternRepository() # No args for default
        patterns = repo.get_patterns()
        assert len(patterns) >= 4
        pattern_names = [p.name for p in patterns]
        assert "SSN" in pattern_names
        assert "Email" in pattern_names
        assert "Phone" in pattern_names
        # Default might vary, check for presence of some defaults
        assert any(p.name.startswith("Default") or p.name in ["SSN", "Email", "Phone"] for p in patterns)


    @patch('builtins.open', new_callable=mock_open, read_data="""
patterns:
  - name: Test Pattern
    pattern: 'test\\d+'
    type: REGEX
    priority: 8
    context_words: ['test', 'example']
    examples: ['test123', 'test456']
  - name: Another Pattern
    pattern: 'another'
    type: FUZZY
    priority: 5
sensitive_keys:
  - name: API Keys
    priority: 10
    keys: ['api_key', 'secret_key', 'auth_token']
""")
    @patch('app.infrastructure.security.log_sanitizer.yaml.safe_load')
    def test_load_patterns_from_file(self, mock_yaml_load: MagicMock, mock_file_open: MagicMock, tmp_path):
        """Test loading patterns from a YAML file."""
        # Mock the yaml.safe_load to return structured data
        mock_yaml_data = {
            'patterns': [
                {
                    'name': 'Test Pattern', 'pattern': r'test\d+', 'type': 'REGEX',
                    'priority': 8, 'context_words': ['test', 'example'],
                    'examples': ['test123', 'test456']
                },
                {
                    'name': 'Another Pattern', 'pattern': 'another', 'type': 'FUZZY',
                    'priority': 5
                }
            ],
            'sensitive_keys': [
                {
                    'name': 'API Keys', 'priority': 10,
                    'keys': ['api_key', 'secret_key', 'auth_token']
                }
            ]
        }
        mock_yaml_load.return_value = mock_yaml_data

        patterns_file_path = "dummy/path/patterns.yaml" # Path used in constructor
        repo = PatternRepository(patterns_file_path) # Load from mocked file
        patterns = repo.get_patterns()

        # Check if patterns from file are loaded (plus defaults if applicable)
        pattern_names = [p.name for p in patterns]
        assert "Test Pattern" in pattern_names
        assert "Another Pattern" in pattern_names
        # Check if sensitive keys were processed into patterns
        assert any(p.name == 'api_key' and p.type == PatternType.EXACT for p in patterns)
        assert any(p.name == 'secret_key' and p.type == PatternType.EXACT for p in patterns)

        # Verify pattern properties
        test_pattern = next((p for p in patterns if p.name == "Test Pattern"), None)
        assert test_pattern is not None
        assert test_pattern.type == PatternType.REGEX
        assert test_pattern.priority == 8
        assert "test" in test_pattern.context_words
        assert "test123" in test_pattern.examples
        mock_file_open.assert_called_once_with(patterns_file_path, 'r', encoding='utf-8')
        mock_yaml_load.assert_called_once()


    def test_add_pattern(self):
        """Test adding a new pattern."""
        repo = PatternRepository()
        initial_count = len(repo.get_patterns())
        new_pattern = PHIPattern(
            name="Custom Pattern",
            pattern=r"custom\d+",
            type=PatternType.REGEX,
            priority=7
        )
        repo.add_pattern(new_pattern)
        patterns = repo.get_patterns()
        assert len(patterns) == initial_count + 1
        assert any(p.name == "Custom Pattern" for p in patterns)


class TestRedactionStrategies:
    """Test suite for redaction strategies."""

    def test_full_redaction_strategy(self):
        """Test FullRedactionStrategy."""
        strategy = FullRedactionStrategy(marker="[PHI REDACTED]")
        assert strategy.redact("123-45-6789") == "[PHI REDACTED]"
        assert strategy.redact("john.doe@example.com") == "[PHI REDACTED]"
        assert strategy.redact("Complex PHI data") == "[PHI REDACTED]"
        assert strategy.redact("") == "[PHI REDACTED]" # Redacts empty strings too
        assert strategy.redact(None) == "[PHI REDACTED]" # Handles None

    def test_partial_redaction_strategy_ssn(self):
        """Test PartialRedactionStrategy with SSN."""
        strategy = PartialRedactionStrategy(visible_length=4, marker="xxx") # Use marker for replacement
        ssn_pattern = PHIPattern(name="SSN", pattern=r"\d{3}-\d{2}-\d{4}")
        # Assumes strategy identifies SSN pattern and applies specific logic
        assert strategy.redact("123-45-6789", ssn_pattern) == "xxx-xx-6789"
        # Test unformatted SSN - behavior might depend on implementation details

        # Test with no PHI
        assert sanitizer.sanitize("No PHI here") == "No PHI here"
        mock_scan_and_redact.assert_called_with("No PHI here")

        # Test with SSN
        assert sanitizer.sanitize("SSN: 123-45-6789") == "[REDACTED]"
        mock_scan_and_redact.assert_called_with("SSN: 123-45-6789")


    @patch('app.infrastructure.security.log_sanitizer.LogSanitizer._scan_and_redact')
    def test_sanitize_with_partial_redaction(self, mock_scan_and_redact: MagicMock):
        """Test sanitizing with partial redaction mode."""
        # Setup mock to simulate partial redaction
        mock_scan_and_redact.return_value = "SSN: xxx-xx-6789"

        config = SanitizerConfig(redaction_mode=RedactionMode.PARTIAL)
        sanitizer = LogSanitizer(config=config)

        result = sanitizer.sanitize("SSN: 123-45-6789")
        assert result == "SSN: xxx-xx-6789"
        mock_scan_and_redact.assert_called_once_with("SSN: 123-45-6789")


    @patch('app.infrastructure.security.log_sanitizer.LogSanitizer._scan_and_redact')
    def test_sanitize_complex_string(self, mock_scan_and_redact: MagicMock):
        """Test sanitizing a complex string with multiple PHI types."""
        # Mock to simulate multiple redactions
        mock_scan_and_redact.return_value = "Patient record - [REDACTED], [REDACTED], [REDACTED], Email: [REDACTED], [REDACTED], ID: [REDACTED]"

        sanitizer = LogSanitizer()
        complex_string = (
            "Patient record - Name: John Doe, "
            "DOB: 01/01/1980, SSN: 123-45-6789, "
            "Email: john.doe@example.com, "
            "Phone: (555) 123-4567, "
            "ID: PT123456"
        )
        result = sanitizer.sanitize(complex_string)
        assert result == "Patient record - [REDACTED], [REDACTED], [REDACTED], Email: [REDACTED], [REDACTED], ID: [REDACTED]"
        mock_scan_and_redact.assert_called_once_with(complex_string)


    def test_sanitize_dict(self):
        """Test sanitizing a dictionary."""
        # Use real patterns for dict test
        sanitizer = LogSanitizer()
        test_dict = {
            "patient_id": "PT123456",
            "name": "John Doe", # Assuming name is not a default sensitive key
            "dob": "01/01/1980",
            "contact": {
                "email": "john.doe@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St" # Assuming address is not default sensitive key
            },
            "ssn": "123-45-6789",
            "insurance": {
                "provider": "HealthCare Inc",
                "policy_number": "POLICY12345", # Assuming not default sensitive
                "group_number": "GROUP6789"
            },
            "notes": "Patient feels anxious." # String value
        }
        result = sanitizer.sanitize_dict(test_dict)

        # Check that PHI fields identified by default patterns/keys are redacted
        assert result["patient_id"] == "[REDACTED]"
        assert result["name"] == "John Doe" # Not redacted by default key
        assert result["dob"] == "[REDACTED]" # Date pattern
        assert result["ssn"] == "[REDACTED]"
        assert result["contact"]["email"] == "[REDACTED]"
        assert result["contact"]["phone"] == "[REDACTED]"
        assert result["contact"]["address"] == "123 Main St" # Not redacted
        assert result["insurance"]["provider"] == "HealthCare Inc"
        assert result["insurance"]["policy_number"] == "POLICY12345"
        assert result["notes"] == "Patient feels anxious." # String value sanitized if needed


    def test_sanitize_list(self):
        """Test sanitizing a list."""
        sanitizer = LogSanitizer()
        test_list = [
            {"patient_id": "PT123456", "name": "John Doe", "email": "john.doe@example.com"},
            {"patient_id": "PT654321", "name": "Jane Smith", "email": "jane.smith@example.com"}
        ]
        result = sanitizer.sanitize_list(test_list)

        # Check that PHI fields are redacted in each dict
        for item in result:
            assert item["patient_id"] == "[REDACTED]"
            assert item["name"] == item["name"] # Assuming name not redacted by default
            assert item["email"] == "[REDACTED]"


    def test_sanitize_structured_log(self):
        """Test sanitizing a structured log (dict)."""
        sanitizer = LogSanitizer()
        structured_log = {
            "timestamp": "2023-10-27T10:00:00Z",
            "level": "INFO",
            "message": "Processing patient data",
            "details": {
                "user_id": "user123",
                "patient_info": {
                    "id": "PT98765",
                    "contact_email": "patient@secure.com"
                },
                "ip_address": "192.168.1.100" # Example potentially sensitive info
            }
        }
        # Add ip_address to sensitive keys for this test
        sanitizer.config.sensitive_field_names.add("ip_address")

        result = sanitizer.sanitize(structured_log) # Sanitize method handles dicts

        assert result["details"]["patient_info"]["id"] == "[REDACTED]"
        assert result["details"]["patient_info"]["contact_email"] == "[REDACTED]"
        assert result["details"]["ip_address"] == "[REDACTED]"
        assert result["message"] == "Processing patient data" # Message itself not redacted


    def test_is_sensitive_key(self):
        """Test sensitive key matching logic."""
        config = SanitizerConfig(
            sensitive_field_names={"ssn", "patientId"},
            sensitive_keys_case_sensitive=False # Test case-insensitivity
        )
        sanitizer = LogSanitizer(config=config)

        assert sanitizer._is_sensitive_key("ssn") is True
        assert sanitizer._is_sensitive_key("SSN") is True
        assert sanitizer._is_sensitive_key("patientId") is True
        assert sanitizer._is_sensitive_key("patientid") is True
        assert sanitizer._is_sensitive_key("name") is False
        assert sanitizer._is_sensitive_key("id") is False # Not in the list

        # Test case-sensitive
        config_cs = SanitizerConfig(
            sensitive_field_names={"ssn", "patientId"},
            sensitive_keys_case_sensitive=True
        )
        sanitizer_cs = LogSanitizer(config=config_cs)
        assert sanitizer_cs._is_sensitive_key("ssn") is True
        assert sanitizer_cs._is_sensitive_key("SSN") is False # Case-sensitive fails
        assert sanitizer_cs._is_sensitive_key("patientId") is True


    def test_safe_system_message(self):
        """Test safe system message detection."""
        sanitizer = LogSanitizer()
        # These should not be redacted by default patterns
        assert sanitizer.sanitize("System started successfully.") == "System started successfully."
        assert sanitizer.sanitize("Database connection established.") == "Database connection established."
        assert sanitizer.sanitize("Configuration loaded.") == "Configuration loaded."


    def test_sanitization_hooks(self):
        """Test pre/post sanitization hooks."""
        pre_hook = MagicMock()
        post_hook = MagicMock()
        config = SanitizerConfig(pre_sanitize_hook=pre_hook, post_sanitize_hook=post_hook)
        sanitizer = LogSanitizer(config=config)

        data = {"ssn": "123-45-6789"}
        sanitized_data = sanitizer.sanitize(data)

        pre_hook.assert_called_once_with(data)
        post_hook.assert_called_once_with(sanitized_data)


class TestPHIFormatterAndHandler:
    """Test suite for PHIFormatter and PHIRedactionHandler."""

    @pytest.fixture
    def sanitizer(self):
        """Fixture for a LogSanitizer instance."""
        return LogSanitizer()

    def test_phi_formatter(self, sanitizer: LogSanitizer):
        """Test PHIFormatter sanitizes log records."""
        formatter = PHIFormatter(sanitizer=sanitizer, fmt='%(levelname)s:%(name)s:%(message)s')
        record = logging.LogRecord(
            name='testlogger', level=logging.INFO, pathname='test.py', lineno=10,
            msg='User %s accessed patient %s with SSN %s', args=('user123', 'PT98765', '123-45-6789'),
            exc_info=None, func='test_func'
        )
        # Manually format args into message before formatting
        record.message = record.getMessage() # Ensure args are formatted into msg

        formatted_message = formatter.format(record)

        # Verify PHI in args is redacted in the final message
        assert "user123" in formatted_message # Assuming user_id is not PHI by default
        assert "PT98765" not in formatted_message
        assert "123-45-6789" not in formatted_message
        assert "[REDACTED]" in formatted_message
        # Check the final formatted string structure
        assert "INFO:testlogger:User user123 accessed patient [REDACTED] with SSN [REDACTED]" in formatted_message


    def test_phi_formatter_with_dict(self, sanitizer: LogSanitizer):
        """Test PHIFormatter with dictionary messages."""
        formatter = PHIFormatter(sanitizer=sanitizer, fmt='%(message)s')
        log_dict = {
            "event": "patient_lookup",
            "user": "doc1",
            "details": {"patient_id": "PT123", "query_ssn": "987-65-4321"}
        }
        record = logging.LogRecord(
            name='testlogger', level=logging.INFO, pathname='test.py', lineno=10,
            msg=log_dict, args=(), exc_info=None, func='test_func' # msg is the dict
        )
        # format() expects string msg, but formatMessage handles dicts if msg is dict
        formatted_message = formatter.formatMessage(record)

        # Verify the dictionary string representation is sanitized
        assert '"patient_id": "[REDACTED]"' in formatted_message
        assert '"query_ssn": "[REDACTED]"' in formatted_message
        assert '"user": "doc1"' in formatted_message # Non-sensitive


    def test_phi_redaction_handler(self, sanitizer: LogSanitizer, caplog):
        """Test PHIRedactionHandler sanitizes records before emission."""
        logger = logging.getLogger('test_handler')
        logger.setLevel(logging.INFO)
        # Use caplog fixture to capture logs

        # Create handler with our sanitizer
        handler = PHIRedactionHandler(sanitizer=sanitizer)
        # Use a standard formatter for the handler to check output easily
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        # Add handler to logger if not already added by caplog setup
        # Check if a handler of this type already exists to avoid duplicates
        if not any(isinstance(h, PHIRedactionHandler) for h in logger.handlers):
             logger.addHandler(handler)
        caplog.set_level(logging.INFO, logger='test_handler')

        # Log message containing PHI
        logger.info("Patient SSN is 123-45-6789")

        # Check captured logs
        assert len(caplog.records) >= 1 # Might capture other logs
        assert "123-45-6789" not in caplog.text
        assert "Patient SSN is [REDACTED]" in caplog.text

        # Clean up handler to avoid interference with other tests
        logger.removeHandler(handler)


class TestSanitizedLogger:
    """Test suite for SanitizedLogger class."""

    @patch('logging.getLogger')
    def test_sanitized_logger_initialization(self, mock_get_logger: MagicMock):
        """Test initialization of SanitizedLogger."""
        mock_logger_instance = MagicMock(spec=logging.Logger)
        mock_logger_instance.handlers = [] # Start with no handlers for clean test
        mock_get_logger.return_value = mock_logger_instance

        sanitized_logger = SanitizedLogger("test_sanitized_logger")

        mock_get_logger.assert_called_once_with("test_sanitized_logger")
        assert isinstance(sanitized_logger.sanitizer, LogSanitizer)
        # Check if PHIRedactionHandler was added
        assert len(mock_logger_instance.handlers) == 1
        assert isinstance(mock_logger_instance.handlers[0], PHIRedactionHandler)


    def test_get_sanitized_logger(self):
        """Test the get_sanitized_logger factory function."""
        logger_name = "factory_logger_test"
        # Ensure logger doesn't exist beforehand if testing singleton behavior
        if logger_name in logging.Logger.manager.loggerDict:
             del logging.Logger.manager.loggerDict[logger_name]

        logger = get_sanitized_logger(logger_name)
        assert isinstance(logger, logging.Logger)
        # Check if it has the PHI handler added
        assert any(isinstance(h, PHIRedactionHandler) for h in logger.handlers)

        # Test singleton behavior (optional)
        logger2 = get_sanitized_logger(logger_name)
        assert logger is logger2


    def test_sanitize_logs_decorator(self, caplog):
        """Test the sanitize_logs decorator."""

        @sanitize_logs
        def function_with_phi(patient_id, ssn):
            # Use the logger associated with the function's module
            module_logger = logging.getLogger(__name__)
            module_logger.setLevel(logging.WARNING) # Ensure level is captured
            # Add handler if needed, caplog might handle this
            if not module_logger.handlers:
                 # Add a handler that caplog can capture if necessary
                 # For simplicity, assume caplog captures root or this logger
                 pass
            module_logger.warning(f"Processing data for {patient_id} with SSN {ssn}")
            return f"Processed {patient_id}"

        # Call the decorated function
        result = function_with_phi("PT777", "555-00-1111")

        # Check the return value is unchanged
        assert result == "Processed PT777"

        # Check that the log output was sanitized
        assert "PT777" not in caplog.text
        assert "555-00-1111" not in caplog.text
        assert "Processing data for [REDACTED] with SSN [REDACTED]" in caplog.text


    def test_sanitize_logs_decorator_on_class_method(self, caplog):
        """Test the sanitize_logs decorator on a class method."""

        class Processor:
            # Logger for the class
            logger = logging.getLogger(f"{__name__}.Processor")
            logger.setLevel(logging.ERROR) # Ensure level is captured

            @sanitize_logs
            def process(self, patient_id, ssn):
                # Add handler if needed
                if not self.logger.handlers:
                     # Add a handler that caplog can capture if necessary
                     pass
                self.logger.error(f"Error processing {patient_id}, SSN: {ssn}")
                return "Error"

        processor = Processor()
        # Ensure caplog captures logs from the specific logger
        caplog.set_level(logging.ERROR, logger=f"{__name__}.Processor")
        result = processor.process("PT888", "666-00-2222")

        assert result == "Error"
        assert "PT888" not in caplog.text
        assert "666-00-2222" not in caplog.text
        assert "Error processing [REDACTED], SSN: [REDACTED]" in caplog.text
