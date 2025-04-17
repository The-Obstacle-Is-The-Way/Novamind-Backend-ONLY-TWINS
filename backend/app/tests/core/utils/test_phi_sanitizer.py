"""
Unit tests for PHI Sanitizer Utility.

Ensures PHI is correctly identified and redacted/masked from various data structures.
"""

import unittest
import pytest
import re
from typing import Dict, Any
import logging
from unittest.mock import patch, MagicMock
import json

# Updated import to use LogSanitizer from the infrastructure layer
# from app.core.utils.phi_sanitizer import sanitize_data # Old import REMOVED
from app.infrastructure.security.phi.log_sanitizer import LogSanitizer, LogSanitizerConfig
from app.infrastructure.security.phi.phi_service import PHIService

# Helper function for tests
def create_test_data() -> Dict[str, Any]:
    """Creates a sample data structure containing potential PHI."""
    return {
        "patient_name": "John Doe",
        "ssn": "000-12-3456",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "zip": "12345",
        },
        "notes": "Patient reported feeling anxious. Phone number: 555-867-5309.",
        "details": [
            {"id": 1, "value": "Regular checkup"}, 
            {"id": 2, "value": "Email: test@example.com"} # Add email
        ],
        "medical_record_number": "MRN12345XYZ",
        "metadata": {
            "unrelated": "safe data",
            "sensitive_key": "DOB: 01/01/1980",
            "nested_sensitive": {
                 "contact": "primary phone is 123-456-7890"
            }
        }
    }

@pytest.fixture
def phi_sanitizer() -> LogSanitizer:
    """Provides an instance of the LogSanitizer."""
    # Using default config for testing
    return LogSanitizer()

@pytest.mark.venv_only()
class TestPHISanitizer(unittest.TestCase):
    """Test suite for PHI sanitization functionality."""
    def setUp(self):
        """Initialize a LogSanitizer instance for each test."""
        self.sanitizer = LogSanitizer()

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
            sanitized = self.sanitizer.sanitize(input_text)
            self.assertEqual(sanitized, expected_output)

    def test_sanitize_string_without_phi(self):
        """Test sanitization of strings without PHI."""
        # Test strings that should not be modified
        test_cases = [
        "Regular checkup scheduled",
        "Medication prescribed as directed",
        "Follow-up in 2 weeks",
        "Lab results within normal range",
        "Patient reports feeling better",
        ]

        for input_text in test_cases:
            sanitized = self.sanitizer.sanitize(input_text)
            self.assertEqual(sanitized, input_text)

    def test_sanitize_dict_with_phi(self):
        """Test sanitization of dictionaries containing PHI."""
        data = create_test_data()
        sanitized = self.sanitizer.sanitize(data)
        
        # Check specific fields
        self.assertNotEqual(sanitized["patient_name"], "John Doe")
        self.assertIn("REDACTED", sanitized["patient_name"])
        self.assertNotEqual(sanitized["ssn"], "000-12-3456")
        self.assertIn("REDACTED", sanitized["ssn"])
        self.assertNotEqual(sanitized["address"]["street"], "123 Main St")
        self.assertNotIn("555-867-5309", sanitized["notes"])
        self.assertNotIn("test@example.com", sanitized["details"][1]["value"])
        self.assertNotEqual(sanitized["medical_record_number"], "MRN12345XYZ")
        self.assertNotIn("01/01/1980", sanitized["metadata"]["sensitive_key"])
        self.assertNotIn("123-456-7890", sanitized["metadata"]["nested_sensitive"]["contact"])
        
        # Check safe fields remain untouched
        self.assertEqual(sanitized["address"]["city"], "Anytown")
        self.assertEqual(sanitized["details"][0]["value"], "Regular checkup")
        self.assertEqual(sanitized["metadata"]["unrelated"], "safe data")

    def test_sanitize_dict_without_phi(self):
        """Test sanitization of dictionaries without PHI."""
        test_dict = {
            "visit_type": "Follow-up",
            "visit_count": 3,
            "notes": "Regular checkup",
            "medication": {
                "name": "Ibuprofen",
                "dosage": "200mg",
                "frequency": "twice daily"
            }
        }

        sanitized = self.sanitizer.sanitize(test_dict)
        self.assertEqual(sanitized, test_dict)

    def test_sanitize_list_with_phi(self):
        """Test sanitization of lists containing PHI."""
        test_list = [
            "Patient: John Smith",
            {"ssn": "123-45-6789", "notes": "Regular checkup"},
            ["Call at 555-123-4567", "Email: john.smith@example.com"],
            123,
        ]

        expected_output = [
            "Patient: [NAME REDACTED]",
            {"ssn": "[SSN REDACTED]", "notes": "Regular checkup"},
            ["Call at [PHONE REDACTED]", "Email: [EMAIL REDACTED]"],
            123,
        ]

        sanitized = self.sanitizer.sanitize(test_list)
        self.assertEqual(sanitized, expected_output)

    def test_sanitize_error_message(self):
        """Test sanitization of error messages containing PHI."""
        error_message = "Error processing data for John Smith (SSN: 123-45-6789)"
        expected = "Error processing data for [NAME REDACTED] (SSN: [SSN REDACTED])"

        sanitized = self.sanitizer.sanitize(error_message)
        self.assertEqual(sanitized, expected)

    def test_sanitize_log_entry(self):
        """Test sanitization of log entries containing PHI."""
        log_entry = "User accessed record for patient John Smith (DOB: 01/01/1980)"
        expected = "User accessed record for patient [NAME REDACTED] (DOB: [DOB REDACTED])"

        sanitized = LogSanitizer.sanitize_log_entry(log_entry)
        self.assertEqual(sanitized, expected)

    def test_update_patterns(self):
        """Test updating PHI detection patterns."""
        # Original string with custom pattern
        test_string = "Patient ID: PT-12345-ABC"
        # Should not be redacted with default patterns
        self.assertEqual(LogSanitizer.sanitize_string(test_string), test_string)

        # Add new pattern
        LogSanitizer.update_patterns({"patient_id": re.compile(r"\bPT-\d{5}-[A-Z]{3}\b")})

        # Now should be redacted
        expected = "Patient ID: [PATIENT_ID REDACTED]"
        self.assertEqual(LogSanitizer.sanitize_string(test_string), expected)

    def test_sanitize_empty_data(self):
        """Test sanitizing empty structures."""
        self.assertEqual(self.sanitizer.sanitize({}), {})
        self.assertEqual(self.sanitizer.sanitize([]), [])
        self.assertEqual(self.sanitizer.sanitize(""), "")
        # None is converted to string 'None'
        self.assertEqual(self.sanitizer.sanitize(None), "None")

    def test_sanitize_non_string_types(self):
        """Test sanitizing non-string/collection types (should pass through)."""
        # Atomic types are converted to string
        self.assertEqual(self.sanitizer.sanitize(123), "123")
        self.assertEqual(self.sanitizer.sanitize(123.45), "123.45")
        self.assertEqual(self.sanitizer.sanitize(True), "True")

    def test_sanitize_json_string(self):
        """Test sanitizing a JSON string."""
        json_str = json.dumps(create_test_data())
        sanitized_str = self.sanitizer.sanitize(json_str)
        
        # Should sanitize content within the string
        self.assertNotIn("John Doe", sanitized_str)
        self.assertNotIn("000-12-3456", sanitized_str)
        self.assertNotIn("555-867-5309", sanitized_str)
        self.assertIn("REDACTED", sanitized_str)

        # Ensure it's still valid JSON (assuming redaction doesn't break JSON structure)
        try:
            json.loads(sanitized_str)
        except json.JSONDecodeError:
            self.fail("Sanitized JSON string is not valid JSON")

    def test_sanitize_with_different_sensitivity(self):
        """Test sanitizing with potentially different sensitivity levels (conceptual)."""
        # Assuming PHIService might have levels like 'high', 'medium', 'low'
        data = {"name": "Sensitive Name", "phone": "555-123-4567", "diagnosis": "Common Cold"}
        
        # Example: Default sensitivity might catch name and phone
        sanitized_default = self.sanitizer.sanitize(data)
        self.assertNotIn("Sensitive Name", sanitized_default["name"])
        self.assertNotIn("555-123-4567", sanitized_default["phone"])
        # Assuming diagnosis is not PHI at default level
        # assert sanitized_default["diagnosis"] == "Common Cold" 
        
        # Example: Higher sensitivity might catch diagnosis too (if configured in PHIService)
        # sanitized_high = phi_sanitizer.sanitize(data, sensitivity='high')
        # assert "Common Cold" not in sanitized_high["diagnosis"] 
        pass # Keep as pass until sensitivity levels are concrete

    def test_sanitization_disabled(self):
        """Test behavior when sanitization is disabled via config."""
        disabled_config = LogSanitizerConfig(enabled=False)
        sanitizer = LogSanitizer(config=disabled_config)
        data = create_test_data()
        sanitized = sanitizer.sanitize(data)
        self.assertEqual(sanitized, data) # Data should be unchanged


if __name__ == "__main__":
    unittest.main()