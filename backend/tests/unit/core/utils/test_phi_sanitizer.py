# -*- coding: utf-8 -*-
"""
Unit tests for PHI sanitization to ensure HIPAA compliance with PHI handling.
"""

import pytest
from datetime import date
from typing import Dict, Any, List
import json

from app.core.utils.phi_sanitizer import (
    PHIType,
    PHIDetector,
    PHISanitizer,
    get_phi_secure_logger,
    sanitize_log_message
)


class TestPHIDetection:
    """Test suite for PHI detection functionality."""
    
    def test_email_detection(self):
        """Test detection of email addresses."""
        test_emails = [
            "patient@example.com",
            "dr.smith@hospital.org",
            "john.doe+tag@gmail.com",
            "support@company-name.co.uk"
        ]
        
        for email in test_emails:
            assert PHIDetector.contains_phi(email), f"Failed to detect email: {email}"
    
    def test_phone_detection(self):
        """Test detection of phone numbers in various formats."""
        test_phones = [
            "555-123-4567",
            "(555) 123-4567",
            "5551234567",
            "+1 555 123 4567"
        ]
        
        for phone in test_phones:
            assert PHIDetector.contains_phi(phone), f"Failed to detect phone: {phone}"
    
    def test_ssn_detection(self):
        """Test detection of Social Security Numbers."""
        test_ssns = [
            "123-45-6789",
            "123456789"
        ]
        
        for ssn in test_ssns:
            assert PHIDetector.contains_phi(ssn), f"Failed to detect SSN: {ssn}"
    
    def test_date_detection(self):
        """Test detection of dates that could be DOB."""
        test_dates = [
            "1980-01-01",
            "1980/01/01",
            "01/01/1980",
            "1980.01.01"
        ]
        
        for date_str in test_dates:
            assert PHIDetector.contains_phi(date_str), f"Failed to detect date: {date_str}"
    
    def test_detection_in_context(self):
        """Test detection of PHI embedded in larger text."""
        test_contexts = [
            "Patient email: patient@example.com should be kept private",
            "Please call at (555) 123-4567 for appointment",
            "SSN: 123-45-6789 was provided for billing",
            "The patient was born on 1980-01-01 in California"
        ]
        
        for context in test_contexts:
            assert PHIDetector.contains_phi(context), f"Failed to detect PHI in: {context}"
    
    def test_known_test_values_detection(self):
        """Test detection of known test values from the KNOWN_TEST_VALUES list."""
        for test_value in PHIDetector.KNOWN_TEST_VALUES:
            assert PHIDetector.contains_phi(test_value), f"Failed to detect known test value: {test_value}"
    
    def test_no_false_positives(self):
        """Test that non-PHI text is not flagged."""
        non_phi_texts = [
            "This contains no PHI",
            "ID-12345",
            "The system version is 2.0.1",
            "Error code: E-12345"
        ]
        
        for text in non_phi_texts:
            assert not PHIDetector.contains_phi(text), f"False positive detection in: {text}"


class TestPHISanitization:
    """Test suite for PHI sanitization functionality."""
    
    def test_email_sanitization(self):
        """Test sanitization of email addresses."""
        email = "patient@example.com"
        sanitized = PHISanitizer.sanitize_text(email)
        
        assert "patient@example.com" not in sanitized
        assert "@example.com" in sanitized  # Format is preserved but value is changed
    
    def test_phone_sanitization(self):
        """Test sanitization of phone numbers."""
        phone = "555-123-4567"
        sanitized = PHISanitizer.sanitize_text(phone)
        
        assert "555-123-4567" not in sanitized
        assert sanitized == "555-000-0000"
    
    def test_ssn_sanitization(self):
        """Test sanitization of SSNs."""
        ssn = "123-45-6789"
        sanitized = PHISanitizer.sanitize_text(ssn)
        
        assert "123-45-6789" not in sanitized
        assert sanitized == "000-00-0000"
    
    def test_dob_sanitization(self):
        """Test sanitization of dates of birth."""
        dob = "1980-01-01"
        sanitized = PHISanitizer.sanitize_text(dob)
        
        assert "1980-01-01" not in sanitized
        assert sanitized == "YYYY-MM-DD"
    
    def test_sanitization_in_context(self):
        """Test sanitization of PHI embedded in larger text."""
        original = "Patient John Doe (DOB: 1980-01-01, SSN: 123-45-6789) " \
                  "can be reached at 555-123-4567 or patient@example.com"
        sanitized = PHISanitizer.sanitize_text(original)
        
        assert "1980-01-01" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "555-123-4567" not in sanitized
        assert "patient@example.com" not in sanitized
        assert "YYYY-MM-DD" in sanitized
        assert "000-00-0000" in sanitized
        assert "555-000-0000" in sanitized
    
    def test_structured_data_sanitization(self):
        """Test sanitization of structured data (dict/list)."""
        structured_data: Dict[str, Any] = {
            "patient": {
                "name": "John Doe",
                "contact": {
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567"
                },
                "dob": "1980-01-01",
                "ssn": "123-45-6789",
                "visits": [
                    {"date": "2025-03-01", "notes": "Patient complained about headaches."},
                    {"date": "2025-03-15", "notes": "Follow-up, call at 555-123-4567."}
                ]
            }
        }
        
        sanitized = PHISanitizer.sanitize_structured_data(structured_data)
        sanitized_json = json.dumps(sanitized)
        
        # Check that PHI has been removed
        assert "john.doe@example.com" not in sanitized_json
        assert "555-123-4567" not in sanitized_json
        assert "1980-01-01" not in sanitized_json
        assert "123-45-6789" not in sanitized_json
        
        # Check structure is preserved
        assert "patient" in sanitized
        assert "contact" in sanitized["patient"]
        assert "email" in sanitized["patient"]["contact"]
        assert "visits" in sanitized["patient"]
        assert len(sanitized["patient"]["visits"]) == 2


class TestSecureLogging:
    """Test suite for secure logging functionality with PHI sanitization."""
    
    def test_log_message_sanitization(self):
        """Test that log messages are properly sanitized."""
        unsanitized = "Patient John Doe (SSN: 123-45-6789) called from 555-123-4567"
        sanitized = sanitize_log_message(unsanitized)
        
        assert "123-45-6789" not in sanitized
        assert "555-123-4567" not in sanitized
    
    def test_log_with_format_args(self):
        """Test sanitization with format arguments."""
        message = "Patient {} has SSN {} and phone {}"
        sanitized = sanitize_log_message(
            message, 
            "John Doe", 
            "123-45-6789", 
            "555-123-4567"
        )
        
        assert "123-45-6789" not in sanitized
        assert "555-123-4567" not in sanitized
    
    def test_secure_logger(self):
        """Test the PHISecureLogger class (no actual logs generated)."""
        # This is a behavioral test, we mock the actual logger
        import logging
        from unittest.mock import patch
        
        test_message = "Patient email: patient@example.com"
        
        with patch.object(logging.Logger, 'info') as mock_info:
            secure_logger = get_phi_secure_logger("test_logger")
            secure_logger.info(test_message)
            
            # Check that the logger was called with sanitized text
            assert mock_info.called
            sanitized_call = mock_info.call_args[0][0]
            assert "patient@example.com" not in sanitized_call


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])