# -*- coding: utf-8 -*-
"""
HIPAA compliance and security tests for the database layer.

This test suite focuses on security-specific aspects of the database
to ensure proper compliance with HIPAA requirements, including:
- Connection security
- Data encryption at rest
- Audit logging of database operations
- Prevention of SQL injection
- Access control for database operations
"""

import pytest
import re
from unittest.mock import patch, MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.infrastructure.persistence.sqlalchemy.config.database import Database
from app.infrastructure.security.encryption import EncryptionService


@pytest.mark.db_required
class TestDatabaseSecurity:
    """HIPAA-focused security tests for the database layer."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        return mock_session
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.logger') as mock_logger:
            yield mock_logger
    
    @pytest.fixture
    def encryption_service(self):
        """Create an instance of the encryption service."""
        return EncryptionService()
    
    @pytest.mark.asyncio
    async def test_ssl_connection_required(self):
        """Test that SSL is required for database connections."""
        # Patch settings to check SSL enforcement
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.settings') as mock_settings:
            mock_settings.database.SSL_REQUIRED = True
            
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
                # Initialize database
                db = Database()
                
                # Check SSL requirement
                args, kwargs = mock_create_engine.call_args
                
                # Assert SSL parameters are present and properly configured
                assert 'connect_args' in kwargs
                assert 'sslmode' in kwargs['connect_args']
                assert kwargs['connect_args']['sslmode'] == 'require'
    
    @pytest.mark.asyncio
    async def test_database_credential_protection(self):
        """Test that database credentials are never logged or exposed."""
        # Patch settings with test credentials
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.settings') as mock_settings:
            mock_settings.database.DB_USER = "test_user"
            mock_settings.database.DB_PASSWORD = "test_password"
            mock_settings.database.DB_HOST = "localhost"
            mock_settings.database.DB_PORT = "5432"
            mock_settings.database.DB_NAME = "test_db"
            mock_settings.database.DB_ENGINE = "postgresql+asyncpg"
            
            # Patch the logger to check for credential leakage
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.logger') as mock_logger:
                # Initialize database
                db = Database()
                
                # Check all log calls to ensure credentials aren't logged
                for call in mock_logger.method_calls:
                    method_name, args, kwargs = call
                    for arg in args:
                        if isinstance(arg, str):
                            assert "test_password" not in arg, "Password found in logs"
    
    @pytest.mark.asyncio
    async def test_database_audit_logging(self, mock_session, mock_logger):
        """Test that database operations are properly audit logged."""
        # Test setup
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.async_sessionmaker') as mock_session_maker:
            mock_session_maker.return_value = mock_session
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine'):
                db = Database()
                
                # Perform a database operation
                async with db.session() as session:
                    await session.execute(text("SELECT 1"))
                    await session.commit()
                
                # Verify audit logs were created for session start, operations, and commit
                assert mock_logger.debug.call_count >= 3
                
                # Verify each session lifecycle event is logged
                debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
                assert any("session started" in call.lower() for call in debug_calls)
                assert any("session committed" in call.lower() for call in debug_calls)
                assert any("session closed" in call.lower() for call in debug_calls)
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, mock_session):
        """Test that SQL injection is prevented through parameterization."""
        # Setup a mock repository that uses the database
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.async_sessionmaker') as mock_session_maker:
            mock_session_maker.return_value = mock_session
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine'):
                db = Database()
                
                # Test with a potentially malicious SQL injection input
                malicious_input = "1'; DROP TABLE patients; --"
                
                async with db.session() as session:
                    # Execute query with potentially malicious input
                    # We expect parameters to be properly escaped
                    await session.execute(
                        text("SELECT * FROM patients WHERE id = :id"),
                        {"id": malicious_input}
                    )
                
                # Verify the execute was called with parameterized query
                mock_session.execute.assert_called_once()
                args, kwargs = mock_session.execute.call_args
                
                # Verify that the parameter is passed separately, not concatenated
                assert "DROP TABLE" not in str(args[0])
                assert kwargs["parameters"]["id"] == malicious_input
    
    @pytest.mark.asyncio
    async def test_encrypted_sensitive_data(self, encryption_service):
        """Test that sensitive data is encrypted in the database."""
        # This is a schema validation test - we're testing that our
        # database models properly encrypt PHI before storage
        
        # Create a mock patient with sensitive PHI
        patient_data = {
            "id": "12345",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-01",
            "ssn": "123-45-6789",
            "address": "123 Main St, Anytown, USA",
            "phone_number": "555-123-4567",
            "email": "john.doe@example.com"
        }
        
        # Setup mocks for repository
        with patch('app.infrastructure.persistence.sqlalchemy.models.patient.encryption_service', 
                  return_value=encryption_service):
            
            # Import here to avoid circular imports in test setup
            from app.infrastructure.persistence.sqlalchemy.models.patient import Patient
            
            # Create a patient model instance
            patient = Patient(**patient_data)
            
            # Verify sensitive fields are encrypted or hashed
            sensitive_fields = ["ssn", "date_of_birth", "address", "phone_number"]
            for field in sensitive_fields:
                field_value = getattr(patient, field)
                
                # Check that the original sensitive data is not stored as plaintext
                assert field_value != patient_data[field], f"Field {field} is not encrypted"
                
                # For encrypted fields, they should have a specific format or length
                # This tests that the fields appear to be encrypted rather than plaintext
                # The exact format depends on the encryption method used
                if field == "ssn":
                    # SSN should be securely hashed or encrypted
                    assert len(field_value) > 20, "SSN does not appear to be properly secured"
    
    @pytest.mark.asyncio
    async def test_database_connection_timeout(self):
        """Test that database connections have appropriate timeouts."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.settings') as mock_settings:
            # Set a reasonable connection timeout
            mock_settings.database.POOL_TIMEOUT = 30
            mock_settings.database.POOL_RECYCLE = 3600
            
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
                # Initialize database
                db = Database()
                
                # Verify timeout settings are applied
                mock_create_engine.assert_called_once()
                args, kwargs = mock_create_engine.call_args
                
                # Check proper timeout settings for security (prevent connection hanging)
                assert kwargs.get("pool_timeout") == 30
                assert kwargs.get("pool_recycle") == 3600
    
    @pytest.mark.asyncio
    async def test_session_isolation_level(self):
        """Test that database sessions use appropriate isolation levels."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine') as mock_create_engine:
            with patch('sqlalchemy.ext.asyncio.async_sessionmaker') as mock_session_maker:
                # Initialize database
                db = Database()
                
                # Check that session creation includes isolation level
                mock_session_maker.assert_called_once()
                args, kwargs = mock_session_maker.call_args
                
                # Sessions should not use the default isolation level for sensitive data
                assert "READ COMMITTED" in str(kwargs) or "SERIALIZABLE" in str(kwargs)
    
    @pytest.mark.asyncio
    async def test_error_response_sanitization(self, mock_session):
        """Test that database errors don't expose sensitive information."""
        with patch('app.infrastructure.persistence.sqlalchemy.config.database.async_sessionmaker') as mock_session_maker:
            # Configure session to raise an error with sensitive information
            mock_session.execute.side_effect = Exception(
                "ERROR: column patients.ssn contains PHI '123-45-6789' which failed constraint"
            )
            mock_session_maker.return_value = mock_session
            
            with patch('app.infrastructure.persistence.sqlalchemy.config.database.create_async_engine'):
                db = Database()
                
                # Mock the logger to check for sanitized error messages
                with patch('app.infrastructure.persistence.sqlalchemy.config.database.logger') as mock_logger:
                    # Attempt operation that will fail
                    with pytest.raises(Exception):
                        async with db.session() as session:
                            await session.execute(text("SELECT * FROM patients"))
                    
                    # Verify error log doesn't contain PHI
                    mock_logger.error.assert_called_once()
                    error_message = mock_logger.error.call_args[0][0]
                    
                    # Error message should not contain the SSN
                    assert "123-45-6789" not in error_message, "Error message contains unsanitized PHI"
                    
                    # There should be a sanitized version of the error
                    assert "Database session rolled back" in error_message