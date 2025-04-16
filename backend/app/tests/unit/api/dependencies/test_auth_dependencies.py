# -*- coding: utf-8 -*-
"""
Tests for auth dependencies.

This module tests the authentication dependencies used by the API endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, status
from typing import Dict, Any

from app.presentation.api.dependencies.auth import (
    get_token_from_header,
    get_current_user
)


@pytest.mark.db_required()
class TestAuthDependencies:
    """Test suite for authentication dependencies."""

    @pytest.mark.asyncio()
    async def test_get_token_from_header_present(self):
        """Test extracting token from header."""
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_token")
        token = await get_token_from_header(credentials=creds)
        assert token == "test_token"

    @pytest.mark.asyncio()
    async def test_get_token_from_header_missing(self):
        """Test behavior with missing token."""
        token = await get_token_from_header(credentials=None)
        assert token is None

    @pytest.mark.asyncio()
    async def test_get_current_user(self, test_token, db_session):
        """Test get_current_user dependency."""
        # Mock the token payload and repository
        mock_payload = {"sub": "test-user-123"}
        mock_user = {"id": "test-user-123", "is_active": True}

        # Mock the repository to return the user
        mock_repository = AsyncMock()
        mock_repository.get_by_id.return_value = mock_user

        with patch("app.api.dependencies.auth.get_current_token_payload") as mock_get_payload:
            mock_get_payload.return_value = mock_payload

            # Call the function
            result = await get_current_user(test_token, mock_repository)

            # Verify
            assert result == mock_user
            mock_get_payload.assert_called_once_with(test_token)
            mock_repository.get_by_id.assert_called_once_with("test-user-123")

    @pytest.mark.asyncio()
    async def test_get_current_user_not_found(self, test_token, db_session):
        """Test get_current_user when user is not found."""
        # Mock the token payload and repository
        mock_payload = {"sub": "test-user-123"}

        # Mock the repository to return None (user not found)
        mock_repository = AsyncMock()
        mock_repository.get_by_id.return_value = None

        with patch("app.api.dependencies.auth.get_current_token_payload") as mock_get_payload:
            mock_get_payload.return_value = mock_payload

            # Verify the exception is raised
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(test_token, mock_repository)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "User not found" in exc_info.value.detail
