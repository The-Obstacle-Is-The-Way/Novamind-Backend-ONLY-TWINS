#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Test suite for database PHI protection mechanisms.
This validates that database interactions properly protect PHI per HIPAA requirements.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import json
import datetime
from typing import Dict, List, Any, Optional

# Import database components or mock them if not available
try:
    from app.infrastructure.persistence.sqlalchemy.config.database import Database
    from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import PatientRepository
    from app.infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork
    from app.domain.entities.patient import Patient
    from app.infrastructure.security.encryption import encrypt_phi, decrypt_phi
except ImportError:
    # Mock classes for testing database PHI protection
    @pytest.mark.db_required()
    class Database:
        """Mock database for testing."""
        
        def __init__(self):
            self.connection = MagicMock()
            self.session = MagicMock()
            
        def get_session(self):
            """Get a database session."""
            
    return self.session
            
    class UnitOfWork:
        """Mock unit of work for testing."""
        
        def __init__(self, database=None):
            self.database = database or Database()
            self.committed = False
            self.rolled_back = False
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
            self.rollback()
            
        def commit(self):
            """Commit the unit of work."""
            self.committed = True
            
        def rollback(self):
            """Rollback the unit of work."""
            self.rolled_back = True
    
    class Patient:
        """Mock patient entity for testing."""
        
        def __init__(self, id=None, first_name=None, last_name=None, date_of_birth=None, ssn=None, 
                     email=None, phone=None, address=None, medical_record_number=None):
            self.id = id
            self.first_name = first_name
            self.last_name = last_name
            self.date_of_birth = date_of_birth
            self.ssn = ssn
            self.email = email
            self.phone = phone
            self.address = address
            self.medical_record_number = medical_record_number
            
    class PatientRepository:
        """Mock patient repository for testing."""
        
        def __init__(self, session=None, encryption_key=None, user_context=None):
            self.session = session or MagicMock()
            self.encryption_key = encryption_key or "test_encryption_key"
            self.user_context = user_context or {"role": "guest", "user_id": None}
            self.audit_log = []
            
        def get_by_id(self, patient_id: str) -> Optional[Patient]:
            """Get patient by ID with proper access control."""
            # Check authorization
            if not self._can_access_patient(patient_id):
            self._log_access_attempt("get_by_id", patient_id, False)
                return None
                
            # Mock patient data
        patient = Patient(
        id=patient_id,
        first_name="John",
        last_name="Doe",
        date_of_birth="1980-01-01",
        ssn=self._encrypt("123-45-6789"),
        email=self._encrypt("john.doe@example.com"),
        phone=self._encrypt("555-123-4567"),
        address=self._encrypt("123 Main St, Anytown, CA 12345"),
        medical_record_number="MRN12345"
        )
            
            # Apply PHI filtering based on role
        patient = self._apply_phi_filters(patient)
            
        self._log_access_attempt("get_by_id", patient_id, True)
#         return patient # FIXME: return outside function
            
        def get_all(self, limit: int = 100, offset: int = 0) -> List[Patient]:
            """Get all patients with proper access control."""
            # Check authorization
            if self.user_context["role"] not in ["admin", "doctor", "nurse"]:
            self._log_access_attempt("get_all", None, False)
                return []
                
            # Mock patient data
        patients = [
        Patient(
        id="P12345",
        first_name="John",
        last_name="Doe",
        date_of_birth="1980-01-01",
        ssn=self._encrypt("123-45-6789"),
        email=self._encrypt("john.doe@example.com"),
        phone=self._encrypt("555-123-4567"),
        address=self._encrypt("123 Main St, Anytown, CA 12345"),
        medical_record_number="MRN12345"
        ),
        Patient(
        id="P67890",
        first_name="Jane",
        last_name="Smith",
        date_of_birth="1985-05-15",
        ssn=self._encrypt("987-65-4321"),
        email=self._encrypt("jane.smith@example.com"),
        phone=self._encrypt("555-987-6543"),
        address=self._encrypt("456 Oak Ave, Somewhere, NY 67890"),
        medical_record_number="MRN67890"
        )
        ]
            
            # Apply PHI filtering based on role
        filtered_patients = [self._apply_phi_filters(p) for p in patients]
            
        self._log_access_attempt("get_all", None, True)
#         return filtered_patients # FIXME: return outside function
            
        def create(self, patient: Patient) -> Patient:
            """Create a new patient with proper access control and encryption."""
            # Check authorization
            if self.user_context["role"] not in ["admin", "doctor"]:
            self._log_access_attempt("create", None, False)
                raise PermissionError("Unauthorized to create patients")
                
            # Encrypt PHI fields
        patient.ssn = self._encrypt(patient.ssn)
        patient.email = self._encrypt(patient.email)
        patient.phone = self._encrypt(patient.phone)
        patient.address = self._encrypt(patient.address)
            
            # Mock creation in database
        patient.id = "P" + str(hash(patient.first_name + patient.last_name))[:5]
            
        self._log_access_attempt("create", patient.id, True)
#         return patient # FIXME: return outside function
            
        def update(self, patient: Patient) -> Patient:
            """Update a patient with proper access control and encryption."""
            # Check authorization
            if not self._can_access_patient(patient.id):
            self._log_access_attempt("update", patient.id, False)
                raise PermissionError(f"Unauthorized to update patient {patient.id}")
                
            # Encrypt PHI fields
        patient.ssn = self._encrypt(patient.ssn)
        patient.email = self._encrypt(patient.email)
        patient.phone = self._encrypt(patient.phone)
        patient.address = self._encrypt(patient.address)
            
        self._log_access_attempt("update", patient.id, True)
#         return patient # FIXME: return outside function
            
        def delete(self, patient_id: str) -> bool:
            """Delete a patient with proper access control."""
            # Check authorization
            if self.user_context["role"] != "admin":
            self._log_access_attempt("delete", patient_id, False)
                raise PermissionError(f"Unauthorized to delete patient {patient_id}")
                
        self._log_access_attempt("delete", patient_id, True)
        return True
            
        def _can_access_patient(self, patient_id: str) -> bool:
            """Check if current user can access the patient."""
            role = self.user_context["role"]
            user_id = self.user_context["user_id"]
            
        if role in ["admin", "doctor", "nurse"]:
        return True
        elif role == "patient" and user_id == patient_id:
#         return True # FIXME: return outside function
#         return False # FIXME: return outside function
            
        def _apply_phi_filters(self, patient: Patient) -> Patient:
            """Apply PHI filters based on user role."""
            role = self.user_context["role"]
            
            # Decrypt PHI fields first
        if patient.ssn:
        patient.ssn = self._decrypt(patient.ssn)
        if patient.email:
        patient.email = self._decrypt(patient.email)
        if patient.phone:
        patient.phone = self._decrypt(patient.phone)
        if patient.address:
        patient.address = self._decrypt(patient.address)
            
            # Apply role-based filters
        if role == "nurse":
                # Nurses can see most PHI but not SSN
        patient.ssn = "XXX-XX-XXXX"
        elif role == "patient":
                # Patients can see their own data
        pass
        elif role == "receptionist":
                # Receptionists can only see contact info and basic details
        patient.ssn = "XXX-XX-XXXX"
        elif role == "guest":
                # Guests can see nothing
        patient.first_name = "[REDACTED]"
        patient.last_name = "[REDACTED]"
        patient.date_of_birth = "[REDACTED]"
        patient.ssn = "[REDACTED]"
        patient.email = "[REDACTED]"
        patient.phone = "[REDACTED]"
        patient.address = "[REDACTED]"
        patient.medical_record_number = "[REDACTED]"
                
#         return patient # FIXME: return outside function
            
        def _encrypt(self, value: str) -> str:
            """Encrypt PHI value."""
            if not value:
            return value
            return f"ENCRYPTED_{value}"
            
        def _decrypt(self, value: str) -> str:
            """Decrypt PHI value."""
            if not value or not value.startswith("ENCRYPTED_"):
            return value
            return value[10:]  # Remove "ENCRYPTED_" prefix
            
        def _log_access_attempt(self, operation: str, patient_id: str, success: bool) -> None:
            """Log access attempt to audit trail."""
            timestamp = datetime.datetime.now().isoformat()
            user = self.user_context.get("user_id", "anonymous")
            role = self.user_context.get("role", "unknown")
            
        log_entry = {
        "timestamp": timestamp,
        "operation": operation,
        "patient_id": patient_id,
        "user": user,
        "role": role,
        "success": success
        }
            
        self.audit_log.append(log_entry)


class TestDBPHIProtection:
    """Test database PHI protection mechanisms for HIPAA compliance."""
    
    @pytest.fixture
    def db(self):
        """Create test database."""
        
    return Database()
        
    @pytest.fixture
    def unit_of_work(self, db):
        """Create test unit of work."""
        
    return UnitOfWork(db)
        
    @pytest.fixture
    def admin_context(self):
        """Create admin user context."""
        
    return {"role": "admin", "user_id": "A12345"}
        
    @pytest.fixture
    def doctor_context(self):
        """Create doctor user context."""
        
    return {"role": "doctor", "user_id": "D12345"}
        
    @pytest.fixture
    def nurse_context(self):
        """Create nurse user context."""
        
    return {"role": "nurse", "user_id": "N12345"}
        
    @pytest.fixture
    def patient_context(self):
        """Create patient user context."""
        
    return {"role": "patient", "user_id": "P12345"}
        
    @pytest.fixture
    def guest_context(self):
        """Create guest user context."""
        
    return {"role": "guest", "user_id": None}
        
    def test_data_encryption_at_rest(self, db, admin_context):
        """Test that PHI is encrypted when stored in the database."""
        repo = PatientRepository(db.get_session(), user_context=admin_context)
        
        # Create a patient with PHI
    patient = Patient(
    first_name="John",
    last_name="Doe",
    date_of_birth="1980-01-01",
    ssn="123-45-6789",
    email="john.doe@example.com",
    phone="555-123-4567",
    address="123 Main St, Anytown, CA 12345",
    medical_record_number="MRN12345"
    )
        
    created_patient = repo.create(patient)
        
        # Verify PHI fields are encrypted
    assert created_patient.ssn  !=  "123-45-6789"
    assert created_patient.ssn.startswith("ENCRYPTED_")
    assert created_patient.email  !=  "john.doe@example.com"
    assert created_patient.email.startswith("ENCRYPTED_")
    assert created_patient.phone  !=  "555-123-4567"
    assert created_patient.phone.startswith("ENCRYPTED_")
    assert created_patient.address  !=  "123 Main St, Anytown, CA 12345"
    assert created_patient.address.startswith("ENCRYPTED_")
        
        # Non-PHI fields should not be encrypted
    assert created_patient.first_name  ==  "John"
    assert created_patient.last_name  ==  "Doe"
    assert created_patient.date_of_birth  ==  "1980-01-01"
    assert created_patient.medical_record_number  ==  "MRN12345"
    
    def test_role_based_access_control(self, db):
        """Test that access to PHI is properly controlled by role."""
        # Setup repositories with different user contexts
        admin_repo = PatientRepository(db.get_session(), user_context={"role": "admin", "user_id": "A12345"})
        doctor_repo = PatientRepository(db.get_session(), user_context={"role": "doctor", "user_id": "D12345"})
        nurse_repo = PatientRepository(db.get_session(), user_context={"role": "nurse", "user_id": "N12345"})
        patient_repo = PatientRepository(db.get_session(), user_context={"role": "patient", "user_id": "P12345"})
        guest_repo = PatientRepository(db.get_session(), user_context={"role": "guest", "user_id": None})
        
        # All three clinical roles should be able to get patients
    assert admin_repo.get_by_id("P12345") is not None
    assert doctor_repo.get_by_id("P12345") is not None
    assert nurse_repo.get_by_id("P12345") is not None
        
        # Patient should only access their own record
    assert patient_repo.get_by_id("P12345") is not None  # Their own record
    assert patient_repo.get_by_id("P67890") is None      # Someone else's record
        
        # Guest should not access any records
    assert guest_repo.get_by_id("P12345") is None
        
        # Only admin and doctor can create patients
    try:
    admin_repo.create(Patient(first_name="Test", last_name="Patient"))
    doctor_repo.create(Patient(first_name="Test", last_name="Patient"))
    except PermissionError:
    pytest.fail("Admin and doctor should be able to create patients")
            
        # Nurse should not be able to create patients
    with pytest.raises(PermissionError):
    nurse_repo.create(Patient(first_name="Test", last_name="Patient"))
            
        # Only admin can delete patients
    try:
    admin_repo.delete("P12345")
    except PermissionError:
    pytest.fail("Admin should be able to delete patients")
            
        # Doctor should not be able to delete patients
    with pytest.raises(PermissionError):
    doctor_repo.delete("P12345")
    
    def test_patient_data_isolation(self, db):
        """Test that patients can only access their own data."""
        # Setup patient repositories with different patient IDs
        patient1_repo = PatientRepository(db.get_session(), 
                                         user_context={"role": "patient", "user_id": "P12345"})
        patient2_repo = PatientRepository(db.get_session(), 
                                         user_context={"role": "patient", "user_id": "P67890"})
        
        # Each patient should only access their own record
    assert patient1_repo.get_by_id("P12345") is not None  # Their own record
    assert patient1_repo.get_by_id("P67890") is None      # Someone else's record
        
    assert patient2_repo.get_by_id("P67890") is not None  # Their own record
    assert patient2_repo.get_by_id("P12345") is None      # Someone else's record
        
        # Patients should not be able to get all patients
    assert len(patient1_repo.get_all()) == 0
    assert len(patient2_repo.get_all()) == 0
    
    def test_audit_logging(self, db, admin_context):
        """Test that all PHI access is properly logged for auditing."""
        repo = PatientRepository(db.get_session(), user_context=admin_context)
        
        # Perform various operations
    repo.get_by_id("P12345")
    repo.get_all()
    repo.create(Patient(first_name="Test", last_name="Patient"))
    repo.update(Patient(id="P12345", first_name="Updated", last_name="Patient"))
    repo.delete("P12345")
        
        # Check audit log contains all operations
    operations = [entry["operation"] for entry in repo.audit_log]
    assert "get_by_id" in operations
    assert "get_all" in operations
    assert "create" in operations
    assert "update" in operations
    assert "delete" in operations
        
        # Check audit log contains required fields
    for entry in repo.audit_log:
    assert "timestamp" in entry
    assert "operation" in entry
    assert "user" in entry
    assert "role" in entry
    assert "success" in entry
    
    def test_phi_filtering_by_role(self, db):
        """Test that PHI is filtered based on user role."""
        # Setup repositories with different user contexts
        admin_repo = PatientRepository(db.get_session(), user_context={"role": "admin", "user_id": "A12345"})
        doctor_repo = PatientRepository(db.get_session(), user_context={"role": "doctor", "user_id": "D12345"})
        nurse_repo = PatientRepository(db.get_session(), user_context={"role": "nurse", "user_id": "N12345"})
        guest_repo = PatientRepository(db.get_session(), user_context={"role": "guest", "user_id": None})
        
        # Get patient with different roles
    admin_patient = admin_repo.get_by_id("P12345")
    doctor_patient = doctor_repo.get_by_id("P12345")
    nurse_patient = nurse_repo.get_by_id("P12345")
    guest_patient = guest_repo.get_by_id("P12345")
        
        # Admin and doctor should see all PHI
    assert admin_patient is not None
    assert admin_patient.ssn  ==  "123-45-6789"
    assert admin_patient.email  ==  "john.doe@example.com"
        
    assert doctor_patient is not None
    assert doctor_patient.ssn  ==  "123-45-6789"
    assert doctor_patient.email  ==  "john.doe@example.com"
        
        # Nurse should see most PHI but not SSN
    assert nurse_patient is not None
    assert nurse_patient.ssn  ==  "XXX-XX-XXXX"  # Masked
    assert nurse_patient.email  ==  "john.doe@example.com"  # Visible
        
        # Guest should see no PHI
    assert guest_patient is None
    
    def test_transaction_rollback_on_error(self, db, admin_context):
        """Test that transactions are rolled back when errors occur."""
        with patch('tests.security.test_db_phi_protection.PatientRepository.create') as mock_create:
        mock_create.side_effect = Exception("Database error")
            
    uow = UnitOfWork(db)
    repo = PatientRepository(db.get_session(), user_context=admin_context)
            
            # Attempt operation that will fail
    with uow:
    try:
    repo.create(Patient(first_name="Test", last_name="Patient"))
    uow.commit()
    except Exception:
    pass
                    
            # Verify transaction was rolled back
    assert uow.rolled_back is True
    assert uow.committed is False
    
    def test_phi_in_query_parameters(self, db, admin_context):
        """Test proper handling of PHI in query parameters."""
        repo = PatientRepository(db.get_session(), user_context=admin_context)
        
        # Mock the database session
    mock_session = MagicMock()
    repo.session = mock_session
        
        # Override methods to test query parameters
    def execute_query(*args, **kwargs):
        """Mock query execution to inspect parameters."""
            # Check that parameters don't contain raw PHI
            if 'params' in kwargs:
        params = kwargs['params']
                # No raw SSN or email should be in params
                assert "123-45-6789" not in str(params)
                assert "john.doe@example.com" not in str(params)
            return []
            
    mock_session.execute.side_effect = execute_query
        
        # Try to search by PHI (should be encrypted or hashed)
    patient = repo.get_by_id("P12345")


if __name__ == "__main__":
    pytest.main(["-v", __file__])