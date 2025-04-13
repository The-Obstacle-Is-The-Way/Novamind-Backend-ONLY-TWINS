import json
import re
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.security.log_sanitizer import LogSanitizer, PHIDetector


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
        input_text = "Patient name: John Smith"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "John Smith" not in sanitized
        assert "name" in sanitized
        assert "[REDACTED:NAME]" in sanitized
        
    @pytest.mark.standalone()
    def test_sanitize_string_with_multiple_phi(self, sanitizer):
        """Test sanitization of strings containing multiple PHI elements."""
        input_text = "Patient John Smith born on 01/15/1980 with phone (555) 123-4567"
        sanitized = sanitizer.sanitize_text(input_text)
        assert "John Smith" not in sanitized
        assert "01/15/1980" not in sanitized
        assert "(555) 123-4567" not in sanitized
        assert "[REDACTED:NAME]" in sanitized
        assert "[REDACTED:DOB]" in sanitized
        assert "[REDACTED:PHONE]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_dict_with_phi(self, sanitizer, sample_phi_data):
        """Test sanitization of dictionary data containing PHI."""
        sanitized_data = sanitizer.sanitize_dict(sample_phi_data)
        
        # Check all PHI values are sanitized
        assert sanitized_data["name"] != "John Smith"
        assert sanitized_data["ssn"] != "123-45-6789"
        assert sanitized_data["dob"] != "01/15/1980"
        assert sanitized_data["phone"] != "(555) 123-4567"
        assert sanitized_data["email"] != "john.smith@example.com"
        assert sanitized_data["address"] != "123 Main St, Anytown, CA 12345"
        assert sanitized_data["mrn"] != "MRN12345678"
        assert sanitized_data["insurance_id"] != "INS123456789"
        
        # Check redaction format
        assert "[REDACTED:NAME]" in sanitized_data["name"]
        assert "[REDACTED:SSN]" in sanitized_data["ssn"]

    @pytest.mark.standalone()
    def test_sanitize_nested_dict_with_phi(self, sanitizer):
        """Test sanitization of nested dictionaries containing PHI."""
        # Create nested data with PHI
        nested_data = {
            "patient": {
                "demographics": {
                    "name": "Jane Doe",
                    "dob": "02/20/1985",
                    "ssn": "987-65-4321"
                },
                "contact": {
                    "phone": "(555) 987-6543",
                    "email": "jane.doe@example.com"
                }
            },
            "non_phi_field": "This data should be untouched"
        }
        
        sanitized_data = sanitizer.sanitize_dict(nested_data)

        # Check nested PHI is sanitized
        assert sanitized_data["patient"]["demographics"]["name"] != "Jane Doe"
        assert sanitized_data["patient"]["demographics"]["ssn"] != "987-65-4321"
        assert sanitized_data["patient"]["contact"]["phone"] != "(555) 987-6543"
        assert sanitized_data["patient"]["contact"]["email"] != "jane.doe@example.com"
        
        # Check non-PHI data is preserved
        assert sanitized_data["non_phi_field"] == "This data should be untouched"

    @pytest.mark.standalone()
    def test_sanitize_list_with_phi(self, sanitizer):
        """Test sanitization of lists containing PHI."""
        list_data = [
            "Patient John Doe",
            "SSN: 987-65-4321",
            "Contact: (555) 987-6543",
            "Non-PHI item"
        ]
        
        sanitized_list = sanitizer.sanitize_list(list_data)
        
        # Check PHI items are sanitized
        assert "John Doe" not in sanitized_list[0]
        assert "987-65-4321" not in sanitized_list[1]
        assert "(555) 987-6543" not in sanitized_list[2]
        
        # Check non-PHI item is preserved
        assert sanitized_list[3] == "Non-PHI item"
        
        # Check redaction format
        assert "[REDACTED:NAME]" in sanitized_list[0]
        assert "[REDACTED:SSN]" in sanitized_list[1]
        assert "[REDACTED:PHONE]" in sanitized_list[2]

    @pytest.mark.standalone()
    def test_sanitize_complex_structure(self, sanitizer):
        """Test sanitization of complex nested structures with PHI."""
        # Create a complex data structure with PHI
        complex_data = {
            "facility": "Medical Center",
            "patients": [
                {
                    "name": "John Smith",
                    "dob": "01/15/1980",
                    "records": [
                        {"date": "2023-01-15", "ssn": "123-45-6789"},
                        {"date": "2023-02-20", "phone": "(555) 123-4567"}
                    ]
                },
                {
                    "name": "Jane Doe",
                    "dob": "02/20/1985",
                    "records": []
                }
            ]
        }
        
        sanitized_data = sanitizer.sanitize_dict(complex_data)

        # Check first patient's PHI is sanitized
        assert sanitized_data["patients"][0]["name"] != "John Smith"
        assert "123-45-6789" not in str(sanitized_data["patients"][0]["records"][0])
        assert "(555) 123-4567" not in str(sanitized_data["patients"][0]["records"][1])
        
        # Check second patient's PHI is sanitized
        assert sanitized_data["patients"][1]["name"] != "Jane Doe"
        
        # Check non-PHI data is preserved
        assert sanitized_data["facility"] == "Medical Center"
        assert sanitized_data["patients"][0]["records"][0]["date"] == "2023-01-15"
        assert sanitized_data["patients"][0]["records"][1]["date"] == "2023-02-20"

    @pytest.mark.standalone()
    def test_sanitize_phi_in_logs(self, sanitizer):
        """Test sanitization of PHI in log messages."""
        # Create a log message with PHI
        log_message = "Error processing patient John Smith (SSN: 123-45-6789) due to system failure"

        # Sanitize the log message
        sanitized_log = sanitizer.sanitize_text(log_message)
        
        # Check PHI is sanitized
        assert "John Smith" not in sanitized_log
        assert "123-45-6789" not in sanitized_log
        
        # Check context is preserved
        assert "Error processing patient" in sanitized_log
        assert "due to system failure" in sanitized_log
        
        # Check redaction format
        assert "[REDACTED:NAME]" in sanitized_log
        assert "[REDACTED:SSN]" in sanitized_log

    @pytest.mark.standalone()
    def test_phi_detection_integration(self, sanitizer):
        """Test integration with PHI detector component."""
        with patch('app.infrastructure.security.log_sanitizer.PHIDetector') as mock_detector:
            # Setup mock PHI detector
            mock_detector.return_value.detect.return_value = [(0, 10, "NAME")]
            
            # Create a test string
            test_text = "John Smith is a patient"
            
            # Test sanitization with the mocked detector
            sanitized = sanitizer.sanitize_text(test_text)
            
            # Verify that the PHI detector was used
            mock_detector.return_value.detect.assert_called_once()
            assert "John Smith" not in sanitized
            assert "[REDACTED:NAME]" in sanitized

    @pytest.mark.standalone()
    def test_phi_sanitizer_performance(self, sanitizer):
        """Test sanitizer performance with large nested structures."""
        # Create a large dataset with PHI
        large_data = {
            "patients": [
                {"name": f"Patient {i}", "ssn": f"123-45-{i:04}"} for i in range(100)
            ],
            "records": [
                {"patient_id": i, "details": f"SSN: 123-45-{i:04}"} for i in range(100)
            ]
        }
        
        # Measure sanitization time
        import time
        start = time.time()
        sanitized_data = sanitizer.sanitize_dict(large_data)
        end = time.time()
        
        # Check sanitization was performed
        for patient in sanitized_data["patients"]:
            assert "Patient" not in patient["name"]
            assert "123-45-" not in patient["ssn"]
        
        for record in sanitized_data["records"]:
            assert "123-45-" not in record["details"]
        
        # Performance assertion - should complete in a reasonable time
        # This is a flexible assertion as performance will vary by environment
        assert end - start < 10.0, "Sanitization took too long"

    @pytest.mark.standalone()
    def test_preservation_of_non_phi(self, sanitizer):
        """Test that non-PHI data is preserved during sanitization."""
        mixed_data = {
            "patient_id": "PT12345",  # Not PHI
            "name": "John Smith",     # PHI
            "ssn": "123-45-6789",     # PHI
            "diagnosis_code": "F41.1", # Not PHI
            "medication_id": "MED123", # Not PHI
            "email": "john.smith@example.com", # PHI
            "status": "Active",       # Not PHI
            "priority": 1,            # Not PHI
            "is_insured": True        # Not PHI
        }
        
        sanitized_data = sanitizer.sanitize_dict(mixed_data)
        
        # Check PHI is sanitized
        assert sanitized_data["name"] != "John Smith"
        assert sanitized_data["ssn"] != "123-45-6789"
        assert sanitized_data["email"] != "john.smith@example.com"
        
        # Check non-PHI is preserved
        assert sanitized_data["patient_id"] == "PT12345"
        assert sanitized_data["diagnosis_code"] == "F41.1"
        assert sanitized_data["medication_id"] == "MED123"
        assert sanitized_data["status"] == "Active"
        assert sanitized_data["priority"] == 1
        assert sanitized_data["is_insured"] is True

    @pytest.mark.standalone()
    def test_sanitizer_edge_cases(self, sanitizer):
        """Test sanitizer with edge cases and unusual inputs."""
        # Test with None input
        assert sanitizer.sanitize_dict(None) is None
        assert sanitizer.sanitize_text(None) is None
        assert sanitizer.sanitize_list(None) is None

        # Test with empty string
        assert sanitizer.sanitize_text("") == ""
        
        # Test with empty dict
        assert sanitizer.sanitize_dict({}) == {}
        
        # Test with empty list
        assert sanitizer.sanitize_list([]) == []
        
        # Test with mixed data types
        mixed_type_data = {
            "text": "John Smith",
            "number": 12345,
            "boolean": True,
            "none_value": None,
            "list": ["Jane Doe", 123, None]
        }
        
        sanitized_mixed = sanitizer.sanitize_dict(mixed_type_data)
        
        # Check PHI is sanitized
        assert sanitized_mixed["text"] != "John Smith"
        assert "Jane Doe" not in str(sanitized_mixed["list"])
        
        # Check non-PHI data types are preserved
        assert sanitized_mixed["number"] == 12345
        assert sanitized_mixed["boolean"] is True
        assert sanitized_mixed["none_value"] is None

    @pytest.mark.standalone()
    def test_redaction_format_consistency(self, sanitizer):
        """Test that redaction format is consistent."""
        # Create test data with various PHI types
        test_data = {
            "name": "John Smith",
            "ssn": "123-45-6789",
            "phone": "(555) 123-4567",
            "mrn": "MRN123456789"
        }
        
        # Sanitize the data
        sanitized = json.dumps(sanitizer.sanitize_dict(test_data))
        
        # Check for consistent redaction format with regex
        redaction_pattern = re.compile(r'\[REDACTED:(\w+)\]')
        matches = redaction_pattern.findall(sanitized)

        # We should have redactions and they should be in the expected format
        assert matches
        
        # All redaction types should be uppercase
        for match in matches:
            assert match.isupper()
