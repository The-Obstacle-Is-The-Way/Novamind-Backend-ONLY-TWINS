"""
Security tests for PHI Detection service.

This module tests the mock PHI detection service to ensure it correctly
identifies and redacts Protected Health Information (PHI) in text.
These tests are security-critical as they validate HIPAA compliance mechanisms.
"""

from app.tests.security.base_security_test import BaseSecurityTest
from app.core.services.ml.mock import MockPHIDetection
import pytest
from typing import Dict, Any, List

from app.core.exceptions import ()
InvalidConfigurationError,
InvalidRequestError,
ServiceUnavailableError,



@pytest.mark.venv_only()
class TestMockPHIDetection(BaseSecurityTest):
    """
    Test suite for MockPHIDetection class.

    These tests verify that the PHI detection service correctly
    identifies and redacts protected health information in text.
    """
    # Add required auth attributes that BaseSecurityTest expects
    test_user_id = "test-security-user-123"
    test_roles = ["user", "clinician", "researcher"]

    def setUp(self) -> None:
        """Set up test fixtures and service instance."""
        super().setUp()
        self.service = MockPHIDetection()
        self.service.initialize({})

        self.sample_phi_text = ()
        "Patient John Smith (SSN: 123-45-6789) was admitted on 03/15/2024. "
        "His email is john.smith@example.com and phone number is (555) 123-4567. "
        "He resides at 123 Main Street, Springfield, IL 62701."
        

        def tearDown(self) -> None:
        """Clean up resources after tests."""
            if hasattr(self, 'service') and self.service.is_healthy():
                self.service.shutdown()
                self.audit_events.clear()
        super().tearDown()

            def test_initialization(self) -> None:
        """Test initialization with valid and invalid configurations."""
        # Test default initialization
        service = MockPHIDetection()
        service.initialize({})
        self.assertTrue(service.is_healthy())
        service.shutdown()
        
        # Test with custom configuration
        service = MockPHIDetection()
        service.initialize({"detection_threshold": 0.8})
        self.assertTrue(service.is_healthy())
        service.shutdown()
        
        # Test with invalid configuration
        service = MockPHIDetection()
        with self.assertRaises(InvalidConfigurationError):
            service.initialize({"detection_threshold": "invalid"})

            def test_detect_phi_basic(self) -> None:
        """Test basic PHI detection functionality."""
        # Test with sample PHI text
        result = self.service.detect_phi(self.sample_phi_text)
        
        # Verify result structure
        self.assertIn("phi_instances", result)
        self.assertIn("confidence_score", result)
        
        # Should detect PHI in the sample text
        self.assertGreater(len(result["phi_instances"]), 0)
        
        # Confidence score should be between 0 and 1
        self.assertGreaterEqual(result["confidence_score"], 0.0)
        self.assertLessEqual(result["confidence_score"], 1.0)

        def test_detect_phi_empty_text(self) -> None:
        """Test PHI detection with empty text."""
        result = self.service.detect_phi("")
        
        # Should return empty PHI instances for empty text
        self.assertEqual(len(result["phi_instances"]), 0)
        
        # Confidence score should be 0 for empty text
        self.assertEqual(result["confidence_score"], 0.0)

        def test_detect_phi_non_phi_text(self) -> None:
        """Test PHI detection with text containing no PHI."""
        non_phi_text = "The weather is nice today. The hospital has new equipment."
        result = self.service.detect_phi(non_phi_text)
        
        # Should not detect PHI in non-PHI text
        self.assertEqual(len(result["phi_instances"]), 0)
        
        # Confidence score should be low for non-PHI text
        self.assertLess(result["confidence_score"], 0.3)

        def test_detect_phi_with_threshold(self) -> None:
        """Test PHI detection with different confidence thresholds."""
        # Initialize service with high threshold
        high_threshold_service = MockPHIDetection()
        high_threshold_service.initialize({"detection_threshold": 0.9})
        
        # Initialize service with low threshold
        low_threshold_service = MockPHIDetection()
        low_threshold_service.initialize({"detection_threshold": 0.1})
        
        # Same text should produce different results based on threshold
        text_with_subtle_phi = "Patient JS was seen on March 15th."
        
        high_result = high_threshold_service.detect_phi(text_with_subtle_phi)
        low_result = low_threshold_service.detect_phi(text_with_subtle_phi)
        
        # Low threshold should detect more PHI instances
        self.assertGreaterEqual()
        len(low_result["phi_instances"]),
        len(high_result["phi_instances"])
        
        
        # Clean up
        high_threshold_service.shutdown()
        low_threshold_service.shutdown()

        def test_detect_phi_types(self) -> None:
        """Test detection of different PHI types."""
        # Test with text containing multiple PHI types
        result = self.service.detect_phi(self.sample_phi_text)
        
        # Extract PHI types from the result
        phi_types = [instance["type"] for instance in result["phi_instances"]]
        
        # Should detect various PHI types
        expected_types = ["NAME", "SSN", "EMAIL", "PHONE", "ADDRESS", "DATE"]
            for expected_type in expected_types:
                self.assertTrue()
                any(expected_type in phi_type for phi_type in phi_types),
                f"Failed to detect {expected_type} in the sample text"
            

            def test_redact_phi_basic(self) -> None:
        """Test basic PHI redaction functionality."""
        # Test with sample PHI text
        result = self.service.redact_phi(self.sample_phi_text)
        
        # Verify result structure
        self.assertIn("redacted_text", result)
        self.assertIn("redaction_count", result)
        
        # Should redact PHI in the sample text
        self.assertNotEqual(result["redacted_text"], self.sample_phi_text)
        
        # Redaction count should be positive
        self.assertGreater(result["redaction_count"], 0)
        
        # Specific PHI should be redacted
        self.assertNotIn("John Smith", result["redacted_text"])
        self.assertNotIn("123-45-6789", result["redacted_text"])
        self.assertNotIn("john.smith@example.com", result["redacted_text"])
        self.assertNotIn("(555) 123-4567", result["redacted_text"])
        self.assertNotIn("123 Main Street", result["redacted_text"])

        def test_redact_phi_empty_text(self) -> None:
        """Test PHI redaction with empty text."""
        result = self.service.redact_phi("")
        
        # Should return empty text for empty input
        self.assertEqual(result["redacted_text"], "")
        
        # Redaction count should be 0 for empty text
        self.assertEqual(result["redaction_count"], 0)

        def test_redact_phi_non_phi_text(self) -> None:
        """Test PHI redaction with text containing no PHI."""
        non_phi_text = "The weather is nice today. The hospital has new equipment."
        result = self.service.redact_phi(non_phi_text)
        
        # Should not modify non-PHI text
        self.assertEqual(result["redacted_text"], non_phi_text)
        
        # Redaction count should be 0 for non-PHI text
        self.assertEqual(result["redaction_count"], 0)

        def test_redact_phi_with_detection_level(self) -> None:
        """Test PHI redaction with different detection levels."""
        # Test with minimal level
        minimal_result = self.service.redact_phi()
        self.sample_phi_text,
        detection_level="minimal"
        
        
        # Then with aggressive level
        aggressive_result = self.service.redact_phi()
        self.sample_phi_text,
        detection_level="aggressive"
        
        
        # Count redactions by counting marker occurrences
        minimal_redactions = minimal_result["redacted_text"].count("[REDACTED]")
        aggressive_redactions = aggressive_result["redacted_text"].count("[REDACTED]")
        
        # Aggressive should redact more
        self.assertLessEqual(minimal_redactions, aggressive_redactions)

        def test_redact_phi_edge_cases(self) -> None:
        """Test PHI redaction with edge cases."""
        # Test already redacted text
        redacted_text = "Patient [REDACTED] with ID [REDACTED]"
        result = self.service.redact_phi(redacted_text)
        
        # Should not double-redact
        double_redacted = "[REDACTED][REDACTED]"
        self.assertNotIn(double_redacted, result["redacted_text"])

        def test_pattern_selection(self) -> None:
        """Test that PHI detection patterns properly match different PHI types."""
        # Test patterns individually
        test_cases = {
        "ssn": "SSN: 123-45-6789",
        "email": "Email: patient@example.com",
        "phone": "Phone: (555) 123-4567",
        "address": "123 Main St, Anytown, CA 12345",
        "name": "John Smith",
        "date": "01/15/2024"
        }

            for phi_type, test_text in test_cases.items():
        # Test each text type individually
        result = self.service.detect_phi(test_text)
            
        # Should find at least one PHI in the text
        self.assertGreater()
        len(result["phi_instances"]), 0,
        f"Failed to detect PHI in '{test_text}'"
            