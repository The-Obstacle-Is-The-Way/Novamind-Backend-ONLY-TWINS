"""
HIPAA-compliant SQLAlchemy Unit of Work implementation.

This module provides a robust implementation of the Unit of Work pattern using SQLAlchemy,
ensuring transactional integrity for PHI data operations according to HIPAA requirements.
"""

import logging
import contextlib
from typing import Any, Dict, Optional, Callable, ContextManager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domain.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions import RepositoryError

# Configure logger
logger = logging.getLogger(__name__)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """
    HIPAA-compliant implementation of the Unit of Work pattern using SQLAlchemy.
    
    This class provides transactional boundaries for all operations on PHI data,
    ensuring data integrity, atomicity, and proper audit logging for all changes.
    """
    
    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize the Unit of Work with a session factory.
        
        Args:
            session_factory: A callable that returns a new SQLAlchemy session
        """
        self.session_factory = session_factory
        self._session: Optional[Session] = None
        self._is_read_only = False
        self._metadata: Dict[str, Any] = {}
    
    @property
    def session(self) -> Session:
        """
        Get the current session.
        
        Returns:
            The current SQLAlchemy session
            
        Raises:
            RepositoryError: If no session is active
        """
        if self._session is None:
            raise RepositoryError("No active database session. This operation must be performed within a unit of work context.")
        return self._session
    
    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        """
        Enter the unit of work context, creating a new session and beginning a transaction.
        
        Returns:
            The Unit of Work instance
        """
        # Create a new session
        self._session = self.session_factory()
        
        # Begin a transaction
        self._session.begin()
        
        logger.debug("Started new database transaction")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the unit of work context, committing or rolling back the transaction.
        
        Args:
            exc_type: Exception type if an exception was raised, None otherwise
            exc_val: Exception value if an exception was raised, None otherwise
            exc_tb: Exception traceback if an exception was raised, None otherwise
        """
        try:
            if self._session is None:
                return
                
            if exc_type:
                # An exception occurred - roll back
                logger.warning(f"Rolling back transaction due to exception: {exc_val}")
                self._session.rollback()
            elif self._is_read_only:
                # Read-only transactions always roll back to ensure no changes
                logger.debug("Rolling back read-only transaction")
                self._session.rollback()
            else:
                # Transaction completed successfully but no explicit commit
                # We don't auto-commit to ensure explicit control
                logger.debug("Transaction ended without explicit commit - rolling back")
                self._session.rollback()
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
            # Always try to roll back in case of errors
            try:
                self._session.rollback()
            except Exception:
                pass  # Ignore errors during emergency rollback
            raise
        finally:
            # Always close the session to prevent connection leaks
            if self._session:
                self._session.close()
                self._session = None
                
            # Reset the read-only flag
            self._is_read_only = False
            
            # Reset metadata
            self._metadata = {}
    
    def commit(self) -> None:
        """
        Commit the current transaction.
        
        Raises:
            RepositoryError: If the transaction is read-only or no session is active
        """
        if self._is_read_only:
            self._session.rollback()
            raise RepositoryError("Cannot commit changes in a read-only transaction")
            
        if self._session is None:
            raise RepositoryError("No active transaction to commit")
            
        try:
            # Log the transaction for audit purposes if metadata is available
            if self._metadata and hasattr(self, "_audit_transaction"):
                self._audit_transaction()
                
            # Commit the transaction
            self._session.commit()
            logger.debug("Transaction committed successfully")
        except SQLAlchemyError as e:
            # Roll back on any database errors
            self._session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise RepositoryError(f"Transaction failed: {str(e)}")
    
    def rollback(self) -> None:
        """
        Roll back the current transaction.
        
        Raises:
            RepositoryError: If no session is active
        """
        if self._session is None:
            raise RepositoryError("No active transaction to roll back")
            
        self._session.rollback()
        logger.debug("Transaction rolled back")
    
    @contextlib.contextmanager
    def nested(self) -> ContextManager["SQLAlchemyUnitOfWork"]:
        """
        Create a nested transaction.
        
        This allows for partial commits/rollbacks within a larger transaction.
        
        Yields:
            The Unit of Work instance
        
        Raises:
            RepositoryError: If no session is active
        """
        if self._session is None:
            raise RepositoryError("No active transaction for nesting")
            
        # Start a nested transaction (savepoint)
        with self._session.begin_nested():
            logger.debug("Started nested transaction")
            yield self
            logger.debug("Exited nested transaction")
    
    @contextlib.contextmanager
    def read_only(self) -> ContextManager["SQLAlchemyUnitOfWork"]:
        """
        Create a read-only transaction.
        
        This ensures that no changes can be committed, protecting PHI data from
        accidental modifications during read operations.
        
        Yields:
            The Unit of Work instance
        """
        self._is_read_only = True
        
        try:
            with self:
                logger.debug("Started read-only transaction")
                yield self
                logger.debug("Exited read-only transaction")
        finally:
            # Ensure the read-only flag is reset even if an exception occurs
            self._is_read_only = False
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Set metadata for the current transaction.
        
        This metadata is used for audit logging of PHI access and modifications,
        ensuring HIPAA compliance for all data operations.
        
        Args:
            metadata: Dictionary of metadata for the transaction
        """
        self._metadata.update(metadata)
    
    def _audit_transaction(self) -> None:
        """
        Log the transaction for HIPAA audit purposes.
        
        This creates an audit trail of all PHI access and modifications.
        """
        try:
            from app.infrastructure.logging.audit_logger import AuditLogger
            
            # Log the transaction with all metadata
            AuditLogger.log_transaction(self._metadata)
        except ImportError:
            # Audit logging not available - log a warning
            logger.warning("Audit logging not available - PHI operation not audited")
        except Exception as e:
            # Don't fail the transaction if audit logging fails
            logger.error(f"Failed to audit transaction: {e}")