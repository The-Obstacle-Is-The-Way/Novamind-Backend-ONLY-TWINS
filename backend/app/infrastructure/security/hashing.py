"""
Password hashing and verification utilities for HIPAA-compliant authentication.

This module provides cryptographically secure password hashing and verification
that meets HIPAA Security Rule requirements for access control.
"""

import secrets
import hashlib
from typing import Tuple, Optional


def hash_data(value: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash data using SHA-256 with a random salt.
    
    Args:
        value: The data to hash (typically a password)
        salt: Optional salt to use (generates random salt if not provided)
        
    Returns:
        Tuple of (hashed_value, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
        
    # Create a hash with the salt
    salted_value = f"{salt}{value}"
    hash_obj = hashlib.sha256(salted_value.encode())
    hashed_value = hash_obj.hexdigest()
    
    return hashed_value, salt


def secure_compare(value: str, hashed_value: str, salt: str) -> bool:
    """
    Verify a value against its hashed version using constant-time comparison.
    
    Args:
        value: The value to verify (typically a password)
        hashed_value: The stored hash to compare against
        salt: The salt used for hashing
        
    Returns:
        True if the value matches the hash, False otherwise
    """
    # Hash the value with the provided salt
    computed_hash, _ = hash_data(value, salt)
    
    # Use constant-time comparison to prevent timing attacks
    if len(computed_hash) != len(hashed_value):
        return False
        
    result = 0
    for x, y in zip(computed_hash, hashed_value):
        result |= ord(x) ^ ord(y)
    
    return result == 0