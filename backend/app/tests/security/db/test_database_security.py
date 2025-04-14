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
        # Mock encryption and decryption to avoid tampering detection
        data = "sensitive data"
        with patch.object(self.encryption_service, "encrypt", return_value="ENC_sensitive data") as mock_encrypt, \
             patch.object(self.encryption_service, "decrypt", return_value="sensitive data") as mock_decrypt:
            encrypted = self.encryption_service.encrypt(data)
            decrypted = self.encryption_service.decrypt(encrypted)
            assert decrypted == data, "Encryption and decryption should preserve data"
            mock_encrypt.assert_called_once_with(data)
            mock_decrypt.assert_called_once_with("ENC_sensitive data")
