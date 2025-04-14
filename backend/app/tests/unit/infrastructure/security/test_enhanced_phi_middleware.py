"""Unit tests for the Enhanced PHI Middleware."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from fastapi import FastAPI, Request, Response, status
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCall
from starlette.datastructures import Headers
from starlette.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any, List, Tuple, Union, Awaitable, Callable

# Correctly import the middleware and related components
from app.infrastructure.security.enhanced_phi_middleware import (
    EnhancedPhiMiddleware,
    PhiDetectionResult,
    PhiSanitizerConfig,
)
from app.core.services.ml.phi_detection_service import PhiDetectionService


@pytest.fixture
def mock_phi_detection_service():
    """Create a mock PHI detection service."""
    service = MagicMock(spec=PhiDetectionService)
    # Configure mock detection method to return clean by default
    service.detect_phi_async = AsyncMock(return_value=PhiDetectionResult( # Use async mock
        contains_phi=False,
        sensitivity_score=0.1,
        detected_entities=[],
        sanitized_text=None,
    ))
    return service

@pytest.fixture
def phi_config():
    """Provides a default PHI sanitizer config."""
    return PhiSanitizerConfig(
        enabled=True,
        sensitivity_threshold=0.7,
        log_detections=True,
        sanitize_responses=True,
        block_high_risk=True,
        high_risk_threshold=0.9,
        excluded_paths=["/docs", "/redoc", "/openapi.json"],
    )


@pytest.fixture
def middleware(mock_phi_detection_service, phi_config):
    """Create the middleware with a mock PHI detection service and config."""
    # Pass a dummy app object if the middleware requires it during init
    dummy_app = MagicMock()
    return EnhancedPhiMiddleware(
        app=dummy_app,
        phi_service=mock_phi_detection_service,
        config=phi_config
    )

@pytest.fixture
def app_with_middleware(mock_phi_detection_service, phi_config):
    """Create a FastAPI app with the PHI middleware for client testing."""
    app = FastAPI()

    # Add some test routes
    @app.get("/test")
    async def test_route(): # Make async if middleware expects awaitable
        return {"message": "This is a test response"}

    @app.post("/api/data")
    async def post_data(request: Request):
        data = await request.json()
        return {"received": data}

    # Add middleware correctly
    app.add_middleware(
        EnhancedPhiMiddleware,
        phi_service=mock_phi_detection_service,
        config=phi_config
    )
    return app


@pytest.fixture
def client(app_with_middleware):
    """Create a test client."""
    return TestClient(app_with_middleware)


class TestEnhancedPhiMiddleware:
    """Test suite for the Enhanced PHI Middleware."""

    def test_init(self, middleware: EnhancedPhiMiddleware, phi_config: PhiSanitizerConfig):
        """Test initialization of the middleware."""
        assert middleware.config.enabled == phi_config.enabled
        assert middleware.config.sensitivity_threshold == phi_config.sensitivity_threshold
        assert middleware.config.log_detections == phi_config.log_detections
        assert middleware.config.sanitize_responses == phi_config.sanitize_responses
        assert middleware.config.block_high_risk == phi_config.block_high_risk
        assert "/docs" in middleware.config.excluded_paths

    def test_should_process_path(self, middleware: EnhancedPhiMiddleware):
        """Test path exclusion logic."""
        # Excluded paths
        assert middleware._should_process_path("/docs") is False
        assert middleware._should_process_path("/redoc") is False
        assert middleware._should_process_path("/openapi.json") is False

        # Included paths
        assert middleware._should_process_path("/api/patients") is True
        assert middleware._should_process_path("/test") is True

    def test_safe_request_no_phi(self, client: TestClient, mock_phi_detection_service: MagicMock):
        """Test processing a safe request with no PHI."""
        # Configure mock to detect no PHI
        mock_phi_detection_service.detect_phi_async.return_value = PhiDetectionResult(
            contains_phi=False, sensitivity_score=0.1, detected_entities=[]
        )

        # Make a request with no PHI
        response = client.post("/api/data", json={"message": "This is a safe message"})

        # Should pass through successfully
        assert response.status_code == 200
        assert response.json() == {"received": {"message": "This is a safe message"}}

        # Verify PHI detection was called on the request body
        mock_phi_detection_service.detect_phi_async.assert_called_once_with(
            json.dumps({"message": "This is a safe message"})
        )

    def test_request_with_phi_below_threshold(self, client: TestClient, mock_phi_detection_service: MagicMock):
        """Test processing a request with PHI below blocking threshold (but sanitized)."""
        original_text = json.dumps({"message": "Patient John Doe has arrived"})
        sanitized_text = json.dumps({"message": "Patient [REDACTED] has arrived"})
        # Configure mock to detect PHI but below blocking threshold
        mock_phi_detection_service.detect_phi_async.return_value = PhiDetectionResult(
            contains_phi=True,
            sensitivity_score=0.75,  # Below high_risk_threshold of 0.9
            detected_entities=["PATIENT_NAME"],
            sanitized_text=sanitized_text,
        )

        # Make a request with PHI
        response = client.post("/api/data", json={"message": "Patient John Doe has arrived"})

        # Should process but sanitize the *request* before it hits the endpoint
        # The endpoint receives the sanitized data
        assert response.status_code == 200
        assert response.json() == {"received": {"message": "[REDACTED]"}} # Endpoint received sanitized data
        mock_phi_detection_service.detect_phi_async.assert_called_once_with(original_text)


    def test_request_with_high_risk_phi(self, client: TestClient, mock_phi_detection_service: MagicMock):
        """Test processing a request with high-risk PHI."""
        original_text = json.dumps({"message": "SSN: 123-45-6789 for John Doe"})
        # Configure mock to detect high-risk PHI
        mock_phi_detection_service.detect_phi_async.return_value = PhiDetectionResult(
            contains_phi=True,
            sensitivity_score=0.95,  # Above high_risk_threshold of 0.9
            detected_entities=["SSN", "PATIENT_NAME"],
            sanitized_text=None,  # Sanitization might not happen if blocked
        )

        # Make a request with high-risk PHI
        response = client.post("/api/data", json={"message": "SSN: 123-45-6789 for John Doe"})

        # Should be blocked
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "contains prohibited sensitive information" in response.json()["detail"].lower()
        mock_phi_detection_service.detect_phi_async.assert_called_once_with(original_text)


    def test_disabled_middleware(self, mock_phi_detection_service: MagicMock):
        """Test middleware when disabled."""
        # Create app with disabled middleware
        app = FastAPI()
        @app.post("/api/data")
        async def post_data(request: Request):
            data = await request.json()
            return {"received": data}

        # Disabled middleware config
        config = PhiSanitizerConfig(enabled=False)
        app.add_middleware(
            EnhancedPhiMiddleware,
            phi_service=mock_phi_detection_service,
            config=config,
        )
        client = TestClient(app)

        # Make a request with PHI
        response = client.post("/api/data", json={"message": "Patient John Doe has SSN 123-45-6789"})

        # Middleware is disabled, should not block or sanitize
        assert response.status_code == 200
        assert response.json() == {"received": {"message": "Patient John Doe has SSN 123-45-6789"}}

        # Verify PHI detection was not called
        mock_phi_detection_service.detect_phi_async.assert_not_called()

    def test_excluded_path_skips_processing(self, client: TestClient, mock_phi_detection_service: MagicMock):
        """Test that excluded paths skip PHI processing."""
        # Make request to excluded path (assuming /docs is handled by TestClient correctly)
        # Note: TestClient might not fully replicate middleware behavior for static/doc paths.
        # A direct call to middleware._should_process_path is more reliable for unit testing this logic.
        response = client.get("/docs") # This might return 404 if docs aren't setup in test app

        # Verify PHI detection was not called
        mock_phi_detection_service.detect_phi_async.assert_not_called()
        # Assert based on _should_process_path tested earlier is sufficient here.


    @pytest.mark.asyncio
    async def test_process_response_with_phi(self, middleware: EnhancedPhiMiddleware, mock_phi_detection_service: MagicMock):
        """Test processing a response with PHI."""
        # Set up a mock response with PHI
        original_body = json.dumps({"data": "Patient John Doe has arrived"}).encode('utf-8')
        sanitized_body_str = json.dumps({"data": "Patient [REDACTED] has arrived"})

        # Mock the call_next function to return the original response
        async def mock_call_next(request: Request) -> Response:
            return JSONResponse(content=json.loads(original_body.decode('utf-8')))

        # Configure PHI detection for the response body
        mock_phi_detection_service.detect_phi_async.return_value = PhiDetectionResult(
            contains_phi=True,
            sensitivity_score=0.8,
            detected_entities=["PATIENT_NAME"],
            sanitized_text=sanitized_body_str,
        )

        # Create a dummy request to pass to dispatch
        mock_request = MagicMock(spec=Request)
        mock_request.scope = {"type": "http", "method": "GET", "path": "/api/somepath", "headers": [], "state": {}}
        mock_request.headers = Headers(scope=mock_request.scope)


        # Process the request/response through middleware.dispatch
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Should have sanitized content
        assert response.status_code == 200
        processed_body = json.loads(response.body.decode('utf-8'))
        assert processed_body == {"data": "Patient [REDACTED] has arrived"}
        # Verify detect_phi was called with the original response body text
        mock_phi_detection_service.detect_phi_async.assert_called_once_with(original_body.decode('utf-8'))


    @pytest.mark.asyncio
    async def test_process_invalid_json_response(self, middleware: EnhancedPhiMiddleware, mock_phi_detection_service: MagicMock):
        """Test processing a response with invalid JSON."""
        invalid_json_body = b"This is not valid JSON"

        async def mock_call_next(request: Request) -> Response:
            # Return a response that looks like JSON but isn't valid
            return Response(content=invalid_json_body, media_type="application/json")

        # Configure PHI detection (might still run on invalid JSON string)
        mock_phi_detection_service.detect_phi_async.return_value = PhiDetectionResult(contains_phi=False)

        mock_request = MagicMock(spec=Request)
        mock_request.scope = {"type": "http", "method": "GET", "path": "/api/somepath", "headers": [], "state": {}}
        mock_request.headers = Headers(scope=mock_request.scope)

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Should return original response without crashing
        assert response.status_code == 200
        assert response.body == invalid_json_body
        # Verify detect_phi was called with the invalid string
        mock_phi_detection_service.detect_phi_async.assert_called_once_with(invalid_json_body.decode('utf-8'))


    @pytest.mark.asyncio
    async def test_process_non_json_response(self, middleware: EnhancedPhiMiddleware, mock_phi_detection_service: MagicMock):
        """Test processing a non-JSON response."""
        plain_text_body = b"This is plain text"

        async def mock_call_next(request: Request) -> Response:
            return PlainTextResponse(content=plain_text_body.decode('utf-8'))

        # Configure PHI detection (should run on plain text)
        mock_phi_detection_service.detect_phi_async.return_value = PhiDetectionResult(contains_phi=False)

        mock_request = MagicMock(spec=Request)
        mock_request.scope = {"type": "http", "method": "GET", "path": "/api/somepath", "headers": [], "state": {}}
        mock_request.headers = Headers(scope=mock_request.scope)

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Should pass through unchanged
        assert response.status_code == 200
        assert response.body == plain_text_body

        # Should still check for PHI
        mock_phi_detection_service.detect_phi_async.assert_called_once_with(plain_text_body.decode('utf-8'))
