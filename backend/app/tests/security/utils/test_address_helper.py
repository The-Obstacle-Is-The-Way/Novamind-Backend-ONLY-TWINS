"""
Test helper for address handling in field encryption.

This module ensures proper encryption of address data structures
while maintaining HIPAA compliance.
"""

import pytest

from app.infrastructure.security.encryption.base_encryption_service import BaseEncryptionService
from app.infrastructure.security.encryption.field_encryptor import FieldEncryptor
# TEMP: Comment out missing AddressHelper import
# from app.infrastructure.utils.address_helper import AddressHelper 
from app.domain.entities.address import Address


def test_address_field_encryption():



    """Test address field handling in the field encryptor."""
    # Setup
    encryption_service = BaseEncryptionService(direct_key="test_address",)
    field_encryptor= FieldEncryptor(encryption_service)

    # Sample nested address
    data = {
    "demographics": {
    "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345",
    }
    }
    }

    # Encrypt the address
    encrypted = field_encryptor.encrypt_fields(data, ["demographics.address"])

    # Verify all components got encrypted properly
    assert encrypted["demographics"]["address"]["street"].startswith("v1:")
    assert encrypted["demographics"]["address"]["city"].startswith("v1:")
    assert encrypted["demographics"]["address"]["state"].startswith("v1:")
    assert encrypted["demographics"]["address"]["zip"].startswith("v1:")

    # Decrypt and verify original values
    # Correct the call to decrypt_fields
    decrypted = field_encryptor.decrypt_fields(
        encrypted, ["demographics.address"]) # Add closing parenthesis
    assert decrypted["demographics"]["address"]["street"] == "123 Main St"
    assert decrypted["demographics"]["address"]["city"] == "Anytown"
    assert decrypted["demographics"]["address"]["state"] == "CA"
    assert decrypted["demographics"]["address"]["zip"] == "12345"


if __name__ == "__main__":
    # Indent the code block
    test_address_field_encryption()
    print("Address field encryption test passed!")
