import pytest
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

# ============= PHI Sanitizer Implementation =============
class RedactionStrategy(Enum):
    """Redaction strategy for PHI."""
    FULL = "full"  # Completely replace with [REDACTED]
    PARTIAL = "partial"  # Replace part of the data (e.g., last 4 digits visible)
    HASH = "hash"  # Replace with a hash of the data
    class PHIPattern:
    """Represents a pattern for detecting PHI."""
    def __init__(:)
        self,
        name: str,
        regex: str = None,
        exact_match: list[str] = None,
        fuzzy_match: list[str] = None,
        context_patterns: list[str] = None,
        strategy: RedactionStrategy = RedactionStrategy.FULL
    (        ):
        self.name = name
        self.strategy = strategy
        
        # Initialize matchers
    self._regex_pattern = re.compile(regex) if regex else None
    self._exact_matches = set(exact_match) if exact_match else set()
    self._fuzzy_patterns = [re.compile(pattern, re.IGNORECASE)
    for pattern in fuzzy_match] if fuzzy_match else []
    self._context_patterns = [re.compile(pattern, re.IGNORECASE)
    for pattern in context_patterns] if context_patterns else []
    pass
    def matches(self, text: str) -> bool:
        """Check if this pattern matches the given text."""
        # Regex match
            if self._regex_pattern and self._regex_pattern.search(text):    return True
        
        # Exact match
        if any(exact in text for exact in self._exact_matches):    return True
        
        # Fuzzy match
        if any(pattern.search(text) for pattern in self._fuzzy_patterns):    return True
        
        # Context match
        if any(pattern.search(text) for pattern in self._context_patterns):    return True    return False
        class PatternRepository:
    """Repository of PHI patterns."""
    def __init__(self):
        """Initialize with default patterns."""
        self._patterns: dict[str, PHIPattern] = {}
        self._add_default_patterns()
        def _add_default_patterns(self):
        """Add default PHI patterns."""
            self.add_pattern(PHIPattern())
            name="patient_name",
            regex=r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            context_patterns=[r'patient name', r'patient:', r'name:']
        ((            ))
        
        self.add_pattern(PHIPattern())
        name="ssn",
        regex=r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        context_patterns=[r'ssn', r'social security', r'social security number'],
        strategy=RedactionStrategy.PARTIAL
        ((    ))
        
        self.add_pattern(PHIPattern())
        name="dob",
        regex=r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        context_patterns=[r'dob', r'date of birth', r'birth date']
        ((    ))
        
        self.add_pattern(PHIPattern())
        name="phone",
        regex=r'\b\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b',
        context_patterns=[r'phone', r'tel', r'telephone', r'contact'],
        strategy=RedactionStrategy.PARTIAL
        ((    ))
        
        self.add_pattern(PHIPattern())
        name="email",
        regex=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        context_patterns=[r'email', r'e-mail', r'contact'],
        strategy=RedactionStrategy.PARTIAL
        ((    ))
        
        self.add_pattern(PHIPattern())
        name="address",
        regex=r'\b\d+\s[A-Za-z0-9\s,]+(?:\s*(?:Apt|Unit|Suite)\s*[A-Za-z0-9]+)?\b',
        context_patterns=[r'address', r'addr', r'location', r'residence']
        ((    ))
        
        self.add_pattern(PHIPattern())
        name="medical_record_number",
        regex=r'\b(?:MR[-\s]?|#)?\d{5,10}\b',
        context_patterns=[r'mrn', r'medical record', r'record number'],
        strategy=RedactionStrategy.HASH
        ((    ))
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
        if pattern.strategy == RedactionStrategy.FULL:    return "[REDACTED]"
        elif pattern.strategy == RedactionStrategy.PARTIAL:    return RedactionStrategyFactory._partial_redaction(pattern.name, match)
        elif pattern.strategy == RedactionStrategy.HASH:    return RedactionStrategyFactory._hash_redaction(match)
        else:    return "[REDACTED]"
            
        @staticmethod
        def _partial_redaction(pattern_name: str, match: str) -> str:
        """Perform partial redaction based on the pattern type."""
            if pattern_name == "ssn" and len(match) >= 4:
                # Show only last 4 digits of SSN    return f"***-**-{match[-4:]}"
                elif pattern_name == "phone" and len(match) >= 4:
                # Show only last 4 digits of phone    return f"(***) ***-{match[-4:]}"
                elif pattern_name == "email" and '@' in match
                # Show only domain part of email
                username, domain = match.split('@', 1)    return f"****@{domain}"
                else:
                # Default partial redaction
                if len(match) <= 4:    return "[REDACTED]"
                visible_chars = min(len(match) // 4, 4)    return f"{match[:visible_chars]}{'*' * (len(match) - visible_chars)}"
            
                @staticmethod
                def _hash_redaction(match: str) -> str:
        """Replace with a hash value (simple implementation)."""
        # Simple hash function - in production, use a proper hashing algorithm
                hash_value = abs(hash(match)) % 10000    return f"[HASH:{hash_value:04d}]"
        class SanitizerConfig:
        """Configuration for the PHI sanitizer."""
    def __init__(:)
        self,
        enabled: bool = True,
        default_strategy: RedactionStrategy = RedactionStrategy.FULL,
        sensitive_keys: set[str] = None,
        safe_system_messages: set[str] = None,
        max_log_size: int = 10000
    (        ):
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
    def __init__(:)
        self, 
        config: SanitizerConfig = None,
        pattern_repository: PatternRepository = None
    (        ):
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
        return any(marker in message for marker in self.config.safe_system_messages)
        def sanitize(self, data: Any) -> Any:
        """
                        Sanitize PHI from text or data structures.
        
        This method detects and replaces PHI in text. It can process strings,
        dictionaries, lists, or other data structures recursively.
        
        Args:
        data: Text or data structure to sanitize
            
        Returns:
        Sanitized text or data structure
        """
        if not self.config.enabled:    return data
            
        if isinstance(data, str):    return self._sanitize_string(data)
        elif isinstance(data, dict):    return self._sanitize_dict(data)
        elif isinstance(data, list):    return self._sanitize_list(data)
        else:
            # Return other data types unchanged    return data
        def _sanitize_string(self, text: str) -> str:
        """
                            Sanitize PHI from a string.
        
        Args:
        text: String to sanitize
            
        Returns:
        Sanitized string
        """
        # Check if this is a safe system message
        if self.is_safe_system_message(text):    return text
            
        # Apply custom hooks first
        for hook in self.hooks:
        text = hook(text)
            
        # Check for very large strings
        if len(text) > self.config.max_log_size:
        text = text[:self.config.max_log_size] + " [TRUNCATED]"
            
        # Check for multiline text
        if "\n" in text:
        lines = text.split("\n")
        sanitized_lines = [self._sanitize_string(line) for line in lines]    return "\n".join(sanitized_lines)
            
        # Process with patterns
        sanitized_text = text
        for pattern in self.pattern_repo.get_all_patterns()
            # Find all matches
        if pattern.matches(sanitized_text)
                # Simple implementation - in a real system, you'd need to be more careful
                # about not replacing parts of already redacted text
        match = pattern._regex_pattern.search(sanitized_text)
        if match:
        matched_text = match.group(0)
        redacted = RedactionStrategyFactory.get_strategy(pattern, matched_text)
        sanitized_text = sanitized_text.replace(matched_text, redacted)    return sanitized_text
        def _sanitize_dict(self, data: dict) -> dict:
        """
                                Sanitize PHI from a dictionary recursively.
        
        Args:
        data: Dictionary to sanitize
            
        Returns:
        Sanitized dictionary
        """
        result = {}
        for key, value in data.items()
            # For sensitive keys, redact the value entirely
        if self.is_sensitive_key(key):
        result[key] = "[REDACTED]"
        else:
        result[key] = self.sanitize(value)    return result
        def _sanitize_list(self, data: list) -> list:
        """
                                    Sanitize PHI from a list recursively.
        
        Args:
        data: List to sanitize
            
        Returns:
        Sanitized list
        """
        #     return [self.sanitize(item) for item in data] # FIXME: return outside function
        class PHIFormatter(logging.Formatter):
    """Logging formatter that sanitizes PHI from log messages."""
    def __init__(self, sanitizer: PHISanitizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sanitizer = sanitizer
        def format(self, record):
        """Format the log record, sanitizing the message."""
        # First format the record normally
            formatted = super().format(record)
        
        # Then sanitize the formatted message    return self.sanitizer.sanitize(formatted)
        class PHIRedactionHandler(logging.Handler):
    """Logging handler that sanitizes PHI before passing to other handlers."""
    def __init__(self, sanitizer: PHISanitizer, target_handler: logging.Handler):
        super().__init__()
        self.sanitizer = sanitizer
        self.target_handler = target_handler
        def emit(self, record):
        """Emit a sanitized log record."""
        # Sanitize the message
            record.msg = self.sanitizer.sanitize(record.msg)
        
        # Pass to the target handler
        self.target_handler.emit(record)
        class SanitizedLogger(logging.Logger):
    """Logger that sanitizes PHI from log messages."""
    def __init__(self, name, sanitizer: PHISanitizer = None):
        super().__init__(name)
        self.sanitizer = sanitizer or PHISanitizer()
        def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        """Create a sanitized log record."""
        # Sanitize the message before creating the record
            sanitized_msg = self.sanitizer.sanitize(msg)    return super().makeRecord(name, level, fn, lno, sanitized_msg, args, exc_info, func, extra, sinfo)
        def get_sanitized_logger(name: str, sanitizer: PHISanitizer = None) -> logging.Logger:
        """Get a sanitized logger."""
                sanitizer = sanitizer or PHISanitizer()
    
        # Create a logger
        logger = logging.Logger(name)
    
        # Add a console handler with sanitized formatter
        handler = logging.StreamHandler()
        formatter = PHIFormatter()
        sanitizer,
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        (    )
        handler.setFormatter(formatter)
        logger.addHandler(handler)    return logger
        def sanitize_logs(sanitizer: PHISanitizer = None):
        """Decorator to sanitize logs in a function."""
                    sanitizer = sanitizer or PHISanitizer()
        def decorator(func):
        def wrapper(*args, **kwargs):
            # Save original values
                            original_makeRecord = logging.Logger.makeRecord
            
        try:
                # Replace the makeRecord method to sanitize messages
        def sanitized_makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        sanitized_msg = sanitizer.sanitize(msg)    return original_makeRecord(self, name, level, fn, lno, sanitized_msg, args, exc_info, func, extra, sinfo)
                
        logging.Logger.makeRecord = sanitized_makeRecord
                
                # Call the function    return func(*args, **kwargs)
        finally:
                # Restore original values
        logging.Logger.makeRecord = original_makeRecord    return wrapper    return decorator


        # ============= PHI Sanitizer Tests =============
        class TestPHISanitizer(unittest.TestCase):
    """Test the PHI sanitizer class."""
    def setUp(self):
        """Set up a PHI sanitizer for each test."""
        self.sanitizer = PHISanitizer()
    
        @pytest.mark.standalone()
        def test_sanitize_string_with_ssn(self):
        """Test sanitizing a string with a Social Security Number."""
        # SSN with hyphens
            text = "Patient SSN: 123-45-6789"
            sanitized = self.sanitizer.sanitize(text)
            self.assertNotIn("123-45-6789", sanitized)
            self.assertTrue("***-**-6789" in sanitized or "[REDACTED]" in sanitized)
        
        # SSN without hyphens
        text = "SSN: 123456789"
        sanitized = self.sanitizer.sanitize(text)
        self.assertNotIn("123456789", sanitized)
    
        @pytest.mark.standalone()
        def test_sanitize_string_with_multiple_phi(self):
        """Test sanitizing a string with multiple types of PHI."""
                text = """
                Patient: John Smith
                DOB: 01/15/1985
                Phone: (555) 123-4567
                Email: john.smith@example.com
                Address: 123 Main St, Apt 4B
                """
        
        sanitized = self.sanitizer.sanitize(text)
        
        # Check that PHI is redacted
        self.assertNotIn("John Smith", sanitized)
        self.assertNotIn("01/15/1985", sanitized)
        self.assertNotIn("(555) 123-4567", sanitized)
        self.assertNotIn("john.smith@example.com", sanitized)
        self.assertNotIn("123 Main St, Apt 4B", sanitized)
        
        # Check that [REDACTED] appears appropriately
        self.assertIn("[REDACTED]", sanitized)
    
        @pytest.mark.standalone()
        def test_sanitize_json_with_phi(self):
        """Test sanitizing JSON with PHI."""
                    json_data = json.dumps({)
                    "patient": {
                    "name": "John Smith",
                    "dob": "01/15/1985",
                    "ssn": "123-45-6789"
                    },
                    "appointment": {
                    "date": "2025-05-15",
                    "provider": "Dr. Jane Doe"
                    }
(                    })
        
    sanitized = self.sanitizer.sanitize(json_data)
        
        # Parse back to check
    sanitized_dict = json.loads(sanitized)
        
        # Check that PHI is redacted in the JSON
    self.assertNotIn("John Smith", sanitized)
    self.assertNotIn("01/15/1985", sanitized)
    self.assertNotIn("123-45-6789", sanitized)
        
        # But non-PHI data should still be intact
    self.assertEqual(sanitized_dict["appointment"]["date"], "2025-05-15")
    
    @pytest.mark.standalone()
    def test_sanitize_dict_with_phi(self):
        """Test sanitizing a dictionary with PHI."""
                        data = {
                        "patient_id": "ABC12345",
                        "name": "John Smith",
                        "age": 35,
                        "contact": {
                        "phone": "555-123-4567",
                        "email": "john.smith@example.com"
                        }
                        }
        
    sanitized = self.sanitizer.sanitize(data)
        
        # Sensitive key should be entirely redacted
    self.assertEqual(sanitized["patient_id"], "[REDACTED]")
        
        # PHI should be redacted
    self.assert NotEqual(sanitized["name"], "John Smith")
        
        # Non-PHI should remain intact
    self.assertEqual(sanitized["age"], 35)
        
        # Nested PHI should be redacted
    self.assert NotEqual(sanitized["contact"]["phone"], "555-123-4567")
    self.assert NotEqual(sanitized["contact"]["email"], "john.smith@example.com")
    
    @pytest.mark.standalone()
    def test_sanitize_nested_dict_with_phi(self):
        """Test sanitizing a nested dictionary with PHI."""
                            data = {
                            "patients": [
                            {
                            "id": "P001",
                            "name": "John Smith",
                            "records": [
                            {
                            "id": "R001",
                            "note": "Patient reported headaches. SSN: 123-45-6789."
                            }
                            ]
                            }
                            ]
                            }
        
    sanitized = self.sanitizer.sanitize(data)
        
        # Deeply nested PHI should be redacted
    self.assertNotIn("123-45-6789", str(sanitized))
    self.assertNotIn("John Smith", str(sanitized))
    
    @pytest.mark.standalone()
    def test_sanitize_list_with_phi(self):
        """Test sanitizing a list with PHI."""
                                data = [
                                "Patient: John Smith",
                                "DOB: 01/15/1985",
                                "Phone: 555-123-4567"
                                ]
        
        sanitized = self.sanitizer.sanitize(data)
        
        # Each item should be sanitized
        self.assertNotIn("John Smith", sanitized[0])
        self.assertNotIn("01/15/1985", sanitized[1])
        self.assertNotIn("555-123-4567", sanitized[2])
    
        @pytest.mark.standalone()
        def test_sanitize_complex_structure(self):
        """Test sanitizing a complex data structure with PHI."""
                                    data = {
                                    "metadata": {
                                    "timestamp": "2025-01-15T14:30:00Z",
                                    "source": "EHR System"
                                    },
                                    "patients": [
                                    {
                                    "name": "John Smith",
                                    "dob": "01/15/1985",
                                    "medical_history": [
                                    "Hypertension diagnosed 2020",
                                    "Email: john.smith@example.com"
                                    ]
                                    },
                                    {
                                    "name": "Jane Doe",
                                    "dob": "05/20/1990",
                                    "medical_history": [
                                    "No significant history",
                                    "SSN: 987-65-4321"
                                    ]
                                    }
                                    ]
                                    }
        
    sanitized = self.sanitizer.sanitize(data)
        
        # Check entire structure as string
    str_sanitized = str(sanitized)
        
        # PHI should be redacted
    self.assertNotIn("John Smith", str_sanitized)
    self.assertNotIn("Jane Doe", str_sanitized)
    self.assertNotIn("01/15/1985", str_sanitized)
    self.assertNotIn("05/20/1990", str_sanitized)
    self.assertNotIn("john.smith@example.com", str_sanitized)
    self.assertNotIn("987-65-4321", str_sanitized)
        
        # Non-PHI should remain intact
    self.assertEqual(sanitized["metadata"]["timestamp"], "2025-01-15T14:30:00Z")
    self.assertEqual(sanitized["metadata"]["source"], "EHR System")
    self.assertIn("Hypertension diagnosed 2020", sanitized["patients"][0]["medical_history"][0])
    self.assertIn("No significant history", sanitized["patients"][1]["medical_history"][0])
    
    @pytest.mark.standalone()
    def test_sanitize_phi_in_logs(self):
        """Test sanitizing PHI in log messages."""
        # Create a memory handler to capture log messages
                                        log_capture = []
        class CapturingHandler(logging.Handler):
    def emit(self, record):
        log_capture.append(self.format(record))
        
        # Create a sanitized logger
        sanitizer = PHISanitizer()
        logger = logging.Logger("test_logger")
        
        # Add the capturing handler
        handler = CapturingHandler()
        formatter = PHIFormatter(sanitizer, fmt='%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Log a message with PHI
        logger.info("Processing data for patient John Smith (SSN: 123-45-6789)")
        
        # Check that PHI was redacted in the log
        self.assertNotIn("John Smith", log_capture[0])
        self.assertNotIn("123-45-6789", log_capture[0])
        self.assertIn("[REDACTED]", log_capture[0])
    
        @pytest.mark.standalone()
        def test_phi_detection_integration(self):
        """Test integration of all PHI detection components."""
        # Create a sanitizer with custom patterns
            pattern_repo = PatternRepository()
            pattern_repo.add_pattern(PHIPattern())
            name="patient_code",
            regex=r'PT\d{6}',
            context_patterns=["patient code", "patient identifier"]
        ((            ))
        
        sanitizer = PHISanitizer(pattern_repository=pattern_repo)
        
        # Test with custom pattern
        text = "Patient code: PT123456 assigned to John Smith"
        sanitized = sanitizer.sanitize(text)
        
        # Both custom and default patterns should be redacted
        self.assertNotIn("PT123456", sanitized)
        self.assertNotIn("John Smith", sanitized)
    
        @pytest.mark.standalone()
        def test_phi_sanitizer_performance(self):
        """Test performance of PHI sanitizer."""
        # In a real test, you would use performance metrics
        # Here we just ensure it handles large data reasonably
        
        # Create a large text
        large_text = "Patient info: " * 1000
        
        # Sanitize it
        sanitized = self.sanitizer.sanitize(large_text)
        
        # Just check that it completed without error
        self.assert IsInstance(sanitized, str)
    
        @pytest.mark.standalone()
        def test_preservation_of_non_phi(self):
        """Test that non-PHI information is preserved."""
                    text = """
                    System status: ONLINE
                    Database connections: 5
                    Cache hit ratio: 0.95
                    Error rate: 0.01
                    """
        
        sanitized = self.sanitizer.sanitize(text)
        
        # Non-PHI should be preserved
        self.assertEqual(sanitized, text)
    
        @pytest.mark.standalone()
        def test_sanitizer_edge_cases(self):
        """Test sanitizer behavior with edge cases."""
        # Empty string
                        self.assertEqual(self.sanitizer.sanitize(""), "")
        
        # None value
        self.assertIsNone(self.sanitizer.sanitize(None))
        
        # Empty list
        self.assertEqual(self.sanitizer.sanitize([]), [])
        
        # Empty dict
        self.assertEqual(self.sanitizer.sanitize({}), {})
        
        # Non-string primitives
        self.assertEqual(self.sanitizer.sanitize(123), 123)
        self.assertEqual(self.sanitizer.sanitize(True), True)
    
        @pytest.mark.standalone()
        def test_redaction_format_consistency(self):
        """Test that redaction formats are consistent."""
        # Full redaction
                            pattern_repo = PatternRepository()
                            pattern_repo.add_pattern(PHIPattern())
                            name="test_full",
                            regex=r'FULL\d+',
                            strategy=RedactionStrategy.FULL
        ((                            ))
        
        # Partial redaction
        pattern_repo.add_pattern(PHIPattern())
        name="test_partial",
        regex=r'PARTIAL\d+',
        strategy=RedactionStrategy.PARTIAL
        ((    ))
        
        # Hash redaction
        pattern_repo.add_pattern(PHIPattern())
        name="test_hash",
        regex=r'HASH\d+',
        strategy=RedactionStrategy.HASH
        ((    ))
        
        sanitizer = PHISanitizer(pattern_repository=pattern_repo)
        
        # Test the different redaction formats
        text = "FULL12345 PARTIAL12345 HASH12345"
        sanitized = sanitizer.sanitize(text)
        
        # Redaction formats should be consistent with pattern types
        self.assertIn("[REDACTED]", sanitized)  # Full redaction
        self.assertIn("****", sanitized)  # Partial redaction (starting characters plus asterisks)
        self.assertIn("[HASH:", sanitized)  # Hash redaction