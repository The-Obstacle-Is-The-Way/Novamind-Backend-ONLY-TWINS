"""
PHI Sanitization utilities for the Novamind Digital Twin Backend.

This module provides tools for detecting and sanitizing Protected Health
Information (PHI) in various data structures to ensure HIPAA compliance.
"""
import re
from typing import Any, Dict, List, Optional, Pattern, Set, Union, Tuple


class PHISanitizer:
    """
    Utility class for sanitizing Protected Health Information (PHI).
    
    This class provides pattern-based detection and sanitization of PHI
    in strings, dictionaries, lists and other data structures to ensure
    HIPAA compliance in logging, error messages, and other outputs.
    """
    
    # PHI detection patterns
    _NAME_PATTERN: Pattern = re.compile(r'\b(?:[A-Z][a-z]+\s+){1,2}[A-Z][a-z]+\b')
    _EMAIL_PATTERN: Pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    _PHONE_PATTERN: Pattern = re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b')
    _SSN_PATTERN: Pattern = re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b')
    _DOB_PATTERN: Pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
    _MRN_PATTERN: Pattern = re.compile(r'\b(?:MRN|Medical Record Number|Patient ID)[: ]+[A-Za-z0-9-]+\b', re.IGNORECASE)
    _ADDRESS_PATTERN: Pattern = re.compile(r'\b\d+\s+[A-Za-z0-9\s.,]+(?:Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Ln|Rd|Blvd|Dr|St)\.?\s*,?\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}\b', re.IGNORECASE)
    
    # Collection of all PHI patterns
    _PHI_PATTERNS: List[Tuple[Pattern, str]] = [
        (_NAME_PATTERN, "[REDACTED NAME]"),
        (_EMAIL_PATTERN, "[REDACTED EMAIL]"),
        (_PHONE_PATTERN, "[REDACTED PHONE]"),
        (_SSN_PATTERN, "[REDACTED SSN]"),
        (_DOB_PATTERN, "[REDACTED DATE]"),
        (_MRN_PATTERN, "[REDACTED MRN]"),
        (_ADDRESS_PATTERN, "[REDACTED ADDRESS]")
    ]
    
    @classmethod
    def sanitize(cls, data: Any) -> Any:
        """
        Sanitize potential PHI from any data structure.
        
        This method detects the type of the input data and applies
        the appropriate sanitization method.
        
        Args:
            data: The data to sanitize
            
        Returns:
            Sanitized data with PHI removed
        """
        if data is None:
            return None
        elif isinstance(data, str):
            return cls.sanitize_text(data)
        elif isinstance(data, dict):
            return cls.sanitize_dict(data)
        elif isinstance(data, (list, tuple, set)):
            return cls.sanitize_collection(data)
        else:
            # For other types (int, float, bool, etc.), return as is
            return data
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize PHI from a text string.
        
        Args:
            text: The text to sanitize
            
        Returns:
            Sanitized text with PHI removed
        """
        if not text:
            return text
            
        sanitized = text
        for pattern, replacement in cls._PHI_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
            
        return sanitized
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize PHI from a dictionary.
        
        Args:
            data: The dictionary to sanitize
            
        Returns:
            Dictionary with sanitized values
        """
        sanitized = {}
        for key, value in data.items():
            # Always sanitize keys that might contain PHI
            sanitized_key = key
            if isinstance(key, str):
                sanitized_key = cls.sanitize_text(key)
                
            # Recursively sanitize values
            sanitized[sanitized_key] = cls.sanitize(value)
            
        return sanitized
    
    @classmethod
    def sanitize_collection(cls, data: Union[List[Any], Tuple[Any, ...], Set[Any]]) -> Union[List[Any], Tuple[Any, ...], Set[Any]]:
        """
        Recursively sanitize PHI from a list, tuple, or set.
        
        Args:
            data: The collection to sanitize
            
        Returns:
            Collection with sanitized values, preserving the original type
        """
        sanitized_items = [cls.sanitize(item) for item in data]
        
        # Return the same type as the input
        if isinstance(data, tuple):
            return tuple(sanitized_items)
        elif isinstance(data, set):
            return set(sanitized_items)
        else:
            return sanitized_items