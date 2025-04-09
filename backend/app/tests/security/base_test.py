"""
Base Security Test Class

This module provides a base class for all security tests in the application,
with a focus on HIPAA compliance, PHI protection, and secure practices.
"""

import unittest
import re
from typing import Dict, Any, List, Optional, Set, Pattern
import json
import logging
from unittest.mock import patch, MagicMock

# Configure logging to prevent PHI leakage
logging.basicConfig(level=logging.ERROR)


class BaseSecurityTest(unittest.TestCase):
    """
    Base class for all security and HIPAA compliance tests.
    
    This class extends unittest.TestCase with enhanced security testing
    capabilities, focusing on PHI protection, access controls, encryption,
    and audit logging validation.
    """
    
    # Common PHI patterns to detect leakage
    PHI_PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "mrn": r"\bMRN[\s:]*\d{6,10}\b",
        "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        "phone": r"\b(\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}\b",
        "name_with_context": r"\b(patient|dr\.|doctor|client)[\s:]+([A-Z][a-z]+\s+[A-Z][a-z]+)\b",
        "address": r"\b\d+\s+[A-Za-z]+\s+(st|ave|road|boulevard|blvd|ln|lane|drive|dr|court|ct)\.?\b",
        "date_of_birth": r"\b(dob|date\s+of\s+birth)[\s:]+\d{1,2}/\d{1,2}/\d{2,4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    }
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        super().setUp()
        # Create patch context managers
        self.patches = []
        self.mocks = {}
        
        # Mock audit log for testing
        self.audit_events = []
        
        # Create patterns for PHI detection
        self.compile_phi_patterns()
        
        # Suppress logs during tests
        logging.disable(logging.CRITICAL)
    
    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Stop all patches
        for patcher in self.patches:
            patcher.stop()
        
        # Clear mocks and audit events
        self.mocks.clear()
        self.audit_events.clear()
        
        # Re-enable logging
        logging.disable(logging.NOTSET)
        
        super().tearDown()
    
    def compile_phi_patterns(self) -> None:
        """Compile PHI regex patterns for efficient reuse."""
        self.phi_compiled_patterns: Dict[str, Pattern] = {}
        for name, pattern in self.PHI_PATTERNS.items():
            self.phi_compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
    
    def create_mock(self, target: str, **kwargs) -> MagicMock:
        """Create a mock for the specified target.
        
        Args:
            target: Target to mock, in the form 'package.module.Class'
            **kwargs: Additional arguments to pass to patch
            
        Returns:
            The created mock object
        """
        patcher = patch(target, **kwargs)
        mock = patcher.start()
        self.patches.append(patcher)
        self.mocks[target] = mock
        return mock
    
    def verify_no_phi_in_logs(self, log_content: str) -> None:
        """Verify that no PHI is present in log content.
        
        Args:
            log_content: Log content to check
            
        Raises:
            AssertionError: If PHI is detected in logs
        """
        for phi_type, pattern in self.phi_compiled_patterns.items():
            matches = pattern.findall(log_content)
            if matches:
                raise AssertionError(
                    f"PHI detected in logs! {phi_type} pattern matched: {matches}"
                )
    
    def verify_secure_headers(self, headers: Dict[str, str]) -> None:
        """Verify that secure headers are present in HTTP response.
        
        Args:
            headers: HTTP headers dictionary
            
        Raises:
            AssertionError: If secure headers are missing or improperly configured
        """
        required_headers = {
            "Strict-Transport-Security": "max-age=",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": None,  # Just check existence
            "X-XSS-Protection": "1; mode=block",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        }
        
        for header, value_prefix in required_headers.items():
            self.assertIn(header, headers, f"Missing secure header: {header}")
            if value_prefix:
                self.assertTrue(
                    headers[header].startswith(value_prefix),
                    f"Invalid value for header {header}: {headers[header]}"
                )
    
    def verify_audit_logging(self, expected_operations: List[str]) -> None:
        """Verify that required operations were properly audit logged.
        
        Args:
            expected_operations: List of operations that should be logged
            
        Raises:
            AssertionError: If audit logging is incomplete
        """
        logged_operations = set(event.get("operation", "") for event in self.audit_events)
        missing_operations = set(expected_operations) - logged_operations
        
        if missing_operations:
            raise AssertionError(
                f"Missing audit logs for operations: {missing_operations}"
            )
    
    def verify_data_encryption(self, data: Any) -> None:
        """Verify that sensitive data is encrypted.
        
        Args:
            data: Data to check for encryption
            
        Raises:
            AssertionError: If unencrypted sensitive data is detected
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Sensitive field detection
                if any(key.lower() == field for field in [
                    "password", "secret", "key", "token", "ssn", "dob", "phi"
                ]):
                    # Ensure value isn't plaintext (basic check)
                    if isinstance(value, str):
                        # Check for typical encryption indicators
                        is_encrypted = (
                            value.startswith("$") or  # Bcrypt
                            value.startswith("pbkdf2:") or  # PBKDF2
                            len(value) > 20 and not self._contains_phi(value)  # Long hash-like string
                        )
                        self.assertTrue(
                            is_encrypted,
                            f"Sensitive field '{key}' appears to be unencrypted"
                        )
                
                # Recursively check nested structures
                if isinstance(value, (dict, list)):
                    self.verify_data_encryption(value)
        
        elif isinstance(data, list):
            for item in data:
                self.verify_data_encryption(item)
    
    def _contains_phi(self, text: str) -> bool:
        """Check if text contains patterns that look like PHI.
        
        Args:
            text: Text to check for PHI
            
        Returns:
            True if PHI is detected, False otherwise
        """
        if not isinstance(text, str):
            return False
            
        for pattern in self.phi_compiled_patterns.values():
            if pattern.search(text):
                return True
        return False
    
    def verify_access_control(self, 
                             unauthorized_user: Dict[str, Any],
                             protected_endpoint: str,
                             method: str = "GET",
                             data: Optional[Dict[str, Any]] = None) -> None:
        """Verify that access control properly restricts unauthorized access.
        
        Args:
            unauthorized_user: User credentials without proper authorization
            protected_endpoint: Endpoint that requires authorization
            method: HTTP method (default: "GET")
            data: Request data for POST/PUT requests (default: None)
            
        Raises:
            AssertionError: If unauthorized access is allowed
        """
        # To be implemented based on specific auth framework
        # This is a placeholder for the actual implementation
        pass