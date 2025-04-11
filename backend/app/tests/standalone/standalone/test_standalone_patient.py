import pytest
"""
Self-contained test for Patient entity.

This module contains both the patient entity implementation and tests in a single file,
making it completely independent of the rest of the application.
"""

import unittest
from datetime import date
from enum import Enum
from typing import Any
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
        email: str | None = None
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
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "relationship": self.relationship,
            "phone": self.phone,
            "email": self.email
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'EmergencyContact':
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
        date_of_birth: str | date = None,
        gender: str | Gender = None,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        insurance_id: str | None = None,
        insurance_provider: str | None = None,
        insurance_group: str | None = None,
        insurance_status: str | InsuranceStatus = InsuranceStatus.UNKNOWN,
        emergency_contacts: list[EmergencyContact] | None = None,
        medical_history: list[str] | None = None,
        medications: list[dict[str, Any]] | None = None,
        allergies: list[str] | None = None,
        status: str | PatientStatus = PatientStatus.ONBOARDING,
        notes: str | None = None,
        last_appointment: str | None = None,
        next_appointment: str | None = None,
        preferred_provider_id: str | None = None
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
        first_name: str | None = None,
        last_name: str | None = None,
        date_of_birth: str | date | None = None,
        gender: str | Gender | None = None,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None
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
        insurance_id: str | None = None,
        insurance_provider: str | None = None,
        insurance_group: str | None = None,
        insurance_status: str | InsuranceStatus | None = None
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
        email: str | None = None
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
        start_date: str | None = None,
        end_date: str | None = None,
        prescribed_by: str | None = None
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
        
    def update_status(self, status: str | PatientStatus):
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
        last_appointment: str | None = None,
        next_appointment: str | None = None
    ):
        """Update appointment times."""
        if last_appointment is not None:
            self.last_appointment = last_appointment
        if next_appointment is not None:
            self.next_appointment = next_appointment
            
    def set_preferred_provider(self, provider_id: str):
        """Set preferred provider."""
        self.preferred_provider_id = provider_id
        
    def to_dict(self) -> dict[str, Any]:
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
            "emergency_contacts": [contact.to_dict() for contact in self.emergency_contacts],
            "medical_history": self.medical_history,
            "medications": self.medications,
            "allergies": self.allergies,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
            "last_appointment": self.last_appointment,
            "next_appointment": self.next_appointment,
            "preferred_provider_id": self.preferred_provider_id
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Patient':
        """Create from dictionary."""
        # Handle emergency contacts
        emergency_contacts = []
        for contact_data in data.get("emergency_contacts", []):
            emergency_contacts.append(EmergencyContact.from_dict(contact_data))
            
        return cls(
            id=data.get("id"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            date_of_birth=data.get("date_of_birth"),
            gender=data.get("gender"),
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            insurance_id=data.get("insurance_id"),
            insurance_provider=data.get("insurance_provider"),
            insurance_group=data.get("insurance_group"),
            insurance_status=data.get("insurance_status"),
            emergency_contacts=emergency_contacts,
            medical_history=data.get("medical_history", []),
            medications=data.get("medications", []),
            allergies=data.get("allergies", []),
            status=data.get("status"),
            notes=data.get("notes"),
            last_appointment=data.get("last_appointment"),
            next_appointment=data.get("next_appointment"),
            preferred_provider_id=data.get("preferred_provider_id")
        )
        
    def __eq__(self, other):
        """Equality comparison."""
        if not isinstance(other, Patient):
            return False
        return self.id == other.id
        
    def __ne__(self, other):
        """Inequality comparison."""
        return not self.__eq__(other)
        
    def __str__(self):
        """String representation."""
        return f"Patient({self.id}: {self.first_name} {self.last_name})"


# ============= Patient Entity Tests =============

class TestPatient(unittest.TestCase):
    """Tests for the Patient class."""
    
    @pytest.mark.standalone
    def test_create_patient(self):
        """Test creating a patient."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE,
            email="john.doe@example.com",
            phone="555-123-4567",
            address="123 Main St, Anytown, USA"
        )
        
        self.assertEqual(patient.first_name, "John")
        self.assertEqual(patient.last_name, "Doe")
        self.assertEqual(patient.date_of_birth, date(1980, 1, 15))
        self.assertEqual(patient.gender, Gender.MALE)
        self.assertEqual(patient.email, "john.doe@example.com")
        self.assertEqual(patient.phone, "555-123-4567")
        self.assertEqual(patient.address, "123 Main St, Anytown, USA")
        self.assertEqual(patient.status, PatientStatus.ONBOARDING)
        
    @pytest.mark.standalone
    def test_create_patient_with_string_enums(self):
        """Test creating a patient with string enums."""
        patient = Patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1985, 5, 20),
            gender="female",
            status="active",
            insurance_status="active"
        )
        
        self.assertEqual(patient.gender, Gender.FEMALE)
        self.assertEqual(patient.status, PatientStatus.ACTIVE)
        self.assertEqual(patient.insurance_status, InsuranceStatus.ACTIVE)
        
    @pytest.mark.standalone
    def test_create_patient_with_string_date(self):
        """Test creating a patient with a string date."""
        patient = Patient(
            first_name="Alice",
            last_name="Smith",
            date_of_birth="1990-10-25",
            gender=Gender.FEMALE
        )
        
        self.assertEqual(patient.date_of_birth, date(1990, 10, 25))
        
    @pytest.mark.standalone
    def test_create_patient_with_auto_id(self):
        """Test creating a patient with auto-generated ID."""
        patient = Patient(
            first_name="Bob",
            last_name="Johnson",
            date_of_birth=date(1975, 3, 12),
            gender=Gender.MALE
        )
        
        self.assertIsNotNone(patient.id)
        self.assertIsInstance(patient.id, str)
        self.assertTrue(len(patient.id) > 0)
        
    @pytest.mark.standalone
    def test_validate_required_fields(self):
        """Test validation of required fields."""
        # Missing first name
        with self.assertRaises(ValueError):
            Patient(
                first_name="",
                last_name="Doe",
                date_of_birth=date(1980, 1, 15),
                gender=Gender.MALE
            )
            
        # Missing last name
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="",
                date_of_birth=date(1980, 1, 15),
                gender=Gender.MALE
            )
            
        # Missing date of birth
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="Doe",
                date_of_birth=None,
                gender=Gender.MALE
            )
            
        # Missing gender
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1980, 1, 15),
                gender=None
            )
            
    @pytest.mark.standalone
    def test_validate_email_format(self):
        """Test validation of email format."""
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1980, 1, 15),
                gender=Gender.MALE,
                email="invalid-email"
            )
            
    @pytest.mark.standalone
    def test_validate_phone_format(self):
        """Test validation of phone format."""
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1980, 1, 15),
                gender=Gender.MALE,
                phone="invalid-phone-no-digits"
            )
            
    @pytest.mark.standalone
    def test_update_personal_info(self):
        """Test updating personal information."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        patient.update_personal_info(
            first_name="Johnny",
            last_name="Smith",
            date_of_birth=date(1981, 2, 16),
            gender=Gender.OTHER,
            email="johnny.smith@example.com",
            phone="555-987-6543",
            address="456 Oak St, Newtown, USA"
        )
        
        self.assertEqual(patient.first_name, "Johnny")
        self.assertEqual(patient.last_name, "Smith")
        self.assertEqual(patient.date_of_birth, date(1981, 2, 16))
        self.assertEqual(patient.gender, Gender.OTHER)
        self.assertEqual(patient.email, "johnny.smith@example.com")
        self.assertEqual(patient.phone, "555-987-6543")
        self.assertEqual(patient.address, "456 Oak St, Newtown, USA")
        
    @pytest.mark.standalone
    def test_update_personal_info_with_string_date(self):
        """Test updating personal information with a string date."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        patient.update_personal_info(date_of_birth="1981-02-16")
        
        self.assertEqual(patient.date_of_birth, date(1981, 2, 16))
        
    @pytest.mark.standalone
    def test_update_personal_info_with_string_gender(self):
        """Test updating personal information with a string gender."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        patient.update_personal_info(gender="non_binary")
        
        self.assertEqual(patient.gender, Gender.NON_BINARY)
        
    @pytest.mark.standalone
    def test_update_insurance_info(self):
        """Test updating insurance information."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        patient.update_insurance_info(
            insurance_id="INS123456",
            insurance_provider="HealthCo",
            insurance_group="GROUP789",
            insurance_status=InsuranceStatus.ACTIVE
        )
        
        self.assertEqual(patient.insurance_id, "INS123456")
        self.assertEqual(patient.insurance_provider, "HealthCo")
        self.assertEqual(patient.insurance_group, "GROUP789")
        self.assertEqual(patient.insurance_status, InsuranceStatus.ACTIVE)
        
    @pytest.mark.standalone
    def test_update_insurance_info_with_string_status(self):
        """Test updating insurance information with a string status."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        patient.update_insurance_info(insurance_status="pending")
        
        self.assertEqual(patient.insurance_status, InsuranceStatus.PENDING)
        
    @pytest.mark.standalone
    def test_add_emergency_contact(self):
        """Test adding an emergency contact."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        contact = patient.add_emergency_contact(
            name="Jane Doe",
            relationship="Spouse",
            phone="555-123-4567",
            email="jane.doe@example.com"
        )
        
        self.assertEqual(len(patient.emergency_contacts), 1)
        self.assertEqual(patient.emergency_contacts[0], contact)
        self.assertEqual(contact.name, "Jane Doe")
        self.assertEqual(contact.relationship, "Spouse")
        self.assertEqual(contact.phone, "555-123-4567")
        self.assertEqual(contact.email, "jane.doe@example.com")
        
    @pytest.mark.standalone
    def test_add_emergency_contact_validation(self):
        """Test validation when adding an emergency contact."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        # Missing name
        with self.assertRaises(ValueError):
            patient.add_emergency_contact(
                name="",
                relationship="Spouse",
                phone="555-123-4567"
            )
            
        # Missing relationship
        with self.assertRaises(ValueError):
            patient.add_emergency_contact(
                name="Jane Doe",
                relationship="",
                phone="555-123-4567"
            )
            
        # Missing phone
        with self.assertRaises(ValueError):
            patient.add_emergency_contact(
                name="Jane Doe",
                relationship="Spouse",
                phone=""
            )
            
    @pytest.mark.standalone
    def test_remove_emergency_contact(self):
        """Test removing an emergency contact."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        contact1 = patient.add_emergency_contact(
            name="Jane Doe",
            relationship="Spouse",
            phone="555-123-4567"
        )
        
        contact2 = patient.add_emergency_contact(
            name="Bob Doe",
            relationship="Brother",
            phone="555-987-6543"
        )
        
        self.assertEqual(len(patient.emergency_contacts), 2)
        
        removed = patient.remove_emergency_contact(0)
        
        self.assertEqual(len(patient.emergency_contacts), 1)
        self.assertEqual(removed, contact1)
        self.assertEqual(patient.emergency_contacts[0], contact2)
        
    @pytest.mark.standalone
    def test_remove_emergency_contact_invalid_index(self):
        """Test removing an emergency contact with an invalid index."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        patient.add_emergency_contact(
            name="Jane Doe",
            relationship="Spouse",
            phone="555-123-4567"
        )
        
        with self.assertRaises(IndexError):
            patient.remove_emergency_contact(1)