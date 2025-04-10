# -*- coding: utf-8 -*-
"""
PHI Sanitization Utility

This module provides utilities for sanitizing Protected Health Information (PHI)
to ensure HIPAA compliance in logs, error messages, and other outputs.
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Set, Union
from enum import Enum, auto


class PHISanitizer:
    """
    Utility class for sanitizing PHI data from various sources.
    
    This class provides methods to detect and redact PHI in strings, log messages,
    error messages, and API responses to ensure HIPAA compliance.
    """
    
    # PHI patterns to detect and sanitize
    PHI_PATTERNS = {
        # Define patterns with careful attention to specificity
        'ssn': re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'),  # Social Security Numbers
        'address': re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Ln|Rd|Blvd|Dr|St)\.?\b', re.IGNORECASE),  # Addresses
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email addresses
        'phone': re.compile(r'(?:\+\d{1,2}\s)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'),  # Phone numbers with international format support
        'dob': re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'),  # Dates of birth
        'name': re.compile(r'\b(?:[A-Z][a-z]+ ){1,2}[A-Z][a-z]+\b'),  # Full names
        'mrn': re.compile(r'\b(?<!\-)\d{5,10}\b(?!\-)'),  # Medical Record Numbers with negative lookahead/lookbehind
    }
    
    # Define the order in which patterns should be applied
    PATTERN_ORDER = [
        'ssn',      # Check for SSNs first
        'address',  # Check addresses before names (to avoid partial matches)
        'email',
        'phone',
        'dob',
        'name',
        'mrn',      # Check MRNs last (as they're less specific)
    ]
    
    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """
        Sanitize a string by redacting potential PHI.
        
        Args:
            text: The input string to sanitize
            
        Returns:
            str: Sanitized string with PHI replaced by [REDACTED]
        """
        if not text:
            return text
            
        sanitized = text
        
        # Apply patterns in the specified order for consistent results
        for phi_type in cls.PATTERN_ORDER:
            pattern = cls.PHI_PATTERNS.get(phi_type)
            if pattern:
                sanitized = pattern.sub(f"[{phi_type.upper()} REDACTED]", sanitized)
            
        return sanitized
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], 
                      exclude_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Sanitize a dictionary by redacting potential PHI in string values.
        
        Args:
            data: The input dictionary to sanitize
            exclude_keys: Optional set of keys to exclude from sanitization
            
        Returns:
            Dict[str, Any]: Sanitized dictionary with PHI values replaced
        """
        if not data:
            return data
            
        sanitized = {}
        exclude = exclude_keys or set()
        
        for key, value in data.items():
            if key in exclude:
                sanitized[key] = value
            elif isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, exclude_keys)
            elif isinstance(value, list):
                sanitized[key] = cls.sanitize_list(value, exclude_keys)
            else:
                sanitized[key] = value
                
        return sanitized
    
    @classmethod
    def sanitize_list(cls, data: List[Any], 
                      exclude_keys: Optional[Set[str]] = None) -> List[Any]:
        """
        Sanitize a list by redacting potential PHI in its items.
        
        Args:
            data: The input list to sanitize
            exclude_keys: Optional set of keys to exclude from sanitization
                          (applies to dictionaries in the list)
            
        Returns:
            List[Any]: Sanitized list with PHI values replaced
        """
        if not data:
            return data
            
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(cls.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(cls.sanitize_dict(item, exclude_keys))
            elif isinstance(item, list):
                sanitized.append(cls.sanitize_list(item, exclude_keys))
            else:
                sanitized.append(item)
                
        return sanitized
    
    @classmethod
    def sanitize_error_message(cls, message: str) -> str:
        """
        Sanitize an error message by redacting potential PHI.
        
        Args:
            message: The error message to sanitize
            
        Returns:
            str: Sanitized error message with PHI replaced
        """
        return cls.sanitize_string(message)
    
    @classmethod
    def sanitize_log_entry(cls, log_entry: str) -> str:
        """
        Sanitize a log entry by redacting potential PHI.
        
        Args:
            log_entry: The log entry to sanitize
            
        Returns:
            str: Sanitized log entry with PHI replaced
        """
        return cls.sanitize_string(log_entry)
    
    @classmethod
    def update_patterns(cls, new_patterns: Dict[str, Pattern]) -> None:
        """
        Update the PHI detection patterns with new patterns.
        
        Args:
            new_patterns: Dictionary of new pattern names and compiled regex patterns
        """
        cls.PHI_PATTERNS.update(new_patterns)
        
        # Update pattern order list if new types are added
        for pattern_type in new_patterns.keys():
            if pattern_type not in cls.PATTERN_ORDER:
                cls.PATTERN_ORDER.append(pattern_type)


# --- Added Missing Definitions ---

class PHIType(Enum):
    """Enumeration of PHI types for classification."""
    SSN = auto()
    ADDRESS = auto()
    EMAIL = auto()
    PHONE = auto()
    DOB = auto()
    NAME = auto()
    MRN = auto()
    CREDIT_CARD = auto() # Example, add others as needed
    OTHER = auto()


class PHIDetector:
    """Base class or interface placeholder for PHI detection logic."""
    # In a real implementation, this might define abstract methods
    # for detecting PHI based on patterns or models.
    def detect(self, text: str) -> List[Dict[str, Any]]:
        """Detect PHI instances in text."""
        # Placeholder implementation
        return []