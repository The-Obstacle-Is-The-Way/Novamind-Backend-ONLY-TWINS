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
        # Check if the path should be excluded from PHI scanning
        if self._should_exclude_path(request.url.path):
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
        
        Args:
            response: The Response object
            path: The request path
            
        Returns:
            Sanitized Response object
        """
        # Skip sanitization for excluded paths
        if self._should_exclude_path(path):
            return response

        # Get whitelisted patterns for the current path
        whitelist = self.whitelist_patterns.get(path, set())

        try:
            # Check if response has a body and is JSON
            # Note: response.media_type might be None
            if response.media_type and "application/json" in response.media_type:
                
                # Handle StreamingResponse differently
                if isinstance(response, StreamingResponse):
                    # Buffer the streaming response body
                    body_bytes = b""
                    async for chunk in response.body_iterator:
                        body_bytes += chunk
                    body_str = body_bytes.decode('utf-8')
                else:
                     # Read standard response body
                    response_body = await response.body()
                    # Ensure body is decoded correctly
                    try:
                        body_str = response_body.decode('utf-8')
                    except UnicodeDecodeError:
                         logger.warning(f"Could not decode response body as UTF-8 for path {path}. Skipping sanitization.")
                         return response # Cannot sanitize if not valid UTF-8

                # If body is empty, no need to sanitize
                if not body_str:
                    return response

                try:
                    # Parse JSON
                    data = json.loads(body_str)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON response body for path {path}. Skipping sanitization.")
                    # If we buffered a stream, we need to return the original content in a new response
                    if isinstance(response, StreamingResponse):
                         return Response(
                             content=body_bytes, # Use original bytes
                             status_code=response.status_code,
                             headers=dict(response.headers),
                             media_type=response.media_type
                         )
                    return response # Return original response if it wasn't a stream

                # DEBUG: Log data structure before sanitization
                logger.info(f"---> PHIMiddleware: Data before sanitize (type {type(data)}): {str(data)[:500]}...") 

                # Sanitize JSON data using the PHI Service
                # The PHIService.sanitize method should handle the recursive logic.
                # Use default sensitivity from the service for now -> Changed to high
                # sanitized_data = self.phi_service.sanitize(data)
                sanitized_data = self.phi_service.sanitize(data, sensitivity="high")

                # DEBUG: Log data structure after sanitization
                logger.info(f"---> PHIMiddleware: Data after sanitize (type {type(sanitized_data)}): {str(sanitized_data)[:500]}...")
                
                # Replace response body with sanitized data
                sanitized_body = json.dumps(sanitized_data).encode('utf-8')
                
                # Create a new response with sanitized body
                # Important: Always create a new standard Response after sanitizing
                # This handles both original standard responses and buffered streaming responses
                new_response = Response(
                    content=sanitized_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                return new_response
                
        except Exception as e:
            # Log the error and the type of response for better debugging
            response_type = type(response).__name__
            logger.exception(f"Error sanitizing {response_type} response for path {path}: {str(e)}") # Use logger.exception for stack trace
        
        # If we couldn't sanitize or don't need to, return original response
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
