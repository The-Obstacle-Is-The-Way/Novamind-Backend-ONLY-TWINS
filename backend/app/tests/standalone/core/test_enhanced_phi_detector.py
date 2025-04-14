# -*- coding: utf-8 -*-
"""
Tests for the enhanced PHI detector utility.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.utils.enhanced_phi_detector import (
    EnhancedPHIDetector,
    EnhancedPHISanitizer,
    EnhancedPHISecureLogger,
    get_enhanced_phi_secure_logger,
)

from app.core.utils.phi_sanitizer import PHIType


class TestEnhancedPHIDetector:
    """Tests for the EnhancedPHIDetector class."""

    @pytest.mark.standalone()
    def test_contains_phi_with_standard_patterns(self):
        """Test detection of PHI using standard patterns."""
        # Test with SSN
        text = "Patient SSN: 123-45-6789"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with email
        text = "Contact: patient@example.com"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with phone number
        text = "Call at (123) 456-7890"
        assert EnhancedPHIDetector.contains_phi(text) is True

    @pytest.mark.standalone()
    def test_contains_phi_with_enhanced_patterns(self):
        """Test detection of PHI using enhanced patterns."""
        # Test with MRN
        text = "MRN: 12345678"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with patient name
        text = "Patient Name: John Doe"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with address
        text = "123 Main St, Apt 4, Springfield, IL 62701"
        assert EnhancedPHIDetector.contains_phi(text) is True

    @pytest.mark.standalone()
    def test_contains_phi_with_medical_context(self):
        """Test detection of PHI in medical context."""
        # Test with medical record context
        text = "Dr. Smith reviewed the chart for John Doe"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with diagnosis context
        text = "Patient diagnosed with condition ABC on 2025-04-01"
        assert EnhancedPHIDetector.contains_phi(text) is True

    @pytest.mark.standalone()
    def test_contains_phi_negative_cases(self):
        """Test cases that should not be detected as PHI."""
        # Test with general medical terms
        text = "The treatment protocol includes medication and therapy"
        assert EnhancedPHIDetector.contains_phi(text) is False

        # Test with non-specific dates
        text = "Follow-up in 30 days"
        assert EnhancedPHIDetector.contains_phi(text) is False

        # Test with anonymous references
        text = "The patient reported improvement"
        assert EnhancedPHIDetector.contains_phi(text) is False

    @pytest.mark.standalone()
    def test_detect_phi_types(self):
        """Test detection of specific PHI types."""
        # Test with multiple PHI types
        text = "Patient John Doe (SSN: 123-45-6789) lives at 123 Main St"
        phi_types = EnhancedPHIDetector.detect_phi_types(text)
        
        assert PHIType.NAME in phi_types
        assert PHIType.SSN in phi_types
        assert PHIType.ADDRESS in phi_types

    @pytest.mark.standalone()
    def test_detect_phi_types_with_context(self):
        """Test detection of PHI types with context."""
        # Test with medical context
        text = "Dr. Smith saw patient on 2025-04-01 for follow-up"
        phi_types = EnhancedPHIDetector.detect_phi_types(text)
        
        assert PHIType.NAME in phi_types
        assert PHIType.DATE in phi_types

    @pytest.mark.standalone()
    def test_detect_phi_locations(self):
        """Test detection of PHI locations in text."""
        # Test with multiple PHI instances
        text = "Patient John Doe (DOB: 1980-01-01) contacted via john.doe@example.com"
        locations = EnhancedPHIDetector.detect_phi_locations(text)
        
        assert len(locations) >= 3  # At least name, DOB, and email
        
        # Check that locations contain expected PHI
        detected_text = [text[loc[0]:loc[1]] for loc in locations]
        assert any("John Doe" in dt for dt in detected_text)
        assert any("1980-01-01" in dt for dt in detected_text)
        assert any("john.doe@example.com" in dt for dt in detected_text)

    @pytest.mark.standalone()
    def test_sensitivity_levels(self):
        """Test different sensitivity levels for PHI detection."""
        # Low sensitivity test
        text = "The patient's appointment is next week"
        assert EnhancedPHIDetector.contains_phi(text, sensitivity_level="low") is False
        
        # Medium sensitivity test
        text = "Follow up with the patient on Tuesday"
        assert EnhancedPHIDetector.contains_phi(text, sensitivity_level="medium") is False
        
        # High sensitivity test (should detect more potential PHI)
        text = "Follow up with the patient on Tuesday"
        assert EnhancedPHIDetector.contains_phi(text, sensitivity_level="high") is True

    @pytest.mark.standalone()
    def test_contains_phi_with_custom_patterns(self):
        """Test PHI detection with custom patterns."""
        # Define custom patterns
        custom_patterns = [
            r"Custom ID: \d{4}-[A-Z]{2}",
            r"Protocol: [A-Z]{3}-\d{5}"
        ]
        
        # Test with custom pattern
        text = "The patient is enrolled in Protocol: ABC-12345"
        assert EnhancedPHIDetector.contains_phi(text, custom_patterns=custom_patterns) is True
        
        # Test with non-matching custom pattern
        text = "Standard treatment applies"
        assert EnhancedPHIDetector.contains_phi(text, custom_patterns=custom_patterns) is False


class TestEnhancedPHISanitizer:
    """Tests for the EnhancedPHISanitizer class."""

    @pytest.mark.standalone()
    def test_sanitize_text_standard(self):
        """Test basic text sanitization."""
        text = "Patient John Doe (SSN: 123-45-6789)"
        sanitized = EnhancedPHISanitizer.sanitize_text(text)
        
        assert "John Doe" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "[REDACTED]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_text_with_custom_replacement(self):
        """Test text sanitization with custom replacement text."""
        text = "Patient John Doe (SSN: 123-45-6789)"
        sanitized = EnhancedPHISanitizer.sanitize_text(text, replacement="[PHI]")
        
        assert "John Doe" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "[PHI]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_text_by_type(self):
        """Test sanitization of specific PHI types."""
        text = "Patient John Doe (DOB: 1980-01-01, SSN: 123-45-6789)"
        sanitized = EnhancedPHISanitizer.sanitize_text_by_type(text, phi_types=[PHIType.SSN])
        
        # SSN should be redacted
        assert "123-45-6789" not in sanitized
        # Name should still be present if not specified for redaction
        assert "John Doe" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_structured_data(self):
        """Test sanitization of structured data (dict, list)."""
        # Test with dictionary
        data = {
            "patient_name": "John Doe",
            "medical_data": {
                "record_id": "12345",
                "ssn": "123-45-6789"
            },
            "contact": "john.doe@example.com"
        }
        
        sanitized = EnhancedPHISanitizer.sanitize_structured_data(data)
        
        assert sanitized["patient_name"] != "John Doe"
        assert sanitized["medical_data"]["ssn"] != "123-45-6789"
        assert sanitized["contact"] != "john.doe@example.com"
        
        # Test with list
        data_list = [
            "Patient: John Doe",
            "DOB: 1980-01-01",
            "Phone: (123) 456-7890"
        ]
        
        sanitized_list = EnhancedPHISanitizer.sanitize_structured_data(data_list)
        
        assert "John Doe" not in sanitized_list[0]
        assert "1980-01-01" not in sanitized_list[1]
        assert "(123) 456-7890" not in sanitized_list[2]

    @pytest.mark.standalone()
    def test_partial_sanitization(self):
        """Test partial sanitization that preserves some information."""
        # Test partial email sanitization
        email = "john.doe@example.com"
        sanitized = EnhancedPHISanitizer.partial_sanitize_email(email)
        
        assert "john.doe" not in sanitized
        assert "example.com" in sanitized  # Domain should be preserved
        
        # Test partial phone sanitization
        phone = "(123) 456-7890"
        sanitized = EnhancedPHISanitizer.partial_sanitize_phone(phone)
        
        assert "456-7890" not in sanitized
        assert sanitized.endswith("7890")  # Last 4 digits preserved


class TestEnhancedPHISecureLogger:
    """Tests for the EnhancedPHISecureLogger class."""

    @pytest.mark.standalone()
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock()
        self.phi_logger = EnhancedPHISecureLogger(self.mock_logger)

    @pytest.mark.standalone()
    def test_info_with_phi(self):
        """Test logging info message containing PHI."""
        message = "Patient John Doe (SSN: 123-45-6789) checked in"
        
        self.phi_logger.info(message)
        
        # Check that the underlying logger was called with sanitized message
        args, _ = self.mock_logger.info.call_args
        sanitized_message = args[0]
        
        assert "John Doe" not in sanitized_message
        assert "123-45-6789" not in sanitized_message
        assert "[REDACTED]" in sanitized_message

    @pytest.mark.standalone()
    def test_error_with_phi(self):
        """Test logging error message containing PHI."""
        message = "Error processing data for patient John Doe"
        
        self.phi_logger.error(message)
        
        # Check that the underlying logger was called with sanitized message
        args, _ = self.mock_logger.error.call_args
        sanitized_message = args[0]
        
        assert "John Doe" not in sanitized_message
        assert "[REDACTED]" in sanitized_message

    @pytest.mark.standalone()
    def test_audit_logging(self):
        """Test audit logging functionality."""
        with patch.object(self.phi_logger, '_log_phi_access') as mock_audit:
            message = "Accessed records for John Doe (MRN: 12345)"
            self.phi_logger.info(message, audit=True)
            
            # Check that audit logging was triggered
            mock_audit.assert_called_once()
            
            # The first argument should be the unsanitized message
            args, _ = mock_audit.call_args
            assert "John Doe" in args[0]

    @pytest.mark.standalone()
    def test_get_enhanced_phi_secure_logger(self):
        """Test the factory function for creating a secure logger."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Get a secure logger
            secure_logger = get_enhanced_phi_secure_logger("test.module")
            
            # Verify it's the right type
            assert isinstance(secure_logger, EnhancedPHISecureLogger)
            
            # Test that it sanitizes messages
            message = "Patient John Doe checked in"
            secure_logger.info(message)
            
            # Check underlying logger was called with sanitized message
            args, _ = mock_logger.info.call_args
            sanitized_message = args[0]
            
            assert "John Doe" not in sanitized_message