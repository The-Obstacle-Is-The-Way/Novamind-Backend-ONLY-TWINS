"""
Tests for PHI protection and redaction functionality.

This module tests the PHI protection mechanisms to ensure they properly
detect and redact sensitive patient information.
"""

import pytest
import os
from typing import Dict, Any, List

# Import SanitizerConfig
from app.infrastructure.security.log_sanitizer import LogSanitizer, SanitizerConfig
from app.tests.security.utils import base_security_test
from app.core.security.roles import Role


@pytest.mark.venv_only()
class TestPHIProtection(base_security_test.BaseSecurityTest):
    """Tests for PHI protection mechanisms."""

    # Add required auth attributes that BaseSecurityTest expects
    test_user_id = "test-security-user-456"
    # Replaced DATA_ANALYST with RESEARCHER
    test_roles = [Role.USER, Role.ADMIN, Role.RESEARCHER]

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        # Initialize PHI redactor for testing
        self.sanitizer = LogSanitizer()  # Use LogSanitizer

        # Sample PHI text snippets for testing
        self.sample_phi_data = {
        "name": "Patient John Smith was admitted on 03/15/2024.",
        "ssn": "Patient SSN: 123-45-6789",
        "phone": "Contact at (555) 123-4567",
        "email": "Email: john.smith@example.com",
        "address": "Lives at 123 Main St, Springfield, IL 62701",
        "mrn": "Medical Record Number: MRN123456",
        "age": "Patient is 92 years old",
        "mixed": "John Smith (SSN: 123-45-6789, Phone: (555) 123-4567) was seen on 03/15/2024."
        }

    def test_phi_detection_basic(self) -> None:
        """Test basic PHI detection functionality."""
        # Test with mixed PHI sample
        # Check if sanitization changes the text (indicates PHI detection)
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["mixed"])
        self.assertNotEqual(self.sample_phi_data["mixed"], sanitized)
        # Cannot easily verify specific types without parsing the redacted string

    def test_phi_detection_name(self) -> None:
        """Test detection of patient names."""
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["name"])
        self.assertNotEqual(self.sample_phi_data["name"], sanitized)
        self.assertNotIn("John Smith", sanitized)

    def test_phi_detection_ssn(self) -> None:
        """Test detection of SSNs."""
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["ssn"])
        self.assertNotEqual(self.sample_phi_data["ssn"], sanitized)
        self.assertNotIn("123-45-6789", sanitized)

    def test_phi_detection_phone(self) -> None:
        """Test detection of phone numbers."""
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["phone"])
        self.assertNotEqual(self.sample_phi_data["phone"], sanitized)
        self.assertNotIn("(555) 123-4567", sanitized)

    def test_phi_detection_email(self) -> None:
        """Test detection of email addresses."""
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["email"])
        self.assertNotEqual(self.sample_phi_data["email"], sanitized)
        self.assertNotIn("john.smith@example.com", sanitized)

    def test_phi_detection_address(self) -> None:
        """Test detection of physical addresses."""
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["address"])
        self.assertNotEqual(self.sample_phi_data["address"], sanitized)
        self.assertNotIn("123 Main St", sanitized)

    def test_phi_detection_mrn(self) -> None:
        """Test detection of medical record numbers."""
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["mrn"])
        self.assertNotEqual(self.sample_phi_data["mrn"], sanitized)
        self.assertNotIn("MRN123456", sanitized)

    def test_phi_detection_age(self) -> None:
        """Test detection of ages over 89."""
        sanitized = self.sanitizer.sanitize(self.sample_phi_data["age"])
        self.assertNotEqual(self.sample_phi_data["age"], sanitized)
        self.assertNotIn("92 years old", sanitized)

    def test_sanitizer_config(self) -> None:
        """Test SanitizerConfig initialization and validation."""
        # Create config with valid settings
        config = SanitizerConfig(
            enabled=True,
            log_detected=True,
            marker="[REDACTED]"
        )

        self.assertTrue(config.enabled)
        self.assertTrue(config.log_detected)
        self.assertEqual(config.marker, "[REDACTED]")

    def test_sanitizer_preserves_structure(self) -> None:
        """Test that sanitizer preserves text structure while redacting PHI."""
        # Test with structured text containing PHI
        original = "Patient: John Smith (DOB: 03/15/2024) has appointment on 03/15/2024."
        redacted = self.sanitizer.sanitize(original)

        # Verify structure is preserved while PHI is redacted
        self.assertIn("Patient:", redacted)
        self.assertIn("has appointment on", redacted)
        self.assertIn("[REDACTED NAME]", redacted)
        self.assertIn("[REDACTED DATE]", redacted)
        self.assertNotIn("John Smith", redacted)

    def test_sanitizer_with_dict(self) -> None:
        """Test sanitization of dictionary values."""
        test_dict = {
            "patient_info": "John Smith, SSN: 123-45-6789",
            "non_phi_data": "Regular appointment at 2:30pm",
            "nested": {
                "phi": "Email: john.smith@example.com",
                "non_phi": "Room 101"
            }
        }

        sanitized = self.sanitizer.sanitize(test_dict)

        # Verify structure is preserved
        self.assertIsInstance(sanitized, dict)
        self.assertIn("patient_info", sanitized)
        self.assertIn("non_phi_data", sanitized)
        self.assertIn("nested", sanitized)
        self.assertIsInstance(sanitized["nested"], dict)

        # Verify PHI is redacted
        self.assertNotIn("John Smith", sanitized["patient_info"])
        self.assertNotIn("123-45-6789", sanitized["patient_info"])
        self.assertNotIn("john.smith@example.com", sanitized["nested"]["phi"])

        # Verify non-PHI is preserved
        self.assertEqual(sanitized["non_phi_data"], "Regular appointment at 2:30pm")
        self.assertEqual(sanitized["nested"]["non_phi"], "Room 101")

    def test_sanitizer_with_list(self) -> None:
        """Test sanitization of list items."""
        # Correctly define the list
        test_list = [
            "Patient John Smith",
            "Regular appointment info",
            "SSN: 123-45-6789",
            ["Nested item with email john.smith@example.com", "Non-PHI item"]
        ]

        sanitized = self.sanitizer.sanitize(test_list)

        # Verify structure is preserved
        self.assertIsInstance(sanitized, list)
        self.assertEqual(len(sanitized), len(test_list))
        self.assertIsInstance(sanitized[3], list)

        # Verify PHI is redacted
        self.assertNotIn("John Smith", sanitized[0])
        self.assertNotIn("123-45-6789", sanitized[2])
        self.assertNotIn("john.smith@example.com", sanitized[3][0])

        # Verify non-PHI is preserved
        self.assertEqual(sanitized[1], "Regular appointment info")
        self.assertEqual(sanitized[3][1], "Non-PHI item")

    def test_redaction_consistency(self) -> None:
        """Test that the same PHI is consistently redacted with the same placeholder."""
        # Same name appears twice
        text = "John Smith visited Dr. Jones. John Smith has a follow-up next week."
        sanitized = self.sanitizer.sanitize(text)

        # Count occurrences of the redacted placeholder that replaced "John Smith"
        # Extract the placeholder (assuming format like [REDACTED-NAME-1])
        words = sanitized.split()
        redacted_placeholders = [word for word in words if "REDACTED" in word]

        # If redaction is consistent, the same placeholder should be used for both occurrences
        # So there should be exactly two occurrences of the same placeholder
        placeholder_counts = {}
        for placeholder in redacted_placeholders:
            if placeholder in placeholder_counts:
                placeholder_counts[placeholder] += 1
            else:
                placeholder_counts[placeholder] = 1

        # At least one placeholder should appear exactly twice (for "John Smith")
        self.assertTrue(any(count == 2 for count in placeholder_counts.values()))

    def test_phi_redaction_format(self) -> None:
        """Test the format of redacted PHI."""
        original = "John Smith has SSN 123-45-6789"
        redacted = self.sanitizer.sanitize(original)

        # Check that redacted text follows expected format (e.g., [REDACTED-TYPE-#])
        # Remove extra closing bracket ']'
        self.assertTrue(any("[REDACTED" in part for part in redacted.split()))

        # Verify original PHI is not present
        self.assertNotIn("John Smith", redacted)
        self.assertNotIn("123-45-6789", redacted)

    def test_invalid_input_handling(self) -> None:
        """Test handling of invalid inputs."""
        # Empty string should return empty string
        self.assertEqual("", self.sanitizer.sanitize(""))

        # None input might return None or 'None' based on implementation
        result = self.sanitizer.sanitize(None)
        self.assertTrue(result is None or (isinstance(result, str) and result == "None"))

    def test_all_supported_phi_types(self) -> None:
        """Test redaction of all supported PHI types."""
        # This comprehensive test text includes various PHI types
        complex_phi = """
        Patient Name: John Smith
        DOB: 01/15/1989
        SSN: 123-45-6789
        MRN: MRN123456
        Address: 123 Main St, Springfield, IL 62701
        Phone: (555) 123-4567
        Email: john.smith@example.com
        Credit Card: 4111-1111-1111-1111
        IP Address: 192.168.1.1
        The patient is 92 years old.
        """

        redacted = self.sanitizer.sanitize(complex_phi)

        # Verify redaction of critical PHI
        self.assertNotIn("John Smith", redacted)
        self.assertNotIn("01/15/1989", redacted) # Assuming DOB is redacted
        self.assertNotIn("123-45-6789", redacted)
        self.assertNotIn("MRN123456", redacted)
        self.assertNotIn("123 Main St", redacted) # Assuming address parts are redacted
        self.assertNotIn("(555) 123-4567", redacted)
        self.assertNotIn("john.smith@example.com", redacted)
        self.assertNotIn("4111-1111-1111-1111", redacted) # Assuming CC# is redacted
