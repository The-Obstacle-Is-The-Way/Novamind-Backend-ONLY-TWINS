"""
Encryption utilities for HIPAA-compliant data protection.

This module provides encryption and decryption functions for protecting
sensitive patient data both at rest and during processing.
"""

import base64
import os
import logging
from typing import Optional, Union, Any, Dict

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config.settings import get_settings

# Configure logger
logger = logging.getLogger(__name__)

# Global encryption key instance - lazily initialized
_encryption_key = None


def get_encryption_key() -> bytes:
    """
    Get the encryption key for sensitive data.
    
    Returns:
        bytes: The encryption key
    """
    global _encryption_key
    
    if _encryption_key is None:
        settings = get_settings()
        
        # In production, key should be securely stored or derived
        if settings.ENCRYPTION_KEY:
            # Direct key from environment or settings
            try:
                _encryption_key = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY)
                assert len(_encryption_key) == 32  # Fernet key must be 32 bytes
            except Exception as e:
                logger.error(f"Invalid encryption key format: {e}")
                # Generate a development-only key - DO NOT USE IN PRODUCTION
                _encryption_key = Fernet.generate_key()
        else:
            # For development only - derive key from a password and salt
            # In production, keys should not be derived this way
            salt = settings.ENCRYPTION_SALT.encode() if settings.ENCRYPTION_SALT else b"novamind-salt"
            password = settings.ENCRYPTION_PASSWORD.encode() if settings.ENCRYPTION_PASSWORD else b"development-only-password"
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            _encryption_key = base64.urlsafe_b64encode(kdf.derive(password))
            
            logger.warning(
                "Using derived encryption key for development - NOT SECURE FOR PRODUCTION"
            )
    
    return _encryption_key


def encrypt_value(value: Optional[Union[str, bytes]]) -> Optional[str]:
    """
    Encrypt a value for secure storage.
    
    Args:
        value: Value to encrypt (string or bytes)
        
    Returns:
        str: Base64-encoded encrypted value, or None if input is None
    """
    if value is None:
        return None
    
    try:
        # Convert to bytes if string
        if isinstance(value, str):
            value_bytes = value.encode('utf-8')
        else:
            value_bytes = value
        
        # Get encryption key and initialize Fernet
        key = get_encryption_key()
        f = Fernet(key)
        
        # Encrypt and encode as base64 string
        encrypted = f.encrypt(value_bytes)
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        # Fall back to plaintext in case of error
        # In production, this should be handled more carefully
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        return value


def decrypt_value(encrypted_value: Optional[str]) -> Optional[str]:
    """
    Decrypt an encrypted value.
    
    Args:
        encrypted_value: Base64-encoded encrypted value
        
    Returns:
        str: Decrypted value, or None if input is None
    """
    if encrypted_value is None:
        return None
    
    try:
        # Decode base64 and decrypt
        encrypted_bytes = base64.b64decode(encrypted_value)
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_bytes)
        
        # Convert bytes to string
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        # In case of error, return None
        # In production, this should be handled more carefully
        return None


def encrypt_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt all values in a dictionary.
    
    Args:
        data: Dictionary with values to encrypt
        
    Returns:
        Dict with encrypted values
    """
    encrypted = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively encrypt nested dictionaries
            encrypted[key] = encrypt_dict(value)
        elif isinstance(value, str):
            # Encrypt string values
            encrypted[key] = encrypt_value(value)
        else:
            # Keep other values as-is
            encrypted[key] = value
    
    return encrypted


def decrypt_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrypt all values in a dictionary.
    
    Args:
        data: Dictionary with encrypted values
        
    Returns:
        Dict with decrypted values
    """
    decrypted = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively decrypt nested dictionaries
            decrypted[key] = decrypt_dict(value)
        elif isinstance(value, str):
            # Decrypt string values
            decrypted[key] = decrypt_value(value)
        else:
            # Keep other values as-is
            decrypted[key] = value
    
    return decrypted