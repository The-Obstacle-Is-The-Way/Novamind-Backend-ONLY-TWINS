# -*- coding: utf-8 -*-
"""Unit tests for Encryption Service functionality.

This module tests the encryption service which secures Protected Health Information (PHI) 
at rest, a critical requirement for HIPAA compliance.
"""

import pytest
import os
import json
import base64
from unittest.mock import patch, MagicMock

from app.infrastructure.security.encryption_service import (
    EncryptionService,
    EncryptionConfig,
    EncryptionAlgorithm,
    KeyManagementService,
    SymmetricEncryption,
    AsymmetricEncryption,
    HashingService,
    EncryptionError,
    DecryptionError,
    InvalidKeyError,
    TamperingDetectedError
)


@pytest.fixture
def encryption_config():
    """Create an encryption service configuration for testing."""
    return EncryptionConfig(
        algorithm=EncryptionAlgorithm.AES_256_GCM,
        key_source="local",
        key_rotation_days=90,
        enable_key_versioning=True,
        key_identifier_prefix="novamind",
        enable_at_rest_encryption=True,
        enable_in_memory_protection=True,
        hash_algorithm="argon2id",
        hash_memory_cost=65536,
        hash_time_cost=3,
        hash_parallelism=4,
        min_key_length=32,
        aad_context="novamind-phi-context",
        iv_length=12
    )


@pytest.fixture
def mock_kms():
    """Create a mock key management service."""
    mock_service = MagicMock(spec=KeyManagementService)
    
    # Mock key generation
    mock_service.generate_data_key.return_value = {
        "key_id": "test-key-001",
        "key_version": 1,
        "key": os.urandom(32),  # 32 bytes = 256 bits
        "created_at": "2025-03-27T12:00:00Z"
    }
    
    # Mock key retrieval
    mock_service.get_key.return_value = {
        "key_id": "test-key-001",
        "key_version": 1,
        "key": os.urandom(32),
        "created_at": "2025-03-27T12:00:00Z"
    }
    
    # Mock listing keys
    mock_service.list_keys.return_value = [
        {"key_id": "test-key-001", "key_version": 1, "created_at": "2025-03-27T12:00:00Z"},
        {"key_id": "test-key-001", "key_version": 2, "created_at": "2025-03-27T13:00:00Z"}
    ]
    
    return mock_service


@pytest.fixture
def encryption_service(encryption_config, mock_kms):
    """Create an encryption service for testing."""
    service = EncryptionService(config=encryption_config)
    service.key_service = mock_kms
    return service


class TestEncryptionService:
    """Test suite for the encryption service."""
    
    def test_encrypt_decrypt_text(self, encryption_service):
        """Test encryption and decryption of text data."""
        # Sample PHI
        sensitive_data = "Patient John Smith (SSN: 123-45-6789) diagnosed with F41.1"
        
        # Encrypt the data
        encrypted_result = encryption_service.encrypt(sensitive_data)
        
        # Verify encrypted result format
        assert "ciphertext" in encrypted_result
        assert "key_id" in encrypted_result
        assert "key_version" in encrypted_result
        assert "iv" in encrypted_result
        assert "tag" in encrypted_result
        
        # Verify ciphertext is not the original plaintext
        assert base64.b64decode(encrypted_result["ciphertext"]) != sensitive_data.encode()
        
        # Decrypt the data
        decrypted_data = encryption_service.decrypt(encrypted_result)
        
        # Verify decryption restores the original plaintext
        assert decrypted_data == sensitive_data
    
    def test_encrypt_decrypt_dict(self, encryption_service):
        """Test encryption and decryption of dictionary data."""
        # Sample PHI in dictionary format
        sensitive_dict = {
            "patient_id": "PT12345",
            "name": "John Smith",
            "ssn": "123-45-6789",
            "diagnosis": "F41.1",
            "contact": {
                "email": "john.smith@example.com",
                "phone": "(555) 123-4567"
            }
        }
        
        # Encrypt the dictionary
        encrypted_result = encryption_service.encrypt_dict(sensitive_dict)
        
        # Verify encrypted result format
        assert "encrypted_data" in encrypted_result
        assert "key_id" in encrypted_result
        assert "key_version" in encrypted_result
        
        # Verify the encrypted data is not the original dict
        assert encrypted_result["encrypted_data"] != json.dumps(sensitive_dict)
        
        # Decrypt the dictionary
        decrypted_dict = encryption_service.decrypt_dict(encrypted_result)
        
        # Verify decryption restores the original dict
        assert decrypted_dict == sensitive_dict
    
    def test_tamper_detection(self, encryption_service):
        """Test detection of tampered ciphertext."""
        # Sample data
        original_data = "Confidential patient data"
        
        # Encrypt the data
        encrypted_result = encryption_service.encrypt(original_data)
        
        # Tamper with the ciphertext
        original_ciphertext = encrypted_result["ciphertext"]
        tampered_bytes = bytearray(base64.b64decode(original_ciphertext))
        # Modify a byte in the ciphertext
        tampered_bytes[5] = (tampered_bytes[5] + 1) % 256
        tampered_ciphertext = base64.b64encode(tampered_bytes).decode()
        
        encrypted_result["ciphertext"] = tampered_ciphertext
        
        # Attempt to decrypt tampered data
        with pytest.raises(TamperingDetectedError):
            encryption_service.decrypt(encrypted_result)
    
    def test_tamper_detection_with_tag(self, encryption_service):
        """Test detection of tampered authentication tag."""
        # Sample data
        original_data = "Confidential patient data"
        
        # Encrypt the data
        encrypted_result = encryption_service.encrypt(original_data)
        
        # Tamper with the authentication tag
        original_tag = encrypted_result["tag"]
        tampered_bytes = bytearray(base64.b64decode(original_tag))
        # Modify a byte in the tag
        tampered_bytes[0] = (tampered_bytes[0] + 1) % 256
        tampered_tag = base64.b64encode(tampered_bytes).decode()
        
        encrypted_result["tag"] = tampered_tag
        
        # Attempt to decrypt with tampered tag
        with pytest.raises(TamperingDetectedError):
            encryption_service.decrypt(encrypted_result)
    
    def test_key_rotation(self, encryption_service, mock_kms):
        """Test key rotation functionality."""
        # Sample data
        original_data = "Patient information"
        
        # Encrypt with the current key
        encrypted_result = encryption_service.encrypt(original_data)
        current_key_id = encrypted_result["key_id"]
        current_key_version = encrypted_result["key_version"]
        
        # Mock key rotation
        mock_kms.generate_data_key.return_value = {
            "key_id": current_key_id,
            "key_version": current_key_version + 1,
            "key": os.urandom(32),  # New random key
            "created_at": "2025-03-28T12:00:00Z"  # One day later
        }
        
        # Trigger key rotation
        encryption_service.rotate_keys()
        
        # Encrypt with the new key
        new_encrypted_result = encryption_service.encrypt(original_data)
        
        # Verify key version has been incremented
        assert new_encrypted_result["key_version"] > current_key_version
        
        # Verify both old and new can be decrypted
        assert encryption_service.decrypt(encrypted_result) == original_data
        assert encryption_service.decrypt(new_encrypted_result) == original_data
    
    def test_password_hashing(self, encryption_service):
        """Test secure password hashing."""
        # Sample password
        password = "StrongP@ssw0rd123!"
        
        # Hash the password
        password_hash = encryption_service.hash_password(password)
        
        # Verify hash format
        assert password_hash.startswith("$argon2id$")
        
        # Verify password verification works
        assert encryption_service.verify_password(password, password_hash) is True
        
        # Verify wrong password fails
        assert encryption_service.verify_password("WrongPassword", password_hash) is False
    
    def test_secure_random_generation(self, encryption_service):
        """Test secure random number generation."""
        # Generate secure random bytes
        random_bytes_16 = encryption_service.generate_secure_random(16)
        random_bytes_32 = encryption_service.generate_secure_random(32)
        
        # Verify length
        assert len(random_bytes_16) == 16
        assert len(random_bytes_32) == 32
        
        # Verify randomness (basic check: outputs should be different)
        assert random_bytes_16 != random_bytes_32[:16]
        
        # Generate two random values of the same length and verify they're different
        another_random_16 = encryption_service.generate_secure_random(16)
        assert random_bytes_16 != another_random_16
    
    def test_key_derivation(self, encryption_service):
        """Test key derivation from passphrases."""
        # Sample passphrase
        passphrase = "This is a secure passphrase for key derivation"
        salt = encryption_service.generate_secure_random(16)
        
        # Derive a key
        derived_key_32 = encryption_service.derive_key(passphrase, salt, key_length=32)
        derived_key_64 = encryption_service.derive_key(passphrase, salt, key_length=64)
        
        # Verify key lengths
        assert len(derived_key_32) == 32
        assert len(derived_key_64) == 64
        
        # Verify consistency (same inputs produce same key)
        assert derived_key_32 == encryption_service.derive_key(passphrase, salt, key_length=32)
        
        # Verify different salt produces different key
        new_salt = encryption_service.generate_secure_random(16)
        assert derived_key_32 != encryption_service.derive_key(passphrase, new_salt, key_length=32)
    
    def test_asymmetric_encryption(self, encryption_service):
        """Test asymmetric encryption for secure key exchange."""
        # Generate a key pair for the recipient
        key_pair = encryption_service.generate_asymmetric_key_pair()
        public_key = key_pair["public_key"]
        private_key = key_pair["private_key"]
        
        # Sample sensitive data
        sensitive_data = "Patient health information that needs to be securely shared"
        
        # Encrypt using recipient's public key
        encrypted_data = encryption_service.encrypt_asymmetric(sensitive_data, public_key)
        
        # Verify encrypted data is not the plaintext
        assert encrypted_data != sensitive_data
        
        # Decrypt using recipient's private key
        decrypted_data = encryption_service.decrypt_asymmetric(encrypted_data, private_key)
        
        # Verify successful decryption
        assert decrypted_data == sensitive_data
    
    def test_digital_signature(self, encryption_service):
        """Test digital signature functionality for data integrity and authenticity."""
        # Generate a key pair for signing
        key_pair = encryption_service.generate_signing_key_pair()
        signing_key = key_pair["signing_key"]
        verify_key = key_pair["verify_key"]
        
        # Data to be signed
        message = "This patient record has been reviewed and approved by Dr. Smith"
        
        # Sign the message
        signature = encryption_service.sign_data(message, signing_key)
        
        # Verify the signature
        is_valid = encryption_service.verify_signature(message, signature, verify_key)
        assert is_valid is True
        
        # Verify signature fails with tampered message
        tampered_message = message + " with unauthorized changes"
        is_valid = encryption_service.verify_signature(tampered_message, signature, verify_key)
        assert is_valid is False
    
    def test_file_encryption(self, encryption_service):
        """Test encryption and decryption of file data."""
        # Sample file content
        file_data = b"This is a confidential patient file containing PHI.\n" * 1000  # ~50KB
        
        # Encrypt the file
        encrypted_file = encryption_service.encrypt_file(file_data)
        
        # Verify encrypted file format
        assert "encrypted_data" in encrypted_file
        assert "key_id" in encrypted_file
        assert "key_version" in encrypted_file
        assert "iv" in encrypted_file
        assert "tag" in encrypted_file
        
        # Verify the encrypted data is different from the original
        assert base64.b64decode(encrypted_file["encrypted_data"]) != file_data
        
        # Decrypt the file
        decrypted_file = encryption_service.decrypt_file(encrypted_file)
        
        # Verify successful decryption
        assert decrypted_file == file_data
    
    def test_authenticated_encryption(self, encryption_service):
        """Test authenticated encryption with additional authenticated data (AAD)."""
        # Sample data and context information
        sensitive_data = "Patient lab results: HDL 65mg/dL, LDL 120mg/dL"
        context = "Lab results for patient PT12345, authorized for Dr. Smith"
        
        # Encrypt with AAD
        encrypted_result = encryption_service.encrypt_with_aad(sensitive_data, context)
        
        # Decrypt with the same AAD
        decrypted_data = encryption_service.decrypt_with_aad(encrypted_result, context)
        
        # Verify successful decryption
        assert decrypted_data == sensitive_data
        
        # Attempt to decrypt with wrong AAD
        wrong_context = "Lab results for patient PT12345, authorized for Dr. Jones"
        with pytest.raises(TamperingDetectedError):
            encryption_service.decrypt_with_aad(encrypted_result, wrong_context)
    
    def test_bulk_encryption(self, encryption_service):
        """Test encryption and decryption of multiple items in bulk."""
        # Multiple items to encrypt
        sensitive_items = [
            "Patient 1: John Smith, DOB: 05/10/1975",
            "Patient 2: Jane Doe, DOB: 11/22/1982",
            "Patient 3: Robert Johnson, DOB: 07/15/1968"
        ]
        
        # Encrypt items in bulk
        encrypted_results = encryption_service.encrypt_bulk(sensitive_items)
        
        # Verify all items were encrypted
        assert len(encrypted_results) == len(sensitive_items)
        
        # Decrypt all items
        decrypted_items = encryption_service.decrypt_bulk(encrypted_results)
        
        # Verify all items were correctly decrypted
        assert decrypted_items == sensitive_items
    
    def test_hash_data_for_storage(self, encryption_service):
        """Test secure hashing of data for storage or comparison."""
        # Data to hash
        data_to_hash = "A unique identifier that should be securely stored"
        
        # Hash the data
        hashed_data = encryption_service.hash_data(data_to_hash)
        
        # Verify hash is not the original data
        assert hashed_data != data_to_hash
        
        # Verify the same input produces the same hash (consistency)
        assert encryption_service.hash_data(data_to_hash) == hashed_data
        
        # Verify different inputs produce different hashes
        different_data = "A slightly different identifier"
        assert encryption_service.hash_data(different_data) != hashed_data
    
    def test_key_wrapping(self, encryption_service):
        """Test key wrapping for secure key storage."""
        # Create a data key to be wrapped
        data_key = encryption_service.generate_secure_random(32)
        
        # Wrap the key for secure storage
        wrapped_key = encryption_service.wrap_key(data_key)
        
        # Verify wrapped key is not the original key
        assert wrapped_key["wrapped_key"] != data_key
        
        # Unwrap the key
        unwrapped_key = encryption_service.unwrap_key(wrapped_key)
        
        # Verify unwrapped key matches the original
        assert unwrapped_key == data_key
    
    def test_aws_kms_integration(self, encryption_service):
        """Test integration with AWS KMS for key management."""
        # Mock AWS KMS client
        mock_aws_kms = MagicMock()
        mock_aws_kms.generate_data_key.return_value = {
            "CiphertextBlob": b"encrypted-key-blob",
            "Plaintext": os.urandom(32),
            "KeyId": "arn:aws:kms:us-west-2:123456789012:key/abcd-1234-efgh-5678"
        }
        
        # Replace the key service with mocked AWS KMS
        with patch.object(encryption_service, "aws_kms", mock_aws_kms):
            # Sample data
            sample_data = "Protected health information for AWS KMS test"
            
            # Encrypt using AWS KMS for key management
            encrypted_result = encryption_service.encrypt_with_aws_kms(sample_data)
            
            # Verify encrypted result format
            assert "ciphertext" in encrypted_result
            assert "encrypted_key" in encrypted_result
            assert "key_id" in encrypted_result
            assert "iv" in encrypted_result
            assert "tag" in encrypted_result
            
            # Mock decryption response
            mock_aws_kms.decrypt.return_value = {
                "Plaintext": mock_aws_kms.generate_data_key.return_value["Plaintext"],
                "KeyId": "arn:aws:kms:us-west-2:123456789012:key/abcd-1234-efgh-5678"
            }
            
            # Decrypt using AWS KMS
            decrypted_data = encryption_service.decrypt_with_aws_kms(encrypted_result)
            
            # Verify successful decryption
            assert decrypted_data == sample_data
    
    def test_error_handling(self, encryption_service):
        """Test handling of various error conditions."""
        # Test with invalid key
        with pytest.raises(InvalidKeyError):
            encryption_service.encrypt("test data", key=b"too-short-key")
        
        # Test decryption with missing required fields
        incomplete_result = {
            "ciphertext": base64.b64encode(b"some-ciphertext").decode(),
            # Missing key_id, key_version, iv, tag
        }
        with pytest.raises(DecryptionError):
            encryption_service.decrypt(incomplete_result)
    
    def test_encryption_performance(self, encryption_service):
        """Test encryption performance with larger data sets."""
        # Generate a larger data set (~1MB)
        large_data = "A" * (1024 * 1024)  # 1MB of 'A' characters
        
        # Time the encryption
        import time
        start_time = time.time()
        
        encrypted_result = encryption_service.encrypt(large_data)
        
        encryption_duration = time.time() - start_time
        
        # Time the decryption
        start_time = time.time()
        
        decrypted_data = encryption_service.decrypt(encrypted_result)
        
        decryption_duration = time.time() - start_time
        
        # Verify successful encryption/decryption
        assert decrypted_data == large_data
        
        # Verify performance is reasonable
        # For 1MB of data, encryption and decryption should each take less than 1 second
        assert encryption_duration < 1.0
        assert decryption_duration < 1.0