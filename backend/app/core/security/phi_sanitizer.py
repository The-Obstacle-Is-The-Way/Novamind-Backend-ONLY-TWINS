"""
PHI Sanitization module for the Novamind Digital Twin Platform.

This module provides functionality for detecting and sanitizing Protected Health
Information (PHI) from logs, error messages, and other text to ensure HIPAA compliance.
"""
import re
from typing import Dict, Any, List, Union, Optional, Pattern
import logging
from datetime import datetime


class PHISanitizer:
    """
    Class for detecting and sanitizing Protected Health Information (PHI).
    
    This class provides methods to detect various types of PHI in text
    and replace them with safe placeholders to ensure HIPAA compliance.
    """
    
    def __init__(self):
        """Initialize PHI detection patterns."""
        # Define regex patterns for different PHI types
        self._patterns: Dict[str, Pattern] = {
            "names": re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),  # Basic name pattern
            "ssn": re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'),  # SSN pattern
            "dob": re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),  # Date pattern
            "phone": re.compile(r'\b\(?[2-9]\d{2}\)?[-\s]?\d{3}[-\s]?\d{4}\b'),  # Phone pattern
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email pattern
            "address": re.compile(r'\b\d+\s[A-Za-z0-9\s,]+\b(?:\s*(?:Apt|Unit|Suite)\s*[A-Za-z0-9]+)?'),  # Address pattern
            "mrn": re.compile(r'\b(?:MR[-\s]?|#)?\d{5,10}\b'),  # Medical Record Number pattern
            "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),  # IP address pattern
            "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),  # Credit card pattern
            "zip_code": re.compile(r'\b\d{5}(?:[-\s]\d{4})?\b'),  # ZIP code pattern
        }
        
        # Initialize a logger
        self._logger = logging.getLogger(__name__)
        
    def sanitize(self, text: Union[str, Dict, List, Any]) -> Union[str, Dict, List, Any]:
        """
        Sanitize PHI from text or data structures.
        
        This method detects and replaces PHI in text. It can process strings,
        dictionaries, lists, or other data structures recursively.
        
        Args:
            text: Text or data structure to sanitize
            
        Returns:
            Sanitized text or data structure
        """
        if isinstance(text, str):
            return self._sanitize_string(text)
        elif isinstance(text, dict):
            return self._sanitize_dict(text)
        elif isinstance(text, list):
            return self._sanitize_list(text)
        else:
            # Return other data types unchanged
            return text
    
    def _sanitize_string(self, text: str) -> str:
        """
        Sanitize PHI from a string.
        
        Args:
            text: String to sanitize
            
        Returns:
            Sanitized string
        """
        # Track if PHI was detected
        phi_detected = False
        detected_types = []
        
        # Process with each pattern
        for phi_type, pattern in self._patterns.items():
            # Find all matches
            matches = pattern.findall(text)
            
            # Replace each match with [REDACTED]
            if matches:
                phi_detected = True
                detected_types.append(phi_type)
                text = pattern.sub("[REDACTED]", text)
        
        # Log PHI detection if any was found (but don't log the actual PHI)
        if phi_detected:
            self._log_phi_detection(
                text_length=len(text),
                detected_types=detected_types
            )
        
        return text
    
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
    
    def _log_phi_detection(self, text_length: int, detected_types: List[str]) -> None:
        """
        Log detection of PHI (without including the actual PHI).
        
        Args:
            text_length: Length of the text where PHI was detected
            detected_types: Types of PHI detected
        """
        # Get the current user ID from the security context if available
        user_id = self._get_current_user_id()
        
        # Log the detection event
        self.log_phi_detection(
            user_id=user_id,
            details={
                "text_length": text_length,
                "detected_types": detected_types,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _get_current_user_id(self) -> str:
        """
        Get the current user ID from the security context.
        
        Returns:
            User ID if available, otherwise "system"
        """
        try:
            # In a real implementation, this would get the current user ID
            # from the security context, but for testing we'll use a placeholder
            return "system"
        except Exception:
            return "system"
    
    def log_phi_detection(self, user_id: str, details: Dict[str, Any]) -> None:
        """
        Log PHI detection event.
        
        This method would typically send the event to an audit logging system.
        
        Args:
            user_id: ID of the user who triggered the event
            details: Additional details about the event
        """
        # In a real implementation, this would log to a secure audit log
        self._logger.warning(
            f"PHI detection event by user {user_id}: {len(details.get('detected_types', []))} type(s) detected"
        )