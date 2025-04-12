# -*- coding: utf-8 -*-
"""Unit tests for Patient domain entity."""

import pytest
from datetime import date
from unittest.mock import MagicMock
from uuid import UUID

from app.domain.entities.patient import Patient
from app.domain.value_objects.contact_info import ContactInfo
from app.domain.value_objects.address import Address
from app.infrastructure.security.encryption import EncryptionService


@pytest.fixture
def mock_encryption_service():
    """Create a mock encryption service."""
    mock = MagicMock(spec=EncryptionService)
    mock.encrypt.side_effect = lambda x: f"encrypted_{x}"
    mock.decrypt.side_effect = lambda x: x.replace("encrypted_", "")
    return mock


@pytest.fixture
def valid_patient_data(mock_encryption_service):
    """Create valid patient test data."""
    return {
        "id": UUID("12345678-1234-5678-1234-567812345678"),
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": date(1990, 1, 1),
        "contact_info": ContactInfo(
            email="john.doe@example.com",
            phone="123-456-7890"
        ),
        "address": Address(
            street="123 Main St",
            city="Anytown",
            state="NY",
            zip_code="12345"
        ),
        "encryption_service": mock_encryption_service
    }


@pytest.mark.venv_only()
def test_create_patient(valid_patient_data, mock_encryption_service):
    """Test patient creation with valid data."""
    # Create patient
    patient = Patient(**valid_patient_data)
    
    # Verify basic attributes
    assert str(patient.id) == "12345678-1234-5678-1234-567812345678"
    assert patient.first_name  ==  "John"
    assert patient.last_name  ==  "Doe"
    assert patient.date_of_birth  ==  date(1990, 1, 1)
    
    # Verify contact info
    assert patient.contact_info.email  ==  "john.doe@example.com"
    assert patient.contact_info.phone  ==  "123-456-7890"
    
    # Verify address
    assert patient.address.street  ==  "123 Main St"
    assert patient.address.city  ==  "Anytown"
    assert patient.address.state  ==  "NY"
    assert patient.address.zip_code  ==  "12345"
    
    # Verify PHI fields are encrypted
    assert mock_encryption_service.encrypt.called
    # Check that the internal attribute is encrypted
    assert patient._first_name.startswith("encrypted_")
    assert patient._last_name.startswith("encrypted_")
    assert patient._contact_info.email.startswith("encrypted_")
    assert patient._contact_info.phone.startswith("encrypted_")


def test_update_patient(valid_patient_data, mock_encryption_service):
    """Test patient update."""
    # Create initial patient
    patient = Patient(**valid_patient_data)
    
    # Update patient
    patient.update(
        first_name="Jane",
        last_name="Smith",
        contact_info=ContactInfo(
            email="jane.smith@example.com",
            phone="987-654-3210"
        )
    )
    
    # Verify updates
    assert patient.first_name  ==  "Jane"
    assert patient.last_name  ==  "Smith"
    assert patient.contact_info.email  ==  "jane.smith@example.com"
    assert patient.contact_info.phone  ==  "987-654-3210"
    
    # Verify PHI fields are encrypted
    assert mock_encryption_service.encrypt.called
    # Check that the internal attribute is encrypted
    assert patient._first_name.startswith("encrypted_")
    assert patient._last_name.startswith("encrypted_")
    assert patient._contact_info.email.startswith("encrypted_")
    assert patient._contact_info.phone.startswith("encrypted_")


def test_patient_phi_masking(valid_patient_data):
    """Test PHI masking in patient data."""
    patient = Patient(**valid_patient_data)
    
    # Test PHI masking in dict representation
    patient_dict = patient.to_dict()
    assert patient_dict["first_name"] == "[REDACTED]"
    assert patient_dict["last_name"] == "[REDACTED]"
    assert patient_dict["contact_info"]["email"] == "[REDACTED]"
    assert patient_dict["contact_info"]["phone"] == "[REDACTED]"
    
    # Test PHI masking in string representation
    patient_str = str(patient)
    assert "[REDACTED]" in patient_str
