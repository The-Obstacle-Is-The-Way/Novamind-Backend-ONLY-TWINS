# -*- coding: utf-8 -*-
"""Unit tests for Log Sanitizer functionality.

This module tests the log sanitizer which ensures Protected Health Information (PHI)
is properly redacted from all system logs, a critical requirement for HIPAA compliance.
"""

import pytest
import json
import logging
from unittest.mock import patch, MagicMock, call

from app.infrastructure.security.log_sanitizer import
    LogSanitizer,  
    SanitizerConfig,  
    PHIPattern,  
    SanitizationStrategy,  
    PatternType,  
    RedactionMode
()


@pytest.fixture
def sanitizer_config():
    """Create a log sanitizer configuration for testing."""
    
    return SanitizerConfig()
        enabled=True,
        redaction_mode=RedactionMode.PARTIAL,
        partial_redaction_length=4,
        redaction_marker="[REDACTED]",
        phi_patterns_path="phi_patterns.yaml",
        enable_contextual_detection=True,
        scan_nested_objects=True,
        sensitive_field_names=[
            "ssn", "social_security", "dob", "birth_date", "address", 
            "phone", "email", "full_name", "patient_name", "mrn",
            "medical_record_number", "credit_card", "insurance_id"
        ],
        sensitive_keys_case_sensitive=False,
        preserve_data_structure=True,
        exceptions_allowed=False,
        log_sanitization_attempts=True,
        max_log_size_kb=256,
        hash_identifiers=True,
        identifier_hash_salt="novamind-phi-salt-key"
    (    )


    @pytest.fixture
    def pattern_repository():
    """Create a mock pattern repository with test data."""
    mock_repo = MagicMock()
    
    # Mock the patterns with test data
    mock_repo.get_patterns.return_value = [
        PHIPattern()
            name="SSN",
            pattern=r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            type=PatternType.REGEX,
            priority=10,
            context_words=["social", "security", "ssn"],
            examples=["123-45-6789", "123 45 6789", "123456789"]
    (        ),
        PHIPattern()
            name="Email",
            pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            type=PatternType.REGEX,
            priority=5,
            context_words=["email", "contact", "@"],
            examples=["user@example.com", "name.surname@domain.co.uk"]
    (        ),
        PHIPattern()
            name="Phone",
            pattern=r"\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
            type=PatternType.REGEX,
            priority=5,
            context_words=["phone", "call", "tel", "contact"],
            examples=["(555) 123-4567", "555-123-4567", "5551234567"]
    (        ),
        PHIPattern()
            name="PatientID",
            pattern=r"\b(PT|MRN)[A-Z0-9]{6,10}\b",
            type=PatternType.REGEX,
            priority=8,
            context_words=["patient", "id", "identifier", "record"],
            examples=["PT123456", "MRN987654321"]
    (        )
    ]
    
    return mock_repo


    @pytest.fixture
    def log_sanitizer(sanitizer_config, pattern_repository):
    """Create a log sanitizer for testing."""
    sanitizer = LogSanitizer(config=sanitizer_config)
    sanitizer.pattern_repository = pattern_repository
    return sanitizer


    @pytest.mark.venv_only()
    class TestLogSanitizer:
    """Test suite for the log sanitizer."""
    
    def test_sanitize_simple_string(self, log_sanitizer):
        """Test sanitization of a simple string with PHI."""
        # String with SSN
        input_string = "Patient record with SSN: 123-45-6789"
        
        # Sanitize the string
        sanitized = log_sanitizer.sanitize(input_string)
        
        # Verify SSN was redacted
        assert "123-45-6789" not in sanitized
        assert "[REDACTED]" in sanitized
    
        def test_sanitize_json_string(self, log_sanitizer):
        """Test sanitization of a JSON string with PHI."""
        # JSON string with PHI
        json_string = json.dumps({)
            "patient_id": "PT123456",
            "name": "John Smith",
            "contact": {
                "email": "john.smith@example.com",
                "phone": "(555) 123-4567"
            }
(        })
        
        # Sanitize the JSON string
    sanitized = log_sanitizer.sanitize(json_string)
        
        # Parse back to verify structure
    sanitized_json = json.loads(sanitized)
        
        # Verify PHI was redacted
    assert sanitized_json["patient_id"] != "PT123456"
    assert "john.smith@example.com" not in sanitized
    assert "(555) 123-4567" not in sanitized
        
        # Verify structure is preserved
    assert "patient_id" in sanitized_json
    assert "contact" in sanitized_json
    assert "email" in sanitized_json["contact"]
    assert "phone" in sanitized_json["contact"]
    
    def test_sanitize_dict(self, log_sanitizer):
        """Test sanitization of a dictionary with PHI."""
        # Dictionary with PHI
        patient_dict = {
            "patient_id": "PT123456",
            "name": "John Smith",
            "dob": "1980-05-15",
            "contact": {
                "email": "john.smith@example.com",
                "phone": "(555) 123-4567",
                "address": "123 Main St, Anytown, USA"
            },
            "ssn": "123-45-6789",
            "insurance": {
                "provider": "HealthCare Inc",
                "policy_number": "POLICY12345",
                "group_number": "GROUP6789"
            }
        }
        
        # Sanitize the dictionary
    sanitized = log_sanitizer.sanitize_dict(patient_dict)
        
        # Verify sensitive fields were redacted
    assert sanitized["patient_id"] != "PT123456"
    assert sanitized["name"] != "John Smith"
    assert sanitized["ssn"] != "123-45-6789"
    assert sanitized["contact"]["email"] != "john.smith@example.com"
    assert sanitized["contact"]["phone"] != "(555) 123-4567"
    assert sanitized["contact"]["address"] != "123 Main St, Anytown, USA"
        
        # Verify redaction marker or partial redaction is present
    assert "[REDACTED]" in str(sanitized)
        
        # Verify non-sensitive fields were preserved
    assert sanitized["insurance"]["provider"] == "HealthCare Inc"
    
    def test_sanitize_list(self, log_sanitizer):
        """Test sanitization of a list with PHI."""
        # List with PHI
        patient_list = [
            {
                "patient_id": "PT123456",
                "name": "John Smith",
                "email": "john.smith@example.com"
            },
            {
                "patient_id": "PT789012",
                "name": "Jane Doe",
                "email": "jane.doe@example.com"
            }
        ]
        
        # Sanitize the list
    sanitized = log_sanitizer.sanitize_list(patient_list)
        
        # Verify all items were sanitized
    for item in sanitized:
        assert item["patient_id"] != "PT123456" and item["patient_id"] != "PT789012"
        assert item["name"] != "John Smith" and item["name"] != "Jane Doe"
        assert "example.com" not in item["email"]
    
        def test_sensitive_key_detection(self, log_sanitizer):
        """Test detection and sanitization based on sensitive key names."""
        # Dictionary with sensitive keys
        data = {
            "user_id": "user123",  # Not sensitive
            "first_name": "John",  # Not explicitly sensitive
            "ssn": "123-45-6789",  # Sensitive key
            "some_data": "normal data",  # Not sensitive
            "credit_card": "4111-1111-1111-1111",  # Sensitive key
            "nested": {
                "dob": "1980-05-15",  # Sensitive key
                "regular_field": "regular value"  # Not sensitive
            }
        }
        
        # Sanitize the dictionary
    sanitized = log_sanitizer.sanitize_dict(data)
        
        # Verify sensitive keys were sanitized
    assert sanitized["ssn"] != "123-45-6789"
    assert sanitized["credit_card"] != "4111-1111-1111-1111"
    assert sanitized["nested"]["dob"] != "1980-05-15"
        
        # Verify non-sensitive keys were preserved
    assert sanitized["user_id"] == "user123"
    assert sanitized["some_data"] == "normal data"
    assert sanitized["nested"]["regular_field"] == "regular value"
    
    def test_pattern_based_detection(self, log_sanitizer):
        """Test detection and sanitization based on PHI patterns."""
        # String with various PHI patterns but no sensitive keys
        log_message = """
        User login: admin
        Action: Viewed patient with ID PT654321
        Note: Please contact the patient at john.doe@example.com or (555) 987-6543
        Reference: Document #12345 mentions insurance policy 987-65-4321
        """
        
        # Sanitize the message
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify PHI patterns were sanitized
        assert "PT654321" not in sanitized
        assert "john.doe@example.com" not in sanitized
        assert "(555) 987-6543" not in sanitized
        assert "987-65-4321" not in sanitized
        
        # Verify non-PHI was preserved
        assert "User login: admin" in sanitized
        assert "Action: Viewed patient with ID" in sanitized
        assert "Reference: Document #12345 mentions insurance policy" in sanitized
    
        def test_contextual_detection(self, log_sanitizer):
        """Test contextual detection of PHI."""
        # Enable contextual detection
        log_sanitizer.config.enable_contextual_detection = True
        
        # String with potential PHI in context
        log_message = """
        Patient social: 987-65-4321
        Email address is: contact@example.org
        Random number: 123-45-6789 (not an SSN)
        """
        
        # Sanitize the message
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify contextual PHI was sanitized
        assert "987-65-4321" not in sanitized  # "social" provides context for SSN
        assert "contact@example.org" not in sanitized  # "Email address" provides context
        
        # When context detection is disabled, random numbers might not be detected
        log_sanitizer.config.enable_contextual_detection = False
        sanitized_no_context = log_sanitizer.sanitize(log_message)
        
        # With context disabled, the regex still detects SSN pattern
        assert "987-65-4321" not in sanitized_no_context
        assert "contact@example.org" not in sanitized_no_context  # Email is still detected by pattern
    
        def test_partial_redaction(self, log_sanitizer):
        """Test partial redaction of PHI."""
        # Configure partial redaction
        log_sanitizer.config.redaction_mode = RedactionMode.PARTIAL
        log_sanitizer.config.partial_redaction_length = 4
        
        # String with PHI
        log_message = "Patient SSN: 123-45-6789, Email: john.doe@example.com"
        
        # Sanitize with partial redaction
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify partial redaction
        assert "123-45-6789" not in sanitized
        assert "john.doe@example.com" not in sanitized
        
        # Depending on implementation, might show last 4 digits
        if log_sanitizer.config.partial_redaction_length == 4:
        assert "-6789" in sanitized or "xxx-xx-6789" in sanitized
        assert "example.com" in sanitized or "xxxx.xxxx@example.com" in sanitized
    
        def test_full_redaction(self, log_sanitizer):
        """Test full redaction of PHI."""
        # Configure full redaction
        log_sanitizer.config.redaction_mode = RedactionMode.FULL
        log_sanitizer.config.redaction_marker = "[REDACTED]"
        
        # String with PHI
        log_message = "Patient SSN: 123-45-6789, Email: john.doe@example.com"
        
        # Sanitize with full redaction
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify full redaction
        assert "123-45-6789" not in sanitized
        assert "john.doe@example.com" not in sanitized
        assert "[REDACTED]" in sanitized
        assert "-6789" not in sanitized  # Last 4 should not be visible
        assert "example.com" not in sanitized  # Domain should not be visible
    
        def test_hash_redaction(self, log_sanitizer):
        """Test hash-based redaction of PHI."""
        # Configure hash redaction
        log_sanitizer.config.redaction_mode = RedactionMode.HASH
        
        # String with PHI
        log_message = "Patient ID: PT123456, SSN: 123-45-6789"
        
        # Sanitize with hash redaction
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify hash redaction
        assert "PT123456" not in sanitized
        assert "123-45-6789" not in sanitized
        
        # Hash values should be consistent for the same input
        sanitized2 = log_sanitizer.sanitize(log_message)
        assert sanitized  ==  sanitized2
    
        def test_log_message_sanitization(self, log_sanitizer):
        """Test sanitization of log messages."""
        # Create a log message with PHI
        log_record = logging.LogRecord()
            name="test_logger",
            level=logging.INFO,
            pathname="test_file.py",
            lineno=100,
            msg="Patient %s with SSN %s had appointment on %s",
            args=("John Smith", "123-45-6789", "2023-05-15"),
            exc_info=None
        (        )
        
        # Sanitize the log record
        sanitized_record = log_sanitizer.sanitize_log_record(log_record)
        
        # Verify the message was sanitized
        assert "John Smith" not in sanitized_record.getMessage()
        assert "123-45-6789" not in sanitized_record.getMessage()
    
        def test_structured_log_sanitization(self, log_sanitizer):
        """Test sanitization of structured logs."""
        # Structured log entry
        structured_log = {
            "timestamp": "2023-05-15T10:30:00Z",
            "level": "INFO",
            "message": "Patient data accessed",
            "context": {
                "user": "doctor_smith",
                "action": "view",
                "patient": {
                    "id": "PT123456",
                    "name": "John Doe",
                    "ssn": "123-45-6789",
                    "contact": {
                        "email": "john.doe@example.com",
                        "phone": "(555) 123-4567"
                    }
                }
            }
        }
        
        # Sanitize the structured log
    sanitized = log_sanitizer.sanitize_structured_log(structured_log)
        
        # Verify structure is preserved
    assert "timestamp" in sanitized
    assert "level" in sanitized
    assert "message" in sanitized
    assert "context" in sanitized
    assert "patient" in sanitized["context"]
    assert "contact" in sanitized["context"]["patient"]
        
        # Verify PHI was sanitized
    assert sanitized["context"]["patient"]["id"] != "PT123456"
    assert sanitized["context"]["patient"]["name"] != "John Doe"
    assert sanitized["context"]["patient"]["ssn"] != "123-45-6789"
    assert sanitized["context"]["patient"]["contact"]["email"] != "john.doe@example.com"
    assert sanitized["context"]["patient"]["contact"]["phone"] != "(555) 123-4567"
        
        # Verify non-PHI was preserved
    assert sanitized["timestamp"] == "2023-05-15T10:30:00Z"
    assert sanitized["level"] == "INFO"
    assert sanitized["message"] == "Patient data accessed"
    assert sanitized["context"]["user"] == "doctor_smith"
    assert sanitized["context"]["action"] == "view"
    
    def test_disabled_sanitizer(self, log_sanitizer):
        """Test behavior when sanitizer is disabled."""
        # Disable the sanitizer
        log_sanitizer.config.enabled = False
        
        # String with PHI
        log_message = "Patient SSN: 123-45-6789"
        
        # Sanitize with disabled sanitizer
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify no sanitization occurred
        assert sanitized  ==  log_message
        assert "123-45-6789" in sanitized
    
        def test_exception_handling(self, log_sanitizer):
        """Test sanitizer's exception handling."""
        # Configure to allow exceptions
        log_sanitizer.config.exceptions_allowed = True
        
        # Create a scenario that would cause an exception
        with patch.object(log_sanitizer, '_sanitize_value', side_effect=Exception("Test exception")):
            # With exceptions allowed, it should return fallback
        result = log_sanitizer.sanitize("Test message with PHI")
        assert result  ==  "[Sanitization Error]"
        
        # Configure to not allow exceptions
        log_sanitizer.config.exceptions_allowed = False
        
        # With exceptions not allowed, it should handle gracefully
        with patch.object(log_sanitizer, '_sanitize_value', side_effect=Exception("Test exception")):
        result = log_sanitizer.sanitize("Test message with PHI")
        assert result  ==  "Test message with PHI"  # Original returned on error
    
        def test_max_log_size(self, log_sanitizer):
        """Test handling of large log messages."""
        # Configure max log size
        log_sanitizer.config.max_log_size_kb = 1  # 1KB
        
        # Create a large log message (>1KB)
        large_message = "A" * 1500
        
        # Sanitize the large message
        sanitized = log_sanitizer.sanitize(large_message)
        
        # Verify the message was truncated or handled appropriately
        assert len(sanitized) < len(large_message)
        assert "[Truncated]" in sanitized
    
        def test_sanitization_hook(self, log_sanitizer):
        """Test custom sanitization hooks."""
        # Define a custom sanitization hook
        def custom_hook(value, context):
            if isinstance(value, str) and "CUSTOM_PHI" in value:
                return value.replace("CUSTOM_PHI", "[CUSTOM_REDACTED]")
                return value
        
                # Add the custom hook
                log_sanitizer.add_sanitization_hook(custom_hook)
        
                # Test with custom PHI
                log_message = "This contains CUSTOM_PHI that should be redacted"
        
                # Sanitize with custom hook
                sanitized = log_sanitizer.sanitize(log_message)
        
                # Verify custom sanitization
                assert "CUSTOM_PHI" not in sanitized
                assert "[CUSTOM_REDACTED]" in sanitized
    
                def test_multiple_phi_instances(self, log_sanitizer):
        """Test sanitization of multiple PHI instances in the same message."""
        # Message with multiple PHI instances
        log_message = """
        Patient: John Smith
        SSN: 123-45-6789
        Contact: john.smith@example.com or (555) 123-4567
        Secondary contact: jane.smith@example.com
        Reference: Another patient with SSN 987-65-4321
        """
        
        # Sanitize the message
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify all PHI instances were sanitized
        assert "John Smith" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "john.smith@example.com" not in sanitized
        assert "(555) 123-4567" not in sanitized
        assert "jane.smith@example.com" not in sanitized
        assert "987-65-4321" not in sanitized
    
        def test_phi_at_boundaries(self, log_sanitizer):
        """Test sanitization of PHI at string boundaries."""
        # PHI at start, middle, and end of string
        log_message = "123-45-6789 is the SSN for patient and email is john@example.com"
        
        # Sanitize the message
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify PHI was sanitized at all positions
        assert "123-45-6789" not in sanitized
        assert "john@example.com" not in sanitized