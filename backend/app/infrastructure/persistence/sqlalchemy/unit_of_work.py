# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Unit of Work Pattern

This module implements the Unit of Work pattern for database transactions,
ensuring HIPAA-compliant atomicity and integrity for all PHI-related operations.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

T = TypeVar("T")


class SQLAlchemyUnitOfWork:
    """
    Unit of Work implementation for SQLAlchemy to ensure HIPAA-compliant
    transaction safety for PHI data.

    This class provides a context manager for database transactions, ensuring
    that all operations within a transaction succeed or fail together, preventing
    partial updates that could compromise data integrity.
    """

    def __init__(self, session_factory: Optional[Callable[[], Session]] = None):
        """
        Initialize the Unit of Work with a session factory.

        Args:
            session_factory: Factory function for creating SQLAlchemy sessions
        """
        self.settings = settings
        self.session_factory = session_factory or self._create_session_factory()
        self.session: Optional[Session] = None
        self.logger = logging.getLogger(__name__)

    def _create_session_factory(self) -> Callable[[], Session]:
        """
        Create a SQLAlchemy session factory from settings.

        Returns:
            Callable: A function that creates a new SQLAlchemy session
        """
        engine = create_engine(
            self.settings.SQLALCHEMY_DATABASE_URI,
            echo=False,  # Never echo SQL in production to avoid PHI leakage
            pool_pre_ping=True,  # Check connection validity before using
            pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
        )
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def __enter__(self):
        """
        Enter the context manager, creating a new session.

        Returns:
            SQLAlchemyUnitOfWork: Self reference for context manager
        """
        self.session = self.session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager, committing or rolling back the transaction.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        if self.session is None:
            return

        try:
            if exc_type is not None:
                # An exception occurred, roll back the transaction
                self.rollback()
            else:
                # No exception, commit the transaction
                self.commit()
        finally:
            # Always close the session
            self.session.close()
            self.session = None

    def commit(self):
        """
        Commit the current transaction.

        Raises:
            ValueError: If no active session exists
        """
        if self.session is None:
            raise ValueError("Cannot commit - no active session")

        try:
            self.session.commit()
            self.logger.debug("Transaction committed successfully")
        except SQLAlchemyError as e:
            self.logger.error(f"Error committing transaction: {type(e).__name__}")
            self.rollback()
            raise

    def rollback(self):
        """
        Roll back the current transaction.

        Raises:
            ValueError: If no active session exists
        """
        if self.session is None:
            raise ValueError("Cannot rollback - no active session")

        try:
            self.session.rollback()
            self.logger.debug("Transaction rolled back")
        except SQLAlchemyError as e:
            self.logger.error(f"Error rolling back transaction: {type(e).__name__}")
            raise


@dataclass
class RepositoryFactory(Generic[T]):
    """
    Factory for creating repositories with a session.

    This class enables dependency injection of repositories, ensuring
    all repositories share the same transaction context when used within
    a Unit of Work.
    """

    unit_of_work: SQLAlchemyUnitOfWork
    repository_class: Type[T]

    def __call__(self) -> T:
        """
        Create a repository instance with the current session.

        Returns:
            T: A repository instance

        Raises:
            ValueError: If the Unit of Work has no active session
        """
        if self.unit_of_work.session is None:
            raise ValueError(
                "Cannot create repository - Unit of Work has no active session. "
                "Make sure you're using the Unit of Work as a context manager."
            )

        return self.repository_class(self.unit_of_work.session)


@contextmanager
def unit_of_work(session_factory: Optional[Callable[[], Session]] = None):
    """
    Context manager for a database unit of work with PHI safeguards.

    Args:
        session_factory: Optional factory function for creating SQLAlchemy sessions

    Yields:
        SQLAlchemyUnitOfWork: The unit of work instance
    """
    uow = SQLAlchemyUnitOfWork(session_factory)
    try:
        with uow:
            yield uow
    except Exception as e:
        # Log the exception type but not details to avoid PHI exposure
        logging.getLogger(__name__).error(f"Transaction failed: {type(e).__name__}")
        raise


def get_unit_of_work() -> SQLAlchemyUnitOfWork:
    """
    Factory function to get a Unit of Work instance.

    Returns:
        SQLAlchemyUnitOfWork: A new Unit of Work instance
    """
    return SQLAlchemyUnitOfWork()


def get_repository_factory(repository_class: Type[T]) -> Callable[[], T]:
    """
    Factory function for creating repository factories.

    This function is used with FastAPI dependency injection to provide
    repositories with the current Unit of Work.

    Args:
        repository_class: The repository class to create

    Returns:
        Callable: A factory function for creating repository instances
    """

    def _create_repository(uow: SQLAlchemyUnitOfWork = get_unit_of_work()):
        return RepositoryFactory(uow, repository_class)()

    return _create_repository
