"""
Repository interface for Patient operations.
Pure domain interface with no infrastructure dependencies.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.patient import Patient


class PatientRepository(ABC):
    """
    Abstract repository interface for Patient operations.
    Concrete implementations will be provided in the infrastructure layer.
    """
    
    @abstractmethod
    async def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        """
        Retrieve a patient by ID.
        
        Args:
            patient_id: The ID of the patient
            
        Returns:
            The patient if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Patient]:
        """
        Retrieve all patients with pagination.
        
        Args:
            limit: Maximum number of patients to retrieve
            offset: Number of patients to skip
            
        Returns:
            List of patients
        """
        pass
    
    @abstractmethod
    async def save(self, patient: Patient) -> Patient:
        """
        Save a patient (create or update).
        
        Args:
            patient: The patient to save
            
        Returns:
            The saved patient with any updates (e.g., generated IDs)
        """
        pass
    
    @abstractmethod
    async def delete(self, patient_id: UUID) -> bool:
        """
        Delete a patient by ID.
        
        Args:
            patient_id: The ID of the patient to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> List[Patient]:
        """
        Find patients by name (partial match).
        
        Args:
            name: The name to search for
            
        Returns:
            List of matching patients
        """
        pass
    
    @abstractmethod
    async def find_by_diagnosis(self, diagnosis_code: str) -> List[Patient]:
        """
        Find patients by diagnosis code.
        
        Args:
            diagnosis_code: The diagnosis code to search for
            
        Returns:
            List of patients with the specified diagnosis
        """
        pass
    
    @abstractmethod
    async def find_by_medication(self, medication_name: str) -> List[Patient]:
        """
        Find patients by medication name.
        
        Args:
            medication_name: The medication name to search for
            
        Returns:
            List of patients with the specified medication
        """
        pass
