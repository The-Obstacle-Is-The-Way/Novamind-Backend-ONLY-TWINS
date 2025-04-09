# -*- coding: utf-8 -*-
"""
Unit tests for Mock PHI Detection Service.

This module tests the mock implementation of the PHI Detection service
to ensure it correctly simulates PHI detection and redaction without
using actual PHI analysis algorithms.
"""

import pytest
import re
import time
from typing import Dict, Any, List

from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from app.core.services.ml.mock_phi import MockPHIDetection


class TestMockPHIDetection:
    """Test suite for MockPHIDetectionService class."""

    @pytest.fixture
    def mock_service(self) -> MockPHIDetection:
        """Create and initialize a MockPHIDetection instance."""
        service = MockPHIDetection()
        service.initialize({"detection_level": "moderate"})
        return service

    @pytest.fixture
    def sample_phi_text(self) -> str:
        """Create a sample text with various types of PHI for testing."""
        return (
            "Patient John Smith (SSN: 123-45-6789) was admitted on 01/15/2023. "
            "He is 45 years old and can be reached at 555-123-4567 or john.smith@example.com. "
            "He lives at 123 Main Street, San Francisco, CA. "
            "His medical record number is MRN 987654."
        )

    def test_initialization(self):
        """Test initialization with valid and invalid configurations."""
        # Test initialization with valid config
        service = MockPHIDetection()
        service.initialize({"detection_level": "strict"})
        assert service.is_healthy()
        
        # Test with different detection levels
        for level in ["strict", "moderate", "relaxed"]:
            service = MockPHIDetection()
            service.initialize({"detection_level": level})
            assert service.is_healthy()
        
        # Test shutdown
        service.shutdown()
        assert not service.is_healthy()
        
        # Test initialization with empty config
        service = MockPHIDetection()
        with pytest.raises(InvalidConfigurationError):
            service.initialize({})
        assert not service.is_healthy()
        
        # Test initialization with invalid config
        service = MockPHIDetection()
        with pytest.raises(InvalidConfigurationError):
            service.initialize("not-a-dict")
        assert not service.is_healthy()

    def test_detect_phi_basic(self, mock_service, sample_phi_text):
        """Test basic PHI detection functionality."""
        # Test default detection
        result = mock_service.detect_phi(sample_phi_text)
        assert "has_phi" in result
        assert result["has_phi"] is True
        assert "phi_count" in result
        assert result["phi_count"] > 0
        assert "phi_entities" in result
        assert len(result["phi_entities"]) > 0
        assert "detection_level" in result
        assert result["detection_level"] == "moderate"
        assert "processing_time" in result
        assert "metadata" in result
        assert result["metadata"]["mock"] is True
        
        # Verify entity structure
        first_entity = result["phi_entities"][0]
        assert "id" in first_entity
        assert "type" in first_entity
        assert "value" in first_entity
        assert "start" in first_entity
        assert "end" in first_entity
        assert "confidence" in first_entity
        assert 0.85 <= first_entity["confidence"] <= 0.98

    def test_detect_phi_with_levels(self, mock_service, sample_phi_text):
        """Test PHI detection with different detection levels."""
        # Test with strict level
        strict_result = mock_service.detect_phi(sample_phi_text, detection_level="strict")
        assert strict_result["detection_level"] == "strict"
        
        # Test with moderate level
        moderate_result = mock_service.detect_phi(sample_phi_text, detection_level="moderate")
        assert moderate_result["detection_level"] == "moderate"
        
        # Test with relaxed level
        relaxed_result = mock_service.detect_phi(sample_phi_text, detection_level="relaxed")
        assert relaxed_result["detection_level"] == "relaxed"
        
        # Compare entity counts across levels
        # Strict should find more than moderate, moderate more than relaxed
        assert strict_result["phi_count"] >= moderate_result["phi_count"]
        assert moderate_result["phi_count"] >= relaxed_result["phi_count"]

    def test_detect_phi_with_specific_types(self, mock_service):
        """Test PHI detection for specific entity types."""
        # Test NAME detection
        name_text = "The patient's name is John Smith."
        name_result = mock_service.detect_phi(name_text)
        assert name_result["has_phi"]
        assert any(entity["type"] == "NAME" for entity in name_result["phi_entities"])
        
        # Test DATE detection
        date_text = "The appointment was on 01/15/2023."
        date_result = mock_service.detect_phi(date_text)
        assert date_result["has_phi"]
        assert any(entity["type"] == "DATE" for entity in date_result["phi_entities"])
        
        # Test PHONE detection
        phone_text = "Call me at 555-123-4567."
        phone_result = mock_service.detect_phi(phone_text)
        assert phone_result["has_phi"]
        assert any(entity["type"] == "PHONE" for entity in phone_result["phi_entities"])
        
        # Test EMAIL detection
        email_text = "My email is john.smith@example.com."
        email_result = mock_service.detect_phi(email_text)
        assert email_result["has_phi"]
        assert any(entity["type"] == "EMAIL" for entity in email_result["phi_entities"])
        
        # Test SSN detection
        ssn_text = "SSN: 123-45-6789"
        ssn_result = mock_service.detect_phi(ssn_text)
        assert ssn_result["has_phi"]
        assert any(entity["type"] == "SSN" for entity in ssn_result["phi_entities"])
        
        # Test ADDRESS detection
        address_text = "I live at 123 Main Street."
        address_result = mock_service.detect_phi(address_text)
        assert address_result["has_phi"]
        assert any(entity["type"] == "ADDRESS" for entity in address_result["phi_entities"])
        
        # Test AGE detection
        age_text = "The patient is 45 years old."
        age_result = mock_service.detect_phi(age_text)
        assert age_result["has_phi"]
        assert any(entity["type"] == "AGE" for entity in age_result["phi_entities"])
        
        # Test MEDICAL_RECORD detection
        mrn_text = "Medical record: MRN 987654."
        mrn_result = mock_service.detect_phi(mrn_text)
        assert mrn_result["has_phi"]
        assert any(entity["type"] == "MEDICAL_RECORD" for entity in mrn_result["phi_entities"])

    def test_detect_phi_no_phi(self, mock_service):
        """Test PHI detection with text that doesn't contain PHI."""
        no_phi_text = "This text does not contain any personal health information."
        result = mock_service.detect_phi(no_phi_text)
        assert not result["has_phi"]
        assert result["phi_count"] == 0
        assert len(result["phi_entities"]) == 0

    def test_detect_phi_edge_cases(self, mock_service):
        """Test PHI detection with edge cases."""
        # Empty text
        empty_text = ""
        result = mock_service.detect_phi(empty_text)
        assert not result["has_phi"]
        assert result["phi_count"] == 0
        
        # Very short text without PHI
        short_text = "Hello."
        result = mock_service.detect_phi(short_text)
        assert not result["has_phi"]
        
        # Text with similar but not matching patterns
        almost_phi_text = "The code is 12345 and the color is red."
        result = mock_service.detect_phi(almost_phi_text)
        assert not result["has_phi"]  # Should not detect these as PHI
        
        # Uninitialized service test
        uninitialized_service = MockPHIDetection()
        with pytest.raises(ServiceUnavailableError):
            uninitialized_service.detect_phi("Some text")

    def test_redact_phi_basic(self, mock_service, sample_phi_text):
        """Test basic PHI redaction functionality."""
        # Test with default replacement
        result = mock_service.redact_phi(sample_phi_text)
        assert "redacted_text" in result
        assert "phi_entities" in result
        assert len(result["phi_entities"]) > 0
        assert "processing_time" in result
        
        # Check that PHI is actually redacted
        redacted_text = result["redacted_text"]
        assert "John Smith" not in redacted_text
        assert "123-45-6789" not in redacted_text
        assert "555-123-4567" not in redacted_text
        assert "john.smith@example.com" not in redacted_text
        assert "[REDACTED]" in redacted_text  # Default replacement marker
        
        # Check redacted_text length information
        assert "original_text_length" in result
        assert result["original_text_length"] == len(sample_phi_text)
        assert "redacted_text_length" in result
        assert result["redacted_text_length"] == len(redacted_text)

    def test_redact_phi_custom_replacement(self, mock_service, sample_phi_text):
        """Test PHI redaction with custom replacement text."""
        # Test with custom replacement
        custom_marker = "***PHI***"
        result = mock_service.redact_phi(sample_phi_text, replacement=custom_marker)
        assert "redacted_text" in result
        
        # Check that PHI is redacted with custom marker
        redacted_text = result["redacted_text"]
        assert "John Smith" not in redacted_text
        assert "123-45-6789" not in redacted_text
        assert custom_marker in redacted_text
        assert "[REDACTED]" not in redacted_text  # Should not use default marker

    def test_redact_phi_levels(self, mock_service, sample_phi_text):
        """Test PHI redaction with different detection levels."""
        # Test each detection level
        for level in ["strict", "moderate", "relaxed"]:
            result = mock_service.redact_phi(sample_phi_text, detection_level=level)
            assert result["detection_level"] == level
            assert "redacted_text" in result
            
            # Strict should have more redactions than moderate, moderate more than relaxed
            if level == "strict":
                strict_phi_count = result["phi_count"]
            elif level == "moderate":
                moderate_phi_count = result["phi_count"]
            elif level == "relaxed":
                relaxed_phi_count = result["phi_count"]
        
        # Verify hierarchy of detection levels
        assert strict_phi_count >= moderate_phi_count
        assert moderate_phi_count >= relaxed_phi_count

    def test_redact_phi_edge_cases(self, mock_service):
        """Test PHI redaction with edge cases."""
        # Empty text
        empty_text = ""
        result = mock_service.redact_phi(empty_text)
        assert result["redacted_text"] == ""
        assert result["phi_count"] == 0
        
        # Text without PHI
        no_phi_text = "This text does not contain any personal health information."
        result = mock_service.redact_phi(no_phi_text)
        assert result["redacted_text"] == no_phi_text  # Should remain unchanged
        assert result["phi_count"] == 0
        
        # Uninitialized service test
        uninitialized_service = MockPHIDetection()
        with pytest.raises(ServiceUnavailableError):
            uninitialized_service.redact_phi("Some text")

    def test_pattern_selection(self):
        """Test the internal pattern selection logic."""
        service = MockPHIDetection()
        
        # Access protected methods directly for testing patterns
        strict_patterns = service._get_strict_patterns()
        moderate_patterns = service._get_moderate_patterns()
        relaxed_patterns = service._get_relaxed_patterns()
        default_patterns = service._get_default_patterns()
        
        # Strict should have more pattern types than moderate
        assert len(strict_patterns.keys()) >= len(moderate_patterns.keys())
        
        # Moderate should have more pattern types than relaxed
        assert len(moderate_patterns.keys()) >= len(relaxed_patterns.keys())
        
        # Default should be the same as moderate patterns (by implementation)
        assert len(default_patterns.keys()) == len(moderate_patterns.keys())
        
        # Check that each pattern dictionary has the expected structure
        for pattern_dict in [strict_patterns, moderate_patterns, relaxed_patterns]:
            for phi_type, patterns in pattern_dict.items():
                assert isinstance(phi_type, str)
                assert isinstance(patterns, list)
                assert all(isinstance(p, re.Pattern) for p in patterns)