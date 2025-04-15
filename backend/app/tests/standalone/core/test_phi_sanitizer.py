import json
import re
from unittest.mock import MagicMock, patch

import pytest
import logging

from app.infrastructure.security.phi.log_sanitizer import LogSanitizer, PHIDetector


class TestPHISanitizer:
    """Test suite for the PHI Sanitizer component with PITUITARY region support."""
    
    @pytest.fixture
    def sanitizer(self):
        """Create a PHI sanitizer instance for testing."""
        return LogSanitizer()
    
    @pytest.fixture
    def sample_phi_data(self):
        """Sample PHI data for testing sanitization."""
        return {
            "ssn": "123-45-6789",
            "name": "John Smith",
            "dob": "01/15/1980",
            "phone": "(555) 123-4567",
            "email": "john.smith@example.com",
            "address": "123 Main St, Anytown, CA 12345",
            "mrn": "MRN12345678",
            "insurance_id": "INS123456789",
        }

    @pytest.mark.standalone()
    def test_sanitize_string_with_ssn(self, sanitizer):
        """Test sanitization of strings containing SSNs."""
        input_text = "Patient SSN: 123-45-6789"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "123-45-6789" not in sanitized
        assert "SSN" in sanitized
        assert "[REDACTED:SSN]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_string_with_name(self, sanitizer):
        """Test sanitization of strings containing names."""
        input_text = "Patient Name: John Smith"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "John Smith" not in sanitized
        assert "Name" in sanitized
        assert "[REDACTED:NAME]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_string_with_email(self, sanitizer):
        """Test sanitization of strings containing email addresses."""
        input_text = "Contact us at: john.smith@example.com"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "john.smith@example.com" not in sanitized
        assert "Contact us at" in sanitized
        assert "[REDACTED:EMAIL]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_string_with_phone(self, sanitizer):
        """Test sanitization of strings containing phone numbers."""
        input_text = "Call us at: (555) 123-4567"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "(555) 123-4567" not in sanitized
        assert "Call us at" in sanitized
        assert "[REDACTED:PHONE]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_string_with_address(self, sanitizer):
        """Test sanitization of strings containing addresses."""
        input_text = "Located at: 123 Main St, Anytown, CA 12345"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "123 Main St" not in sanitized
        assert "Anytown" not in sanitized
        assert "Located at" in sanitized
        assert "[REDACTED:ADDRESS]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_string_with_mrn(self, sanitizer):
        """Test sanitization of strings containing medical record numbers."""
        input_text = "Medical Record Number: MRN12345678"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "MRN12345678" not in sanitized
        assert "Medical Record Number" in sanitized
        assert "[REDACTED:MRN]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_json(self, sanitizer, sample_phi_data):
        """Test sanitization of JSON containing PHI."""
        # Convert sample data to JSON
        json_data = json.dumps(sample_phi_data)
        
        # Sanitize JSON
        sanitized_json = sanitizer.sanitize_json(json_data)
        sanitized_data = json.loads(sanitized_json)
        
        # Check that all PHI fields have been sanitized
        for key, value in sample_phi_data.items():
            assert sanitized_data[key] != value
            assert "[REDACTED" in sanitized_data[key]

    @pytest.mark.standalone()
    def test_sanitize_dict(self, sanitizer, sample_phi_data):
        """Test sanitization of dictionaries containing PHI."""
        # Sanitize dictionary
        sanitized_data = sanitizer.sanitize_dict(sample_phi_data)
        
        # Check that all PHI fields have been sanitized
        for key, value in sample_phi_data.items():
            assert sanitized_data[key] != value
            assert "[REDACTED" in sanitized_data[key]

    @pytest.mark.standalone()
    def test_sanitize_with_custom_patterns(self):
        """Test sanitization with custom patterns."""
        # Create sanitizer with custom patterns
        custom_patterns = {
            "CUSTOM_ID": r"CUST-\d{6}",
            "PROJECT_CODE": r"PROJ-[A-Z]{2}\d{4}"
        }
        
        sanitizer = LogSanitizer(custom_patterns=custom_patterns)
        
        # Test with custom patterns
        input_text = "Customer ID: CUST-123456, Project: PROJ-AB1234"
        sanitized = sanitizer.sanitize_text(input_text)
        
        assert "CUST-123456" not in sanitized
        assert "PROJ-AB1234" not in sanitized
        assert "[REDACTED:CUSTOM_ID]" in sanitized
        assert "[REDACTED:PROJECT_CODE]" in sanitized

    @pytest.mark.standalone()
    def test_phi_detector(self):
        """Test the PHI detector component."""
        detector = PHIDetector()
        
        # Test SSN detection
        assert detector.contains_phi("SSN: 123-45-6789")
        assert detector.detect_phi_type("SSN: 123-45-6789") == "SSN"
        
        # Test name detection
        assert detector.contains_phi("Name: John Smith")
        assert detector.detect_phi_type("Name: John Smith") == "NAME"
        
        # Test email detection
        assert detector.contains_phi("Email: john.smith@example.com")
        assert detector.detect_phi_type("Email: john.smith@example.com") == "EMAIL"
        
        # Test non-PHI text
        assert not detector.contains_phi("This is a generic message")
        assert detector.detect_phi_type("This is a generic message") is None

    @pytest.mark.standalone()
    def test_redaction(self):
        """Test different redaction strategies."""
        detector = PHIDetector()
        
        # Test default redaction (full)
        ssn_text = "SSN: 123-45-6789"
        redacted = detector.redact(ssn_text)
        assert "123-45-6789" not in redacted
        assert "[REDACTED:SSN]" in redacted
        
        # Test partial redaction
        detector.set_redaction_mode("partial")
        ssn_text = "SSN: 123-45-6789"
        redacted = detector.redact(ssn_text)
        assert "123-45-" not in redacted
        assert "6789" in redacted  # Last 4 digits preserved
        
        # Test hash redaction
        detector.set_redaction_mode("hash")
        ssn_text = "SSN: 123-45-6789"
        redacted = detector.redact(ssn_text)
        assert "123-45-6789" not in redacted
        assert "[HASH:" in redacted

    @pytest.mark.standalone()
    def test_performance(self, sanitizer, sample_phi_data):
        """Test sanitization performance with large datasets."""
        # Create a large dataset
        large_data = {f"key_{i}": sample_phi_data for i in range(10)}
        
        # Measure time to sanitize
        import time
        start_time = time.time()
        sanitized = sanitizer.sanitize_dict(large_data)
        end_time = time.time()
        
        # Performance assertions
        assert end_time - start_time < 1.0  # Should take less than 1 second
        assert len(sanitized) == len(large_data)  # All data should be processed
        
        # All PHI should be sanitized
        for key, value in sanitized.items():
            for inner_key, inner_value in value.items():
                assert sample_phi_data[inner_key] not in str(inner_value)

    @pytest.mark.standalone()
    def test_sanitize_with_context(self, sanitizer):
        """Test sanitization with contextual awareness."""
        # Test context-aware sanitization 
        input_text = "The patient can be reached at his home number (555) 123-4567 or work extension 1234"
        sanitized = sanitizer.sanitize_text(input_text)
        
        # Phone number should be redacted, but not extension
        assert "(555) 123-4567" not in sanitized
        assert "extension 1234" in sanitized  # Should not be redacted
        assert "[REDACTED:PHONE]" in sanitized

    @pytest.mark.standalone()
    def test_log_sanitizer_integration(self, caplog):
        """Test integration with logging system."""
        # Setup logger with sanitizer
        from app.infrastructure.security.log_sanitizer import SanitizedLogger
        
        logger = SanitizedLogger("test_logger")
        caplog.set_level(logging.INFO)
        
        # Log message with PHI
        logger.info("Patient SSN: 123-45-6789")
        
        # Check logs are sanitized
        for record in caplog.records:
            assert "123-45-6789" not in record.message
            assert "[REDACTED" in record.message


if __name__ == "__main__":
    pytest.main(["-v", __file__])
