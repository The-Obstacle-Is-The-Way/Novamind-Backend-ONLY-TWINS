# -*- coding: utf-8 -*-
"""
NOVAMIND Password Handler
=======================
Secure password handling for the NOVAMIND psychiatric platform.
Implements HIPAA-compliant password hashing and verification.
"""

import secrets
import string
from typing import Optional, Tuple

from passlib.context import CryptContext

from app.core.config import settings
from app.core.utils.logging import HIPAACompliantLogger

# Initialize logger
logger = HIPAACompliantLogger(__name__)


class PasswordHandler:
    """
    Handles secure password hashing and verification.
    Implements HIPAA-compliant password security.
    """

    def __init__(self):
        """Initialize password context with secure hashing schemes."""
        # Configure password hashing schemes with appropriate security levels
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=settings.security.PASSWORD_SALT_ROUNDS,
        )
        logger.debug("PasswordHandler initialized with secure hashing schemes")

    def hash_password(self, password: str) -> str:
        """
        Hash a password securely.

        Args:
            password: Plain text password

        Returns:
            Securely hashed password
        """
        hashed_password = self.pwd_context.hash(password)
        logger.debug("Password hashed securely")
        return hashed_password

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Previously hashed password

        Returns:
            True if password matches, False otherwise
        """
        is_valid = self.pwd_context.verify(plain_password, hashed_password)
        if is_valid:
            logger.debug("Password verification successful")
        else:
            logger.warning("Password verification failed")
        return is_valid

    def password_needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be upgraded.

        Args:
            hashed_password: Currently stored password hash

        Returns:
            True if rehashing is recommended, False otherwise
        """
        return self.pwd_context.needs_update(hashed_password)

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
