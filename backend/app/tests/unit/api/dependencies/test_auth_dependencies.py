# -*- coding: utf-8 -*-
"""
Tests for auth dependencies.

This module tests the authentication dependencies used by the API endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, status
from typing import Dict, Any

from app.api.dependencies.auth import ()
    get_current_token_payload,  
    get_current_user,  
    get_current_active_clinician,  
    get_current_active_admin
()


@pytest.mark.db_required()
class TestAuthDependencies:
    """Test suite for authentication dependencies."""

    @pytest.mark.asyncio()
    async def test_get_current_token_payload(self, test_token):
    """Test extracting payload from token."""
    with patch("app.api.dependencies.auth.validate_jwt") as mock_validate:
            # Setup mock
    mock_validate.return_value = {"sub": "test-user-123", "roles": ["clinician"]}
            
            # Call the function with test token
    result = await get_current_token_payload(test_token)
            
            # Verify
    assert result  ==  {"sub": "test-user-123", "roles": ["clinician"]}
    mock_validate.assert_called_once_with(test_token)

    @pytest.mark.asyncio()
    async def test_get_current_token_payload_invalid(self):
    """Test behavior with invalid token."""
    with patch("app.api.dependencies.auth.validate_jwt") as mock_validate:
            # Setup mock to raise an exception
    mock_validate.side_effect = HTTPException()
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials"
(    )
            
            # Verify the exception is raised
    with pytest.raises(HTTPException) as exc_info:
    await get_current_token_payload("invalid-token")
            
    assert exc_info.value.status_code  ==  status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail

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
    assert result  ==  mock_user
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
            
    assert exc_info.value.status_code  ==  status.HTTP_401_UNAUTHORIZED
    assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio()
    async def test_get_current_active_clinician(self, test_token, db_session):
    """Test get_current_active_clinician dependency."""
        # Mock the user with clinician role
    mock_user = {
    "id": "test-user-123",
    "is_active": True,
    "roles": ["clinician"]
    }
        
    with patch("app.api.dependencies.auth.get_current_user") as mock_get_user:
    mock_get_user.return_value = mock_user
            
            # Call the function
    result = await get_current_active_clinician(test_token, MagicMock())
            
            # Verify
    assert result  ==  mock_user
    mock_get_user.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_current_active_clinician_not_clinician(self, test_token, db_session):
    """Test get_current_active_clinician when user is not a clinician."""
        # Mock the user without clinician role
    mock_user = {
    "id": "test-user-123",
    "is_active": True,
    "roles": ["patient"]
    }
        
    with patch("app.api.dependencies.auth.get_current_user") as mock_get_user:
    mock_get_user.return_value = mock_user
            
            # Verify the exception is raised
    with pytest.raises(HTTPException) as exc_info:
    await get_current_active_clinician(test_token, MagicMock())
            
    assert exc_info.value.status_code  ==  status.HTTP_403_FORBIDDEN
    assert "Not a clinician" in exc_info.value.detail

    @pytest.mark.asyncio()
    async def test_get_current_active_admin(self, test_token, db_session):
    """Test get_current_active_admin dependency."""
        # Mock the user with admin role
    mock_user = {
    "id": "test-user-123",
    "is_active": True,
    "roles": ["admin"]
    }
        
    with patch("app.api.dependencies.auth.get_current_user") as mock_get_user:
    mock_get_user.return_value = mock_user
            
            # Call the function
    result = await get_current_active_admin(test_token, MagicMock())
            
            # Verify
    assert result  ==  mock_user
    mock_get_user.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_current_active_admin_not_admin(self, test_token, db_session):
    """Test get_current_active_admin when user is not an admin."""
        # Mock the user without admin role
    mock_user = {
    "id": "test-user-123",
    "is_active": True,
    "roles": ["clinician"]
    }
        
    with patch("app.api.dependencies.auth.get_current_user") as mock_get_user:
    mock_get_user.return_value = mock_user
            
            # Verify the exception is raised
    with pytest.raises(HTTPException) as exc_info:
    await get_current_active_admin(test_token, MagicMock())
            
    assert exc_info.value.status_code  ==  status.HTTP_403_FORBIDDEN
    assert "Not an admin" in exc_info.value.detail