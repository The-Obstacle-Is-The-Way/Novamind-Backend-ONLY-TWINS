# -*- coding: utf-8 -*-
"""
Security Test Fixtures
=====================

This module provides pytest fixtures for testing HIPAA security and compliance features.
These fixtures create mock data, authentication credentials, and contexts that are
specifically designed for testing security controls like PHI redaction, encryption,
and access control.
"""

import os
import uuid
import json
import pytest
import datetime
from typing import Dict, Any, List, Generator, Optional
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

# Import application components
# (paths would be adjusted to your actual application structure)

# ==== Mock PHI Data for Testing ====

@pytest.fixture
def mock_patient_phi_data() -> Dict[str, Any]:
    """
    Create mock patient PHI data for testing.
    
    Contains realistic but fake PHI that should be properly redacted or secured
    during tests. None of this data belongs to real individuals.
    """
    return {
        "id": "PT10001",
        "mrn": "MRN78901234",
        "name": "John Doe",
        "dob": "1980-01-15",
        "ssn": "123-45-6789",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "90210"
        },
        "insurance": {
            "provider": "Blue Cross",
            "policy_number": "BCBS123456789",
            "group_number": "GRP987654"
        },
        "medical_history": [
            {
                "diagnosis": "Major Depressive Disorder",
                "date_diagnosed": "2020-03-10",
                "treating_physician": "Dr. Jane Smith"
            },
            {
                "diagnosis": "Generalized Anxiety Disorder",
                "date_diagnosed": "2020-03-10", 
                "treating_physician": "Dr. Jane Smith"
            }
        ],
        "medications": [
            {
                "name": "Fluoxetine",
                "dosage": "20mg",
                "frequency": "Daily",
                "prescribed_by": "Dr. Jane Smith",
                "date_prescribed": "2020-03-15"
            }
        ]
    }


@pytest.fixture
def mock_appointment_data(mock_patient_phi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create mock appointment data with PHI references.
    
    This fixture creates appointment data that contains references to patient PHI,
    which should be properly handled during testing.
    """
    return {
        "id": "APT50001",
        "patient_id": mock_patient_phi_data["id"],
        "patient_name": mock_patient_phi_data["name"],
        "provider_id": "PROV123",
        "provider_name": "Dr. Jane Smith",
        "date": "2023-12-15",
        "time": "14:30",
        "duration_minutes": 50,
        "appointment_type": "Medication Management",
        "status": "Scheduled",
        "notes": f"Follow-up with {mock_patient_phi_data['name']} regarding medication efficacy.",
        "insurance_verification": {
            "verified": True,
            "insurance_id": mock_patient_phi_data["insurance"]["policy_number"],
            "copay": 25.00
        }
    }


@pytest.fixture
def mock_clinical_note_data(mock_patient_phi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create mock clinical note with PHI content for testing.
    
    This fixture creates a realistic clinical note containing PHI that should
    be properly secured or redacted during testing.
    """
    return {
        "id": "NOTE10001",
        "patient_id": mock_patient_phi_data["id"],
        "provider_id": "PROV123",
        "date": "2023-12-01",
        "title": f"Therapy Session - {mock_patient_phi_data['name']}",
        "content": f"""
            Patient: {mock_patient_phi_data['name']} (DOB: {mock_patient_phi_data['dob']})
            
            Subjective:
            Patient reports continued difficulty sleeping and persistent worry.
            States that current medication is "helping somewhat" but still experiencing
            breakthrough anxiety. Denies suicidal ideation.
            
            Patient can be reached at {mock_patient_phi_data['phone']} for follow-up.
            
            Objective:
            Patient appears alert and oriented. Affect congruent with reported mood.
            No evidence of psychosis or thought disorder.
            
            Assessment:
            Generalized Anxiety Disorder, moderate severity.
            Major Depressive Disorder, mild, partially responsive to treatment.
            
            Plan:
            1. Continue Fluoxetine 20mg daily
            2. Add Hydroxyzine 25mg as needed for breakthrough anxiety
            3. Schedule follow-up in 3 weeks
            4. Patient provided with crisis resources
            
            Electronically signed by: Dr. Jane Smith
        """,
        "tags": ["anxiety", "depression", "medication management"],
        "status": "signed",
        "version": 1
    }


# ==== Authentication & Authorization Fixtures ====

class MockUser:
    """Mock user class for testing authentication."""
    
    def __init__(self, id: str, role: str, name: str):
        self.id = id
        self.role = role
        self.name = name
        self.permissions = self._get_permissions_for_role(role)
    
    def _get_permissions_for_role(self, role: str) -> List[str]:
        """Get permissions based on user role."""
        permissions = {
            "patient": ["read:own_records", "create:appointment", "update:own_profile"],
            "provider": ["read:patient_records", "create:clinical_note", "update:appointment"],
            "admin": ["read:all_records", "create:user", "update:system_settings", "delete:records"]
        }
        return permissions.get(role, [])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions


@pytest.fixture
def mock_patient_user() -> MockUser:
    """Create a mock patient user for testing."""
    return MockUser(
        id="user-patient-123",
        role="patient",
        name="John Doe"
    )


@pytest.fixture
def mock_provider_user() -> MockUser:
    """Create a mock provider user for testing."""
    return MockUser(
        id="user-provider-456",
        role="provider",
        name="Dr. Jane Smith"
    )


@pytest.fixture
def mock_admin_user() -> MockUser:
    """Create a mock admin user for testing."""
    return MockUser(
        id="user-admin-789",
        role="admin",
        name="Admin User"
    )


@pytest.fixture
def mock_jwt_token(request, mock_patient_user: MockUser) -> str:
    """
    Create a mock JWT token for testing authentication.
    
    This fixture creates a mock JWT token with claims that reflect the user type.
    The token is not actually valid for cryptographic verification - it's a mock
    for testing purposes only.
    
    Usage:
        @pytest.mark.parametrize('mock_jwt_token', ['patient'], indirect=True)
        def test_with_patient_token(mock_jwt_token):
            # Test with a patient token
    """
    user_type = getattr(request, "param", "patient")
    user_map = {
        "patient": mock_patient_user,
        "provider": mock_provider_user,
        "admin": mock_admin_user
    }
    
    user = user_map.get(user_type, mock_patient_user)
    
    # This is a mock token, not a real JWT
    return f"mockedtoken.{user.id}.{user.role}"


# ==== Test Client & Application Fixtures ====

@pytest.fixture
def test_app() -> FastAPI:
    """
    Create a test FastAPI application with all middleware and routes.
    
    This fixture sets up a FastAPI application with all security middleware
    and routes for testing, but uses test configurations.
    """
    # This would normally import your actual app factory
    # but for now we'll create a simple test app
    from fastapi import FastAPI, Depends, HTTPException, status
    
    app = FastAPI(title="Test HIPAA Compliant API")
    
    # Add security middleware (in a real app, this would be imported)
    @app.middleware("http")
    async def mock_phi_middleware(request, call_next):
        response = await call_next(request)
        return response
    
    # Add some test routes with security
    @app.get("/api/public")
    def public_endpoint():
        return {"status": "public endpoint"}
    
    @app.get("/api/protected")
    def protected_endpoint(token: str = Depends(lambda: None)):
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return {"status": "protected endpoint"}
    
    @app.get("/api/patient/{patient_id}")
    def get_patient_data(patient_id: str, token: str = Depends(lambda: None)):
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return {"id": patient_id, "name": "Test Patient", "phi": "This should be redacted"}
    
    return app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """Create a TestClient for making test requests."""
    return TestClient(test_app)


@pytest.fixture
def authenticated_client(test_app: FastAPI, mock_jwt_token: str) -> TestClient:
    """Create an authenticated TestClient with a mock JWT token."""
    client = TestClient(test_app)
    client.headers = {
        "Authorization": f"Bearer {mock_jwt_token}"
    }
    return client


# ==== Encryption & Security Testing Fixtures ====

@pytest.fixture
def mock_encryption_service():
    """
    Create a mock encryption service for testing secure data handling.
    
    This fixture provides a mock implementation of encryption/decryption
    functionality for testing security features without using real cryptography.
    """
    class MockEncryptionService:
        def encrypt(self, plaintext: str) -> str:
            """Mock encryption that just wraps text."""
            return f"ENCRYPTED({plaintext})"
        
        def decrypt(self, ciphertext: str) -> str:
            """Mock decryption that unwraps text."""
            if ciphertext.startswith("ENCRYPTED(") and ciphertext.endswith(")"):
                return ciphertext[10:-1]
            return ciphertext
    
    return MockEncryptionService()


@pytest.fixture
def mock_phi_detector():
    """
    Create a mock PHI detector for testing PHI identification.
    
    This fixture provides a mock implementation of PHI detection 
    that can be used in tests to verify PHI handling logic.
    """
    class MockPHIDetector:
        def __init__(self):
            self.phi_patterns = {
                "SSN": r"\d{3}-\d{2}-\d{4}",
                "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                "Phone": r"\(\d{3}\)\s*\d{3}-\d{4}",
                "DOB": r"\d{4}-\d{2}-\d{2}"
            }
        
        def contains_phi(self, text: str) -> bool:
            """Check if text contains PHI based on patterns."""
            import re
            for pattern in self.phi_patterns.values():
                if re.search(pattern, text):
                    return True
            return False
        
        def redact_phi(self, text: str) -> str:
            """Redact PHI in text with [REDACTED]."""
            import re
            result = text
            for name, pattern in self.phi_patterns.items():
                result = re.sub(pattern, "[REDACTED]", result)
            return result
    
    return MockPHIDetector()


# ==== Database & Repository Testing Fixtures ====

@pytest.fixture
def mock_patient_repository(mock_patient_phi_data: Dict[str, Any]):
    """
    Create a mock patient repository for testing data access controls.
    
    This fixture provides a mock implementation of a patient repository
    that can be used to test access controls and PHI handling.
    """
    class MockPatientRepository:
        def __init__(self):
            self.patients = {
                mock_patient_phi_data["id"]: mock_patient_phi_data
            }
        
        async def get_by_id(self, id: str, user: Optional[MockUser] = None) -> Dict[str, Any]:
            """Get patient by ID with access control."""
            if user and user.role not in ["provider", "admin"] and user.id != f"user-patient-{id}":
                raise PermissionError("Not authorized to access this patient record")
            
            patient = self.patients.get(id)
            if not patient:
                return None
            
            return patient.copy()
        
        async def create(self, patient_data: Dict[str, Any], user: Optional[MockUser] = None) -> Dict[str, Any]:
            """Create a new patient with access control."""
            if user and user.role not in ["provider", "admin"]:
                raise PermissionError("Not authorized to create patient records")
            
            patient_id = patient_data.get("id", f"PT{str(uuid.uuid4())[:8]}")
            self.patients[patient_id] = patient_data
            return self.patients[patient_id].copy()
    
    return MockPatientRepository()


@pytest.fixture
def mock_audit_logger():
    """
    Create a mock audit logger for testing logging of PHI access.
    
    This fixture provides a mock implementation of an audit logger
    that can be used to verify proper logging of PHI access attempts.
    """
    class MockAuditLogger:
        def __init__(self):
            self.logs = []
        
        def log_access(self, user_id: str, resource_type: str, resource_id: str, 
                       action: str, success: bool, details: str = None):
            """Log an access attempt to a protected resource."""
            self.logs.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "success": success,
                "details": details
            })
            
        def get_logs(self) -> List[Dict[str, Any]]:
            """Get all recorded audit logs."""
            return self.logs.copy()
    
    return MockAuditLogger()


# ==== HIPAA Compliance Testing Fixtures ====

@pytest.fixture
def hipaa_security_rule_requirements() -> Dict[str, List[str]]:
    """
    Provide a list of HIPAA Security Rule requirements for testing compliance.
    
    This fixture returns key HIPAA Security Rule requirements organized by category,
    which can be used in tests to validate compliance features.
    """
    return {
        "administrative_safeguards": [
            "Security Management Process",
            "Assigned Security Responsibility",
            "Workforce Security",
            "Information Access Management",
            "Security Awareness and Training",
            "Security Incident Procedures",
            "Contingency Plan",
            "Evaluation"
        ],
        "physical_safeguards": [
            "Facility Access Controls",
            "Workstation Use",
            "Workstation Security",
            "Device and Media Controls"
        ],
        "technical_safeguards": [
            "Access Control",
            "Audit Controls",
            "Integrity",
            "Person or Entity Authentication",
            "Transmission Security"
        ],
        "organizational_requirements": [
            "Business Associate Contracts",
            "Requirements for Group Health Plans"
        ],
        "policies_procedures_documentation": [
            "Policies and Procedures",
            "Documentation"
        ]
    }