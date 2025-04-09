# -*- coding: utf-8 -*-
"""
PHI Detection and Validation Utility.

This module provides utilities for detecting and validating Protected Health Information (PHI)
in various formats to ensure HIPAA compliance across the platform.
"""

import re
from typing import List, Optional, Union, Dict, Any, Pattern


class PHIMatch:
    """Represents a matched PHI instance in text content."""

    def __init__(self, phi_type: str, value: str, position: int):
        """
        Initialize a PHI match.

        Args:
            phi_type: Type of PHI detected (e.g., SSN, NAME, EMAIL)
            value: The PHI value that was detected
            position: Character position in the text where PHI was found
        """
        self.phi_type = phi_type
        self.value = value
        self.position = position

    def __repr__(self) -> str:
        """Return string representation of the PHI match."""
        # Mask the actual PHI value in logs
        return f"PHIMatch(type={self.phi_type}, value=[REDACTED], position={self.position})"


class PHIDetector:
    """
    Detects and validates Protected Health Information (PHI) in content.
    
    This class provides robust pattern matching to identify various types of PHI
    including SSNs, names, addresses, phone numbers, etc. to ensure HIPAA compliance.
    """

    def __init__(self, custom_patterns: Optional[Dict[str, Pattern]] = None):
        """
        Initialize the PHI detector with configurable patterns.

        Args:
            custom_patterns: Optional dictionary of custom regex patterns to use
                            instead of or in addition to the default patterns
        """
        # Default patterns for various PHI types
        self.patterns = {
            # Social Security Numbers in various formats
            'SSN': re.compile(
                r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b|'  # Basic formats: 123-45-6789, 123 45 6789
                r'"\d{3}-\d{2}-\d{4}"|'              # Double-quoted: "123-45-6789"
                r'"\d{3}\s\d{2}\s\d{4}"|'            # Double-quoted with spaces: "123 45 6789"
                r'\'\d{3}-\d{2}-\d{4}\'|'            # Single-quoted: '123-45-6789'
                r'\'(?:\d{3})[- ]?(?:\d{2})[- ]?(?:\d{4})\'|'  # General single-quoted
                r'[=:]\s*[\'"]?\d{3}-\d{2}-\d{4}[\'"]?|'       # Assignment with quotes
                r'ssn\s*[=:]\s*[\'"]?\d{3}[- ]?\d{2}[- ]?\d{4}[\'"]?',  # Explicit SSN assignment
                re.IGNORECASE
            ),
            
            # Email addresses
            'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            
            # Phone numbers in various formats
            'PHONE': re.compile(
                r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b|'  # Standard formats
                r'phone\s*[=:]\s*[\'"]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}[\'"]?',  # Assignments
                re.IGNORECASE
            ),
            
            # Medical Record Numbers
            'MRN': re.compile(
                r'\bMRN\s*[#:]?\s*\d{5,10}\b|'  # Basic MRN format
                r'medical[\s_-]*record[\s_-]*number[\s_-]*[#:]?\s*\d{5,10}',  # Explicit MRN
                re.IGNORECASE
            ),
            
            # Full names (2+ words starting with capital letters)
            'NAME': re.compile(
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b|'  # Basic name format: John Doe
                r'name\s*[=:]\s*[\'"]?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+[\'"]?',  # Assignment
                re.IGNORECASE
            ),
            
            # Dates of birth
            'DOB': re.compile(
                r'\b\d{1,2}/\d{1,2}/\d{4}\b|'  # MM/DD/YYYY
                r'\b\d{4}-\d{1,2}-\d{1,2}\b|'  # YYYY-MM-DD
                r'(?:DOB|Date\s+of\s+Birth)[:\s]+\d{1,2}[/.-]\d{1,2}[/.-]\d{4}',  # Labeled DOB
                re.IGNORECASE
            ),
            
            # Addresses with street information
            'ADDRESS': re.compile(
                r'\b\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Lane|Ln|Place|Pl|Court|Ct|Circle|Cir|Highway|Hwy|Way)\b',
                re.IGNORECASE
            ),
            
            # Credit card numbers
            'CREDIT_CARD': re.compile(
                r'\b(?:\d{4}[- ]?){3}\d{4}\b|'  # Basic 16-digit format with separators
                r'\b\d{13,16}\b'  # Continuous digit format
            )
        }
        
        # Merge or replace with custom patterns if provided
        if custom_patterns:
            for key, pattern in custom_patterns.items():
                self.patterns[key] = pattern

    def detect_phi(self, content: str) -> List[PHIMatch]:
        """
        Detect PHI in the provided content.
        
        Args:
            content: Text content to scan for PHI
            
        Returns:
            List of PHIMatch objects for each detected PHI instance
        """
        if not isinstance(content, str):
            return []
            
        found_phi = []
        for phi_type, pattern in self.patterns.items():
            matches = pattern.finditer(content)
            for match in matches:
                found_phi.append(PHIMatch(
                    phi_type=phi_type,
                    value=match.group(0),
                    position=match.start()
                ))
                
        return found_phi
    
    def contains_phi(self, content: str) -> bool:
        """
        Check if the content contains any PHI.
        
        Args:
            content: Text content to check
            
        Returns:
            True if PHI is detected, False otherwise
        """
        return len(self.detect_phi(content)) > 0
    
    def sanitize_phi(self, content: str) -> str:
        """
        Replace all detected PHI with [REDACTED] marker.
        
        Args:
            content: Text content to sanitize
            
        Returns:
            Sanitized content with PHI replaced by [REDACTED]
        """
        if not isinstance(content, str):
            return content
            
        # Detect all PHI
        phi_matches = self.detect_phi(content)
        
        # If no PHI, return original content
        if not phi_matches:
            return content
            
        # Sort matches by position (reversed to avoid messing up positions)
        phi_matches.sort(key=lambda m: m.position, reverse=True)
        
        # Replace each match with [REDACTED]
        sanitized = content
        for match in phi_matches:
            start = match.position
            end = start + len(match.value)
            sanitized = sanitized[:start] + "[REDACTED]" + sanitized[end:]
            
        return sanitized
    
    def is_phi_test_context(self, file_path: str, content: str) -> bool:
        """
        Determine if the file is a legitimate PHI test context.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            
        Returns:
            True if the file appears to be testing PHI detection, False otherwise
        """
        # PHI Test patterns
        phi_test_patterns = [
            r"test_phi_",
            r"phi_test",
            r"test_sanitiz",
            r"sanitiz.*test",
            r"test.*phi.*detect",
            r"phi.*detect.*test",
            r"test_audit_detects_phi",
            r"test_phi_audit",
            r"test.*audit.*phi"
        ]
        
        # Check filename for PHI test patterns
        filename = file_path.split("/")[-1]
        if any(re.search(pattern, filename, re.IGNORECASE) for pattern in phi_test_patterns):
            return True
        
        # Check for test-specific imports and context
        test_indicators = [
            "import pytest",
            "from pytest",
            "unittest",
            "PHIDetector",
            "LogSanitizer",
            "PHISanitizer",
            "test_detect_phi",
            "test_phi_detection",
            "test_phi_in_code"
        ]
        
        # Is this code in a test context?
        test_files = "/tests/" in file_path or file_path.endswith("_test.py") or file_path.endswith("test.py")
        test_content = any(indicator in content for indicator in test_indicators)
        
        return test_files and test_content


def validate_us_phone(phone_number: str) -> bool:
    """
    Validate if a string is a properly formatted US phone number.
    
    Args:
        phone_number: Phone number string to validate
        
    Returns:
        True if valid US phone number, False otherwise
    """
    # Remove any non-digit characters for validation
    digits_only = re.sub(r'\D', '', phone_number)
    
    # US phone numbers should have 10 digits (or 11 with country code 1)
    return (len(digits_only) == 10 or 
            (len(digits_only) == 11 and digits_only.startswith('1')))


def validate_ssn(ssn: str) -> bool:
    """
    Validate if a string is a properly formatted US Social Security Number.
    
    Args:
        ssn: SSN string to validate
        
    Returns:
        True if valid SSN, False otherwise
    """
    # Remove any non-digit characters for validation
    digits_only = re.sub(r'\D', '', ssn)
    
    # Check basic format
    if len(digits_only) != 9:
        return False
    
    # Check for invalid values:
    # - SSNs don't start with 000, 666, or 900-999
    # - The middle two digits can't be 00
    # - The last four digits can't be 0000
    if (digits_only.startswith('000') or
        digits_only.startswith('666') or
        digits_only.startswith('9') or
        digits_only[3:5] == '00' or
        digits_only[5:] == '0000'):
        return False
        
    return True


def validate_email(email: str) -> bool:
    """
    Validate if a string is a properly formatted email address.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email, False otherwise
    """
    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date_of_birth(dob: str) -> bool:
    """
    Validate if a string is a properly formatted date of birth.
    
    Args:
        dob: Date of birth string to validate
        
    Returns:
        True if valid date of birth, False otherwise
    """
    # Try common date formats
    date_patterns = [
        r'^\d{1,2}/\d{1,2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{4}-\d{1,2}-\d{1,2}$',  # YYYY-MM-DD
        r'^\d{1,2}-\d{1,2}-\d{4}$'   # MM-DD-YYYY
    ]
    
    for pattern in date_patterns:
        if re.match(pattern, dob):
            # Additional logic could be added to validate the date values
            # (e.g., valid month/day ranges, no future dates for DOB)
            return True
            
    return False
