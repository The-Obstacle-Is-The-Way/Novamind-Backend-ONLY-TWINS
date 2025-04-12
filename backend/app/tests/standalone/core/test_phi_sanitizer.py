"""
Tests for the PHI sanitization utilities.
"""
import pytest
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
    "address": self.patient_address
    },
    "medical_info": {
    "mrn": self.patient_mrn,
    "diagnosis": "Depression",
    "severity": "Moderate"
    },
    "non_phi_data": {
    "appointment_type": "Follow-up",
    "duration_minutes": 30
    }
    }
        
        # List with PHI
    self.list_with_phi = [
    f"Name: {self.patient_name}",
    f"DOB: {self.patient_dob}",
    f"Contact: {self.patient_email}",
    "Notes: Patient reports improved mood",
    f"ID: {self.patient_mrn}"
    ]
    
    def test_sanitize_string(self):
        """Test that strings containing PHI are properly sanitized."""
        sanitized = self.sanitizer.sanitize(self.text_with_phi)
        
        # Verify PHI is redacted
    assert self.patient_name not in sanitized
    assert self.patient_email not in sanitized
    assert self.patient_ssn not in sanitized
    assert self.patient_phone not in sanitized
    assert self.patient_address not in sanitized
    assert self.patient_dob not in sanitized
    assert self.patient_mrn not in sanitized
        
        # Verify redaction markers are present
    assert "[REDACTED]" in sanitized
    
    def test_sanitize_dict(self):
        """Test that dictionaries containing PHI are properly sanitized."""
        sanitized = self.sanitizer.sanitize(self.dict_with_phi)
        
        # Check that PHI fields are sanitized
    assert sanitized["name"] != self.patient_name
    assert sanitized["contact"]["email"] != self.patient_email
    assert sanitized["contact"]["phone"] != self.patient_phone
    assert sanitized["demographics"]["dob"] != self.patient_dob
    assert sanitized["demographics"]["ssn"] != self.patient_ssn
    assert sanitized["demographics"]["address"] != self.patient_address
    assert sanitized["medical_info"]["mrn"] != self.patient_mrn
        
        # Non-PHI data should be preserved
    assert sanitized["non_phi_data"]["appointment_type"] == "Follow-up"
    assert sanitized["non_phi_data"]["duration_minutes"] == 30
    assert sanitized["medical_info"]["diagnosis"] == "Depression"
    assert sanitized["medical_info"]["severity"@pytest.mark.standalone()
] == "Moderate"
    
    def test_sanitize_list(self):
        """Test that lists containing PHI are properly sanitized."""
        sanitized = self.sanitizer.sanitize(self.list_with_phi)
        
        # Check that PHI entries are sanitized
        for item in sanitized:
            assert self.patient_name not in item
            assert self.patient_email not in item
            assert self.patient_dob not in item
            assert self.patient_mrn not in item
        
        # Non-PHI entries should be preserved
    assert "Notes: Patient reports improved mood" in sanitized
    
    def test_sanitize_complex_nested_structure(self):
        """Test sanitization of complex nested data structures with PHI."""
        complex_structure = {
            "patients": [
                {
                    "details": self.dict_with_phi,
                    "notes": self.list_with_phi,
                    "summary": self.text_with_phi
                },
                {
                    "details": {"name": "Another Patient", "id": "12345"},
                    "notes": ["General note"]
                }
            ],
            "metadata": {
                "generated_by": "Test System",
                "timestamp": "2025-04-10T00:00:00Z"
            }
        }
        
    sanitized = self.sanitizer.sanitize(complex_structure)
        
        # Verify PHI is redacted at all levels
    patient_details = sanitized["patients"][0]["details"]
    patient_notes = sanitized["patients"][0]["notes"]
    patient_summary = sanitized["patients"][0]["summary"]
        
    assert patient_details["name"] != self.patient_name
    assert patient_details["contact"]["email"] != self.patient_email
        
    for note in patient_notes:
    assert self.patient_name not in note
    assert self.patient_email not in note
        
    assert self.patient_name not in patient_summary
    assert self.patient_ssn not in patient_summary
        
        # Non-PHI should remain intact
    assert sanitized["metadata"]["generated_by"] == "Test System"
    assert sanitized["metadata"]["timestamp"] == "2025-04-10T00:00:00Z"
    
    def test_sanitize_with_custom_patterns(self):
        """Test sanitization with custom PHI patterns."""
        # Create sanitizer with custom patterns
        custom_sanitizer = PHISanitizer()
            additional_patterns=[
                r"Depression",  # Now treat "Depression" as PHI
                r"Moderate"     # Now treat "Moderate" as PHI
            ]
(        )
        
    sanitized = custom_sanitizer.sanitize(self.dict_with_phi)
        
        # Standard PHI should be sanitized
    assert sanitized["name"] != self.patient_name
        
        # Custom patterns should also be sanitized
    assert sanitized["medical_info"]["diagnosis"] != "Depression" # Corrected key and removed marker
    assert sanitized["medical_info"]["severity"] != "Moderate"
    
    def test_sanitization_preserves_structure(self):
        """Test that sanitization preserves the structure of the input data."""
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
    assert isinstance(string_sanitized, str) # Ensure no hidden characters