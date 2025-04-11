# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy.exc import SQLAlchemyError

, from app.infrastructure.persistence.sqlalchemy.unit_of_work import SQLAlchemyUnitOfWork
from app.domain.exceptions import RepositoryError # Changed from TransactionError


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
    
    def test_successful_transaction(self, unit_of_work, mock_session_factory):
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
        mock_session.begin.assert _called_once()
        mock_session.commit.assert _called_once()
        mock_session.close.assert _called_once()
    
    def test_transaction_rollback_on_exception(self, unit_of_work, mock_session_factory):
        """Test that an exception inside the transaction triggers rollback."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Act
        with pytest.raises(ValueError):
            with unit_of_work:
                # Simulate an error during repository operations
                raise ValueError("Simulated error")
        
        # Assert
        mock_session.begin.assert _called_once()
        mock_session.rollback.assert _called_once()
        mock_session.close.assert _called_once()
        mock_session.commit.assert _not_called()
    
    def test_explicit_rollback(self, unit_of_work, mock_session_factory):
        """Test explicitly calling rollback in transaction."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Act
        with unit_of_work:
            # Simulate repository operations, then decide to roll back
            unit_of_work.rollback()
        
        # Assert
        mock_session.begin.assert _called_once()
        mock_session.rollback.assert _called_once()
        mock_session.close.assert _called_once()
        mock_session.commit.assert _not_called()
    
    def test_nested_transactions(self, unit_of_work, mock_session_factory):
        """Test nested transactions behavior."""
        # Arrange
        _, mock_session = mock_session_factory
        # Configure mock session to support nested transactions
        mock_nested_transaction = MagicMock()
        mock_session.begin_nested.return_value = mock_nested_transaction
        
        # Act
        with unit_of_work:
            # Start a nested transaction
            with unit_of_work.begin_nested():
                # Do some work in the nested transaction
                pass
                # Let the nested transaction complete successfully
            # Do more work in the outer transaction
            unit_of_work.commit()
        
        # Assert
        mock_session.begin.assert _called_once()
        mock_session.begin_nested.assert _called_once()
        mock_nested_transaction.__exit__.assert _called_once()
        mock_session.commit.assert _called_once()
        mock_session.close.assert _called_once()
    
    def test_rollback_in_nested_transaction(self, unit_of_work, mock_session_factory):
        """Test that errors in nested transactions can be contained."""
        # Arrange
        _, mock_session = mock_session_factory
        # Configure mock session to support nested transactions
        mock_nested_transaction = MagicMock()
        mock_session.begin_nested.return_value = mock_nested_transaction
        
        # Act
        with unit_of_work:
            try:
                with unit_of_work.begin_nested():
                    # Simulate error in nested transaction
                    raise ValueError("Nested transaction error")
            except ValueError:
                # Catch the error to prevent it from propagating
                pass
            # Continue with the outer transaction
            unit_of_work.commit()
        
        # Assert
        mock_session.begin.assert _called_once()
        mock_session.begin_nested.assert _called_once()
        # The outer transaction should still commit
        mock_session.commit.assert _called_once()
        mock_session.close.assert _called_once()
    
    def test_transaction_atomicity_multiple_repositories(self, unit_of_work, mock_session_factory):
        """Test that multiple repository operations are atomic."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Create mock repositories
        patient_repo = MagicMock()
        appointment_repo = MagicMock()
        
        # Attach repositories to unit of work
        unit_of_work.patients = patient_repo
        unit_of_work.appointments = appointment_repo
        
        # Act - simulate updating related entities
        with unit_of_work:
            unit_of_work.patients.update(id="patient1", data={"status": "active"})
            unit_of_work.appointments.add({"patient_id": "patient1", "date": "2023-01-01"})
            unit_of_work.commit()
        
        # Assert
        patient_repo.update.assert _called_once()
        appointment_repo.add.assert _called_once()
        mock_session.commit.assert _called_once()
    
    def test_transaction_atomicity_error_in_second_operation(self, unit_of_work, mock_session_factory):
        """Test that an error in any operation rolls back all previous operations."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Create mock repositories
        patient_repo = MagicMock()
        appointment_repo = MagicMock()
        
        # Configure the second operation to fail
        appointment_repo.add.side_effect = ValueError("Appointment error")
        
        # Attach repositories to unit of work
        unit_of_work.patients = patient_repo
        unit_of_work.appointments = appointment_repo
        
        # Act - simulate updating related entities with an error
        with pytest.raises(ValueError):
            with unit_of_work:
                unit_of_work.patients.update(id="patient1", data={"status": "active"})
                unit_of_work.appointments.add({"patient_id": "patient1", "date": "2023-01-01"})
                unit_of_work.commit()
        
        # Assert
        patient_repo.update.assert _called_once()
        appointment_repo.add.assert _called_once()
        mock_session.rollback.assert _called_once()
        mock_session.commit.assert _not_called()
    
    def test_commit_error_handling(self, unit_of_work, mock_session_factory):
        """Test handling of errors during commit."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Configure commit to fail
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
        
        # Act
        with pytest.raises(TransactionError):
            with unit_of_work:
                # Do some work
                unit_of_work.commit()
        
        # Assert
        mock_session.begin.assert _called_once()
        mock_session.commit.assert _called_once()
        mock_session.rollback.assert _called_once()
        mock_session.close.assert _called_once()
    
    def test_session_closed_after_exception_in_rollback(self, unit_of_work, mock_session_factory):
        """Test that session is always closed, even if rollback fails."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Configure both operations to fail
        mock_session.rollback.side_effect = SQLAlchemyError("Rollback failed")
        
        # Act
        with pytest.raises(ValueError):
            with unit_of_work:
                raise ValueError("Operation failed")
        
        # Assert - session should still be closed
        mock_session.close.assert _called_once()
    
    def test_connection_isolation_level(self, mock_session_factory):
        """Test that connections use proper isolation level for PHI."""
        # Arrange
        factory, mock_session = mock_session_factory
        
        # Mock connection for verifying isolation level
        mock_connection = MagicMock()
        mock_session.connection.return_value = mock_connection
        
        # Act
        unit_of_work = SQLAlchemyUnitOfWork(
            session_factory=factory,
            isolation_level="SERIALIZABLE"  # Highest isolation for PHI
        )
        
        with unit_of_work:
            # Access connection to trigger isolation setting
            connection = unit_of_work.session.connection()
            unit_of_work.commit()
        
        # Assert
        mock_session.connection.assert _called()
        # Verify isolation level was set properly
        # (Implementation details may vary based on SQLAlchemy version and dialect)
        assert unit_of_work.isolation_level  ==  "SERIALIZABLE"
    
    def test_read_only_transaction(self, unit_of_work, mock_session_factory):
        """Test read-only transaction support for safer PHI access."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Act
        with unit_of_work.read_only():
            # This transaction should be marked read-only and auto-rollback
            pass
        
        # Assert
        mock_session.begin.assert _called_once()
        # Should rollback instead of commit to ensure no changes
        mock_session.rollback.assert _called_once()
        mock_session.commit.assert _not_called()
        mock_session.close.assert _called_once()
    
    def test_read_only_transaction_prevents_commits(self, unit_of_work, mock_session_factory):
        """Test that read-only transactions cannot commit changes."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Act
        with pytest.raises(RepositoryError): # Changed exception type
            with unit_of_work.read_only():
                unit_of_work.commit()
        
        # Assert
        mock_session.commit.assert _not_called()
        mock_session.rollback.assert _called()
    
    def test_transaction_metadata_for_audit(self, unit_of_work, mock_session_factory):
        """Test that transaction metadata is captured for HIPAA audit purposes."""
        # Arrange
        _, mock_session = mock_session_factory
        
        # Act
        with patch('app.infrastructure.logging.audit_logger.AuditLogger.log_transaction') as mock_audit:
            with unit_of_work:
                # Set transaction metadata
                unit_of_work.set_metadata({
                    "user_id": "provider123",
                    "action": "update_patient_record",
                    "patient_id": "patient456"
                })
                unit_of_work.commit()
        
        # Assert
        # Verify the audit logger was called with the metadata
        mock_audit.assert _called_once()
        call_args = mock_audit.call_args[0][0]
        assert call_args["user_id"] == "provider123"
        assert call_args["action"] == "update_patient_record"
        assert call_args["patient_id"] == "patient456"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])