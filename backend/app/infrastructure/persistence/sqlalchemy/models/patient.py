"""
SQLAlchemy models for patient data with encryption.

This module defines the patient-related SQLAlchemy models with built-in
encryption capabilities for HIPAA compliance.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

import sqlalchemy as sa
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.core.security.encryption import encrypt_value, decrypt_value, get_encryption_key
from app.infrastructure.persistence.sqlalchemy.database import Base


class Patient(Base):
    """
    SQLAlchemy model for patient data with sensitive field encryption.
    
    This model supports automatic encryption of PHI fields for HIPAA compliance,
    while allowing normal database operations like filtering and sorting on
    non-sensitive fields.
    """
    
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(64), unique=True, index=True, nullable=True)
    
    # Non-sensitive fields (not encrypted)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Encrypted patient fields
    _first_name = Column("first_name", Text, nullable=True)
    _last_name = Column("last_name", Text, nullable=True)
    _dob = Column("dob", Text, nullable=True)
    _email = Column("email", Text, nullable=True)
    _phone = Column("phone", Text, nullable=True)
    _address = Column("address", Text, nullable=True)
    _medical_record_number = Column("medical_record_number", Text, nullable=True)
    
    # Public non-PHI identification field
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # JSON data for additional fields (encrypted)
    _extra_data = Column("extra_data", Text, nullable=True)
    
    # Relationships
    biometric_twin_id = Column(UUID(as_uuid=True), nullable=True)
    
    def __init__(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        dob: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        medical_record_number: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a patient model with encryption.
        
        Args:
            first_name: Patient's first name
            last_name: Patient's last name
            dob: Date of birth (ISO format)
            email: Email address
            phone: Phone number
            address: Physical address
            medical_record_number: Medical record identifier
            extra_data: Additional structured data
            **kwargs: Other fields passed directly to SQLAlchemy
        """
        super().__init__(**kwargs)
        
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if dob is not None:
            self.dob = dob
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address
        if medical_record_number is not None:
            self.medical_record_number = medical_record_number
        if extra_data is not None:
            self.extra_data = extra_data
    
    @hybrid_property
    def first_name(self) -> Optional[str]:
        """Get decrypted first name."""
        return decrypt_value(self._first_name) if self._first_name else None
    
    @first_name.setter
    def first_name(self, value: Optional[str]) -> None:
        """Set encrypted first name."""
        self._first_name = encrypt_value(value) if value is not None else None
    
    @hybrid_property
    def last_name(self) -> Optional[str]:
        """Get decrypted last name."""
        return decrypt_value(self._last_name) if self._last_name else None
    
    @last_name.setter
    def last_name(self, value: Optional[str]) -> None:
        """Set encrypted last name."""
        self._last_name = encrypt_value(value) if value is not None else None
    
    @hybrid_property
    def dob(self) -> Optional[str]:
        """Get decrypted date of birth."""
        return decrypt_value(self._dob) if self._dob else None
    
    @dob.setter
    def dob(self, value: Optional[str]) -> None:
        """Set encrypted date of birth."""
        self._dob = encrypt_value(value) if value is not None else None
    
    @hybrid_property
    def email(self) -> Optional[str]:
        """Get decrypted email."""
        return decrypt_value(self._email) if self._email else None
    
    @email.setter
    def email(self, value: Optional[str]) -> None:
        """Set encrypted email."""
        self._email = encrypt_value(value) if value is not None else None
    
    @hybrid_property
    def phone(self) -> Optional[str]:
        """Get decrypted phone number."""
        return decrypt_value(self._phone) if self._phone else None
    
    @phone.setter
    def phone(self, value: Optional[str]) -> None:
        """Set encrypted phone number."""
        self._phone = encrypt_value(value) if value is not None else None
    
    @hybrid_property
    def address(self) -> Optional[str]:
        """Get decrypted address."""
        return decrypt_value(self._address) if self._address else None
    
    @address.setter
    def address(self, value: Optional[str]) -> None:
        """Set encrypted address."""
        self._address = encrypt_value(value) if value is not None else None
    
    @hybrid_property
    def medical_record_number(self) -> Optional[str]:
        """Get decrypted medical record number."""
        return decrypt_value(self._medical_record_number) if self._medical_record_number else None
    
    @medical_record_number.setter
    def medical_record_number(self, value: Optional[str]) -> None:
        """Set encrypted medical record number."""
        self._medical_record_number = encrypt_value(value) if value is not None else None
    
    @hybrid_property
    def extra_data(self) -> Optional[Dict[str, Any]]:
        """Get decrypted extra data JSON."""
        if not self._extra_data:
            return None
        
        try:
            decrypted = decrypt_value(self._extra_data)
            if decrypted:
                return json.loads(decrypted)
            return None
        except Exception as e:
            # Log error but don't expose it to prevent information leakage
            return None
    
    @extra_data.setter
    def extra_data(self, value: Optional[Dict[str, Any]]) -> None:
        """Set encrypted extra data JSON."""
        if value is None:
            self._extra_data = None
        else:
            json_str = json.dumps(value)
            self._extra_data = encrypt_value(json_str)
    
    def to_dict(self, include_phi: bool = False) -> Dict[str, Any]:
        """
        Convert patient model to dictionary.
        
        Args:
            include_phi: Whether to include PHI fields
            
        Returns:
            Dict representation of the patient
        """
        result = {
            "id": str(self.id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }
        
        if include_phi:
            result.update({
                "first_name": self.first_name,
                "last_name": self.last_name,
                "dob": self.dob,
                "email": self.email,
                "phone": self.phone,
                "address": self.address,
                "medical_record_number": self.medical_record_number,
                "extra_data": self.extra_data,
            })
        
        return result
