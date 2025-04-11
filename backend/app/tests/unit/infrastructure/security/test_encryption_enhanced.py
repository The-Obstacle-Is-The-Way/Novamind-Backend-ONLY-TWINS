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
    secure_compare
)
from app.core.config import Settings


@pytest.mark.db_required
class TestEncryptionUtils:
    """Tests for the encryption utility functions."""
    
    def test_derive_key(self):
        """Test key derivation from password and salt."""
        # Test with known inputs
        password = b"test_password"
        salt = b"test_salt"
        
        # Derive the key
        key = derive_key(password, salt)
        
        # Verify it's a 32-byte base64 encoded string
        assert isinstance(key, bytes)
        assert len(key) == 32  # 256 bits = 32 bytes
        
        # Verify deterministic output (same inputs yield same key)
        key2 = derive_key(password, salt)
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
        
        # Verify decryption recovers the original data
        assert decrypted == data
    
    def test_encrypt_decrypt_with_wrong_key(self):
        """Test decryption with wrong key fails."""
        # Test data and keys
        data = "Sensitive patient information"
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        
        # Encrypt with key1
        encrypted = encrypt_data(data, key1)
        
        # Attempt to decrypt with key2 should fail
        with pytest.raises(Exception):
            decrypt_data(encrypted, key2)
    
    def test_hash_data(self):
        """Test hashing of data."""
        # Test with known input
        data = "Sensitive patient information"
        
        # Hash the data
        hashed = hash_data(data)
        
        # Verify it's a string and starts with expected algorithm prefix
        assert isinstance(hashed, str)
        assert hashed.startswith("scrypt$")
        
        # Verify hashing with same input produces different output (due to salt)
        hashed2 = hash_data(data)
        assert hashed != hashed2  # Different due to random salt
        
        # Verify secure_compare can validate the hash
        assert secure_compare(data, hashed)
        assert not secure_compare("wrong data", hashed)
    
    def test_secure_compare(self):
        """Test secure comparison of plain text against hash."""
        # Test data
        data = "Sensitive patient information"
        wrong_data = "Wrong information"
        
        # Hash the data
        hashed = hash_data(data)
        
        # Verify correct data matches
        assert secure_compare(data, hashed)
        
        # Verify incorrect data doesn't match
        assert not secure_compare(wrong_data, hashed)
        
        # Test with invalid hash format
        with pytest.raises(ValueError):
            secure_compare(data, "invalid_hash_format")
        
        # Test with unsupported algorithm
        unsupported_hash = "unknown$salt$hash"
        with pytest.raises(ValueError):
            secure_compare(data, unsupported_hash)


class TestEncryptionService:
    """Tests for the EncryptionService class."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create a mock settings object."""
        with patch('app.infrastructure.security.encryption.settings') as mock_settings:
            # Configure default settings
            mock_settings.security.ENCRYPTION_KEY = Fernet.generate_key().decode()
            mock_settings.security.KDF_SALT = base64.b64encode(os.urandom(16)).decode()
            mock_settings.security.HASH_PEPPER = "test_pepper"
            yield mock_settings
    
    @pytest.fixture
    def encryption_service(self, mock_settings):
        """Create an EncryptionService instance with mocked settings."""
        return EncryptionService()
    
    def test_initialization(self, encryption_service, mock_settings):
        """Test encryption service initialization with settings."""
        # Verify key is initialized correctly
        assert encryption_service.key is not None
        assert isinstance(encryption_service.key, bytes)
        
        # Verify cipher suite is initialized
        assert encryption_service.cipher_suite is not None
        assert isinstance(encryption_service.cipher_suite, Fernet)
        
        # Verify pepper is initialized
        assert encryption_service.pepper is not None
        assert encryption_service.pepper == mock_settings.security.HASH_PEPPER
    
    def test_encrypt_decrypt(self, encryption_service):
        """Test encryption and decryption with the service."""
        # Test data
        data = "Sensitive patient information"
        
        # Encrypt the data
        encrypted = encryption_service.encrypt(data)
        
        # Verify encrypted data is different and in bytes
        assert encrypted != data
        assert isinstance(encrypted, bytes)
        
        # Decrypt the data
        decrypted = encryption_service.decrypt(encrypted)
        
        # Verify decryption recovers the original data
        assert decrypted == data
    
    def test_encrypt_decrypt_with_metadata(self, encryption_service):
        """Test encryption and decryption with metadata."""
        # Test data with metadata
        data = "Sensitive patient information"
        metadata = {"patient_id": "123", "record_type": "medical"}
        
        # Encrypt with metadata
        encrypted = encryption_service.encrypt(data, metadata)
        
        # Verify encrypted data is in bytes
        assert isinstance(encrypted, bytes)
        
        # Decrypt and verify both data and metadata
        decrypted, retrieved_metadata = encryption_service.decrypt(encrypted, return_metadata=True)
        
        # Verify decryption recovers original data and metadata
        assert decrypted == data
        assert retrieved_metadata["patient_id"] == "123"
        assert retrieved_metadata["record_type"] == "medical"
    
    def test_hash_password(self, encryption_service):
        """Test password hashing."""
        # Test password
        password = "SecurePassword123!"
        
        # Hash the password
        hashed = encryption_service.hash_password(password)
        
        # Verify it's a string and has expected format
        assert isinstance(hashed, str)
        assert hashed.startswith("scrypt$")
        
        # Verify hashing with same password produces different output (due to salt)
        hashed2 = encryption_service.hash_password(password)
        assert hashed != hashed2
        
        # Verify password verification works
        assert encryption_service.verify_password(password, hashed)
        assert not encryption_service.verify_password("WrongPassword", hashed)
    
    def test_pepper_text(self, encryption_service):
        """Test text peppering."""
        # Test text
        text = "Text to be peppered"
        
        # Pepper the text
        peppered = encryption_service._pepper_text(text)
        
        # Verify peppered text is different from original
        assert peppered != text
        
        # Verify deterministic output with same text and pepper
        peppered2 = encryption_service._pepper_text(text)
        assert peppered == peppered2
        
        # Verify different text yields different peppered result
        assert encryption_service._pepper_text("Different text") != peppered
    
    def test_encrypt_decrypt_phi(self, encryption_service):
        """Test PHI-specific encryption and decryption."""
        # Test PHI data
        phi_data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "dob": "1980-01-01"
        }
        
        # Encrypt PHI
        encrypted_phi = encryption_service.encrypt_phi(phi_data)
        
        # Verify encrypted PHI is in bytes
        assert isinstance(encrypted_phi, bytes)
        
        # Decrypt PHI
        decrypted_phi = encryption_service.decrypt_phi(encrypted_phi)
        
        # Verify decryption recovers original PHI
        assert decrypted_phi == phi_data
    
    def test_encrypt_file_decrypt_file(self, encryption_service, tmp_path):
        """Test file encryption and decryption."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = "Sensitive file content"
        test_file.write_text(test_content)
        
        # Create output files
        encrypted_file = tmp_path / "encrypted.bin"
        decrypted_file = tmp_path / "decrypted.txt"
        
        # Encrypt the file
        with patch('builtins.open', mock_open(read_data=test_content)):
            with patch('app.infrastructure.security.encryption.os.path.exists', return_value=True):
                encryption_service.encrypt_file(str(test_file), str(encrypted_file))
        
        # Mock the encrypted content
        mock_encrypted = encryption_service.encrypt(test_content)
        
        # Decrypt the file
        with patch('builtins.open', mock_open(read_data=mock_encrypted)):
            with patch('app.infrastructure.security.encryption.os.path.exists', return_value=True):
                encryption_service.decrypt_file(str(encrypted_file), str(decrypted_file))
        
        # Verify the content was encrypted and decrypted correctly
        with patch('builtins.open', mock_open(read_data=test_content)):
            with open(str(decrypted_file), 'r') as f:
                assert f.read() == test_content
    
    def test_encrypt_file_nonexistent(self, encryption_service, tmp_path):
        """Test encryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.bin"
        
        # Attempt to encrypt nonexistent file
        with patch('app.infrastructure.security.encryption.os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                encryption_service.encrypt_file(str(nonexistent_file), str(output_file))
    
    def test_decrypt_file_nonexistent(self, encryption_service, tmp_path):
        """Test decryption of nonexistent file."""
        # Nonexistent input file
        nonexistent_file = tmp_path / "nonexistent.bin"
        output_file = tmp_path / "output.txt"
        
        # Attempt to decrypt nonexistent file
        with patch('app.infrastructure.security.encryption.os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                encryption_service.decrypt_file(str(nonexistent_file), str(output_file))