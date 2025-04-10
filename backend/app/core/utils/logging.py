# -*- coding: utf-8 -*-
"""
Logging Utility Module.

This module provides logging configuration and utilities for the application,
with special care for HIPAA compliance and PHI protection.
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast
import re
import uuid
import json

from app.core.constants import LogLevel

# Try to import the PHI detection service if available
try:
    from app.core.services.ml.mock import MockPHIDetection
    PHI_DETECTION_AVAILABLE = True
except ImportError:
    PHI_DETECTION_AVAILABLE = False


# Configure the root logger
def configure_logging(
    level: Union[int, str] = logging.INFO,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure application logging.
    
    Args:
        level: Logging level
        log_format: Logging format
        log_file: Path to log file
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    if not log_format:
        log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers,
    )


class PHIRedactor:
    """
    Class for redacting Protected Health Information (PHI) from text.
    
    This class uses pattern matching and/or ML-based PHI detection to find and
    redact sensitive information in text to comply with HIPAA regulations.
    """
    
    # Common PHI patterns
    DEFAULT_PHI_PATTERNS = {
        # Names (simplified pattern - actual implementation would be more robust)
        "NAME": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
        
        # Dates of birth or any dates (matches common date formats)
        "DATE": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{2,4}\b",
        
        # SSN (Social Security Number)
        "SSN": r"\b\d{3}[-]\d{2}[-]\d{4}\b",
        
        # MRN (Medical Record Number) - various formats
        "MRN": r"\b(?:MRN|Medical Record):?\s*[A-Za-z0-9-]+\b",
        
        # Phone numbers
        "PHONE": r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        
        # Email addresses
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        
        # Addresses
        "ADDRESS": r"\b\d+\s[A-Za-z0-9\s,]+\b(?:Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Plaza|Plz|Place|Pl)\b",
        
        # ZIP codes
        "ZIP": r"\b\d{5}(?:-\d{4})?\b",
    }
    
    def __init__(self, 
                 phi_patterns: Optional[Dict[str, str]] = None, 
                 use_ml_detection: bool = True,
                 default_replacement: str = "[REDACTED]"):
        """
        Initialize PHI redactor.
        
        Args:
            phi_patterns: Dictionary of PHI type patterns to use for regex-based redaction
            use_ml_detection: Whether to use ML-based PHI detection if available
            default_replacement: Default text to replace PHI with
        """
        self.patterns = phi_patterns or self.DEFAULT_PHI_PATTERNS
        self.use_ml_detection = use_ml_detection and PHI_DETECTION_AVAILABLE
        self.default_replacement = default_replacement
        
        # Compile patterns for efficiency
        self.compiled_patterns = {
            phi_type: re.compile(pattern) 
            for phi_type, pattern in self.patterns.items()
        }
        
        # Initialize ML detection service if available and requested
        self.phi_detection_service = None
        if self.use_ml_detection and PHI_DETECTION_AVAILABLE:
            try:
                self.phi_detection_service = MockPHIDetection()
                self.phi_detection_service.initialize({})
            except Exception:
                self.use_ml_detection = False
                logging.warning("Failed to initialize PHI detection service. Falling back to regex only.")
        
    def redact(self, 
              text: str, 
              replacement: Optional[str] = None,
              phi_types: Optional[List[str]] = None) -> str:
        """
        Redact PHI from text.
        
        Args:
            text: Text to redact
            replacement: Text to replace PHI with (defaults to class default)
            phi_types: Specific PHI types to redact (if None, redact all)
            
        Returns:
            Redacted text
        """
        if not text:
            return text
            
        replacement = replacement or self.default_replacement
        
        # Track the redactions we're going to make
        redactions = []
        
        # First use ML-based detection if available and enabled
        if self.use_ml_detection and self.phi_detection_service:
            try:
                result = self.phi_detection_service.redact_phi(
                    text, 
                    replacement=replacement
                )
                if result and "redacted_text" in result:
                    return result["redacted_text"]
            except Exception as e:
                logging.warning(f"ML-based PHI redaction failed: {str(e)}. Falling back to regex.")
        
        # Otherwise fall back to regex-based redaction
        redacted_text = text
        
        # Filter patterns if specific types are requested
        patterns_to_use = self.compiled_patterns
        if phi_types:
            patterns_to_use = {
                phi_type: pattern 
                for phi_type, pattern in self.compiled_patterns.items()
                if phi_type in phi_types
            }
            
        # Apply each pattern
        for phi_type, pattern in patterns_to_use.items():
            redacted_text = pattern.sub(replacement, redacted_text)
            
        return redacted_text
        
    def detect(self, 
              text: str, 
              phi_types: Optional[List[str]] = None,
              min_confidence: float = 0.8) -> List[Dict[str, Any]]:
        """
        Detect PHI in text.
        
        Args:
            text: Text to analyze
            phi_types: Specific PHI types to detect (if None, detect all)
            min_confidence: Minimum confidence level for ML-based detection
            
        Returns:
            List of detected PHI instances
        """
        if not text:
            return []
            
        # First use ML-based detection if available and enabled
        if self.use_ml_detection and self.phi_detection_service:
            try:
                result = self.phi_detection_service.detect_phi(text)
                if result and "phi_instances" in result:
                    return [
                        {
                            "type": phi["type"],
                            "text": phi["text"],
                            "position": phi["position"],
                            "confidence": phi.get("confidence", 1.0)
                        }
                        for phi in result["phi_instances"]
                        if (not phi_types or phi["type"] in phi_types) and
                           phi.get("confidence", 1.0) >= min_confidence
                    ]
            except Exception as e:
                logging.warning(f"ML-based PHI detection failed: {str(e)}. Falling back to regex.")
        
        # Otherwise fall back to regex-based detection
        detected_phi = []
        
        # Filter patterns if specific types are requested
        patterns_to_use = self.patterns
        if phi_types:
            patterns_to_use = {
                phi_type: pattern 
                for phi_type, pattern in self.patterns.items()
                if phi_type in phi_types
            }
            
        # Apply each pattern
        for phi_type, pattern in patterns_to_use.items():
            for match in re.finditer(self.compiled_patterns[phi_type], text):
                detected_phi.append({
                    "type": phi_type,
                    "text": match.group(0),
                    "position": {
                        "start": match.start(),
                        "end": match.end()
                    },
                    "confidence": 1.0  # Regex always has 100% confidence
                })
            
        return detected_phi


class AuditLogger:
    """
    Audit logger for HIPAA-compliant audit trail.
    
    This class provides methods for logging audit events related to PHI access,
    modifications, and other security-relevant actions.
    """
    
    def __init__(self, logger_name: str = "audit", level: int = logging.INFO):
        """
        Initialize audit logger.
        
        Args:
            logger_name: Name of the logger
            level: Logging level
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)
        
        # Add special handler for audit logs if not already present
        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            audit_file = os.environ.get("AUDIT_LOG_FILE", "audit.log")
            
            # Create directory if it doesn't exist
            audit_dir = os.path.dirname(audit_file)
            if audit_dir and not os.path.exists(audit_dir):
                os.makedirs(audit_dir, exist_ok=True)
                
            handler = logging.FileHandler(audit_file)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] [%(trace_id)s] - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _create_audit_record(self, 
                           user_id: str, 
                           action: str, 
                           resource_type: str,
                           resource_id: Optional[str] = None,
                           details: Optional[Dict[str, Any]] = None,
                           result: str = "success") -> Dict[str, Any]:
        """
        Create an audit record.
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed (e.g., "read", "write", "delete")
            resource_type: Type of resource being accessed (e.g., "patient", "note")
            resource_id: ID of the resource being accessed
            details: Additional details about the action
            result: Result of the action ("success" or "failure")
            
        Returns:
            Audit record as a dictionary
        """
        trace_id = str(uuid.uuid4())
        
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trace_id": trace_id,
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "result": result
        }
        
        if resource_id:
            record["resource_id"] = resource_id
            
        if details:
            # Make sure we don't log any PHI
            phi_redactor = PHIRedactor()
            safe_details = {}
            for key, value in details.items():
                if isinstance(value, str):
                    safe_details[key] = phi_redactor.redact(value)
                else:
                    safe_details[key] = value
            record["details"] = safe_details
            
        return record, trace_id
    
    def log_access(self, 
                  user_id: str, 
                  resource_type: str, 
                  resource_id: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  result: str = "success") -> None:
        """
        Log access to PHI.
        
        Args:
            user_id: ID of the user accessing the data
            resource_type: Type of resource being accessed
            resource_id: ID of the resource being accessed
            details: Additional details about the access
            result: Result of the access ("success" or "failure")
        """
        record, trace_id = self._create_audit_record(
            user_id=user_id,
            action="access",
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            result=result
        )
        
        self.logger.info(
            f"User {user_id} accessed {resource_type} {resource_id or ''} - {result}",
            extra={"trace_id": trace_id}
        )
        
        # Also log the structured record
        self.logger.debug(json.dumps(record), extra={"trace_id": trace_id})
    
    def log_modification(self, 
                        user_id: str, 
                        resource_type: str, 
                        resource_id: Optional[str] = None,
                        details: Optional[Dict[str, Any]] = None,
                        result: str = "success") -> None:
        """
        Log modification of PHI.
        
        Args:
            user_id: ID of the user modifying the data
            resource_type: Type of resource being modified
            resource_id: ID of the resource being modified
            details: Additional details about the modification
            result: Result of the modification ("success" or "failure")
        """
        record, trace_id = self._create_audit_record(
            user_id=user_id,
            action="modify",
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            result=result
        )
        
        self.logger.info(
            f"User {user_id} modified {resource_type} {resource_id or ''} - {result}",
            extra={"trace_id": trace_id}
        )
        
        # Also log the structured record
        self.logger.debug(json.dumps(record), extra={"trace_id": trace_id})
    
    def log_deletion(self, 
                    user_id: str, 
                    resource_type: str, 
                    resource_id: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None,
                    result: str = "success") -> None:
        """
        Log deletion of PHI.
        
        Args:
            user_id: ID of the user deleting the data
            resource_type: Type of resource being deleted
            resource_id: ID of the resource being deleted
            details: Additional details about the deletion
            result: Result of the deletion ("success" or "failure")
        """
        record, trace_id = self._create_audit_record(
            user_id=user_id,
            action="delete",
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            result=result
        )
        
        self.logger.info(
            f"User {user_id} deleted {resource_type} {resource_id or ''} - {result}",
            extra={"trace_id": trace_id}
        )
        
        # Also log the structured record
        self.logger.debug(json.dumps(record), extra={"trace_id": trace_id})
    
    def log_export(self, 
                  user_id: str, 
                  resource_type: str, 
                  resource_id: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  result: str = "success") -> None:
        """
        Log export of PHI.
        
        Args:
            user_id: ID of the user exporting the data
            resource_type: Type of resource being exported
            resource_id: ID of the resource being exported
            details: Additional details about the export
            result: Result of the export ("success" or "failure")
        """
        record, trace_id = self._create_audit_record(
            user_id=user_id,
            action="export",
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            result=result
        )
        
        self.logger.info(
            f"User {user_id} exported {resource_type} {resource_id or ''} - {result}",
            extra={"trace_id": trace_id}
        )
        
        # Also log the structured record
        self.logger.debug(json.dumps(record), extra={"trace_id": trace_id})
    
    def log_authentication(self, 
                          user_id: str, 
                          details: Optional[Dict[str, Any]] = None,
                          result: str = "success") -> None:
        """
        Log authentication event.
        
        Args:
            user_id: ID of the user attempting authentication
            details: Additional details about the authentication
            result: Result of the authentication ("success" or "failure")
        """
        record, trace_id = self._create_audit_record(
            user_id=user_id,
            action="authenticate",
            resource_type="authentication",
            details=details,
            result=result
        )
        
        self.logger.info(
            f"User {user_id} authentication - {result}",
            extra={"trace_id": trace_id}
        )
        
        # Also log the structured record
        self.logger.debug(json.dumps(record), extra={"trace_id": trace_id})


class HIPAACompliantLogger:
    """
    Logger wrapper that ensures HIPAA compliance by redacting PHI.
    
    This class wraps a standard Python logger and automatically redacts
    any PHI in log messages to ensure HIPAA compliance.
    """
    
    def __init__(self, name: str, level: Union[int, str] = logging.INFO):
        """
        Initialize HIPAA-compliant logger.
        
        Args:
            name: Logger name
            level: Logging level
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
            
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.phi_redactor = PHIRedactor()
    
    def _sanitize_phi(self, message: Any) -> Any:
        """
        Sanitize PHI from log message.
        
        Args:
            message: Log message to sanitize
            
        Returns:
            Sanitized message
        """
        if isinstance(message, str):
            return self.phi_redactor.redact(message)
        return message
    
    def debug(self, message: Any, *args, **kwargs) -> None:
        """Log a debug message with PHI sanitization."""
        self.logger.debug(self._sanitize_phi(message), *args, **kwargs)
    
    def info(self, message: Any, *args, **kwargs) -> None:
        """Log an info message with PHI sanitization."""
        self.logger.info(self._sanitize_phi(message), *args, **kwargs)
    
    def warning(self, message: Any, *args, **kwargs) -> None:
        """Log a warning message with PHI sanitization."""
        self.logger.warning(self._sanitize_phi(message), *args, **kwargs)
    
    def error(self, message: Any, *args, **kwargs) -> None:
        """Log an error message with PHI sanitization."""
        self.logger.error(self._sanitize_phi(message), *args, **kwargs)
    
    def critical(self, message: Any, *args, **kwargs) -> None:
        """Log a critical message with PHI sanitization."""
        self.logger.critical(self._sanitize_phi(message), *args, **kwargs)
    
    def exception(self, message: Any, *args, **kwargs) -> None:
        """Log an exception with PHI sanitization."""
        self.logger.exception(self._sanitize_phi(message), *args, **kwargs)
    
    def log(self, level: int, message: Any, *args, **kwargs) -> None:
        """Log a message with PHI sanitization at the specified level."""
        self.logger.log(level, self._sanitize_phi(message), *args, **kwargs)


def get_hipaa_logger(name: str, level: Union[int, str] = logging.INFO) -> HIPAACompliantLogger:
    """
    Get a HIPAA-compliant logger instance for the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        level: Log level to use
        
    Returns:
        HIPAA-compliant logger instance
    """
    return HIPAACompliantLogger(name, level)


def get_audit_logger(name: str = "audit", level: int = logging.INFO) -> AuditLogger:
    """
    Get an audit logger instance.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Audit logger instance
    """
    return AuditLogger(name, level)


def get_logger(name: str, level: Union[int, str] = logging.INFO) -> HIPAACompliantLogger:
    """
    Get a logger instance for the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        level: Log level to use
        
    Returns:
        HIPAA-compliant logger instance
    """
    return get_hipaa_logger(name, level)
