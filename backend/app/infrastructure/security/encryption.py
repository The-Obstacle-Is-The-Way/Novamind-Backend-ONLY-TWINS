# -*- coding: utf-8 -*-
"""
HIPAA-compliant encryption service.

This module provides cryptographic services for securing Protected Health Information (PHI)
in accordance with HIPAA requirements for encryption at rest and in transit.
"""

import base64
import json
import os
import hashlib
import hmac
from typing import Any, Dict, Optional, Tuple, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.core.config import settings


def derive_key(password: bytes, salt: bytes, iterations: int = 100000) -> bytes:
    """
    Derive a cryptographic key from a password and salt using PBKDF2.
    
    Args:
        password: The password to derive the key from
        salt: The salt for key derivation
        iterations: Number of iterations for the KDF
        
    Returns:
        Derived key as bytes
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password)


def encrypt_data(data: str, key: bytes) -> bytes:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: String data to encrypt
        key: Encryption key
        
    Returns:
        Encrypted data as bytes
    """
    if not data:
        return b""
    
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())


def decrypt_data(data: bytes, key: bytes) -> str:
    """
    Decrypt data using Fernet symmetric encryption.
    
    Args:
        data: Encrypted bytes to decrypt
        key: Encryption key
        
    Returns:
        Decrypted string
    """
    if not data:
        return ""
    
    fernet = Fernet(key)
    return fernet.decrypt(data).decode()


def hash_data(data: str, salt: Optional[bytes] = None) -> str:
    """
    Hash data using scrypt with a random salt.
    
    Args:
        data: Data to hash
        salt: Optional salt, generated randomly if not provided
        
    Returns:
        Hash string in format "scrypt$salt$hash"
    """
    if not salt:
        salt = os.urandom(16)
    
    # Use scrypt for password hashing (more secure than PBKDF2)
    hash_bytes = hashlib.scrypt(
        password=data.encode(),
        salt=salt,
        n=16384,  # CPU/memory cost parameter
        r=8,      # Block size parameter
        p=1,      # Parallelization parameter
        dklen=64  # Output length
    )
    
    # Format: algorithm$salt$hash
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(hash_bytes).decode()}"


def secure_compare(data: str, hash_string: str) -> bool:
    """
    Securely compare plain text against a hash string.
    
    Args:
        data: Plain text data
        hash_string: Hash string in format "algorithm$salt$hash"
        
    Returns:
        True if match, False otherwise
        
    Raises:
        ValueError: If hash string format is invalid or algorithm is unsupported
    """
    parts = hash_string.split('$')
    if len(parts) != 3:
        raise ValueError("Invalid hash format")
    
    algorithm, salt_b64, hash_b64 = parts
    
    if algorithm != "scrypt":
        raise ValueError(f"Unsupported hashing algorithm: {algorithm}")
    
    salt = base64.b64decode(salt_b64)
    
    # Hash the input data with the same salt
    data_hash = hash_data(data, salt)
    
    # Secure constant-time comparison to prevent timing attacks
    return hmac.compare_digest(hash_string, data_hash)


class EncryptionService:
    """
    HIPAA-compliant encryption service for PHI.
    
    Uses Fernet (AES-128-CBC) with a key derived using PBKDF2.
    """
    
    def __init__(self, key: Optional[str] = None) -> None:
        """
        Initialize encryption service with a key.
        
        Args:
            key: Encryption key. If None, uses the key from settings.
        """
        # Use the imported settings object directly
        app_settings = settings
        security_settings = getattr(app_settings, 'security', {})
        self._key = key or getattr(security_settings, 'ENCRYPTION_KEY', 'novamind_default_key')
        self._salt = base64.b64decode(getattr(security_settings, 'KDF_SALT', b'novamind_hipaa_salt')) 
        self.pepper = getattr(security_settings, 'HASH_PEPPER', "novamind_pepper")
        
        # Derive the key and create Fernet instance
        self.key = self._derive_key(self._key.encode(), self._salt)
        self.cipher_suite = Fernet(base64.urlsafe_b64encode(self.key))
    
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """
        Derive a cryptographic key using PBKDF2.
        
        Args:
            password: Password bytes
            salt: Salt bytes
            
        Returns:
            Derived key
        """
        return derive_key(password, salt)
    
    def _pepper_text(self, text: str) -> str:
        """
        Add a pepper to text before hashing (server-side secret).
        
        Args:
            text: Text to pepper
            
        Returns:
            Peppered text
        """
        return f"{text}{self.pepper}"
    
    def encrypt(self, data: str, metadata: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Encrypt data with optional metadata.
        
        Args:
            data: Data to encrypt
            metadata: Optional metadata to include with encrypted data
            
        Returns:
            Encrypted data as bytes
        """
        if not data:
            return b""
        
        # If metadata is provided, include it with the data
        if metadata:
            payload = {
                "data": data,
                "metadata": metadata
            }
            plaintext = json.dumps(payload)
        else:
            plaintext = data
        
        # Encrypt the data
        return self.cipher_suite.encrypt(plaintext.encode())
    
    def decrypt(self, data: bytes, return_metadata: bool = False) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Decrypt data and optionally return metadata.
        
        Args:
            data: Encrypted data
            return_metadata: If True, return both data and metadata
            
        Returns:
            Decrypted data string, or tuple of (data, metadata) if return_metadata is True
        """
        if not data:
            return "" if not return_metadata else ("", {})
        
        # Decrypt the data
        plaintext = self.cipher_suite.decrypt(data).decode()
        
        # Check if the decrypted data is JSON with metadata
        try:
            payload = json.loads(plaintext)
            if isinstance(payload, dict) and "data" in payload and "metadata" in payload:
                if return_metadata:
                    return payload["data"], payload["metadata"]
                return payload["data"]
        except (json.JSONDecodeError, TypeError):
            # Not JSON or doesn't have the expected structure
            pass
        
        return plaintext
    
    def encrypt_phi(self, phi_data: Dict[str, Any]) -> bytes:
        """
        Encrypt PHI data with special handling.
        
        Args:
            phi_data: Dictionary of PHI data
            
        Returns:
            Encrypted PHI as bytes
        """
        # Add metadata to indicate this is PHI
        metadata = {"content_type": "phi", "version": "1.0"}
        return self.encrypt(json.dumps(phi_data), metadata)
    
    def decrypt_phi(self, encrypted_phi: bytes) -> Dict[str, Any]:
        """
        Decrypt PHI data.
        
        Args:
            encrypted_phi: Encrypted PHI bytes
            
        Returns:
            Decrypted PHI as dictionary
        """
        decrypted, metadata = self.decrypt(encrypted_phi, return_metadata=True)
        
        # Validate that this is PHI data
        if isinstance(metadata, dict) and metadata.get("content_type") == "phi":
            return json.loads(decrypted)
        
        # If not in expected format, just try to parse as JSON
        return json.loads(decrypted)
    
    def hash_password(self, password: str) -> str:
        """
        Securely hash a password with salt and pepper.
        
        Args:
            password: Password to hash
            
        Returns:
            Secure hash string
        """
        # Add pepper before hashing
        peppered_password = self._pepper_text(password)
        return hash_data(peppered_password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Password to verify
            hashed_password: Stored hash to check against
            
        Returns:
            True if password matches, False otherwise
        """
        # Add pepper before verification
        peppered_password = self._pepper_text(password)
        return secure_compare(peppered_password, hashed_password)
    
    def encrypt_file(self, input_path: str, output_path: str) -> None:
        """
        Encrypt a file.
        
        Args:
            input_path: Path to the file to encrypt
            output_path: Path where the encrypted file will be saved
            
        Raises:
            FileNotFoundError: If input file doesn't exist
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read file content
        with open(input_path, 'rb') as f:
            content_bytes = f.read()
            
        # Handle both string and bytes content (for test mocking)
        try:
            # If it's bytes, decode to string
            content = content_bytes.decode('utf-8')
        except AttributeError:
            # If it's already a string (from mock), use directly
            content = content_bytes
        
        # Encrypt the content
        encrypted = self.encrypt(content)
        
        # Write encrypted content to output file
        with open(output_path, 'wb') as f:
            f.write(encrypted)
    
    def decrypt_file(self, input_path: str, output_path: str) -> None:
        """
        Decrypt a file.
        
        Args:
            input_path: Path to the encrypted file
            output_path: Path where the decrypted file will be saved
            
        Raises:
            FileNotFoundError: If input file doesn't exist
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read encrypted content
        with open(input_path, 'rb') as f:
            encrypted_content = f.read()
            
        # Handle both string and bytes content (for test mocking)
        try:
            # If it's already bytes, use directly
            if isinstance(encrypted_content, bytes):
                encrypted = encrypted_content
            else:
                # If it's a string (from mock), convert to bytes if needed
                encrypted = encrypted_content.encode() if hasattr(encrypted_content, 'encode') else encrypted_content
        except AttributeError:
            # Fallback
            encrypted = encrypted_content
        
        # Decrypt the content
        decrypted = self.decrypt(encrypted)
        
        # Write decrypted content to output file
        with open(output_path, 'w') as f:
            f.write(decrypted)


def get_encryption_service() -> EncryptionService:
    """
    Factory function to get or create the encryption service.

    Returns:
        EncryptionService: Encryption service instance
    """
    # In a real application, consider using a singleton pattern or dependency injection
    return EncryptionService()
