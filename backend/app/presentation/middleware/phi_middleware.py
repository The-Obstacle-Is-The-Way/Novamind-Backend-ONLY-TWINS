# -*- coding: utf-8 -*-
"""
PHI Middleware for FastAPI.

This middleware intercepts API requests and responses to sanitize any potential
Protected Health Information (PHI) before it's logged or returned to clients,
ensuring HIPAA compliance at the API layer.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Union, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, StreamingResponse
from starlette.requests import Request
from starlette.types import ASGIApp
from fastapi import FastAPI, HTTPException

# Import the canonical PHIService instead of PHIDetector
# from app.infrastructure.security.phi.detector import PHIDetector
from app.infrastructure.security.phi.phi_service import PHIService, PHIType


logger = logging.getLogger(__name__)


class PHIMiddleware(BaseHTTPMiddleware):
    """
    HIPAA-compliant middleware that sanitizes PHI in requests and responses.
    
    This middleware sits between the client and the application to ensure no PHI
    is accidentally leaked through the API layer.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        # Replace detector dependency with service dependency
        # phi_detector: Optional[PHIDetector] = None,
        phi_service: Optional[PHIService] = None,
        redaction_text: str = "[REDACTED {phi_type}]", # Update default redaction
        exclude_paths: Optional[List[str]] = None,
        whitelist_patterns: Optional[Dict[str, List[str]]] = None,
        audit_mode: bool = False,
    ):
        """
        Initialize the PHI middleware.
        
        Args:
            app: The ASGI application
            # phi_detector: Custom PHI detector to use
            phi_service: Custom PHI service to use
            redaction_text: Text to use when redacting PHI (can use {phi_type})
            exclude_paths: List of path prefixes to exclude from PHI scanning
            whitelist_patterns: Dict mapping paths to patterns that are allowed
            audit_mode: If True, only log potential PHI without redacting
        """
        super().__init__(app)
        # Use PHIService instance
        # self.phi_detector = phi_detector or PHIDetector()
        self.phi_service = phi_service or PHIService() # Instantiate service
        self.redaction_text = redaction_text
        self.exclude_paths = set(exclude_paths or [])
        self.whitelist_patterns = whitelist_patterns or {}
        self.audit_mode = audit_mode
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and response.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware/route handler
            
        Returns:
            The processed response
        """
        # Explicitly log entry into dispatch to confirm execution
        # logger.critical(f"[PHIMiddleware.dispatch] ENTERED for path: {request.url.path}")

        # Check if the path should be excluded from PHI scanning
        if self._should_exclude_path(request.url.path):
            # logger.debug(f"[PHIMiddleware.dispatch] Path {request.url.path} excluded.")
            return await call_next(request)
        
        # Create a copy of the request with sanitized content
        sanitized_request = await self._sanitize_request(request)
        
        # Call the next middleware/route handler with sanitized request
        response = await call_next(sanitized_request)
        
        # Sanitize the response before returning it
        sanitized_response = await self._sanitize_response(response, request.url.path)
        
        return sanitized_response
    
    def _should_exclude_path(self, path: str) -> bool:
        """
        Check if a path should be excluded from PHI scanning.
        
        Args:
            path: The request path
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        # Skip PHI scanning for static files, health checks, etc.
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def _sanitize_request(self, request: Request) -> Request:
        """
        Sanitize the request body and headers for PHI.
        
        Args:
            request: The incoming request
            
        Returns:
            The sanitized request
        """
        # Clone the request before modifying it
        # Note: FastAPI doesn't provide an easy way to modify requests,
        # so we just log potential PHI in the request but don't modify it
        try:
            # Get request body
            body = await request.body()
            if body:
                body_str = body.decode('utf-8', errors='replace')
                # Check if body contains PHI using the service
                # if self.phi_detector.contains_phi(body_str):
                detected_phi_in_body = self.phi_service.detect_phi(body_str)
                if detected_phi_in_body:
                    if self.audit_mode:
                        # In audit mode, just log the potential PHI
                        logger.warning(
                            f"Potential PHI detected in request to {request.url.path}",
                            extra={"sanitized": True}
                        )
                    else:
                        # Log warning about PHI in request
                        # Sanitize using the service
                        # sanitized_body = self.phi_detector.sanitize_phi(body_str)
                        # Note: The middleware typically shouldn't modify the incoming request body.
                        # It should log/audit, and rely on response sanitization.
                        # We log the types found for better info.
                        phi_types_found = ", ".join(sorted(list(set([p[0].name for p in detected_phi_in_body]))))
                        logger.warning(
                            f"PHI ({phi_types_found}) detected in request to {request.url.path}",
                            extra={"sanitized": False} # Indicate request body was not sanitized
                        )
            
            # Check query parameters
            for key, value in request.query_params.items():
                # if self.phi_detector.contains_phi(value):
                if self.phi_service.contains_phi(value):
                    logger.warning(
                        f"Potential PHI detected in query parameter '{key}' "
                        f"for request to {request.url.path}",
                        extra={"sanitized": True}
                    )
            
            # Check headers (excluding common headers that never contain PHI)
            safe_headers = {'accept', 'accept-encoding', 'accept-language', 'connection', 
                          'content-length', 'content-type', 'host', 'user-agent'}
            for key, value in request.headers.items():
                # if key.lower() not in safe_headers and self.phi_detector.contains_phi(value):
                if key.lower() not in safe_headers and self.phi_service.contains_phi(value):
                    logger.warning(
                        f"Potential PHI detected in header '{key}' "
                        f"for request to {request.url.path}",
                        extra={"sanitized": True}
                    )
                    
        except Exception as e:
            logger.error(f"Error sanitizing request: {str(e)}")
        
        # Return the original request since we can't easily modify it
        return request
    
    async def _sanitize_response(self, response: Response, path: str) -> Response:
        """
        Sanitize the response body if it contains potential PHI and matches criteria.
        Handles both standard and streaming responses by reading the body once.
        
        Args:
            response: The Response object
            path: The request path
            
        Returns:
            Sanitized Response object
        """
        # Skip sanitization for excluded paths or non-success status codes
        if self._should_exclude_path(path) or not (200 <= response.status_code < 300):
            # logger.debug(f"[PHIMiddleware._sanitize_response] Skipping sanitization for path {path} or status {response.status_code}")
            return response

        # Get whitelisted patterns for the current path (currently unused but kept for future)
        # whitelist = self.whitelist_patterns.get(path, set())

        original_body_bytes: bytes = b""
        sanitized_body_bytes: bytes
        is_json_response = False
        original_media_type = response.media_type

        try:
            # --- Step 1: Read the entire response body once --- 
            # Primarily assume a streaming response from TestClient/Starlette
            # logger.debug(f"[PHIMiddleware._sanitize_response] Attempting to read response body via iterator for path: {path} (Type: {type(response).__name__})")
            try:
                body_chunks = [chunk async for chunk in response.body_iterator]
                original_body_bytes = b"".join(body_chunks)
                # logger.debug(f"[PHIMiddleware._sanitize_response] Read {len(original_body_bytes)} bytes via iterator.")
            except AttributeError:
                # Fallback for non-streaming responses (e.g., standard Response)
                # logger.warning(f"[PHIMiddleware._sanitize_response] Response type {type(response).__name__} lacks body_iterator. Attempting await response.body().")
                try:
                     original_body_bytes = await response.body() # type: ignore
                     # logger.debug(f"[PHIMiddleware._sanitize_response] Read {len(original_body_bytes)} bytes via await body().")
                except Exception as fallback_err:
                     logger.error(f"Could not read body using iterator or await body(): {fallback_err}")
                     original_body_bytes = b""
            except Exception as stream_err:
                logger.error(f"Error reading response body stream: {stream_err}")
                original_body_bytes = b""

            # Try to guess media type if it was None (often the case for StreamingResponse)
            if original_media_type is None and original_body_bytes:
                if original_body_bytes.strip().startswith(b'{') and original_body_bytes.strip().endswith(b'}'):
                    original_media_type = "application/json"
                    # logger.debug(f"[PHIMiddleware._sanitize_response] Guessed media type as application/json")
                # Add other guesses if needed (e.g., for HTML, XML)

            # Ensure original_body_bytes is assigned before proceeding
            sanitized_body_bytes = original_body_bytes 
            # logger.debug(f"[PHIMiddleware._sanitize_response] Original body read ({len(original_body_bytes)} bytes), Media Type: {original_media_type}")

            # --- Step 2: Attempt JSON sanitization if applicable --- 
            if original_media_type and "application/json" in original_media_type and original_body_bytes:
                is_json_response = True
                # logger.debug(f"[PHIMiddleware._sanitize_response] Attempting JSON sanitization for path: {path}")
                try:
                    body_str = original_body_bytes.decode('utf-8')
                    data = json.loads(body_str)
                    
                    # logger.info(f"---> PHIMiddleware: Data before sanitize (type {type(data)}): {str(data)[:500]}...")
                    sanitized_data = self.phi_service.sanitize(data, sensitivity="high")
                    # logger.info(f"---> PHIMiddleware: Data after sanitize (type {type(sanitized_data)}): {str(sanitized_data)[:500]}...")
                    
                    sanitized_body_bytes = json.dumps(sanitized_data).encode('utf-8')
                    # logger.debug(f"[PHIMiddleware._sanitize_response] JSON sanitization successful for path: {path}")
                except (UnicodeDecodeError, json.JSONDecodeError) as json_err:
                    logger.warning(f"Could not decode/parse JSON response for path {path}. Skipping sanitization. Error: {json_err}")
                    # Keep original_body_bytes in sanitized_body_bytes
                except Exception as sanitize_err:
                    logger.exception(f"Unexpected error during JSON sanitization for path {path}: {sanitize_err}")
                    # Keep original_body_bytes in sanitized_body_bytes
            else:
                 # logger.debug(f"[PHIMiddleware._sanitize_response] Skipping JSON sanitization for path: {path} (Not JSON or empty body)")
                 pass # No longer needed with pass

            # --- Step 3: Create a new standard Response --- 
            # Always create a new Response to ensure correct headers and content length.
            new_response = Response(
                content=sanitized_body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=original_media_type # Use the original/guessed media type
            )
            # Ensure content-length is updated if body changed
            if "content-length" in new_response.headers:
                 new_response.headers["content-length"] = str(len(sanitized_body_bytes))
                 
            # logger.debug(f"[PHIMiddleware._sanitize_response] Returning new Response for path: {path}")
            return new_response

        except Exception as e:
            response_type = type(response).__name__
            logger.exception(f"Critical error in _sanitize_response for {response_type} at path {path}: {str(e)}")
            # Fallback: return original response if critical error occurs
            # This might leak PHI in edge cases but prevents total failure.
            return response


def add_phi_middleware(
    app: FastAPI,
    exclude_paths: Optional[List[str]] = None,
    whitelist_patterns: Optional[Dict[str, List[str]]] = None,
    audit_mode: bool = False,
) -> None:
    """
    Adds the PHIMiddleware to the FastAPI application.

    Args:
        app: The FastAPI application instance.
        exclude_paths: List of path prefixes to exclude from PHI scanning.
        whitelist_patterns: Dict mapping paths to patterns that are allowed.
        audit_mode: If True, only log potential PHI without redacting.
    """
    # Instantiate the PHI service (could eventually use dependency injection)
    phi_service = PHIService()
    
    # Add the PHIMiddleware to the application
    app.add_middleware(
        PHIMiddleware,
        phi_service=phi_service,
        exclude_paths=exclude_paths,
        whitelist_patterns=whitelist_patterns,
        audit_mode=audit_mode,
    )
    logger.info("PHI Middleware added.")
