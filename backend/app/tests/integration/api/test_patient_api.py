"""
Integration test for Patient API endpoints.

This test verifies the Patient API endpoints with real database connections
and external service dependencies.
"""

import pytest
import json
import uuid
from datetime import date
from fastapi import status

from app.domain.value_objects.patient_id import PatientId
from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel


@pytest.mark.integration
def test_get_patient_by_id_returns_correct_data(test_client, db_session, token_headers, create_test_patients):
    """Test that GET /api/patients/{id} returns the correct patient data."""
    # Arrange
    patient_id = "123e4567-e89b-12d3-a456-426614174000"  # From the create_test_patients fixture
    
    # Act
    response = test_client.get(f"/api/patients/{patient_id}", headers=token_headers)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == patient_id
    assert data["name"] == "John Doe"
    assert data["medical_record_number"] == "MRN12345"


@pytest.mark.integration
def test_create_patient_persists_to_database(test_client, db_session, token_headers):
    """Test that POST /api/patients creates a new patient in the database."""
    # Arrange
    patient_data = {
        "name": "New Test Patient",
        "date_of_birth": "1995-08-24",
        "medical_record_number": "MRN-TEST-001"
    }
    
    # Act
    response = test_client.post(
        "/api/patients",
        json=patient_data,
        headers=token_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    
    # Verify database state
    db_patient = db_session.query(PatientModel).filter(
        PatientModel.id == data["id"]
    ).first()
    
    assert db_patient is not None
    assert db_patient.name == patient_data["name"]
    assert db_patient.medical_record_number == patient_data["medical_record_number"]


@pytest.mark.integration
def test_update_patient_modifies_database_record(test_client, db_session, token_headers, create_test_patients):
    """Test that PUT /api/patients/{id} updates the patient in the database."""
    # Arrange
    patient_id = "123e4567-e89b-12d3-a456-426614174000"  # From the create_test_patients fixture
    update_data = {
        "name": "John Doe Updated",
        "date_of_birth": "1990-01-01",
        "medical_record_number": "MRN12345-UPDATED"
    }
    
    # Act
    response = test_client.put(
        f"/api/patients/{patient_id}",
        json=update_data,
        headers=token_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    # Verify database state
    db_patient = db_session.query(PatientModel).filter(
        PatientModel.id == patient_id
    ).first()
    
    assert db_patient.name == update_data["name"]
    assert db_patient.medical_record_number == update_data["medical_record_number"]


@pytest.mark.integration
def test_delete_patient_removes_from_database(test_client, db_session, token_headers, create_test_patients):
    """Test that DELETE /api/patients/{id} removes the patient from the database."""
    # Arrange
    patient_id = "223e4567-e89b-12d3-a456-426614174001"  # From the create_test_patients fixture
    
    # Act
    response = test_client.delete(
        f"/api/patients/{patient_id}",
        headers=token_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify database state
    db_patient = db_session.query(PatientModel).filter(
        PatientModel.id == patient_id
    ).first()
    
    assert db_patient is None


@pytest.mark.integration
def test_get_all_patients_returns_paginated_list(test_client, token_headers, create_test_patients):
    """Test that GET /api/patients returns a paginated list of patients."""
    # Act
    response = test_client.get(
        "/api/patients?page=1&limit=10",
        headers=token_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert len(data["items"]) == 2  # From the create_test_patients fixture
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["limit"] == 10


@pytest.mark.integration
@pytest.mark.security
def test_access_patient_api_without_token_fails(test_client):
    """Test that accessing patient API endpoints without a token fails with 401."""
    # Arrange - No token
    
    # Act & Assert
    response = test_client.get("/api/patients")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    response = test_client.get("/api/patients/123e4567-e89b-12d3-a456-426614174000")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    response = test_client.post(
        "/api/patients",
        json={"name": "Test", "date_of_birth": "1990-01-01", "medical_record_number": "MRN123"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.security
def test_admin_only_endpoints_require_admin_role(test_client, token_headers, admin_token_headers):
    """Test that admin-only endpoints require the admin role."""
    # Arrange - Test with non-admin token
    
    # Act & Assert
    response = test_client.get(
        "/api/patients/audit-trail",
        headers=token_headers  # Regular user token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Try with admin token
    response = test_client.get(
        "/api/patients/audit-trail",
        headers=admin_token_headers  # Admin token
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.hipaa
def test_patient_data_is_encrypted_in_database(test_client, db_session, token_headers):
    """Test that sensitive patient data is stored encrypted in the database."""
    # Arrange
    patient_data = {
        "name": "Encryption Test Patient",
        "date_of_birth": "1980-05-15",
        "medical_record_number": "MRN-SENSITIVE-123",
        "phi_notes": "This patient has a history of sensitive conditions."
    }
    
    # Act - Create a patient
    response = test_client.post(
        "/api/patients",
        json=patient_data,
        headers=token_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    # Direct database inspection to verify encryption
    patient_model = db_session.query(PatientModel).filter(
        PatientModel.id == data["id"]
    ).first()
    
    # Verify that the sensitive field is not stored as plaintext
    # This assumes the phi_notes field is encrypted at rest
    assert patient_model.phi_notes != patient_data["phi_notes"]
    
    # While API response should contain decrypted data
    assert data["phi_notes"] == patient_data["phi_notes"]


@pytest.mark.integration
@pytest.mark.performance
def test_bulk_patient_creation_performance(test_client, db_session, token_headers):
    """Test the performance of bulk patient creation."""
    # Arrange
    num_patients = 10
    bulk_patients = []
    
    for i in range(num_patients):
        bulk_patients.append({
            "name": f"Bulk Test Patient {i}",
            "date_of_birth": "1990-01-01",
            "medical_record_number": f"MRN-BULK-{i:03d}"
        })
    
    # Act
    import time
    start_time = time.time()
    
    response = test_client.post(
        "/api/patients/bulk",
        json={"patients": bulk_patients},
        headers=token_headers
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["created_ids"]) == num_patients
    
    # Performance assertion - should create 10 patients in under 1 second
    assert execution_time < 1.0, f"Bulk creation took {execution_time} seconds, which exceeds the 1.0 second threshold"
