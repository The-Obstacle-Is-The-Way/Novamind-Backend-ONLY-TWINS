"""
Patient entity in the Novamind Digital Twin platform.

Represents the core domain entity for a patient with all relevant attributes.
This is a pure domain model with no external dependencies.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field


@dataclass
class Patient:
    """
    Patient entity representing a person receiving care.
    
    This class is a pure domain entity with no dependencies on external
    systems or frameworks.
    """
    id: str
    name: str
    date_of_birth: Union[datetime, str]
    gender: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_number: Optional[str] = None
    medical_history: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    treatment_notes: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None
    
    def __post_init__(self):
        """
        Perform post-initialization validation and normalization.
        """
        # Ensure created_at and updated_at are set
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
            
        # Convert string dates to datetime if needed
        if isinstance(self.date_of_birth, str):
            try:
                self.date_of_birth = datetime.fromisoformat(self.date_of_birth.replace('Z', '+00:00'))
            except ValueError:
                # If it's not an ISO format, try common formats
                try:
                    self.date_of_birth = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
                except ValueError:
                    pass  # Keep as string if we can't parse it
                
        if isinstance(self.created_at, str):
            try:
                self.created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except ValueError:
                pass
                
        if isinstance(self.updated_at, str):
            try:
                self.updated_at = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
            except ValueError:
                pass
    
    def add_medical_history_item(self, condition: str) -> None:
        """
        Add a medical condition to the patient's history.
        
        Args:
            condition: The medical condition to add
        """
        if condition and condition not in self.medical_history:
            self.medical_history.append(condition)
            self.updated_at = datetime.now()
    
    def add_medication(self, medication: str) -> None:
        """
        Add a medication to the patient's current medications.
        
        Args:
            medication: The medication to add
        """
        if medication and medication not in self.medications:
            self.medications.append(medication)
            self.updated_at = datetime.now()
    
    def add_allergy(self, allergy: str) -> None:
        """
        Add an allergy to the patient's allergies list.
        
        Args:
            allergy: The allergy to add
        """
        if allergy and allergy not in self.allergies:
            self.allergies.append(allergy)
            self.updated_at = datetime.now()
    
    def add_treatment_note(self, note: Dict[str, Any]) -> None:
        """
        Add a treatment note to the patient's record.
        
        Args:
            note: The treatment note to add, must contain 'date' and 'content' keys
        """
        if note and isinstance(note, dict) and 'content' in note:
            # Ensure note has a date
            if 'date' not in note:
                note['date'] = datetime.now()
                
            self.treatment_notes.append(note)
            self.updated_at = datetime.now()
    
    def update_contact_info(self, email: Optional[str] = None, phone: Optional[str] = None, 
                           address: Optional[str] = None) -> None:
        """
        Update the patient's contact information.
        
        Args:
            email: New email address
            phone: New phone number
            address: New physical address
        """
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address
            
        self.updated_at = datetime.now()
