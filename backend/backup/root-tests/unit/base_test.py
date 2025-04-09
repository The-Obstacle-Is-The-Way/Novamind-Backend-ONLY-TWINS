# -*- coding: utf-8 -*-
"""Base test class for unit tests."""

import pytest
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.infrastructure.security.encryption import EncryptionService
from app.infrastructure.security.jwt_service import JWTService

class BaseTest:
    """Base test class with common setup and utilities."""
    
    @pytest.fixture(autouse=True)
    def setup(
        self,
        test_settings: Settings,
        test_db_session: AsyncSession,
        mock_encryption_service: EncryptionService,
        mock_jwt_service: JWTService
    ) -> None:
        """Set up test environment."""
        self.settings = test_settings
        self.db = test_db_session
        self.encryption = mock_encryption_service
        self.jwt = mock_jwt_service
    
    async def cleanup_db(self) -> None:
        """Clean up database after test."""
        await self.db.rollback()
        
        # Delete all data from tables
        for table in reversed(self.db.get_bind().dialect.get_table_names()):
            await self.db.execute(f'DELETE FROM {table}')
        
        await self.db.commit()
    
    def assert_encrypted(self, value: str) -> None:
        """Assert that a value is encrypted."""
        assert value.startswith('encrypted_'), f"Value {value} is not encrypted"
    
    def assert_not_encrypted(self, value: str) -> None:
        """Assert that a value is not encrypted."""
        assert not value.startswith('encrypted_'), f"Value {value} is encrypted"
    
    async def assert_audit_logged(self, event_type: str, details: Optional[dict] = None) -> None:
        """Assert that an audit log entry exists."""
        # Implementation depends on your audit logging system
        pass
    
    async def assert_phi_masked(self, value: str) -> None:
        """Assert that PHI is properly masked."""
        # Implementation depends on your PHI masking system
        pass
