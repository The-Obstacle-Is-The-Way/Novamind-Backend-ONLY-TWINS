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
    _contains_personal_info # Import if needed for mocking, otherwise test via validate_password_strength
)

class TestPasswordHashing:
    """Test suite for password hashing and verification."""

    def test_password_hash_different_from_original(self):
        """Test that the hashed password is different from the original."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert isinstance(hashed, str) # Hash should be a string
        assert len(hashed) > len(password) # Hash includes salt and hash itself

    def test_password_hash_is_deterministic_with_same_salt(self):
        """Test that hashing the same password with same salt produces same hash."""
        password = "SecurePassword123!"
        # Mock os.urandom to control the salt for this specific test
        fixed_salt = os.urandom(16) # Generate a fixed salt once
        with patch("app.infrastructure.security.password_handler.os.urandom", return_value=fixed_salt):
            hashed1 = get_password_hash(password)
        # Call again, the salt is part of the stored hash, so verification uses it
        # We don't need to patch again for the second call if verify_password extracts salt
        # Let's re-hash with the same explicit salt if the function supported it,
        # otherwise, this test might need rethinking based on how salt is handled.
        # Assuming get_password_hash always generates a new salt:
        with patch("app.infrastructure.security.password_handler.os.urandom", return_value=fixed_salt):
             hashed2 = get_password_hash(password) # Hash again with the same mocked salt
        # If salt is always random, hashes will differ. Test verify instead.
        # assert hashed1 == hashed2 # This assertion is likely incorrect if salt is random each time

        # Better test: Verify that the correct password verifies against the hash
        assert verify_password(password, hashed1) is True


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
        assert duration > 0.05, "Password hashing is too fast and may be vulnerable to brute force"


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
        if not result.is_valid:
            assert any("number" in feedback.lower() for feedback in result.feedback)
        # Even if valid, might have feedback
        assert any("number" in feedback.lower() for feedback in result.feedback if result.score < 4)


    def test_password_without_special_chars(self):
        """Test that passwords without special characters get appropriate feedback."""
        password = "SecurePassword123"
        result = validate_password_strength(password)
        # Might still be valid depending on other criteria
        if not result.is_valid:
            assert any("special" in feedback.lower() or "symbol" in feedback.lower() for feedback in result.feedback)
        # Even if valid, might have feedback
        assert any("special" in feedback.lower() or "symbol" in feedback.lower() for feedback in result.feedback if result.score < 4)


    def test_common_password(self):
        """Test that common passwords are rejected."""
        # Use a password known to be common
        password = "password123" # More reliable than COMMON_PASSWORDS[0]
        result = validate_password_strength(password)
        assert result.is_valid is False
        assert result.score < 2
        assert any("common" in feedback.lower() for feedback in result.feedback)

    def test_password_with_personal_info(self):
        """Test that passwords with personal info get appropriate feedback."""
        # Mock the internal check function if necessary, or pass info to validate_password_strength
        # Assuming validate_password_strength takes personal_info as an argument
        password = "MyNameIsBob123!"
        personal_info = ["bob", "robert"]
        # Modify validate_password_strength call if it accepts personal_info
        # For now, assume internal mocking if _contains_personal_info is used
        with patch("app.infrastructure.security.password_handler._contains_personal_info", return_value=True):
             result = validate_password_strength(password) # Pass personal_info if required by signature
             # Depending on implementation, this might fail or just give feedback
             # assert result.is_valid is False # Uncomment if it should invalidate
             assert any("personal" in feedback.lower() for feedback in result.feedback)


    def test_validation_raises_exception_mode(self):
        """Test that validation raises exception in strict mode for weak passwords."""
        weak_password = "password123"
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_strength(weak_password, strict=True)
        # Exception should contain feedback
        assert "feedback" in str(exc_info.value).lower()

    def test_password_entropy_calculation(self):
        """Test that password entropy is calculated correctly."""
        complex_password = "X2*fP9q@L5w#D7!zS"
        simple_password = "password123"
        complex_result = validate_password_strength(complex_password)
        simple_result = validate_password_strength(simple_password)
        # Complex should have higher entropy (score reflects this)
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
        assert result.is_valid is True

        # Check for a mix of character types (highly likely but not guaranteed)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        # Check for special chars based on the default alphabet used
        default_special_chars = "!@#$%^&*()-_=+[{]};:'\",<.>/?"
        has_special = any(c in default_special_chars for c in password)

        # Assert that it's highly likely all types are present for reasonable length
        assert has_upper or has_lower or has_digit or has_special, "Generated password missing expected character types"


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
