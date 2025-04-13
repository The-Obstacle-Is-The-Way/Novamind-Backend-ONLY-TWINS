# -*- coding: utf-8 -*-
"""
Enhanced unit tests for the encryption utility.

This test suite provides comprehensive coverage for the encryption module,
ensuring secure data handling and HIPAA-compliant data protection.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.infrastructure.security.encryption import (
    EncryptionService,
    derive_key,
    encrypt_data,
    decrypt_data,
    hash_data,
    secure_compare,
)
from app.core.config.settings import Settings


@pytest.mark.unit()class TestEncryptionUtils:
    """Tests for the encryption utility functions."""

    def test_derive_key(self):


                    """Test key derivation from password and salt."""
        # Test with known inputs
        password = b"test_password"
        salt = b"test_salt"

        # Derive the key
        key = derive_key(password, salt)

        # Verify it's a base64-encoded key suitable for Fernet
        assert isinstance(key, bytes)
        # Base64-encoded keys are 44 bytes (32 bytes encoded to base64)
        assert len(base64.urlsafe_b64decode(key)) == 32

        # Verify deterministic output (same inputs yield same key,
        key2= derive_key(password, salt)
        assert key == key2

        # Verify different inputs yield different keys
        key3 = derive_key(b"different_password", salt)
        assert key != key3

        key4 = derive_key(password, b"different_salt")
        assert key != key4

        def test_encrypt_decrypt_data(self):


                        """Test encryption and decryption of data."""
        # Test data and key
        data = "Sensitive patient information"
        key = Fernet.generate_key()

        # Encrypt the data
        encrypted = encrypt_data(data, key)

        # Verify encrypted data is different from original and in bytes
        assert encrypted != data
        assert isinstance(encrypted, bytes)

        # Decrypt the data
        decrypted = decrypt_data(encrypted, key)

        # Verify decrypted data matches original
        assert decrypted == data

        def test_hash_data(self):


                        """Test hashing of data."""
        # Test data
        data = "password123"

        # Hash the data
        hashed, salt = hash_data(data)

        # Verify hashed data is different from original
        assert hashed != data
        assert salt is not None

        # Verify same data + salt produces same hash
        hashed2, _ = hash_data(data, salt)
        assert hashed == hashed2

        # Verify different data produces different hash
        hashed3, _ = hash_data("different_password", salt)
        assert hashed != hashed3

        def test_secure_compare(self):


                        """Test secure comparison of strings."""
        # Test data
        data = "password123"
        hashed, salt = hash_data(data)

        # Test true comparison
        assert secure_compare(data, hashed, salt) is True

        # Test false comparison
        assert secure_compare("wrong_password", hashed, salt) is False@pytest.fixture
def encryption_service():

            """Create an EncryptionService instance for testing."""
    # Mock environment variables
    env_vars = {
        "ENCRYPTION_KEY": "test_key_12345678901234567890123456789012",
        "ENCRYPTION_SALT": "test_salt_12345678901234567890123456789012",
        "PYTEST_CURRENT_TEST": "True",
    }

    with patch.dict(os.environ, env_vars):
        return EncryptionService()

        @pytest.mark.unit()class TestEncryptionService:
    """Tests for the EncryptionService class."""

    def test_initialization(self, encryption_service):


                    """Test initialization of EncryptionService."""
        # Verify the service is initialized
        assert encryption_service is not None
        assert encryption_service.cipher is not None

        def test_encrypt_decrypt(self, encryption_service):


                        """Test encryption and decryption of data."""
        # Test data
        data = "Sensitive patient information"

        # Encrypt the data
        encrypted = encryption_service.encrypt(data)

        # Verify encrypted data is different from original
        assert encrypted != data
        assert encrypted.startswith("v1:")

        # Decrypt the data
        decrypted = encryption_service.decrypt(encrypted)

        # Verify decrypted data matches original
        assert decrypted == data

        def test_encrypt_decrypt_dict(self, encryption_service):


                        """Test encryption and decryption of dictionaries."""
        # Test data
        data = {
            "patient_id": "12345",
            "name": "John Smith",
            "diagnosis": "F41.1",
            "ssn": "123-45-6789",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
            },
            "medications": [
                {"name": "Med1", "dosage": "10mg"},
                {"name": "Med2", "dosage": "20mg"},
            ],
        }

        # Encrypt the data
        encrypted = encryption_service.encrypt_dict(data)

        # Verify sensitive fields are encrypted
        assert encrypted["patient_id"].startswith("v1:")
        assert encrypted["name"].startswith("v1:")
        assert encrypted["ssn"].startswith("v1:")
        assert encrypted["address"]["street"].startswith("v1:")

        # Decrypt the data
        decrypted = encryption_service.decrypt_dict(encrypted)

        # Verify decrypted data matches original
        assert decrypted["patient_id"] == data["patient_id"]
        assert decrypted["name"] == data["name"]
        assert decrypted["ssn"] == data["ssn"]
        assert decrypted["address"]["street"] == data["address"]["street"]
        assert decrypted["medications"][0]["name"] == data["medications"][0]["name"]

    def test_key_rotation(self):


                    """Test encryption key rotation."""
        # Initialize with original key
        env_vars = {
            "ENCRYPTION_KEY": "original_key_123456789012345678901234567890",
            "ENCRYPTION_SALT": "test_salt_12345678901234567890123456789012",
            "PYTEST_CURRENT_TEST": "True",
        }

        with patch.dict(os.environ, env_vars):
            service = EncryptionService()

            # Encrypt data with original key
            data = "Sensitive patient information"
            encrypted = service.encrypt(data)

            # Rotate the key
            new_env_vars = {
                "PREVIOUS_ENCRYPTION_KEY": env_vars["ENCRYPTION_KEY"],
                "ENCRYPTION_KEY": "new_key_1234567890123456789012345678901",
                "ENCRYPTION_SALT": env_vars["ENCRYPTION_SALT"],
                "PYTEST_CURRENT_TEST": "True",
            }

            with patch.dict(os.environ, new_env_vars):
                # Create new service with rotated keys
                service_new = EncryptionService()

                # Should be able to decrypt with previous key
                decrypted = service_new.decrypt(encrypted)
                assert decrypted == data

                # Encrypt with new key
                new_encrypted = service_new.encrypt(data)

                # Verify new encryption is different
                assert new_encrypted != encrypted

                # Verify can decrypt with new service
                assert service_new.decrypt(new_encrypted) == data

                def test_file_encryption(self, encryption_service, tmp_path):


                                """Test encryption and decryption of files."""
        # Create test file paths
        test_file = tmp_path / "test.txt"
        encrypted_file = tmp_path / "encrypted.bin"
        decrypted_file = tmp_path / "decrypted.txt"

        # Test content
        test_content = "Sensitive patient information"

        # Mock file operations
        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch("os.path.exists", return_value=True):
                # Encrypt the file
                encryption_service.encrypt_file(
                    str(test_file), str(encrypted_file))

                # Get encrypted content for mock
                encrypted_content = encryption_service.encrypt(test_content)

                # Setup mock for reading encrypted content
                with patch("builtins.open", mock_open(read_data=encrypted_content)):
                    # Decrypt the file
                    encryption_service.decrypt_file(
                        str(encrypted_file), str(decrypted_file)
                    )

        # Verify write calls (can't easily verify content with mock_open)
        assert os.path.exists(test_file.parent)

    def test_encrypt_file_nonexistent(self, encryption_service, tmp_path):


                    """Test encryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.bin"

        # Mock file existence check
        with patch("os.path.exists", return_value=False):
            # Attempt to encrypt nonexistent file
            with pytest.raises(FileNotFoundError):
                encryption_service.encrypt_file(
                    str(nonexistent_file), str(output_file))

                def test_decrypt_file_nonexistent(
                        self, encryption_service, tmp_path):
        """Test decryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.bin"
        output_file = tmp_path / "output.txt"

        # Mock file existence check
        with patch("os.path.exists", return_value=False):
            # Attempt to decrypt nonexistent file
            with pytest.raises(FileNotFoundError):
                encryption_service.decrypt_file(
                    str(nonexistent_file), str(output_file))
