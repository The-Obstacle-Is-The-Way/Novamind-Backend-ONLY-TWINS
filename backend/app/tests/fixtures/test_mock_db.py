"""
Tests for the MockAsyncSession fixture.
"""
import pytest
from sqlalchemy import select
from uuid import uuid4

from app.tests.fixtures.mock_db_fixture import MockAsyncSession


class TestMockAsyncSession:
    """Test cases for the MockAsyncSession class."""

    @pytest.fixture
    @pytest.mark.asyncio
    @pytest.mark.db_required
    def mock_db(self):
        """Provides a mock async database session."""
        return MockAsyncSession()

        @pytest.mark.asyncio
        async def test_mock_session_basic_operations(self, mock_db):
        """Test that basic CRUD operations work with MockAsyncSession."""
        # Setup test entity
        test_entity = object()  # Use standard object for mock testing
        test_entity.id = uuid4()

        # Test add
        mock_db.add(test_entity)
        assert test_entity in mock_db._pending_objects

        # Test commit
        await mock_db.commit()
        assert test_entity in mock_db._committed_objects
        assert not mock_db._pending_objects

        # Test execution of a query
        # For mock testing, we can simulate query execution without a real query object
        query = "mock_query"
        mock_db._query_results = [test_entity]  # Set expected result

        result = await mock_db.execute(query)
        fetched_entity = result.scalars().first()

        assert fetched_entity == test_entity
        assert mock_db._last_executed_query is not None

        # Test rollback
        mock_db.add(object())  # Add another entity
        assert len(mock_db._pending_objects) == 1

        await mock_db.rollback()
        assert not mock_db._pending_objects

        @pytest.mark.asyncio
        @pytest.mark.db_required
        async def test_mock_session_refresh(self, mock_db):
        """Test the refresh operation."""
        test_entity = object()  # Use standard object
        test_entity.id = uuid4()

        # Add and commit entity
        mock_db.add(test_entity)
        await mock_db.commit()

        # Refresh entity - should not raise any exception
        await mock_db.refresh(test_entity)

        # Verify entity is still tracked
        assert test_entity in mock_db._committed_objects

        @pytest.mark.asyncio
        @pytest.mark.db_required
        async def test_mock_session_delete(self, mock_db):
        """Test the delete operation."""
        test_entity = object()  # Use standard object
        test_entity.id = uuid4()

        # Add and commit entity
        mock_db.add(test_entity)
        await mock_db.commit()

        # Delete entity
        mock_db.delete(test_entity)
        assert test_entity in mock_db._deleted_objects

        # Commit deletion
        await mock_db.commit()
        assert test_entity not in mock_db._committed_objects
        assert not mock_db._deleted_objects

        @pytest.mark.asyncio
        @pytest.mark.db_required
        async def test_mock_session_close(self, mock_db):
        """Test the close operation."""
        test_entity = object()  # Use standard object
        mock_db.add(test_entity)

        # Close session
        await mock_db.close()

        # Session should be cleared
        assert not mock_db._pending_objects
        assert not mock_db._committed_objects
        assert not mock_db._deleted_objects
        assert mock_db._closed
