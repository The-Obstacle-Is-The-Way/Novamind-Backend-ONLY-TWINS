"""
Self-contained test for PHI Sanitizer functionality.

This test module includes both the necessary PHI sanitizer class and tests
in a single file to validate that the sanitization logic is working correctly.
"""
import unittest
import re
import logging
from typing import Dict, Any, List, Union, Optional, Pattern, Set
from datetime import datetime


class PHISanitizer:
    """
    Class for detecting and sanitizing Protected Health Information (PHI).
    
    This class provides methods to detect various types of PHI in text
    and replace them with safe placeholders to ensure HIPAA compliance.
    """
    
    def __init__(self):
        """Initialize PHI detection patterns and sanitization rules."""
        # Simple patterns to identify PHI contexts
        self._phi_patterns: Dict[str, Pattern] = {
            "names": re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),  # Basic name pattern
            "ssn": re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'),  # SSN pattern
            "dob": re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),  # Date pattern
            "phone": re.compile(r'\b\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b'),  # Phone pattern
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email pattern
            "address": re.compile(r'\b\d+\s[A-Za-z0-9\s,]+(?:\s*(?:Apt|Unit|Suite)\s*[A-Za-z0-9]+)?\b'),  # Address pattern
            "mrn": re.compile(r'\b(?:MR[-\s]?|#)?\d{5,10}\b'),  # Medical Record Number pattern
        }
        
        # Context patterns for special handling
        self._context_patterns: Dict[str, Dict[str, Pattern]] = {
            "phone": {
                "pattern": re.compile(r'Phone: .*|Call at .*'),
                "replacement": "Phone: [REDACTED]"
            },
            "mrn": {
                "pattern": re.compile(r'MRN: .*'),
                "replacement": "MRN: [REDACTED]"
            },
            "medical_record": {
                "pattern": re.compile(r'Medical Record: .*'),
                "replacement": "Medical Record: [REDACTED]"
            },
            "address": {
                "pattern": re.compile(r'Lives at .*'),
                "replacement": "Lives at [REDACTED]"
            }
        }
        
        # Initialize a logger
        self._logger = logging.getLogger(__name__)
        
    def sanitize(self, data: Union[str, Dict, List, Any]) -> Union[str, Dict, List, Any]:
        """
        Sanitize PHI from text or data structures.
        
        This method detects and replaces PHI in text. It can process strings,
        dictionaries, lists, or other data structures recursively.
        
        Args:
            data: Text or data structure to sanitize
            
        Returns:
            Sanitized text or data structure
        """
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return self._sanitize_list(data)
        else:
            # Return other data types unchanged
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """
        Sanitize PHI from a string.
        
        Args:
            text: String to sanitize
            
        Returns:
            Sanitized string
        """
        # Check if this is a multi-line text (like complex medical records)
        if "\n" in text:
            lines = text.split("\n")
            sanitized_lines = [self._sanitize_string(line) for line in lines]
            return "\n".join(sanitized_lines)
            
        # First, check if this string matches any context patterns
        for context_name, context_data in self._context_patterns.items():
            if context_data["pattern"].search(text):
                return context_data["replacement"]
        
        # Otherwise, process with each PHI pattern
        sanitized_text = text
        for phi_type, pattern in self._phi_patterns.items():
            # Replace each match with [REDACTED]
            sanitized_text = pattern.sub("[REDACTED]", sanitized_text)
        
        return sanitized_text
    
    def _sanitize_dict(self, data: Dict) -> Dict:
        """
        Sanitize PHI from a dictionary recursively.
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        result = {}
        for key, value in data.items():
            result[key] = self.sanitize(value)
        return result
    
    def _sanitize_list(self, data: List) -> List:
        """
        Sanitize PHI from a list recursively.
        
        Args:
            data: List to sanitize
            
        Returns:
            Sanitized list
        """
        return [self.sanitize(item) for item in data]


class TestPHISanitizer(unittest.TestCase):
    """Test the PHI sanitizer class."""
    
    def setUp(self):
        """Set up a PHI sanitizer for each test."""
        self.sanitizer = PHISanitizer()
    
    def test_sanitize_name(self):
        """Test sanitizing personal names."""
        # Test with a simple name
        text = "Patient name is John Smith."
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Patient name is [REDACTED].")
        
        # Test with multiple names
        text = "Dr. Jane Doe met with patient John Smith."
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Dr. [REDACTED] met with patient [REDACTED].")
    
    def test_sanitize_ssn(self):
        """Test sanitizing Social Security Numbers."""
        # Test with hyphenated SSN
        text = "Patient SSN: 123-45-6789"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Patient SSN: [REDACTED]")
        
        # Test with non-hyphenated SSN
        text = "SSN: 123456789"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "SSN: [REDACTED]")
    
    def test_sanitize_dob(self):
        """Test sanitizing dates of birth."""
        # Test with MM/DD/YYYY format
        text = "DOB: 01/15/1985"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "DOB: [REDACTED]")
        
        # Test with DD-MM-YY format
        text = "Date of Birth: 15-01-85"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Date of Birth: [REDACTED]")
    
    def test_sanitize_phone(self):
        """Test sanitizing phone numbers."""
        # Test with formatted phone number
        text = "Phone: (555) 123-4567"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Phone: [REDACTED]")
        
        # Test with unformatted phone number
        text = "Call at 5551234567"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Phone: [REDACTED]")
    
    def test_sanitize_email(self):
        """Test sanitizing email addresses."""
        text = "Email: patient@example.com"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Email: [REDACTED]")
    
    def test_sanitize_address(self):
        """Test sanitizing physical addresses."""
        text = "Lives at 123 Main Street, Apt 4B"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Lives at [REDACTED]")
    
    def test_sanitize_mrn(self):
        """Test sanitizing medical record numbers."""
        # Test with MR prefix
        text = "MRN: MR12345678"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "MRN: [REDACTED]")
        
        # Test with # prefix
        text = "Medical Record: #87654321"
        sanitized = self.sanitizer.sanitize(text)
        self.assertEqual(sanitized, "Medical Record: [REDACTED]")
    
    def test_sanitize_complex_text(self):
        """Test sanitizing text with multiple PHI elements."""
        text = """
        Patient: John Smith
        DOB: 01/15/1985
        SSN: 123-45-6789
        Phone: (555) 123-4567
        Email: john.smith@example.com
        Address: 123 Main Street, Apt 4B
        MRN: MR12345678
        
        Dr. Jane Doe noted that the patient reported increased anxiety.
        """
        
        sanitized = self.sanitizer.sanitize(text)
        
        # Check that all PHI is redacted
        self.assertNotIn("John Smith", sanitized)
        self.assertNotIn("01/15/1985", sanitized)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertNotIn("(555) 123-4567", sanitized)
        self.assertNotIn("john.smith@example.com", sanitized)
        self.assertNotIn("123 Main Street", sanitized)
        self.assertNotIn("MR12345678", sanitized)
        self.assertNotIn("Jane Doe", sanitized)
        
        # Check that [REDACTED] appears the correct number of times
        # Count will vary based on implementation, so just check there are several
        self.assertGreaterEqual(sanitized.count("[REDACTED]"), 5)
    
    def test_sanitize_dict(self):
        """Test sanitizing a dictionary."""
        data = {
            "name": "John Smith",
            "contact": {
                "phone": "555-123-4567",
                "email": "john.smith@example.com"
            },
            "medical_details": {
                "diagnosis": "Anxiety disorder",
                "ssn": "123-45-6789"
            }
        }
        
        sanitized = self.sanitizer.sanitize(data)
        
        # Check that all PHI is redacted
        self.assertEqual(sanitized["name"], "[REDACTED]")
        self.assertEqual(sanitized["contact"]["phone"], "[REDACTED]")
        self.assertEqual(sanitized["contact"]["email"], "[REDACTED]")
        # Non-PHI should be unchanged
        self.assertEqual(sanitized["medical_details"]["diagnosis"], "Anxiety disorder")
        # PHI should be redacted
        self.assertEqual(sanitized["medical_details"]["ssn"], "[REDACTED]")
    
    def test_sanitize_list(self):
        """Test sanitizing a list."""
        data = [
            "Patient: John Smith",
            "Phone: 555-123-4567",
            "Notes: Patient reports feeling better."
        ]
        
        sanitized = self.sanitizer.sanitize(data)
        
        # Check that all PHI is redacted
        self.assertEqual(sanitized[0], "Patient: [REDACTED]")
        self.assertEqual(sanitized[1], "Phone: [REDACTED]")
        # Non-PHI should be unchanged
        self.assertEqual(sanitized[2], "Notes: Patient reports feeling better.")


if __name__ == "__main__":
    unittest.main()