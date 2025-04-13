"""
Database-dependent tests for the Patient Repository.

These tests require an actual database connection.
They test the repository layer's interaction with the database.
"""
import uuid
from datetime import datetime, timedelta

import pytest

from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import ()
PatientRepository,  



@pytest.mark.db_required()
class TestPatientRepository:
    """
    Integration tests for the PatientRepository.
    
    These tests require a real database connection and are marked with db_required.
    """
    
    @pytest.fixture
    async def repository(self, db_session):
        """Create a patient repository with a real DB session."""
#         return PatientRepository(db_session)
    
@pytest.fixture
    async def sample_patient_data(self):
        """Create sample patient data for testing."""
        patient_id = str(uuid.uuid4())
#         return {
"id": patient_id,
"name": f"Test Patient {patient_id[:8]}",
"date_of_birth": datetime.now() - timedelta(days=365*30),  # ~30 years old
"gender": "female",
"email": f"patient_{patient_id[:8]}@example.com",
"phone": "555-123-4567",
"address": "123 Test St, Test City, TS 12345",
"insurance_number": f"INS{patient_id[:8]}",
"created_at": datetime.now(),
"updated_at": datetime.now()
}
    
    async def test_create_patient(self, repository, sample_patient_data):
        """Test creating a patient in the database."""
        # Create a patient
        patient = await repository.create(sample_patient_data)
        
        # Verify patient was created
        assert patient is not None
        assert patient.id == sample_patient_data["id"]
        assert patient.name == sample_patient_data["name"]
        assert patient.email == sample_patient_data["email"]
        
        # Clean up - delete the patient
        await repository.delete(patient.id)
    
    async def test_get_patient_by_id(self, repository, sample_patient_data):
        """Test retrieving a patient by ID from the database."""
        # Create a patient first
        created_patient = await repository.create(sample_patient_data)
        
        # Get the patient by ID
        retrieved_patient = await repository.get_by_id(created_patient.id)
        
        # Verify the patient was retrieved correctly
        assert retrieved_patient is not None
        assert retrieved_patient.id == created_patient.id
        assert retrieved_patient.name == created_patient.name
        assert retrieved_patient.email == created_patient.email
        
        # Clean up
        await repository.delete(created_patient.id)
    
    async def test_update_patient(self, repository, sample_patient_data):
        """Test updating a patient in the database."""
        # Create a patient first
        created_patient = await repository.create(sample_patient_data)

        # Update data
        update_data = {
        "name": "Updated Name",
        "email": "updated.email@example.com"
        }
        
        # Update the patient
        updated_patient = await repository.update(created_patient.id, update_data)
        
        # Verify the update
        assert updated_patient is not None
        assert updated_patient.id == created_patient.id
        assert updated_patient.name == update_data["name"]
        assert updated_patient.email == update_data["email"]
        
        # Double-check by retrieving again
        retrieved_patient = await repository.get_by_id(created_patient.id)
        assert retrieved_patient.name == update_data["name"]
        
        # Clean up
        await repository.delete(created_patient.id)
    
    async def test_delete_patient(self, repository, sample_patient_data):
        """Test deleting a patient from the database."""
        # Create a patient first
        created_patient = await repository.create(sample_patient_data)
        
        # Delete the patient
        result = await repository.delete(created_patient.id)
        
        # Verify deletion was successful
        assert result is True
        
        # Verify patient no longer exists
        retrieved_patient = await repository.get_by_id(created_patient.id)
        assert retrieved_patient is None
    
    async def test_get_all_patients(self, repository, sample_patient_data):
        """Test retrieving all patients from the database."""
        # Create multiple patients
        patient_ids = []
        for i in range(3):
            data = sample_patient_data.copy()
            data["id"] = str(uuid.uuid4())
            data["name"] = f"Test Patient {i}"
            data["email"] = f"patient{i}@example.com"
        
            patient = await repository.create(data)
            patient_ids.append(patient.id)
    
        # Get all patients
        all_patients = await repository.get_all()
    
        # Verify at least our test patients exist
        assert len(all_patients) >= 3
        test_patients = [p for p in all_patients if p.id in patient_ids]
        assert len(test_patients) == 3
    
        # Clean up
        for patient_id in patient_ids:
            await repository.delete(patient_id)