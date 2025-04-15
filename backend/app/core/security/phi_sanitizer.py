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
    
    # Refined PHI detection patterns with priorities
    # Priority: Higher number = higher priority (matched first in overlaps)
    _PHI_PATTERNS_DEFINITIONS: List[Dict[str, Any]] = [
        {
            "name": "Medical Record Number", "priority": 10, "label": "[REDACTED MRN]",
            "pattern": r'\b(?:MRN#?|Medical Record Number|Patient ID|MR#?)[: ]*\d{5,10}\b', "flags": re.IGNORECASE
        },
        {
            "name": "SSN", "priority": 10, "label": "[REDACTED SSN]",
            "pattern": r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
        },
        {
            "name": "Address", "priority": 9, "label": "[REDACTED ADDRESS]",
            "pattern": r'\b\d+\s+[A-Z0-9][a-zA-Z0-9\s.,]+(?:St|Street|Ave|Avenue|Rd|Road|Ln|Lane|Dr|Drive|Ct|Court|Pl|Place|Blvd|Boulevard)\b', "flags": re.IGNORECASE
        },
        {
            "name": "Credit Card", "priority": 8, "label": "[REDACTED CARD]",
            "pattern": r'\b(?:4[0-9]{3}[ -]?[0-9]{4}[ -]?[0-9]{4}[ -]?[0-9]{4}|5[1-5][0-9]{2}[ -]?[0-9]{4}[ -]?[0-9]{4}[ -]?[0-9]{4}|3[47][0-9]{2}[ -]?[0-9]{6}[ -]?[0-9]{5}|6(?:011|5[0-9]{2})[ -]?[0-9]{4}[ -]?[0-9]{4}[ -]?[0-9]{4})\b'
        },
        {
            "name": "Email", "priority": 8, "label": "[REDACTED EMAIL]",
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        },
        {
            "name": "Phone", "priority": 7, "label": "[REDACTED PHONE]",
            "pattern": r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
        },
        {
            "name": "Date of Birth", "priority": 6, "label": "[REDACTED DATE]",
            "pattern": r'\b(?:(?:DOB|Date of Birth|Born|Birthdate)[: ]+)?(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?[\s,.\/-]+\d{2,4})\b|\b(?:(?:DOB|Date of Birth|Born|Birthdate)[: ]+)?\d{1,2}[\s.\/-]\d{1,2}[\s.\/-]\d{2,4}\b', "flags": re.IGNORECASE
        },
        {
            "name": "Age", "priority": 5, "label": "[REDACTED AGE]",
            "pattern": r'\b(?:age|aged)\s+\d{1,3}\b|\b\d{1,3}\s+years?(?:\s+old)?\b', "flags": re.IGNORECASE
        },
        {
            "name": "Name", "priority": 4, "label": "[REDACTED NAME]",
            "pattern": r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*[A-Z][a-z\'-]+(?:\s+[A-Z][a-z\'-]+){1,2}\b' # Case-sensitive
        }
    ]

    # Compiled patterns stored for efficiency
    _COMPILED_PHI_PATTERNS: List[Dict[str, Any]] = []

    def __init__(self):
        """Initialize the sanitizer and compile patterns."""
        if not PHISanitizer._COMPILED_PHI_PATTERNS: # Compile only once
            for p_def in PHISanitizer._PHI_PATTERNS_DEFINITIONS:
                flags = p_def.get("flags", 0)
                PHISanitizer._COMPILED_PHI_PATTERNS.append({
                    **p_def,
                    "compiled": re.compile(p_def["pattern"], flags)
                })
            # Sort compiled patterns by priority (desc) for processing order
            PHISanitizer._COMPILED_PHI_PATTERNS.sort(key=lambda p: p["priority"], reverse=True)
    
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
    
    # Keep sanitize method as the main entry point
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize PHI from a text string using robust overlap handling.

        Args:
            text: The text to sanitize

        Returns:
            Sanitized text with PHI removed
        """
        if not text or not isinstance(text, str):
            return text

        matches_found = []
        text_length = len(text)

        # 1. Find all potential matches for all compiled patterns
        for pattern_info in cls._COMPILED_PHI_PATTERNS:
            pattern = pattern_info["compiled"]
            for match in pattern.finditer(text):
                start, end = max(0, match.start()), min(text_length, match.end())
                if start < end:
                    matches_found.append({
                        "start": start, "end": end, "pattern_info": pattern_info,
                        "matched_text": match.group(0), "priority": pattern_info["priority"],
                        "length": end - start
                    })

        if not matches_found:
            return text

        # 2. Resolve overlaps based on priority using a coverage tracker
        matches_found.sort(key=lambda m: (m["priority"], m["length"], -m["start"]), reverse=True)

        covered = [False] * text_length
        final_matches = []

        for match in matches_found:
            start, end = match["start"], match["end"]
            is_overlapped = any(covered[i] for i in range(start, end))
            if not is_overlapped:
                for i in range(start, end):
                    covered[i] = True
                final_matches.append(match)

        # 3. Apply replacements in reverse order
        result = list(text)
        final_matches.sort(key=lambda m: m["start"], reverse=True)

        for match in final_matches:
            start, end = match["start"], match["end"]
            replacement_label = match["pattern_info"]["label"]
            # Simple replacement with the label for now
            # TODO: Integrate redaction strategies if needed later
            result[start:end] = list(replacement_label)

        sanitized = "".join(result)
        # Optional: Remove leftover parens/brackets (consider if needed with new logic)
        # sanitized = re.sub(r'[\(\[]+\s*\[REDACTED ([A-Z ]+)\]\s*[\)\]]+', r'[REDACTED \1]', sanitized)
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
