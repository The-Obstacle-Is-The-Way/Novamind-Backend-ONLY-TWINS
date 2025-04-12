# -*- coding: utf-8 -*-
"""
Tests for PHI Detection Service.

This module contains unit tests for the PHI detection functionality,
ensuring it correctly identifies and handles Protected Health Information.
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import patch, mock_open

from app.infrastructure.ml.phi_detection import PHIDetectionService
from app.infrastructure.security.log_sanitizer import (
    PHIPattern,
)  # Corrected import path


@pytest.fixture
def phi_detection_service():
    """Fixture providing a PHI detection service with test patterns."""
    service = PHIDetectionService()
    service.initialize()
    return service


    @pytest.mark.db_required()
    def test_initialize_loads_default_patterns():
    """Test that initialize loads default patterns when file loading fails."""
    service = PHIDetectionService("nonexistent_file.yaml")

    # Initialize should not raise exceptions when file is missing
    service.initialize()

    # Should have loaded default patterns
    assert service.initialized
    assert len(service.patterns) > 0


    def test_ensure_initialized_calls_initialize():
    """Test that ensure_initialized calls initialize if not initialized."""
    service = PHIDetectionService()
    assert not service.initialized

    service.ensure_initialized()
    assert service.initialized


    def test_detect_phi_empty_text():
    """Test that detect_phi returns empty list for empty text."""
    service = PHIDetectionService()
    service.initialize()

    results = service.detect_phi("")
    assert isinstance(results, list)
    assert len(results) == 0


    def test_contains_phi_empty_text():
    """Test that contains_phi returns False for empty text."""
    service = PHIDetectionService()
    service.initialize()

    assert not service.contains_phi("")


    @pytest.mark.parametrize(
    "text,expected",
    [
        ("No PHI here", False),
        ("SSN: 123-45-6789", True),
        ("Contact me at test@example.com", True),
        ("Call me at (555) 123-4567", True),
        ("John Smith is 92 years old", True),
        ("The patient's MRN is MRN12345", True),
    ],
)
def test_contains_phi(phi_detection_service, text, expected):
    """Test contains_phi with various texts containing/not containing PHI."""
    assert phi_detection_service.contains_phi(text) == expected


    @pytest.mark.parametrize(
    "text,phi_type",
    [
        ("SSN: 123-45-6789", "US SSN"),
        ("Contact me at test@example.com", "Email Address"),
        ("Call me at (555) 123-4567", "US Phone Number"),
        ("John Smith lives here", "Name"),
        ("Born on 01/01/1980", "Date"),
        ("Lives at 123 Main St, Anytown, CA 12345", "Address"),
        ("Credit card: 4111 1111 1111 1111", "Credit Card"),
        ("Patient is 95 years old", "Age over 90"),
    ],
)
def test_detect_phi_finds_different_types(phi_detection_service, text, phi_type):
    """Test that detect_phi finds different types of PHI."""
    results = phi_detection_service.detect_phi(text)

    # Should find at least one instance of the expected PHI type
    assert any(r["type"] == phi_type for r in results)


    def test_detect_phi_results_format():
    """Test that detect_phi returns correctly formatted results."""
    service = PHIDetectionService()
    service.initialize()

    text = "SSN: 123-45-6789, Email: test@example.com"
    results = service.detect_phi(text)

    assert len(results) >= 2  # Should find at least SSN and email

    # Check structure of first result
    first_result = results[0]
    assert "type" in first_result
    assert "category" in first_result
    assert "risk_level" in first_result
    assert "start" in first_result
    assert "end" in first_result
    assert "value" in first_result
    assert "description" in first_result


    @pytest.mark.parametrize(
    "text,replacement,expected",
    [
        ("SSN: 123-45-6789", "[REDACTED]", "SSN: [REDACTED]"),
        ("Contact: test@example.com", "***PHI***", "Contact: ***PHI***"),
        ("John Smith, DOB: 01/01/1980", "[PHI]", "[PHI], DOB: [PHI]"),
        ("No PHI here", "[REDACTED]", "No PHI here"),
    ],
)
def test_redact_phi(phi_detection_service, text, replacement, expected):
    """Test redacting PHI with different replacement strings."""
    redacted = phi_detection_service.redact_phi(text, replacement)
    assert redacted == expected


    def test_redact_phi_empty_text():
    """Test that redact_phi handles empty text gracefully."""
    service = PHIDetectionService()
    service.initialize()

    assert service.redact_phi("") == ""


    def test_redact_phi_overlapping_matches():
    """Test that redact_phi correctly handles overlapping PHI."""
    service = PHIDetectionService()
    service.initialize()

    # Create text with potentially overlapping PHI
    # For example, "John Smith" (name) contains "John" (could be detected as a name too)
    text = "Patient John Smith has SSN 123-45-6789"
    redacted = service.redact_phi(text)

    # Exact assert ion depends on how patterns are defined and how overlaps are handled
    # But at minimum, both the name and SSN should be redacted
    assert "[REDACTED]" in redacted
    assert "123-45-6789" not in redacted
    assert "John Smith" not in redacted


    def test_get_phi_types():
    """Test getting the list of PHI types."""
    service = PHIDetectionService()
    service.initialize()

    phi_types = service.get_phi_types()

    assert isinstance(phi_types, list)
    assert len(phi_types) > 0
    assert "US SSN" in phi_types
    assert "Email Address" in phi_types


    def test_get_statistics():
    """Test getting statistics about PHI patterns."""
    service = PHIDetectionService()
    service.initialize()

    stats = service.get_statistics()

    assert "total_patterns" in stats
    assert "categories" in stats
    assert "risk_levels" in stats

    assert stats["total_patterns"] > 0
    assert len(stats["categories"]) > 0
    assert "high" in stats["risk_levels"]


    @patch("app.infrastructure.ml.phi_detection.re")
    def test_phi_pattern_creation(mock_re):
    """Test creating a PHIPattern instance."""
    # Mock re.compile for testing
    mock_re.compile.return_value = "mock_pattern"

    pattern = PHIPattern(
        name="Test Pattern",
        pattern=mock_re.compile(r"test"),
        description="A test pattern",
        risk_level="high",
        category="test",
    )

    assert pattern.name == "Test Pattern"
    assert pattern.pattern == "mock_pattern"
    assert pattern.description == "A test pattern"
    assert pattern.risk_level == "high"
    assert pattern.category == "test"
