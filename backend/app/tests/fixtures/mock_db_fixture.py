# -*- coding: utf-8 -*-
"""
Mock Database Fixtures for Testing

This module provides Mock Database fixtures to allow tests to run without
requiring an actual PostgreSQL database connection, while still providing
all necessary functionality for test cases.
"""

import pytest
import pytest_asyncio
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Type
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession


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
