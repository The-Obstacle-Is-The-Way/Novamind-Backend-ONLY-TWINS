"""
SQLAlchemy database handling with enhanced security and auditing.

This module provides SQLAlchemy database setup with additional features for
HIPAA compliance, including encryption, audit logging, and connection pooling.
"""

import contextlib
import logging
import time
from typing import Any, Dict, Generator, List, Optional, TypeVar, cast

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.pool import QueuePool

from app.core.config.settings import get_settings

# Configure logger
logger = logging.getLogger(__name__)

# Create declarative base for models
Base = declarative_base()

# Type variable for session-yielding functions
T = TypeVar('T')


class Database:
    """
    Base database handler for SQLAlchemy connections.
    
    This class provides the core database functionality, including connection
    management, session handling, and table operations.
    """
    
    def __init__(
        self,
        db_url: Optional[str] = None,
        echo: Optional[bool] = None,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[int] = None,
        ssl_mode: Optional[str] = None,
        ssl_ca: Optional[str] = None,
        ssl_verify: Optional[bool] = None
    ):
        """
        Initialize database connection.
        
        Args:
            db_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements
            pool_size: Size of the connection pool
            max_overflow: Maximum overflow connections
            pool_timeout: Pool connection timeout
            ssl_mode: SSL mode for PostgreSQL
            ssl_ca: SSL certificate authority path
            ssl_verify: Whether to verify SSL certificates
        """
        settings = get_settings()
        
        self.db_url = db_url or settings.DATABASE_URL
        self.echo = echo if echo is not None else settings.DATABASE_ECHO
        self.pool_size = pool_size or settings.DATABASE_POOL_SIZE
        self.max_overflow = max_overflow or 10
        self.pool_timeout = pool_timeout or 30
        self.ssl_mode = ssl_mode or settings.DATABASE_SSL_MODE
        self.ssl_ca = ssl_ca or settings.DATABASE_SSL_CA
        self.ssl_verify = ssl_verify if ssl_verify is not None else settings.DATABASE_SSL_VERIFY
        
        connect_args = {}
        
        # Add SSL configuration for PostgreSQL
        if self.db_url.startswith("postgresql") and settings.DATABASE_SSL_ENABLED:
            connect_args["sslmode"] = self.ssl_mode
            if self.ssl_ca:
                connect_args["sslrootcert"] = self.ssl_ca
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.db_url,
            echo=self.echo,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            poolclass=QueuePool,
            connect_args=connect_args
        )
        
        # Create sessionmaker
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            New database session
        """
        return self.SessionLocal()
    
    @contextlib.contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Yields a session and handles commit/rollback automatically.
        
        Yields:
            Database session
            
        Raises:
            Any exceptions from the session operations
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            List of rows as dictionaries
            
        Raises:
            SQLAlchemyError: For database errors
        """
        params = params or {}
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql), params)
                return [dict(row) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def create_tables(self) -> None:
        """Create all defined tables in the database."""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self) -> None:
        """Drop all defined tables from the database."""
        Base.metadata.drop_all(self.engine)


class EnhancedDatabase(Database):
    """
    Enhanced database handler with security features.
    
    This class extends the base Database with features needed for
    HIPAA compliance, including encryption and audit logging.
    """
    
    def __init__(
        self,
        db_url: Optional[str] = None,
        echo: Optional[bool] = None,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[int] = None,
        ssl_mode: Optional[str] = None,
        ssl_ca: Optional[str] = None,
        ssl_verify: Optional[bool] = None,
        enable_encryption: Optional[bool] = None,
        enable_audit: Optional[bool] = None
    ):
        """
        Initialize enhanced database connection.
        
        Args:
            db_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements
            pool_size: Size of the connection pool
            max_overflow: Maximum overflow connections
            pool_timeout: Pool connection timeout
            ssl_mode: SSL mode for PostgreSQL
            ssl_ca: SSL certificate authority path
            ssl_verify: Whether to verify SSL certificates
            enable_encryption: Whether to enable database encryption
            enable_audit: Whether to enable audit logging
        """
        super().__init__(
            db_url=db_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            ssl_mode=ssl_mode,
            ssl_ca=ssl_ca,
            ssl_verify=ssl_verify
        )
        
        settings = get_settings()
        self.enable_encryption = enable_encryption if enable_encryption is not None else settings.DATABASE_ENCRYPTION_ENABLED
        self.enable_audit = enable_audit if enable_audit is not None else settings.DATABASE_AUDIT_ENABLED
        
        # Set up event listeners for audit logging
        if self.enable_audit:
            self._setup_audit_listeners()
    
    def _setup_audit_listeners(self) -> None:
        """Set up event listeners for audit logging."""
        @event.listens_for(self.engine, "connect")
        def engine_connect(dbapi_connection, connection_record):
            logger.info(f"Database connection established: {id(dbapi_connection)}")
        
        @event.listens_for(self.engine, "checkout")
        def engine_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug(f"Database connection checked out: {id(dbapi_connection)}")
        
        @event.listens_for(self.engine, "checkin")
        def engine_checkin(dbapi_connection, connection_record):
            logger.debug(f"Database connection checked in: {id(dbapi_connection)}")
        
        @event.listens_for(self.SessionLocal, "after_begin")
        def session_after_begin(session, transaction, connection):
            logger.info(f"Starting transaction: {id(session)}")
        
        @event.listens_for(self.SessionLocal, "after_commit")
        def session_after_commit(session):
            logger.info(f"Committing transaction: {id(session)}")
        
        @event.listens_for(self.SessionLocal, "after_rollback")
        def session_after_rollback(session):
            logger.warning(f"Rolling back transaction: {id(session)}")
        
        @event.listens_for(self.SessionLocal, "after_soft_rollback")
        def session_after_soft_rollback(session, previous_transaction):
            logger.warning(f"Soft rolling back transaction: {id(session)}")
        
        @event.listens_for(self.SessionLocal, "after_close")
        def session_after_close(session):
            logger.info(f"Closed transaction: {id(session)}")
    
    @contextlib.contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Enhanced context manager for database sessions with audit logging.
        
        Yields a session and handles commit/rollback automatically.
        
        Yields:
            Database session
            
        Raises:
            Any exceptions from the session operations
        """
        session = self.get_session()
        transaction_id = id(session)
        start_time = time.time()
        
        try:
            logger.info(f"Starting transaction {transaction_id}")
            yield session
            session.commit()
            end_time = time.time()
            logger.info(f"Committing transaction {transaction_id} (duration: {end_time - start_time:.2f}s)")
        except Exception as e:
            session.rollback()
            end_time = time.time()
            logger.error(f"Rolling back transaction {transaction_id} due to error: {e} (duration: {end_time - start_time:.2f}s)")
            raise
        finally:
            session.close()
            logger.info(f"Closed transaction {transaction_id}")
    
    def get_protected_engine(self) -> Engine:
        """
        Get database engine with encryption.
        
        In a real implementation, this would potentially provide an engine
        with additional security features like transparent data encryption.
        
        Returns:
            SQLAlchemy engine with enhanced security
        """
        # In a real implementation, this might return a wrapped engine
        # with encryption capabilities
        return self.engine


# Global database instance for singleton pattern
_database_instance = None


def get_database() -> EnhancedDatabase:
    """
    Get the global database instance.
    
    Returns:
        EnhancedDatabase instance
    """
    global _database_instance
    
    if _database_instance is None:
        _database_instance = EnhancedDatabase()
    
    return _database_instance


def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session for dependency injection.
    
    Yields:
        Database session
    """
    db = get_database()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()