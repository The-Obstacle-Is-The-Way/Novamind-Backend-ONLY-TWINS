"""
PHI sanitization utilities for HIPAA compliance.

This module provides tools to detect and sanitize Protected Health Information (PHI)
from various data structures before logging, error reporting, or external transmission.
"""

import re
from typing import Dict, List, Any, Union, Pattern, Optional


class PHISanitizer:
    """
    Class responsible for sanitizing Protected Health Information (PHI) from data.
    
    This sanitizer can detect and redact common PHI patterns in strings, or recursively
    process complex data structures (dictionaries, lists) to sanitize PHI at all levels.
    """
    
    # Default PHI patterns to detect
    DEFAULT_PHI_PATTERNS = [
        # Names (first and last names adjacent to each other)
        r'(?i)\b[A-Z][a-z]+ [A-Z][a-z]+\b',
        
        # Email addresses
        r'(?i)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        
        # US Social Security Numbers
        r'\b\d{3}-\d{2}-\d{4}\b',
        
        # US Phone numbers
        r'(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
        
        # Dates that could be birthdates
        r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
        
        # Street addresses
        r'\b\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Court|Ct|Lane|Ln|Way|Parkway|Pkwy|Place|Pl)\b',
        
        # ZIP codes
        r'\b\d{5}(?:-\d{4})?\b',
        
        # Medical Record Numbers (common formats)
        r'\b(?:MRN)?[A-Z0-9]{6,10}\b',
        
        # Health plan beneficiary numbers
        r'\b[A-Z]{1,2}[0-9]{6,12}\b',
        
        # Account numbers
        r'\bACC[0-9]{6,12}\b',
        
        # Certificate/license numbers
        r'\b(?:LIC|CERT)[A-Z0-9]{6,12}\b',
        
        # Vehicle identifiers
        r'\b[A-Z0-9]{1,3}[\s-]?[A-Z0-9]{3,7}\b',
        
        # Device identifiers and serial numbers
        r'\b(?:DEV|SN)[A-Z0-9]{6,12}\b',
        
        # Biometric identifiers
        r'\b(?:BIO|BIOID)[A-Z0-9]{6,12}\b',
        
        # URLs containing identifiable information
        r'https?://[^\s/$.?#].[^\s]*(?:patient|profile|id)[=][^\s&]+',
        
        # IP addresses
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ]
    
    def __init__(self, additional_patterns: Optional[List[str]] = None):
        """
        Initialize the PHI sanitizer with default and custom patterns.
        
        Args:
            additional_patterns: Optional list of additional regex patterns to detect as PHI
        """
        patterns = self.DEFAULT_PHI_PATTERNS.copy()
        
        if additional_patterns:
            patterns.extend(additional_patterns)
        
        # Compile patterns for better performance
        self.patterns = [re.compile(pattern) for pattern in patterns]
    
    def sanitize(self, data: Any) -> Any:
        """
        Sanitize PHI from any data structure.
        
        This method can handle strings, dictionaries, lists, and nested combinations.
        The original structure is preserved, but PHI content is replaced with [REDACTED].
        
        Args:
            data: The data to sanitize, can be a string, dict, list, or nested structure
            
        Returns:
            The sanitized data with the same structure as the input
        """
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return self._sanitize_list(data)
        else:
            # For other data types (int, float, bool, None), return as is
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """
        Sanitize PHI from a string by replacing matches with [REDACTED].
        
        Args:
            text: The string to sanitize
            
        Returns:
            The sanitized string with PHI replaced by [REDACTED]
        """
        sanitized = text
        for pattern in self.patterns:
            sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize PHI from a dictionary and its nested structures.
        
        Args:
            data: The dictionary to sanitize
            
        Returns:
            A new dictionary with the same structure but sanitized values
        """
        result = {}
        for key, value in data.items():
            result[key] = self.sanitize(value)
        return result
    
    def _sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively sanitize PHI from a list and its items.
        
        Args:
            data: The list to sanitize
            
        Returns:
            A new list with the same structure but sanitized items
        """
        return [self.sanitize(item) for item in data]