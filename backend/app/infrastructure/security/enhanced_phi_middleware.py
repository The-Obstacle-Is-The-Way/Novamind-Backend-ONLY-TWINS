# -*- coding: utf-8 -*-
"""
Enhanced PHI Middleware for FastAPI

This module provides middleware for detecting and sanitizing PHI in request/response
data to ensure HIPAA compliance at the API level.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional, Union

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.utils.enhanced_phi_detector import EnhancedPHIDetector, EnhancedPHISanitizer
from app.infrastructure.logging.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class EnhancedPHIMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detecting and sanitizing PHI in request/response data.
    
    This middleware intercepts requests and responses to ensure no PHI is
    accidentally leaked through API endpoints. It uses the EnhancedPHIDetector
    to identify potential PHI and sanitizes it when necessary.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        audit_logger: Optional[AuditLogger] = None,
        exclude_paths: Optional[list] = None,
        sanitize_responses: bool = True,
        block_phi_in_requests: bool = False
    ):
        """
        Initialize the PHI middleware.
        
        Args:
            app: The ASGI application
            audit_logger: Optional audit logger for recording PHI detection events
            exclude_paths: List of path prefixes to exclude from PHI checking
            sanitize_responses: Whether to sanitize PHI in responses
            block_phi_in_requests: Whether to block requests containing PHI
        """
        super().__init__(app)
        self.audit_logger = audit_logger
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/health"]
        self.sanitize_responses = sanitize_responses
        self.block_phi_in_requests = block_phi_in_requests
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request and response through PHI detection and sanitization.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The processed response
        """
        # Skip excluded paths
        if self._should_skip_path(request.url.path):
            return await call_next(request)
        
        # Check for PHI in request
        phi_detected = await self._check_request_for_phi(request)
        
        # If PHI detected in request and blocking is enabled, return error
        if phi_detected and self.block_phi_in_requests:
            return self._create_phi_detected_response()
        
        # Process the request
        response = await call_next(request)
        
        # Check and sanitize response if needed
        if self.sanitize_responses:
            response = await self._process_response(response)
        
        return response
    
    def _should_skip_path(self, path: str) -> bool:
        """
        Check if the path should be excluded from PHI checking.
        
        Args:
            path: The request path
            
        Returns:
            True if the path should be skipped, False otherwise
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def _check_request_for_phi(self, request: Request) -> bool:
        """
        Check if the request contains PHI.
        
        Args:
            request: The incoming request
            
        Returns:
            True if PHI is detected, False otherwise
        """
        # Check query parameters
        for param, value in request.query_params.items():
            if EnhancedPHIDetector.contains_phi(value):
                self._log_phi_detection("query parameter", request)
                return True
        
        # Check request body if it exists
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Clone the request body
                body_bytes = await request.body()
                
                # If there's a body, check it for PHI
                if body_bytes:
                    # Try to parse as JSON
                    try:
                        body = json.loads(body_bytes)
                        # Check JSON body recursively
                        if self._check_json_for_phi(body):
                            self._log_phi_detection("request body", request)
                            return True
                    except json.JSONDecodeError:
                        # If not JSON, check as string
                        if EnhancedPHIDetector.contains_phi(body_bytes.decode()):
                            self._log_phi_detection("request body", request)
                            return True
            except Exception as e:
                logger.warning(f"Error checking request body for PHI: {str(e)}")
        
        return False
    
    def _check_json_for_phi(self, data: Union[Dict, list, Any]) -> bool:
        """
        Recursively check JSON data for PHI.
        
        Args:
            data: The JSON data to check
            
        Returns:
            True if PHI is detected, False otherwise
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Check the key itself
                if EnhancedPHIDetector.contains_phi(key):
                    return True
                
                # Check the value
                if isinstance(value, (dict, list)):
                    if self._check_json_for_phi(value):
                        return True
                elif isinstance(value, str) and EnhancedPHIDetector.contains_phi(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    if self._check_json_for_phi(item):
                        return True
                elif isinstance(item, str) and EnhancedPHIDetector.contains_phi(item):
                    return True
        elif isinstance(data, str) and EnhancedPHIDetector.contains_phi(data):
            return True
        
        return False
    
    async def _process_response(self, response: Response) -> Response:
        """
        Process the response to sanitize any PHI.
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        # Only process JSON responses
        if not isinstance(response, JSONResponse):
            return response
        
        # Get the response body
        body = response.body
        
        try:
            # Parse the JSON body
            data = json.loads(body)
            
            # Sanitize the data
            sanitized_data = EnhancedPHISanitizer.sanitize_structured_data(data)
            
            # Create a new response with sanitized data
            return JSONResponse(
                content=sanitized_data,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        except Exception as e:
            logger.warning(f"Error sanitizing response: {str(e)}")
            return response
    
    def _create_phi_detected_response(self) -> JSONResponse:
        """
        Create an error response for PHI detection.
        
        Returns:
            A JSON response indicating PHI was detected
        """
        return JSONResponse(
            status_code=400,
            content={
                "error": "PHI detected in request",
                "message": "Protected Health Information (PHI) was detected in your request. "
                           "Please remove any personal identifiers and try again."
            }
        )
    
    def _log_phi_detection(self, location: str, request: Request) -> None:
        """
        Log a PHI detection event.
        
        Args:
            location: Where the PHI was detected
            request: The request containing PHI
        """
        # Log the detection
        logger.warning(
            f"Potential PHI detected in {location}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        # Record audit event if audit logger is available
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type="phi_detection",
                user_id=getattr(request.state, "user_id", None),
                resource_type="api",
                resource_id=request.url.path,
                action="detect_phi",
                status="warning",
                details={
                    "location": location,
                    "method": request.method,
                    "path": request.url.path
                }
            )


def setup_enhanced_phi_middleware(
    app: ASGIApp,
    audit_logger: Optional[AuditLogger] = None,
    exclude_paths: Optional[list] = None,
    sanitize_responses: bool = True,
    block_phi_in_requests: bool = False
) -> None:
    """
    Set up the enhanced PHI middleware for a FastAPI application.
    
    Args:
        app: The FastAPI application
        audit_logger: Optional audit logger for recording PHI detection events
        exclude_paths: List of path prefixes to exclude from PHI checking
        sanitize_responses: Whether to sanitize PHI in responses
        block_phi_in_requests: Whether to block requests containing PHI
    """
    app.add_middleware(
        EnhancedPHIMiddleware,
        audit_logger=audit_logger,
        exclude_paths=exclude_paths,
        sanitize_responses=sanitize_responses,
        block_phi_in_requests=block_phi_in_requests
    )