# -*- coding: utf-8 -*-
"""
Enhanced unit tests for the HIPAA-compliant logging utilities.

This test suite provides comprehensive coverage for the enhanced PHI detection
and sanitization modules, focusing on HIPAA compliance and PHI protection.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from app.core.utils.enhanced_phi_detector import (
    EnhancedPHIDetector, 
    EnhancedPHISanitizer, 
    EnhancedPHISecureLogger,
    get_enhanced_phi_secure_logger
)
from app.core.utils.phi_sanitizer import PHIType


class TestEnhancedPHIDetector:
    """Comprehensive tests for the EnhancedPHIDetector class."""
    
    def test_contains_phi_with_standard_patterns(self):
        """Test PHI detection with standard patterns."""
        # Test email detection
        text_with_email = "Contact user@example.com for support"
        assert EnhancedPHIDetector.contains_phi(text_with_email)
        
        # Test SSN detection
        text_with_ssn = "SSN: 123-45-6789"
        assert EnhancedPHIDetector.contains_phi(text_with_ssn)
        
        # Test phone detection
        text_with_phone = "Call (555) 123-4567"
        assert EnhancedPHIDetector.contains_phi(text_with_phone)
    
    def test_contains_phi_with_enhanced_patterns(self):
        """Test PHI detection with enhanced patterns."""
        # Test name detection with enhanced pattern
        text_with_name = "Dr. John Smith is your new physician"
        assert EnhancedPHIDetector.contains_phi(text_with_name)
        
        # Test address detection with enhanced pattern
        text_with_address = "Appointment at 123 Medical Boulevard"
        assert EnhancedPHIDetector.contains_phi(text_with_address)
        
        # Test MRN detection with enhanced pattern
        text_with_mrn = "Patient ID: ABC1234567"
        assert EnhancedPHIDetector.contains_phi(text_with_mrn)
    
    def test_contains_phi_with_medical_context(self):
        """Test PHI detection with medical context combined with potential identifiers."""
        text_with_context = "Patient Johnson reported symptoms of dizziness"
        assert EnhancedPHIDetector.contains_phi(text_with_context)
        
        # Test with numbers in medical context
        text_with_id = "Patient diagnosis 12345 confirmed"
        assert EnhancedPHIDetector.contains_phi(text_with_id)
    
    def test_detect_phi_types(self):
        """Test detection of specific PHI types with the enhanced detector."""
        # Create test text with multiple PHI types
        test_text = "Patient John Doe (SSN: 123-45-6789) can be reached at john.doe@example.com or (555) 123-4567"
        
        # Detect PHI types
        detected = EnhancedPHIDetector.detect_phi_types(test_text)
        
        # Check that all types were detected
        phi_types = [phi_type for phi_type, _ in detected]
        assert PHIType.SSN in phi_types
        assert PHIType.EMAIL in phi_types
        assert PHIType.PHONE in phi_types
        assert PHIType.NAME in phi_types
        
        # Check that PHI values were correctly matched
        phi_values = [value for _, value in detected]
        assert "123-45-6789" in phi_values
        assert "john.doe@example.com" in phi_values
        assert "(555) 123-4567" in phi_values
    
    def test_no_phi_in_regular_text(self):
        """Test that regular non-PHI text is not flagged."""
        regular_text = "This is a standard message without any PHI"
        assert not EnhancedPHIDetector.contains_phi(regular_text)
        
        # Technical text
        tech_text = "Error code 404 occurred at module LoadBalance.function()"
        assert not EnhancedPHIDetector.contains_phi(tech_text)


class TestEnhancedPHISanitizer:
    """Tests for the EnhancedPHISanitizer class."""
    
    def test_sanitize_text(self):
        """Test sanitization of text containing PHI."""
        # Create test text with PHI
        text_with_phi = "Patient John Doe (SSN: 123-45-6789) can be reached at john.doe@example.com"
        
        # Sanitize
        sanitized = EnhancedPHISanitizer.sanitize_text(text_with_phi)
        
        # Check PHI has been removed
        assert "John Doe" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "john.doe@example.com" not in sanitized
        
        # Check anonymized values were added
        assert "ANONYMIZED_NAME" in sanitized or "ANONYMIZED" in sanitized
        assert "000-00-0000" in sanitized or "ANONYMIZED" in sanitized
    
    def test_create_safe_log_message(self):
        """Test creation of safe log messages."""
        # Create log message with PHI
        log_message = "User {} accessed records for patient {}"
        user = "admin"
        patient = "John Smith (MRN: 12345678)"
        
        # Create safe log message
        safe_message = EnhancedPHISanitizer.create_safe_log_message(
            log_message, user, patient
        )
        
        # Check PHI has been sanitized
        assert "John Smith" not in safe_message
        assert "12345678" not in safe_message
    
    def test_sanitize_structured_data(self):
        """Test sanitization of structured data."""
        # Create structured data with PHI
        data = {
            "patient": {
                "name": "John Doe",
                "ssn": "123-45-6789",
                "contact": {
                    "email": "john.doe@example.com",
                    "phone": "(555) 123-4567"
                },
                "appointment_date": "2025-06-15"  # Future date should be preserved
            },
            "doctor": "Dr. Jane Smith",
            "notes": "Patient reported symptoms"
        }
        
        # Sanitize data
        sanitized = EnhancedPHISanitizer.sanitize_structured_data(data)
        
        # Check PHI was sanitized
        assert sanitized["patient"]["name"] != "John Doe"
        assert sanitized["patient"]["ssn"] != "123-45-6789"
        assert sanitized["patient"]["contact"]["email"] != "john.doe@example.com"
        assert sanitized["doctor"] != "Dr. Jane Smith"
        
        # Check appointment date was preserved
        assert sanitized["patient"]["appointment_date"] == "2025-06-15"


class TestEnhancedPHISecureLogger:
    """Tests for the EnhancedPHISecureLogger class."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock underlying logger."""
        
    return MagicMock()
    
    def test_secure_logger_initialization(self):
        """Test initialization of secure logger."""
        logger = EnhancedPHISecureLogger("test_logger")
        assert isinstance(logger.logger, logging.Logger)
        assert logger.logger.name == "test_logger"
    
    def test_debug_log_sanitization(self, mock_logger):
        """Test sanitization of debug logs."""
        # Setup
        secure_logger = EnhancedPHISecureLogger("test")
        secure_logger.logger = mock_logger
        
        # Log with PHI
        secure_logger.debug("Debug log with SSN: 123-45-6789")
        
        # Check sanitization
        call_args = mock_logger.debug.call_args[0][0]
        assert "123-45-6789" not in call_args
    
    def test_info_log_sanitization(self, mock_logger):
        """Test sanitization of info logs."""
        # Setup
        secure_logger = EnhancedPHISecureLogger("test")
        secure_logger.logger = mock_logger
        
        # Log with PHI
        secure_logger.info("Info log with email: user@example.com")
        
        # Check sanitization
        call_args = mock_logger.info.call_args[0][0]
        assert "user@example.com" not in call_args
    
    def test_error_log_sanitization(self, mock_logger):
        """Test sanitization of error logs."""
        # Setup
        secure_logger = EnhancedPHISecureLogger("test")
        secure_logger.logger = mock_logger
        
        # Log with PHI
        secure_logger.error("Error log with phone: (555) 123-4567")
        
        # Check sanitization
        call_args = mock_logger.error.call_args[0][0]
        assert "(555) 123-4567" not in call_args
    
    def test_exception_log_sanitization(self, mock_logger):
        """Test sanitization of exception logs."""
        # Setup
        secure_logger = EnhancedPHISecureLogger("test")
        secure_logger.logger = mock_logger
        
        # Log with PHI
        secure_logger.exception("Exception with patient name: John Smith")
        
        # Check sanitization
        call_args = mock_logger.exception.call_args[0][0]
        assert "John Smith" not in call_args
        assert mock_logger.exception.call_args[1].get('exc_info') is True


def test_get_enhanced_phi_secure_logger():
    """Test getting an enhanced PHI secure logger."""
    logger = get_enhanced_phi_secure_logger("test_logger")
    
    # Verify it's the right type
    assert isinstance(logger, EnhancedPHISecureLogger)
    assert logger.logger.name == "test_logger"