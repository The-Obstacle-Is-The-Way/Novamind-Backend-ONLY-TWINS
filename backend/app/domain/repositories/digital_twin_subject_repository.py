"""
Repository interface for Digital Twin Subject operations.

This module defines the abstract interface for persisting and retrieving
Digital Twin Subject entities, following the repository pattern.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.domain.entities.digital_twin.digital_twin_subject import DigitalTwinSubject


class DigitalTwinSubjectRepository(ABC):
    """
    Repository interface for Digital Twin Subject persistence.
    
    This abstract class defines the contract for storing and retrieving
    DigitalTwinSubject entities, independent of the storage mechanism.
    """
    
    @abstractmethod
    async def save(self, subject: DigitalTwinSubject) -> UUID:
        """
        Save a Digital Twin Subject.
        
        Args:
            subject: The subject entity to save
            
        Returns:
            The subject's UUID
            
        Raises:
            RepositoryError: If the save operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, subject_id: UUID) -> Optional[DigitalTwinSubject]:
        """
        Retrieve a subject by its ID.
        
        Args:
            subject_id: UUID of the subject
            
        Returns:
            DigitalTwinSubject if found, None otherwise
            
        Raises:
            RepositoryError: If the retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def list_by_attribute(self, attribute_name: str, value: Any) -> List[DigitalTwinSubject]:
        """
        Get all subjects with a specific attribute value.
        
        Args:
            attribute_name: Name of the attribute to filter by
            value: Value to match
            
        Returns:
            List of matching DigitalTwinSubject entities
            
        Raises:
            RepositoryError: If the query operation fails
        """
        pass
    
    @abstractmethod
    async def list_by_twin_id(self, twin_id: UUID) -> List[DigitalTwinSubject]:
        """
        Get all subjects associated with a specific Digital Twin.
        
        Args:
            twin_id: UUID of the Digital Twin
            
        Returns:
            List of associated DigitalTwinSubject entities
            
        Raises:
            RepositoryError: If the query operation fails
        """
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[DigitalTwinSubject]:
        """
        Get all subjects with pagination.
        
        Args:
            limit: Maximum number of subjects to return
            offset: Number of subjects to skip
            
        Returns:
            List of DigitalTwinSubject entities
            
        Raises:
            RepositoryError: If the query operation fails
        """
        pass
    
    @abstractmethod
    async def update(self, subject: DigitalTwinSubject) -> bool:
        """
        Update an existing Digital Twin Subject.
        
        Args:
            subject: The updated subject entity
            
        Returns:
            True if update was successful, False otherwise
            
        Raises:
            RepositoryError: If the update operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, subject_id: UUID) -> bool:
        """
        Delete a Digital Twin Subject.
        
        Args:
            subject_id: UUID of the subject to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If the delete operation fails
        """
        pass
    
    @abstractmethod
    async def exists(self, subject_id: UUID) -> bool:
        """
        Check if a subject with the given ID exists.
        
        Args:
            subject_id: UUID to check
            
        Returns:
            True if subject exists, False otherwise
            
        Raises:
            RepositoryError: If the query operation fails
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Get the total number of subjects in the repository.
        
        Returns:
            Total number of subjects
            
        Raises:
            RepositoryError: If the count operation fails
        """
        pass