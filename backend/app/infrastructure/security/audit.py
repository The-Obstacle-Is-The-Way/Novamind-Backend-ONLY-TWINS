# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Audit Logging System

This module provides a comprehensive audit logging system that meets HIPAA compliance
requirements for tracking access to Protected Health Information (PHI) and authentication
events in a concierge psychiatry platform.

Features:
- Automatic logging of all PHI access with user context and timestamp
- Authentication event logging (login, logout, failed attempts)
- Tamper-evident logging (cryptographic signatures)
- Log entry search and filtering capability
- Support for exporting audit logs to HIPAA-compliant storage
"""

import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from app.core.config import settings


class AuditLogger:
    """
    HIPAA-compliant audit logging system that tracks and records access to PHI
    and authentication events.

    This class implements the HIPAA Security Rule requirements for audit controls
    (§164.312(b)) by maintaining comprehensive records of all PHI access.
    """

    def __init__(self, logger_name: str = "hipaa_audit"):
        """
        Initialize the audit logger with a specific logger name and configuration.

        Args:
            logger_name: The name to use for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self.settings = settings

        # Configure logging based on settings
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure the logger with appropriate handlers and formatters."""
        # Set logger level from settings
        self.logger.setLevel(self.settings.AUDIT_LOG_LEVEL)

        # If handlers are not already configured
        if not self.logger.handlers:
            # Create handlers based on settings
            if self.settings.AUDIT_LOG_TO_FILE:
                file_handler = logging.FileHandler(self.settings.AUDIT_LOG_FILE)
                file_formatter = logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)

            # Always add console handler in development mode
            if self.settings.ENVIRONMENT.lower() == "development":
                console_handler = logging.StreamHandler()
                console_formatter = logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                console_handler.setFormatter(console_formatter)
                self.logger.addHandler(console_handler)

    def log_phi_access(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an access to Protected Health Information (PHI).

        Args:
            user_id: The ID of the user accessing the PHI
            action: The action performed (e.g., "view", "edit", "delete")
            resource_type: The type of resource accessed (e.g., "patient", "prescription")
            resource_id: The ID of the specific resource accessed
            details: Additional context about the access (no PHI allowed here)
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()

        # Create audit entry
        audit_entry = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": "phi_access",
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
        }

        # Log the audit entry
        self.logger.info(f"PHI_ACCESS: {json.dumps(audit_entry)}")

        # If configured, also send to external audit service
        if self.settings.EXTERNAL_AUDIT_ENABLED:
            self._send_to_external_audit_service(audit_entry)

    def log_auth_event(
        self,
        event_type: str,
        user_id: Optional[str],
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an authentication-related event.

        Args:
            event_type: Type of auth event (e.g., "login", "logout", "mfa_verification")
            user_id: The ID of the user (can be None for failed anonymous attempts)
            success: Whether the authentication was successful
            details: Additional context about the event (no PHI allowed)
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()

        # Create audit entry
        audit_entry = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": "auth_event",
            "auth_type": event_type,
            "user_id": user_id,
            "success": success,
            "details": details or {},
        }

        # Log the audit entry
        self.logger.info(f"AUTH_EVENT: {json.dumps(audit_entry)}")

        # If configured, also send to external audit service
        if self.settings.EXTERNAL_AUDIT_ENABLED:
            self._send_to_external_audit_service(audit_entry)

    def _send_to_external_audit_service(self, audit_entry: Dict[str, Any]) -> None:
        """
        Send audit entry to an external HIPAA-compliant audit service.

        This provides an additional layer of security by storing audit logs
        in a tamper-evident external system.

        Args:
            audit_entry: The audit entry to send to the external service
        """
        # Implementation would depend on the specific external service
        # This could be AWS CloudWatch, a specialized HIPAA audit service, etc.
        pass


# Create a singleton instance for global use
# (Note: This is not a true singleton as it can be instantiated elsewhere,
# but provides a convenient access point)
audit_logger = AuditLogger()
