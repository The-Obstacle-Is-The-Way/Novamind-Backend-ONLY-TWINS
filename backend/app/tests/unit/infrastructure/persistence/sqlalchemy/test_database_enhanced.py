"""Unit tests for the enhanced SQLAlchemy database module."""
import pytest
from unittest.mock import patch, MagicMock, call
import logging
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming Base is correctly defined elsewhere or use declarative_base
Base = declarative_base()

# Correct import - Assuming these are the intended imports
from app.infrastructure.persistence.sqlalchemy.database import (
    Database,
    EnhancedDatabase,
    get_database,
    get_db_session,
    _database_instance # Import for resetting in tests if necessary
)
from app.config.settings import get_settings


# Define a test model for database operations
class TestModel(Base):
    """Test model for database operations."""
    __tablename__ = "test_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    value = Column(String(100), nullable=True)

@pytest.fixture(scope="module")
def mock_settings_module():
    """Mock application settings for the module."""
    settings = MagicMock()
    settings.DATABASE_URL = "sqlite:///:memory:"
    settings.DATABASE_ECHO = False
    settings.DATABASE_POOL_SIZE = 5
    settings.DATABASE_SSL_ENABLED = False
    settings.DATABASE_ENCRYPTION_ENABLED = True # Example setting
    settings.DATABASE_AUDIT_ENABLED = True # Example setting
    with patch("app.infrastructure.persistence.sqlalchemy.database.get_settings", return_value=settings):
        yield settings

@pytest.fixture(scope="function") # Use function scope for isolation
def in_memory_db(mock_settings_module):
    """Create an in-memory SQLite database."""
    # Use the mocked settings URL
    db = Database(db_url=mock_settings_module.DATABASE_URL)
    Base.metadata.create_all(db.engine)
    yield db
    Base.metadata.drop_all(db.engine)
    db.engine.dispose() # Dispose engine after test

@pytest.fixture(scope="function") # Use function scope for isolation
def enhanced_db(mock_settings_module):
    """Create an enhanced in-memory SQLite database."""
    # Use the mocked settings URL and enable features explicitly for testing
    db = EnhancedDatabase(
        db_url=mock_settings_module.DATABASE_URL,
        enable_encryption=True,
        enable_audit=True
    )
    Base.metadata.create_all(db.engine)
    yield db
    Base.metadata.drop_all(db.engine)
    db.engine.dispose() # Dispose engine after test

class TestDatabase:
    """Tests for the base Database class."""

    def test_init(self, mock_settings_module):
        """Test database initialization."""
        # Use mocked settings for initialization test
        db = Database(db_url=mock_settings_module.DATABASE_URL, echo=False, pool_size=5)

        assert db.db_url == mock_settings_module.DATABASE_URL
        assert db.echo is False
        assert db.pool_size == 5
        assert db.engine is not None
        assert db.SessionLocal is not None

    def test_get_session(self, in_memory_db):
        """Test getting a database session."""
        session = None
        try:
            session = in_memory_db.get_session()
            assert isinstance(session, Session)
        finally:
            if session:
                session.close()

    def test_create_tables(self, in_memory_db):
        """Test creating database tables."""
        # Tables are created in the fixture. Verify by inserting data.
        with in_memory_db.session_scope() as session:
            test_model = TestModel(name="test_create", value="created")
            session.add(test_model)
            session.commit() # Commit needed to save

        # Verify the record exists
        with in_memory_db.session_scope() as session:
            result = session.query(TestModel).filter_by(name="test_create").first()
            assert result is not None
            assert result.name == "test_create"
            assert result.value == "created"

    def test_drop_tables(self, in_memory_db):
        """Test dropping database tables."""
        # Insert a test record
        with in_memory_db.session_scope() as session:
            test_model = TestModel(name="test_drop", value="to_be_dropped")
            session.add(test_model)
            session.commit()

        # Drop tables
        in_memory_db.drop_tables()

        # Attempt to query - should fail if tables are dropped
        with pytest.raises(SQLAlchemyError): # Expect an error (e.g., NoSuchTableError)
             with in_memory_db.session_scope() as session:
                 session.query(TestModel).first()

        # Re-create tables for subsequent tests if needed (handled by fixture scope)
        # in_memory_db.create_tables()


    def test_session_scope(self, in_memory_db):
        """Test session scope context manager."""
        # Use context manager to add a record
        with in_memory_db.session_scope() as session:
            test_model = TestModel(name="test_scope", value="context_manager")
            session.add(test_model)
            # Commit happens automatically on exit if no exception

        # Verify record was committed
        with in_memory_db.session_scope() as session:
            result = session.query(TestModel).filter_by(name="test_scope").first()
            assert result is not None
            assert result.value == "context_manager"

    def test_session_scope_rollback(self, in_memory_db):
        """Test session scope rollback on exception."""
        try:
            with in_memory_db.session_scope() as session:
                test_model = TestModel(name="should_rollback", value="value")
                session.add(test_model)
                raise ValueError("Test exception") # Force rollback
        except ValueError:
            pass # Expected exception

        # Verify record was not committed
        with in_memory_db.session_scope() as session:
            result = session.query(TestModel).filter_by(name="should_rollback").first()
            assert result is None

    @patch("app.infrastructure.persistence.sqlalchemy.database.logger")
    def test_execute_query(self, mock_logger, in_memory_db):
        """Test executing a raw SQL query."""
        # Insert test data
        with in_memory_db.session_scope() as session:
            test_model = TestModel(name="query_test", value="raw_sql")
            session.add(test_model)
            session.commit()

        # Execute raw query using text() for parameter binding
        results = in_memory_db.execute_query(
            text("SELECT * FROM test_models WHERE name = :name"), {"name": "query_test"}
        )

        assert len(results) == 1
        # Access by index or key depending on execute_query implementation
        # Assuming it returns dict-like rows or RowProxy
        assert results[0].name == "query_test"
        assert results[0].value == "raw_sql"
        # mock_logger.debug.assert_called() # Verify logging if implemented

class TestEnhancedDatabase:
    """Tests for the EnhancedDatabase class."""

    def test_init(self, mock_settings_module):
        """Test enhanced database initialization."""
        db = EnhancedDatabase(
            db_url=mock_settings_module.DATABASE_URL,
            enable_encryption=True,
            enable_audit=True
        )

        assert db.db_url == mock_settings_module.DATABASE_URL
        assert db.echo is False # Assuming default or from settings
        assert db.pool_size == 5 # Assuming default or from settings
        assert db.enable_encryption is True
        assert db.enable_audit is True
        assert db.engine is not None

    @patch("app.infrastructure.persistence.sqlalchemy.database.logger")
    def test_session_scope_with_audit(self, mock_logger, enhanced_db):
        """Test session scope with audit logging."""
        with enhanced_db.session_scope() as session:
            test_model = TestModel(name="audit_test", value="logged")
            session.add(test_model)
            # Commit happens automatically

        # Verify audit logging calls (adjust count based on implementation)
        assert mock_logger.info.call_count >= 2 # Start, Commit/Close
        log_calls = [c.args[0] for c in mock_logger.info.call_args_list]
        assert any("Starting transaction" in log for log in log_calls)
        # assert any("Committing transaction" in log for log in log_calls) # Might be debug
        assert any("Closing session" in log for log in log_calls) # Or similar message

    @patch("app.infrastructure.persistence.sqlalchemy.database.logger")
    def test_session_scope_rollback_with_audit(self, mock_logger, enhanced_db):
        """Test session scope rollback with audit logging."""
        try:
            with enhanced_db.session_scope() as session:
                test_model = TestModel(name="audit_rollback", value="should_log")
                session.add(test_model)
                raise ValueError("Test exception")
        except ValueError:
            pass # Expected

        # Verify error logging
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Rolling back transaction" in error_msg # Or similar message
        assert "ValueError" in error_msg # Check if exception type is logged

    def test_get_protected_engine(self, enhanced_db):
        """Test getting a protected database engine (if implemented differently)."""
        protected_engine = enhanced_db.get_protected_engine()
        # If it's just returning the same engine:
        assert protected_engine is enhanced_db.engine
        # If it returns a proxy or different object, add specific tests here.

class TestDatabaseFactory:
    """Tests for the database factory functions."""

    @patch("app.infrastructure.persistence.sqlalchemy.database._database_instance", None) # Reset singleton
    @patch("app.infrastructure.persistence.sqlalchemy.database.EnhancedDatabase") # Mock the class
    def test_get_database(self, mock_enhanced_db_class, mock_settings_module):
        """Test get_database function creates singleton EnhancedDatabase."""
        # Mock get_settings used within get_database
        with patch("app.infrastructure.persistence.sqlalchemy.database.get_settings", return_value=mock_settings_module):
            db1 = get_database()
            # Assert EnhancedDatabase was called with settings
            mock_enhanced_db_class.assert_called_once_with(
                db_url=mock_settings_module.DATABASE_URL,
                echo=mock_settings_module.DATABASE_ECHO,
                pool_size=mock_settings_module.DATABASE_POOL_SIZE,
                ssl_args=None, # Assuming default or based on settings
                enable_encryption=mock_settings_module.DATABASE_ENCRYPTION_ENABLED,
                enable_audit=mock_settings_module.DATABASE_AUDIT_ENABLED
            )
            assert isinstance(db1, MagicMock) # It's the mocked instance

            # Call again to test singleton behavior
            db2 = get_database()
            assert db1 is db2  # Should be the same instance (the mocked one)
            # Ensure EnhancedDatabase is called only once
            mock_enhanced_db_class.assert_called_once()


    @patch("app.infrastructure.persistence.sqlalchemy.database.get_database")
    def test_get_db_session(self, mock_get_database, mock_settings_module):
        """Test get_db_session dependency injection function."""
        # Mock the database instance returned by get_database
        mock_db_instance = MagicMock(spec=EnhancedDatabase)
        mock_session = MagicMock(spec=Session)
        # Mock the session_scope context manager
        mock_db_instance.session_scope.return_value.__enter__.return_value = mock_session
        mock_get_database.return_value = mock_db_instance

        # Create a generator from the function
        session_gen = get_db_session()

        # Get the session from the generator
        retrieved_session = next(session_gen)
        assert retrieved_session is mock_session # Should be the mocked session
        mock_db_instance.session_scope.assert_called_once() # Verify session_scope was entered

        # Simulate closing the session by exhausting the generator
        with pytest.raises(StopIteration):
            next(session_gen)
        # Verify the context manager exit was called (which should close the session)
        mock_db_instance.session_scope.return_value.__exit__.assert_called_once()
