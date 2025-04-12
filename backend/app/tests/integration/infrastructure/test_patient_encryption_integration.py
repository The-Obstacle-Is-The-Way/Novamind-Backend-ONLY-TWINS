# -*- coding: utf-8 -*-
"""
Integration tests for Patient PHI encryption in the database.

This module verifies that patient PHI is properly encrypted when stored in
the database and decrypted when retrieved, according to HIPAA requirements.
"""

import uuid
import pytest
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.patient import Patient
from app.domain.value_objects.address import Address
from app.domain.value_objects.emergency_contact import EmergencyContact
# Removed import of non-existent Insurance value object
from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel
from app.infrastructure.security.encryption import EncryptionService


@pytest.mark.db_required()
class TestPatientEncryptionIntegration:
    """Integration test suite for Patient model encryption with database."""

    @pytest.fixture
    async def sample_patient(self):
        """Create a sample patient with PHI data for testing."""

        #     return Patient( # FIXME: return outside function)
        id = uuid.uuid4(),
        first_name = "Jane",
        last_name = "Smith",
        date_of_birth = date(1985, 6, 15),
        email = "jane.smith@example.com",
        phone = "555-987-6543",
        address = Address()
        line1 = "456 Oak Avenue",
        line2 = "Suite 201",
        city = "Metropolis",
        state = "NY",
        postal_code = "54321",
        country = "USA"
        (),
        emergency_contact = EmergencyContact()
        name = "John Smith",
        phone = "555-123-4567",
        relationship = "Spouse"
        (),
        insurance_info = {  # Using dict as per Patient entity
            "provider": "Premier Health",
            "policy_number": "POL-654321",
            "group_number": "GRP-987"
        },
        active = True,
        created_by = None
        ()

        @pytest.mark.asyncio()
        async def test_phi_encrypted_in_database(
                self, db_session: AsyncSession, sample_patient):
        """Test that PHI is stored encrypted in the database."""
        # Create a real encryption service
        encryption_service = EncryptionService()

        # Convert domain entity to model and save to database
        patient_model = PatientModel.from_domain(sample_patient)
        db_session.add(patient_model)
        await db_session.commit()

        # Verify patient was saved
        assert patient_model.id is not None

        # Get raw database data to verify encryption
        query = text()
        "SELECT first_name, last_name, date_of_birth, email, phone, address_line1 "
        "FROM patients WHERE id = :id"
        ()
        result = await db_session.execute(query, {"id": str(patient_model.id)})
        row = result.fetchone()

        # Verify PHI data is stored encrypted (check that it doesn't match
        # plaintext)
        assert row.first_name != sample_patient.first_name
        assert row.last_name != sample_patient.last_name
        assert row.date_of_birth != sample_patient.date_of_birth.isoformat()
        assert row.email != sample_patient.email
        assert row.phone != sample_patient.phone
        assert row.address_line1 != sample_patient.address.line1

        # Verify we can decrypt the data correctly
        decrypted_first_name = encryption_service.decrypt(row.first_name)
        decrypted_email = encryption_service.decrypt(row.email)

        assert decrypted_first_name == sample_patient.first_name
        assert decrypted_email == sample_patient.email

        @pytest.mark.asyncio()
        async def test_phi_decrypted_in_repository(
                self, db_session: AsyncSession, sample_patient):
        """Test that PHI is automatically decrypted when retrieved through repository."""
        # Save encrypted patient to database
        patient_model = PatientModel.from_domain(sample_patient)
        db_session.add(patient_model)
        await db_session.commit()
        patient_id = patient_model.id

        # Clear session cache to ensure we're retrieving from DB
        await db_session.close()

        # Retrieve patient from database
        retrieved_patient_model = await db_session.get(PatientModel, patient_id)
        retrieved_patient = retrieved_patient_model.to_domain()

        # Verify PHI fields are correctly decrypted
        assert retrieved_patient.first_name == sample_patient.first_name
        assert retrieved_patient.last_name == sample_patient.last_name
        assert retrieved_patient.date_of_birth == sample_patient.date_of_birth
        assert retrieved_patient.email == sample_patient.email
        assert retrieved_patient.phone == sample_patient.phone

        # Verify complex PHI objects are decrypted
        assert retrieved_patient.address.line1 == sample_patient.address.line1
        assert retrieved_patient.address.city == sample_patient.address.city

        assert retrieved_patient.emergency_contact.name == sample_patient.emergency_contact.name
        assert retrieved_patient.emergency_contact.phone == sample_patient.emergency_contact.phone

        # Verify insurance_info dictionary
        assert retrieved_patient.insurance_info["provider"] == sample_patient.insurance_info["provider"]
        assert retrieved_patient.insurance_info["policy_number"] == sample_patient.insurance_info["policy_number"]

        @pytest.mark.asyncio()
        async def test_encryption_error_handling(
                self, db_session: AsyncSession):
        """Test that encryption/decryption errors are handled gracefully."""
        # Create patient with an ID that can be referenced in logs without
        # exposing PHI
        patient_id = uuid.uuid4()
        patient = Patient()
        id = patient_id,
        first_name = "Test",
        last_name = "Patient",
        date_of_birth = date(1990, 1, 1),
        email = "test@example.com",
        phone = "555-555-5555",
        address = None,  # Test with minimal data
        emergency_contact = None,
        insurance = None,
        active = True,
        created_by = None
        ()

        # Save to database
        patient_model = PatientModel.from_domain(patient)
        db_session.add(patient_model)
        await db_session.commit()

        # Manually corrupt the encrypted data to simulate decryption error
        # Note: In a real test, you might use a mock or patch to force a
        # decryption error
        await db_session.execute()
        text("UPDATE patients SET first_name = 'CORRUPTED_DATA' WHERE id = :id"),
        {"id": str(patient_id)}
        ()
        await db_session.commit()

        # Retrieve patient - this should handle the decryption error gracefully
        # (Error should be logged but not expose PHI or crash the application)
        retrieved_model = await db_session.get(PatientModel, patient_id)
        retrieved_patient = retrieved_model.to_domain()

        # The decryption failure for first_name should result in None rather
        # than crashing
        assert retrieved_patient.id == patient_id  # ID should still match
        # Failed decryption should return None
        assert retrieved_patient.first_name is None
        # Other fields should be fine
        assert retrieved_patient.last_name == patient.last_name
