# -*- coding: utf-8 -*-
"""
Tests for the enhanced PHI middleware.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from app.infrastructure.security.enhanced_phi_middleware import (
    EnhancedPHIMiddleware,
    setup_enhanced_phi_middleware
)


@pytest.fixture
def mock_audit_logger():
    """Fixture for a mock audit logger."""
    logger = MagicMock()
    logger.log_security_event = MagicMock()
    return logger


@pytest.fixture
def test_app(mock_audit_logger):
    """Fixture for a test FastAPI application with PHI middleware."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint"}
    
    @app.get("/test-with-phi")
    async def test_with_phi():
        return {"patient": "John Doe", "ssn": "123-45-6789"}
    
    @app.post("/test-post")
    async def test_post(data: dict):
        return data
    
    setup_enhanced_phi_middleware(
        app,
        audit_logger=mock_audit_logger,
        sanitize_responses=True,
        block_phi_in_requests=True
    )
    
    return app


@pytest.fixture
def test_client(test_app):
    """Fixture for a test client."""
    return TestClient(test_app)


class TestEnhancedPHIMiddleware:
    """Tests for the EnhancedPHIMiddleware class."""
    
    def test_excluded_paths_are_skipped(self, test_client):
        """Test that excluded paths are skipped."""
        # The /docs path should be excluded by default
        response = test_client.get("/docs")
        assert response.status_code == 404  # 404 because the path doesn't exist, but middleware didn't block it
    
    def test_sanitize_response_with_phi(self, test_client):
        """Test that responses with PHI are sanitized."""
        response = test_client.get("/test-with-phi")
        assert response.status_code == 200
        
        data = response.json()
        # PHI should be sanitized
        assert data["patient"] != "John Doe"
        assert "ANONYMIZED_NAME" in data["patient"]
        assert data["ssn"] != "123-45-6789"
        assert data["ssn"] == "000-00-0000"
    
    def test_block_request_with_phi_in_query(self, test_client):
        """Test that requests with PHI in query parameters are blocked."""
        response = test_client.get("/test?patient=John%20Doe")
        assert response.status_code == 400
        assert "PHI detected in request" in response.json()["error"]
    
    def test_block_request_with_phi_in_body(self, test_client):
        """Test that requests with PHI in body are blocked."""
        response = test_client.post(
            "/test-post",
            json={"patient": "John Doe", "ssn": "123-45-6789"}
        )
        assert response.status_code == 400
        assert "PHI detected in request" in response.json()["error"]
    
    def test_allow_request_without_phi(self, test_client):
        """Test that requests without PHI are allowed."""
        response = test_client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "Test endpoint"}
    
    def test_allow_post_without_phi(self, test_client):
        """Test that POST requests without PHI are allowed."""
        response = test_client.post(
            "/test-post",
            json={"data": "test data", "value": 123}
        )
        assert response.status_code == 200
        assert response.json() == {"data": "test data", "value": 123}
    
    @patch("app.infrastructure.security.enhanced_phi_middleware.EnhancedPHIDetector")
    def test_phi_detection_in_request(self, mock_detector, test_client, mock_audit_logger):
        """Test PHI detection in requests."""
        # Mock the PHI detector to always detect PHI
        mock_detector.contains_phi.return_value = True
        
        response = test_client.get("/test")
        assert response.status_code == 400
        assert "PHI detected in request" in response.json()["error"]
        
        # Verify audit logging
        mock_audit_logger.log_security_event.assert_called_once()
    
    @patch("app.infrastructure.security.enhanced_phi_middleware.EnhancedPHISanitizer")
    def test_phi_sanitization_in_response(self, mock_sanitizer, test_client):
        """Test PHI sanitization in responses."""
        # Mock the sanitizer to return a specific sanitized value
        mock_sanitizer.sanitize_structured_data.return_value = {"sanitized": True}
        
        response = test_client.get("/test-with-phi")
        assert response.status_code == 200
        assert response.json() == {"sanitized": True}
    
    def test_non_json_response_not_sanitized(self, test_app, test_client):
        """Test that non-JSON responses are not sanitized."""
        @test_app.get("/test-text")
        async def test_text():
            return "This is a text response with John Doe's information"
        
        response = test_client.get("/test-text")
        assert response.status_code == 200
        assert "John Doe" in response.text
    
    @patch("app.infrastructure.security.enhanced_phi_middleware.logger")
    def test_error_handling_in_response_processing(self, mock_logger, test_app, test_client):
        """Test error handling in response processing."""
        # Create a response that will cause an error during processing
        @test_app.get("/test-error")
        async def test_error():
            # Return a response that will cause a JSON decode error
            return JSONResponse(content=b"invalid json")
        
        response = test_client.get("/test-error")
        assert response.status_code == 200
        
        # Verify error was logged
        mock_logger.warning.assert_called_once()
        assert "Error sanitizing response" in mock_logger.warning.call_args[0][0]


def test_setup_enhanced_phi_middleware():
    """Test the setup function for the middleware."""
    app = FastAPI()
    mock_logger = MagicMock()
    
    # Setup middleware with custom options
    setup_enhanced_phi_middleware(
        app,
        audit_logger=mock_logger,
        exclude_paths=["/custom-exclude"],
        sanitize_responses=False,
        block_phi_in_requests=True
    )
    
    # Verify middleware was added
    assert any(
        isinstance(middleware, EnhancedPHIMiddleware)
        for middleware in app.user_middleware
    )
    
    # Get the middleware instance
    phi_middleware = next(
        middleware.cls
        for middleware in app.user_middleware
        if middleware.cls == EnhancedPHIMiddleware
    )
    
    # Verify middleware was configured correctly
    assert phi_middleware