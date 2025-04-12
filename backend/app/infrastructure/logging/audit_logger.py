"""
HIPAA-compliant audit logging for the Novamind Digital Twin Platform.

This module provides comprehensive audit logging for all PHI access and
modifications, ensuring compliance with HIPAA Security Rule § 164.312(b).
"""

import json
import logging
import os
import datetime
from typing import Any, Dict, Optional

from app.core.config.settings import settings


class AuditLogger:
    """
    HIPAA-compliant audit logger for PHI operations.
    
    This class provides secure, immutable logging of all PHI access and
    modifications, supporting both debugging and regulatory compliance.
    """
    
    # Configure standard Python logger for audit events
    _logger = logging.getLogger("hipaa.audit")
    
    @classmethod
    def setup(cls, log_dir: Optional[str] = None) -> None:
        """
        Set up the audit logger with appropriate handlers.
        
        Args:
            log_dir: Directory to store audit logs (default: from settings)
        """
        if cls._logger.handlers:
            return  # Already configured
            
        # Use settings if log_dir not provided
        log_dir = log_dir or settings.AUDIT_LOG_DIR
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a file handler for the audit log
        audit_file = os.path.join(log_dir, f"hipaa_audit_{datetime.date.today().isoformat()}.log")
        file_handler = logging.FileHandler(audit_file)
        
        # Set a secure formatter with all relevant fields
        formatter = logging.Formatter(
            '%(asctime)s [AUDIT] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Configure the logger
        cls._logger.setLevel(logging.INFO)
        cls._logger.addHandler(file_handler)
        
        # Log startup message
        cls._logger.info("HIPAA audit logging initialized")
    
    @classmethod
    def log_transaction(cls, metadata: Dict[str, Any]) -> None:
        """
        Log a transaction for audit purposes.
        
        Args:
            metadata: Dictionary containing transaction metadata:
                - user_id: ID of the user performing the action
                - action: Type of action performed
                - resource_type: Type of resource affected
                - resource_id: ID of the resource affected
                - details: Additional details about the action
        """
        # Ensure required fields are present
        required_fields = ["user_id", "action"]
        for field in required_fields:
            if field not in metadata:
                cls._logger.warning(f"Audit log missing required field: {field}")
                metadata[field] = "unknown"
        
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.datetime.now().isoformat()
        
        # Format the message as JSON for machine readability
        message = json.dumps(metadata)
        
        # Log the transaction
        cls._logger.info(f"PHI_ACCESS: {message}")
    
    @classmethod
    def log_phi_access(cls, user_id: str, patient_id: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log PHI access for audit purposes.
        
        Args:
            user_id: ID of the user accessing the PHI
            patient_id: ID of the patient whose PHI was accessed
            action: Type of access (read, write, delete)
            details: Additional details about the access
        """
        metadata = {
            "user_id": user_id,
            "patient_id": patient_id,
            "action": action,
            "timestamp": datetime.datetime.now().isoformat(),
            "details": details or {}
        }
        
        cls.log_transaction(metadata)
    
    @classmethod
    def log_security_event(cls, event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a security event for audit purposes.
        
        Args:
            event_type: Type of security event
            user_id: ID of the user involved (if applicable)
            details: Additional details about the event
        """
        metadata = {
            "event_type": event_type,
            "user_id": user_id or "system",
            "action": "security_event",
            "timestamp": datetime.datetime.now().isoformat(),
            "details": details or {}
        }
        
        cls.log_transaction(metadata)
        
        # Log at appropriate level based on event type
        if event_type in ["authentication_failure", "authorization_failure", "tampering_detected"]:
            cls._logger.warning(f"SECURITY_EVENT: {json.dumps(metadata)}")
        else:
            cls._logger.info(f"SECURITY_EVENT: {json.dumps(metadata)}")


# Initialize the audit logger when the module is imported
AuditLogger.setup()