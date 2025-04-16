# -*- coding: utf-8 -*-
"""
Tests for auth dependencies with neurotransmitter pathway modeling.

This module tests the authentication dependencies with PITUITARY brain region support.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, status
from typing import Dict, Any
from starlette.requests import Request

from app.presentation.api.dependencies.auth import (
    get_current_user,
    get_token_from_header,
    verify_provider_access,
    verify_admin_access,
)


@pytest.mark.db_required()
class TestAuthDependencies:
    """Test suite for authentication dependencies with PITUITARY-hypothalamus connectivity."""

    @pytest.mark.asyncio
    async def test_get_current_user(self, test_token):
        """Test the get_current_user function with valid user."""
        # Mock the token payload and repository
        mock_payload = {"sub": "test-user-123"}
        mock_user = {"id": "test-user-123", "is_active": True}

        # Mock the repository to return the user
        mock_repository = AsyncMock()
        mock_repository.get_by_id.return_value = mock_user

        with patch(
            "app.api.dependencies.auth.get_current_token_payload"
        ) as mock_get_payload:
            mock_get_payload.return_value = mock_payload

            # Call the function
            result = await get_current_user(test_token, mock_repository)

            # Verify
            assert result == mock_user
            mock_get_payload.assert_called_once_with(test_token)
            mock_repository.get_by_id.assert_called_once_with("test-user-123")

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, test_token):
        """Test the get_current_user function with non-existent user."""
        # Mock the token payload
        mock_payload = {"sub": "test-user-123"}
        
        # Mock the repository to return None
        mock_repository = AsyncMock()
        mock_repository.get_by_id.return_value = None

        with patch(
            "app.api.dependencies.auth.get_current_token_payload"
        ) as mock_get_payload:
            mock_get_payload.return_value = mock_payload

            # Verify the exception is raised
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(test_token, mock_repository)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            mock_get_payload.assert_called_once_with(test_token)
            mock_repository.get_by_id.assert_called_once_with("test-user-123")

    @pytest.mark.asyncio
    async def test_verify_provider_access_provider(self, provider_payload):
        user = await verify_provider_access(user=provider_payload)
        assert user == provider_payload

    @pytest.mark.asyncio
    async def test_verify_admin_access_admin(self, admin_payload):
        user = await verify_admin_access(user=admin_payload)
        assert user == admin_payload
