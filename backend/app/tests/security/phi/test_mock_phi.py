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
        "Patient lives at 123 Main St, Springfield, IL 62701."
        

        self.no_phi_text = ()
        "The patient reported feeling better after the treatment. "
        "Symptoms have decreased in severity and frequency. "
        "Regular exercise and medication adherence are recommended."
        

        def test_initialization(self) -> None:
        """Test initialization of the PHI detection service."""
        self.assertIsNotNone(self.service)
        # _initialized is a private attribute, use is_healthy() instead
        self.assertTrue(self.service.is_healthy())

        def test_detect_phi_basic(self) -> None:
        """Test basic PHI detection functionality."""
        # Test with sample text containing PHI
        result = self.service.detect_phi(self.sample_phi_text)
        
        # Verify result structure
        self.assertIn('phi_instances', result)
        self.assertIn('confidence_score', result)
        
        # Should find PHI in the sample text
        self.assertGreater(len(result['phi_instances']), 0)
        
        # Test with text containing no PHI
        result_no_phi = self.service.detect_phi(self.no_phi_text)
        
        # Should not find PHI in the no-PHI text
        self.assertEqual(len(result_no_phi['phi_instances']), 0)

        def test_detect_phi_types(self) -> None:
        """Test detection of different PHI types."""
        result = self.service.detect_phi(self.sample_phi_text)
        
        # Extract PHI types from the result
        phi_types = [instance['type'] for instance in result['phi_instances']]
        
        # Should detect various PHI types
        self.assertTrue(any('NAME' in phi_type for phi_type in phi_types))
        self.assertTrue(any('SSN' in phi_type for phi_type in phi_types))
        self.assertTrue(any('EMAIL' in phi_type for phi_type in phi_types))
        self.assertTrue(any('PHONE' in phi_type for phi_type in phi_types))
        self.assertTrue(any('ADDRESS' in phi_type for phi_type in phi_types))

        def test_detect_phi_locations(self) -> None:
        """Test that PHI locations are correctly identified."""
        result = self.service.detect_phi(self.sample_phi_text)
        
        # Each PHI instance should have start and end positions
            for instance in result['phi_instances']:
                self.assertIn('start', instance)
                self.assertIn('end', instance)
                self.assertIsInstance(instance['start'], int)
                self.assertIsInstance(instance['end'], int)
            
        # Positions should be valid
        self.assertGreaterEqual(instance['start'], 0)
        self.assertLess(instance['start'], len(self.sample_phi_text))
        self.assertGreater(instance['end'], instance['start'])
        self.assertLessEqual(instance['end'], len(self.sample_phi_text))
            
        # The text at the specified location should match the value
        self.assertEqual()
        self.sample_phi_text[instance['start']:instance['end']],
        instance['value']
            

            def test_detect_phi_confidence(self) -> None:
        """Test confidence scores for PHI detection."""
        result = self.service.detect_phi(self.sample_phi_text)
        
        # Overall confidence score should be between 0 and 1
        self.assertGreaterEqual(result['confidence_score'], 0.0)
        self.assertLessEqual(result['confidence_score'], 1.0)
        
        # Each PHI instance should have a confidence score
            for instance in result['phi_instances']:
                self.assertIn('confidence', instance)
                self.assertGreaterEqual(instance['confidence'], 0.0)
                self.assertLessEqual(instance['confidence'], 1.0)

            def test_redact_phi_basic(self) -> None:
        """Test basic PHI redaction functionality."""
        result = self.service.redact_phi(self.sample_phi_text)
        
        # Verify result structure
        self.assertIn('redacted_text', result)
        self.assertIn('redaction_count', result)
        
        # Should redact PHI in the sample text
        self.assertNotEqual(result['redacted_text'], self.sample_phi_text)
        
        # Redaction count should match the number of redactions
        redaction_count = result['redacted_text'].count('[REDACTED]')
        self.assertEqual(result['redaction_count'], redaction_count)
        
        # Specific PHI should be redacted
        self.assertNotIn('John Smith', result['redacted_text'])
        self.assertNotIn('123-45-6789', result['redacted_text'])
        self.assertNotIn('john.smith@example.com', result['redacted_text'])

        def test_redact_phi_custom_replacement(self) -> None:
        """Test PHI redaction with custom replacement text."""
        replacement = '[PHI REMOVED]'
        redacted = self.service.redact_phi()
        self.sample_phi_text,
        replacement=replacement
        
        
        # Verify the redacted text uses the custom replacement
        redacted_text = redacted['redacted_text']
        self.assertIn(replacement, redacted_text)
        self.assertNotIn('[REDACTED]', redacted_text)
        self.assertNotEqual(redacted_text, self.sample_phi_text)

        # Verify the replacement was used (based on replacement_used in result)
        self.assertEqual(redacted['replacement_used'], replacement)

        def test_redact_phi_levels(self) -> None:
        """Test PHI redaction with confidence levels."""
        # Use detection_level parameter instead of min_confidence
        redacted_high = self.service.redact_phi()
        self.sample_phi_text,
        detection_level="strict"
        

        redacted_low = self.service.redact_phi()
        self.sample_phi_text,
        detection_level="relaxed"
        

        # Both should return dictionaries with redacted_text
        self.assertIn('redacted_text', redacted_high)
        self.assertIn('redacted_text', redacted_low)

        def test_redact_phi_edge_cases(self) -> None:
        """Test PHI redaction with edge cases."""
        # Empty text should raise InvalidRequestError
        with self.assertRaises(InvalidRequestError):
            self.service.redact_phi("")

        # None input should raise InvalidRequestError
        with self.assertRaises(InvalidRequestError):
            self.service.redact_phi(None)

            def test_pattern_selection(self) -> None:
        """Test selection of detection patterns based on configuration."""
        # Initialize with specific configuration
        pattern_service = MockPHIDetection()
        pattern_service.initialize({)
        "sensitivity": "high"  # Use supported config option
        }

        result = pattern_service.detect_phi(self.sample_phi_text)

        # Verify the result structure
        self.assertIn('phi_instances', result)