# -*- coding: utf-8 -*-
"""
PHI Sanitizer Implementation

This module provides a HIPAA-compliant PHI sanitization implementation that
ensures Protected Health Information is properly detected and anonymized
in both logs and structured data.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from app.core.utils.phi_sanitizer import PHIType, PHIDetector, PHISanitizer as CorePHISanitizer

logger = logging.getLogger(__name__)


class PHISanitizer:
    """
    PHI Sanitizer for HIPAA-compliant data handling.
    
    This class provides methods to detect and sanitize Protected Health Information
    in strings, dictionaries, lists, and other data structures to ensure HIPAA compliance.
    """
    
    def __init__(self):
        """Initialize the PHI sanitizer with detection patterns."""
        self.core_sanitizer = CorePHISanitizer()
        
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize a string by replacing all detected PHI with redaction markers.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text with PHI replaced by redaction markers
        """
        if not text or not isinstance(text, str):
            return text
            
        return self.core_sanitizer.sanitize_text(text)
    
    def sanitize_json(self, json_str: str) -> str:
        """
        Sanitize a JSON string by parsing it, sanitizing fields, and reserializing.
        
        Args:
            json_str: JSON string to sanitize
            
        Returns:
            Sanitized JSON string
        """
        if not json_str or not isinstance(json_str, str):
            return json_str
            
        try:
            # Parse JSON to dictionary
            data = json.loads(json_str)
            
            # Sanitize the dictionary
            sanitized_data = self.sanitize_dict(data)
            
            # Reserialize to JSON
            return json.dumps(sanitized_data)
            
        except json.JSONDecodeError:
            # If not valid JSON, treat as regular text
            return self.sanitize_text(json_str)
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a dictionary by recursively sanitizing its values.
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        if not data or not isinstance(data, dict):
            return data
            
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self.sanitize_list(value)
            else:
                sanitized[key] = value
                
        return sanitized
    
    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Sanitize a list by recursively sanitizing its items.
        
        Args:
            data: List to sanitize
            
        Returns:
            Sanitized list
        """
        if not data or not isinstance(data, list):
            return data
            
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_text(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
                
        return sanitized


# Create a default instance for convenience
default_sanitizer = PHISanitizer()


def sanitize_phi(value: Any) -> Any:
    """
    Convenience function to sanitize PHI in any value.
    
    Args:
        value: Value to sanitize (string, dict, list, etc.)
        
    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        return default_sanitizer.sanitize_text(value)
    elif isinstance(value, dict):
        return default_sanitizer.sanitize_dict(value)
    elif isinstance(value, list):
        return default_sanitizer.sanitize_list(value)
    else:
        return value