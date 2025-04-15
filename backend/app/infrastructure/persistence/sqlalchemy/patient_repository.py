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


class PatientRepository:
    """
    Repository for secure patient data access with encryption and access controls.

    This repository implements the Repository pattern for patient data with HIPAA-compliant
    security features:
    - Field-level encryption for PHI using an injected encryption service.
    - Role-based access controls via the _check_access method.
    - Uses SQLAlchemy async session for database interactions.
    - Assumes an ORM model 'PatientModel' mapped to the database table.
    """

    def __init__(self, db_session: AsyncSession, encryption_service: BaseEncryptionService): # Corrected type hint
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

        logger.info("PatientRepository initialized")

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
        self, user: Dict[str, Any], skip: int = 0, limit: int = 100
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

    async def create(
        self, patient_data: Dict[str, Any], user: Optional[Dict[str, Any]] = None
    ) -> Optional[Patient]: # Return domain entity
        """
        Create a new patient with encrypted sensitive data.

        Args:
            patient_data: Dict representing patient data (e.g., from PatientCreateSchema).
            user: User context dict.

        Returns:
            Created Patient domain entity or None if unauthorized or error occurs.

        Raises:
            PermissionError: If user is not authorized.
        """
        # Check creation permissions
        if not user or user.get("role") not in ["admin", "doctor"]:
            logger.warning(
                f"Patient creation denied for user {user.get('id') if user else 'Unknown'} "
                f"- unauthorized role: {user.get('role') if user else 'None'}"
            )
            raise PermissionError("Unauthorized to create patient records")

        try:
            # Prepare data for ORM model, generate ID if needed
            creation_data = patient_data.copy()
            if "id" not in creation_data or not creation_data["id"]:
                creation_data["id"] = str(uuid4()) # Ensure ID is string for model if needed

            # Combine first/last name into 'name' if PatientModel expects 'name'
            # Adjust this based on your actual PatientModel definition
            if 'first_name' in creation_data and 'last_name' in creation_data:
                 creation_data['name'] = f"{creation_data['first_name']} {creation_data['last_name']}"
                 # Optionally remove first_name/last_name if not in PatientModel
                 # del creation_data['first_name']
                 # del creation_data['last_name']

            # Encrypt sensitive fields before creating the model instance
            encrypted_data = self._encrypt_patient_fields(creation_data.copy())

            # Filter data to match PatientModel fields
            # This prevents passing extra fields (like first_name/last_name if removed)
            model_field_names = {c.name for c in PatientModel.__table__.columns}
            filtered_encrypted_data = {k: v for k, v in encrypted_data.items() if k in model_field_names}

            # Create ORM model instance
            db_patient = PatientModel(**filtered_encrypted_data)

            # Add to session and commit
            self.db_session.add(db_patient)
            await self.db_session.commit()
            await self.db_session.refresh(db_patient)

            # Log the creation (without PHI)
            logger.info(
                f"Patient {db_patient.id} created by user {user.get('id')}"
            )

            # Convert the created ORM instance back to a dict for decryption
            created_patient_dict = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}

            # Decrypt for return
            decrypted_patient_dict = self._decrypt_patient_fields(created_patient_dict.copy())

            # Return the domain entity
            return Patient(**decrypted_patient_dict)

        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}", exc_info=True)
            await self.db_session.rollback() # Rollback on error
            return None

    async def update(
        self,
        patient_id: str,
        update_data: Dict[str, Any], # Data from PatientUpdateSchema (exclude_unset=True)
        user: Optional[Dict[str, Any]] = None,
    ) -> Optional[Patient]: # Return domain entity
        """
        Update patient data with encryption and access control.

        Args:
            patient_id: Patient ID to update.
            update_data: Dict containing fields to update.
            user: User context dict.

        Returns:
            Updated Patient domain entity or None if not found, unauthorized, or error.

        Raises:
            PermissionError: If user is not authorized.
        """
        # Fetch the existing patient first to apply updates
        stmt = select(PatientModel).where(PatientModel.id == str(patient_id))
        result = await self.db_session.execute(stmt)
        db_patient = result.scalar_one_or_none()

        if not db_patient:
            logger.warning(f"Update failed: Patient with ID {patient_id} not found.")
            return None # Or raise NotFoundError

        # Check update permissions based on fetched patient and user context
        if not self._check_access(user, str(patient_id)): # Pass fetched patient ID
            logger.warning(
                f"Patient update denied for user {user.get('id') if user else 'Unknown'} "
                f"on patient {patient_id} - unauthorized."
            )
            raise PermissionError("Unauthorized to update this patient record")

        try:
            # Prepare data for update - encrypt sensitive fields present in update_data
            update_data_copy = update_data.copy()

             # Handle combined name field if necessary
            if 'first_name' in update_data_copy or 'last_name' in update_data_copy:
                 # Get current names if needed, or rely on provided ones
                 first = update_data_copy.get('first_name', db_patient.first_name if hasattr(db_patient, 'first_name') else '')
                 last = update_data_copy.get('last_name', db_patient.last_name if hasattr(db_patient, 'last_name') else '')
                 update_data_copy['name'] = f"{first} {last}".strip()
                 # Optionally remove first/last if PatientModel only has 'name'
                 # update_data_copy.pop('first_name', None)
                 # update_data_copy.pop('last_name', None)

            encrypted_update_data = self._encrypt_patient_fields(update_data_copy)

            # Update the ORM model instance fields
            updated = False
            for key, value in encrypted_update_data.items():
                if hasattr(db_patient, key) and getattr(db_patient, key) != value:
                    setattr(db_patient, key, value)
                    updated = True

            if not updated:
                 logger.info(f"No changes detected for patient {patient_id}. Update skipped.")
                 # Return current state (decrypted)
                 current_patient_dict = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}
                 decrypted_patient_dict = self._decrypt_patient_fields(current_patient_dict.copy())
                 return Patient(**decrypted_patient_dict)

            # Commit changes
            await self.db_session.commit()
            await self.db_session.refresh(db_patient)

            # Log the update (without PHI)
            logger.info(
                f"Patient {patient_id} updated by user {user.get('id') if user else 'Unknown'}"
            )

            # Convert updated ORM instance back to dict for decryption
            updated_patient_dict = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}

            # Decrypt for return
            decrypted_patient_dict = self._decrypt_patient_fields(updated_patient_dict.copy())

            # Return the domain entity
            return Patient(**decrypted_patient_dict)

        except Exception as e:
            logger.error(f"Error updating patient {patient_id}: {str(e)}", exc_info=True)
            await self.db_session.rollback() # Rollback on error
            return None

    async def delete(self, patient_id: str, user: Dict[str, Any]) -> bool:
        """
        Delete a patient record.

        Args:
            patient_id: The ID of the patient to delete.
            user: User context dict. Authorization typically restricted to admins.

        Returns:
            True if deletion was successful, False otherwise.

        Raises:
            PermissionError: If user is not authorized.
        """
        # Authorization: Check if user role is allowed to delete
        # Typically restricted, e.g., to 'admin'
        if not user or user.get("role") != "admin":
            logger.warning(
                f"Patient deletion denied for user {user.get('id') if user else 'Unknown'} "
                f"on patient {patient_id} - requires admin role."
            )
            raise PermissionError("User not authorized to delete patient records.")

        try:
            # Check if patient exists before attempting delete
            stmt_select = select(PatientModel.id).where(PatientModel.id == str(patient_id))
            result_select = await self.db_session.execute(stmt_select)
            exists = result_select.scalar_one_or_none()

            if not exists:
                 logger.warning(f"Deletion failed: Patient {patient_id} not found.")
                 return False # Indicate patient was not found to delete

            # Perform the deletion using SQLAlchemy Core delete statement
            stmt_delete = sqlalchemy_delete(PatientModel).where(PatientModel.id == str(patient_id))
            result = await self.db_session.execute(stmt_delete)
            await self.db_session.commit()

            # Check if any row was actually deleted
            if result.rowcount == 0:
                # This case might happen in race conditions or if the previous check failed somehow
                logger.warning(f"Attempted to delete patient {patient_id}, but no rows were affected.")
                # Rollback might be appropriate if rowcount is unexpected
                # await self.db_session.rollback() # Optional: depends on desired transaction handling
                return False
            elif result.rowcount > 1:
                 # Should not happen with primary key delete
                 logger.error(f"Unexpected row count ({result.rowcount}) when deleting patient {patient_id}.")
                 # Rollback is strongly recommended here
                 await self.db_session.rollback()
                 return False
            else:
                 logger.info(
                     f"Patient {patient_id} deleted successfully by user {user.get('id')}."
                 )
                 return True

        except Exception as e:
            logger.error(f"Error deleting patient {patient_id}: {str(e)}", exc_info=True)
            await self.db_session.rollback() # Rollback on error
            return False


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

    def _encrypt_patient_fields(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in the patient data dictionary.

        Iterates over self.sensitive_fields and encrypts corresponding values
        using the injected encryption_service. Skips None or empty values.

        Args:
            patient_data: Patient data dictionary.

        Returns:
            Patient data dictionary with sensitive fields encrypted.
        """
        for field in self.sensitive_fields:
            if field in patient_data and patient_data[field] is not None:
                 try:
                     # Ensure data is serializable (e.g., list/dict to JSON string) if needed by encryption service
                     value_to_encrypt = patient_data[field]
                     # Example: Convert list/dict to JSON string before encryption if service expects string
                     # if isinstance(value_to_encrypt, (list, dict)):
                     #     import json
                     #     value_to_encrypt = json.dumps(value_to_encrypt)
                     # elif not isinstance(value_to_encrypt, (str, bytes)): # Ensure it's encryptable type
                     #     value_to_encrypt = str(value_to_encrypt)

                     patient_data[field] = self.encryption_service.encrypt(str(value_to_encrypt)) # Ensure string input?
                 except Exception as e:
                      logger.error(f"Encryption failed for field '{field}' in patient data: {e}", exc_info=True)
                      # Decide error handling: raise, skip, set to None? Skipping for now.
                      pass # Or raise specific EncryptionError
        return patient_data

    def _decrypt_patient_fields(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in the patient data dictionary.

        Iterates over self.sensitive_fields and decrypts corresponding values
        using the injected encryption_service. Skips None or empty values.
        Handles potential decryption errors gracefully.

        Args:
            patient_data: Patient data dictionary with potentially encrypted fields.

        Returns:
            Patient data dictionary with sensitive fields decrypted.
        """
        for field in self.sensitive_fields:
            if field in patient_data and patient_data[field] is not None:
                try:
                    decrypted_value = self.encryption_service.decrypt(patient_data[field])
                    # Example: Convert back from JSON string if needed
                    # if field in ["medical_history", "medications", "allergies", "treatment_notes"]: # Fields stored as JSON
                    #     import json
                    #     try:
                    #         decrypted_value = json.loads(decrypted_value)
                    #     except json.JSONDecodeError:
                    #         logger.warning(f"Could not JSON decode decrypted field '{field}'. Keeping as string.")
                    patient_data[field] = decrypted_value
                except Exception as e:
                    # Log error but don't crash; potentially return None or placeholder
                    logger.error(
                        f"Decryption failed for field '{field}'. Leaving encrypted or setting None. Error: {e}",
                        exc_info=False # Set True for full traceback if needed
                    )
                    # Decide handling: keep encrypted, set None, raise? Setting None might be safest.
                    patient_data[field] = None # Or keep encrypted: pass
        return patient_data

    # Removed internal mock methods like _get_mock_patient, _generate_id as they are replaced by DB logic
    # def _get_mock_patient(self, patient_id: str) -> Optional[Dict[str, Any]]: ...
    # def _generate_id(self) -> str: ...

# Example Usage (Illustrative - not for production execution here)
# async def example_repo_usage(db: AsyncSession, enc_service: BaseEncryptionService):
#     repo = PatientRepository(db, enc_service)
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
#         updated = await repo.update(patient_id, update_info, admin_user)
#         print(f"Updated patient: {updated}")

#         # Get All
#         all_patients = await repo.get_all(admin_user, limit=10)
#         print(f"All patients: {all_patients}")

#         # Delete
#         deleted = await repo.delete(patient_id, admin_user)
#         print(f"Deleted patient: {deleted}")
