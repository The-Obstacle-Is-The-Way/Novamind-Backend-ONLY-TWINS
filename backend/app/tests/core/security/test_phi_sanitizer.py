"""
Tests for the PHI sanitization utilities.
"""
import pytest
import re
from typing import Dict, List, Any, Union
from logging import LogRecord

# Corrected import path based on file search results
from app.infrastructure.security.phi.log_sanitizer import LogSanitizer, LogSanitizerConfig, PHIFormatter


class TestPHISanitizer:
    """Test cases for the PHI sanitization utilities."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.sanitizer = LogSanitizer()

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


# Mock PHIService for testing the infrastructure layer
class MockPHIService:
    def sanitize(self, data, sensitivity=None, replacement=None):
        if isinstance(data, str) and "PHI" in data:
            return "[SANITIZED]"
        return data

@pytest.fixture
def mock_phi_service(mocker):
    """Fixture to mock the core PHIService."""
    # Mock the instantiation within LogSanitizer
    mock_instance = MockPHIService()
    mocker.patch('app.infrastructure.security.phi.log_sanitizer.PHIService', return_value=mock_instance)
    return mock_instance

@pytest.fixture
def sanitizer_config():
    """Fixture for LogSanitizerConfig."""
    return LogSanitizerConfig(enabled=True)

@pytest.fixture
def log_sanitizer(sanitizer_config, mock_phi_service): # Ensure mock is active
    """Fixture for LogSanitizer instance."""
    # The mock_phi_service fixture ensures PHIService() inside LogSanitizer.__init__ returns the mock
    return LogSanitizer(config=sanitizer_config)

def test_log_sanitizer_init(log_sanitizer, sanitizer_config):
    """Test initialization of LogSanitizer."""
    assert log_sanitizer.config == sanitizer_config
    assert isinstance(log_sanitizer._phi_service, MockPHIService) # Check if the mock was injected

def test_log_sanitizer_sanitize_method(log_sanitizer, mock_phi_service):
    """Test the sanitize method delegates correctly."""
    assert log_sanitizer.sanitize("No sensitive data") == "No sensitive data"
    assert log_sanitizer.sanitize("Contains PHI data") == "[SANITIZED]"

def test_log_sanitizer_disabled(mock_phi_service):
    """Test sanitization is skipped when disabled."""
    config = LogSanitizerConfig(enabled=False)
    sanitizer = LogSanitizer(config=config)
    assert sanitizer.sanitize("Contains PHI data") == "Contains PHI data"

@pytest.fixture
def log_record():
    """Fixture for a sample LogRecord."""
    # Use dummy values for required LogRecord attributes
    return LogRecord(
        name='test_logger',
        level=20, # INFO
        pathname='/path/to/test.py',
        lineno=10,
        msg="Log message with PHI",
        args=[],
        exc_info=None,
        func='test_func'
    )

def test_log_sanitizer_sanitize_log_record(log_sanitizer, log_record, mock_phi_service):
    """Test sanitization of a LogRecord message."""
    sanitized_record = log_sanitizer.sanitize_log_record(log_record)
    # getMessage() handles the formatting, which might be empty if args were used and cleared
    # Instead, check the msg attribute directly after potential sanitization
    assert sanitized_record.getMessage() == "[SANITIZED]" # Check the final formatted msg
    # Verify args are cleared as per implementation
    assert sanitized_record.args == []

def test_log_sanitizer_sanitize_log_record_with_exception(log_sanitizer, mock_phi_service):
    """Test sanitization of LogRecord exception info."""
    try:
        raise ValueError("Exception with PHI details")
    except ValueError as e:
        exc_info = (type(e), e, e.__traceback__)

    record = LogRecord(
        name='test_exception_logger',
        level=40, # ERROR
        pathname='/path/to/error.py',
        lineno=25,
        msg="An error occurred",
        args=[],
        exc_info=exc_info,
        func='error_func'
    )

    sanitized_record = log_sanitizer.sanitize_log_record(record)

    assert sanitized_record.exc_info is not None
    exc_type, sanitized_exc_value, exc_traceback = sanitized_record.exc_info
    assert isinstance(sanitized_exc_value, ValueError)
    assert str(sanitized_exc_value) == "[SANITIZED]"

# --- Tests for PHIFormatter ---

@pytest.fixture
def phi_formatter(sanitizer_config, mock_phi_service): # Mock service needed for formatter's sanitizer
    """Fixture for PHIFormatter instance."""
    # Pass the config to the formatter
    return PHIFormatter(fmt='%(levelname)s:%(name)s:%(message)s', sanitizer_config=sanitizer_config)

def test_phi_formatter_format(phi_formatter, log_record):
    """Test the format method sanitizes the final output."""
    log_record.msg = "Log message with PHI" # Reset msg for this test
    log_record.args = [] # Ensure args are empty for direct msg check
    formatted_sanitized = phi_formatter.format(log_record)
    assert formatted_sanitized == "INFO:test_logger:[SANITIZED]"

def test_phi_formatter_format_no_phi(phi_formatter, log_record):
    """Test the format method when no PHI is present."""
    log_record.msg = "Normal log message"
    log_record.args = []
    formatted_sanitized = phi_formatter.format(log_record)
    assert formatted_sanitized == "INFO:test_logger:Normal log message"

def test_phi_formatter_format_with_args(phi_formatter, mock_phi_service):
    """Test formatting with arguments (handled by standard Formatter + final sanitization)."""
    record = LogRecord(
        name='test_args_logger',
        level=20,
        pathname='/path/to/args.py',
        lineno=5,
        msg="User %s action failed for patient %s",
        args=["admin", "ID123 contains PHI"], # Patient ID contains PHI
        exc_info=None,
        func='action_func'
    )
    formatted_sanitized = phi_formatter.format(record)
    # The full message "User admin action failed for patient ID123 contains PHI" is sanitized
    assert formatted_sanitized == "INFO:test_args_logger:[SANITIZED]"

def test_phi_formatter_format_exception(phi_formatter, mock_phi_service):
    """Test formatting and sanitizing exceptions."""
    try:
        raise RuntimeError("Critical error with PHI payload")
    except RuntimeError as e:
        ei = (type(e), e, e.__traceback__)

    formatted_exception = phi_formatter.formatException(ei)
    # Assuming the default exception format includes the message
    assert "[SANITIZED]" in formatted_exception
    assert "RuntimeError" in formatted_exception # Type should remain