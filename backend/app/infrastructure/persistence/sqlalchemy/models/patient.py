"""
SQLAlchemy models for patient data.

This module defines the patient-related SQLAlchemy models.
Encryption/decryption is handled by the repository layer.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast
import json

import sqlalchemy as sa
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.sqlalchemy.database import Base
from app.infrastructure.security.encryption.base_encryption_service import BaseEncryptionService
from app.domain.value_objects.address import Address
from app.domain.value_objects.emergency_contact import EmergencyContact
from app.domain.entities.patient import Patient as DomainPatient


class Patient(Base):
    """
    SQLAlchemy model for patient data.

    Represents the structure of the 'patients' table.
    Encryption/decryption logic is handled externally by the PatientRepository.
    """
    
    __tablename__ = "patients"
    
    # --- Core Identification and Metadata ---
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # external_id could be from an EMR or other system
    external_id = Column(String(64), unique=True, index=True, nullable=True)
    # Foreign key to the associated user account (if applicable)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # --- Encrypted PHI Fields (Stored as Text/Blob in DB) ---
    # Actual database columns storing potentially encrypted data.
    # Naming convention with underscore prefix indicates raw/potentially encrypted storage.
    _first_name = Column("first_name", Text, nullable=True)
    _last_name = Column("last_name", Text, nullable=True)
    # Storing DOB as encrypted text is common for flexibility, though dedicated date types exist.
    # Date of birth stored as encrypted text
    _dob = Column("date_of_birth", Text, nullable=True)
    _email = Column("email", Text, nullable=True)
    _phone = Column("phone", Text, nullable=True)
    # Legacy generic address storage removed in favor of structured address fields
    # _address = Column("address", Text, nullable=True)
    _medical_record_number = Column("medical_record_number", Text, nullable=True)
    # Use Text for potentially long encrypted JSON strings or large text fields
    _ssn = Column("ssn", Text, nullable=True)
    _insurance_number = Column("insurance_number", Text, nullable=True)
    _medical_history = Column("medical_history", Text, nullable=True) # Assumed stored as encrypted JSON list/text
    _medications = Column("medications", Text, nullable=True)       # Assumed stored as encrypted JSON list/text
    _allergies = Column("allergies", Text, nullable=True)           # Assumed stored as encrypted JSON list/text
    _treatment_notes = Column("treatment_notes", Text, nullable=True) # Assumed stored as encrypted JSON list/text
    _gender = Column("gender", Text, nullable=True)                  # Encrypted gender identity/expression


    # --- Other Fields (Potentially Sensitive/Encrypted or Not) ---
    # Example: Encrypted JSON blob for arbitrary additional structured data
    _extra_data = Column("extra_data", Text, nullable=True)
    # Structured address fields
    _address_line1 = Column("address_line1", Text, nullable=True)
    _address_line2 = Column("address_line2", Text, nullable=True)
    _city = Column("city", Text, nullable=True)
    _state = Column("state", Text, nullable=True)
    _postal_code = Column("postal_code", Text, nullable=True)
    _country = Column("country", Text, nullable=True)

    # Emergency contact and insurance information
    _emergency_contact = Column("emergency_contact", Text, nullable=True)
    _insurance_info = Column("insurance_info", JSONB, nullable=True)

    # --- Relationships (Example) ---
    # Assuming a DigitalTwin model exists
    # digital_twin = relationship("DigitalTwin", back_populates="patient", uselist=False)
    biometric_twin_id = Column(UUID(as_uuid=True), nullable=True) # Example FK if needed

    def __repr__(self) -> str:
        # Provide a representation useful for debugging, avoiding PHI exposure
        return f"<Patient(id={self.id}, created_at={self.created_at}, is_active={self.is_active})>"
    
    @classmethod
    def from_domain(cls, patient: DomainPatient) -> "Patient":
        """
        Create a Patient model instance from a domain Patient entity,
        encrypting PHI fields.
        """
        encryption_service = BaseEncryptionService()
        model = cls()
        # Core metadata
        model.id = patient.id
        model.external_id = getattr(patient, "external_id", None)
        model.user_id = patient.created_by
        model.is_active = patient.active
        model.created_at = patient.created_at or model.created_at
        model.updated_at = patient.updated_at or model.updated_at

        # Encrypt PHI fields
        model._first_name = encryption_service.encrypt(patient.first_name) if patient.first_name else None
        model._last_name = encryption_service.encrypt(patient.last_name) if patient.last_name else None
        # Date of birth to ISO string
        dob_value = patient.date_of_birth.isoformat() if patient.date_of_birth else None
        model._dob = encryption_service.encrypt(dob_value) if dob_value else None
        model._email = encryption_service.encrypt(patient.email) if patient.email else None
        model._phone = encryption_service.encrypt(patient.phone) if patient.phone else None

        # Structured address
        if patient.address:
            addr = patient.address
            model._address_line1 = encryption_service.encrypt(addr.street) if getattr(addr, "street", None) else None
            model._address_line2 = encryption_service.encrypt(addr.line2) if getattr(addr, "line2", None) else None
            model._city = encryption_service.encrypt(addr.city) if addr.city else None
            model._state = encryption_service.encrypt(addr.state) if addr.state else None
            model._postal_code = encryption_service.encrypt(addr.zip_code) if addr.zip_code else None
            model._country = encryption_service.encrypt(addr.country) if addr.country else None
        else:
            model._address_line1 = model._address_line2 = model._city = model._state = model._postal_code = model._country = None

        # Emergency contact
        if patient.emergency_contact:
            ec = patient.emergency_contact
            contact_data: Dict[str, Any] = {
                "name": ec.name,
                "relationship": ec.relationship,
                "phone": ec.phone,
            }
            if getattr(ec, "email", None):
                contact_data["email"] = ec.email
            model._emergency_contact = json.dumps(contact_data)
        else:
            model._emergency_contact = None

        # Insurance info (stored as JSONB)
        model._insurance_info = patient.insurance_info
        return model

    def to_domain(self) -> DomainPatient:
        """
        Convert this Patient model instance to a domain Patient entity,
        decrypting PHI fields.
        """
        encryption_service = BaseEncryptionService()
        # Helper for decryption with graceful failure
        def _decrypt(val: Optional[str]) -> Optional[str]:
            try:
                return encryption_service.decrypt(val) if val else None
            except Exception:
                return None

        # Decrypt simple fields
        first_name = _decrypt(self._first_name)
        last_name = _decrypt(self._last_name)
        dob_str = _decrypt(self._dob)
        date_of_birth = dob_str or None
        email = _decrypt(self._email)
        phone = _decrypt(self._phone)

        # Reconstruct Address object
        addr_line1 = _decrypt(getattr(self, '_address_line1', None))
        addr_line2 = _decrypt(getattr(self, '_address_line2', None))
        city = _decrypt(getattr(self, '_city', None))
        state = _decrypt(getattr(self, '_state', None))
        postal_code = _decrypt(getattr(self, '_postal_code', None))
        country = _decrypt(getattr(self, '_country', None))
        address = None
        if addr_line1 or city or state or postal_code or country:
            address = Address(
                line1=addr_line1,
                line2=addr_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
            )

        # Reconstruct EmergencyContact
        ec = None
        if getattr(self, '_emergency_contact', None):
            try:
                data = json.loads(self._emergency_contact)
                ec = EmergencyContact(**data)
            except Exception:
                ec = None

        # Insurance info
        insurance_info = getattr(self, '_insurance_info', None)

        # Build domain Patient
        patient = DomainPatient(
            id=self.id,
            date_of_birth=date_of_birth,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            emergency_contact=ec,
            insurance_info=insurance_info,
            active=self.is_active,
            created_by=self.user_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        return patient

# Example of adding other potentially sensitive fields if needed later:
# Add columns like _ethnicity, _preferred_language, etc. following the pattern above.
