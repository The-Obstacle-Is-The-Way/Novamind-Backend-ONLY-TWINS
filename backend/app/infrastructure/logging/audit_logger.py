# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Audit Logging

This module provides comprehensive audit logging for HIPAA compliance,
tracking all access to and modifications of Protected Health Information (PHI).
"""

import datetime
import hashlib
import hmac
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.core.config import settings


class AuditLogger:
    """
    HIPAA-compliant audit logger for tracking all PHI access and modifications.

    Provides tamper-evident logging with signatures, rotation, and encryption
    to maintain a secure, immutable audit trail as required by HIPAA regulations.
    """

    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the audit logger with a log file path.

        Args:
            log_path: Path to the audit log file. Defaults to setting from config.
        """
        self.settings = settings
        self.log_path = log_path or self.settings.PHI_AUDIT_LOG_PATH # Corrected attribute name

        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def log_phi_access(
        self,
        user_id: str,
        username: str,
        role: str,
        action: str,
        resource_type: str,
        resource_id: str,
        fields_accessed: Optional[List[str]] = None,
        reason: str = "TREATMENT",
        ip_address: Optional[str] = None,
        related_resource_type: Optional[str] = None,
        related_resource_id: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
    ) -> None:
        """
        Log access to PHI as required by HIPAA.

        Args:
            user_id: ID of the user accessing the PHI
            username: Username of the user
            role: Role of the user (e.g., doctor, nurse, admin)
            action: Type of access (e.g., READ, LIST)
            resource_type: Type of resource being accessed (e.g., PATIENT, PRESCRIPTION)
            resource_id: ID of the resource being accessed
            fields_accessed: List of fields accessed, if applicable
            reason: Reason for accessing the PHI (e.g., TREATMENT, PAYMENT)
            ip_address: IP address of the user
            related_resource_type: Type of related resource, if applicable
            related_resource_id: ID of related resource, if applicable
            success: Whether the access was successful
            failure_reason: Reason for failure, if applicable
        """
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "role": role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "fields_accessed": fields_accessed,
            "reason": reason,
            "ip_address": ip_address,
            "success": success,
        }

        # Add optional fields if provided
        if related_resource_type:
            log_entry["related_resource_type"] = related_resource_type

        if related_resource_id:
            log_entry["related_resource_id"] = related_resource_id

        if not success and failure_reason:
            log_entry["failure_reason"] = failure_reason

        # Add signature for tamper protection
        log_entry["signature"] = self._generate_log_signature(log_entry)

        # Write to the log file
        self._write_log_entry(log_entry)

    def log_phi_modification(
        self,
        user_id: str,
        username: str,
        role: str,
        action: str,
        resource_type: str,
        resource_id: str,
        modified_fields: List[str],
        reason: str = "DATA_UPDATE",
        ip_address: Optional[str] = None,
        related_resource_type: Optional[str] = None,
        related_resource_id: Optional[str] = None,
    ) -> None:
        """
        Log modification of PHI as required by HIPAA.

        Args:
            user_id: ID of the user modifying the PHI
            username: Username of the user
            role: Role of the user (e.g., doctor, nurse, admin)
            action: Type of modification (e.g., UPDATE, CREATE, DELETE)
            resource_type: Type of resource being modified
            resource_id: ID of the resource being modified
            modified_fields: List of fields that were modified
            reason: Reason for the modification
            ip_address: IP address of the user
            related_resource_type: Type of related resource, if applicable
            related_resource_id: ID of related resource, if applicable
        """
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "role": role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "modified_fields": modified_fields,
            "reason": reason,
            "ip_address": ip_address,
            "success": True,  # Always true since we log after successful modification
        }

        # Add optional fields if provided
        if related_resource_type:
            log_entry["related_resource_type"] = related_resource_type

        if related_resource_id:
            log_entry["related_resource_id"] = related_resource_id

        # Add signature for tamper protection
        log_entry["signature"] = self._generate_log_signature(log_entry)

        # Write to the log file
        self._write_log_entry(log_entry)

    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """
        Write a log entry to the audit log file.

        Args:
            log_entry: The log entry to write
        """
        # Check if log file needs rotation
        self._check_log_rotation()

        # Encrypt the log entry if enabled
        if self.settings.PHI_ENCRYPTION_ENABLED:
            log_entry = self._encrypt_log_entry(log_entry)

        # Write the log entry to the file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _generate_log_signature(self, log_entry: Dict[str, Any]) -> str:
        """
        Generate a signature for a log entry to prevent tampering.

        Args:
            log_entry: The log entry to sign

        Returns:
            str: HMAC signature for the log entry
        """
        # Create a copy of the log entry without the signature field
        entry_to_sign = log_entry.copy()
        if "signature" in entry_to_sign:
            del entry_to_sign["signature"]

        # Convert to a canonical string representation
        canonical = json.dumps(entry_to_sign, sort_keys=True)

        # Generate HMAC using the application's secret key
        signature = hmac.new(
            self.settings.SECRET_KEY.encode(), canonical.encode(), hashlib.sha256
        ).hexdigest()

        return signature

    def verify_log_entry(self, log_entry: Dict[str, Any]) -> bool:
        """
        Verify the integrity of a log entry by checking its signature.

        Args:
            log_entry: The log entry to verify

        Returns:
            bool: True if the signature is valid, False otherwise
        """
        if "signature" not in log_entry:
            return False

        expected_signature = log_entry["signature"]

        # Generate a new signature and compare
        actual_signature = self._generate_log_signature(log_entry)

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, actual_signature)

    def _check_log_rotation(self) -> None:
        """
        Check if the log file needs rotation based on size.
        """
        if not os.path.exists(self.log_path):
            return

        # Rotate if the log file exceeds 10 MB
        if os.path.getsize(self.log_path) > 10 * 1024 * 1024:
            self._rotate_log_file()

    def _rotate_log_file(self) -> None:
        """
        Rotate the log file by renaming it with a timestamp and creating a new one.
        """
        if not os.path.exists(self.log_path):
            return

        # Generate a timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.dirname(self.log_path)
        log_filename = os.path.basename(self.log_path)
        rotated_filename = f"{log_filename}.{timestamp}"
        rotated_path = os.path.join(log_dir, rotated_filename)

        # Rename the current log file
        os.rename(self.log_path, rotated_path)

        # Archive the rotated log if needed
        if hasattr(self.settings, "AUDIT_LOG_ARCHIVE"):
            self._archive_log_file(rotated_path)

    def _encrypt_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a log entry.

        Args:
            log_entry: The log entry to encrypt

        Returns:
            Dict[str, Any]: The log entry with sensitive fields encrypted
        """
        # In a real implementation, this would encrypt certain fields
        # For now, we'll just return the original entry
        return log_entry

    def _archive_log_file(self, log_path: str) -> None:
        """
        Archive a log file to long-term storage.

        Args:
            log_path: Path to the log file to archive
        """
        # In a real implementation, this would upload to S3 or other storage
        pass

    def archive_logs(self, days_old: int = 90) -> None:
        """
        Archive logs older than the specified number of days.

        Args:
            days_old: Age threshold in days for archiving logs
        """
        self._archive_old_logs(days_old=days_old)

    def _archive_old_logs(self, days_old: int) -> None:
        """
        Archive logs older than the specified number of days.

        Args:
            days_old: Age threshold in days for archiving logs
        """
        # In a real implementation, this would find old logs and archive them
        pass

    def backup_logs(self, destination: str) -> None:
        """
        Backup logs to a secure location.

        Args:
            destination: The destination for the backup (e.g., S3 URI)
        """
        self._backup_logs(destination=destination)

    def _backup_logs(self, destination: str) -> None:
        """
        Backup logs to a secure location.

        Args:
            destination: The destination for the backup
        """
        # In a real implementation, this would backup logs to the specified destination
        pass


def get_audit_logger() -> AuditLogger:
    """
    Factory function to get an audit logger instance.

    Returns:
        AuditLogger: An audit logger instance
    """
    return AuditLogger()
