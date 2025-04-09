"""
In-memory implementation of SubjectIdentityRepository.

This module provides a simple in-memory implementation of the
SubjectIdentityRepository interface, suitable for development,
testing, and as a reference implementation.
"""
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.entities.identity.subject_identity import SubjectIdentity, SubjectIdentityRepository


class InMemorySubjectIdentityRepository(SubjectIdentityRepository):
    """
    In-memory implementation of the SubjectIdentityRepository interface.
    
    This class stores subject identities in memory, making it suitable for
    development and testing environments. It's not intended for production use
    as it doesn't persist data between application restarts.
    """
    
    def __init__(self):
        """Initialize an empty repository."""
        self._identities: Dict[UUID, SubjectIdentity] = {}
        self._external_refs: Dict[str, Dict[str, UUID]] = {}
    
    async def save(self, identity: SubjectIdentity) -> UUID:
        """
        Save a subject identity to the repository.
        
        Args:
            identity: The identity to save
            
        Returns:
            The identity's UUID
        """
        # Store the identity
        self._identities[identity.subject_id] = identity
        
        # Index external references
        for system, identifier in identity.external_references.items():
            if system not in self._external_refs:
                self._external_refs[system] = {}
            
            # Create index entry for this external reference
            self._external_refs[system][identifier] = identity.subject_id
        
        return identity.subject_id
    
    async def get_by_id(self, subject_id: UUID) -> Optional[SubjectIdentity]:
        """
        Retrieve an identity by its ID.
        
        Args:
            subject_id: UUID of the identity
            
        Returns:
            Subject identity if found, None otherwise
        """
        return self._identities.get(subject_id)
    
    async def get_by_external_reference(self, system: str, identifier: str) -> Optional[SubjectIdentity]:
        """
        Retrieve an identity by external reference.
        
        Args:
            system: External system name
            identifier: External identifier
            
        Returns:
            Subject identity if found, None otherwise
        """
        # Check if we have this system
        if system not in self._external_refs:
            return None
        
        # Check if we have this identifier in this system
        if identifier not in self._external_refs[system]:
            return None
        
        # Get the subject ID
        subject_id = self._external_refs[system][identifier]
        
        # Return the identity
        return self._identities.get(subject_id)
    
    async def list_by_identity_type(self, identity_type: str) -> List[SubjectIdentity]:
        """
        List all identities of a specific type.
        
        Args:
            identity_type: Type of identities to list
            
        Returns:
            List of subject identities
        """
        return [
            identity for identity in self._identities.values()
            if identity.identity_type == identity_type
        ]
    
    async def delete(self, subject_id: UUID) -> bool:
        """
        Delete a subject identity.
        
        Args:
            subject_id: UUID of the identity to delete
            
        Returns:
            True if deletion was successful
        """
        # Check if identity exists
        if subject_id not in self._identities:
            return False
        
        # Get the identity
        identity = self._identities[subject_id]
        
        # Remove external references
        for system, identifier in identity.external_references.items():
            if system in self._external_refs and identifier in self._external_refs[system]:
                del self._external_refs[system][identifier]
        
        # Remove the identity
        del self._identities[subject_id]
        
        return True
        
    def clear(self) -> None:
        """
        Clear all data from the repository.
        
        This method is primarily used for testing.
        """
        self._identities.clear()
        self._external_refs.clear()