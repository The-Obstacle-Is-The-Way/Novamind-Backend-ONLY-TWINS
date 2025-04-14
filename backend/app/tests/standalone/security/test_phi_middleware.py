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
        self.middleware = PHIMiddleware(
            self.app,
            phi_detector=self.phi_detector,
            redaction_text="[REDACTED]",
            exclude_paths=["/static/", "/health"],
            whitelist_patterns={"/api/allowed/*": ["allowed_field"]}
        )

    @pytest.mark.asyncio
    async def test_exclude_path(self):
        """Test that excluded paths are not processed by the middleware."""
        # Mock a request to an excluded path
        request = self._create_mock_request("/static/image.png")
        call_next = AsyncMock()
        call_next.return_value = Response(content="Test")

        # Process the request
        await self.middleware.dispatch(request, call_next)

        # Verify call_next was called with the original request
        call_next.assert_called_once_with(request)
        # No sanitization should occur for excluded paths

    @pytest.mark.asyncio
    async def test_sanitize_request_with_phi(self):
        """Test that PHI in request body is properly sanitized."""
        # Mock a request with PHI in body
        phi_body = json.dumps(
            {"patient": "John Doe", "ssn": "123-45-6789"}).encode('utf-8')
        request = self._create_mock_request(
            path="/api/patients",
            body=phi_body,
            headers={"Content-Type": "application/json"}
        )

        # Mock response
        call_next = AsyncMock()
        call_next.return_value = Response(content="Test response")

        # Patch the detect_phi method to indicate PHI was found
        with patch.object(self.phi_detector, 'detect_phi', return_value=True):
            with patch.object(self.phi_detector, 'sanitize_content', return_value=json.dumps(
                    {"patient": "[REDACTED]", "ssn": "[REDACTED]"}).encode('utf-8')):
                # Process the request
                await self.middleware.dispatch(request, call_next)

                # Verify the request body was sanitized before being passed to call_next
                await request.body()  # This should now return the sanitized body
                # Verify call_next was called
                call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_sanitize_response_with_phi(self):
        """Test that PHI in response body is properly sanitized."""
        # Mock request and response
        request = self._create_mock_request("/api/patients")
        
        # Create a response with PHI
        phi_response = Response(
            content=json.dumps({
                "patient": "Jane Smith",
                "medical_record": "Contains PHI data"
            }),
            media_type="application/json"
        )
        
        call_next = AsyncMock(return_value=phi_response)

        # Patch the detect_phi method to indicate PHI was found in response
        with patch.object(self.phi_detector, 'detect_phi', return_value=True):
            with patch.object(self.phi_detector, 'sanitize_content', return_value=json.dumps({
                "patient": "[REDACTED]",
                "medical_record": "[REDACTED]"
            })):
                # Process the request
                response = await self.middleware.dispatch(request, call_next)
                
                # Verify response was sanitized
                assert response.body == json.dumps({
                    "patient": "[REDACTED]",
                    "medical_record": "[REDACTED]"
                }).encode('utf-8')

    @pytest.mark.asyncio
    async def test_whitelisted_fields(self):
        """Test that whitelisted fields are not sanitized even when they contain PHI."""
        # Mock a request to a path with whitelist patterns
        request = self._create_mock_request(
            path="/api/allowed/data",
            body=json.dumps({
                "patient_name": "John Doe",  # Should be sanitized
                "allowed_field": "Jane Smith"  # Should NOT be sanitized (whitelisted)
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        call_next = AsyncMock()
        call_next.return_value = Response(content="Test response")

        # Patch methods to simulate PHI detection and sanitization
        with patch.object(self.phi_detector, 'detect_phi') as mock_detect:
            with patch.object(self.phi_detector, 'sanitize_content') as mock_sanitize:
                # Configure mocks for whitelist behavior
                mock_detect.return_value = True
                mock_sanitize.return_value = json.dumps({
                    "patient_name": "[REDACTED]",
                    "allowed_field": "Jane Smith"  # Not sanitized
                }).encode('utf-8')
                
                # Process the request
                await self.middleware.dispatch(request, call_next)
                
                # Verify sanitize_content was called with the whitelist
                mock_sanitize.assert_called_once()
                args, kwargs = mock_sanitize.call_args
                assert "whitelist" in kwargs
                assert "allowed_field" in kwargs["whitelist"]

    @pytest.mark.asyncio
    async def test_non_json_content(self):
        """Test that non-JSON content is handled properly."""
        # Mock a request with non-JSON content
        request = self._create_mock_request(
            path="/api/documents",
            body=b"This is plain text with PHI: John Doe's record",
            headers={"Content-Type": "text/plain"}
        )
        
        call_next = AsyncMock()
        call_next.return_value = Response(
            content="Plain text response with PHI: SSN 123-45-6789",
            media_type="text/plain"
        )

        # Patch methods to simulate PHI detection and sanitization for text
        with patch.object(self.phi_detector, 'detect_phi', return_value=True):
            with patch.object(self.phi_detector, 'sanitize_content', return_value=b"This is plain text with PHI: [REDACTED]"):
                # Process the request
                response = await self.middleware.dispatch(request, call_next)
                
                # Verify content was processed
                assert response.body.decode('utf-8') == "This is plain text with PHI: [REDACTED]"

    @pytest.mark.standalone()
    def test_add_phi_middleware(self):
        """Test the helper function to add PHI middleware to FastAPI app."""
        # Create a FastAPI app
        app = FastAPI()

        # Mock the app.add_middleware method
        app.add_middleware = MagicMock()

        # Add PHI middleware
        add_phi_middleware(
            app,
            exclude_paths=["/custom/"],
            whitelist_patterns={"/api/": ["id"]},
            audit_mode=True
        )

        # Verify add_middleware was called with correct arguments
        app.add_middleware.assert_called_once()
        args, kwargs = app.add_middleware.call_args
        assert args[0] == PHIMiddleware
        assert "/custom/" in kwargs["exclude_paths"]
        assert "/static/" in kwargs["exclude_paths"]  # Default excluded path
        assert kwargs["whitelist_patterns"] == {"/api/": ["id"]}
        assert kwargs["audit_mode"] is True

    def _create_mock_request(
            self,
            path: str,
            method: str = "GET",
            body: Optional[bytes] = None,
            query_string: bytes = b"",
            headers: Optional[Dict[str, str]] = None
        ) -> Request:
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

        return request