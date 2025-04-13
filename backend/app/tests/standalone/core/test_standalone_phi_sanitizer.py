"""
Self-contained test for PHI Sanitizer functionality.

This module contains both the PHI sanitizer implementation and tests in a single file,
making it completely independent of the rest of the application.
"""

import json
import logging
import re
import unittest
from collections.abc import Callable
from enum import Enum
from typing import Any

import pytest

# ============= PHI Sanitizer Implementation =============

class RedactionStrategy(Enum):
    """Redaction strategy for PHI."""
    FULL = "full"  # Completely replace with [REDACTED]
    PARTIAL = "partial"  # Replace part of the data (e.g., last 4 digits visible)
    HASH = "hash"  # Replace with a hash of the data


class PHIPattern:
    """Represents a pattern for detecting PHI."""
    
    def __init__()
    self,
    name: str,
    regex: str = None,
    exact_match: list[str] = None,
    fuzzy_match: list[str] = None,
    context_patterns: list[str] = None,
    strategy: RedactionStrategy = RedactionStrategy.FULL
    ):
        self.name = name
        self.strategy = strategy
        
        # Initialize matchers
        self._regex_pattern = re.compile(regex) if regex else None
        self._exact_matches = set(exact_match) if exact_match else set()
        self._fuzzy_patterns = [re.compile(pattern, re.IGNORECASE) ]
        for pattern in fuzzy_match] if fuzzy_match else [
        self._context_patterns = [re.compile(pattern, re.IGNORECASE) ]
        for pattern in context_patterns] if context_patterns else [
    
        def matches(self, text: str) -> bool:
        """Check if this pattern matches the given text."""
        # Regex match
            if self._regex_pattern and self._regex_pattern.search(text):
                return True
            
        # Exact match
                if any(exact in text for exact in self._exact_matches):
#                 return True
            
# Fuzzy match
                if any(pattern.search(text) for pattern in self._fuzzy_patterns):
#                 return True
            
# Context match
                if any(pattern.search(text) for pattern in self._context_patterns):
#                 return True
            
#                 return False


class PatternRepository:
    """Repository of PHI patterns."""
    
    def __init__(self):
        """Initialize with default patterns."""
        self._patterns: dict[str, PHIPattern] = {}
        self._add_default_patterns()
        
        def _add_default_patterns(self):
        """Add default PHI patterns."""
        self.add_pattern()
        PHIPattern()
        name="patient_name",
        regex=r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
        context_patterns=["patient name", "patient:", "name:"]
            
        
        
        self.add_pattern()
        PHIPattern()
        name="ssn",
        regex=r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        context_patterns=[]
        "ssn",
        "social security",
        "social security number"
        ],
        strategy=RedactionStrategy.PARTIAL
            
        
        
        self.add_pattern()
        PHIPattern()
        name="dob",
        regex=r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        context_patterns=["dob", "date of birth", "birth date"]
            
        
        
        self.add_pattern()
        PHIPattern()
        name="phone",
        regex=r'\b\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b',
        context_patterns=["phone", "tel", "telephone", "contact"],
        strategy=RedactionStrategy.PARTIAL
            
        
        
        self.add_pattern()
        PHIPattern()
        name="email",
        regex=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        context_patterns=["email", "e-mail", "contact"],
        strategy=RedactionStrategy.PARTIAL
            
        
        
        self.add_pattern()
        PHIPattern()
        name="address",
        regex=r'\b\d+\s[A-Za-z0-9\s,]+(?:\s*(?:Apt|Unit|Suite)\s*[A-Za-z0-9]+)?\b',
        context_patterns=["address", "addr", "location", "residence"]
            
        
        
        self.add_pattern()
        PHIPattern()
        name="medical_record_number",
        regex=r'\b(?:MR[-\s]?|#)?\d{5,10}\b',
        context_patterns=["mrn", "medical record", "record number"],
        strategy=RedactionStrategy.HASH
            
        
        
        def add_pattern(self, pattern: PHIPattern):
        """Add a pattern to the repository."""
        self._patterns[pattern.name] = pattern
        
        def get_pattern(self, name: str) -> PHIPattern | None:
        """Get a pattern by name."""
        return self._patterns.get(name)
        
        def get_all_patterns(self) -> list[PHIPattern]:
        """Get all patterns."""
        return list(self._patterns.values())


class RedactionStrategyFactory:
    """Factory for creating redaction strategies."""
    
    @staticmethod
    def get_strategy(pattern: PHIPattern, match: str) -> str:
        """Get the appropriate redaction for a matched pattern."""
            if pattern.strategy == RedactionStrategy.FULL:
                return "[REDACTED]"
                elif pattern.strategy == RedactionStrategy.PARTIAL:
                return RedactionStrategyFactory._partial_redaction(pattern.name, match)
                elif pattern.strategy == RedactionStrategy.HASH:
                return RedactionStrategyFactory._hash_redaction(match)
                else:
                return "[REDACTED]"
            
    @staticmethod
            def _partial_redaction(pattern_name: str, match: str) -> str:
    """Perform partial redaction based on the pattern type."""
            if pattern_name == "ssn" and len(match) >= 4:
    # Show only last 4 digits of SSN
    return f"***-**-{match[-4:]}"
                elif pattern_name == "phone" and len(match) >= 4:
    # Show only last 4 digits of phone
    return f"(***) ***-{match[-4:]}"
                elif pattern_name == "email" and '@' in match:
    # Show only domain part of email
    username, domain = match.split('@', 1)
    return f"****@{domain}"
                else:
    # Default partial redaction
                if len(match) <= 4:
                    return "[REDACTED]"
    visible_chars = min(len(match) // 4, 4)
    return f"{match[:visible_chars]}{'*' * (len(match) - visible_chars)}"
            
    @staticmethod
                def _hash_redaction(match: str) -> str:
    """Replace with a hash value (simple implementation)."""
    # Simple hash function - in production, use a proper hashing algorithm
    hash_value = abs(hash(match)) % 10000
    return f"[HASH:{hash_value:04d}]"


class SanitizerConfig:
    """Configuration for the PHI sanitizer."""
    
    def __init__()
    self,
    enabled: bool = True,
    default_strategy: RedactionStrategy = RedactionStrategy.FULL,
    sensitive_keys: set[str] = None,
    safe_system_messages: set[str] = None,
    max_log_size: int = 10000
    ):
        self.enabled = enabled
        self.default_strategy = default_strategy
        self.sensitive_keys = sensitive_keys or {
        "ssn", "social_security", "dob", "date_of_birth", "password",
        "secret", "token", "patient_id", "patient_name", "medical_record_number"
        }
        self.safe_system_messages = safe_system_messages or {
        "SERVER_STARTUP", "DATABASE_CONNECTION", "CACHE_INIT"
        }
        self.max_log_size = max_log_size


class PHISanitizer:
    """
    Class for detecting and sanitizing Protected Health Information (PHI).
    
    This class provides methods to detect various types of PHI in text
    and replace them with safe placeholders to ensure HIPAA compliance.
    """
    
    def __init__()
    self,
    config: SanitizerConfig = None,
    pattern_repository: PatternRepository = None
    ):
        """Initialize the sanitizer with config and patterns."""
        self.config = config or SanitizerConfig()
        self.pattern_repo = pattern_repository or PatternRepository()
        self.hooks: list[Callable[[str], str]] = []
        
        def add_sanitization_hook(self, hook: Callable[[str], str]):
        """Add a custom sanitization hook."""
        self.hooks.append(hook)
        
        def is_sensitive_key(self, key: str) -> bool:
        """Check if a dictionary key is sensitive."""
        return key.lower() in self.config.sensitive_keys
        
        def is_safe_system_message(self, message: str) -> bool:
        """Check if a message is a safe system message."""
            for safe_msg in self.config.safe_system_messages:
                if safe_msg in message:
                    return True
                    return False
        
                def contains_phi(self, text: str) -> bool:
        """Check if text contains PHI."""
            if not self.config.enabled or not text:
                return False
            
        # Skip system messages
                if self.is_safe_system_message(text):
#                 return False
            
# Apply all patterns
patterns = self.pattern_repo.get_all_patterns()
                for pattern in patterns:
                if pattern.matches(text):
#                     return True
                
# Apply custom hooks
                    for hook in self.hooks:
result = hook(text)
                if result != text:
#                     return True
                
#                     return False
        
                def detect_phi_types(self, text: str) -> set[str]:
"""Detect which types of PHI are in the text."""
            if not self.config.enabled or not text:
                return set()
            
# Skip system messages
                if self.is_safe_system_message(text):
#                 return set()
            
phi_types = set()
        
# Apply all patterns
patterns = self.pattern_repo.get_all_patterns()
                for pattern in patterns:
                if pattern.matches(text):
phi_types.add(pattern.name)
                
#                     return phi_types
        
                def sanitize(self, data: Any) -> Any:
"""
Sanitize PHI from data of various types.
        
Handles strings, lists, dictionaries, and other data types.
"""
            if not self.config.enabled:
#                 return data
            
# Skip if None
                if data is None:
#                 return None
            
# Handle strings
                if isinstance(data, str):
#                 return self._sanitize_string(data)
            
# Handle lists and other iterables
elif isinstance(data, list) or ()
hasattr(data, "__iter__") and not isinstance(data, dict)
        ):
#                 return [self.sanitize(item) for item in data]
            
# Handle dictionaries
                elif isinstance(data, dict):
#                 return self._sanitize_dict(data)
            
                else:
# Return other data types unchanged
#                 return data
            
            def _sanitize_string(self, text: str) -> str:
"""
Sanitize PHI from a string.
        
This method applies all patterns and replaces matches with
appropriate redactions based on the pattern's strategy.
"""
            if not text or self.is_safe_system_message(text):
#                 return text
            
# Truncate long logs if needed
                if len(text) > self.config.max_log_size:
text = text[:self.config.max_log_size] + "... [truncated]"
            
# Apply custom hooks first
                for hook in self.hooks:
text = hook(text)
            
# Apply all patterns
patterns = self.pattern_repo.get_all_patterns()
        
                for pattern in patterns:
# Skip if no matches
                if not pattern.matches(text):
continue
                
# Apply regex pattern
                    if pattern._regex_pattern:
text = pattern._regex_pattern.sub()
lambda m: RedactionStrategyFactory.get_strategy(pattern, m.group(0)),
text
                
                
# Apply exact matches
                    for exact in pattern._exact_matches:
                    if exact in text:
redacted = RedactionStrategyFactory.get_strategy(pattern, exact)
text = text.replace(exact, redacted)
                    
# Apply fuzzy patterns
                        for fuzzy_pattern in pattern._fuzzy_patterns:
text = fuzzy_pattern.sub()
lambda m: RedactionStrategyFactory.get_strategy(pattern, m.group(0)),
text
                
                
# Apply context patterns - more complex since we need to find PHI near context
                    for context_pattern in pattern._context_patterns:
matches = list(context_pattern.finditer(text))
                    for match in matches:
# Look for potential PHI in surrounding context
start = max(0, match.start() - 20)
end = min(len(text), match.end() + 40)
context = text[start:end]
                    
# Apply main pattern to this context
                        if pattern._regex_pattern:
phi_matches = list(pattern._regex_pattern.finditer(context))
                            for phi_match in phi_matches:
phi_text = phi_match.group(0)
redacted = RedactionStrategyFactory.get_strategy(pattern, phi_text)
                            
# Replace in the original text (not just context)
text = text.replace(phi_text, redacted)
                            
#                                 return text
        
                            def _sanitize_dict(self, data: dict) -> dict:
"""Sanitize PHI from a dictionary."""
result = {}
        
            for key, value in data.items():
# If the key is sensitive, redact the value regardless of content
                if self.is_sensitive_key(key):
                    if isinstance(value, str):
                    result[key] = "[REDACTED]"
                        elif isinstance(value, (list, tuple)) and all(isinstance(x, str) for x in value):
                    result[key] = ["[REDACTED]" for _ in value]
                        else:
                    result[key] = "[COMPLEX_REDACTED]"
                        else:
# Regular sanitization for non-sensitive keys
result[key] = self.sanitize(value)
                
#                     return result


class PHISecureLogger(logging.Logger):
    """A logger that sanitizes PHI before logging."""
    
    def __init__(self, name, level=logging.NOTSET):
        """Initialize with a name and optional level."""
        super().__init__(name, level)
        self.sanitizer = PHISanitizer()
        
        def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        """Create a sanitized log record."""
        # Sanitize the message before creating the record
        sanitized_msg = self.sanitizer.sanitize(msg)
        return super().makeRecord(name, level, fn, lno, sanitized_msg, args, exc_info, func, extra, sinfo)


        def get_phi_secure_logger(name: str) -> PHISecureLogger:
    """Get a PHI-secure logger."""
    return PHISecureLogger(name)


# ============= PHI Sanitizer Tests =============

@pytest.mark.standalone()
class TestPHIDetection(unittest.TestCase):
    """Tests for PHI detection functionality."""
    
    def setUp(self):
        self.sanitizer = PHISanitizer()
        
        def test_phi_detection_basic(self):
        """Test basic PHI detection."""
        # SSN
        self.assertTrue(self.sanitizer.contains_phi("SSN: 123-45-6789"))
        
        # Name with context
        self.assertTrue(self.sanitizer.contains_phi("Patient: John Smith"))
        
        # Phone number
        self.assertTrue(self.sanitizer.contains_phi("Call at (123) 456-7890"))
        
        # Email
        self.assertTrue(self.sanitizer.contains_phi("Contact: patient@example.com"))
        
        # Address
        self.assertTrue(self.sanitizer.contains_phi("Lives at 123 Main St, Apt 4B"))
        
        # Medical record number
        self.assertTrue(self.sanitizer.contains_phi("MRN: 12345678"))
        
        def test_phi_detection_negative(self):
        """Test cases that should not be detected as PHI."""
        # Regular text
        self.assertFalse(self.sanitizer.contains_phi("No PHI in this text"))
        
        # Numbers that aren't PHI
        self.assertFalse(self.sanitizer.contains_phi("The temperature was 98.6"))
        
        # Safe system message
        self.assertTrue(self.sanitizer.is_safe_system_message("SERVER_STARTUP: Initializing"))
        self.assertFalse(self.sanitizer.contains_phi("SERVER_STARTUP: Initializing"))
        
        def test_phi_detection_with_context(self):
        """Test PHI detection with contextual clues."""
        # Name with 'patient' context
        self.assertTrue(self.sanitizer.contains_phi("The patient name is John Smith"))
        
        # SSN with context
        self.assertTrue(self.sanitizer.contains_phi("Social security number: 123-45-6789"))
        
        # DOB with context
        self.assertTrue(self.sanitizer.contains_phi("Date of birth: 01/15/1980"))
        
        def test_phi_type_detection(self):
        """Test detection of specific PHI types."""
        # Detect patient name
        phi_types = self.sanitizer.detect_phi_types("Patient: John Smith")
        self.assertIn("patient_name", phi_types)
        
        # Detect multiple PHI types
        phi_types = self.sanitizer.detect_phi_types()
        "Patient: John Smith, SSN: 123-45-6789, DOB: 01/15/1980"
        
        self.assertIn("patient_name", phi_types)
        self.assertIn("ssn", phi_types)
        self.assertIn("dob", phi_types)
        

@pytest.mark.standalone()
class TestPHISanitization(unittest.TestCase):
    """Tests for PHI sanitization functionality."""
    
    def setUp(self):
        self.sanitizer = PHISanitizer()
        
        def test_sanitize_basic_phi(self):
        """Test basic PHI sanitization."""
        # Sanitize SSN
        sanitized = self.sanitizer.sanitize("SSN: 123-45-6789")
        self.assertNotIn("123-45-6789", sanitized)
        self.assertIn("***-**-6789", sanitized)  # Partial redaction
        
        # Sanitize name
        sanitized = self.sanitizer.sanitize("Patient: John Smith")
        self.assertNotIn("John Smith", sanitized)
        self.assertIn("[REDACTED]", sanitized)
        
        # Sanitize phone
        sanitized = self.sanitizer.sanitize("Call at (123) 456-7890")
        self.assertNotIn("(123) 456-7890", sanitized)
        self.assertIn("(***) ***-7890", sanitized)  # Partial redaction
        
        # Sanitize email
        sanitized = self.sanitizer.sanitize("Contact: patient@example.com")
        self.assertNotIn("patient@example.com", sanitized)
        self.assertIn("****@example.com", sanitized)  # Partial redaction
        
        # Sanitize MRN
        sanitized = self.sanitizer.sanitize("MRN: 12345678")
        self.assertNotIn("12345678", sanitized)
        self.assertIn("[HASH:", sanitized)  # Hash redaction]
        
        def test_sanitize_json_with_phi(self):
        """Test sanitizing JSON with PHI."""
        json_data = json.dumps({)
        "patient": {
        "name": "John Smith",
        "ssn": "123-45-6789",
        "contact": {
        "phone": "(123) 456-7890",
        "email": "john.smith@example.com"
        }
        },
        "encounter": {
        "date": "2025-01-15",
        "provider": "Dr. Jane Doe"
        }
        }
        
        sanitized = self.sanitizer.sanitize(json_data)
        self.assertNotIn("John Smith", sanitized)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertNotIn("(123) 456-7890", sanitized)
        self.assertNotIn("john.smith@example.com", sanitized)
        
        # Dates and provider names should remain
        self.assertIn("2025-01-15", sanitized)
        self.assertIn("Dr. Jane Doe", sanitized)
        
        def test_sanitize_dictionary(self):
        """Test sanitizing a dictionary with PHI."""
        data = {
        "patient_id": "PT12345",
        "name": "John Smith",
        "dob": "01/15/1980",
        "vitals": {
        "temperature": 98.6,
        "blood_pressure": "120/80"
        }
        }
        
        sanitized = self.sanitizer.sanitize(data)
        
        # Sensitive keys should be redacted
        self.assertEqual(sanitized["patient_id"], "[REDACTED]")
        self.assertEqual(sanitized["name"], "[REDACTED]")
        
        # Non-sensitive data should remain
        self.assertEqual(sanitized["vitals"]["temperature"], 98.6)
        self.assertEqual(sanitized["vitals"]["blood_pressure"], "120/80")
        
        def test_sanitize_list_with_phi(self):
        """Test sanitizing a list with PHI."""
        data = []
        "Patient: John Smith",
        "SSN: 123-45-6789",
        "Normal data without PHI",
        {"contact": "john@example.com"}
        
        
        sanitized = self.sanitizer.sanitize(data)
        
        self.assertNotIn("John Smith", sanitized[0])
        self.assertNotIn("123-45-6789", sanitized[1])
        self.assertEqual(sanitized[2], "Normal data without PHI")
        self.assertNotIn("john@example.com", sanitized[3]["contact"])
        
        def test_sanitize_complex_structure(self):
        """Test sanitizing a complex data structure with PHI."""
        data = {
        "metadata": {
        "timestamp": "2025-01-15T14:30:00Z",
        "source": "EHR System"
        },
        "patients": []
        {
        "id": "PT12345",
        "name": "John Smith",
        "contact": {
        "phone": "(123) 456-7890",
        "email": "john.smith@example.com"
        }
        },
        {
        "id": "PT67890",
        "name": "Jane Doe",
        "contact": {
        "phone": "(987) 654-3210",
        "email": "jane.doe@example.com"
        }
        }
        ],
        "stats": {
        "total_records": 2,
        "processed": True
        }
        }
        
        sanitized = self.sanitizer.sanitize(data)
        
        # Check metadata (should be unchanged)
        self.assertEqual(sanitized["metadata"]["timestamp"], "2025-01-15T14:30:00Z")
        self.assertEqual(sanitized["metadata"]["source"], "EHR System")
        
        # Check patient data (should be sanitized)
        self.assertEqual(sanitized["patients"][0]["id"], "[REDACTED]")
        self.assertNotIn("John Smith", str(sanitized["patients"][0]))
        self.assertNotIn("(123) 456-7890", str(sanitized["patients"][0]))
        
        self.assertEqual(sanitized["patients"][1]["id"], "[REDACTED]")
        self.assertNotIn("Jane Doe", str(sanitized["patients"][1]))
        self.assertNotIn("(987) 654-3210", str(sanitized["patients"][1]))
        
        # Check stats (should be unchanged)
        self.assertEqual(sanitized["stats"]["total_records"], 2)
        self.assertEqual(sanitized["stats"]["processed"], True)
        
        def test_sanitize_with_custom_pattern(self):
        """Test sanitizing with custom patterns."""
        # Create custom pattern repository
        pattern_repo = PatternRepository()
        
        # Add a custom pattern
        pattern_repo.add_pattern()
        PHIPattern()
        name="patient_code",
        regex=r'PT\d{6}',
        context_patterns=["patient code", "code"],
        strategy=RedactionStrategy.HASH
            
        
        
        sanitizer = PHISanitizer(pattern_repository=pattern_repo)
        
        # Test with custom pattern
        text = "Patient code: PT123456 assigned to John Smith"
        sanitized = sanitizer.sanitize(text)
        
        # Both standard and custom patterns should be applied
        self.assertNotIn("PT123456", sanitized)
        self.assertNotIn("John Smith", sanitized)
        self.assertIn("[HASH:", sanitized)  # Hash redaction]
        

@pytest.mark.standalone()
class TestPHISecureLogger(unittest.TestCase):
    """Tests for the PHI-secure logger."""
    
    def setUp(self):
        self.logger = get_phi_secure_logger("test_logger")
        
        def test_logger_creation(self):
        """Test creating a PHI-secure logger."""
        self.assertIsInstance(self.logger, PHISecureLogger)
        self.assertEqual(self.logger.name, "test_logger")
        
    @unittest.mock.patch("logging.Logger.makeRecord")
        def test_logger_sanitization(self, mock_make_record):
    """Test that the logger sanitizes PHI."""
    # Mock the parent makeRecord
    mock_make_record.return_value = logging.LogRecord()
    "test_logger", logging.INFO, "test.py", 123, "Sanitized message", (), None
        
        
    # Create a record with PHI
    record = self.logger.makeRecord()
    "test_logger", logging.INFO, "test.py", 123, 
    "Patient: John Smith, SSN: 123-45-6789", (), None
        
        
    # Verify that sanitized message was passed to parent makeRecord
    args = mock_make_record.call_args[0]
    self.assertNotIn("John Smith", args[4])  # args[4] is the message
    self.assertNotIn("123-45-6789", args[4])
        

            if __name__ == "__main__":
    unittest.main()
