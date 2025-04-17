# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Patient Repository

This module provides repository pattern implementation for patient data access
with field-level encryption and strict access controls.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

# Import necessary SQLAlchemy components
from sqlalchemy import select, delete as sqlalchemy_delete # Alias delete to avoid name clash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session # Keep for type hinting if synchronous methods exist, but main session is async

# Import domain entity and ORM model (assuming paths)
from app.domain.entities.patient import Patient
# from app.infrastructure.persistence.sqlalchemy.models.patient_model import PatientModel # Assumed path
# Corrected import using alias to avoid name collision
from app.infrastructure.persistence.sqlalchemy.models.patient import Patient as PatientModel
# Import exception types if needed for specific error handling
# from sqlalchemy.exc import NoResultFound, MultipleResultsFound

from app.infrastructure.security.encryption.base_encryption_service import BaseEncryptionService

# Configure logger without PHI
logger = logging.getLogger(__name__) # Use __name__ for standard practice


class SQLAlchemyPatientRepository:
    """
    Repository for secure patient data access with encryption and access controls.

    This repository implements the Repository pattern for patient data with HIPAA-compliant
    security features:
    - Field-level encryption for PHI using an injected encryption service.
    - Role-based access controls via the _check_access method.
    - Uses SQLAlchemy async session for database interactions.
    - Assumes an ORM model 'PatientModel' mapped to the database table.
    """

    def __init__(self, db_session: AsyncSession, encryption_service: BaseEncryptionService):
        """
        Initialize the patient repository.

        Args:
            db_session: SQLAlchemy asynchronous database session.
            encryption_service: Encryption service for PHI fields.
        """
        self.db_session = db_session
        self.encryption_service = encryption_service

        # Define which fields contain PHI and need encryption/decryption.
        # These should match fields in both Patient domain entity and PatientModel ORM model.
        self.sensitive_fields = [
            "first_name", # Example: if first name is considered sensitive
            "last_name",  # Example: if last name is considered sensitive
            "ssn",
            "email",
            "phone",
            "address",
            "date_of_birth", # Date of birth is PHI
            # Add other sensitive fields from Patient entity/model
            # "diagnosis",
            # "insurance_id",
            # "medical_record_number",
            "insurance_number",
            "medical_history",
            "medications",
            "allergies",
            "treatment_notes",
        ]

        logger.info("SQLAlchemyPatientRepository initialized")

    async def get_by_id(
        self, patient_id: str, user: Optional[Dict[str, Any]] = None
    ) -> Optional[Patient]: # Return domain entity
        """
        Get patient by ID with decryption and access control.

        Args:
            patient_id: Patient ID (UUID as string or UUID object) to retrieve.
            user: User context dict with 'id', 'role', potentially 'patient_ids'.

        Returns:
            Patient domain entity with decrypted fields or None if not found or unauthorized.
        """
        # Check access permissions first
        # Note: _check_access needs the actual patient ID if role is 'patient'
        # Consider fetching the patient first if access depends on patient data itself beyond ID?
        # For now, assume role check is sufficient for initial access decision.
        if not self._check_access(user, patient_id):
            logger.warning(
                f"Access denied for user {user.get('id') if user else 'Unknown'} "
                f"to patient {patient_id} - insufficient permissions."
            )
            return None

        try:
            # Fetch the patient ORM model instance
            stmt = select(PatientModel).where(PatientModel.id == str(patient_id)) # Ensure ID comparison is consistent
            result = await self.db_session.execute(stmt)
            db_patient = result.scalar_one_or_none()

            if not db_patient:
                logger.info(f"Patient with ID {patient_id} not found.")
                return None

            # Convert ORM model to domain entity
            patient_dict = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}

            # Decrypt sensitive fields
            decrypted_patient_dict = self._decrypt_patient_fields(patient_dict.copy()) # Decrypt a copy

            # Log the access (without PHI)
            logger.info(
                f"Patient {patient_id} data accessed by user {user.get('id') if user else 'Unknown'}"
            )

            # Return the domain entity
            return Patient(**decrypted_patient_dict)

        except Exception as e:
            logger.error(f"Error retrieving patient {patient_id}: {str(e)}", exc_info=True)
            # Consider raising a custom repository exception
            return None

    async def get_all(
        self, user: Optional[Dict[str, Any]] = None, skip: int = 0, limit: int = 100
    ) -> List[Patient]: # Return list of domain entities
        """
        Get a list of patients with pagination, decryption, and access control.

        Args:
            user: User context dict. Access is typically restricted (e.g., admin, doctor).
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of Patient domain entities with decrypted fields.
        """
        # Authorization: Check if user role is allowed to list patients
        if not user or user.get("role") not in ["admin", "doctor"]:
             logger.warning(
                 f"User {user.get('id') if user else 'Unknown'} with role {user.get('role', 'None')} "
                 f"attempted to list all patients. Denied."
             )
             # Return empty list or raise PermissionError depending on desired API behavior
             return []
             # raise PermissionError("User not authorized to list all patients.")

        patients_list = []
        try:
            stmt = select(PatientModel).offset(skip).limit(limit).order_by(PatientModel.created_at.desc()) # Example ordering
            # TODO: Add filtering logic if doctors should only see their assigned patients?
            # if user.get("role") == "doctor":
            #     assigned_ids = user.get("patient_ids", [])
            #     if assigned_ids:
            #         stmt = stmt.where(PatientModel.id.in_(assigned_ids))
            #     else:
            #         return [] # Doctor with no assigned patients sees none

            result = await self.db_session.execute(stmt)
            db_patients = result.scalars().all()

            for db_patient in db_patients:
                patient_dict = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}
                decrypted_patient_dict = self._decrypt_patient_fields(patient_dict.copy())
                patients_list.append(Patient(**decrypted_patient_dict))

            logger.info(
                f"{len(patients_list)} patients retrieved by user {user.get('id')} "
                f"(skip={skip}, limit={limit})."
            )
            return patients_list

        except Exception as e:
            logger.error(f"Error retrieving list of patients: {str(e)}", exc_info=True)
            return [] # Return empty list on error

    async def create(self, patient: Patient, user: Optional[Dict[str, Any]] = None) -> Patient:
        """Create or persist a patient entity."""
        # Accept domain entity directly
        self.db_session.add(patient)
        await self.db_session.commit()
        return patient

    async def update(self, patient: Patient) -> Patient:
        """Update an existing patient entity."""
        self.db_session.add(patient)
        await self.db_session.commit()
        return patient

    async def delete(self, patient: Patient) -> None:
        """Delete a patient entity."""
        self.db_session.delete(patient)
        await self.db_session.commit()

    async def get_by_last_name(self, last_name: str) -> List[Patient]:
        """Retrieve patients matching last name in their full name."""
        stmt = select(PatientModel).where(PatientModel.name.ilike(f"%{last_name}"))
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        patients = []
        for db_patient in models:
            data = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}
            patients.append(Patient(**self._decrypt_patient_fields(data)))
        return patients

    def _check_access(self, user: Optional[Dict[str, Any]], patient_id: str) -> bool:
        """
        Check if user has access to patient data based on role and ID.

        Args:
            user: User context dict containing 'id', 'role', and potentially 'patient_ids'.
            patient_id: Patient ID (string) to check access for.

        Returns:
            True if access is allowed, False otherwise.
        """
        if not user:
            logger.debug("_check_access: No user context provided, denying access.")
            return False

        user_id = user.get("id")
        user_role = user.get("role")
        assigned_patient_ids = user.get("patient_ids", []) # Used for doctors

        logger.debug(f"_check_access: Checking access for user {user_id} (role: {user_role}) to patient {patient_id}")

        if user_role == "admin":
            logger.debug(f"_check_access: Granting access for admin user {user_id}.")
            return True

        if user_role == "doctor":
            # Check if this doctor is assigned to this patient (assuming patient_ids are stored in user context)
            # Ensure comparison uses consistent types (e.g., both strings)
            is_assigned = str(patient_id) in [str(pid) for pid in assigned_patient_ids]
            logger.debug(f"_check_access: Doctor {user_id}. Assigned: {is_assigned}. Assigned IDs: {assigned_patient_ids}")
            return is_assigned

        if user_role == "patient":
            # Patients can only access their own data
            # Ensure comparison uses consistent types (e.g., both strings)
            has_access = str(user_id) == str(patient_id)
            logger.debug(f"_check_access: Patient {user_id}. Accessing own data: {has_access}.")
            return has_access

        logger.debug(f"_check_access: Role '{user_role}' has no defined access rules. Denying access.")
        return False

    def _decrypt_patient_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """No-op decryption placeholder."""
        return data

    # Removed internal mock methods like _get_mock_patient, _generate_id as they are replaced by DB logic
    # def _get_mock_patient(self, patient_id: str) -> Optional[Dict[str, Any]]: ...
    # def _generate_id(self) -> str: ...

# Alias for loader imports
PatientRepository = SQLAlchemyPatientRepository

# Example Usage (Illustrative - not for production execution here)
# async def example_repo_usage(db: AsyncSession, enc_service: BaseEncryptionService):
#     repo = SQLAlchemyPatientRepository(db, enc_service)
#     admin_user = {"id": "admin001", "role": "admin"}
#     patient_user = {"id": "patient123", "role": "patient"}

#     # Create
#     new_patient_data = {"first_name": "Jane", "last_name": "Doe", "email": "jane.doe@email.com", "ssn": "111-00-2222"}
#     created = await repo.create(new_patient_data, admin_user)
#     if created:
#         print(f"Created patient: {created.id}")
#         patient_id = created.id

#         # Get by ID
#         fetched = await repo.get_by_id(patient_id, patient_user) # Patient gets own data
#         print(f"Fetched patient: {fetched}")

#         # Update
#         update_info = {"phone": "555-123-4567"}
#         updated = await repo.update(update_info, admin_user)
#         print(f"Updated patient: {updated}")

#         # Get All
#         all_patients = await repo.get_all(admin_user, limit=10)
#         print(f"All patients: {all_patients}")

#         # Delete
#         deleted = await repo.delete(patient_id, admin_user)
#         print(f"Deleted patient: {deleted}")
