"""
Integration test for Patient API endpoints

These tests verify the behavior of the Patient API endpoints with actual
HTTP requests and database interactions.
"""

import pytest
import json
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.infrastructure.database.models import PatientModel
from backend.app.infrastructure.database.session import get_session


@pytest.fixture
def api_client():
    """Provide a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Provide a database session for testing."""
    # This would typically be a test database connection
    from sqlalchemy.orm import Session
    , session = next(get_session())
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_patient(db_session):
    """Create a test patient in the database."""
    patient = PatientModel(
        id="P12345",
        medical_record_number="MRN-678901",
        name="Test Patient",
        date_of_birth="1980-01-15",
        gender="male",
        email="test@example.com"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    
    yield patient
    
    # Clean up after test
    db_session.delete(patient)
    db_session.commit()


@pytest.mark.integration()
class TestPatientAPI:
    """Tests for the Patient API endpoints."""
    
    def test_get_patient_by_id_success(self, api_client, test_patient):
        """Test retrieving a patient by ID successfully."""
        # Arrange - patient is created by fixture
        
        # Act
        response = api_client.get(f"/api/v1/patients/{test_patient.id}")
        
        # Assert
        assert response.status_code  ==  200
        data = response.json()
        assert data["id"] == test_patient.id
        assert data["name"] == test_patient.name
        assert data["medical_record_number"] == test_patient.medical_record_number
    
    def test_get_patient_by_id_not_found(self, api_client):
        """Test retrieving a non-existent patient by ID."""
        # Arrange
        non_existent_id = "NONEXISTENT"
        
        # Act
        response = api_client.get(f"/api/v1/patients/{non_existent_id}")
        
        # Assert
        assert response.status_code  ==  404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_create_patient_success(self, api_client, db_session):
        """Test creating a new patient successfully."""
        # Arrange
        patient_data = {
            "id": "P67890",
            "medical_record_number": "MRN-123456",
            "name": "New Test Patient",
            "date_of_birth": "1990-05-20",
            "gender": "female",
            "email": "newtest@example.com"
        }
        
        # Act
        response = api_client.post(
            "/api/v1/patients/",
            json=patient_data
        )
        
        # Assert
        assert response.status_code  ==  201
        data = response.json()
        assert data["id"] == patient_data["id"]
        assert data["name"] == patient_data["name"]
        
        # Verify the patient was actually saved to the database
        saved_patient = db_session.query(PatientModel).filter_by(id=patient_data["id"]).first()
        assert saved_patient is not None
        assert saved_patient.name  ==  patient_data["name"]
        
        # Clean up
        db_session.delete(saved_patient)
        db_session.commit()
    
    def test_update_patient_success(self, api_client, test_patient, db_session):
        """Test updating an existing patient successfully."""
        # Arrange
        update_data = {
            "name": "Updated Test Patient",
            "email": "updated@example.com"
        }
        
        # Act
        response = api_client.patch(
            f"/api/v1/patients/{test_patient.id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code  ==  200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["email"] == update_data["email"]
        
        # Verify the changes were saved to the database
        db_session.refresh(test_patient)
        assert test_patient.name  ==  update_data["name"]
        assert test_patient.email  ==  update_data["email"]
    
    def test_delete_patient_success(self, api_client, db_session):
        """Test deleting a patient successfully."""
        # Arrange - Create a patient specifically for deletion
        patient_to_delete = PatientModel(
            id="P-DELETE",
            medical_record_number="MRN-DELETE",
            name="Patient to Delete",
            date_of_birth="1985-06-15",
            gender="female",
            email="delete@example.com"
        )
        db_session.add(patient_to_delete)
        db_session.commit()
        
        # Act
        response = api_client.delete(f"/api/v1/patients/{patient_to_delete.id}")
        
        # Assert
        assert response.status_code  ==  204
        
        # Verify the patient was actually deleted from the database
        deleted_patient = db_session.query(PatientModel).filter_by(id=patient_to_delete.id).first()
        assert deleted_patient is None
