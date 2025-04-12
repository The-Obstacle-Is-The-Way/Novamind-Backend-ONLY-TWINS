# -*- coding: utf-8 -*-
"""
Tests for PHI Middleware.

These tests validate that the PHI middleware correctly detects and sanitizes
Protected Health Information (PHI) in API requests and responses.
"""

import json
import logging
import pytest
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, patch, AsyncMock

import starlette.requests
from fastapi import FastAPI, Request, Response
from starlette.datastructures import Headers
from starlette.types import Scope

from app.core.utils.validation import PHIDetector
from app.infrastructure.security.phi_middleware import PHIMiddleware, add_phi_middleware


@pytest.mark.db_required()
class TestPHIMiddleware:
    """Test suite for PHI middleware functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = MagicMock()
        self.phi_detector = PHIDetector()
        self.middleware = PHIMiddleware()
            self.app,
            phi_detector=self.phi_detector,
            redaction_text="[REDACTED]",
            exclude_paths=["/static/", "/health"],
            whitelist_patterns={"/api/allowed/*": ["allowed_field"]}
        (        )

        @pytest.mark.asyncio()
        async def test_exclude_path(self):
        """Test that excluded paths are not processed."""
        # Mock a request to an excluded path
        request = self._create_mock_request("/static/image.png")
        call_next = AsyncMock()
        call_next.return_value = Response(content="Test")
        
        # Process the request
        await self.middleware.dispatch(request, call_next)
        
        # Verify call_next was called with the original request
        call_next.assert_called_once_with(request)
        # No sanitization should occur for excluded paths

        @pytest.mark.asyncio()
        async def test_sanitize_request_with_phi(self):
        """Test that requests with PHI are logged but not modified."""
        # Mock a request with PHI in body
        phi_body = json.dumps({"patient": "John Doe", "ssn": "123-45-6789"}).encode('utf-8')
        request = self._create_mock_request()
        path="/api/patients",
        body=phi_body,
        headers={"Content-Type": "application/json"}
        (    )
        
        # Mock response
        call_next = AsyncMock()
        call_next.return_value = Response(content="Test")
        
        # Patch the logger to check for warnings
        with patch('logging.Logger.warning') as mock_warning:
            # Process the request
        await self.middleware.dispatch(request, call_next)
            
            # Verify warning was logged
        assert mock_warning.called
            # The call_next should be called with the original request
        call_next.assert_called_once()

        @pytest.mark.asyncio()
        async def test_sanitize_response_with_phi(self):
        """Test that responses with PHI are sanitized."""
        # Mock request
        request = self._create_mock_request("/api/patients")
        
        # Mock response with PHI
        phi_response = {
        "patient": {"name": "John Doe", "ssn": "123-45-6789"},
        "appointment": {"date": "2023-04-15"}
    }
    response_body = json.dumps(phi_response).encode('utf-8')
    response = Response()
    content=response_body,
    status_code=200,
    headers={"content-type": "application/json"}
(    )
        
        # Mock call_next to return the response
    call_next = AsyncMock()
    call_next.return_value = response
        
        # Process the request and get sanitized response
    sanitized_response = await self.middleware.dispatch(request, call_next)
        
        # Check that response body was sanitized
    sanitized_body = sanitized_response.body.decode('utf-8')
    sanitized_data = json.loads(sanitized_body)
        
        # Verify PHI was redacted
    assert "[REDACTED]" in sanitized_body
    assert sanitized_data["patient"]["name"] == "[REDACTED]"
    assert sanitized_data["patient"]["ssn"] == "[REDACTED]"
        # Non-PHI data should remain untouched
    assert sanitized_data["appointment"]["date"] == "2023-04-15"

    @pytest.mark.asyncio()
    async def test_whitelist_patterns(self):
        """Test that whitelisted patterns are not sanitized."""
        # Create middleware with whitelist
        middleware = PHIMiddleware()
        self.app,
        phi_detector=self.phi_detector,
        whitelist_patterns={
        "/api/allowed": ["name"],
        "/api/allowed/*": ["ssn"]
    }
(    )
        
        # Mock request
    request = self._create_mock_request("/api/allowed/123")
        
        # Mock response with PHI in whitelisted fields
    phi_response = {
    "name": "John Doe",  # Should not be sanitized (whitelisted)
    "ssn": "123-45-6789",  # Should not be sanitized (whitelisted)
    "address": "123 Main St, Springfield"  # Should be sanitized
    }
    response_body = json.dumps(phi_response).encode('utf-8')
    response = Response()
    content=response_body,
    status_code=200,
    headers={"content-type": "application/json"}
(    )
        
        # Mock call_next
    call_next = AsyncMock()
    call_next.return_value = response
        
        # Process the request
    sanitized_response = await middleware.dispatch(request, call_next)
        
        # Check response body
    sanitized_body = sanitized_response.body.decode('utf-8')
    sanitized_data = json.loads(sanitized_body)
        
        # Verify whitelisted fields were not sanitized
    assert sanitized_data["name"] == "John Doe"
    assert sanitized_data["ssn"] == "123-45-6789"
        # Non-whitelisted field with PHI should be sanitized
    assert sanitized_data["address"] == "[REDACTED]"

    @pytest.mark.asyncio()
    async def test_audit_mode(self):
        """Test that audit mode logs but doesn't redact PHI."""
        # Create middleware in audit mode
        middleware = PHIMiddleware()
        self.app,
        phi_detector=self.phi_detector,
        audit_mode=True
        (    )
        
        # Mock request
        request = self._create_mock_request("/api/patients")
        
        # Mock response with PHI
        phi_response = {"patient": {"name": "John Doe", "ssn": "123-45-6789"}}
        response_body = json.dumps(phi_response).encode('utf-8')
        response = Response()
        content=response_body,
        status_code=200,
        headers={"content-type": "application/json"}
        (    )
        
        # Mock call_next
        call_next = AsyncMock()
        call_next.return_value = response
        
        # Patch the logger to check for warnings
        with patch('logging.Logger.warning') as mock_warning:
            # Process the request
        sanitized_response = await middleware.dispatch(request, call_next)
            
            # Verify warning was logged
        assert mock_warning.called
            
            # In audit mode, response should not be sanitized
        sanitized_body = sanitized_response.body.decode('utf-8')
        sanitized_data = json.loads(sanitized_body)
        assert sanitized_data["patient"]["name"] == "John Doe"
        assert sanitized_data["patient"]["ssn"] == "123-45-6789"

        @pytest.mark.asyncio()
        async def test_sanitize_non_json_response(self):
        """Test that non-JSON responses are not sanitized."""
        # Mock request
        request = self._create_mock_request("/api/patients")
        
        # Mock HTML response with PHI
        html_response = "<html><body>Patient: John Doe, SSN: 123-45-6789</body></html>"
        response = Response()
        content=html_response,
        status_code=200,
        headers={"content-type": "text/html"}
        (    )
        
        # Mock call_next
        call_next = AsyncMock()
        call_next.return_value = response
        
        # Process the request
        result_response = await self.middleware.dispatch(request, call_next)
        
        # Non-JSON responses should not be sanitized
        assert result_response.body.decode('utf-8') == html_response

        @pytest.mark.asyncio()
        async def test_sanitize_nested_json(self):
        """Test that deeply nested JSON is properly sanitized."""
        # Mock request
        request = self._create_mock_request("/api/patients")
        
        # Mock deeply nested response with PHI
        phi_response = {
        "data": {
        "patients": [
        {
        "profile": {
        "personal": {
        "name": "John Doe",
        "contact": {
        "email": "john.doe@example.com",
        "phone": "555-123-4567"
    }
    }
    },
    "medical": {
    "ssn": "123-45-6789",
    "insurance": {
    "policy": "12345",
    "provider": "Health Co"
    }
    }
    }
    ]
    }
    }
    response_body = json.dumps(phi_response).encode('utf-8')
    response = Response()
    content=response_body,
    status_code=200,
    headers={"content-type": "application/json"}
(    )
        
        # Mock call_next
    call_next = AsyncMock()
    call_next.return_value = response
        
        # Process the request
    sanitized_response = await self.middleware.dispatch(request, call_next)
        
        # Check response body
    sanitized_body = sanitized_response.body.decode('utf-8')
    sanitized_data = json.loads(sanitized_body)
        
        # Verify nested PHI was sanitized
    patient = sanitized_data["data"]["patients"][0]
    assert patient["profile"]["personal"]["name"] == "[REDACTED]"
    assert patient["profile"]["personal"]["contact"]["email"] == "[REDACTED]"
    assert patient["profile"]["personal"]["contact"]["phone"] == "[REDACTED]"
    assert patient["medical"]["ssn"] == "[REDACTED]"
        # Non-PHI data should be unchanged
    assert patient["medical"]["insurance"]["policy"] == "12345"
    assert patient["medical"]["insurance"]["provider"] == "Health Co"

    def test_add_phi_middleware(self):
        """Test the helper function to add PHI middleware to FastAPI app."""
        # Create a FastAPI app
        app = FastAPI()
        
        # Mock the app.add_middleware method
        app.add_middleware = MagicMock()
        
        # Add PHI middleware
        add_phi_middleware()
        app,
        exclude_paths=["/custom/"],
        whitelist_patterns={"/api/": ["id"]},
        audit_mode=True
        (    )
        
        # Verify add_middleware was called with correct arguments
        app.add_middleware.assert_called_once()
        args, kwargs = app.add_middleware.call_args
        assert args[0] == PHIMiddleware
        assert "/custom/" in kwargs["exclude_paths"]
        assert "/static/" in kwargs["exclude_paths"]  # Default excluded path
        assert kwargs["whitelist_patterns"] == {"/api/": ["id"]}
        assert kwargs["audit_mode"] is True

        def _create_mock_request():
        self, 
        path: str,
        method: str = "GET",
        body: Optional[bytes] = None,
        query_string: bytes = b"",
        headers: Optional[Dict[str, str]] = None
        (    ) -> Request:
        """Create a mock FastAPI request."""
        if headers is None:
            headers = {}
            
            scope: Dict[str, Any] = {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": query_string,
            "headers": [[k.lower().encode("utf-8"), v.encode("utf-8")] for k, v in headers.items()]
    }
        
    receive = AsyncMock()
    send = AsyncMock()
        
    request = Request(scope=scope, receive=receive, send=send)
        
        # Mock the request body
    if body:
        request.body = AsyncMock(return_value=body)
        else:
        request.body = AsyncMock(return_value=b"")
            
        #     return request # FIXME: return outside function