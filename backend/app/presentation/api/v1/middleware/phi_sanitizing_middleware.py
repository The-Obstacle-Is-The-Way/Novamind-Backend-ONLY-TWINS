#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
PHI sanitizing middleware for FastAPI.
This middleware ensures all API requests and responses are properly sanitized
to prevent accidental PHI disclosure in accordance with HIPAA regulations.
"""

import json
import logging
from typing import Callable, Dict, Any, Optional, Union
import time
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse

from app.infrastructure.security.log_sanitizer import LogSanitizer
from app.core.utils.validation import PHIDetector


logger = logging.getLogger(__name__)


class PHISanitizingMiddleware(BaseHTTPMiddleware):
    """Middleware to sanitize PHI in API requests and responses."""
    
    def __init__(
        self, 
        app: ASGIApp,
        sanitizer: Optional[LogSanitizer] = None,
        exclude_paths: Optional[list[str]] = None,
        sanitize_responses: bool = True,
        sanitize_requests: bool = True,
        sanitize_headers: bool = True,
        audit_requests: bool = True
    ):
        """
        Initialize PHI sanitizing middleware.
        
        Args:
            app: The FastAPI application
            sanitizer: LogSanitizer to use (creates a new one if not provided)
            exclude_paths: List of paths to exclude from sanitization
            sanitize_responses: Whether to sanitize response bodies
            sanitize_requests: Whether to sanitize request bodies
            sanitize_headers: Whether to sanitize request/response headers
            audit_requests: Whether to log requests for auditing
        """
        super().__init__(app)
        self.sanitizer = sanitizer or LogSanitizer()
        self.exclude_paths = exclude_paths or []
        self.sanitize_responses = sanitize_responses
        self.sanitize_requests = sanitize_requests
        self.sanitize_headers = sanitize_headers
        self.audit_requests = audit_requests
        
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process an incoming request through the middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The sanitized response
        """
        # Skip sanitization for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate a request ID for tracing
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Record start time for performance monitoring
        start_time = time.time()
        
        # Process request (including sanitization if enabled)
        if self.sanitize_requests:
            await self._sanitize_request(request)
            
        # Create a response with PHI sanitization
        try:
            # Call the next middleware or endpoint handler
            response = await call_next(request)
            
            # Sanitize the response if needed
            if self.sanitize_responses:
                response = await self._sanitize_response(response)
                
            return response
        except Exception as e:
            # Log the exception with sanitization
            sanitized_exc = self.sanitizer.sanitize(str(e))
            logger.error(f"Request {request_id} failed: {sanitized_exc}")
            
            # Re-raise to allow FastAPI exception handlers to process it
            raise
        finally:
            # Log request completion for auditing
            if self.audit_requests:
                duration = time.time() - start_time
                self._audit_request(request, duration)
    
    async def _sanitize_request(self, request: Request) -> None:
        """
        Sanitize PHI in the request body and headers.
        
        Args:
            request: The request to sanitize
        """
        # Sanitize headers if enabled
        if self.sanitize_headers:
            # We can't modify headers directly, so we store the sanitized versions
            # in request.state for logging purposes
            sanitized_headers = {}
            for name, value in request.headers.items():
                # Don't sanitize some standard headers
                if name.lower() in {"content-type", "content-length", "authorization", 
                                   "user-agent", "accept", "host"}:
                    sanitized_headers[name] = value
                else:
                    sanitized_headers[name] = self.sanitizer.sanitize(value)
            request.state.sanitized_headers = sanitized_headers
        
        # Sanitize body for logging
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                # Read the request body
                body = await request.body()
                
                # If there's a body, try to parse and sanitize it
                if body:
                    try:
                        # Try to parse as JSON first
                        json_body = json.loads(body)
                        sanitized_body = self.sanitizer.sanitize(json_body)
                        request.state.sanitized_body = sanitized_body
                    except json.JSONDecodeError:
                        # Not JSON, sanitize as string
                        request.state.sanitized_body = self.sanitizer.sanitize(body.decode("utf-8"))
            except Exception as e:
                logger.warning(f"Could not sanitize request body: {str(e)}")
    
    async def _sanitize_response(self, response: Response) -> Response:
        """
        Sanitize PHI in the response.
        
        Args:
            response: The response to sanitize
            
        Returns:
            Sanitized response
        """
        # Skip sanitization for non-JSON responses
        if not isinstance(response, JSONResponse):
            return response
            
        # Sanitize headers if enabled
        if self.sanitize_headers:
            for name, value in response.headers.items():
                if name.lower() not in {"content-type", "content-length"}:
                    sanitized_value = self.sanitizer.sanitize(value)
                    if sanitized_value != value:
                        response.headers[name] = sanitized_value
        
        # Sanitize the response body
        try:
            # Get the response body as a dictionary
            body = response.body.decode("utf-8")
            body_dict = json.loads(body)
            
            # Sanitize the body
            sanitized_body = self.sanitizer.sanitize(body_dict)
            
            # Create a new response with the sanitized body
            return JSONResponse(
                content=sanitized_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception as e:
            logger.warning(f"Could not sanitize response body: {str(e)}")
            return response
    
    def _audit_request(self, request: Request, duration: float) -> None:
        """
        Log an audit record for the request.
        
        Args:
            request: The request to audit
            duration: Request processing duration in seconds
        """
        # Construct audit log entry with sanitized data
        audit_data = {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "method": request.method,
            "path": request.url.path,
            "client": self.sanitizer.sanitize(request.client.host if request.client else "unknown"),
            "duration_ms": int(duration * 1000),
            "status_code": getattr(request.state, "status_code", "unknown"),
        }
        
        # Add sanitized user ID if available
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            audit_data["user_id"] = self.sanitizer.sanitize(user_id)
            
        # Add sanitized request data if available
        if hasattr(request.state, "sanitized_body"):
            audit_data["request_body"] = request.state.sanitized_body
            
        # Log the sanitized audit data
        logger.info(f"API Request: {json.dumps(audit_data)}")


class PHIAuditMiddleware(BaseHTTPMiddleware):
    """Middleware to audit PHI exposure risks in API requests and responses."""
    
    def __init__(
        self, 
        app: ASGIApp,
        phi_detector: Optional[PHIDetector] = None,
        exclude_paths: Optional[list[str]] = None,
        audit_responses: bool = True,
        audit_requests: bool = True,
        audit_headers: bool = True,
        alert_on_phi: bool = True
    ):
        """
        Initialize PHI auditing middleware.
        
        Args:
            app: The FastAPI application
            phi_detector: PHI detector to use (creates a new one if not provided)
            exclude_paths: List of paths to exclude from auditing
            audit_responses: Whether to audit response bodies
            audit_requests: Whether to audit request bodies
            audit_headers: Whether to audit request/response headers
            alert_on_phi: Whether to log alerts when PHI is detected
        """
        super().__init__(app)
        self.phi_detector = phi_detector or PHIDetector()
        self.exclude_paths = exclude_paths or []
        self.audit_responses = audit_responses
        self.audit_requests = audit_requests
        self.audit_headers = audit_headers
        self.alert_on_phi = alert_on_phi
        
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process an incoming request through the middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response
        """
        # Skip auditing for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate a request ID for tracing
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Audit request if enabled
        if self.audit_requests:
            await self._audit_request(request)
            
        # Process the request normally
        response = await call_next(request)
        
        # Audit response if enabled
        if self.audit_responses:
            await self._audit_response(request, response)
            
        return response
    
    async def _audit_request(self, request: Request) -> None:
        """
        Audit the request for PHI.
        
        Args:
            request: The request to audit
        """
        # Audit headers if enabled
        if self.audit_headers:
            for name, value in request.headers.items():
                # Skip authorization headers
                if name.lower() == "authorization":
                    continue
                    
                # Check for PHI in header values
                if self.phi_detector.contains_phi(value):
                    self._log_phi_alert(
                        "request header", 
                        name, 
                        request.url.path, 
                        request.state.request_id
                    )
        
        # Audit body
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                # Read the request body
                body = await request.body()
                
                # If there's a body, check for PHI
                if body:
                    try:
                        # Try to parse as JSON first
                        json_body = json.loads(body)
                        self._audit_json(json_body, "request body", request.url.path, request.state.request_id)
                    except json.JSONDecodeError:
                        # Not JSON, check as string
                        body_str = body.decode("utf-8")
                        if self.phi_detector.contains_phi(body_str):
                            self._log_phi_alert(
                                "request body", 
                                "", 
                                request.url.path, 
                                request.state.request_id
                            )
            except Exception as e:
                logger.warning(f"Could not audit request body: {str(e)}")
    
    async def _audit_response(self, request: Request, response: Response) -> None:
        """
        Audit the response for PHI.
        
        Args:
            request: The original request
            response: The response to audit
        """
        # Audit headers if enabled
        if self.audit_headers:
            for name, value in response.headers.items():
                # Skip standard headers
                if name.lower() in {"content-type", "content-length"}:
                    continue
                    
                # Check for PHI in header values
                if self.phi_detector.contains_phi(value):
                    self._log_phi_alert(
                        "response header", 
                        name, 
                        request.url.path, 
                        request.state.request_id
                    )
        
        # Audit response body
        if isinstance(response, JSONResponse):
            try:
                # Get the response body as a dictionary
                body = response.body.decode("utf-8")
                body_dict = json.loads(body)
                
                # Audit the body
                self._audit_json(body_dict, "response body", request.url.path, request.state.request_id)
            except Exception as e:
                logger.warning(f"Could not audit response body: {str(e)}")
    
    def _audit_json(self, data: Any, context: str, path: str, request_id: str) -> None:
        """
        Audit JSON data for PHI.
        
        Args:
            data: The data to audit
            context: The context of the data (e.g., 'request body')
            path: The API path
            request_id: The request ID
        """
        # Handle dictionaries
        if isinstance(data, dict):
            for key, value in data.items():
                # Check if the value contains PHI
                if isinstance(value, (str, int, float, bool)) and self.phi_detector.contains_phi(str(value)):
                    self._log_phi_alert(
                        f"{context} field", 
                        key, 
                        path, 
                        request_id
                    )
                # Recursively check nested data
                elif isinstance(value, (dict, list)):
                    self._audit_json(value, f"{context}.{key}", path, request_id)
        
        # Handle lists
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, (str, int, float, bool)) and self.phi_detector.contains_phi(str(item)):
                    self._log_phi_alert(
                        f"{context} item", 
                        str(index), 
                        path, 
                        request_id
                    )
                # Recursively check nested data
                elif isinstance(item, (dict, list)):
                    self._audit_json(item, f"{context}[{index}]", path, request_id)
        
        # Handle primitives
        elif isinstance(data, (str, int, float, bool)) and self.phi_detector.contains_phi(str(data)):
            self._log_phi_alert(
                context, 
                "", 
                path, 
                request_id
            )
    
    def _log_phi_alert(self, context: str, field: str, path: str, request_id: str) -> None:
        """
        Log an alert when PHI is detected.
        
        Args:
            context: Where the PHI was found (e.g., 'request body')
            field: The field name containing PHI
            path: The API path
            request_id: The request ID
        """
        if not self.alert_on_phi:
            return
            
        field_info = f" in field '{field}'" if field else ""
        
        logger.warning(
            f"PHI ALERT: Potential PHI detected in {context}{field_info} "
            f"for API path '{path}' (request {request_id})"
        )


def configure_fastapi_phi_protection(app: ASGIApp) -> None:
    """
    Configure FastAPI with PHI protection middleware.
    
    Args:
        app: The FastAPI application
    """
    # Add PHI sanitizing middleware
    app.add_middleware(
        PHISanitizingMiddleware,
        exclude_paths=["/docs", "/redoc", "/openapi.json"],
        sanitize_responses=True,
        sanitize_requests=True,
        sanitize_headers=True,
        audit_requests=True
    )
    
    # Add PHI auditing middleware in non-production environments
    # This helps detect potential PHI leaks during development and testing
    from app.core.config import get_settings
    settings = get_settings()
    if settings.ENVIRONMENT != "production":
        app.add_middleware(
            PHIAuditMiddleware,
            exclude_paths=["/docs", "/redoc", "/openapi.json"],
            audit_responses=True,
            audit_requests=True,
            audit_headers=True,
            alert_on_phi=True
        )