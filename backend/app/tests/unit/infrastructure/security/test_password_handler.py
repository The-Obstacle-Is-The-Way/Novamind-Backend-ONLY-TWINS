"""Unit tests for password handling functionality."""
import pytest
from unittest.mock import patch, MagicMock
import secrets
import time

from app.infrastructure.security.password_handler import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    PasswordStrengthError,
    get_random_password,
    COMMON_PASSWORDS,
    PasswordStrengthResult,
)


class TestPasswordHashing:
    """Test suite for password hashing and verification."""

    def test_password_hash_different_from_original(self):
        """Test that the hashed password is different from the original."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > len(password)

        def test_password_hash_is_deterministic(self):
        """Test that hashing the same password with same salt produces same hash."""
        password = "SecurePassword123!"

        # Mock the salt generation to return the same value
        fixed_salt = b"fixed_salt_for_testing"
        with patch(
            "app.infrastructure.security.password_handler.os.urandom",
            return_value=fixed_salt,
        ):
            hashed1 = get_password_hash(password)
            hashed2 = get_password_hash(password)

            assert hashed1 == hashed2

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
        # None password
        assert verify_password(None, "somehash") is False

        # None hash
        assert verify_password("somepassword", None) is False

        # Both None
        assert verify_password(None, None) is False

        def test_hashing_is_slow_enough_for_security(self):
        """Test that password hashing takes a reasonable amount of time for security."""
        password = "SecurePassword123!"

        start_time = time.time()
        get_password_hash(password)
        duration = time.time() - start_time

        # Should take at least some time to be secure against brute force
        # This is a balance - too fast is insecure, too slow is bad UX
        # Typically we want at least 100ms per hash
        assert (
            duration > 0.05
        ), "Password hashing is too fast and may be vulnerable to brute force"


        class TestPasswordStrengthValidation:
    """Test suite for password strength validation."""

    def test_valid_password_strength(self):
        """Test that a strong password passes validation."""
        password = "SecureP@ssw0rd123!"

        result = validate_password_strength(password)

        assert result.is_valid is True
        assert result.score >= 3  # Strong enough
        assert len(result.feedback) == 0  # No improvement suggestions

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

            def test_password_without_special_chars(self):
        """Test that passwords without special characters get appropriate feedback."""
        password = "SecurePassword123"

        result = validate_password_strength(password)

        # Might still be valid depending on other criteria
        if not result.is_valid:
            assert any(
                "special" in feedback.lower() or "symbol" in feedback.lower()
                for feedback in result.feedback
            )

    def test_common_password(self):
        """Test that common passwords are rejected."""
        # Use a password from the common passwords list
        password = COMMON_PASSWORDS[0] if COMMON_PASSWORDS else "password123"

        result = validate_password_strength(password)

        assert result.is_valid is False
        assert result.score < 2  # Very weak
        assert any("common" in feedback.lower() for feedback in result.feedback)

        def test_password_with_personal_info(self):
        """Test that passwords with personal info get appropriate feedback."""
        # Mock the personal info check to simulate finding personal information
        with patch(
            "app.infrastructure.security.password_handler._contains_personal_info",
            return_value=True,
        ):
            password = "MyNameIsBob123!"

            result = validate_password_strength(password)

            assert result.is_valid is False
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
        # A password with high entropy
        complex_password = "X2*fP9q@L5w#D7!zS"

        # A password with lower entropy
        simple_password = "password123"

        complex_result = validate_password_strength(complex_password)
        simple_result = validate_password_strength(simple_password)

        # Complex should have higher entropy
        assert complex_result.entropy > simple_result.entropy

        def test_repeated_characters(self):
        """Test that passwords with repeated characters get appropriate feedback."""
        password = "aaaBBB123!!!"

        result = validate_password_strength(password)

        # Check if repetition is caught
        repetition_feedback = False
        for feedback in result.feedback:
            if "repeat" in feedback.lower() or "sequential" in feedback.lower():
                repetition_feedback = True
                break

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

        # Should be valid by default
        result = validate_password_strength(password)
        assert result.is_valid is True

        # Should have a mix of character types
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        assert has_upper
        assert has_lower
        assert has_digit
        assert has_special

        def test_random_password_uniqueness(self):
        """Test that generated passwords are unique."""
        num_passwords = 10
        passwords = [get_random_password(16) for _ in range(num_passwords)]

        # All passwords should be different
        assert len(set(passwords)) == num_passwords

        @patch("app.infrastructure.security.password_handler.secrets.choice")
        def test_uses_cryptographically_secure_rng(self, mock_choice):
        """Test that password generation uses cryptographically secure RNG."""
        # Mock the choice function to track calls
        mock_choice.side_effect = lambda x: x[0]

        get_random_password(16)

        # Verify that secrets.choice was used (not random.choice)
        assert mock_choice.called
