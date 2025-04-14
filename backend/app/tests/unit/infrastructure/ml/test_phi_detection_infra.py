# -*- coding: utf-8 -*-
"""
Tests for PHI Detection Service.

This module contains tests for the PHI detection service functionality,
including pattern loading, detection, and redaction capabilities.
"""

import pytest
import re # Import re for pattern creation test
from typing import List, Dict, Any
from unittest.mock import patch, mock_open, MagicMock

from app.infrastructure.ml.phi_detection import PHIDetectionService
from app.core.exceptions.ml_exceptions import PHIDetectionError
# Corrected import: Import PHIPattern directly
from app.infrastructure.security.log_sanitizer import PHIPattern


@pytest.fixture
def phi_detection_service():
    """Fixture providing a PHI detection service with mocked patterns."""
    # Define mock patterns in YAML format as a string
    mock_patterns_yaml = """
contact:
  - name: "US Phone Number"
    pattern: "\\\\(?(\\\\d{3})\\\\)?[-. ]?(\\\\d{3})[-. ]?(\\\\d{4})"
    description: "US phone number with or without formatting"
    category: "contact"
    risk_level: "high"
name:
  - name: "Full Name"
    pattern: "(?:[A-Z][a-z]+\\\\s+){1,2}[A-Z][a-z]+"
    description: "Full name with 2-3 parts"
    category: "name"
    risk_level: "high"
"""
    # Patch open to return the mock patterns
    with patch("builtins.open", mock_open(read_data=mock_patterns_yaml)):
        # Patch _get_default_patterns to avoid dependency on actual default patterns file
        with patch.object(PHIDetectionService, "_get_default_patterns", return_value=[]):
            service = PHIDetectionService(pattern_file="mock_path.yaml") # Use the mocked path
            service.ensure_initialized() # Initialize using the mocked patterns
            return service

# Define the test class
class TestPHIDetectionService:
    """Test suite for PHI detection service."""

    def test_initialization(self, phi_detection_service):
        """Test that the service initializes correctly with mocked patterns."""
        assert phi_detection_service._initialized is True
        # Check based on the mocked patterns provided in the fixture
        assert len(phi_detection_service.patterns) == 2
        assert any(p.name == "US Phone Number" for p in phi_detection_service.patterns)
        assert any(p.name == "Full Name" for p in phi_detection_service.patterns)

    def test_pattern_loading_error_falls_back_to_defaults(self):
        """Test that service falls back to default patterns when loading fails."""
        # Mock default patterns to check if they are loaded
        default_pattern_mock = PHIPattern(name="DefaultTest", pattern=r"default", description="desc", risk_level="low", category="test")
        default_patterns = [default_pattern_mock]

        with patch("builtins.open", side_effect=IOError("Mock file error")):
            # Patch the method that loads defaults
            with patch.object(PHIDetectionService, "_get_default_patterns", return_value=default_patterns) as mock_get_defaults:
                service = PHIDetectionService(pattern_file="nonexistent_file.yaml")
                service.ensure_initialized() # This will trigger the fallback

                assert service.initialized
                assert len(service.patterns) == 1
                assert service.patterns[0].name == "DefaultTest"
                mock_get_defaults.assert_called_once() # Ensure defaults were loaded

    def test_ensure_initialized_calls_initialize_once(self):
        """Test that ensure_initialized calls initialize only if not already initialized."""
        service = PHIDetectionService()
        assert not service._initialized

        # Mock initialize to check if it's called
        with patch.object(service, 'initialize', wraps=service.initialize) as mock_init:
            service.ensure_initialized()
            assert service._initialized
            mock_init.assert_called_once()

        # Call again, should not call initialize again
        with patch.object(service, 'initialize') as mock_init_again:
             service.ensure_initialized()
             mock_init_again.assert_not_called()


    def test_detect_phi_empty_text(self, phi_detection_service):
        """Test that detect_phi returns empty list for empty text."""
        results = phi_detection_service.detect_phi("")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_contains_phi_empty_text(self, phi_detection_service):
        """Test that contains_phi returns False for empty text."""
        assert not phi_detection_service.contains_phi("")

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("No PHI here", False),
            ("SSN: 123-45-6789", False), # SSN pattern not in mock fixture
            ("Contact me at test@example.com", False), # Email pattern not in mock
            ("Call me at (555) 123-4567", True), # Phone pattern is in mock
            ("John Smith is 92 years old", True), # Name pattern is in mock
            ("The patient's MRN is MRN12345", False), # MRN pattern not in mock
        ]
    )
    def test_contains_phi(self, phi_detection_service, text, expected):
        """Test contains_phi with various texts using mocked patterns."""
        assert phi_detection_service.contains_phi(text) == expected

    @pytest.mark.parametrize(
        "text,phi_type",
        [
            # ("SSN: 123-45-6789", "US SSN"), # Not in mock
            # ("Contact me at test@example.com", "Email Address"), # Not in mock
            ("Call me at (555) 123-4567", "US Phone Number"),
            ("John Smith lives here", "Full Name"),
            # ("Born on 01/01/1980", "Date"), # Not in mock
            # ("Lives at 123 Main St, Anytown, CA 12345", "Address"), # Not in mock
            # ("Credit card: 4111 1111 1111 1111", "Credit Card"), # Not in mock
            # ("Patient is 95 years old", "Age over 90"), # Not in mock
        ]
    )
    def test_detect_phi_finds_different_types(
        self, phi_detection_service, text, phi_type):
        """Test that detect_phi finds different types of PHI based on mocked patterns."""
        results = phi_detection_service.detect_phi(text)

        # Should find at least one instance of the expected PHI type
        assert any(r["type"] == phi_type for r in results)

    def test_detect_phi_results_format(self, phi_detection_service):
        """Test that detect_phi returns correctly formatted results."""
        text = "Call John Smith at (555) 123-4567"
        results = phi_detection_service.detect_phi(text)

        assert len(results) == 2  # Should find Name and Phone

        # Check structure of results (order might vary)
        found_name = False
        found_phone = False
        for result in results:
            assert "type" in result
            assert "category" in result
            assert "risk_level" in result
            assert "start" in result
            assert "end" in result
            assert "value" in result
            assert "description" in result
            if result["type"] == "Full Name":
                found_name = True
            if result["type"] == "US Phone Number":
                found_phone = True
        assert found_name
        assert found_phone


    @pytest.mark.parametrize(
        "text,replacement,expected",
        [
            ("SSN: 123-45-6789", "[REDACTED]", "SSN: 123-45-6789"), # No SSN pattern
            ("Contact: test@example.com", "***PHI***", "Contact: test@example.com"), # No Email pattern
            ("John Smith, DOB: 01/01/1980", "[PHI]", "[PHI], DOB: 01/01/1980"), # Only Name redacted
            ("Call (555) 123-4567", "[PHONE]", "Call [PHONE]"),
            ("No PHI here", "[REDACTED]", "No PHI here"),
        ]
    )
    def test_redact_phi(self, phi_detection_service, text, replacement, expected):
        """Test redacting PHI with different replacement strings using mocked patterns."""
        redacted = phi_detection_service.redact_phi(text, replacement)
        assert redacted == expected

    def test_redact_phi_empty_text(self, phi_detection_service):
        """Test that redact_phi handles empty text gracefully."""
        assert phi_detection_service.redact_phi("") == ""

    def test_redact_phi_overlapping_matches(self, phi_detection_service):
        """Test that redact_phi correctly handles potentially overlapping PHI based on mock."""
        # Using mock patterns: "Full Name" and "US Phone Number"
        text = "Patient John Smith called from (555) 123-4567"
        redacted = phi_detection_service.redact_phi(text)

        # Based on mock patterns, only Name and Phone should be redacted
        # Allow for default redaction marker or category-based marker
        assert "[REDACTED:name]" in redacted or "[REDACTED]" in redacted
        assert "[REDACTED:contact]" in redacted or "[REDACTED]" in redacted
        assert "John Smith" not in redacted
        assert "(555) 123-4567" not in redacted

    def test_get_phi_types(self, phi_detection_service):
        """Test getting the list of PHI types based on mocked patterns."""
        phi_types = phi_detection_service.get_phi_types()

        assert isinstance(phi_types, list)
        assert len(phi_types) == 2 # Based on mock
        assert "US Phone Number" in phi_types
        assert "Full Name" in phi_types

    def test_get_statistics(self, phi_detection_service):
        """Test getting statistics about PHI patterns based on mocked patterns."""
        stats = phi_detection_service.get_statistics()

        assert "total_patterns" in stats
        assert "categories" in stats
        assert "risk_levels" in stats

        assert stats["total_patterns"] == 2 # Based on mock
        assert len(stats["categories"]) == 2 # name, contact
        assert "name" in stats["categories"]
        assert "contact" in stats["categories"]
        assert "high" in stats["risk_levels"]
        assert stats["risk_levels"]["high"] == 2 # Both mock patterns are high risk

    @patch("app.infrastructure.ml.phi_detection.re")
    def test_phi_pattern_creation(self, mock_re):
        """Test creating a PHIPattern instance."""
        # Mock re.compile for testing
        mock_compiled_pattern = MagicMock()
        mock_re.compile.return_value = mock_compiled_pattern

        pattern = PHIPattern( # Corrected instantiation
            name="Test Pattern",
            pattern=r"test", # Pass regex string
            description="A test pattern",
            risk_level="high",
            category="test",
        )

        assert pattern.name == "Test Pattern"
        # Check that re.compile was called with the pattern string
        mock_re.compile.assert_called_once_with(r"test")
        assert pattern.pattern == mock_compiled_pattern # Check it stores the compiled pattern
        assert pattern.description == "A test pattern"
        assert pattern.risk_level == "high"
        assert pattern.category == "test"

    def test_error_handling(self, phi_detection_service):
        """Test that the service handles errors during detection/redaction gracefully."""
        # Mock the ensure_initialized to raise an error during a call
        with patch.object(phi_detection_service, "ensure_initialized", side_effect=Exception("Initialization failed")):
            with pytest.raises(PHIDetectionError):
                phi_detection_service.contains_phi("Test text")

            with pytest.raises(PHIDetectionError):
                phi_detection_service.detect_phi("Test text")

            with pytest.raises(PHIDetectionError):
                phi_detection_service.redact_phi("Test text")

            # Anonymize might depend on detect_phi, so it should also raise
            with pytest.raises(PHIDetectionError):
                phi_detection_service.anonymize_phi("Test text")
