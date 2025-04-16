# -*- coding: utf-8 -*-
"""
NOVAMIND Password Handler
=======================
Secure password handling for the NOVAMIND psychiatric platform.
Implements HIPAA-compliant password hashing and verification.
"""

import secrets
import string
from typing import Optional, Tuple, List

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# Use canonical config import
# from app.core.config import get_settings
from app.config.settings import get_settings

# Use standard logger instead of old import
# from app.core.utils.logging import get_logger # Use the standard logger function
import logging

# Initialize logger
# logger = get_logger(__name__) # Use the standard logger function
logger = logging.getLogger(__name__)

# Default context using bcrypt
# default_crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHandler:
    """
    Handles password hashing and verification using passlib.
    Allows configuration of hashing schemes and parameters.
    """

    def __init__(self, schemes: Optional[List[str]] = None, deprecated: str = "auto"):
        """
        Initialize the PasswordHandler with specified schemes.

        Args:
            schemes: List of hashing schemes (e.g., ["bcrypt"]). Defaults to settings.
            deprecated: Handling of deprecated hashes ("auto", "warn", "error").
        """
        # ADDED: Load settings within __init__
        settings = get_settings()
        
        # Use schemes from settings if not provided, default to bcrypt if settings are missing
        default_schemes = ["bcrypt"]
        self.schemes = schemes or getattr(settings, 'PASSWORD_HASHING_SCHEMES', default_schemes)
        self.deprecated = deprecated
        
        try:
            self.context = CryptContext(schemes=self.schemes, deprecated=self.deprecated)
            logger.info(f"PasswordHandler initialized with schemes: {self.schemes}")
        except Exception as e:
            logger.error(f"Failed to initialize CryptContext with schemes {self.schemes}: {e}", exc_info=True)
            # Fallback to default context if initialization fails
            logger.warning("Falling back to default bcrypt CryptContext.")
            self.context = CryptContext(schemes=default_schemes, deprecated=deprecated)
            self.schemes = default_schemes # Update schemes to reflect fallback

    def get_password_hash(self, password: str) -> str:
        """
        Hashes a plain text password.

        Args:
            password: The plain text password.

        Returns:
            The hashed password.
            
        Raises:
            ValueError: If hashing fails.
        """
        try:
            return self.context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing failed: {e}", exc_info=True)
            raise ValueError("Password hashing failed.") from e

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain text password against a hashed password.

        Args:
            plain_password: The plain text password.
            hashed_password: The hashed password to compare against.

        Returns:
            True if the password matches, False otherwise.
        """
        try:
            return self.context.verify(plain_password, hashed_password)
        except Exception as e:
            # Log potential errors during verification (e.g., malformed hash)
            logger.warning(f"Password verification encountered an issue: {e}", exc_info=True)
            return False

    def password_needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be upgraded.

        Args:
            hashed_password: Currently stored password hash

        Returns:
            True if rehashing is recommended, False otherwise
        """
        return self.context.needs_update(hashed_password)

    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.

        Args:
            length: Length of password to generate (default: 16)

        Returns:
            Secure random password string
        """
        # Ensure minimum password length for security
        if length < 12:
            length = 12

        # Define character sets for secure passwords
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*()-_=+[]{}|;:,.<>?/"

        # Ensure at least one character from each set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]

        # Fill the rest with random characters from all sets
        all_chars = uppercase + lowercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))

        # Shuffle for randomness
        secrets.SystemRandom().shuffle(password)

        # Convert to string
        password_str = "".join(password)
        logger.debug(f"Generated secure password of length {length}")

        return password_str

    def validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength against HIPAA-compliant security requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check length
        if len(password) < 12:
            return False, "Password must be at least 12 characters long"

        # Check complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            return (
                False,
                "Password must include uppercase, lowercase, digits, and special characters",
            )

        # Check for common patterns (basic check)
        if (
            "12345" in password
            or "qwerty" in password.lower()
            or "password" in password.lower()
        ):
            return False, "Password contains common patterns"

        # Check for repeating characters
        for i in range(len(password) - 2):
            if password[i] == password[i + 1] == password[i + 2]:
                return False, "Password contains repeated characters"

        # All checks passed
        logger.debug("Password strength validation passed")
        return True, None

# Default instance for direct use (optional, depends on usage pattern)
# Consider using dependency injection instead for better testability
# _default_password_handler: Optional[PasswordHandler] = None
# def get_default_password_handler() -> PasswordHandler:
#     global _default_password_handler
#     if _default_password_handler is None:
#         _default_password_handler = PasswordHandler()
#     return _default_password_handler

# Utility functions using a default instance (if needed)
# def get_password_hash(password: str) -> str:
#     handler = get_default_password_handler()
#     return handler.get_password_hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     handler = get_default_password_handler()
#     return handler.verify_password(plain_password, hashed_password)
