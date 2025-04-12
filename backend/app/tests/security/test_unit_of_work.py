# -*- coding: utf-8 -*-
"""
HIPAA Security Test Suite - Database Security Tests

Tests for the SQLAlchemy Unit of Work implementation to ensure HIPAA-compliant
data integrity and proper transaction management for PHI operations.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SQLAlchemyUnitOfWork
from app.domain.exceptions import RepositoryError  # Changed from TransactionError


@pytest.mark.db_required()
class TestSQLAlchemyUnitOfWork:
    """
    Tests for the SQLAlchemy Unit of Work to ensure HIPAA-compliant data integrity.

    These tests verify:
        1. Proper transaction management for all PHI operations
        2. Atomicity of related data changes
        3. Rollback on errors to prevent inconsistent PHI states
        4. Clean session management to prevent data leaks
        """

    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock session factory for testing."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        return mock_session_factory, mock_session

        @pytest.fixture
        def unit_of_work(self, mock_session_factory):
        """Create a Unit of Work instance for testing."""
        factory, _ = mock_session_factory
        return SQLAlchemyUnitOfWork(session_factory=factory)

        def test_successful_transaction(
                self, unit_of_work, mock_session_factory):
        """Test that a successful transaction commits all changes."""
        # Arrange
        _, mock_session = mock_session_factory

        # Act
        with unit_of_work:
            # Simulate repository operations
            # In real usage, this would be something like:
            # unit_of_work.patients.add(patient)
            pass

            # Complete the transaction
            unit_of_work.commit()

            # Assert
            mock_session.begin.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

            def test_transaction_rollback_on_exception(
                self, unit_of_work, mock_session_factory
            ):
        """Test that an exception inside the transaction triggers rollback.

        This ensures that PHI data integrity is maintained even when errors occur.
        """
        # Arrange
        _, mock_session = mock_session_factory

        # Act - raise an exception within the transaction
        with pytest.raises(ValueError):
            with unit_of_work:
                # Simulate repository operations that cause an error
                raise ValueError("Test exception")

                # Assert
                mock_session.begin.assert_called_once()
                mock_session.rollback.assert_called_once()
                mock_session.commit.assert_not_called()
                mock_session.close.assert_called_once()

                def test_nested_transaction_support(
                        self, unit_of_work, mock_session_factory):
        """Test that nested transactions are handled correctly.

        This is important for complex PHI operations that span multiple repositories.
        """
        # Arrange
        _, mock_session = mock_session_factory
        mock_session.begin.return_value = MagicMock()

        # Act
        with unit_of_work:
            # Outer transaction
            with unit_of_work.nested():
                # Inner transaction
                pass

                unit_of_work.commit()

                # Assert
                # Verify that the session's begin_nested was called for the
                # inner transaction
                mock_session.begin_nested.assert_called_once()
                mock_session.commit.assert_called_once()
                mock_session.close.assert_called_once()

                def test_read_only_transaction(
                        self, unit_of_work, mock_session_factory):
        """Test read-only transaction support for safer PHI access."""
        # Arrange
        _, mock_session = mock_session_factory

        # Act
        with unit_of_work.read_only():
            # This transaction should be marked read-only and auto-rollback
            pass

            # Assert
            mock_session.begin.assert_called_once()
            # Should rollback instead of commit to ensure no changes
            mock_session.rollback.assert_called_once()
            mock_session.commit.assert_not_called()
            mock_session.close.assert_called_once()

            def test_read_only_transaction_prevents_commits(
                self, unit_of_work, mock_session_factory
            ):
        """Test that read-only transactions cannot commit changes."""
        # Arrange
        _, mock_session = mock_session_factory

        # Act
        with pytest.raises(RepositoryError):  # Changed exception type
            with unit_of_work.read_only():
                unit_of_work.commit()

                # Assert
                mock_session.commit.assert_not_called()
                mock_session.rollback.assert_called()

                def test_transaction_metadata_for_audit(
                        self, unit_of_work, mock_session_factory):
        """Test that transaction metadata is captured for HIPAA audit purposes."""
        # Arrange
        _, mock_session = mock_session_factory

        # Act
        with patch(
            "app.infrastructure.logging.audit_logger.AuditLogger.log_transaction"
        ) as mock_audit:
            with unit_of_work:
                # Set transaction metadata
                unit_of_work.set_metadata(
                    {
                        "user_id": "provider123",
                        "action": "update_patient_record",
                        "patient_id": "patient456",
                    }
                )
                unit_of_work.commit()

        # Assert
        # Verify the audit logger was called with the metadata
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args[0][0]
        assert call_args["user_id"] == "provider123"
        assert call_args["action"] == "update_patient_record"
        assert call_args["patient_id"] == "patient456"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
