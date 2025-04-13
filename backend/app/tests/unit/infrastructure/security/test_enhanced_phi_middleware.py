"""Unit tests for the Enhanced PHI Middleware."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

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
    service.detect_phi.return_value = PhiDetectionResult(
        contains_phi=False,
        sensitivity_score=0.1,
        detected_entities=[],
        sanitized_text=None,
    )

    return service


@pytest.fixture
def middleware(mock_phi_detection_service):

            """Create the middleware with a mock PHI detection service."""
    config = PhiSanitizerConfig(
        enabled=True,
        sensitivity_threshold=0.7,
        log_detections=True,
        sanitize_responses=True,
        block_high_risk=True,
        high_risk_threshold=0.9,
        excluded_paths=["/docs", "/redoc", "/openapi.json"],
    )

    return EnhancedPhiMiddleware(
        app=MagicMock(), phi_service=mock_phi_detection_service, config=config
    )


@pytest.fixture
def app_with_middleware(mock_phi_detection_service):

            """Create a FastAPI app with the PHI middleware."""
    app = FastAPI()

    # Add some test routes
    @app.get("/test")
    def test_route():

                return {"message": "This is a test response"}

        @app.post("/api/data")
        async def post_data(request: Request):
             data = await request.json()
            return {"received": data}

            # Add middleware
            config = PhiSanitizerConfig(
            enabled=True,
            sensitivity_threshold=0.7,
            log_detections=True,
            sanitize_responses=True,
            block_high_risk=True,
            high_risk_threshold=0.9,
            excluded_paths=["/docs", "/redoc", "/openapi.json"],
        )

    app.add_middleware(
        EnhancedPhiMiddleware,
        phi_service=mock_phi_detection_service,
        config=config)

    return app


@pytest.fixture
def client(app_with_middleware):

            """Create a test client."""
    return TestClient(app_with_middleware)
    class TestEnhancedPhiMiddleware:
        """Test suite for the Enhanced PHI Middleware."""

        def test_init(self, middleware):


                    """Test initialization of the middleware."""
            assert middleware.config.enabled is True
            assert middleware.config.sensitivity_threshold == 0.7
            assert middleware.config.log_detections is True
            assert middleware.config.sanitize_responses is True
            assert middleware.config.block_high_risk is True
            assert "/docs" in middleware.config.excluded_paths

            def test_should_process_path(self, middleware):


                        """Test path exclusion logic."""
            # Excluded paths
            assert middleware._should_process_path("/docs") is False
            assert middleware._should_process_path("/redoc") is False
            assert middleware._should_process_path("/openapi.json") is False

            # Included paths
            assert middleware._should_process_path("/api/patients") is True
            assert middleware._should_process_path("/test") is True

            def test_safe_request_no_phi(self, client, mock_phi_detection_service):


                        """Test processing a safe request with no PHI."""
                # Configure mock to detect no PHI
                mock_phi_detection_service.detect_phi.return_value = PhiDetectionResult(
                contains_phi=False,
                sensitivity_score=0.1,
                detected_entities=[],
                sanitized_text=None,
        )

        # Make a request with no PHI
        response = client.post("/api/data",
                               json={"message": "This is a safe message"})

        # Should pass through successfully
        assert response.status_code == 200
        assert response.json() == {
            "received": {
                "message": "This is a safe message"}}

        # Verify PHI detection was called
        mock_phi_detection_service.detect_phi.assert_called_once()

    def test_request_with_phi_below_threshold(
            self, client, mock_phi_detection_service):
                """Test processing a request with PHI below blocking threshold."""
                # Configure mock to detect PHI but below blocking threshold
                mock_phi_detection_service.detect_phi.return_value = PhiDetectionResult(
                contains_phi=True,
                sensitivity_score=0.75,  # Below high_risk_threshold of 0.9
                detected_entities=["PATIENT_NAME"],
                sanitized_text=json.dumps({"message": "[REDACTED]"}),
        )

        # Make a request with PHI
        response = client.post(
            "/api/data", json={"message": "Patient John Doe has arrived"}
        )

        # Should process but sanitize
        assert response.status_code == 200
        # Response should be sanitized
        assert response.json() == {"received": {"message": "[REDACTED]"}}

    def test_request_with_high_risk_phi(
            self, client, mock_phi_detection_service):
                """Test processing a request with high-risk PHI."""
                # Configure mock to detect high-risk PHI
                mock_phi_detection_service.detect_phi.return_value = PhiDetectionResult(
                contains_phi=True,
                sensitivity_score=0.95,  # Above high_risk_threshold of 0.9
                detected_entities=["SSN", "PATIENT_NAME"],
                sanitized_text=None,  # No need to sanitize as it will be blocked
        )

        # Make a request with high-risk PHI
        response = client.post(
            "/api/data", json={"message": "SSN: 123-45-6789 for John Doe"}
        )

        # Should be blocked
        assert response.status_code == 403
        assert (
            "contains prohibited sensitive information"
            in response.json()["detail"].lower()
        )

    def test_disabled_middleware(self, mock_phi_detection_service):


                    """Test middleware when disabled."""
        # Create app with disabled middleware
        app = FastAPI()

        @app.post("/api/data")
        async def post_data(request: Request):
                 data = await request.json()
            return {"received": data}

            # Disabled middleware
            config = PhiSanitizerConfig(
                enabled=False,
                sensitivity_threshold=0.7,
                log_detections=True,
                sanitize_responses=True,
                block_high_risk=True,
                high_risk_threshold=0.9,
                excluded_paths=["/docs", "/redoc", "/openapi.json"],
            )

        app.add_middleware(
            EnhancedPhiMiddleware,
            phi_service=mock_phi_detection_service,
            config=config,

        client= TestClient(app)

        # Make a request with PHI
        response = client.post(
            "/api/data",
            json={
                "message": "Patient John Doe has SSN 123-45-6789"})

        # Middleware is disabled, should not block or sanitize
        assert response.status_code == 200
        assert response.json() == {
            "received": {"message": "Patient John Doe has SSN 123-45-6789"}
        }

        # Verify PHI detection was not called
        mock_phi_detection_service.detect_phi.assert_not_called()

    def test_excluded_path_skips_processing(
            self, client, mock_phi_detection_service):
                """Test that excluded paths skip PHI processing."""
                # Make request to excluded path
                response = client.get("/docs")

                # Should not process PHI detection
                mock_phi_detection_service.detect_phi.assert_not_called()

                @pytest.mark.asyncio
                async def test_process_response_with_phi(
                self, middleware, mock_phi_detection_service
        ):
            """Test processing a response with PHI."""
            # Set up a mock response with PHI
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "application/json"}
            mock_response.body = json.dumps(
            {"data": "Patient John Doe has arrived"}
        ).encode()

            # Configure PHI detection to find PHI
            mock_phi_detection_service.detect_phi.return_value = PhiDetectionResult(
            contains_phi=True,
            sensitivity_score=0.8,
            detected_entities=["PATIENT_NAME"],
            sanitized_text=json.dumps({"data": "Patient [REDACTED] has arrived"}),
        )

        # Process the response
        processed_response = await middleware._process_response(mock_response)

        # Should have sanitized content
        processed_body = json.loads(processed_response.body.decode())
        assert processed_body["data"] == "Patient [REDACTED] has arrived"

    @pytest.mark.asyncio
    async def test_process_invalid_json_response(self, middleware):
                 """Test processing a response with invalid JSON."""
        # Set up a mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.body = "This is not valid JSON".encode()

        # Process the response - should not crash
        processed_response = await middleware._process_response(mock_response)

        # Should return original response
        assert processed_response.body.decode() == "This is not valid JSON"

        @pytest.mark.asyncio
        async def test_process_non_json_response(
            self, middleware, mock_phi_detection_service
        ):
            """Test processing a non-JSON response."""
            # Set up a mock response with non-JSON content
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "text/plain"}
            mock_response.body = "This is plain text".encode()

            # Process the response
            processed_response = await middleware._process_response(mock_response)

            # Should pass through unchanged
            assert processed_response.body.decode() == "This is plain text"

            # Should still check for PHI
            mock_phi_detection_service.detect_phi.assert_called_once_with(
            "This is plain text"
        )
