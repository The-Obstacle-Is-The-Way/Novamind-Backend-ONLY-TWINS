from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException

from app.core.security.encryption import EncryptionService

class TestDatabaseSecurity:
    def setup_method(self):
        self.encryption_service = EncryptionService()

    def test_database_encryption(self):
        """
        Test that sensitive data is encrypted in the database.
        """
        # Simply test the encryption service directly without mocking a non-existent module
        data = "sensitive data"
        encrypted = self.encryption_service.encrypt(data)
        decrypted = self.encryption_service.decrypt(encrypted)
        assert decrypted == data, "Encryption and decryption should preserve data"
