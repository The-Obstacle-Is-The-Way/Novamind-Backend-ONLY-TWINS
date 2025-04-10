# -*- coding: utf-8 -*-
"""
Tests for PHI Sanitizer utility.

These tests ensure that the PHI Sanitizer correctly identifies and sanitizes
Protected Health Information to maintain HIPAA compliance.
"""

import pytest
from typing import Dict, Any, List

from app.core.utils.phi_sanitizer import PHISanitizer, PHIDetector, PHIType, get_phi_secure_logger


class TestPHIDetector:
    """Test suite for the PHI detector functionality."""

    def test_contains_phi_true(self, sample_phi_text):
        """Test PHI detection in text containing PHI."""
        # Act
        result = PHIDetector.contains_phi(sample_phi_text)
        
        # Assert
        assert result is True, "Should detect PHI in the sample text"

    def test_contains_phi_false(self, sample_non_phi_text):
        """Test PHI detection in text without PHI."""
        # Act
        result = PHIDetector.contains_phi(sample_non_phi_text)
        
        # Assert
        assert result is False, "Should not detect PHI in text without PHI"

    def test_contains_phi_edge_cases(self):
        """Test PHI detection with edge cases."""
        # Test with empty string
        assert PHIDetector.contains_phi("") is False
        
        # Test with None
        assert PHIDetector.contains_phi(None) is False
        
        # Test with non-string
        assert PHIDetector.contains_phi(123) is False

    def test_detect_phi_types(self, sample_phi_text):
        """Test detection of specific PHI types."""
        # Act
        result = PHIDetector.detect_phi_types(sample_phi_text)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) > 0, "Should detect multiple PHI instances"
        
        # Verify structure of results
        for phi_type, match_text in result:
            assert isinstance(phi_type, PHIType)
            assert isinstance(match_text, str)
            assert match_text in sample_phi_text
        
        # Check for specific PHI types
        phi_types = [phi_type for phi_type, _ in result]
        assert PHIType.SSN in phi_types, "Should detect SSN"
        assert PHIType.EMAIL in phi_types, "Should detect email"
        assert PHIType.PHONE in phi_types, "Should detect phone number"
        assert PHIType.ADDRESS in phi_types, "Should detect address"
        assert PHIType.NAME in phi_types, "Should detect name"

    def test_detect_phi_types_edge_cases(self):
        """Test PHI type detection with edge cases."""
        # Test with empty string
        assert PHIDetector.detect_phi_types("") == []
        
        # Test with None
        assert PHIDetector.detect_phi_types(None) == []
        
        # Test with non-string
        assert PHIDetector.detect_phi_types(123) == []


class TestPHISanitizer:
    """Test suite for the PHI sanitizer functionality."""

    def test_sanitize_text(self, sample_phi_text):
        """Test sanitization of text containing PHI."""
        # Act
        sanitized = PHISanitizer.sanitize_text(sample_phi_text)
        
        # Assert
        assert sanitized != sample_phi_text, "Sanitized text should differ from original"
        
        # Check that PHI has been redacted
        assert "123-45-6789" not in sanitized, "SSN should be redacted"
        assert "john.smith@example.com" not in sanitized, "Email should be redacted"
        assert "(555) 123-4567" not in sanitized, "Phone should be redacted"
        assert "123 Main St" not in sanitized, "Address should be redacted"
        
        # Verify redaction markers
        assert "[REDACTED:SSN]" in sanitized or "000-00-0000" in sanitized
        assert "[REDACTED:EMAIL]" in sanitized or "[REDACTED]" in sanitized
        assert "[REDACTED:PHONE]" in sanitized or "555-000-0000" in sanitized

    def test_sanitize_text_no_phi(self, sample_non_phi_text):
        """Test sanitization of text without PHI."""
        # Act
        sanitized = PHISanitizer.sanitize_text(sample_non_phi_text)
        
        # Assert
        assert sanitized == sample_non_phi_text, "Text without PHI should remain unchanged"

    def test_sanitize_structured_data(self, sample_patient_data):
        """Test sanitization of structured data containing PHI."""
        # Act
        sanitized = PHISanitizer.sanitize_structured_data(sample_patient_data)
        
        # Assert
        assert sanitized != sample_patient_data, "Sanitized data should differ from original"
        
        # Check that PHI has been redacted
        assert sanitized["email"] != sample_patient_data["email"], "Email should be redacted"
        assert sanitized["phone"] != sample_patient_data["phone"], "Phone should be redacted"
        assert sanitized["address"]["street"] != sample_patient_data["address"]["street"], "Address should be redacted"
        assert sanitized["medical_record_number"] != sample_patient_data["medical_record_number"], "MRN should be redacted"
        assert sanitized["insurance"]["policy_number"] != sample_patient_data["insurance"]["policy_number"], "Policy number should be redacted"

    def test_sanitize_structured_data_nested(self):
        """Test sanitization of deeply nested structured data."""
        # Arrange
        nested_data = {
            "patient": {
                "personal": {
                    "ssn": "123-45-6789",
                    "name": "John Smith",
                    "contacts": [
                        {"type": "email", "value": "john.smith@example.com"},
                        {"type": "phone", "value": "(555) 123-4567"}
                    ]
                }
            },
            "non_phi_data": {
                "appointment_type": "Follow-up",
                "duration_minutes": 30
            }
        }
        
        # Act
        sanitized = PHISanitizer.sanitize_structured_data(nested_data)
        
        # Assert
        assert sanitized != nested_data, "Sanitized data should differ from original"
        
        # Check that PHI has been redacted at all levels
        assert sanitized["patient"]["personal"]["ssn"] != nested_data["patient"]["personal"]["ssn"]
        assert sanitized["patient"]["personal"]["name"] != nested_data["patient"]["personal"]["name"]
        assert sanitized["patient"]["personal"]["contacts"][0]["value"] != nested_data["patient"]["personal"]["contacts"][0]["value"]
        assert sanitized["patient"]["personal"]["contacts"][1]["value"] != nested_data["patient"]["personal"]["contacts"][1]["value"]
        
        # Check that non-PHI data is preserved
        assert sanitized["non_phi_data"] == nested_data["non_phi_data"]


class TestPHISecureLogger:
    """Test suite for the PHI secure logger functionality."""

    def test_get_phi_secure_logger(self):
        """Test creation of PHI-secure logger."""
        # Act
        logger = get_phi_secure_logger("test_logger")
        
        # Assert
        assert logger is not None, "Should return a logger instance"
        assert hasattr(logger, "debug"), "Logger should have debug method"
        assert hasattr(logger, "info"), "Logger should have info method"
        assert hasattr(logger, "warning"), "Logger should have warning method"
        assert hasattr(logger, "error"), "Logger should have error method"
        assert hasattr(logger, "critical"), "Logger should have critical method"
        assert hasattr(logger, "exception"), "Logger should have exception method"

    def test_sanitize_log_message(self):
        """Test sanitization of log messages."""
        # Arrange
        message = "Patient {name} with SSN {ssn} needs attention"
        name = "John Smith"
        ssn = "123-45-6789"
        
        # Act
        sanitized = sanitize_log_message(message, name=name, ssn=ssn)
        
        # Assert
        assert "John Smith" not in sanitized, "Name should be redacted"
        assert "123-45-6789" not in sanitized, "SSN should be redacted"
        assert message != sanitized, "Sanitized message should differ from original"

    def test_phi_secure_logger_methods(self, caplog):
        """Test PHI secure logger methods."""
        # Arrange
        logger = get_phi_secure_logger("test_phi_logger")
        phi_text = "SSN: 123-45-6789, Patient: John Smith"
        
        # Act - Test different log levels
        logger.debug(phi_text)
        logger.info(phi_text)
        logger.warning(phi_text)
        logger.error(phi_text)
        logger.critical(phi_text)
        
        # Assert
        for record in caplog.records:
            assert "123-45-6789" not in record.message, f"SSN should be redacted in {record.levelname} log"
            assert "John Smith" not in record.message, f"Name should be redacted in {record.levelname} log"