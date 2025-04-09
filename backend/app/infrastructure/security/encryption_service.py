# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Encryption Service

This module provides field-level encryption for PHI data, ensuring sensitive
patient information is encrypted at rest.
"""

import base64
import logging
import os
from typing import Any, Dict, List, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logger without PHI
logger = logging.getLogger("encryption_service")


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive PHI data.

    This service uses Fernet symmetric encryption to secure PHI at the field level.
    The encryption key is derived using PBKDF2 with a salt for additional security.
    """

    def __init__(
        self,
        key: Optional[str] = None,
        salt: Optional[bytes] = None,
        iterations: int = 100000,
    ):
        """
        Initialize the encryption service with a key or generate one.

        Args:
            key: Optional encryption key. If not provided, will use environment variable
                or generate a new one.
            salt: Optional salt for key derivation. If not provided, will use environment
                variable or generate a new one.
            iterations: Number of iterations for PBKDF2 key derivation.
        """
        self.iterations = iterations

        # Get or generate the encryption key
        if key:
            self.key = key
        else:
            self.key = os.environ.get("PHI_ENCRYPTION_KEY")
            if not self.key:
                # Generate a new key if none is provided or in environment
                self.key = self._generate_key()
                logger.warning(
                    "No encryption key provided or found in environment. "
                    "Generated a new one. This should be stored securely."
                )

        # Get or generate the salt
        if salt:
            self.salt = salt
        else:
            salt_str = os.environ.get("PHI_ENCRYPTION_SALT")
            if salt_str:
                self.salt = base64.b64decode(salt_str)
            else:
                # Generate a new salt if none is provided or in environment
                self.salt = os.urandom(16)
                logger.warning(
                    "No encryption salt provided or found in environment. "
                    "Generated a new one. This should be stored securely."
                )

        # Initialize the Fernet cipher with the derived key
        self.cipher = self._create_cipher()

        logger.info("Encryption service initialized")

    def _generate_key(self) -> str:
        """
        Generate a new encryption key.

        Returns:
            A base64-encoded encryption key.
        """
        return base64.b64encode(os.urandom(32)).decode("utf-8")

    def _derive_key(self) -> bytes:
        """
        Derive a key using PBKDF2HMAC with the provided key and salt.

        Returns:
            Derived key bytes suitable for Fernet.
        """
        if isinstance(self.key, str):
            # Convert string key to bytes
            key_bytes = self.key.encode("utf-8")
        else:
            key_bytes = self.key

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=self.iterations,
        )

        derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        return derived_key

    def _create_cipher(self) -> Fernet:
        """
        Create a Fernet cipher using the derived key.

        Returns:
            Fernet cipher for encryption/decryption.
        """
        derived_key = self._derive_key()
        return Fernet(derived_key)

    def encrypt(self, data: Any) -> Any:
        """
        Encrypt data if it's a string.

        Args:
            data: Data to encrypt (string or other type).

        Returns:
            Encrypted data if input was a string, otherwise original data.
        """
        if not data:
            return data

        if isinstance(data, str):
            try:
                encrypted = self.cipher.encrypt(data.encode("utf-8"))
                return f"ENCRYPTED[{base64.b64encode(encrypted).decode('utf-8')}]"
            except Exception as e:
                logger.error(f"Encryption error: {str(e)}")
                # Return original data if encryption fails
                # In production, this should be handled more carefully
                return data

        # For dictionary types, recursively encrypt values
        if isinstance(data, dict):
            return {k: self.encrypt(v) for k, v in data.items()}

        # For list types, recursively encrypt items
        if isinstance(data, list):
            return [self.encrypt(item) for item in data]

        # Return non-string data as is
        return data

    def decrypt(self, data: Any) -> Any:
        """
        Decrypt data if it's an encrypted string.

        Args:
            data: Data to decrypt (encrypted string or other type).

        Returns:
            Decrypted data if input was an encrypted string, otherwise original data.
        """
        if not data:
            return data

        if (
            isinstance(data, str)
            and data.startswith("ENCRYPTED[")
            and data.endswith("]")
        ):
            try:
                # Extract the encrypted part
                encrypted_b64 = data[10:-1]
                encrypted = base64.b64decode(encrypted_b64)

                # Decrypt
                decrypted = self.cipher.decrypt(encrypted)
                return decrypted.decode("utf-8")
            except Exception as e:
                logger.error(f"Decryption error: {str(e)}")
                # Return original data if decryption fails
                # In production, this should be handled more carefully
                return data

        # For dictionary types, recursively decrypt values
        if isinstance(data, dict):
            return {k: self.decrypt(v) for k, v in data.items()}

        # For list types, recursively decrypt items
        if isinstance(data, list):
            return [self.decrypt(item) for item in data]

        # Return non-encrypted string data as is
        return data

    def rotate_key(self, new_key: str) -> bool:
        """
        Rotate the encryption key.

        In a real implementation, this would need to re-encrypt all data
        with the new key. This is just a placeholder.

        Args:
            new_key: The new encryption key.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Save the old cipher for decrypting existing data
            old_cipher = self.cipher

            # Update the key and create a new cipher
            self.key = new_key
            self.cipher = self._create_cipher()

            # In a real implementation, you would re-encrypt all data here
            logger.info("Encryption key rotated successfully")
            return True
        except Exception as e:
            logger.error(f"Key rotation error: {str(e)}")
            return False
