"""
Security module for the Novamind Digital Twin Backend.

This package contains authentication, authorization, and security
utilities for the application.
"""

# Import functions directly to make them available
# Import password functions from the correct infrastructure location and alias them
from app.infrastructure.security.encryption import hash_data as get_password_hash, secure_compare as verify_password

__all__ = ["authentication", "rbac", "get_password_hash", "verify_password"]