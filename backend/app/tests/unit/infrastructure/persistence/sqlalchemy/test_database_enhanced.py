"""Unit tests for the enhanced SQLAlchemy database module."""
import pytest
from unittest.mock import patch, MagicMock, call
import logging
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.persistence.sqlalchemy.database import (
    Base,
    Database,
    EnhancedDatabase,
    get_database,
    get_db_session
)


# Define a test model for database operations
class TestModel(Base):
    """Test model for database operations."""
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    value = Column(String(100), nullable=True)


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch("app.infrastructure.persistence.sqlalchemy.database.get_settings") as mock:
        settings = MagicMock()
        settings.DATABASE_URL = "sqlite:///:memory:"
        settings.DATABASE_ECHO = False
        settings.DATABASE_POOL_SIZE = 5
        settings.DATABASE_SSL_ENABLED = False
        settings.DATABASE_ENCRYPTION_ENABLED = True
        settings.DATABASE_AUDIT_ENABLED = True
        mock.return_value = settings
        yield settings


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database."""
    db = Database(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db.engine)
    yield db
    Base.metadata.drop_all(db.engine)


@pytest.fixture
def enhanced_db():
    """Create an enhanced in-memory SQLite database."""
    db = EnhancedDatabase(
        db_url="sqlite:///:memory:",
        enable_encryption=True,
        enable_audit=True
    )
    Base.metadata.create_all(db.engine)
    yield db
    Base.metadata.drop_all(db.engine)


class TestDatabase:
    """Tests for the base Database class."""
    
    def test_init(self, mock_settings):
        """Test database initialization."""
        db = Database()
        
        assert db.db_url == mock_settings.DATABASE_URL
        assert db.echo == False
        assert db.pool_size == 5
        assert db.engine is not None
        assert db.SessionLocal is not None
    
    def test_get_session(self, in_memory_db):
        """Test getting a database session."""
        session = in_memory_db.get_session()
        
        assert isinstance(session, Session)
        session.close()
    
    def test_create_tables(self, in_memory_db):
        """Test creating database tables."""
        # Tables are already created in the fixture
        # This would normally fail if create_tables didn't work
        
        # Insert a test record to verify table exists
        with in_memory_db.session_scope() as session:
            test_model = TestModel(name="test", value="value")
            session.add(test_model)
        
        # Query to verify the record was inserted
        with in_memory_db.session_scope() as session:
            result = session.query(TestModel).filter_by(name="test").first()
            assert result is not None
            assert result.name == "test"
            assert result.value == "value"
    
    def test_drop_tables(self, in_memory_db):
        """Test dropping database tables."""
        # Insert a test record
        with in_memory_db.session_scope() as session:
            test_model = TestModel(name="test", value="value")
            session.add(test_model)
        
        # Drop tables
        in_memory_db.drop_tables()
        
        # Re-create tables to verify they were dropped
        in_memory_db.create_tables()
        
        # Query to verify no records exist
        with in_memory_db.session_scope() as session:
            result = session.query(TestModel).filter_by(name="test").first()
            assert result is None
    
    def test_session_scope(self, in_memory_db):
        """Test session scope context manager."""
        # Use context manager to add a record
        with in_memory_db.session_scope() as session:
            test_model = TestModel(name="test_scope", value="context_manager")
            session.add(test_model)
        
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
                raise ValueError("Test exception")
        except ValueError:
            pass
        
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
        
        # Execute raw query
        results = in_memory_db.execute_query(
            "SELECT * FROM test_models WHERE name = :name",
            {"name": "query_test"}
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "query_test"
        assert results[0]["value"] == "raw_sql"


class TestEnhancedDatabase:
    """Tests for the EnhancedDatabase class."""
    
    def test_init(self, mock_settings):
        """Test enhanced database initialization."""
        db = EnhancedDatabase()
        
        assert db.db_url == mock_settings.DATABASE_URL
        assert db.echo == False
        assert db.pool_size == 5
        assert db.enable_encryption == True
        assert db.enable_audit == True
        assert db.engine is not None
    
    @patch("app.infrastructure.persistence.sqlalchemy.database.logger")
    def test_session_scope_with_audit(self, mock_logger, enhanced_db):
        """Test session scope with audit logging."""
        with enhanced_db.session_scope() as session:
            test_model = TestModel(name="audit_test", value="logged")
            session.add(test_model)
        
        # Verify audit logging calls
        assert mock_logger.info.call_count >= 2
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Starting transaction" in log for log in log_calls)
        assert any("Committing transaction" in log for log in log_calls)
        assert any("Closed transaction" in log for log in log_calls)
    
    @patch("app.infrastructure.persistence.sqlalchemy.database.logger")
    def test_session_scope_rollback_with_audit(self, mock_logger, enhanced_db):
        """Test session scope rollback with audit logging."""
        try:
            with enhanced_db.session_scope() as session:
                test_model = TestModel(name="audit_rollback", value="should_log")
                session.add(test_model)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify error logging
        mock_logger.error.assert_called()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Rolling back" in error_msg
        assert "error" in error_msg.lower()
    
    def test_get_protected_engine(self, enhanced_db):
        """Test getting a protected database engine."""
        protected_engine = enhanced_db.get_protected_engine()
        
        # In our implementation, this currently returns the same engine
        assert protected_engine is enhanced_db.engine


class TestDatabaseFactory:
    """Tests for the database factory functions."""
    
    @patch("app.infrastructure.persistence.sqlalchemy.database._database_instance", None)
    def test_get_database(self, mock_settings):
        """Test get_database function."""
        db = get_database()
        
        assert isinstance(db, EnhancedDatabase)
        assert db.db_url == mock_settings.DATABASE_URL
        
        # Call again to test singleton behavior
        db2 = get_database()
        assert db is db2  # Should be the same instance
    
    def test_get_db_session(self, mock_settings):
        """Test get_db_session dependency injection function."""
        # Reset global instance
        from app.infrastructure.persistence.sqlalchemy.database import _database_instance
        _database_instance = None
        
        # Create a generator from the function
        session_gen = get_db_session()
        
        # Get the session from the generator
        session = next(session_gen)
        assert isinstance(session, Session)
        
        # Clean up
        try:
            next(session_gen)
        except StopIteration:
            pass
