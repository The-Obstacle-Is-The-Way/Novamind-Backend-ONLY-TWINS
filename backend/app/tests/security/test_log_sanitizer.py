# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock

from app.infrastructure.security.log_sanitizer import LogSanitizer


@pytest.mark.db_required()
class TestLogSanitizer:
            """
    Tests for the LogSanitizer to ensure PHI is properly redacted from logs.
    
    These tests verify HIPAA compliance in logging by ensuring:
        1. All PHI patterns are correctly identified and redacted
    2. No PHI leakage occurs in various log formats
    3. The sanitizer handles edge cases correctly
    """
@pytest.fixture
    def log_sanitizer(self):
        """Create a LogSanitizer instance for testing."""    return LogSanitizer()
    def test_sanitize_patient_names(self, log_sanitizer):
            """Test that patient names are properly redacted."""
        # Arrange
            log_message = "Patient John Smith checked in at 4pm"
        
        # Act
            sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert
            assert "John Smith" not in sanitized
            assert "[REDACTED-NAME]" in sanitized
            assert "Patient [REDACTED-NAME] checked in at 4pm" == sanitized
    def test_sanitize_email_addresses(self, log_sanitizer):
                """Test that email addresses are properly redacted."""
        # Arrange
                log_message = "Sent reminder to patient@example.com for their appointment"
        
        # Act
                sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert
                assert "patient@example.com" not in sanitized
                assert "[REDACTED-EMAIL]" in sanitized
                assert "Sent reminder to [REDACTED-EMAIL] for their appointment" == sanitized
    def test_sanitize_phone_numbers(self, log_sanitizer):
                    """Test that phone numbers are properly redacted."""
        # Test various phone number formats
                    phone_formats = [
                    "Called patient at (555) 123-4567",
                    "SMS sent to 555-123-4567",
                    "New contact: 5551234567",
                    "International: +1-555-123-4567"
                    ]
        
                    for log_message in phone_formats:
            # Act
                    sanitized = log_sanitizer.sanitize(log_message)
            
            # Assert
                    assert "555" not in sanitized
                    assert "[REDACTED-PHONE]" in sanitized
    def test_sanitize_addresses(self, log_sanitizer):
                        """Test that addresses are properly redacted."""
        # Arrange
                        log_message = "Sending mail to 123 Main St, Anytown CA 90210"
        
        # Act
                        sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert
                        assert "123 Main St" not in sanitized
                        assert "Anytown" not in sanitized
                        assert "90210" not in sanitized
                        assert "[REDACTED-ADDRESS]" in sanitized
    def test_sanitize_dates_of_birth(self, log_sanitizer):
                            """Test that dates of birth are properly redacted."""
        # Test various date formats
                            date_formats = [
                            "Patient DOB: 01/02/1980",
                            "Born on January 2, 1980",
                            "DOB: 1980-01-02",
                            "02-Jan-1980"
                            ]
        
                            for log_message in date_formats:
            # Act
                            sanitized = log_sanitizer.sanitize(log_message)
            
            # Assert - should not contain any part of the date
                            assert "1980" not in sanitized
                            assert "01/02" not in sanitized
                            assert "January 2" not in sanitized
                            assert "Jan" not in sanitized
                            assert "[REDACTED-DOB]" in sanitized
    def test_sanitize_medical_record_numbers(self, log_sanitizer):
                                """Test that medical record numbers are properly redacted."""
        # Arrange
                                log_message = "Accessed MRN: 12345678 for appointment scheduling"
        
        # Act
                                sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert
                                assert "12345678" not in sanitized
                                assert "[REDACTED-MRN]" in sanitized
    def test_sanitize_ssn(self, log_sanitizer):
                                    """Test that social security numbers are properly redacted."""
        # Test various SSN formats
                                    ssn_formats = [
                                    "SSN: 123-45-6789",
                                    "Social Security: 123456789",
                                    "SSN: 123 45 6789"
                                    ]
        
                                    for log_message in ssn_formats:
            # Act
                                    sanitized = log_sanitizer.sanitize(log_message)
            
            # Assert
                                    assert "123" not in sanitized
                                    assert "45" not in sanitized
                                    assert "6789" not in sanitized
                                    assert "[REDACTED-SSN]" in sanitized
    def test_sanitize_credit_card(self, log_sanitizer):
                                        """Test that credit card numbers are properly redacted."""
        # Arrange
                                        log_message = "Payment processed with card 4111-1111-1111-1111"
        
        # Act
                                        sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert
                                        assert "4111" not in sanitized
                                        assert "1111-1111-1111" not in sanitized
                                        assert "[REDACTED-CC]" in sanitized
    def test_sanitize_json_data(self, log_sanitizer):
                                            """Test that PHI in JSON is properly redacted."""
        # Arrange
                                            log_message = """Log: {"user": "patient1", "name": "John Smith", "email": "john@example.com"}"""
        
        # Act
                                            sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert
                                            assert "John Smith" not in sanitized
                                            assert "john@example.com" not in sanitized
                                            assert "[REDACTED-NAME]" in sanitized
                                            assert "[REDACTED-EMAIL]" in sanitized
    def test_sanitize_complex_mixed_content(self, log_sanitizer):
                                                """Test that complex mixed content with multiple PHI types is properly sanitized."""
        # Arrange
                                                log_message = (
                                                "Patient John Smith (DOB: 01/02/1980) with MRN 12345678 and ",
                                                "SSN 123-45-6789 contacted us from john@example.com and phone "
                                                "(555) 123-4567 regarding their appointment at 123 Main St."
                                                )
        
        # Act
                                                sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert - Check that all PHI is redacted
                                                assert "John Smith" not in sanitized
                                                assert "01/02/1980" not in sanitized
                                                assert "12345678" not in sanitized
                                                assert "123-45-6789" not in sanitized
                                                assert "john@example.com" not in sanitized
                                                assert "(555) 123-4567" not in sanitized
                                                assert "123 Main St" not in sanitized
        
        # Check for redaction markers
                                                assert "[REDACTED-NAME]" in sanitized
                                                assert "[REDACTED-DOB]" in sanitized
                                                assert "[REDACTED-MRN]" in sanitized
                                                assert "[REDACTED-SSN]" in sanitized
                                                assert "[REDACTED-EMAIL]" in sanitized
                                                assert "[REDACTED-PHONE]" in sanitized
                                                assert "[REDACTED-ADDRESS]" in sanitized
    def test_no_false_positives(self, log_sanitizer):
                                                    """Test that non-PHI data is not incorrectly redacted."""
        # Arrange - These should NOT be redacted
                                                    safe_messages = [
                                                    "Service restarted at 12:30pm",
                                                    "HTTP 404 error on /patient/search",
                                                    "Database query took 123.45ms",
                                                    "Loaded 5 records from cache",
                                                    "API version 2.0.1 initialized"
                                                    ]
        
        # Act & Assert
                                                    for message in safe_messages:
                                                    sanitized = log_sanitizer.sanitize(message)
                                                    assert sanitized  ==  message, f"False positive: {message} was incorrectly sanitized"
    def test_sanitize_preserves_log_structure(self, log_sanitizer):
                                                        """Test that sanitization preserves the overall log structure."""
        # Arrange
                                                        log_message = "ERROR [2023-01-02T15:30:45] Patient John Smith (ID: 12345) - Failed to schedule appointment"
        
        # Act
                                                        sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert - Structure is preserved, only PHI is redacted
                                                        assert "ERROR [2023-01-02T15:30:45]" in sanitized
                                                        assert "Failed to schedule appointment" in sanitized
                                                        assert "John Smith" not in sanitized
                                                        assert "[REDACTED-NAME]" in sanitized
    def test_sanitize_performance(self, log_sanitizer):
                                                            """Test that sanitization performs efficiently on large logs."""
        # Arrange
        # Create a large log message with repeated PHI patterns
                                                            large_log = " ".join(["Patient John Smith with email john@example.com called from 555-123-4567"] * 100)
        
        # Act
                                                            import time
                                                            start_time = time.time()
                                                            sanitized = log_sanitizer.sanitize(large_log)
                                                            end_time = time.time()
                                                            execution_time = end_time - start_time
        
        # Assert
                                                            assert "John Smith" not in sanitized
                                                            assert "john@example.com" not in sanitized
                                                            assert "555-123-4567" not in sanitized
        # Performance threshold - sanitization should be fast even on large logs
        # This is a reasonable threshold for large log processing
                                                            assert execution_time < 1.0, f"Sanitization took too long: {execution_time} seconds"
    def test_sanitizer_with_custom_patterns(self, log_sanitizer):
                                                                """Test that custom PHI patterns can be added and detected."""
        # Arrange - Add a custom pattern for patient IDs
                                                                with patch.object(log_sanitizer, 'add_custom_pattern') as mock_add:
                                                                log_sanitizer.add_custom_pattern('PATIENT-ID', r'P\d{6}')
                                                                mock_add.assert_called_once()
        
        # Create a message with the custom pattern
                                                                log_message = "Retrieved record for patient ID P123456"
        
        # Act
                                                                with patch.object(log_sanitizer, 'patterns', {:)
                                                                'PATIENT-ID': r'P\d{6}')
                                                                }):
                                                                sanitized = log_sanitizer.sanitize(log_message)
        
        # Assert
                                                                assert "P123456" not in sanitized
                                                                assert "[REDACTED-PATIENT-ID]" in sanitized
    def test_audit_trail_integration(self, log_sanitizer):
                                                                    """Test that sanitization is properly integrated with audit logging."""
        # Arrange
                                                                    from app.infrastructure.logging.audit_logger import AuditLogger
        
        # Mock the audit logger
                                                                    mock_audit_logger = MagicMock(spec=AuditLogger)
        
        # Sensitive message that should be sanitized before being passed to the audit logger
                                                                    sensitive_message = "Patient John Smith (SSN: 123-45-6789) accessed their records"
        
        # Act - simulate what would happen when log sanitizer is used with audit logger
                                                                    sanitized = log_sanitizer.sanitize(sensitive_message)
        # In production, the sanitized message would be passed to the audit logger
                                                                    mock_audit_logger.log_access.return_value = None
                                                                    mock_audit_logger.log_access(sanitized))
        
        # Assert
                                                                    assert "John Smith" not in sanitized
                                                                    assert "123-45-6789" not in sanitized
                                                                    mock_audit_logger.log_access.assert_called_once()
        # Check that the message passed to the audit logger was sanitized
                                                                    call_args = mock_audit_logger.log_access.call_args[0][0]
                                                                    assert "John Smith" not in call_args
                                                                    assert "123-45-6789" not in call_args


                                                                    if __name__ == "__main__":
                                                                    pytest.main(["-xvs", __file__])