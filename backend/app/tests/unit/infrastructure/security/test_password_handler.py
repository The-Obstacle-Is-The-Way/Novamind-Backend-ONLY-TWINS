# -*- coding: utf-8 -*-
"""
Unit tests for Password Handler.

These tests verify that our password handling meets HIPAA security requirements
for secure password storage, validation, and generation.
"""

import pytest
import re
from unittest.mock import patch, MagicMock

from app.infrastructure.security.password.password_handler import PasswordHandler

@pytest.fixture
def password_handler():
    """
    Create a password handler instance for testing.
    
    Returns:
        PasswordHandler instance
    """
    return PasswordHandler()


@pytest.mark.db_required()
class TestPasswordHandler:
    """Test suite for password handler."""
    
    def test_hash_password(self, password_handler):
        """Test that passwords are properly hashed."""
        # Arrange
        test_password = "Secure@Password123"
        
        # Act
        hashed = password_handler.hash_password(test_password)
        
        # Assert
        assert hashed is not None
        assert hashed  !=  test_password
        assert len(hashed) > 20  # Bcrypt hashes are longer than this
        assert hashed.startswith("$2")  # Bcrypt hash signature
    
    def test_verify_password_valid(self, password_handler):
        """Test that valid password verification works."""
        # Arrange
        test_password = "Secure@Password123"
        hashed = password_handler.hash_password(test_password)
        
        # Act
        result = password_handler.verify_password(test_password, hashed)
        
        # Assert
        assert result is True
    
    def test_verify_password_invalid(self, password_handler):
        """Test that invalid password verification fails."""
        # Arrange
        test_password = "Secure@Password123"
        wrong_password = "WrongPassword456!"
        hashed = password_handler.hash_password(test_password)
        
        # Act
        result = password_handler.verify_password(wrong_password, hashed)
        
        # Assert
        assert result is False
    
    def test_password_needs_rehash(self, password_handler):
        """Test detection of passwords that need rehashing."""
        # This is more challenging to test directly since we'd need outdated hashes
        # We'll mock the internal pwd_context.needs_update method
        
        with patch.object(password_handler.pwd_context, 'needs_update') as mock_needs_update:
            # Arrange
            mock_needs_update.return_value = True
            test_hash = "$2a$12$mockhashformockhashformoc"
            
            # Act
            result = password_handler.password_needs_rehash(test_hash)
            
            # Assert
            assert result is True
            mock_needs_update.assert _called_once_with(test_hash)
    
    def test_generate_secure_password(self, password_handler):
        """Test secure password generation."""
        # Act
        password = password_handler.generate_secure_password()
        
        # Assert
        assert len(password) == 16  # Default length
        
        # Check character sets
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*()-_=+[]{}|;,.<>?/" for c in password)
    
    def test_generate_secure_password_custom_length(self, password_handler):
        """Test secure password generation with custom length."""
        # Act
        password = password_handler.generate_secure_password(length=24)
        
        # Assert
        assert len(password) == 24
        
        # Check character sets are still included with longer length
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*()-_=+[]{}|;,.<>?/" for c in password)
    
    def test_generate_secure_password_minimum_length(self, password_handler):
        """Test secure password generation with length below minimum."""
        # Act - try to generate a short password (should enforce minimum)
        password = password_handler.generate_secure_password(length=8)
        
        # Assert
        assert len(password) == 12  # Should enforce minimum of 12
    
    def test_password_strength_valid(self, password_handler):
        """Test password strength validation with valid password."""
        # Arrange
        strong_password = "Str0ng@P4ssw0rd!"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(strong_password)
        
        # Assert
        assert is_valid is True
        assert error is None
    
    def test_password_strength_too_short(self, password_handler):
        """Test password strength validation with short password."""
        # Arrange
        short_password = "Short1!"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(short_password)
        
        # Assert
        assert is_valid is False
        assert "at least 12 characters" in error
    
    def test_password_strength_missing_uppercase(self, password_handler):
        """Test password strength validation with missing uppercase."""
        # Arrange
        password = "no_uppercase123!"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(password)
        
        # Assert
        assert is_valid is False
        assert "uppercase" in error
    
    def test_password_strength_missing_lowercase(self, password_handler):
        """Test password strength validation with missing lowercase."""
        # Arrange
        password = "NO_LOWERCASE123!"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(password)
        
        # Assert
        assert is_valid is False
        assert "lowercase" in error
    
    def test_password_strength_missing_digit(self, password_handler):
        """Test password strength validation with missing digit."""
        # Arrange
        password = "NoDigits@Here!"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(password)
        
        # Assert
        assert is_valid is False
        assert "digits" in error
    
    def test_password_strength_missing_special(self, password_handler):
        """Test password strength validation with missing special characters."""
        # Arrange
        password = "NoSpecialChars123"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(password)
        
        # Assert
        assert is_valid is False
        assert "special characters" in error
    
    def test_password_strength_common_patterns(self, password_handler):
        """Test password strength validation rejecting common patterns."""
        # Arrange
        password = "Password12345!"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(password)
        
        # Assert
        assert is_valid is False
        assert "common patterns" in error
    
    def test_password_strength_repeating_chars(self, password_handler):
        """Test password strength validation rejecting repeating characters."""
        # Arrange
        password = "StrongPasswwwrd123!"
        
        # Act
        is_valid, error = password_handler.validate_password_strength(password)
        
        # Assert
        assert is_valid is False
        assert "repeated characters" in error
    
    @patch('app.infrastructure.security.password.password_handler.logger')
    def test_logging_behavior(self, mock_logger, password_handler):
        """Test that no sensitive information is logged."""
        # Arrange
        test_password = "SecretP@ssw0rd!"
        
        # Act
        password_handler.hash_password(test_password)
        
        # Assert logger was called but didn't contain the password
        mock_logger.debug.assert _called()
        
        # Check all calls to logger to ensure password is not present
        for call in mock_logger.debug.call_args_list:
            log_message = call[0][0]
            assert test_password not in log_message
    
    def test_random_password_uniqueness(self, password_handler):
        """Test that generated passwords are unique/random."""
        # Generate multiple passwords
        passwords = [
            password_handler.generate_secure_password() 
            for _ in range(10)
        ]
        
        # Check that all are unique
        assert len(passwords) == len(set(passwords))