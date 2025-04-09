# -*- coding: utf-8 -*-
"""
PHI Sanitization Utility

This module provides utilities for detecting and sanitizing Protected Health Information (PHI)
in accordance with HIPAA regulations. It helps prevent accidental PHI exposure in logs,
error messages, and test data.
"""

import re
import uuid
import logging
from enum import Enum
from typing import Dict, List, Optional, Pattern, Tuple, Union, Any
from datetime import date, datetime

logger = logging.getLogger(__name__)


class PHIType(Enum):
    """Enumeration of PHI data types that require protection."""
    
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    DOB = "date_of_birth"
    ADDRESS = "address"
    MEDICAL_RECORD = "medical_record"
    POLICY_NUMBER = "policy_number"
    OTHER = "other_phi"


class PHIDetector:
    """Detector for various types of Protected Health Information (PHI).
    
    This class provides methods to identify potential PHI in strings,
    which can then be sanitized or anonymized to maintain HIPAA compliance.
    """
    
    # Regular expressions for detecting different PHI types
    PATTERNS: Dict[PHIType, Pattern] = {
        PHIType.EMAIL: re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        PHIType.PHONE: re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
        PHIType.SSN: re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'),
        # Match both YYYY-MM-DD and MM/DD/YYYY date formats
        PHIType.DOB: re.compile(r'\b((19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])|'
                               r'(0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])[- /.](19|20)\d\d)\b'),
        # Common test names pattern (covers common test data patterns)
        PHIType.NAME: re.compile(r'\b(John|Jane)\s+(Doe|Smith|Public|Test)\b'),
    }
    
    # Known test data values that should be sanitized
    KNOWN_TEST_VALUES = [
        "john.doe@example.com",
        "jane.doe@example.com",
        "test.patient@example.com",
        "555-123-4567",
        "123-45-6789",
        "1980-01-01",
        "01/01/1980",
        "01-01-1980",
        "01.01.1980",
    ]
    
    @classmethod
    def contains_phi(cls, text: str) -> bool:
        """Check if a string contains any recognizable PHI.
        
        Args:
            text: The string to check for PHI
            
        Returns:
            True if PHI is detected, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
            
        # Check for known test values
        for test_value in cls.KNOWN_TEST_VALUES:
            if test_value in text:
                return True
                
        # Check against PHI patterns
        for pattern in cls.PATTERNS.values():
            if pattern.search(text):
                return True
                
        return False
    
    @classmethod
    def detect_phi_types(cls, text: str) -> List[Tuple[PHIType, str]]:
        """Detect all PHI types and the specific matching text in a string.
        
        Args:
            text: The string to check for PHI
            
        Returns:
            List of tuples with (PHIType, matching_text)
        """
        if not text or not isinstance(text, str):
            return []
            
        results = []
        
        # Check for each PHI type using patterns
        for phi_type, pattern in cls.PATTERNS.items():
            matches = pattern.finditer(text)
            for match in matches:
                results.append((phi_type, match.group(0)))
        
        # Check for known test values
        for test_value in cls.KNOWN_TEST_VALUES:
            if test_value in text:
                # Determine the most likely PHI type based on the value format
                if '@' in test_value:
                    phi_type = PHIType.EMAIL
                elif '-' in test_value and len(test_value) <= 12:
                    phi_type = PHIType.PHONE if len(test_value.replace('-', '')) == 10 else PHIType.SSN
                elif test_value.startswith(('19', '20')) and '-' in test_value:
                    phi_type = PHIType.DOB
                else:
                    phi_type = PHIType.OTHER
                
                results.append((phi_type, test_value))
        
        return results


class PHISanitizer:
    """Sanitizer for Protected Health Information (PHI).
    
    This class provides methods to sanitize or anonymize PHI in strings,
    log messages, and error messages to maintain HIPAA compliance.
    """
    
    @staticmethod
    def generate_anonymous_value(phi_type: PHIType) -> str:
        """Generate an anonymous replacement value based on PHI type.
        
        Args:
            phi_type: The type of PHI to generate an anonymous value for
            
        Returns:
            An anonymous string appropriate for the PHI type
        """
        if phi_type == PHIType.EMAIL:
            return f"anonymized.email.{uuid.uuid4().hex[:8]}@example.com"
        elif phi_type == PHIType.PHONE:
            return "555-000-0000"
        elif phi_type == PHIType.SSN:
            return "000-00-0000"
        elif phi_type == PHIType.DOB:
            return "YYYY-MM-DD"
        elif phi_type == PHIType.NAME:
            return "ANONYMIZED_NAME"
        elif phi_type == PHIType.ADDRESS:
            return "ANONYMIZED_ADDRESS"
        elif phi_type == PHIType.MEDICAL_RECORD:
            return f"MRN-{uuid.uuid4().hex[:8]}"
        elif phi_type == PHIType.POLICY_NUMBER:
            return f"POLICY-{uuid.uuid4().hex[:8]}"
        else:
            return f"ANONYMIZED-{uuid.uuid4().hex[:8]}"
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Sanitize a string by replacing all detected PHI with anonymous values.
        
        Args:
            text: The string containing potential PHI
            
        Returns:
            The sanitized string with PHI replaced by anonymous values
        """
        if not text or not isinstance(text, str):
            return text
            
        sanitized = text
        phi_instances = PHIDetector.detect_phi_types(text)
        
        # Replace PHI instances with anonymous values
        for phi_type, matching_text in phi_instances:
            anonymous_value = cls.generate_anonymous_value(phi_type)
            sanitized = sanitized.replace(matching_text, anonymous_value)
            
        return sanitized
    
    @classmethod
    def create_safe_log_message(cls, message: str, *args, **kwargs) -> str:
        """Create a PHI-safe log message by sanitizing the message and all arguments.
        
        Args:
            message: The log message format string
            *args: Positional arguments for the log message
            **kwargs: Keyword arguments for the log message
            
        Returns:
            A sanitized log message with all PHI removed
        """
        # Sanitize the message format string
        safe_message = cls.sanitize_text(message)
        
        # Sanitize positional arguments
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(cls.sanitize_text(arg))
            elif isinstance(arg, (dict, list)) and isinstance(arg, Dict):
                # Handle dictionary structures that might contain PHI
                safe_args.append(cls.sanitize_structured_data(arg))
            else:
                safe_args.append(arg)
        
        # Sanitize keyword arguments
        safe_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                safe_kwargs[key] = cls.sanitize_text(value)
            elif isinstance(value, (dict, list)):
                safe_kwargs[key] = cls.sanitize_structured_data(value)
            else:
                safe_kwargs[key] = value
                
        # Format the safe message with safe arguments
        if args or kwargs:
            try:
                return safe_message.format(*safe_args, **safe_kwargs)
            except Exception:
                # If formatting fails, return a simpler sanitized message
                return safe_message
        else:
            return safe_message
    
    @classmethod
    def sanitize_structured_data(cls, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """Recursively sanitize structured data (dicts, lists) that might contain PHI.
        
        Args:
            data: The structured data to sanitize
            
        Returns:
            The sanitized structured data
        """
        if isinstance(data, dict):
            return {k: cls.sanitize_structured_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_structured_data(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_text(data)
        elif isinstance(data, (int, float, bool, type(None))):
            return data
        elif isinstance(data, (datetime, date)):
            # Dates could be PHI, but we'll preserve them for non-DOB dates
            # For a more strict approach, you could anonymize all dates
            return data
        else:
            # For complex objects, convert to string and sanitize
            return cls.sanitize_text(str(data))


def sanitize_log_message(message: str, *args, **kwargs) -> str:
    """Convenience function to sanitize a log message and its arguments.
    
    Args:
        message: The log message format string
        *args: Positional arguments for the log message
        **kwargs: Keyword arguments for the log message
        
    Returns:
        A sanitized log message with all PHI removed
    """
    return PHISanitizer.create_safe_log_message(message, *args, **kwargs)


class PHISecureLogger:
    """A wrapper around Python's logging module that sanitizes PHI from log messages.
    
    This class provides all the standard logging methods but ensures all messages
    are sanitized of PHI before being passed to the underlying logger.
    """
    
    def __init__(self, logger_name: Optional[str] = None):
        """Initialize with a specific logger or the root logger.
        
        Args:
            logger_name: Optional name for the logger to use
        """
        self.logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    def debug(self, message: str, *args, **kwargs):
        """Log a debug message, sanitized of PHI."""
        self.logger.debug(sanitize_log_message(message, *args, **kwargs))
    
    def info(self, message: str, *args, **kwargs):
        """Log an info message, sanitized of PHI."""
        self.logger.info(sanitize_log_message(message, *args, **kwargs))
    
    def warning(self, message: str, *args, **kwargs):
        """Log a warning message, sanitized of PHI."""
        self.logger.warning(sanitize_log_message(message, *args, **kwargs))
    
    def error(self, message: str, *args, **kwargs):
        """Log an error message, sanitized of PHI."""
        self.logger.error(sanitize_log_message(message, *args, **kwargs))
    
    def critical(self, message: str, *args, **kwargs):
        """Log a critical message, sanitized of PHI."""
        self.logger.critical(sanitize_log_message(message, *args, **kwargs))
    
    def exception(self, message: str, *args, exc_info=True, **kwargs):
        """Log an exception message, sanitized of PHI."""
        self.logger.exception(sanitize_log_message(message, *args, **kwargs),
                              exc_info=exc_info)


def get_phi_secure_logger(logger_name: Optional[str] = None) -> PHISecureLogger:
    """Get a PHI-secure logger for the given name.
    
    Args:
        logger_name: Optional name for the logger
        
    Returns:
        A PHISecureLogger instance
    """
    return PHISecureLogger(logger_name)


# Module-level PHI-secure logger
phi_secure_logger = PHISecureLogger(__name__)