import pytest
from datetime import datetime, timedelta

"""
Standalone tests for utility functions in the Novamind Digital Twin platform.

These tests have no external dependencies and can run in complete isolation.
They test pure functions and business logic with mathematical precision and adherence to 
quantum neural architecture principles including hypothalamus-pituitary connectivity.
"""

# Import utilities to test
from app.core.utils.date_utils import format_date_iso, is_date_in_range
from app.core.utils.string_utils import sanitize_name, truncate_text


@pytest.mark.standalone()
def test_is_date_in_range():
    """Test date range validation logic."""
    # Base date
    base_date = datetime(2025, 1, 1)

    # Test dates within range
    assert is_date_in_range(
        base_date,
        base_date - timedelta(days=10),
        base_date + timedelta(days=10)
    )

    # Test dates at range boundaries
    assert is_date_in_range(
        base_date,
        base_date,
        base_date + timedelta(days=10)
    )
    assert is_date_in_range(
        base_date + timedelta(days=10),
        base_date,
        base_date + timedelta(days=10)
    )

    # Test dates outside range
    assert not is_date_in_range(
        base_date - timedelta(days=11),
        base_date,
        base_date + timedelta(days=10)
    )
    assert not is_date_in_range(
        base_date + timedelta(days=11),
        base_date,
        base_date + timedelta(days=10)
    )

    # Test with None values
    assert not is_date_in_range(
        None,
        base_date,
        base_date + timedelta(days=10)
    )
    assert not is_date_in_range(
        base_date,
        None,
        base_date + timedelta(days=10)
    )
    assert not is_date_in_range(
        base_date,
        base_date,
        None
    )

    # Test with inverted range (end before start)
    assert not is_date_in_range(
        base_date,
        base_date + timedelta(days=10),
        base_date
    )


@pytest.mark.standalone()
def test_format_date_iso():
    """Test ISO date formatting."""
    # Test basic formatting
    date = datetime(2025, 1, 1, 12, 30, 45)
    assert format_date_iso(date) == "2025-01-01T12:30:45"

    # Test with microseconds
    date_with_micros = datetime(2025, 1, 1, 12, 30, 45, 123456)
    assert format_date_iso(date_with_micros) == "2025-01-01T12:30:45.123456"

    # Test with timezone parameter
    assert format_date_iso(date, include_timezone=True).endswith("Z")

    # Test None handling
    assert format_date_iso(None) is None

    # Test custom format
    assert format_date_iso(date, format_str="%Y-%m-%d") == "2025-01-01"


@pytest.mark.standalone()
def test_sanitize_name():
    """Test name sanitization utility."""
    # Test basic sanitization
    assert sanitize_name("John Doe") == "john_doe"
    
    # Test spaces and special characters
    assert sanitize_name("John-Doe Smith!") == "john_doe_smith"
    
    # Test leading/trailing spaces
    assert sanitize_name("  John Doe  ") == "john_doe"
    
    # Test multiple spaces
    assert sanitize_name("John   Doe") == "john_doe"
    
    # Test mixed case
    assert sanitize_name("JoHn DoE") == "john_doe"
    
    # Test numbers
    assert sanitize_name("John Doe 123") == "john_doe_123"
    
    # Test with None
    assert sanitize_name(None) == ""
    
    # Test empty string
    assert sanitize_name("") == ""


@pytest.mark.standalone()
def test_truncate_text():
    """Test text truncation utility."""
    # Test basic truncation
    assert truncate_text("This is a long text", 10) == "This is a..."
    
    # Test no truncation needed
    assert truncate_text("Short", 10) == "Short"
    
    # Test exact length
    assert truncate_text("Exactly 10", 10) == "Exactly 10"
    
    # Test with custom suffix
    assert truncate_text("This is a long text", 10, suffix="[...]") == "This is a[...]"
    
    # Test with empty suffix
    assert truncate_text("This is a long text", 10, suffix="") == "This is a "
    
    # Test with None
    assert truncate_text(None, 10) == ""
    
    # Test with empty string
    assert truncate_text("", 10) == ""
    
    # Test with negative max_length
    assert truncate_text("This is a long text", -5) == "This is a long text"
    
    # Test with zero max_length
    assert truncate_text("This is a long text", 0) == "..."
