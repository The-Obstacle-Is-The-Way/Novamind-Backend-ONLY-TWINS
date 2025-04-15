# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Patient Repository

This module provides repository pattern implementation for patient data access
with field-level encryption and strict access controls.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session, joinedload

from app.infrastructure.security.encryption.base_encryption_service import BaseEncryptionService

# Configure logger without PHI
logger = logging.getLogger("patient_repository")


class PatientRepository:
    """
    Repository for secure patient data access with encryption and access controls.

    This repository implements the Repository pattern for patient data with HIPAA-compliant
    security features:
    - Field-level encryption for PHI
    - Role-based access controls
    - Audit logging (sanitized of PHI)
    """

    def __init__(self, db_session: Session, encryption_service: BaseEncryptionService):
        """
        Initialize the patient repository.

        Args:
            db_session: SQLAlchemy database session
            encryption_service: Encryption service for PHI fields
        """
        self.db_session = db_session
        self.encryption_service = encryption_service

        # Define which fields contain PHI and need encryption
        self.sensitive_fields = [
            "ssn",
            "email",
            "phone",
            "diagnosis",
            "address",
            "insurance_id",
            "medical_record_number",
        ]

        logger.info("PatientRepository initialized")

    async def get_by_id(
        self, patient_id: str, user: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get patient by ID with encryption and access control.

        Args:
            patient_id: Patient ID to retrieve
            user: User context with role and permissions

        Returns:
            Patient data with decrypted fields or None if unauthorized
        """
        # Check access permissions
        if not self._check_access(user, patient_id):
            logger.warning(f"Access denied to patient {patient_id} - unauthorized user")
            return None

        try:
            # In a real implementation, this would query the database
            # For now, return mock data
            patient_data = self._get_mock_patient(patient_id)

            if not patient_data:
                return None

            # Log the access (without PHI)
            logger.info(
                f"Patient {patient_id} data accessed by user {user.get('id') if user else 'Unknown'}"
            )

            # Decrypt sensitive fields before returning
            self._decrypt_patient_fields(patient_data)
            return patient_data

        except Exception as e:
            logger.error(f"Error retrieving patient: {str(e)}")
            return None

    async def create(
        self, patient_data: Dict[str, Any], user: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new patient with encrypted sensitive data.

        Args:
            patient_data: Patient data to store
            user: User context with role and permissions

        Returns:
            Created patient data or None if unauthorized

        Raises:
            PermissionError: If user is not authorized to create patients
        """
        # Check creation permissions
        if not user or user.get("role") not in ["admin", "doctor"]:
            logger.warning(
                f"Patient creation denied - unauthorized user role: {user.get('role') if user else 'None'}"
            )
            raise PermissionError("Unauthorized to create patient records")

        try:
            # Make a copy to avoid modifying the original
            patient_copy = patient_data.copy()

            # Generate an ID if not provided
            if "id" not in patient_copy:
                patient_copy["id"] = f"patient_{self._generate_id()}"

            # Encrypt sensitive fields
            self._encrypt_patient_fields(patient_copy)

            # In a real implementation, this would save to the database
            # Log the creation (without PHI)
            logger.info(
                f"Patient {patient_copy['id']} created by user {user.get('id')}"
            )

            # Return the created patient with encrypted fields
            return patient_copy

        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}")
            return None

    async def update(
        self,
        patient_id: str,
        patient_data: Dict[str, Any],
        user: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update patient data with encryption and access control.

        Args:
            patient_id: Patient ID to update
            patient_data: New patient data
            user: User context with role and permissions

        Returns:
            Updated patient data or None if unauthorized

        Raises:
            PermissionError: If user is not authorized to update the patient
        """
        # Check update permissions
        if not self._check_access(user, patient_id):
            logger.warning(
                f"Patient update denied for {patient_id} - unauthorized user"
            )
            raise PermissionError("Unauthorized to update patient records")

        try:
            # Make a copy to avoid modifying the original
            patient_copy = patient_data.copy()

            # Ensure ID matches
            patient_copy["id"] = patient_id

            # Encrypt sensitive fields
            self._encrypt_patient_fields(patient_copy)

            # In a real implementation, this would update the database
            # Log the update (without PHI)
            logger.info(
                f"Patient {patient_id} updated by user {user.get('id') if user else 'Unknown'}"
            )

            # Decrypt for return
            self._decrypt_patient_fields(patient_copy)
            return patient_copy

        except Exception as e:
            logger.error(f"Error updating patient: {str(e)}")
            return None

    def _check_access(self, user: Optional[Dict[str, Any]], patient_id: str) -> bool:
        """
        Check if user has access to patient data.

        Args:
            user: User context with role and permissions
            patient_id: Patient ID to check access for

        Returns:
            True if access is allowed, False otherwise
        """
        if not user:
            return False

        if user.get("role") == "admin":
            return True

        if user.get("role") == "doctor":
            # Check if this doctor is assigned to this patient
            return patient_id in user.get("patient_ids", [])

        if user.get("role") == "patient":
            # Patients can only access their own data
            return user.get("id") == patient_id

        return False

    def _encrypt_patient_fields(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive patient fields.

        Args:
            patient_data: Patient data to encrypt

        Returns:
            Patient data with encrypted sensitive fields
        """
        for field in self.sensitive_fields:
            if field in patient_data and patient_data[field]:
                patient_data[field] = self.encryption_service.encrypt(
                    patient_data[field]
                )
        return patient_data

    def _decrypt_patient_fields(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive patient fields.

        Args:
            patient_data: Patient data to decrypt

        Returns:
            Patient data with decrypted sensitive fields
        """
        for field in self.sensitive_fields:
            if field in patient_data and patient_data[field]:
                patient_data[field] = self.encryption_service.decrypt(
                    patient_data[field]
                )
        return patient_data

    def _generate_id(self) -> str:
        """
        Generate a unique ID for a new patient.

        Returns:
            Unique ID string
        """
        import uuid

        return str(uuid.uuid4())

    def _get_mock_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get mock patient data for testing.

        Args:
            patient_id: Patient ID to get

        Returns:
            Mock patient data with encrypted fields
        """
        # This is just mock data for testing
        if patient_id == "patient1":
            return {
                "id": patient_id,
                "name": "Jane Doe",
                "ssn": "ENCRYPTED[123-45-6789]",
                "email": "ENCRYPTED[jane.doe@example.com]",
                "phone": "ENCRYPTED[555-123-4567]",
                "diagnosis": "ENCRYPTED[F41.1 Generalized Anxiety Disorder]",
            }
        return None
