from unittest.mock import patch
import pytest
from fastapi import HTTPException

from app.core.security.encryption import EncryptionService
from app.tests.security.base_test import BaseSecurityTest
class TestDatabaseSecurity(BaseSecurityTest):
    def setup_method(self):

                super().setup_method()
        self.encryption_service = EncryptionService()

        def test_database_encryption(self):


                    """
            Test that sensitive data is encrypted in the database.
            """
            with patch(
            "app.infrastructure.persistence.sqlalchemy.models.patient.encryption_service",
            return_value=self.encryption_service,
        ):
            # Test code here
            pass
