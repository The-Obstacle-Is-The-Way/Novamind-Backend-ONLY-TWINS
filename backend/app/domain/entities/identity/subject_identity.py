"""
Abstract Subject Identity Module for Digital Twin.

This module defines a generalized identity abstraction that separates
Digital Twin functionality from direct EHR/patient record dependencies,
while maintaining compliance with security and privacy requirements.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional, Any, List
from uuid import UUID, uuid4


class SubjectIdentity:
    """
    Subject Identity representation that abstracts patient details.
    
    This entity allows Digital Twin functionality to operate without direct
    dependency on patient records while maintaining security and audit capabilities.
    It serves as a bridge between Digital Twin functionality and potential 
    downstream EHR integration.
    """
    
    def __init__(
        self,
        subject_id: UUID,
        identity_type: str = "research_subject",
        metadata: Optional[Dict[str, Any]] = None,
        creation_date: Optional[datetime] = None,
        last_updated: Optional[datetime] = None,
        attributes: Optional[Dict[str, Any]] = None,
        external_references: Optional[Dict[str, str]] = None
    ):
        """
        Initialize a new subject identity.
        
        Args:
            subject_id: Unique identifier for the subject
            identity_type: Type of identity ("research_subject", "patient", etc.)
            metadata: Optional metadata about this identity
            creation_date: When this identity was created
            last_updated: When this identity was last updated
            attributes: Subject attributes relevant to Digital Twin functionality
            external_references: Mappings to external system identifiers
        """
        self.subject_id = subject_id
        self.identity_type = identity_type
        self.metadata = metadata or {}
        self.creation_date = creation_date or datetime.utcnow()
        self.last_updated = last_updated or datetime.utcnow()
        self.attributes = attributes or {}
        self.external_references = external_references or {}
    
    @classmethod
    def create_new(cls, 
                  identity_type: str = "research_subject", 
                  attributes: Optional[Dict[str, Any]] = None,
                  external_references: Optional[Dict[str, str]] = None) -> "SubjectIdentity":
        """
        Create a new subject identity with a generated UUID.
        
        Args:
            identity_type: Type of identity
            attributes: Optional attributes for the subject
            external_references: Optional mappings to external systems
            
        Returns:
            New SubjectIdentity instance
        """
        return cls(
            subject_id=uuid4(),
            identity_type=identity_type,
            attributes=attributes,
            external_references=external_references
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
    
    def add_external_reference(self, system: str, identifier: str) -> None:
        """
        Add a reference to an external system identifier.
        
        Args:
            system: Name of the external system
            identifier: Identifier in that system
        """
        self.external_references[system] = identifier
        self.last_updated = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert identity to dictionary representation.
        
        Returns:
            Dictionary representation of identity
        """
        return {
            "subject_id": str(self.subject_id),
            "identity_type": self.identity_type,
            "creation_date": self.creation_date.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "attributes": self.attributes,
            "external_references": self.external_references,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubjectIdentity":
        """
        Create identity from dictionary representation.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Reconstructed SubjectIdentity instance
        """
        return cls(
            subject_id=UUID(data["subject_id"]),
            identity_type=data.get("identity_type", "research_subject"),
            creation_date=datetime.fromisoformat(data["creation_date"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            attributes=data.get("attributes", {}),
            external_references=data.get("external_references", {}),
            metadata=data.get("metadata", {})
        )


class SubjectIdentityRepository(ABC):
    """
    Repository interface for subject identity persistence.
    
    This abstract class defines the contract for storing and retrieving
    subject identities independent of the underlying storage mechanism.
    """
    
    @abstractmethod
    async def save(self, identity: SubjectIdentity) -> UUID:
        """
        Save a subject identity.
        
        Args:
            identity: The identity to save
            
        Returns:
            The identity's UUID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, subject_id: UUID) -> Optional[SubjectIdentity]:
        """
        Retrieve an identity by its ID.
        
        Args:
            subject_id: UUID of the identity
            
        Returns:
            Subject identity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_external_reference(self, system: str, identifier: str) -> Optional[SubjectIdentity]:
        """
        Retrieve an identity by external reference.
        
        Args:
            system: External system name
            identifier: External identifier
            
        Returns:
            Subject identity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_by_identity_type(self, identity_type: str) -> List[SubjectIdentity]:
        """
        List all identities of a specific type.
        
        Args:
            identity_type: Type of identities to list
            
        Returns:
            List of subject identities
        """
        pass
    
    @abstractmethod
    async def delete(self, subject_id: UUID) -> bool:
        """
        Delete a subject identity.
        
        Args:
            subject_id: UUID of the identity to delete
            
        Returns:
            True if deletion was successful
        """
        pass


class PatientSubjectAdapter:
    """
    Adapter that maps between patient records and subject identities.
    
    This adapter enables Digital Twin functionality to work with legacy
    patient-centric code while maintaining the new abstraction barriers.
    """
    
    def __init__(self, subject_repository: SubjectIdentityRepository):
        """
        Initialize the adapter.
        
        Args:
            subject_repository: Repository for subject identity access
        """
        self._repository = subject_repository
    
    async def get_or_create_for_patient(self, patient_id: UUID) -> SubjectIdentity:
        """
        Get or create a subject identity for a patient.
        
        Args:
            patient_id: UUID of the patient
            
        Returns:
            Subject identity linked to the patient
        """
        # Try to find existing mapping
        identity = await self._repository.get_by_external_reference("patient", str(patient_id))
        
        if identity:
            return identity
        
        # Create new identity linked to patient
        identity = SubjectIdentity.create_new(
            identity_type="patient_subject",
            external_references={"patient": str(patient_id)}
        )
        
        # Save identity
        await self._repository.save(identity)
        
        return identity
    
    async def get_patient_id(self, subject_id: UUID) -> Optional[UUID]:
        """
        Get patient ID for a subject identity.
        
        Args:
            subject_id: UUID of the subject identity
            
        Returns:
            Patient UUID if found, None otherwise
        """
        identity = await self._repository.get_by_id(subject_id)
        
        if not identity:
            return None
        
        patient_ref = identity.external_references.get("patient")
        if not patient_ref:
            return None
        
        return UUID(patient_ref)