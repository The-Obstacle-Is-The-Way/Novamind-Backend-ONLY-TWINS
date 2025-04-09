# -*- coding: utf-8 -*-
"""
SQLAlchemy model for Patient entity.

This module defines the SQLAlchemy ORM model for the Patient entity,
mapping the domain entity to the database schema.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.sqlalchemy.config.database import Base
from app.infrastructure.security.encryption import EncryptionService

# Initialize encryption service for sensitive patient data
encryption_service = EncryptionService()


class PatientModel(Base):
    """
    SQLAlchemy model for the Patient entity with HIPAA-compliant encryption.

    This model maps to the 'patients' table in the database and
    represents patients in the NOVAMIND concierge psychiatry platform.
    All PHI (Protected Health Information) fields are encrypted at rest.
    """

    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Identity information - encrypted
    first_name = Column(String(255), nullable=False)  # Increased length for encryption
    last_name = Column(String(255), nullable=False)   # Increased length for encryption
    date_of_birth = Column(String(255), nullable=False)  # Stored as encrypted string
    
    # Contact information - encrypted
    email = Column(String(512), nullable=True, unique=True)  # Increased length for encryption
    phone = Column(String(255), nullable=True)  # Encrypted
    
    # Address information - encrypted
    address_line1 = Column(String(512), nullable=True)  # Encrypted
    address_line2 = Column(String(512), nullable=True)  # Encrypted
    city = Column(String(255), nullable=True)  # Encrypted
    state = Column(String(255), nullable=True)  # Encrypted
    postal_code = Column(String(255), nullable=True)  # Encrypted
    country = Column(String(255), nullable=True)  # Encrypted
    
    # Emergency contact information - encrypted
    emergency_contact_name = Column(String(512), nullable=True)  # Encrypted
    emergency_contact_phone = Column(String(255), nullable=True)  # Encrypted
    emergency_contact_relationship = Column(String(255), nullable=True)  # Encrypted
    
    # Insurance information - encrypted
    insurance_provider = Column(String(255), nullable=True)  # Encrypted
    insurance_policy_number = Column(String(255), nullable=True)  # Encrypted
    insurance_group_number = Column(String(255), nullable=True)  # Encrypted
    
    # Non-PHI fields (not encrypted)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    appointments = relationship("AppointmentModel", back_populates="patient")
    medications = relationship("MedicationModel", back_populates="patient")
    clinical_notes = relationship("ClinicalNoteModel", back_populates="patient")
    digital_twin = relationship(
        "DigitalTwinModel", back_populates="patient", uselist=False
    )

    def __repr__(self) -> str:
        """Return string representation of the patient."""
        return f"<Patient(id={self.id}, name={self.first_name} {self.last_name})>"

    @classmethod
    def from_domain(cls, patient) -> "PatientModel":
        """
        Create a SQLAlchemy model instance from a domain entity.
        Encrypts all PHI fields for HIPAA compliance.

        Args:
            patient: Domain Patient entity

        Returns:
            PatientModel: SQLAlchemy model instance with encrypted PHI
        """
        # Convert date to string for encryption
        dob_str = patient.date_of_birth.isoformat() if patient.date_of_birth else None
        
        # Encrypt PHI fields
        return cls(
            id=patient.id,
            first_name=encryption_service.encrypt(patient.first_name) if patient.first_name else None,
            last_name=encryption_service.encrypt(patient.last_name) if patient.last_name else None,
            date_of_birth=encryption_service.encrypt(dob_str) if dob_str else None,
            email=encryption_service.encrypt(patient.email) if patient.email else None,
            phone=encryption_service.encrypt(patient.phone) if patient.phone else None,
            address_line1=encryption_service.encrypt(patient.address.line1) if patient.address and patient.address.line1 else None,
            address_line2=encryption_service.encrypt(patient.address.line2) if patient.address and patient.address.line2 else None,
            city=encryption_service.encrypt(patient.address.city) if patient.address and patient.address.city else None,
            state=encryption_service.encrypt(patient.address.state) if patient.address and patient.address.state else None,
            postal_code=encryption_service.encrypt(patient.address.postal_code) if patient.address and patient.address.postal_code else None,
            country=encryption_service.encrypt(patient.address.country) if patient.address and patient.address.country else None,
            emergency_contact_name=encryption_service.encrypt(patient.emergency_contact.name)
                if patient.emergency_contact and patient.emergency_contact.name else None,
            emergency_contact_phone=encryption_service.encrypt(patient.emergency_contact.phone)
                if patient.emergency_contact and patient.emergency_contact.phone else None,
            emergency_contact_relationship=encryption_service.encrypt(patient.emergency_contact.relationship)
                if patient.emergency_contact and patient.emergency_contact.relationship else None,
            insurance_provider=encryption_service.encrypt(patient.insurance.provider)
                if patient.insurance and patient.insurance.provider else None,
            insurance_policy_number=encryption_service.encrypt(patient.insurance.policy_number)
                if patient.insurance and patient.insurance.policy_number else None,
            insurance_group_number=encryption_service.encrypt(patient.insurance.group_number)
                if patient.insurance and patient.insurance.group_number else None,
            active=patient.active,
            created_by=patient.created_by,
        )

    def to_domain(self):
        """
        Convert SQLAlchemy model instance to domain entity.
        Decrypts all PHI fields for application use.

        Returns:
            Patient: Domain entity instance with decrypted PHI
        """
        from app.domain.entities.patient import Patient
        from app.domain.value_objects.address import Address
        from app.domain.value_objects.emergency_contact import EmergencyContact
        from app.domain.value_objects.insurance import Insurance
        from datetime import date

        # Decrypt PHI fields
        first_name = encryption_service.decrypt(self.first_name) if self.first_name else None
        last_name = encryption_service.decrypt(self.last_name) if self.last_name else None
        
        # Handle date conversion
        date_of_birth = None
        if self.date_of_birth:
            date_str = encryption_service.decrypt(self.date_of_birth)
            if date_str:
                try:
                    date_of_birth = date.fromisoformat(date_str)
                except ValueError:
                    # Log error but don't expose PHI
                    from app.core.utils.logging import get_logger
                    logger = get_logger(__name__)
                    logger.error("Error parsing decrypted date_of_birth")
        
        email = encryption_service.decrypt(self.email) if self.email else None
        phone = encryption_service.decrypt(self.phone) if self.phone else None

        # Create value objects with decrypted data
        address = None
        if any([self.address_line1, self.city, self.state, self.postal_code, self.country]):
            address = Address(
                line1=encryption_service.decrypt(self.address_line1) if self.address_line1 else None,
                line2=encryption_service.decrypt(self.address_line2) if self.address_line2 else None,
                city=encryption_service.decrypt(self.city) if self.city else None,
                state=encryption_service.decrypt(self.state) if self.state else None,
                postal_code=encryption_service.decrypt(self.postal_code) if self.postal_code else None,
                country=encryption_service.decrypt(self.country) if self.country else None,
            )

        emergency_contact = None
        if self.emergency_contact_name:
            emergency_contact = EmergencyContact(
                name=encryption_service.decrypt(self.emergency_contact_name) if self.emergency_contact_name else None,
                phone=encryption_service.decrypt(self.emergency_contact_phone) if self.emergency_contact_phone else None,
                relationship=encryption_service.decrypt(self.emergency_contact_relationship) if self.emergency_contact_relationship else None,
            )

        insurance = None
        if self.insurance_provider:
            insurance = Insurance(
                provider=encryption_service.decrypt(self.insurance_provider) if self.insurance_provider else None,
                policy_number=encryption_service.decrypt(self.insurance_policy_number) if self.insurance_policy_number else None,
                group_number=encryption_service.decrypt(self.insurance_group_number) if self.insurance_group_number else None,
            )

        return Patient(
            id=self.id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            email=email,
            phone=phone,
            address=address,
            emergency_contact=emergency_contact,
            insurance=insurance,
            active=self.active,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
