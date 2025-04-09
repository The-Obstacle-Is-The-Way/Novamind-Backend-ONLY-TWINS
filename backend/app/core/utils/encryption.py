# -*- coding: utf-8 -*-
"""
NOVAMIND Encryption Utility
==========================
Provides secure encryption for sensitive data in the NOVAMIND platform.
Implements HIPAA-compliant encryption for PHI with proper key management.
"""

import base64
import hashlib
import hmac
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings


class EncryptionService:
    """
    HIPAA-compliant encryption service for securing sensitive data.
    Provides methods for encrypting/decrypting strings and dictionaries.
    """

    def __init__(self, secret_key: Optional[str] = None, salt: Optional[bytes] = None):
        """
        Initialize the encryption service with a secret key and salt.

        Args:
            secret_key: Secret key for encryption (defaults to environment variable)
            salt: Salt for key derivation (generates random salt if None)
        """
        self.secret_key = secret_key or os.getenv("ENCRYPTION_KEY", "")
        if not self.secret_key:
            raise ValueError("Encryption key not provided and not found in environment")

        # Generate or use provided salt
        self.salt = salt or os.urandom(16)

        # Generate encryption key from secret key and salt
        self.key = self._derive_key(self.secret_key.encode(), self.salt)

        # Create Fernet cipher
        self.cipher = Fernet(self.key)

    def _derive_key(self, secret_key: bytes, salt: bytes) -> bytes:
        """
        Derive encryption key from secret key and salt using PBKDF2.

        Args:
            secret_key: Secret key bytes
            salt: Salt bytes

        Returns:
            Derived key bytes suitable for Fernet
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        derived_key = kdf.derive(secret_key)
        return base64.urlsafe_b64encode(derived_key)

    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a string using Fernet symmetric encryption.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        # Encrypt the plaintext
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())

        # Return base64-encoded encrypted bytes
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt_string(self, encrypted_text: str) -> str:
        """
        Decrypt a previously encrypted string.

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails
        """
        if not encrypted_text:
            return ""

        try:
            # Decode base64 and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text)
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)

            # Return decrypted string
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt string: {str(e)}")

    def encrypt_dict(
        self, data: Dict[str, Any], sensitive_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a dictionary.

        Args:
            data: Dictionary containing data to encrypt
            sensitive_fields: List of field names to encrypt (encrypts all string values if None)

        Returns:
            Dictionary with sensitive fields encrypted
        """
        if not data:
            return {}

        encrypted_data = {}

        for key, value in data.items():
            # Determine if this field should be encrypted
            should_encrypt = sensitive_fields is None or key in (sensitive_fields or [])

            if should_encrypt and isinstance(value, str):
                # Encrypt string values
                encrypted_data[key] = self.encrypt_string(value)
            elif isinstance(value, dict):
                # Recursively encrypt nested dictionaries
                encrypted_data[key] = self.encrypt_dict(value, sensitive_fields)
            elif isinstance(value, list):
                # Handle lists - encrypt dictionaries in lists
                encrypted_data[key] = [
                    (
                        self.encrypt_dict(item, sensitive_fields)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                # Keep other values as is
                encrypted_data[key] = value

        return encrypted_data

    def decrypt_dict(
        self, data: Dict[str, Any], encrypted_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Decrypt encrypted fields in a dictionary.

        Args:
            data: Dictionary containing encrypted data
            encrypted_fields: List of field names to decrypt (attempts to decrypt all string values if None)

        Returns:
            Dictionary with fields decrypted
        """
        if not data:
            return {}

        decrypted_data = {}

        for key, value in data.items():
            # Determine if this field should be decrypted
            should_decrypt = encrypted_fields is None or key in (encrypted_fields or [])

            if should_decrypt and isinstance(value, str):
                try:
                    # Attempt to decrypt string values
                    decrypted_data[key] = self.decrypt_string(value)
                except:
                    # If decryption fails, keep the original value
                    decrypted_data[key] = value
            elif isinstance(value, dict):
                # Recursively decrypt nested dictionaries
                decrypted_data[key] = self.decrypt_dict(value, encrypted_fields)
            elif isinstance(value, list):
                # Handle lists - decrypt dictionaries in lists
                decrypted_data[key] = [
                    (
                        self.decrypt_dict(item, encrypted_fields)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                # Keep other values as is
                decrypted_data[key] = value

        return decrypted_data

    def generate_hash(
        self, data: str, salt: Optional[bytes] = None
    ) -> Tuple[str, bytes]:
        """
        Generate a secure hash of data with salt.

        Args:
            data: String data to hash
            salt: Optional salt (generates random salt if None)

        Returns:
            Tuple of (hash_hex_string, salt_bytes)
        """
        # Generate or use provided salt
        salt_bytes = salt or os.urandom(16)

        # Create hash
        hash_obj = hashlib.sha256()
        hash_obj.update(salt_bytes)
        hash_obj.update(data.encode())

        return hash_obj.hexdigest(), salt_bytes

    def verify_hash(self, data: str, hash_value: str, salt: bytes) -> bool:
        """
        Verify that data matches a previously generated hash.

        Args:
            data: String data to verify
            hash_value: Expected hash value (hex string)
            salt: Salt bytes used for the original hash

        Returns:
            True if hash matches, False otherwise
        """
        # Generate hash with the same salt
        calculated_hash, _ = self.generate_hash(data, salt)

        # Compare hashes (constant-time comparison)
        return hmac.compare_digest(calculated_hash, hash_value)

    def generate_hmac(self, data: str) -> str:
        """
        Generate HMAC for data integrity verification.

        Args:
            data: String data to generate HMAC for

        Returns:
            Hex string HMAC
        """
        h = hmac.new(self.secret_key.encode(), data.encode(), hashlib.sha256)
        return h.hexdigest()

    def verify_hmac(self, data: str, hmac_value: str) -> bool:
        """
        Verify HMAC for data integrity.

        Args:
            data: String data to verify
            hmac_value: Expected HMAC value

        Returns:
            True if HMAC matches, False otherwise
        """
        calculated_hmac = self.generate_hmac(data)
        return hmac.compare_digest(calculated_hmac, hmac_value)


# Create a default encryption service
default_encryption_service = EncryptionService()
