"""
Digital Twin Repository Interface.
Refactored to remove EHR dependencies and focus on Digital Twin state storage.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from backend.app.domain.entities.refactored.digital_twin_core import DigitalTwinState


class DigitalTwinRepository(ABC):
    """
    Repository interface for Digital Twin state persistence operations.
    Defines the data access contract for the Digital Twin core component.
    """
    
    @abstractmethod
    async def get_by_id(self, state_id: UUID) -> Optional[DigitalTwinState]:
        """
        Retrieve a Digital Twin state by its unique state ID.
        
        Args:
            state_id: Unique identifier for the Digital Twin state
            
        Returns:
            DigitalTwinState if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_latest_for_reference(self, reference_id: UUID) -> Optional[DigitalTwinState]:
        """
        Retrieve the latest Digital Twin state for a reference ID.
        
        Args:
            reference_id: Reference ID associated with the Digital Twin
            
        Returns:
            The most recent DigitalTwinState if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_history_for_reference(
        self,
        reference_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DigitalTwinState]:
        """
        Retrieve historical Digital Twin states for a reference ID.
        
        Args:
            reference_id: Reference ID associated with the Digital Twin
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of states to retrieve
            
        Returns:
            List of DigitalTwinState instances, ordered by timestamp (newest first)
        """
        pass
    
    @abstractmethod
    async def save(self, digital_twin_state: DigitalTwinState) -> DigitalTwinState:
        """
        Save a Digital Twin state.
        
        Args:
            digital_twin_state: DigitalTwinState to persist
            
        Returns:
            The saved DigitalTwinState (with any generated IDs if new)
        """
        pass
    
    @abstractmethod
    async def delete(self, state_id: UUID) -> bool:
        """
        Delete a Digital Twin state.
        
        Args:
            state_id: Unique identifier for the state to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def compare_states(
        self, state_id_1: UUID, state_id_2: UUID
    ) -> Dict:
        """
        Compare two Digital Twin states and return differences.
        
        Args:
            state_id_1: ID of first state to compare
            state_id_2: ID of second state to compare
            
        Returns:
            Dictionary containing the differences between the states
        """
        pass