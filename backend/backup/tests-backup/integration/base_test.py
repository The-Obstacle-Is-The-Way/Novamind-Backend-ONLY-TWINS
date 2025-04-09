"""
Base Integration Test Class

This module provides a base class for all integration tests in the application,
with a focus on testing API endpoints, database interactions, and full workflows.
"""

import unittest
import asyncio
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator, cast
import json
import logging
from unittest.mock import patch, MagicMock
from contextlib import contextmanager, asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import get_db


class BaseIntegrationTest(unittest.TestCase):
    """
    Base class for all integration tests.
    
    This class extends unittest.TestCase with enhanced integration testing
    capabilities, focusing on API endpoint testing, database interactions,
    and end-to-end workflows with proper transaction management.
    """
    
    app: FastAPI = None  # Will be set in setUpClass
    test_client: TestClient = None  # Will be set in setUpClass
    settings: Settings = None  # Will be set in setUpClass
    
    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level test fixtures."""
        super().setUpClass()
        
        # Import app here to avoid circular imports
        from app.main import app as fastapi_app
        from app.core.config import get_settings
        
        cls.app = fastapi_app
        cls.settings = get_settings()
        cls.test_client = TestClient(cls.app)
        
        # Set up test database
        cls._setup_test_db()
    
    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up class-level test fixtures."""
        # Clean up test database
        cls._teardown_test_db()
        
        super().tearDownClass()
    
    @classmethod
    def _setup_test_db(cls) -> None:
        """Set up test database."""
        # Create test database URL (in-memory SQLite for speed)
        cls.test_db_url = "sqlite+aiosqlite:///:memory:"
        
        # Create engine and session
        cls.engine = create_async_engine(cls.test_db_url, echo=False)
        cls.async_session_maker = sessionmaker(
            cls.engine, expire_on_commit=False, class_=AsyncSession
        )
        
        # Create all tables
        asyncio.run(cls._create_tables())
        
        # Override get_db dependency
        cls.original_get_db = get_db
        
        # Patch the get_db dependency
        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            async with cls.async_session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        
        cls.app.dependency_overrides[get_db] = override_get_db
    
    @classmethod
    async def _create_tables(cls) -> None:
        """Create all tables in the test database."""
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @classmethod
    def _teardown_test_db(cls) -> None:
        """Tear down test database."""
        # Remove the dependency override
        if hasattr(cls, 'original_get_db'):
            cls.app.dependency_overrides.pop(get_db, None)
        
        # Drop all tables
        asyncio.run(cls._drop_tables())
        
        # Close engine
        if hasattr(cls, 'engine'):
            asyncio.run(cls.engine.dispose())
    
    @classmethod
    async def _drop_tables(cls) -> None:
        """Drop all tables in the test database."""
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        super().setUp()
        # Create patch context managers
        self.patches = []
        self.mocks = {}
        
        # Create a new test transaction that will be rolled back after the test
        self.transaction_rollback = self._transaction_rollback_context()
        self.transaction_rollback.__enter__()
        
        # Suppress logs during tests
        logging.disable(logging.CRITICAL)
    
    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Roll back the test transaction
        if hasattr(self, 'transaction_rollback'):
            self.transaction_rollback.__exit__(None, None, None)
        
        # Stop all patches
        for patcher in self.patches:
            patcher.stop()
        
        # Clear mocks
        self.mocks.clear()
        
        # Re-enable logging
        logging.disable(logging.NOTSET)
        
        super().tearDown()
    
    @contextmanager
    def _transaction_rollback_context(self) -> Generator[None, None, None]:
        """Create a transaction context that will be rolled back after the test."""
        # SQLAlchemy transaction handling will be done by the test database setup
        try:
            yield
        finally:
            # No-op for SQLite in-memory, but would be needed for actual rollback
            # with production databases like PostgreSQL
            pass
    
    @asynccontextmanager
    async def async_client(self) -> AsyncGenerator[AsyncClient, None]:
        """Create an async test client for the FastAPI app.
        
        Yields:
            AsyncClient: Async test client
        """
        async with AsyncClient(app=self.app, base_url="http://test") as client:
            yield client
    
    async def async_request(
        self,
        method: str,
        url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
    ) -> Response:
        """Make an async HTTP request to the FastAPI app.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: URL to request
            json: JSON data to send (default: None)
            data: Form data to send (default: None)
            headers: HTTP headers (default: None)
            cookies: Cookies to send (default: None)
            auth_token: JWT token for authorization (default: None)
            
        Returns:
            Response: HTTP response
        """
        headers = headers or {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        async with self.async_client() as client:
            response = await client.request(
                method=method,
                url=url,
                json=json,
                data=data,
                headers=headers,
                cookies=cookies,
            )
            return response
    
    def run_async(self, coroutine: Any) -> Any:
        """Run an async coroutine in a test.
        
        Args:
            coroutine: Async coroutine to run
            
        Returns:
            Result of the coroutine
        """
        return asyncio.run(coroutine)
    
    def create_mock(self, target: str, **kwargs) -> MagicMock:
        """Create a mock for the specified target.
        
        Args:
            target: Target to mock, in the form 'package.module.Class'
            **kwargs: Additional arguments to pass to patch
            
        Returns:
            The created mock object
        """
        patcher = patch(target, **kwargs)
        mock = patcher.start()
        self.patches.append(patcher)
        self.mocks[target] = mock
        return mock
    
    async def create_test_user(
        self,
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "password123",
        is_superuser: bool = False,
    ) -> Dict[str, Any]:
        """Create a test user for authentication testing.
        
        Args:
            username: Username (default: "testuser")
            email: Email (default: "test@example.com")
            password: Password (default: "password123")
            is_superuser: Whether the user is a superuser (default: False)
            
        Returns:
            Created user object
        """
        # Implementation depends on your auth system
        # This is a placeholder - implement based on your actual User model
        from app.infrastructure.database.models import User
        from app.core.security import get_password_hash
        
        async with self.async_session_maker() as session:
            db_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                is_superuser=is_superuser,
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            return db_user.to_dict()
    
    async def get_auth_token(
        self, username: str = "testuser", password: str = "password123"
    ) -> str:
        """Get a JWT auth token for a test user.
        
        Args:
            username: Username (default: "testuser")
            password: Password (default: "password123")
            
        Returns:
            JWT auth token
        """
        response = await self.async_request(
            "POST",
            "/api/auth/token",
            json={"username": username, "password": password},
        )
        return response.json()["access_token"]