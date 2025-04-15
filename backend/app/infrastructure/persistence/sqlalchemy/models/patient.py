"""
SQLAlchemy models for patient data.

This module defines the patient-related SQLAlchemy models.
Encryption/decryption is handled by the repository layer.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

import sqlalchemy as sa
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.sqlalchemy.database import Base


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
    _dob = Column("dob", Text, nullable=True)
    _email = Column("email", Text, nullable=True)
    _phone = Column("phone", Text, nullable=True)
    _address = Column("address", Text, nullable=True) # Could be JSONB if structured address needed
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

    # --- Relationships (Example) ---
    # Assuming a DigitalTwin model exists
    # digital_twin = relationship("DigitalTwin", back_populates="patient", uselist=False)
    biometric_twin_id = Column(UUID(as_uuid=True), nullable=True) # Example FK if needed

    def __repr__(self) -> str:
        # Provide a representation useful for debugging, avoiding PHI exposure
        return f"<Patient(id={self.id}, created_at={self.created_at}, is_active={self.is_active})>"

# Example of adding other potentially sensitive fields if needed later:
# Add columns like _ethnicity, _preferred_language, etc. following the pattern above.
