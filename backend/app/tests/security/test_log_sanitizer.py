# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch, MagicMock
import time

from app.infrastructure.security.log_sanitizer import LogSanitizer


class TestLogSanitizer(unittest.TestCase):
    """Test suite for log sanitizer to prevent PHI exposure."""

    def setUp(self):
        """Set up test environment."""
        self.log_sanitizer = LogSanitizer()

        # Test log messages with various types of PHI
        self.test_logs = {
            "patient_name": "Patient John Smith visited on 2023-01-01",
            "patient_email": "Contact patient at john.smith@example.com for follow-up",
            "patient_phone": "Patient phone number is 555-123-4567",
            "patient_address": "Patient lives at 123 Main St, Anytown, CA 90210",
            "patient_ssn": "Patient SSN is 123-45-6789",
            "patient_mrn": "Patient MRN#987654 admitted to ward",
            "patient_dob": "Patient DOB is 01/15/1980",
            "multiple_phi": "Patient John Smith, DOB 01/15/1980, SSN 123-45-6789 lives at 123 Main St",
            "no_phi": "System initialized with error code 0x123",
            "mixed_case": "PATIENT JOHN SMITH has email JOHN.SMITH@EXAMPLE.COM",
        }

        # Expected patterns after sanitization
        self.expected_patterns = {
            "patient_name": "Patient [REDACTED_NAME] visited on 2023-01-01",
            "patient_email": "Contact patient at [REDACTED_EMAIL] for follow-up",
            "patient_phone": "Patient phone number is [REDACTED_PHONE]",
            "patient_address": "Patient lives at [REDACTED_ADDRESS]",
            "patient_ssn": "Patient SSN is [REDACTED_SSN]",
            "patient_mrn": "Patient MRN#[REDACTED_MRN] admitted to ward",
            "patient_dob": "Patient DOB is [REDACTED_DOB]",
            "multiple_phi": "Patient [REDACTED_NAME], DOB [REDACTED_DOB], SSN [REDACTED_SSN] lives at [REDACTED_ADDRESS]",
            "no_phi": "System initialized with error code 0x123",
            "mixed_case": "PATIENT [REDACTED_NAME] has email [REDACTED_EMAIL]",
        }

    def test_sanitize_patient_names(self):
        """Test sanitization of patient names."""
        log_key = "patient_name"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("John Smith", sanitized)

    def test_sanitize_email_addresses(self):
        """Test sanitization of email addresses."""
        log_key = "patient_email"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("john.smith@example.com", sanitized)

    def test_sanitize_phone_numbers(self):
        """Test sanitization of phone numbers."""
        log_key = "patient_phone"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("555-123-4567", sanitized)

    def test_sanitize_addresses(self):
        """Test sanitization of physical addresses."""
        log_key = "patient_address"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("123 Main St", sanitized)

    def test_sanitize_ssn(self):
        """Test sanitization of Social Security Numbers."""
        log_key = "patient_ssn"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("123-45-6789", sanitized)

    def test_sanitize_mrn(self):
        """Test sanitization of Medical Record Numbers."""
        log_key = "patient_mrn"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("987654", sanitized)

    def test_sanitize_dob(self):
        """Test sanitization of Dates of Birth."""
        log_key = "patient_dob"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("01/15/1980", sanitized)

    def test_sanitize_multiple_phi(self):
        """Test sanitization of logs with multiple PHI elements."""
        log_key = "multiple_phi"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("John Smith", sanitized)
        self.assertNotIn("01/15/1980", sanitized)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertNotIn("123 Main St", sanitized)

    def test_no_phi_unchanged(self):
        """Test that logs without PHI are unchanged."""
        log_key = "no_phi"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertEqual(sanitized, self.test_logs[log_key])

    def test_case_insensitive_sanitization(self):
        """Test that sanitization works regardless of case."""
        log_key = "mixed_case"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])
        self.assertEqual(sanitized, self.expected_patterns[log_key])
        self.assertNotIn("JOHN SMITH", sanitized)
        self.assertNotIn("JOHN.SMITH@EXAMPLE.COM", sanitized)

    def test_hipaa_compliance(self):
        """Verify compliance with HIPAA requirements for log sanitization."""
        log_key = "multiple_phi"
        sanitized = self.log_sanitizer.sanitize(self.test_logs[log_key])

        # HIPAA requires that PHI is not visible in logs
        self.assertNotIn("John Smith", sanitized)
        self.assertNotIn("01/15/1980", sanitized)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertNotIn("123 Main St", sanitized)

        # Verify that sanitized log contains redaction markers
        self.assertIn("[REDACTED_NAME]", sanitized)
        self.assertIn("[REDACTED_DOB]", sanitized)
        self.assertIn("[REDACTED_SSN]", sanitized)
        self.assertIn("[REDACTED_ADDRESS]", sanitized)

if __name__ == "__main__":
    unittest.main()
