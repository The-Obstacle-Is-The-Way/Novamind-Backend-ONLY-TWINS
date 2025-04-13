"""
Self-contained test for Patient entity.

This module contains both the patient entity implementation and tests in a single file,
making it completely independent of the rest of the application.
"""

import pytest
import unittest
from datetime import date
from enum import Enum
from typing import Any, List, Optional
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "relationship": self.relationship,
            "phone": self.phone,
            "email": self.email
        }


class Insurance:
    """Insurance information."""

    def __init__(
        self,
        provider: str,
        policy_number: str,
        group_number: Optional[str] = None,
        status: InsuranceStatus = InsuranceStatus.ACTIVE
    ):
        self.provider = provider
        self.policy_number = policy_number
        self.group_number = group_number
        self.status = status

        # Validation
        if not provider or not provider.strip():
            raise ValueError("Insurance provider cannot be empty")
        if not policy_number or not policy_number.strip():
            raise ValueError("Insurance policy number cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "policy_number": self.policy_number,
            "group_number": self.group_number,
            "status": self.status
        }


class Patient:
    """Patient entity."""

    def __init__(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        gender: Gender,
        patient_id: str = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        status: PatientStatus = PatientStatus.ACTIVE
    ):
        self.patient_id = patient_id or str(uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.email = email
        self.phone = phone
        self.address = address
        self.status = status
        self.emergency_contacts: List[EmergencyContact] = []
        self.insurance: Optional[Insurance] = None

        # Validation
        if not first_name or not first_name.strip():
            raise ValueError("First name cannot be empty")
        if not last_name or not last_name.strip():
            raise ValueError("Last name cannot be empty")
        if not date_of_birth:
            raise ValueError("Date of birth cannot be empty")
        if not gender:
            raise ValueError("Gender cannot be empty")

    def add_emergency_contact(
        self,
        name: str,
        relationship: str,
        phone: str,
        email: Optional[str] = None
    ) -> EmergencyContact:
        """Add an emergency contact."""
        contact = EmergencyContact(
            name=name,
            relationship=relationship,
            phone=phone,
            email=email
        )
        self.emergency_contacts.append(contact)
        return contact

    def remove_emergency_contact(self, index: int) -> EmergencyContact:
        """Remove an emergency contact by index."""
        if index < 0 or index >= len(self.emergency_contacts):
            raise IndexError("Emergency contact index out of range")
        return self.emergency_contacts.pop(index)

    def set_insurance(
        self,
        provider: str,
        policy_number: str,
        group_number: Optional[str] = None,
        status: InsuranceStatus = InsuranceStatus.ACTIVE
    ) -> Insurance:
        """Set insurance information."""
        insurance = Insurance(
            provider=provider,
            policy_number=policy_number,
            group_number=group_number,
            status=status
        )
        self.insurance = insurance
        return insurance

    def update_status(self, status: PatientStatus) -> None:
        """Update patient status."""
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "patient_id": self.patient_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth.isoformat(),
            "gender": self.gender,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "status": self.status,
            "emergency_contacts": [c.to_dict() for c in self.emergency_contacts],
            "insurance": self.insurance.to_dict() if self.insurance else None
        }


# ============= Tests for Patient Entity =============

class TestPatient(unittest.TestCase):
    """Tests for the Patient class."""

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
        self.assertEqual(patient.status, PatientStatus.ACTIVE)
        self.assertEqual(len(patient.emergency_contacts), 0)
        self.assertIsNone(patient.insurance)

    def test_create_patient_with_invalid_data(self):
        """Test creating a patient with invalid data."""
        with self.assertRaises(ValueError):
            Patient(
                first_name="",
                last_name="Doe",
                date_of_birth=date(1980, 1, 15),
                gender=Gender.MALE
            )
        
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="",
                date_of_birth=date(1980, 1, 15),
                gender=Gender.MALE
            )
        
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="Doe",
                date_of_birth=None,
                gender=Gender.MALE
            )
        
        with self.assertRaises(ValueError):
            Patient(
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1980, 1, 15),
                gender=None
            )

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

    def test_add_emergency_contact_with_invalid_data(self):
        """Test adding an emergency contact with invalid data."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        with self.assertRaises(ValueError):
            patient.add_emergency_contact(
                name="",
                relationship="Spouse",
                phone="555-123-4567"
            )
        
        with self.assertRaises(ValueError):
            patient.add_emergency_contact(
                name="Jane Doe",
                relationship="",
                phone="555-123-4567"
            )
        
        with self.assertRaises(ValueError):
            patient.add_emergency_contact(
                name="Jane Doe",
                relationship="Spouse",
                phone=""
            )

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

    def test_set_insurance(self):
        """Test setting insurance information."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        insurance = patient.set_insurance(
            provider="Blue Cross",
            policy_number="BC123456789",
            group_number="G987654321",
            status=InsuranceStatus.ACTIVE
        )
        
        self.assertEqual(patient.insurance, insurance)
        self.assertEqual(insurance.provider, "Blue Cross")
        self.assertEqual(insurance.policy_number, "BC123456789")
        self.assertEqual(insurance.group_number, "G987654321")
        self.assertEqual(insurance.status, InsuranceStatus.ACTIVE)

    def test_set_insurance_with_invalid_data(self):
        """Test setting insurance information with invalid data."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        with self.assertRaises(ValueError):
            patient.set_insurance(
                provider="",
                policy_number="BC123456789"
            )
        
        with self.assertRaises(ValueError):
            patient.set_insurance(
                provider="Blue Cross",
                policy_number=""
            )

    def test_update_status(self):
        """Test updating patient status."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE
        )
        
        self.assertEqual(patient.status, PatientStatus.ACTIVE)
        
        patient.update_status(PatientStatus.DISCHARGED)
        self.assertEqual(patient.status, PatientStatus.DISCHARGED)
        
        patient.update_status(PatientStatus.INACTIVE)
        self.assertEqual(patient.status, PatientStatus.INACTIVE)

    def test_to_dict(self):
        """Test converting patient to dictionary."""
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender=Gender.MALE,
            email="john.doe@example.com",
            phone="555-123-4567",
            address="123 Main St, Anytown, USA"
        )
        
        patient.add_emergency_contact(
            name="Jane Doe",
            relationship="Spouse",
            phone="555-123-4567",
            email="jane.doe@example.com"
        )
        
        patient.set_insurance(
            provider="Blue Cross",
            policy_number="BC123456789",
            group_number="G987654321"
        )
        
        data = patient.to_dict()
        
        self.assertEqual(data["first_name"], "John")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["date_of_birth"], "1980-01-15")
        self.assertEqual(data["gender"], Gender.MALE)
        self.assertEqual(data["email"], "john.doe@example.com")
        self.assertEqual(data["phone"], "555-123-4567")
        self.assertEqual(data["address"], "123 Main St, Anytown, USA")
        self.assertEqual(data["status"], PatientStatus.ACTIVE)
        self.assertEqual(len(data["emergency_contacts"]), 1)
        self.assertEqual(data["emergency_contacts"][0]["name"], "Jane Doe")
        self.assertEqual(data["insurance"]["provider"], "Blue Cross")


# Run the tests if this file is executed directly
if __name__ == "__main__":
    unittest.main()