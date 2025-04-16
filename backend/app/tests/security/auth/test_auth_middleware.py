import pytest
from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.presentation.middleware.authentication_middleware import AuthenticationMiddleware
from app.infrastructure.security.auth.authentication_service import AuthenticationService

@pytest.fixture
def mock_auth_service():
    mock = AsyncMock(spec=AuthenticationService)
    async def mock_get_user_by_id(user_id: str):
        if user_id == "expired":
            raise Exception("TokenExpiredError")
        if user_id == "invalid":
            raise Exception("InvalidTokenError")
        if user_id in ["patient123", "provider123", "admin123"]:
            user = MagicMock()
            user.id = user_id
            if user_id.startswith("patient"):
                user.roles = ["patient"]
            elif user_id.startswith("provider"):
                user.roles = ["provider"]
            elif user_id.startswith("admin"):
                user.roles = ["admin"]
            return user
        return None
    mock.get_user_by_id.side_effect = mock_get_user_by_id
    return mock

@pytest.fixture
def app(mock_auth_service):
    app = FastAPI()
    app.add_middleware(
        AuthenticationMiddleware,
        auth_service=mock_auth_service,
        public_paths={"/public"}
    )
    @app.get("/public")
    async def public_route():
        return {"message": "public access"}
    # Add other protected routes as needed, using Depends and mock_auth_service
    return app

@pytest.fixture
def test_client(app):
    return TestClient(app)

def test_public_route_access(test_client):
    response = test_client.get("/public")
    assert response.status_code == 200
    assert response.json() == {"message": "public access"}

# Add additional test cases for protected routes, expired/invalid tokens, etc.
