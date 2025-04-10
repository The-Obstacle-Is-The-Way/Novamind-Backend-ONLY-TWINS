"""
Patient service for the Novamind Digital Twin platform.

This service implements business logic related to patients, independent
of specific infrastructure concerns like databases or APIs.
"""
from typing import List, Dict, Any, Optional, Protocol, Union
import logging
from datetime import datetime

from app.domain.entities.patient import Patient
from app.domain.exceptions.patient_exceptions import (
    PatientNotFoundError,
    PatientValidationError,
    PatientAlreadyExistsError,
    PatientOperationError
)


class PatientRepositoryProtocol(Protocol):
    """Protocol defining the interface for patient repositories."""
    
    async def get_by_id(self, id: str) -> Optional[Patient]: ...
    async def get_all(self) -> List[Patient]: ...
    async def create(self, patient_data: Dict[str, Any]) -> Patient: ...
    async def update(self, id: str, patient_data: Dict[str, Any]) -> Optional[Patient]: ...
    async def delete(self, id: str) -> bool: ...


class PatientService:
    """
    Service for managing patient data and operations.
    
    This service implements business logic and coordinates between
    the domain model and persistence layer.
    """
    
    def __init__(self, repository: PatientRepositoryProtocol, logger: Optional[logging.Logger] = None):
        """
        Initialize the patient service.
        
        Args:
            repository: Repository for patient data persistence
            logger: Optional logger for service operations
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)
    
    async def get_by_id(self, patient_id: str) -> Patient:
        """
        Get a patient by their ID.
        
        Args:
            patient_id: The unique identifier of the patient
            
        Returns:
            Patient: The patient entity
            
        Raises:
            PatientNotFoundError: If no patient with the ID exists
        """
        patient = await self.repository.get_by_id(patient_id)
        
        if not patient:
            self.logger.warning(f"Patient with ID {patient_id} not found")
            raise PatientNotFoundError(patient_id)
            
        self.logger.info(f"Retrieved patient with ID {patient_id}")
        return patient
    
    async def get_all(self) -> List[Patient]:
        """
        Get all patients.
        
        Returns:
            List[Patient]: List of all patients
        """
        patients = await self.repository.get_all()
        self.logger.info(f"Retrieved {len(patients)} patients")
        return patients
    
    async def create(self, patient_data: Dict[str, Any]) -> Patient:
        """
        Create a new patient.
        
        Args:
            patient_data: Dictionary containing patient data
            
        Returns:
            Patient: The created patient entity
            
        Raises:
            PatientValidationError: If patient data is invalid
            PatientAlreadyExistsError: If a patient with the same ID already exists
        """
        # Ensure required fields
        required_fields = ["id", "name", "date_of_birth", "gender"]
        for field in required_fields:
            if field not in patient_data:
                self.logger.error(f"Missing required field '{field}' in patient data")
                raise PatientValidationError(f"missing required field", field)
        
        # Check if patient already exists
        if patient_data.get("id"):
            existing_patient = await self.repository.get_by_id(patient_data["id"])
            if existing_patient:
                self.logger.warning(f"Patient with ID {patient_data['id']} already exists")
                raise PatientAlreadyExistsError(patient_data["id"])
        
        # Set created and updated timestamps
        now = datetime.now().isoformat()
        if "created_at" not in patient_data:
            patient_data["created_at"] = now
        if "updated_at" not in patient_data:
            patient_data["updated_at"] = now
        
        # Create patient
        try:
            patient = await self.repository.create(patient_data)
            self.logger.info(f"Created patient with ID {patient.id}")
            return patient
        except Exception as e:
            self.logger.error(f"Failed to create patient: {str(e)}")
            raise PatientOperationError("create", str(e))
    
    async def update(self, patient_id: str, patient_data: Dict[str, Any]) -> Patient:
        """
        Update an existing patient.
        
        Args:
            patient_id: The unique identifier of the patient
            patient_data: Dictionary containing updated patient data
            
        Returns:
            Patient: The updated patient entity
            
        Raises:
            PatientNotFoundError: If no patient with the ID exists
            PatientValidationError: If patient data is invalid
        """
        # Check if patient exists
        patient = await self.repository.get_by_id(patient_id)
        if not patient:
            self.logger.warning(f"Patient with ID {patient_id} not found for update")
            raise PatientNotFoundError(patient_id)
        
        # Update timestamp
        patient_data["updated_at"] = datetime.now().isoformat()
        
        # Update patient
        try:
            updated_patient = await self.repository.update(patient_id, patient_data)
            self.logger.info(f"Updated patient with ID {patient_id}")
            return updated_patient
        except Exception as e:
            self.logger.error(f"Failed to update patient with ID {patient_id}: {str(e)}")
            raise PatientOperationError("update", str(e))
    
    async def delete(self, patient_id: str) -> bool:
        """
        Delete a patient.
        
        Args:
            patient_id: The unique identifier of the patient
            
        Returns:
            bool: True if the patient was deleted, False otherwise
            
        Raises:
            PatientNotFoundError: If no patient with the ID exists
        """
        # Check if patient exists
        patient = await self.repository.get_by_id(patient_id)
        if not patient:
            self.logger.warning(f"Patient with ID {patient_id} not found for deletion")
            raise PatientNotFoundError(patient_id)
        
        # Delete patient
        try:
            result = await self.repository.delete(patient_id)
            self.logger.info(f"Deleted patient with ID {patient_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to delete patient with ID {patient_id}: {str(e)}")
            raise PatientOperationError("delete", str(e))
