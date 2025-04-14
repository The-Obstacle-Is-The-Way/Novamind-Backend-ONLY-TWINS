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
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Correctly import the necessary components
from app.infrastructure.security.encryption import (
    EncryptionService,
    derive_key,
    encrypt_data,
    decrypt_data,
    hash_data,
    secure_compare,
)
# Assuming Settings might be needed for context, though not directly used here
# from app.core.config.settings import Settings


@pytest.mark.unit()
class TestEncryptionUtils:
    """Tests for the encryption utility functions."""

    def test_derive_key(self):
        """Test key derivation from password and salt."""
        # Test with known inputs
        password = b"test_password"
        salt = b"test_salt_16bytes" # Ensure salt is appropriate length if needed

        # Derive the key
        key = derive_key(password, salt)

        # Verify it's a base64-encoded key suitable for Fernet
        assert isinstance(key, bytes)
        # Base64-encoded keys are 44 bytes (32 bytes encoded to base64)
        assert len(base64.urlsafe_b64decode(key)) == 32

        # Verify deterministic output (same inputs yield same key)
        key2 = derive_key(password, salt)
        assert key == key2

        # Verify different inputs yield different keys
        key3 = derive_key(b"different_password", salt)
        assert key != key3

        key4 = derive_key(password, b"different_salt16b") # Different salt
        assert key != key4

    def test_encrypt_decrypt_data(self):
        """Test encryption and decryption of data."""
        # Test data and key
        data = "Sensitive patient information"
        key = Fernet.generate_key()

        # Encrypt the data
        encrypted = encrypt_data(data, key)

        # Verify encrypted data is different from original and in bytes
        assert encrypted != data.encode() # Compare bytes with encoded string
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
        assert isinstance(hashed, str) # Assuming hash_data returns hex string
        assert isinstance(salt, str)   # Assuming hash_data returns hex string

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
        assert secure_compare("wrong_password", hashed, salt) is False

@pytest.fixture
def encryption_service():
    """Create an EncryptionService instance for testing."""
    # Mock environment variables using a valid Fernet key format
    test_key = Fernet.generate_key().decode() # Generate a valid key for the test
    test_salt = os.urandom(16).hex() # Generate a valid salt
    env_vars = {
        "ENCRYPTION_KEY": test_key,
        "ENCRYPTION_SALT": test_salt,
        "PYTEST_CURRENT_TEST": "True", # Keep if needed by service logic
    }

    # Patch os.environ for the duration of the fixture setup
    with patch.dict(os.environ, env_vars):
        # Patch get_settings if EncryptionService uses it internally
        with patch("app.infrastructure.security.encryption.get_settings", return_value=MagicMock(ENCRYPTION_KEY=test_key, ENCRYPTION_SALT=test_salt)):
             # Ensure the service is initialized within the patched context
             service = EncryptionService()
             # Manually set the cipher if initialization logic depends on env vars directly
             # service.cipher = Fernet(derive_key(test_key.encode(), bytes.fromhex(test_salt)))
             yield service # Yield the service instance

@pytest.mark.unit()
class TestEncryptionService:
    """Tests for the EncryptionService class."""

    def test_initialization(self, encryption_service: EncryptionService):
        """Test initialization of EncryptionService."""
        # Verify the service is initialized
        assert encryption_service is not None
        assert encryption_service.cipher is not None
        assert isinstance(encryption_service.cipher, Fernet) # Check type

    def test_encrypt_decrypt(self, encryption_service: EncryptionService):
        """Test encryption and decryption of data."""
        # Test data
        data = "Sensitive patient information"

        # Encrypt the data
        encrypted = encryption_service.encrypt(data)

        # Verify encrypted data is different from original
        assert encrypted != data
        assert isinstance(encrypted, str) # Assuming encrypt returns string
        assert encrypted.startswith("v1:") # Check for version prefix

        # Decrypt the data
        decrypted = encryption_service.decrypt(encrypted)

        # Verify decrypted data matches original
        assert decrypted == data

    def test_encrypt_decrypt_dict(self, encryption_service: EncryptionService):
        """Test encryption and decryption of dictionaries."""
        # Test data
        data = {
            "patient_id": "12345",
            "name": "John Smith",
            "diagnosis": "F41.1", # Non-sensitive example
            "ssn": "123-45-6789",
            "address": {
                "street": "123 Main St",
                "city": "Anytown", # Non-sensitive example
                "state": "CA",     # Non-sensitive example
                "zip": "12345",    # Non-sensitive example
            },
            "medications": [ # Example of list handling
                {"name": "Med1", "dosage": "10mg"},
                {"name": "Med2", "dosage": "20mg"},
            ],
            "notes": None, # Test None value
            "age": 42 # Test integer value
        }

        # Encrypt the data (assuming encrypt_dict handles structure)
        encrypted = encryption_service.encrypt_dict(data)

        # Verify sensitive fields are encrypted (check format)
        assert isinstance(encrypted["patient_id"], str) and encrypted["patient_id"].startswith("v1:")
        assert isinstance(encrypted["name"], str) and encrypted["name"].startswith("v1:")
        assert isinstance(encrypted["ssn"], str) and encrypted["ssn"].startswith("v1:")
        assert isinstance(encrypted["address"], dict) # Address itself isn't encrypted, only fields within
        assert isinstance(encrypted["address"]["street"], str) and encrypted["address"]["street"].startswith("v1:")
        # Non-sensitive fields should remain unchanged
        assert encrypted["diagnosis"] == data["diagnosis"]
        assert encrypted["address"]["city"] == data["address"]["city"]
        assert encrypted["age"] == data["age"]
        assert encrypted["notes"] is None # None values should be preserved

        # Verify list structure and encrypted content within lists
        assert isinstance(encrypted["medications"], list)
        assert len(encrypted["medications"]) == 2
        assert isinstance(encrypted["medications"][0], dict)
        assert isinstance(encrypted["medications"][0]["name"], str) and encrypted["medications"][0]["name"].startswith("v1:")
        assert isinstance(encrypted["medications"][0]["dosage"], str) and encrypted["medications"][0]["dosage"].startswith("v1:")


        # Decrypt the data
        decrypted = encryption_service.decrypt_dict(encrypted)

        # Verify decrypted data matches original (deep comparison might be needed)
        assert decrypted == data # Simple comparison works if structure and values match


    def test_key_rotation(self):
        """Test encryption key rotation."""
        # Initialize with original key
        original_key = Fernet.generate_key()
        original_salt = os.urandom(16)
        env_vars_orig = {
            "ENCRYPTION_KEY": original_key.decode(),
            "ENCRYPTION_SALT": original_salt.hex(),
            "PYTEST_CURRENT_TEST": "True",
        }

        with patch.dict(os.environ, env_vars_orig):
             with patch("app.infrastructure.security.encryption.get_settings", return_value=MagicMock(ENCRYPTION_KEY=original_key.decode(), ENCRYPTION_SALT=original_salt.hex())):
                service_orig = EncryptionService()

        # Encrypt data with original key
        data = "Sensitive patient information"
        encrypted_v1 = service_orig.encrypt(data)
        assert encrypted_v1.startswith("v1:")

        # Rotate the key
        new_key = Fernet.generate_key()
        env_vars_new = {
            "PREVIOUS_ENCRYPTION_KEY": original_key.decode(), # Provide previous key
            "ENCRYPTION_KEY": new_key.decode(),
            "ENCRYPTION_SALT": original_salt.hex(), # Salt might stay the same or change
            "PYTEST_CURRENT_TEST": "True",
        }

        with patch.dict(os.environ, env_vars_new):
            with patch("app.infrastructure.security.encryption.get_settings", return_value=MagicMock(ENCRYPTION_KEY=new_key.decode(), PREVIOUS_ENCRYPTION_KEY=original_key.decode(), ENCRYPTION_SALT=original_salt.hex())):
                service_new = EncryptionService()

            # Should be able to decrypt data encrypted with the *previous* key
            decrypted_from_v1 = service_new.decrypt(encrypted_v1)
            assert decrypted_from_v1 == data

            # Encrypt with new key
            encrypted_v2 = service_new.encrypt(data)
            assert encrypted_v2.startswith("v1:") # Prefix might stay the same
            assert encrypted_v2 != encrypted_v1 # Ciphertext should differ

            # Verify can decrypt with new service (using the new key)
            assert service_new.decrypt(encrypted_v2) == data

            # Verify original service CANNOT decrypt data encrypted with the new key
            with pytest.raises(InvalidToken): # Or appropriate exception
                 service_orig.decrypt(encrypted_v2)


    def test_file_encryption(self, encryption_service: EncryptionService, tmp_path):
        """Test encryption and decryption of files."""
        # Create test file paths
        test_file = tmp_path / "test.txt"
        encrypted_file = tmp_path / "encrypted.bin"
        decrypted_file = tmp_path / "decrypted.txt"

        # Test content
        test_content = "Sensitive patient information\nLine 2\nLine3"
        test_file.write_text(test_content)

        # Encrypt the file
        encryption_service.encrypt_file(str(test_file), str(encrypted_file))

        # Verify encrypted file exists and content is different
        assert encrypted_file.exists()
        encrypted_content_bytes = encrypted_file.read_bytes()
        assert encrypted_content_bytes != test_content.encode()

        # Decrypt the file
        encryption_service.decrypt_file(str(encrypted_file), str(decrypted_file))

        # Verify decrypted file exists and content matches original
        assert decrypted_file.exists()
        decrypted_content = decrypted_file.read_text()
        assert decrypted_content == test_content


    def test_encrypt_file_nonexistent(self, encryption_service: EncryptionService, tmp_path):
        """Test encryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.bin"

        # Attempt to encrypt nonexistent file
        with pytest.raises(FileNotFoundError):
            encryption_service.encrypt_file(str(nonexistent_file), str(output_file))

    def test_decrypt_file_nonexistent(self, encryption_service: EncryptionService, tmp_path):
        """Test decryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.bin"
        output_file = tmp_path / "output.txt"

        # Attempt to decrypt nonexistent file
        with pytest.raises(FileNotFoundError):
            encryption_service.decrypt_file(str(nonexistent_file), str(output_file))

    def test_decrypt_invalid_file_content(self, encryption_service: EncryptionService, tmp_path):
        """Test decryption of a file with invalid encrypted content."""
        invalid_encrypted_file = tmp_path / "invalid.bin"
        output_file = tmp_path / "output.txt"

        # Write invalid data to the file
        invalid_encrypted_file.write_bytes(b"this is not valid fernet data")

        # Attempt to decrypt the invalid file
        with pytest.raises(InvalidToken): # Fernet raises InvalidToken
            encryption_service.decrypt_file(str(invalid_encrypted_file), str(output_file))
