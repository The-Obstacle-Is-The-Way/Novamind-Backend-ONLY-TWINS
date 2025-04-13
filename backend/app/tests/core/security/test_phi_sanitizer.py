"""
Tests for the PHI sanitization utilities.
"""
import pytest
import re
from typing import Dict, List, Any, Union

from app.core.security.phi_sanitizer import PHISanitizer


class TestPHISanitizer:
    """Test cases for the PHI sanitization utilities."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.sanitizer = PHISanitizer()

        # Sample PHI data
        self.patient_name = "John Smith"
        self.patient_email = "john.smith@example.com"
        self.patient_ssn = "123-45-6789"
        self.patient_phone = "(555) 123-4567"
        self.patient_address = "123 Main St, Anytown, CA 94321"
        self.patient_dob = "01/15/1980"
        self.patient_mrn = "MRN12345678"

        # Sample text with PHI
        self.text_with_phi = f"""
        Patient {self.patient_name} (DOB: {self.patient_dob})
        Contact: {self.patient_email}, {self.patient_phone}
        SSN: {self.patient_ssn}
        Address: {self.patient_address}
        Medical Record Number: {self.patient_mrn}
        """

        # Dictionary with PHI
        self.dict_with_phi = {
            "name": self.patient_name,
            "contact": {
                "email": self.patient_email,
                "phone": self.patient_phone,
            },
            "demographics": {
                "dob": self.patient_dob,
                "ssn": self.patient_ssn,
                "address": self.patient_address,
            },
            "medical_info": {
                "mrn": self.patient_mrn,
                "diagnosis": "Depression",
                "severity": "Moderate",
            },
            "non_phi_data": {
                "appointment_type": "Follow-up",
                "duration_minutes": 30
            },
        }

        # List with PHI
        self.list_with_phi = [
            f"Name: {self.patient_name}",
            f"DOB: {self.patient_dob}",
            f"Contact: {self.patient_email}",
            "Notes: Patient reports improved mood",
            f"ID: {self.patient_mrn}",
        ]

    def test_sanitize_string(self):
        """Test that strings containing PHI are properly sanitized."""
        sanitized_text = self.sanitizer.sanitize(self.text_with_phi)
        
        # Verify PHI is redacted
        assert self.patient_name not in sanitized_text
        assert self.patient_email not in sanitized_text
        assert self.patient_ssn not in sanitized_text
        assert self.patient_phone not in sanitized_text
        assert self.patient_address not in sanitized_text
        assert self.patient_dob not in sanitized_text
        assert self.patient_mrn not in sanitized_text
        
        # Verify redaction markers are present
        assert "[REDACTED" in sanitized_text
        
        # Verify non-PHI content is preserved
        assert "Patient" in sanitized_text
        assert "Contact:" in sanitized_text
        assert "SSN:" in sanitized_text
        assert "Address:" in sanitized_text
        assert "Medical Record Number:" in sanitized_text

    def test_sanitize_dict(self):
        """Test that dictionaries containing PHI are properly sanitized."""
        sanitized_dict = self.sanitizer.sanitize(self.dict_with_phi)
        
        # Verify PHI is redacted in top-level keys
        assert sanitized_dict["name"] != self.patient_name
        assert "[REDACTED" in sanitized_dict["name"]
        
        # Verify PHI is redacted in nested dictionaries
        assert sanitized_dict["contact"]["email"] != self.patient_email
        assert "[REDACTED" in sanitized_dict["contact"]["email"]
        assert sanitized_dict["contact"]["phone"] != self.patient_phone
        assert "[REDACTED" in sanitized_dict["contact"]["phone"]
        
        assert sanitized_dict["demographics"]["dob"] != self.patient_dob
        assert "[REDACTED" in sanitized_dict["demographics"]["dob"]
        assert sanitized_dict["demographics"]["ssn"] != self.patient_ssn
        assert "[REDACTED" in sanitized_dict["demographics"]["ssn"]
        assert sanitized_dict["demographics"]["address"] != self.patient_address
        assert "[REDACTED" in sanitized_dict["demographics"]["address"]
        
        assert sanitized_dict["medical_info"]["mrn"] != self.patient_mrn
        assert "[REDACTED" in sanitized_dict["medical_info"]["mrn"]
        
        # Verify non-PHI content is preserved
        assert sanitized_dict["medical_info"]["diagnosis"] == "Depression"
        assert sanitized_dict["medical_info"]["severity"] == "Moderate"
        assert sanitized_dict["non_phi_data"]["appointment_type"] == "Follow-up"
        assert sanitized_dict["non_phi_data"]["duration_minutes"] == 30

    def test_sanitize_list(self):
        """Test that lists containing PHI are properly sanitized."""
        sanitized_list = self.sanitizer.sanitize(self.list_with_phi)
        
        # Verify PHI is redacted
        assert all(self.patient_name not in item for item in sanitized_list)
        assert all(self.patient_email not in item for item in sanitized_list)
        assert all(self.patient_dob not in item for item in sanitized_list)
        assert all(self.patient_mrn not in item for item in sanitized_list)
        
        # Verify redaction markers are present
        assert any("[REDACTED" in item for item in sanitized_list)
        
        # Verify non-PHI content is preserved
        assert "Notes: Patient reports improved mood" in sanitized_list

    def test_sanitize_empty_values(self):
        """Test sanitization of empty values."""
        # Empty string
        assert self.sanitizer.sanitize("") == ""
        
        # Empty dict
        assert self.sanitizer.sanitize({}) == {}
        
        # Empty list
        assert self.sanitizer.sanitize([]) == []
        
        # None
        assert self.sanitizer.sanitize(None) == "None"

    def test_sanitize_non_string_values(self):
        """Test sanitization of non-string values."""
        # Integer
        assert self.sanitizer.sanitize(42) == "42"
        
        # Float
        assert self.sanitizer.sanitize(3.14) == "3.14"
        
        # Boolean
        assert self.sanitizer.sanitize(True) == "True"

    def test_sanitize_mixed_data(self):
        """Test sanitization of mixed data types."""
        mixed_data = {
            "patient": self.patient_name,
            "age": 42,
            "active": True,
            "notes": [
                f"Patient {self.patient_name} contacted via {self.patient_email}",
                "Follow-up scheduled for next week"
            ]
        }
        
        sanitized_data = self.sanitizer.sanitize(mixed_data)
        
        # Verify PHI is redacted
        assert sanitized_data["patient"] != self.patient_name
        assert self.patient_name not in sanitized_data["notes"][0]
        assert self.patient_email not in sanitized_data["notes"][0]
        
        # Verify non-PHI content is preserved
        assert sanitized_data["age"] == 42
        assert sanitized_data["active"] is True
        assert "Follow-up scheduled for next week" in sanitized_data["notes"][1]

    def test_sanitize_preserves_structure(self):
        """Test that sanitization preserves the original data structure."""
        # Test with dictionary
        dict_sanitized = self.sanitizer.sanitize(self.dict_with_phi)
        assert isinstance(dict_sanitized, dict)
        assert set(dict_sanitized.keys()) == set(self.dict_with_phi.keys())

        # Test with list
        list_sanitized = self.sanitizer.sanitize(self.list_with_phi)
        assert isinstance(list_sanitized, list)
        assert len(list_sanitized) == len(self.list_with_phi)

        # Test with string
        string_sanitized = self.sanitizer.sanitize(self.text_with_phi)
        assert isinstance(string_sanitized, str)


class TestCustomPHISanitizer:
    """Test cases for PHI sanitization with custom patterns."""

    # Define custom patterns using PHISanitizer's internal structure
    CUSTOM_PATTERNS = [
        (pattern, replacement) for pattern, replacement in PHISanitizer._PHI_PATTERNS
    ] + [
        (re.compile(r"\bEmployeeID:\s*\d+\b", re.IGNORECASE), "[REDACTED EMPLOYEE ID]"),
        (re.compile(r"\bProjectCode:\s*[A-Z]{3}-\d{4}\b"), "[REDACTED PROJECT CODE]"),
    ]

    def setup_method(self):
        """Set up test fixtures for custom sanitization."""
        self.sanitizer = PHISanitizer(additional_patterns=self.CUSTOM_PATTERNS)
        self.text_with_phi = "EmployeeID: 1234, ProjectCode: ABC-1234"

    def test_custom_patterns_in_string(self):
        """Test custom patterns in string sanitization."""
        sanitized_text = self.sanitizer.sanitize(self.text_with_phi)
        assert "[REDACTED EMPLOYEE ID]" in sanitized_text
        assert "[REDACTED PROJECT CODE]" in sanitized_text

    def test_custom_patterns_in_dict(self):
        """Test custom patterns in dictionary sanitization."""
        dict_with_phi = {"employee_id": "EmployeeID: 1234", "project_code": "ProjectCode: ABC-1234"}
        sanitized_dict = self.sanitizer.sanitize(dict_with_phi)
        assert "[REDACTED EMPLOYEE ID]" in sanitized_dict["employee_id"]
        assert "[REDACTED PROJECT CODE]" in sanitized_dict["project_code"]