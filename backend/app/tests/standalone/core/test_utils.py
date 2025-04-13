import pytest
from datetime import datetime, timedelta

"""
Standalone tests for utility functions in the Novamind Digital Twin platform.

These tests have no external dependencies and can run in complete isolation.
They test pure functions and business logic.
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
        base_date -
        timedelta(
            days=10),
        base_date +
        timedelta(
            days=10))

    # Test dates at range boundaries
    assert is_date_in_range(
        base_date,
        base_date,
        base_date +
        timedelta(
            days=10))
    assert is_date_in_range(
        base_date +
        timedelta(
            days=10),
        base_date,
        base_date +
        timedelta(
            days=10))

    # Test dates outside range
    assert not is_date_in_range(
        base_date -
        timedelta(
            days=1),
        base_date,
        base_date +
        timedelta(
            days=10))
    assert not is_date_in_range(
        base_date +
        timedelta(
            days=11),
        base_date,
        base_date +
        timedelta(
            days=10))


    @pytest.mark.standalone()
    def test_format_date_iso():

            """Test ISO date formatting."""
        # Test date
        test_date = datetime(2025, 1, 1, 12, 30, 45)

        # Test default formatting (with time)
        assert format_date_iso(test_date) == "2025-01-01T12:30:45"

        # Test date-only formatting
        assert format_date_iso(test_date, include_time=False) == "2025-01-01"

        @pytest.mark.standalone()
        def test_sanitize_name():

                """Test name sanitization for security and consistency."""
        # Test basic sanitization
        assert sanitize_name("John O'Connor") == "John OConnor"
        assert sanitize_name(" Bob Smith ") == "Bob Smith"

        # Test special character removal
        assert sanitize_name("Alice <script>") == "Alice script"
        assert sanitize_name("User@Example.com") == "UserExamplecom"

        # Test empty input
        assert sanitize_name("") == ""
        assert sanitize_name(None) == ""

        @pytest.mark.standalone()
        def test_truncate_text():

                """Test text truncation utility."""
            # Test no truncation needed
            assert truncate_text("Short text", 20) == "Short text"

            # Test exact length
            assert truncate_text("Exactly twenty chars", 20) == "Exactly twenty chars"

            # Test truncation
            assert (
            truncate_text("This text is too long and should be truncated", 20)
            == "This text is too lo..."
    )

    # Test custom suffix
    assert (
        truncate_text(
            "This text is too long and should be truncated", 20, suffix="[...]"
        )
        == "This text is too [...]"
    )
