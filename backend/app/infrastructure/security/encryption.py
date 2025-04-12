"""
HIPAA-compliant encryption implementation for the infrastructure layer.

This module provides PHI encryption in accordance with HIPAA Security Rule requirements,
leveraging the core encryption services while adhering to clean architecture principles.
"""

import os
from typing import Dict, Any, List, Optional, Union

# Import the core implementation - zero redundancy
from app.core.security.encryption import EncryptionService as CoreEncryptionService
from app.core.security.field_encryption import FieldEncryptor


class EncryptionError(Exception):
    """Exception raised for encryption-related errors.
    
    This provides a consistent error interface for encryption operations
    throughout the application.
    """
    pass


class EncryptionKeyManager:
    """Manage encryption keys for HIPAA-compliant data protection.
    
    This class provides key management functionality for encryption operations,
    including key retrieval, rotation, and validation.
    """
    
    def __init__(self, key_source: str = "env"):
        """Initialize the key manager.
        
        Args:
            key_source: Source of the encryption key ('env' for environment variables)
        """
        self.key_source = key_source
        self._core_service = CoreEncryptionService()
    
    def get_encryption_key(self) -> bytes:
        """Get the current encryption key.
        
        Returns:
            The current encryption key as bytes
        """
        return self._core_service.key
    
    def rotate_encryption_key(self) -> bytes:
        """Rotate the encryption key.
        
        This generates a new encryption key and sets it as the current key.
        The previous key is retained for decrypting existing data.
        
        Returns:
            The new encryption key
        """
        # Generate a new key directly using the core service's methodology
        old_key = self._core_service.key
        
        # The core service will handle key rotation internally when environment
        # variables are updated, but we simulate the process here
        new_key = os.urandom(32)
        os.environ["ENCRYPTION_KEY"] = new_key.hex()
        os.environ["PREVIOUS_ENCRYPTION_KEY"] = old_key.hex()
        
        # Reinitialize with new keys
        self._core_service = CoreEncryptionService()
        return new_key


class PHIFieldEncryption:
    """Encrypt/decrypt PHI fields in data structures.
    
    This class provides selective encryption of Protected Health Information (PHI)
    fields within data structures according to HIPAA requirements.
    """
    
    def __init__(self, key_manager: Optional[EncryptionKeyManager] = None):
        """Initialize the field encryption utility.
        
        Args:
            key_manager: Optional key manager for encryption
        """
        self.key_manager = key_manager or EncryptionKeyManager()
        self._core_service = CoreEncryptionService()
        self._field_encryptor = FieldEncryptor(self._core_service)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a single value.
        
        Args:
            value: String value to encrypt
            
        Returns:
            Encrypted value
            
        Raises:
            EncryptionError: If encryption fails
        """
        if not value:
            return value
            
        try:
            return self._core_service.encrypt(value)
        except ValueError as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, value: str) -> str:
        """Decrypt a single value.
        
        Args:
            value: Encrypted value to decrypt
            
        Returns:
            Decrypted value
            
        Raises:
            EncryptionError: If decryption fails
        """
        if not value:
            return value
            
        try:
            return self._core_service.decrypt(value)
        except ValueError as e:
            # Handle invalid formats more gracefully for legacy data
            if "Invalid encryption format" in str(e):
                return value
            raise EncryptionError(f"Decryption failed: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any], phi_fields: List[str]) -> Dict[str, Any]:
        """Encrypt PHI fields in a dictionary.
        
        Args:
            data: Dictionary containing data to encrypt
            phi_fields: List of field paths to encrypt
            
        Returns:
            Dictionary with encrypted PHI fields
        """
        if not data or not phi_fields:
            return data
            
        try:
            return self._field_encryptor.encrypt_fields(data, phi_fields)
        except Exception as e:
            raise EncryptionError(f"Field encryption failed: {str(e)}")
    
    def decrypt_dict(self, data: Dict[str, Any], phi_fields: List[str]) -> Dict[str, Any]:
        """Decrypt PHI fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            phi_fields: List of field paths to decrypt
            
        Returns:
            Dictionary with decrypted PHI fields
        """
        if not data or not phi_fields:
            return data
            
        try:
            return self._field_encryptor.decrypt_fields(data, phi_fields)
        except Exception as e:
            raise EncryptionError(f"Field decryption failed: {str(e)}")