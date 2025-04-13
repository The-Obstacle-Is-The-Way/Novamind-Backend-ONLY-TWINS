import pytest
from app.infrastructure.security.log_sanitizer import (
    LogSanitizer,
    SanitizerConfig,
    RedactionMode,
)
import json


@pytest.fixture
def sanitizer():
    """Create a sanitizer with default configuration."""

    return LogSanitizer()

    class TestPHISanitizer:
    """Test suite for PHI sanitization functionality."""

    @pytest.mark.standalone()
    def test_preservation_of_non_phi(self, sanitizer):
        """Test that non-PHI data is preserved during sanitization."""
        mixed_data = {
            "patient_id": "PT12345",  # PHI - patient IDs are PHI under HIPAA
            "name": "John Smith",  # PHI
            "ssn": "123-45-6789",  # PHI
            "status": "Active",  # Not PHI
            "priority": 1,  # Not PHI
            "is_insured": True,  # Not PHI
        }

    sanitized = sanitizer.sanitize_dict(mixed_data)

    # PHI should be sanitized
    assert sanitized["name"] != "John Smith"
    assert sanitized["ssn"] != "123-45-6789"
    assert (
        sanitized["patient_id"] != "PT12345"
    )  # Patient ID is PHI and should be redacted

    # Non-PHI should be preserved
    assert sanitized["status"] == "Active"
    assert sanitized["priority"] == 1
    assert sanitized["is_insured"] is True

    # Additional tests can be added here if needed
