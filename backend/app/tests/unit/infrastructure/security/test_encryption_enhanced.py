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
import json
from typing import Dict, Any, Optional

# Correctly import the necessary components
from app.infrastructure.security.encryption.base_encryption_service import BaseEncryptionService
# Assuming Settings might be needed for context, though not directly used here
# from app.core.config.settings import Settings

# Define constants for testing
TEST_KEY_MATERIAL = "test-key-material-needs-32-bytes!"
TEST_SALT = b'test-salt-16-bytes'
TEST_DATA = "This is sensitive test data."

@pytest.mark.unit()
class TestEncryptionUtils:
    """Tests for the encryption utility functions."""

    # TODO: Refactor tests for derive_key as the function is not public.
    #       Test the behavior of _get_key() indirectly via service initialization.
    # @pytest.mark.parametrize(
    #     "password, salt, expected_key_length",
    #     [
    #         ("testpassword", TEST_SALT, 32),
    #         ("another-secure-password-123", os.urandom(16), 32),
    #     ]
    # )
    # def test_derive_key(password, salt, expected_key_length):
    #     """Test key derivation produces a key of the correct length."""
    #     derived = derive_key(password.encode(), salt)
    #     assert isinstance(derived, bytes)
    #     assert len(base64.urlsafe_b64decode(derived)) == expected_key_length

    # def test_derive_key_with_invalid_input():
    #     """Test key derivation with invalid input types."""
    #     with pytest.raises(TypeError):
    #         derive_key(12345, TEST_SALT) # Non-bytes password
    #     with pytest.raises(TypeError):
    #         derive_key(b"password", "not_bytes_salt") # Non-bytes salt

    # def test_derive_key_determinism():
    #     """Test that key derivation is deterministic."""
    #     key1 = derive_key(b"password", TEST_SALT)
    #     key2 = derive_key(b"password", TEST_SALT)
    #     assert key1 == key2

    def test_encrypt_decrypt_cycle(self, encryption_service):
        """Test that encrypting and then decrypting returns the original data."""
        encrypted = encryption_service.encrypt(TEST_DATA) # Use service method
        assert encrypted != TEST_DATA
        assert isinstance(encrypted, str)
        assert encrypted.startswith(BaseEncryptionService.VERSION_PREFIX)

        decrypted = encryption_service.decrypt(encrypted) # Use service method
        assert decrypted == TEST_DATA

    def test_decrypt_invalid_token(self, encryption_service):
        """Test decryption with an invalid token raises InvalidToken."""
        invalid_encrypted_data = "v1:this-is-not-valid-base64-or-fernet-token"
        with pytest.raises(InvalidToken):
            encryption_service.decrypt(invalid_encrypted_data) # Use service method

    # TODO: Locate or reimplement hash_data and secure_compare functionality.
    #       These tests are currently commented out.
    # def test_hash_data_consistency():
    #     """Test that hashing the same data yields the same hash."""
    #     hash1 = hash_data(TEST_DATA)
    #     hash2 = hash_data(TEST_DATA)
    #     assert hash1 == hash2
    #     assert isinstance(hash1, str)

    # def test_hash_data_uniqueness():
    #     """Test that hashing different data yields different hashes."""
    #     hash1 = hash_data(TEST_DATA)
    #     hash2 = hash_data("Slightly different test data.")
    #     assert hash1 != hash2

    # def test_secure_compare_matching():
    #     """Test secure comparison with matching values."""
    #     value = "some_secret_value"
    #     hashed_value = hash_data(value)
    #     assert secure_compare(value, hashed_value)

    # def test_secure_compare_non_matching():
    #     """Test secure comparison with non-matching values."""
    #     value = "some_secret_value"
    #     hashed_value = hash_data("different_value")
    #     assert not secure_compare(value, hashed_value)

@pytest.fixture(scope="module")
def encryption_service() -> BaseEncryptionService:
    """Provide a BaseEncryptionService instance with default test keys."""
    # Use sufficiently long keys for testing
    test_key = "test_encryption_key_longer_than_32_chars"
    test_prev_key = "previous_test_key_also_longer_than_32"
    return BaseEncryptionService(direct_key=test_key, previous_key=test_prev_key)

@pytest.mark.unit()
class TestEnhancedEncryptionService:
    """Tests for the EncryptionService class."""

    def test_initialization(self, encryption_service: BaseEncryptionService):
        """Test initialization of EncryptionService."""
        # Verify the service is initialized
        assert encryption_service is not None
        assert encryption_service.cipher is not None
        assert isinstance(encryption_service.cipher, Fernet) # Check type

    def test_encrypt_decrypt(self, encryption_service: BaseEncryptionService):
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

    def test_encrypt_decrypt_dict(self, encryption_service: BaseEncryptionService):
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
                service_orig = BaseEncryptionService()

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
                service_new = BaseEncryptionService()

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


    def test_file_encryption(self, encryption_service: BaseEncryptionService, tmp_path):
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


    def test_encrypt_file_nonexistent(self, encryption_service: BaseEncryptionService, tmp_path):
        """Test encryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.bin"

        # Attempt to encrypt nonexistent file
        with pytest.raises(FileNotFoundError):
            encryption_service.encrypt_file(str(nonexistent_file), str(output_file))

    def test_decrypt_file_nonexistent(self, encryption_service: BaseEncryptionService, tmp_path):
        """Test decryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.bin"
        output_file = tmp_path / "output.txt"

        # Attempt to decrypt nonexistent file
        with pytest.raises(FileNotFoundError):
            encryption_service.decrypt_file(str(nonexistent_file), str(output_file))

    def test_decrypt_invalid_file_content(self, encryption_service: BaseEncryptionService, tmp_path):
        """Test decryption of a file with invalid encrypted content."""
        invalid_encrypted_file = tmp_path / "invalid.bin"
        output_file = tmp_path / "output.txt"

        # Write invalid data to the file
        invalid_encrypted_file.write_bytes(b"this is not valid fernet data")

        # Attempt to decrypt the invalid file
        with pytest.raises(InvalidToken): # Fernet raises InvalidToken
            encryption_service.decrypt_file(str(invalid_encrypted_file), str(output_file))
