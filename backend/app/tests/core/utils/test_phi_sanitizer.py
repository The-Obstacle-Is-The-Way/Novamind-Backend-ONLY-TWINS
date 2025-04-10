TEST# -*- coding: utf-8 -*-
"""
PHI Sanitizer Tests

This module contains tests for the PHI sanitization utilities
to ensure proper detection and redaction of Protected Health Information.
"""

import unittest
from typing import Dict, Any

from app.core.utils.phi_sanitizer import PHISanitizer


class TestPHISanitizer(unittest.TestCase):
    """Test suite for PHI sanitization functionality."""
    
    def test_sanitize_string_with_phi(self):
        """Test sanitization of strings containing PHI."""
        # Test various PHI patterns
        test_cases = [
            # MRN
            ("Patient MRN: 12345678", "Patient MRN: [MRN REDACTED]"),
            # SSN
            ("SSN: 123-45-6789", "SSN: [SSN REDACTED]"),
            ("SSN: 123 45 6789", "SSN: [SSN REDACTED]"),
            ("SSN: 123456789", "SSN: [SSN REDACTED]"),
            # Name
            ("Patient name: John Smith", "Patient name: [NAME REDACTED]"),
            ("Dr. Jane Doe will see you", "Dr. [NAME REDACTED] will see you"),
            # DOB
            ("DOB: 01/01/1980", "DOB: [DOB REDACTED]"),
            ("DOB: 1980/01/01", "DOB: [DOB REDACTED]"),
            # Address
            ("Lives at 123 Main Street", "Lives at [ADDRESS REDACTED]"),
            ("Address: 456 Park Avenue", "Address: [ADDRESS REDACTED]"),
            # Phone
            ("Phone: (555) 123-4567", "Phone: [PHONE REDACTED]"),
            ("Call me at 555-123-4567", "Call me at [PHONE REDACTED]"),
            ("International: +1 555 123 4567", "International: [PHONE REDACTED]"),
            # Email
            ("Email: patient@example.com", "Email: [EMAIL REDACTED]"),
        ]
        
        for input_text, expected_output in test_cases:
            sanitized = PHISanitizer.sanitize_string(input_text)
            self.assertEqual(sanitized, expected_output)
    
    def test_sanitize_string_without_phi(self):
        """Test sanitization of strings without PHI."""
        # Test strings that shouldn't be affected
        non_phi_strings = [
            "This text has no PHI content",
            "Regular diagnostic information",
            "Patient reports feeling better",
            "Medication prescribed at standard dose"
        ]
        
        for text in non_phi_strings:
            sanitized = PHISanitizer.sanitize_string(text)
            self.assertEqual(sanitized, text)
    
    def test_sanitize_empty_and_none_inputs(self):
        """Test sanitization with empty or None inputs."""
        self.assertEqual(PHISanitizer.sanitize_string(""), "")
        self.assertEqual(PHISanitizer.sanitize_string(None), None)
        self.assertEqual(PHISanitizer.sanitize_dict({}), {})
        self.assertEqual(PHISanitizer.sanitize_dict(None), None)
        self.assertEqual(PHISanitizer.sanitize_list([]), [])
        self.assertEqual(PHISanitizer.sanitize_list(None), None)
    
    def test_sanitize_dict(self):
        """Test sanitization of dictionaries with PHI."""
        # Test dictionary with various PHI elements
        test_dict = {
            "patient_id": "A12345",
            "name": "John Smith",
            "contact": {
                "email": "john.smith@example.com",
                "phone": "555-123-4567",
                "address": "123 Main Street"
            },
            "dob": "01/01/1980",
            "ssn": "123-45-6789",
            "notes": "Patient reports feeling better",
            "medications": ["Med A", "Med B"],
            "vitals": {
                "heart_rate": 72,
                "blood_pressure": "120/80"
            }
        }
        
        expected_output = {
            "patient_id": "A12345",  # Not matched by PHI patterns
            "name": "[NAME REDACTED]",
            "contact": {
                "email": "[EMAIL REDACTED]",
                "phone": "[PHONE REDACTED]",
                "address": "[ADDRESS REDACTED]"
            },
            "dob": "[DOB REDACTED]",
            "ssn": "[SSN REDACTED]",
            "notes": "Patient reports feeling better",  # No PHI
            "medications": ["Med A", "Med B"],  # No PHI
            "vitals": {
                "heart_rate": 72,  # Not a string
                "blood_pressure": "120/80"  # Not matching PHI patterns
            }
        }
        
        sanitized = PHISanitizer.sanitize_dict(test_dict)
        self.assertEqual(sanitized, expected_output)
    
    def test_sanitize_dict_with_excluded_keys(self):
        """Test dictionary sanitization with excluded keys."""
        test_dict = {
            "patient_id": "A12345",
            "name": "John Smith",
            "contact": {
                "email": "john.smith@example.com"
            }
        }
        
        # Exclude name from sanitization
        sanitized = PHISanitizer.sanitize_dict(test_dict, exclude_keys={"name"})
        
        expected = {
            "patient_id": "A12345",
            "name": "John Smith",  # Not sanitized
            "contact": {
                "email": "[EMAIL REDACTED]"
            }
        }
        
        self.assertEqual(sanitized, expected)
    
    def test_sanitize_list(self):
        """Test sanitization of lists containing PHI."""
        test_list = [
            "Patient: John Smith",
            {"ssn": "123-45-6789", "notes": "Regular checkup"},
            ["Call at 555-123-4567", "Email: patient@example.com"],
            123
        ]
        
        expected_output = [
            "Patient: [NAME REDACTED]",
            {"ssn": "[SSN REDACTED]", "notes": "Regular checkup"},
            ["Call at [PHONE REDACTED]", "Email: [EMAIL REDACTED]"],
            123
        ]
        
        sanitized = PHISanitizer.sanitize_list(test_list)
        self.assertEqual(sanitized, expected_output)
    
    def test_sanitize_error_message(self):
        """Test sanitization of error messages containing PHI."""
        error_message = "Error processing data for John Smith (SSN: 123-45-6789)"
        expected = "Error processing data for [NAME REDACTED] (SSN: [SSN REDACTED])"
        
        sanitized = PHISanitizer.sanitize_error_message(error_message)
        self.assertEqual(sanitized, expected)
    
    def test_sanitize_log_entry(self):
        """Test sanitization of log entries containing PHI."""
        log_entry = "User accessed record for patient John Smith (DOB: 01/01/1980)"
        expected = "User accessed record for patient [NAME REDACTED] (DOB: [DOB REDACTED])"
        
        sanitized = PHISanitizer.sanitize_log_entry(log_entry)
        self.assertEqual(sanitized, expected)
    
    def test_update_patterns(self):
        """Test updating PHI detection patterns."""
        # Original string with custom pattern
        test_string = "Patient ID: PT-12345-ABC"
        # Should not be redacted with default patterns
        self.assertEqual(PHISanitizer.sanitize_string(test_string), test_string)
        
        # Add new pattern
        import re
        PHISanitizer.update_patterns({
            "patient_id": re.compile(r'\bPT-\d{5}-[A-Z]{3}\b')
        })
        
        # Now should be redacted
        expected = "Patient ID: [PATIENT_ID REDACTED]"
        self.assertEqual(PHISanitizer.sanitize_string(test_string), expected)


if __name__ == "__main__":
    unittest.main()