"""
Self-contained test for Patient entity.

This module contains both the patient entity implementation and tests in a single file,
making it completely independent of the rest of the application.
"""

import unittest
import pytest
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

# ============= Patient Entity Implementation =============

class Gender(str, Enum):
    """Gender enumeration."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class InsuranceStatus(str, Enum):
    """Insurance status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class PatientStatus(str, Enum):
    """Patient status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ONBOARDING = "onboarding"
    DISCHARGED = "discharged"
    TERMINATED = "terminated"


class EmergencyContact:
    """Emergency contact information."""
    
    def __init__(
        self,
        name: str,
        relationship: str,
        phone: str,
        email: Optional[str] = None
    ):
        self.name = name
        self.relationship = relationship
        self.phone = phone
        self.email = email
        
        # Validation
        if not name or not name.strip():
            raise ValueError("Emergency contact name cannot be empty")
        if not relationship or not relationship.strip():
            raise ValueError("Emergency contact relationship cannot be empty")
        if not phone or not phone.strip():
            raise ValueError("Emergency contact phone cannot be empty")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "relationship": self.relationship,
            "phone": self.phone,
            "email": self.email
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmergencyContact':
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            relationship=data.get("relationship", ""),
            phone=data.get("phone", ""),
            email=data.get("email")
        )


class Patient:
    """Patient entity."""
    
    def __init__(
        self,
        id: str = None,
        first_name: str = None,
        last_name: str = None,
        date_of_birth: Union[str, date] = None,
        gender: Union[str, Gender] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        insurance_id: Optional[str] = None,
        insurance_provider: Optional[str] = None,
        insurance_group: Optional[str] = None,
        insurance_status: Union[str, InsuranceStatus] = InsuranceStatus.UNKNOWN,
        emergency_contacts: Optional[List[EmergencyContact]] = None,
        medical_history: Optional[List[str]] = None,
        medications: Optional[List[Dict[str, Any]]] = None,
        allergies: Optional[List[str]] = None,
        status: Union[str, PatientStatus] = PatientStatus.ONBOARDING,
        notes: Optional[str] = None,
        last_appointment: Optional[str] = None,
        next_appointment: Optional[str] = None,
        preferred_provider_id: Optional[str] = None
    ):
        # Generate ID if not provided
        self.id = id if id else str(uuid4())
        
        # Required fields
        self.first_name = first_name
        self.last_name = last_name
        
        # Convert string date to date object
        if isinstance(date_of_birth, str):
            try:
                date_parts = date_of_birth.split('-')
                self.date_of_birth = date(
                    int(date_parts[0]), 
                    int(date_parts[1]), 
                    int(date_parts[2])
                )
            except (ValueError, IndexError):
                raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        else:
            self.date_of_birth = date_of_birth
            
        # Convert string enums to enum values
        if isinstance(gender, str):
            try:
                self.gender = Gender(gender.lower())
            except ValueError:
                raise ValueError(f"Invalid gender: {gender}")
        else:
            self.gender = gender
            
        # Contact information
        self.email = email
        self.phone = phone
        self.address = address
        
        # Insurance information
        self.insurance_id = insurance_id
        self.insurance_provider = insurance_provider
        self.insurance_group = insurance_group
        
        if isinstance(insurance_status, str):
            try:
                self.insurance_status = InsuranceStatus(insurance_status.lower())
            except ValueError:
                raise ValueError(f"Invalid insurance status: {insurance_status}")
        else:
            self.insurance_status = insurance_status
            
        # Lists of related data
        self.emergency_contacts = emergency_contacts or []
        self.medical_history = medical_history or []
        self.medications = medications or []
        self.allergies = allergies or []
        
        # Status information
        if isinstance(status, str):
            try:
                self.status = PatientStatus(status.lower())
            except ValueError:
                raise ValueError(f"Invalid patient status: {status}")
        else:
            self.status = status
            
        # Additional metadata
        self.notes = notes
        self.last_appointment = last_appointment
        self.next_appointment = next_appointment
        self.preferred_provider_id = preferred_provider_id
        
        # Validate
        self.validate()
        
    def validate(self):
        """Validate the patient data."""
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name is required")
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name is required")
        if not self.date_of_birth:
            raise ValueError("Date of birth is required")
        if not self.gender:
            raise ValueError("Gender is required")
            
        # Validate email format if provided
        if self.email and '@' not in self.email:
            raise ValueError("Invalid email format")
            
        # Validate phone format if provided (simplified)
        if self.phone and not any(c.isdigit() for c in self.phone):
            raise ValueError("Phone number must contain digits")
            
    def update_personal_info(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[Union[str, date]] = None,
        gender: Optional[Union[str, Gender]] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None
    ):
        """Update patient's personal information."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
            
        if date_of_birth is not None:
            if isinstance(date_of_birth, str):
                try:
                    date_parts = date_of_birth.split('-')
                    self.date_of_birth = date(
                        int(date_parts[0]), 
                        int(date_parts[1]), 
                        int(date_parts[2])
                    )
                except (ValueError, IndexError):
                    raise ValueError("Invalid date format. Use YYYY-MM-DD.")
            else:
                self.date_of_birth = date_of_birth
                
        if gender is not None:
            if isinstance(gender, str):
                try:
                    self.gender = Gender(gender.lower())
                except ValueError:
                    raise ValueError(f"Invalid gender: {gender}")
            else:
                self.gender = gender
                
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address
            
        self.validate()
        
    def update_insurance_info(
        self,
        insurance_id: Optional[str] = None,
        insurance_provider: Optional[str] = None,
        insurance_group: Optional[str] = None,
        insurance_status: Optional[Union[str, InsuranceStatus]] = None
    ):
        """Update patient's insurance information."""
        if insurance_id is not None:
            self.insurance_id = insurance_id
        if insurance_provider is not None:
            self.insurance_provider = insurance_provider
        if insurance_group is not None:
            self.insurance_group = insurance_group
            
        if insurance_status is not None:
            if isinstance(insurance_status, str):
                try:
                    self.insurance_status = InsuranceStatus(insurance_status.lower())
                except ValueError:
                    raise ValueError(f"Invalid insurance status: {insurance_status}")
            else:
                self.insurance_status = insurance_status
                
    def add_emergency_contact(
        self,
        name: str,
        relationship: str,
        phone: str,
        email: Optional[str] = None
    ):
        """Add an emergency contact."""
        contact = EmergencyContact(
            name=name,
            relationship=relationship,
            phone=phone,
            email=email
        )
        self.emergency_contacts.append(contact)
        return contact
        
    def remove_emergency_contact(self, index: int):
        """Remove an emergency contact by index."""
        if index < 0 or index >= len(self.emergency_contacts):
            raise IndexError("Emergency contact index out of range")
        return self.emergency_contacts.pop(index)
        
    def add_medical_history_item(self, item: str):
        """Add a medical history item."""
        if not item or not item.strip():
            raise ValueError("Medical history item cannot be empty")
        self.medical_history.append(item)
        
    def add_medication(
        self,
        name: str,
        dosage: str,
        frequency: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        prescribed_by: Optional[str] = None
    ):
        """Add a medication."""
        if not name or not name.strip():
            raise ValueError("Medication name cannot be empty")
        if not dosage or not dosage.strip():
            raise ValueError("Medication dosage cannot be empty")
        if not frequency or not frequency.strip():
            raise ValueError("Medication frequency cannot be empty")
            
        medication = {
            "name": name,
            "dosage": dosage,
            "frequency": frequency,
            "start_date": start_date,
            "end_date": end_date,
            "prescribed_by": prescribed_by
        }
        self.medications.append(medication)
        return medication
        
    def remove_medication(self, index: int):
        """Remove a medication by index."""
        if index < 0 or index >= len(self.medications):
            raise IndexError("Medication index out of range")
        return self.medications.pop(index)
        
    def add_allergy(self, allergy: str):
        """Add an allergy."""
        if not allergy or not allergy.strip():
            raise ValueError("Allergy cannot be empty")
        if allergy not in self.allergies:
            self.allergies.append(allergy)
            
    def remove_allergy(self, allergy: str):
        """Remove an allergy."""
        if allergy in self.allergies:
            self.allergies.remove(allergy)
            return True
        return False
        
    def update_status(self, status: Union[str, PatientStatus]):
        """Update patient status."""
        if isinstance(status, str):
            try:
                self.status = PatientStatus(status.lower())
            except ValueError:
                raise ValueError(f"Invalid patient status: {status}")
        else:
            self.status = status
            
    def update_notes(self, notes: str):
        """Update patient notes."""
        self.notes = notes
        
    def update_appointment_times(
        self,
        last_appointment: Optional[str] = None,
        next_appointment: Optional[str] = None
    ):
        """Update appointment times."""
        if last_appointment is not None:
            self.last_appointment = last_appointment
        if next_appointment is not None:
            self.next_appointment = next_appointment
            
    def set_preferred_provider(self, provider_id: str):
        """Set preferred provider."""
        self.preferred_provider_id = provider_id
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender.value if self.gender else None,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "insurance_id": self.insurance_id,
            "insurance_provider": self.insurance_provider,
            "insurance_group": self.insurance_group,
            "insurance_status": self.insurance_status.value if self.insurance_status else None,
