"""
Security tests for PHI Detection service.

This module tests the mock PHI detection service to ensure it correctly
identifies and redacts Protected Health Information (PHI) in text.
These tests are security-critical as they validate HIPAA compliance mechanisms.
"""

import pytest
from typing import Dict, Any, List

from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from app.core.services.ml.mock import MockPHIDetection
from app.tests.security.base_security_test import BaseSecurityTest

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
        
        self.sample_phi_text = (
            "Patient John Smith (SSN: 123-45-6789) was admitted on 03/15/2024. "
            "His email is john.smith@example.com and phone number is (555) 123-4567. "
            "Patient lives at 123 Main St, Springfield, IL 62701."
        )
        
        self.no_phi_text = (
            "The patient reported feeling better after the treatment. "
            "Symptoms have decreased in severity and frequency. "
            "Regular exercise and medication adherence are recommended."
        )
    
    def test_initialization(self) -> None:
        """Test initialization of the PHI detection service."""
        self.assertIsNotNone(self.service)
        self.assertTrue(self.service.is_initialized)
    
    def test_detect_phi_basic(self) -> None:
        """Test basic PHI detection in text."""
        results = self.service.detect_phi(self.sample_phi_text)
        self.assertGreater(len(results), 0)
        
        # Check that key PHI entities are detected
        detected_types = [result["type"] for result in results]
        self.assertIn("NAME", detected_types)
        self.assertIn("SSN", detected_types)
        self.assertIn("DATE", detected_types)
        self.assertIn("EMAIL", detected_types)
        self.assertIn("PHONE", detected_types)
        self.assertIn("ADDRESS", detected_types)
    
    def test_detect_phi_with_levels(self) -> None:
        """Test PHI detection with confidence levels."""
        results = self.service.detect_phi(self.sample_phi_text, min_confidence=0.8)
        high_confidence_results = [r for r in results if r["confidence"] >= 0.8]
        
        # We should have fewer results with high confidence filter
        self.assertEqual(len(results), len(high_confidence_results))
        
        # Test with low confidence to get more results
        all_results = self.service.detect_phi(self.sample_phi_text, min_confidence=0.1)
        self.assertGreaterEqual(len(all_results), len(results))
    
    def test_detect_phi_with_specific_types(self) -> None:
        """Test PHI detection with specific entity types."""
        # Only detect names and phone numbers
        results = self.service.detect_phi(
            self.sample_phi_text, 
            phi_types=["NAME", "PHONE"]
        )
        
        detected_types = [result["type"] for result in results]
        self.assertIn("NAME", detected_types)
        self.assertIn("PHONE", detected_types)
        self.assertNotIn("SSN", detected_types)
        self.assertNotIn("EMAIL", detected_types)
    
    def test_detect_phi_no_phi(self) -> None:
        """Test PHI detection with text that doesn't contain PHI."""
        results = self.service.detect_phi(self.no_phi_text)
        self.assertEqual(len(results), 0)
    
    def test_detect_phi_edge_cases(self) -> None:
        """Test PHI detection with edge cases."""
        # Empty text
        results = self.service.detect_phi("")
        self.assertEqual(len(results), 0)
        
        # None input should raise an error
        with self.assertRaises(InvalidRequestError):
            self.service.detect_phi(None)
        
        # Very short text
        results = self.service.detect_phi("Hello")
        self.assertEqual(len(results), 0)
    
    def test_redact_phi_basic(self) -> None:
        """Test basic PHI redaction in text."""
        redacted = self.service.redact_phi(self.sample_phi_text)
        
        # Check that PHI has been redacted
        self.assertNotIn("John Smith", redacted)
        self.assertNotIn("123-45-6789", redacted)
        self.assertNotIn("john.smith@example.com", redacted)
        self.assertNotIn("(555) 123-4567", redacted)
        self.assertNotIn("123 Main St", redacted)
        
        # Check that redaction markers are present
        self.assertIn("[REDACTED]", redacted)
    
    def test_redact_phi_custom_replacement(self) -> None:
        """Test PHI redaction with custom replacement text."""
        redacted = self.service.redact_phi(
            self.sample_phi_text,
            replacement="[PHI]"
        )
        
        # Check that custom replacement is used
        self.assertIn("[PHI]", redacted)
        self.assertNotIn("[REDACTED]", redacted)
    
    def test_redact_phi_levels(self) -> None:
        """Test PHI redaction with confidence levels."""
        redacted_high = self.service.redact_phi(
            self.sample_phi_text,
            min_confidence=0.9
        )
        
        redacted_low = self.service.redact_phi(
            self.sample_phi_text,
            min_confidence=0.1
        )
        
        # Lower confidence should redact more
        self.assertNotEqual(redacted_high, redacted_low)
        self.assertGreater(redacted_low.count("[REDACTED]"), redacted_high.count("[REDACTED]"))
    
    def test_redact_phi_edge_cases(self) -> None:
        """Test PHI redaction with edge cases."""
        # Empty text
        redacted = self.service.redact_phi("")
        self.assertEqual(redacted, "")
        
        # None input should raise an error
        with self.assertRaises(InvalidRequestError):
            self.service.redact_phi(None)
        
        # No PHI in text should return original
        redacted = self.service.redact_phi(self.no_phi_text)
        self.assertEqual(redacted, self.no_phi_text)
    
    def test_pattern_selection(self) -> None:
        """Test selection of detection patterns based on configuration."""
        # Initialize with specific patterns
        pattern_service = MockPHIDetection()
        pattern_service.initialize({
            "patterns": ["NAME", "EMAIL"]
        })
        
        results = pattern_service.detect_phi(self.sample_phi_text)
        detected_types = [result["type"] for result in results]
        
        # Only configured patterns should be detected
        self.assertIn("NAME", detected_types)
        self.assertIn("EMAIL", detected_types)
        self.assertNotIn("SSN", detected_types)
        self.assertNotIn("PHONE", detected_types)