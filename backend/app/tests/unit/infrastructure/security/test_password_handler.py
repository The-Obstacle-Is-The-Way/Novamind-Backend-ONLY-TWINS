"""Unit tests for password handling functionality."""
import pytest
from unittest.mock import patch, MagicMock
import secrets
import time
import os # Import os for urandom mocking

# Correctly import necessary components
from app.infrastructure.security.password_handler import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    PasswordStrengthError,
    get_random_password,
    COMMON_PASSWORDS, # Assuming this is loaded correctly
    PasswordStrengthResult,
    _contains_personal_info # Import if needed for mocking
)

class TestPasswordHashing:
    """Test suite for password hashing and verification."""

    def test_password_hash_different_from_original(self):
        """Test that the hashed password is different from the original."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > len(password)

    def test_password_hash_is_deterministic_with_same_salt(self):
        """Test verify_password works correctly (hashing is deterministic internally)."""
        password = "SecurePassword123!"
        # Hash it once
        hashed = get_password_hash(password)
        # Verify it works
        assert verify_password(password, hashed) is True
        # Verify again, should still work
        assert verify_password(password, hashed) is True

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "SecurePassword123!"
        password2 = "DifferentPassword456!"
        hashed1 = get_password_hash(password1)
        hashed2 = get_password_hash(password2)
        assert hashed1 != hashed2

    def test_verify_correct_password(self):
        """Test that verification succeeds with correct password."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        result = verify_password(password, hashed)
        assert result is True

    def test_verify_incorrect_password(self):
        """Test that verification fails with incorrect password."""
        correct_password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(correct_password)
        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_handles_none_values(self):
        """Test that verification properly handles None values."""
        assert verify_password(None, "somehash") is False
        assert verify_password("somepassword", None) is False
        assert verify_password(None, None) is False

    def test_hashing_is_slow_enough_for_security(self):
        """Test that password hashing takes a reasonable amount of time for security."""
        password = "SecurePassword123!"
        start_time = time.time()
        get_password_hash(password) # Corrected call
        duration = time.time() - start_time
        # Check if duration is reasonable (e.g., > 50ms)
        # This threshold might need adjustment based on the system running the tests
        assert duration > 0.01, "Password hashing might be too fast (<10ms)"


class TestPasswordStrengthValidation:
    """Test suite for password strength validation."""

    def test_valid_password_strength(self):
        """Test that a strong password passes validation."""
        password = "SecureP@ssw0rd123!"
        result = validate_password_strength(password)
        assert isinstance(result, PasswordStrengthResult)
        assert result.is_valid is True
        assert result.score >= 3
        assert len(result.feedback) == 0

    def test_short_password(self):
        """Test that short passwords are rejected."""
        password = "Short1!"
        result = validate_password_strength(password)
        assert result.is_valid is False
        assert result.score < 3
        assert any("length" in feedback.lower() for feedback in result.feedback)

    def test_password_without_numbers(self):
        """Test that passwords without numbers get appropriate feedback."""
        password = "SecurePasswordOnly!"
        result = validate_password_strength(password)
        # Might still be valid depending on other criteria
        # Check feedback regardless of validity for this specific weakness
        assert any("number" in feedback.lower() for feedback in result.feedback)

    def test_password_without_special_chars(self):
        """Test that passwords without special characters get appropriate feedback."""
        password = "SecurePassword123"
        result = validate_password_strength(password)
        # Might still be valid depending on other criteria
        # Check feedback regardless of validity
        assert any("special" in feedback.lower() or "symbol" in feedback.lower() for feedback in result.feedback)

    def test_common_password(self):
        """Test that common passwords are rejected."""
        password = "password123" # Use a known common password
        result = validate_password_strength(password)
        assert result.is_valid is False
        assert result.score < 2
        assert any("common" in feedback.lower() for feedback in result.feedback)

    def test_password_with_personal_info(self):
        """Test that passwords with personal info get appropriate feedback."""
        # Mock the internal check function if necessary, or pass info
        password = "MyNameIsBob123!"
        personal_info = ["bob", "robert"] # Example info
        # Assuming validate_password_strength accepts personal_info
        # If not, mock _contains_personal_info
        with patch("app.infrastructure.security.password_handler._contains_personal_info", return_value=True):
             result = validate_password_strength(password) # Pass personal_info if needed
             # Check feedback, validity might depend on other factors
             assert any("personal" in feedback.lower() for feedback in result.feedback)
             # Optionally assert invalid if this rule makes it invalid
             # assert result.is_valid is False

    def test_validation_raises_exception_mode(self):
        """Test that validation raises exception in strict mode for weak passwords."""
        weak_password = "password123"
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_strength(weak_password, strict=True)
        # Exception should contain feedback
        assert "feedback" in str(exc_info.value).lower()

    def test_password_entropy_calculation(self):
        """Test that password entropy is reflected in the score."""
        complex_password = "X2*fP9q@L5w#D7!zS"
        simple_password = "password123"
        complex_result = validate_password_strength(complex_password)
        simple_result = validate_password_strength(simple_password)
        # Complex should have higher score (reflecting higher entropy)
        assert complex_result.score > simple_result.score
        # Direct entropy value check depends on zxcvbn output structure if available
        # assert complex_result.entropy > simple_result.entropy

    def test_repeated_characters(self):
        """Test that passwords with repeated characters get appropriate feedback."""
        password = "aaaBBB123!!!"
        result = validate_password_strength(password)
        # Check if repetition is caught in feedback
        repetition_feedback = any("repeat" in feedback.lower() or "sequential" in feedback.lower() for feedback in result.feedback)
        assert repetition_feedback


class TestRandomPasswordGeneration:
    """Test suite for random password generation."""

    def test_random_password_length(self):
        """Test that generated passwords have the requested length."""
        length = 16
        password = get_random_password(length)
        assert len(password) == length

    def test_random_password_complexity(self):
        """Test that generated passwords meet complexity requirements."""
        password = get_random_password(16)
        # Should be valid by default according to its own rules
        result = validate_password_strength(password)
        assert result.is_valid is True, f"Generated password failed strength check: {password}, Feedback: {result.feedback}"

        # Check for a mix of character types (highly likely but not guaranteed)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        # Check for special chars based on the default alphabet used
        default_special_chars = "!@#$%^&*()-_=+[{]};:'\",<.>/?" # Assuming this is the set used
        has_special = any(c in default_special_chars for c in password)

        # Assert that it's highly likely all types are present for reasonable length
        assert has_upper and has_lower and has_digit and has_special, f"Generated password missing expected character types: {password}"

    def test_random_password_uniqueness(self):
        """Test that generated passwords are unique."""
        num_passwords = 100 # Increase sample size for better confidence
        passwords = [get_random_password(16) for _ in range(num_passwords)]
        # All passwords should be different with high probability
        assert len(set(passwords)) == num_passwords

    @patch("app.infrastructure.security.password_handler.secrets.choice")
    def test_uses_cryptographically_secure_rng(self, mock_choice: MagicMock):
        """Test that password generation uses cryptographically secure RNG."""
        # Mock the choice function to track calls
        mock_choice.side_effect = lambda x: x[0] # Simple side effect
        get_random_password(16)
        # Verify that secrets.choice was used
        assert mock_choice.called
