"""
Repository interface for Digital Twin operations.
Pure domain interface with no infrastructure dependencies.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.digital_twin import DigitalTwinState


class DigitalTwinRepository(ABC):
    """
    Abstract repository interface for Digital Twin state operations.
    Concrete implementations will be provided in the infrastructure layer.
    """
    
    @abstractmethod
    async def get_by_id(self, digital_twin_id: UUID) -> DigitalTwinState | None:
        """
        Retrieve a Digital Twin state by its ID.
        
        Args:
            digital_twin_id: The ID of the Digital Twin state
            
        Returns:
            The Digital Twin state if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_latest_for_patient(self, patient_id: UUID) -> DigitalTwinState | None:
        """
        Retrieve the latest Digital Twin state for a patient.
        
        Args:
            patient_id: The ID of the patient
            
        Returns:
            The latest Digital Twin state if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_history_for_patient(
        self, 
        patient_id: UUID, 
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[DigitalTwinState]:
        """
        Retrieve historical Digital Twin states for a patient.
        
        Args:
            patient_id: The ID of the patient
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of records to return
            
        Returns:
            List of Digital Twin states ordered by timestamp (newest first)
        """
        pass
    
    @abstractmethod
    async def save(self, digital_twin_state: DigitalTwinState) -> DigitalTwinState:
        """
        Save a Digital Twin state.
        
        Args:
            digital_twin_state: The Digital Twin state to save
            
        Returns:
            The saved Digital Twin state with any updates (e.g., generated IDs)
        """
        pass
    
    @abstractmethod
    async def find_by_clinical_significance(
        self,
        significance_level: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[tuple[UUID, DigitalTwinState]]:
        """
        Find Digital Twin states with specified clinical significance.
        
        Args:
            significance_level: The clinical significance level to search for
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of records to return
            
        Returns:
            List of tuples containing patient ID and Digital Twin state
        """
        pass
