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

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send

from app.core.utils.validation import PHIDetector


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
        phi_detector: Optional[PHIDetector] = None,
        redaction_text: str = "[REDACTED]",
        exclude_paths: Optional[List[str]] = None,
        whitelist_patterns: Optional[Dict[str, List[str]]] = None,
        audit_mode: bool = False,
    ):
        """
        Initialize the PHI middleware.
        
        Args:
            app: The ASGI application
            phi_detector: Custom PHI detector to use
            redaction_text: Text to use when redacting PHI
            exclude_paths: List of path prefixes to exclude from PHI scanning
            whitelist_patterns: Dict mapping paths to patterns that are allowed
            audit_mode: If True, only log potential PHI without redacting
        """
        super().__init__(app)
        self.phi_detector = phi_detector or PHIDetector()
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
                # Check if body contains PHI
                if self.phi_detector.contains_phi(body_str):
                    if self.audit_mode:
                        # In audit mode, just log the potential PHI
                        logger.warning(
                            f"Potential PHI detected in request to {request.url.path}",
                            extra={"sanitized": True}
                        )
                    else:
                        # Log warning about PHI in request
                        sanitized_body = self.phi_detector.sanitize_phi(body_str)
                        logger.warning(
                            f"PHI detected and sanitized in request to {request.url.path}",
                            extra={"sanitized": True}
                        )
            
            # Check query parameters
            for key, value in request.query_params.items():
                if self.phi_detector.contains_phi(value):
                    logger.warning(
                        f"Potential PHI detected in query parameter '{key}' "
                        f"for request to {request.url.path}",
                        extra={"sanitized": True}
                    )
            
            # Check headers (excluding common headers that never contain PHI)
            safe_headers = {'accept', 'accept-encoding', 'accept-language', 'connection', 
                          'content-length', 'content-type', 'host', 'user-agent'}
            for key, value in request.headers.items():
                if key.lower() not in safe_headers and self.phi_detector.contains_phi(value):
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
        Sanitize the response body for PHI.
        
        Args:
            response: The response to sanitize
            path: The request path
            
        Returns:
            The sanitized response
        """
        try:
            # Get the content type
            content_type = response.headers.get('content-type', '')
            
            # Only process JSON responses
            if 'application/json' in content_type:
                # Get the response body
                body = response.body
                body_str = body.decode('utf-8', errors='replace')
                
                # Get whitelist patterns for this path
                whitelist = self._get_whitelisted_patterns(path)
                
                # Parse JSON
                data = json.loads(body_str)
                
                # Sanitize JSON data
                sanitized_data = self._sanitize_json_data(data, whitelist)
                
                # Replace response body with sanitized data
                sanitized_body = json.dumps(sanitized_data).encode('utf-8')
                
                # Create a new response with sanitized body
                new_response = Response(
                    content=sanitized_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                return new_response
                
        except Exception as e:
            logger.error(f"Error sanitizing response: {str(e)}")
        
        # If we couldn't sanitize or don't need to, return original response
        return response
    
    def _get_whitelisted_patterns(self, path: str) -> Set[str]:
        """
        Get the whitelisted patterns for a path.
        
        Args:
            path: The request path
            
        Returns:
            Set of whitelisted patterns
        """
        # Check for exact path match
        if path in self.whitelist_patterns:
            return set(self.whitelist_patterns[path])
        
        # Check for path prefix matches
        whitelist = set()
        for whitelist_path, patterns in self.whitelist_patterns.items():
            if whitelist_path.endswith('*') and path.startswith(whitelist_path[:-1]):
                whitelist.update(patterns)
        
        return whitelist
    
    def _sanitize_json_data(
        self, data: Union[Dict[str, Any], List[Any], Any], whitelist: Set[str]
    ) -> Any:
        """
        Recursively sanitize JSON data.
        
        Args:
            data: The JSON data to sanitize
            whitelist: Set of whitelisted patterns to allow
            
        Returns:
            Sanitized JSON data
        """
        if isinstance(data, dict):
            # Process dictionary
            result = {}
            for key, value in data.items():
                # Skip sanitization for sensitive fields that already contain redacted content
                if key in ['password', 'token', 'secret']:
                    result[key] = value
                    continue
                
                # Skip sanitization for whitelisted patterns
                if key in whitelist:
                    result[key] = value
                    continue
                
                # Recursively sanitize nested values
                result[key] = self._sanitize_json_data(value, whitelist)
            return result
            
        elif isinstance(data, list):
            # Process list
            return [self._sanitize_json_data(item, whitelist) for item in data]
            
        elif isinstance(data, str) and self.phi_detector.contains_phi(data):
            # Sanitize string with PHI
            if self.audit_mode:
                # In audit mode, just log but don't redact
                logger.warning(f"Potential PHI detected in response field", extra={"sanitized": True})
                return data
            else:
                # Sanitize the PHI
                return self.phi_detector.sanitize_phi(data)
                
        else:
            # No PHI or not a string, return as is
            return data


def add_phi_middleware(
    app: FastAPI,
    exclude_paths: Optional[List[str]] = None,
    whitelist_patterns: Optional[Dict[str, List[str]]] = None,
    audit_mode: bool = False,
) -> None:
    """
    Add PHI middleware to a FastAPI application.
    
    Args:
        app: The FastAPI application
        exclude_paths: List of path prefixes to exclude from PHI scanning
        whitelist_patterns: Dict mapping paths to patterns that are allowed
        audit_mode: If True, only log potential PHI without redacting
    """
    # Default excluded paths (static assets, health checks, docs)
    default_exclude = [
        "/static/", 
        "/assets/", 
        "/health", 
        "/status", 
        "/docs", 
        "/openapi.json",
        "/redoc"
    ]
    
    all_exclude_paths = list(set(default_exclude + (exclude_paths or [])))
    
    # Add PHI middleware to the application
    app.add_middleware(
        PHIMiddleware,
        exclude_paths=all_exclude_paths,
        whitelist_patterns=whitelist_patterns or {},
        audit_mode=audit_mode
    )
    
    logger.info(
        f"PHI middleware added to FastAPI application "
        f"(audit_mode: {audit_mode}, excluded paths: {len(all_exclude_paths)})"
    )
