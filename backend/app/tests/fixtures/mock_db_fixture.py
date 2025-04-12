"""
Mock Database Fixtures for Testing

This module provides Mock Database fixtures to allow tests to run without
requiring an actual PostgreSQL database connection, while still providing
all necessary functionality for test cases.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
class MockAsyncSession(MagicMock):
    """Mock AsyncSession for testing without actual database dependencies."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track session state
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.flushed = False
        
        # Track operations for assertions
        self.refreshed_objects = []
        self.executed_queries = []
        self.query_results = {}
        self.added_objects = []
        self.deleted_objects = []
        self._transaction_active = False
        self._entity_registry = {}  # For get() operations

        # Set up async context manager methods
        self.__aenter__ = AsyncMock(return_value=self)
        self.__aexit__ = AsyncMock(return_value=None)
        
        # Set up async methods
        self.commit = AsyncMock(side_effect=self._commit)
        self.rollback = AsyncMock(side_effect=self._rollback)
        self.close = AsyncMock(side_effect=self._close)
        self.flush = AsyncMock(side_effect=self._flush)
        self.refresh = AsyncMock(side_effect=self._refresh)
        self.execute = AsyncMock(side_effect=self._execute)
        self.scalars = AsyncMock(side_effect=self._scalars)
        
    async def _commit(self, *args, **kwargs):
        """Mock implementation of commit."""
        self.committed = True
        self._transaction_active = False
        return None
        
    async def _rollback(self, *args, **kwargs):
        """Mock implementation of rollback."""
        self.rolled_back = True
        self._transaction_active = False
        return None
        
    async def _close(self, *args, **kwargs):
        """Mock implementation of close."""
        self.closed = True
        return None
        
    async def _flush(self, *args, **kwargs):
        """Mock implementation of flush."""
        self.flushed = True
        return None
    
    async def _refresh(self, obj, *args, **kwargs):
        """Mock implementation of refresh."""
        self.refreshed_objects.append(obj)
        return None
    
    async def _execute(self, query, *args, **kwargs):
        """Mock implementation of execute."""
        query_str = str(query)
        self.executed_queries.append(query_str)
        
        # Return result based on query type
        if query_str.lower().startswith("select"):
            return MagicMock() # Configured with scalars and mappings methods
        elif query_str.lower().startswith("insert"):
            return MagicMock(rowcount=1)
        elif query_str.lower().startswith("update"):
            return MagicMock(rowcount=1)
        elif query_str.lower().startswith("delete"):
            return MagicMock(rowcount=1)
        else:
            return MagicMock()
    
    async def _scalars(self, result, *args, **kwargs):
        """Mock implementation of scalars."""
        # Create a mock that can be used with first(), all(), etc.
        mock_scalar_result = MagicMock()
        mock_scalar_result.first = MagicMock(return_value=None)  # Default to None
        mock_scalar_result.all = MagicMock(return_value=[])  # Default to empty list
        
        # Can be configured in test to return specific values
        query_str = str(result.query) if hasattr(result, 'query') else "unknown_query"
        if query_str in self.query_results:
            result_value = self.query_results[query_str]
            if isinstance(result_value, list):
                mock_scalar_result.all = MagicMock(return_value=result_value)
                mock_scalar_result.first = MagicMock(return_value=result_value[0] if result_value else None)
            else:
                mock_scalar_result.first = MagicMock(return_value=result_value)
                mock_scalar_result.all = MagicMock(return_value=[result_value] if result_value else [])
        return mock_scalar_result
    def add(self, obj):
        """Mock implementation of add."""
        self.added_objects.append(obj)
        # Store in entity registry for future get() operations
        if hasattr(obj, 'id'):
            self._entity_registry[obj.id] = obj
    def delete(self, obj):
        """Mock implementation of delete."""
        self.deleted_objects.append(obj)
        # Remove from entity registry
        if hasattr(obj, 'id') and obj.id in self._entity_registry:
            del self._entity_registry[obj.id]
    def get(self, model_class, object_id):
        """Mock implementation of get."""
        
        return self._entity_registry.get(object_id)
    def configure_mock_results(self, query: str, results: Any):
        """
        Configure the mock to return specific results for a query.

        Args:
            query: Query string or identifier
            results: Results to return (single object or list)
        """
        self.query_results[query] = results


@pytest_asyncio.fixture
async def mock_db_session():
    """
    Fixture that provides a mock database session for testing.

    This fixture creates and returns a configured MockAsyncSession
    that can be used in place of a real database session.

    Returns:
        MockAsyncSession: A configured mock database session
    """
    session = MockAsyncSession()
    yield session
@pytest.fixture
def mock_db_fixture():
    """
    Fixture that provides both a mock session and utility functions.

    Returns:
        tuple: A tuple containing (session, configure_mock) where
        session is a MockAsyncSession and configure_mock is a
        function to configure the session with mock results
    """
    session = MockAsyncSession()
    def configure_mock(query: str, results: Any):
        """Configure the mock session to return specific results for a query."""
        session.configure_mock_results(query, results)
        return session, configure_mock
class MockRepository:
    """Base repository mock for testing repository pattern implementations."""
    def __init__(self, session=None):
        """Initialize with an optional mock session."""
        self.session = session or MockAsyncSession()
        self.entities = {}  # In-memory store
    
    async def add(self, entity):
        """Mock adding an entity."""
        if hasattr(entity, 'id'):
            self.entities[entity.id] = entity
        return entity
    
    async def get(self, entity_id):
        """Mock retrieving an entity by ID."""
        
        return self.entities.get(entity_id)
    
    async def get_all(self):
        """Mock retrieving all entities."""
        
        return list(self.entities.values())
    
    async def update(self, entity):
        """Mock updating an entity."""
        if hasattr(entity, 'id') and entity.id in self.entities:
            self.entities[entity.id] = entity
        return entity
    
    async def delete(self, entity_id):
        """Mock deleting an entity."""
        if entity_id in self.entities:
            del self.entities[entity_id]
        return True
        return False
    def configure_mock_get(self, entity_id, entity):
        """Configure the mock to return a specific entity for get()."""
        self.entities[entity_id] = entity
    def configure_mock_get_all(self, entities):
        """Configure the mock to return specific entities for get_all()."""
        self.entities = {
            entity.id: entity for entity in entities
            if hasattr(entity, 'id')
        }
@pytest.fixture
def mock_repository():
    """
    Fixture that provides a mock repository for testing.

    Returns:
        MockRepository: A configured mock repository
    """
    
    return MockRepository()