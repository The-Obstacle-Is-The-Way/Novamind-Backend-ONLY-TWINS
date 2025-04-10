# -*- coding: utf-8 -*-
"""
HIPAA Compliance Integration Tests for NOVAMIND

These tests verify that all security components work together properly to protect PHI
and maintain HIPAA compliance in realistic application scenarios.
"""
import pytest
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY

from app.domain.entities.patient import Patient
from app.domain.entities.user import User, Role
from app.infrastructure.security.middleware.phi_sanitizer import PHISanitizerMiddleware
from app.infrastructure.security.encryption.field_encryption import encrypt_phi, decrypt_phi
from app.infrastructure.security.auth.jwt_handler import (
    create_access_token,
    verify_token,
    get_current_user,
    get_user_with_permissions
)
from app.infrastructure.security.audit.audit_log import AuditLogger, AuditAction
from app.infrastructure.persistence.sqlalchemy.patient_repository import PatientRepository


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.add.return_value = None
    session.commit.return_value = None
    return session


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    return MagicMock(spec=AuditLogger)


@pytest.fixture
def jwt_settings():
    """JWT settings fixture with test values."""
    return MagicMock(
        secret_key="test_secret_key_for_testing_only_not_for_production",
        algorithm="HS256",
        access_token_expire_minutes=30
    )


@pytest.fixture
def encryption_settings():
    """Encryption settings fixture with test values."""
    return MagicMock(
        phi_encryption_key="test_encryption_key_32_bytes_long!!",
        phi_encryption_iv_prefix="test_prefix",
        enable_phi_encryption=True
    )


@pytest.fixture
def sample_patient_data():
    """Sample patient data with PHI."""
    return {
        "id": "patient-123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "email": "john.doe@example.com",
        "phone_number": "555-123-4567",
        "address": "123 Main St, Anytown, USA",
        "ssn": "123-45-6789",
        "insurance_id": "INS-987654",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def patient_user():
    """Create a patient user."""
    return User(
        id="patient-123",
        email="john.doe@example.com",
        role=Role.PATIENT
    )


@pytest.fixture
def doctor_user():
    """Create a psychiatrist user."""
    return User(
        id="doctor-456",
        email="doctor@example.com",
        role=Role.PSYCHIATRIST
    )


@pytest.fixture
def patient_token(jwt_settings, patient_user):
    """Create a valid patient JWT token."""
    user_data = {
        "id": patient_user.id,
        "email": patient_user.email,
        "role": patient_user.role.value
    }
    return create_access_token(user_data, jwt_settings)


@pytest.fixture
def doctor_token(jwt_settings, doctor_user):
    """Create a valid doctor JWT token."""
    user_data = {
        "id": doctor_user.id,
        "email": doctor_user.email,
        "role": doctor_user.role.value
    }
    return create_access_token(user_data, jwt_settings)


@pytest.fixture
def patient_repository(mock_session, mock_audit_logger):
    """Create a patient repository with mocked dependencies."""
    return PatientRepository(
        session=mock_session,
        audit_logger=mock_audit_logger
    )


@pytest.fixture
@pytest.mark.db_required
def test_app(jwt_settings, encryption_settings, patient_repository):
    """Create a test FastAPI app with all security middleware and endpoints."""
    app = FastAPI()
    app.add_middleware(PHISanitizerMiddleware)
    
    # Patch dependency injection
    def get_test_jwt_settings():
        return jwt_settings
    
    def get_test_encryption_settings():
        return encryption_settings
    
    def get_patient_repository():
        return patient_repository
    
    with patch('app.infrastructure.security.auth.jwt_handler.get_jwt_settings', 
               return_value=jwt_settings), \
         patch('app.infrastructure.security.encryption.field_encryption.get_encryption_settings',
               return_value=encryption_settings):
        
        @app.get("/api/patients/{patient_id}")
        async def get_patient(
            patient_id: str,
            current_user: User = Depends(get_current_user),
            repository: PatientRepository = Depends(get_patient_repository)
        ):
            """Endpoint to get patient data that should sanitize PHI."""
            # Access control - patients can only view their own data
            if current_user.role == Role.PATIENT and current_user.id != patient_id:
                raise HTTPException(status_code=403, detail="Not authorized to access this patient")
                
            patient = repository.get_by_id(patient_id)
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")
                
            return {
                "id": patient.id,
                "name": f"{patient.first_name} {patient.last_name}",
                "email": patient.email,
                "date_of_birth": patient.date_of_birth,
                "ssn": patient.ssn,  # This should be sanitized in the response
                "phone_number": patient.phone_number,
                "address": patient.address,
                "insurance_id": patient.insurance_id
            }
        
        @app.post("/api/patients")
        async def create_patient(
            patient_data: dict,
            current_user: User = Depends(
                get_user_with_permissions([Role.PSYCHIATRIST, Role.ADMIN])
            ),
            repository: PatientRepository = Depends(get_patient_repository)
        ):
            """Endpoint to create a patient that should encrypt PHI."""
            patient = Patient(**patient_data)
            repository.create(patient)
            return {"id": patient.id, "message": "Patient created successfully"}
        
        return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.mark.db_required
def test_full_hipaa_flow_patient_viewing_own_data(
    client, patient_token, sample_patient_data, patient_repository, mock_session
):
    """
    Test a complete HIPAA flow where:
    1. A patient record exists with encrypted PHI
    2. A patient authenticates and accesses their own data
    3. PHI is properly decrypted for authorized access
    4. Response is sanitized of raw PHI
    5. Audit logging occurs
    """
    # Setup a mock patient in the database (with encrypted fields)
    encrypted_patient = {k: encrypt_phi(v) if k in ['ssn', 'date_of_birth', 'phone_number', 'address', 'insurance_id'] else v 
                        for k, v in sample_patient_data.items()}
    
    patient_model = MagicMock()
    patient_model.configure_mock(**encrypted_patient)
    mock_session.query.return_value.filter.return_value.first.return_value = patient_model
    
    # Setup a mock User from the token for the current_user dependency
    with patch('app.infrastructure.security.auth.jwt_handler.verify_token') as mock_verify:
        mock_verify.return_value = {
            "id": "patient-123", 
            "email": "john.doe@example.com",
            "role": "PATIENT"
        }
        
        # Access the patient endpoint with patient token
        response = client.get(
            "/api/patients/patient-123",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        # Verify response status
        assert response.status_code == 200
        
        # Patient should see their decrypted data, but PHI should be sanitized in the response
        data = response.json()
        
        # These assertions verify that sensitive data was properly handled
        assert "123-45-6789" not in response.text, "Raw SSN found in response"
        assert "[REDACTED-SSN]" in response.text, "SSN not properly redacted"
        
        # Verify repository called to get the patient
        patient_repository.get_by_id.assert_called_once_with("patient-123")
        
        # Verify audit logging occurred
        patient_repository.audit_logger.log_access.assert_called()


@pytest.mark.db_required
def test_full_hipaa_flow_doctor_creating_patient(
    client, doctor_token, sample_patient_data, patient_repository
):
    """
    Test a complete HIPAA flow where:
    1. A doctor authenticates
    2. Creates a new patient with PHI
    3. PHI is properly encrypted in the database
    4. Audit logging occurs
    """
    # Setup a mock User from the token for the current_user dependency
    with patch('app.infrastructure.security.auth.jwt_handler.verify_token') as mock_verify:
        mock_verify.return_value = {
            "id": "doctor-456", 
            "email": "doctor@example.com",
            "role": "PSYCHIATRIST"
        }
        
        # Create a new patient
        response = client.post(
            "/api/patients",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json=sample_patient_data
        )
        
        # Verify response status
        assert response.status_code == 200
        
        # Verify repository called to create the patient
        patient_repository.create.assert_called_once()
        
        # Get the patient entity passed to create
        created_patient = patient_repository.create.call_args[0][0]
        
        # Verify sensitive PHI was not logged
        patient_repository.audit_logger.log_access.assert_called()
        audit_call = patient_repository.audit_logger.log_access.call_args[0]
        assert "123-45-6789" not in str(audit_call), "SSN found in audit log"


@pytest.mark.db_required
def test_full_hipaa_flow_patient_unauthorized_for_other_patient(
    client, patient_token, sample_patient_data, patient_repository
):
    """
    Test a complete HIPAA flow where:
    1. A patient authenticates
    2. Attempts to access another patient's data
    3. Access is denied
    4. Failed access attempt is logged
    """
    # Setup a mock User from the token for the current_user dependency
    with patch('app.infrastructure.security.auth.jwt_handler.verify_token') as mock_verify:
        mock_verify.return_value = {
            "id": "patient-123", 
            "email": "john.doe@example.com",
            "role": "PATIENT"
        }
        
        # Try to access a different patient's data
        response = client.get(
            "/api/patients/patient-456",  # Different patient ID
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        # Verify access denied
        assert response.status_code == 403
        
        # Verify error response is sanitized and doesn't leak PHI
        assert "123-45-6789" not in response.text, "SSN leaked in error response"


@pytest.mark.db_required
def test_full_hipaa_flow_error_handling_and_logging(
    client, doctor_token, sample_patient_data, patient_repository, mock_session, mock_audit_logger
):
    """
    Test a complete HIPAA flow where:
    1. A doctor authenticates
    2. Repository has an error during data access
    3. Error is properly handled without leaking PHI
    4. Error is properly logged without PHI
    """
    # Setup a mock error in the repository
    mock_session.query.side_effect = Exception("Error processing patient with SSN 123-45-6789")
    
    # Setup a mock User from the token for the current_user dependency
    with patch('app.infrastructure.security.auth.jwt_handler.verify_token') as mock_verify, \
         patch('app.infrastructure.security.middleware.phi_sanitizer.logger') as mock_logger:
        
        mock_verify.return_value = {
            "id": "doctor-456", 
            "email": "doctor@example.com",
            "role": "PSYCHIATRIST"
        }
        
        # Access the patient endpoint
        response = client.get(
            "/api/patients/patient-123",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Verify response indicates error
        assert response.status_code >= 400
        
        # Verify error doesn't contain PHI
        assert "123-45-6789" not in response.text, "SSN leaked in error response"
        
        # Verify logs don't contain PHI
        for call in mock_logger.error.call_args_list:
            log_message = str(call)
            assert "123-45-6789" not in log_message, "SSN leaked in error log"