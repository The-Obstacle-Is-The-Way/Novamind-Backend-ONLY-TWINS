"""
Digital Twin Subject Entity Module.

This module defines the core subject entity for the Digital Twin system,
representing an individual whose psychiatric and neurotransmitter state
is being modeled by the system.
"""
from datetime import datetime
from typing import Dict, Optional, Any, List, Set
from uuid import UUID, uuid4


class DigitalTwinSubject:
    """
    Digital Twin Subject entity representing an individual in the Digital Twin system.
    
    This is the core domain entity that serves as the foundation for Digital Twin models.
    It maintains the essential identity attributes while supporting the requirements
    of the Digital Twin architecture.
    """
    
    def __init__(
        self,
        subject_id: UUID,
        creation_date: datetime,
        last_updated: datetime,
        attributes: Dict[str, Any],
        twin_ids: Optional[Set[UUID]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new Digital Twin Subject.
        
        Args:
            subject_id: Unique identifier for the subject
            creation_date: When this subject was first created
            last_updated: When this subject was last updated
            attributes: Subject attributes relevant to Digital Twin modeling
            twin_ids: Set of Digital Twin UUIDs associated with this subject
            metadata: Optional metadata about this subject
        """
        self.subject_id = subject_id
        self.creation_date = creation_date
        self.last_updated = last_updated
        self.attributes = attributes
        self.twin_ids = twin_ids or set()
        self.metadata = metadata or {}
    
    @classmethod
    def create_new(cls, 
                  attributes: Dict[str, Any],
                  metadata: Optional[Dict[str, Any]] = None) -> "DigitalTwinSubject":
        """
        Create a new Digital Twin Subject with a generated UUID.
        
        Args:
            attributes: Attributes for the subject (age, sex, baseline factors, etc.)
            metadata: Optional metadata about this subject
            
        Returns:
            New DigitalTwinSubject instance
        """
        now = datetime.utcnow()
        return cls(
            subject_id=uuid4(),
            creation_date=now,
            last_updated=now,
            attributes=attributes,
            metadata=metadata
        )
    
    def update_attribute(self, key: str, value: Any) -> None:
        """
        Update a single attribute for this subject.
        
        Args:
            key: Attribute name
            value: Attribute value
        """
        self.attributes[key] = value
        self.last_updated = datetime.utcnow()
    
    def add_twin_id(self, twin_id: UUID) -> None:
        """
        Associate a Digital Twin with this subject.
        
        Args:
            twin_id: UUID of the Digital Twin
        """
        self.twin_ids.add(twin_id)
        self.last_updated = datetime.utcnow()
    
    def remove_twin_id(self, twin_id: UUID) -> bool:
        """
        Remove a Digital Twin association from this subject.
        
        Args:
            twin_id: UUID of the Digital Twin to remove
            
        Returns:
            True if the twin ID was removed, False if it wasn't found
        """
        if twin_id in self.twin_ids:
            self.twin_ids.remove(twin_id)
            self.last_updated = datetime.utcnow()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert subject to dictionary representation.
        
        Returns:
            Dictionary representation of subject
        """
        return {
            "subject_id": str(self.subject_id),
            "creation_date": self.creation_date.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "attributes": self.attributes,
            "twin_ids": [str(twin_id) for twin_id in self.twin_ids],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DigitalTwinSubject":
        """
        Create subject from dictionary representation.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Reconstructed DigitalTwinSubject instance
        """
        twin_ids = {UUID(twin_id) for twin_id in data.get("twin_ids", [])}
        
        return cls(
            subject_id=UUID(data["subject_id"]),
            creation_date=datetime.fromisoformat(data["creation_date"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            attributes=data.get("attributes", {}),
            twin_ids=twin_ids,
            metadata=data.get("metadata", {})
        )