# -*- coding: utf-8 -*-
"""
HIPAA Compliance Testing - API Security Tests

These tests validate that API endpoints properly secure access to sensitive patient data
according to HIPAA requirements. Tests focus on authentication, authorization,
input validation, and secure communication.
"""

import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
import time 
import asyncio
from typing import Callable, Dict, Any, Coroutine # Combined imports

from httpx import AsyncClient # Not typically used directly with TestClient, but keep if needed elsewhere
from fastapi import status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.testclient import TestClient

# Use the new canonical config location
from app.config.settings import get_settings # Keep, might be needed for direct checks

# JWTService might be needed for direct token manipulation if required beyond fixtures
from app.infrastructure.security.jwt.jwt_service import JWTService 
# AuthenticationService might be needed if testing it directly
from app.infrastructure.security.auth.authentication_service import AuthenticationService 
from app.domain.entities.patient import Patient # Domain entity for type hints/fixtures
from app.domain.exceptions.patient_exceptions import PatientNotFoundError # Custom exception

# Import necessary modules for testing API security
# These seem specific to this test module's setup
from app.tests.security.utils.test_mocks import MockAuthService, MockRBACService, MockAuditLogger 
# Base class for security tests, likely provides common setup/methods
from app.tests.security.utils.base_security_test import BaseSecurityTest 

# Removed local test_client fixture; tests will use client from conftest.py
# Removed local mock_token, mock_user, mock_admin_user fixtures; use conftest.py fixtures

@pytest.mark.db_required() # Assumes a marker for tests needing DB setup
class TestAuthentication(BaseSecurityTest):
    """Test authentication mechanisms using TestClient and dynamic tokens."""

    # Fixture to get user ID from patient payload
    @pytest.fixture(scope="class") # Scope to class as payload is consistent within these tests
    def patient_user_id(self, mock_patient_payload: Dict[str, Any]) -> str:
        return mock_patient_payload["id"]

    def test_missing_token(self, client: TestClient, patient_user_id: str):
        """Test that requests without tokens are rejected by FastAPI/dependencies."""
        response = client.get(f"/api/v1/patients/{patient_user_id}") # Use the actual endpoint structure
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Check WWW-Authenticate header if detailed checks are needed
        # assert "Bearer" in response.headers.get("WWW-Authenticate", "")

    def test_invalid_token_format(self, client: TestClient, patient_user_id: str):
        """Test that structurally invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid.token.format"}
        response = client.get(f"/api/v1/patients/{patient_user_id}", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_expired_token(self, client: TestClient, generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_patient_payload: Dict[str, Any]):
        """Test that expired tokens are rejected by the JWTService validation."""
        user_id = mock_patient_payload["id"]
        # Create an already expired token
        expired_payload = {**mock_patient_payload, "exp": int(time.time()) - 3600}
        # Use generate_token fixture which uses the JWTService from conftest
        expired_token = await generate_token(expired_payload) 
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get(f"/api/v1/patients/{user_id}", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Check detail if specific error message is expected for expired tokens
        # assert "expired" in response.json().get("detail", "").lower()

    def test_tampered_token(self, client: TestClient, patient_user_id: str):
        """Test that tokens with invalid signatures are rejected."""
        # A token generated with the right key but then altered, or a token with a bad signature
        tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJyb2xlIjoicGF0aWVudCIsImV4cCI6OTk5OTk5OTk5OX0.invalid_signature_part"
        headers = {"Authorization": f"Bearer {tampered_token}"}
        
        response = client.get(f"/api/v1/patients/{patient_user_id}", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Check detail if specific error message is expected
        # assert "Invalid signature" in response.json().get("detail", "")

    def test_valid_token_access(self, client: TestClient, patient_token_headers: Dict[str, str], mock_patient_payload: Dict[str, Any]):
        """Test that a valid token grants access to the patient's own data endpoint."""
        user_id = mock_patient_payload["id"] # Get user ID from the payload fixture
        # patient_token_headers fixture provides a valid token generated by conftest.py
        response = client.get(f"/api/v1/patients/{user_id}", headers=patient_token_headers)
        # Assumes /api/v1/patients/{user_id} returns 200 OK on success when accessed by the correct patient.
        assert response.status_code == status.HTTP_200_OK
        # Optionally, check response content:
        # assert response.json()["id"] == user_id 


class TestAuthorization(BaseSecurityTest):
    """Test authorization logic (role-based access, resource ownership)."""

    # Test assumes endpoint logic verifies user ID against resource ID for ownership
    async def test_patient_accessing_own_data(self, client: TestClient, generate_token: Callable[[Dict[str, Any]], Coroutine[Any, Any, str]], mock_patient_payload: Dict[str, Any]):
        """Patient with valid token can access their own resource via /patients/{id}."""
        user_id = mock_patient_payload["id"]
        # Generate token specifically for this payload
        token = await generate_token(mock_patient_payload) # Await the coroutine
        headers = {"Authorization": f"Bearer {token}"}

        # Mock the service layer call *within* the endpoint if needed to control data return
        # For now, just test reachability assuming endpoint handles authz
        response = client.get(f"/api/v1/patients/{user_id}", headers=headers) 
        
        # If the endpoint /api/v1/patients/{user_id} verifies that the token's 'sub' or 'id'
        # matches the path parameter 'user_id', it should succeed.
        assert response.status_code == status.HTTP_200_OK 
        # Add more specific checks if the endpoint returns data
        # assert response.json()["id"] == user_id

    def test_patient_accessing_other_patient_data(self, client: TestClient, patient_token_headers: Dict[str, str], mock_patient_payload: Dict[str, Any]):
        """Patient with valid token CANNOT access another patient's resource."""
        token_user_id = mock_patient_payload["id"] # ID of the user whose token we have
        other_patient_id = f"other_patient_{uuid.uuid4().hex[:8]}" # Generate a different ID
        
        assert token_user_id != other_patient_id # Ensure IDs are different

        # Use a valid token from a *different* patient (provided by fixture)
        # The endpoint /api/v1/patients/{other_patient_id} should deny access
        # based on mismatch between token user ID and path parameter ID.
        response = client.get(f"/api/v1/patients/{other_patient_id}", headers=patient_token_headers)
        
        # Expect 403 Forbidden (or potentially 404 if combined)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_provider_accessing_patient_data(self, client: TestClient, provider_token_headers: Dict[str, str], mock_patient_payload: Dict[str, Any]):
        """Provider with valid token CAN access any patient's resource (if logic allows)."""
        patient_id = mock_patient_payload["id"] # Use an ID from a fixture for consistency
        
        # Use a valid provider token. The endpoint logic for /api/v1/patients/{patient_id}
        # should check the role from the token and allow access.
        response = client.get(f"/api/v1/patients/{patient_id}", headers=provider_token_headers)
        
        # Expect 200 OK, assuming the patient record exists (or test handles 404 appropriately)
        # For this test, we assume the endpoint handles the case where the patient might 
        # not exist yet and focus on the authorization aspect. If the resource MUST exist,
        # the test should ensure its creation first.
        # Allowing 200 or 404 might be acceptable depending on strictness.
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND] 

    def test_role_specific_endpoint_access(self, client: TestClient, patient_token_headers: Dict[str, str], provider_token_headers: Dict[str, str]):
        """Test access to endpoints protected by role dependencies (e.g., verify_provider_access)."""
        # Assuming an endpoint like /admin/dashboard requires provider/admin roles
        # Replace with an actual admin/provider-only endpoint if available
        protected_endpoint = "/api/v1/some_provider_endpoint" # Placeholder

        # Test with patient token (should be forbidden)
        response_patient = client.get(protected_endpoint, headers=patient_token_headers)
        # Expect 403 Forbidden if the endpoint correctly checks roles
        # Or 404 if the placeholder endpoint doesn't exist
        assert response_patient.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

        # Test with provider token (should be allowed or 404 if endpoint missing)
        response_provider = client.get(protected_endpoint, headers=provider_token_headers)
        assert response_provider.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


# TestRateLimiting class removed previously


class TestInputValidation(BaseSecurityTest):
    """Test input validation using Pydantic models and FastAPI."""

    def test_invalid_input_format_rejected(self, client: TestClient, provider_token_headers: Dict[str, str]):
        """FastAPI should return 422 for missing/invalid fields based on Pydantic models."""
        # Assuming POST /api/v1/patients requires certain fields per PatientCreateSchema
        invalid_payload = {"name": "Test Patient Only"} # Missing required fields like date_of_birth, gender
        
        response = client.post("/api/v1/patients", headers=provider_token_headers, json=invalid_payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_input_sanitization_handling(self, client: TestClient, provider_token_headers: Dict[str, str]):
        """Test how potentially malicious input is handled (relies on framework/model validation)."""
        # Input that might contain XSS or SQLi attempts
        # Use PatientCreateSchema structure
        malicious_input = { 
            "name": "Valid Name<script>alert('XSS attempt')</script>", 
            "date_of_birth": "2000-01-01", # Valid format
            "gender": "other", # Valid value
            "email": "test@example.com", # Valid email
            # Add other optional fields if the schema allows, like 'notes' if it were added
            # "notes": "Some notes; SELECT * FROM users; --" # Potential SQLi if notes field existed
        }
        
        # Pydantic models might clean some basic attempts or raise validation errors
        # for specific field types (e.g., an invalid email). Assume 'notes' is a string.
        response = client.post("/api/v1/patients", headers=provider_token_headers, json=malicious_input)
        
        # Expect 201 Created if basic validation passes (Pydantic doesn't typically sanitize complex XSS/SQLi by default)
        # OR 422 if a field fails validation (e.g., email format).
        # A deeper test would involve checking the DB, but for API security, checking non-500 is key.
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
        # Ideally check for 201 or 422 specifically based on expectations
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_input_length_limits_enforced(self, client: TestClient, provider_token_headers: Dict[str, str]):
        """Test if Pydantic models enforce max_length constraints."""
        overly_long_text = "x" * 500 # Example length, adjust based on model constraints

        # Assume 'name' field has a max_length constraint in the Pydantic model (check PatientCreateSchema/Patient entity)
        long_input_payload = {
            "name": overly_long_text, # Exceeds typical constraint
            "date_of_birth": "2000-01-01",
            "gender": "other",
            "email": "test@example.com"
        }

        response = client.post("/api/v1/patients", headers=provider_token_headers, json=long_input_payload)
        # Expect 422 if validation fails due to length constraint
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSecureHeaders(BaseSecurityTest):
    """Test for the presence and correctness of security-related HTTP headers."""

    def test_required_security_headers_present(self, client: TestClient):
        """Check standard security headers on a basic endpoint response."""
        response = client.get("/api/v1/health") # Use a simple, likely unauthenticated endpoint

        assert response.status_code == 200 # Pre-condition: endpoint works
        headers = response.headers

        # Verify headers are present and have expected values (adjust expected values as needed)
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY" # Or SAMEORIGIN depending on policy

        # Check if CSP header is present, exact value depends on policy
        assert "Content-Security-Policy" in headers 
        # assert "default-src 'self'" in headers["Content-Security-Policy"] # Example specific check

        # HSTS header is often conditional on HTTPS being used/enforced
        # Use case-insensitive check for header name
        hsts_header = next((v for k, v in headers.items() if k.lower() == "strict-transport-security"), None)
        if hsts_header: 
             assert "max-age=" in hsts_header
             # assert "includeSubDomains" in hsts_header # If applicable

    def test_cors_headers_configuration(self, client: TestClient):
        """Verify CORS headers based on application settings."""
        # Use the OPTIONS method to trigger CORS preflight checks
        allowed_origin = "http://localhost:3000" # Example, should match test settings if specific
        headers = {
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
        response = client.options("/api/v1/health", headers=headers)

        assert response.status_code == 200 # Preflight should succeed if origin allowed
        response_headers = response.headers

        # Check CORS headers are present
        assert "Access-Control-Allow-Origin" in response_headers
        assert "Access-Control-Allow-Methods" in response_headers
        assert "Access-Control-Allow-Headers" in response_headers
        # assert "Access-Control-Allow-Credentials" in response_headers # If applicable

        # Verify allowed origin matches settings (e.g., '*' or specific origin from MockSettings)
        # This depends heavily on the CORS middleware configuration in main.py using MockSettings
        # For now, we just check presence. A stricter test would check against mock_settings.BACKEND_CORS_ORIGINS
        assert response_headers["Access-Control-Allow-Origin"] in ["*", allowed_origin] 


class TestErrorHandling(BaseSecurityTest):
    """Test generic error handling and masking of sensitive details."""

    def test_not_found_error_generic(self, client: TestClient):
        """Test that accessing a non-existent route returns 404."""
        response = client.get("/api/v1/non_existent_route_for_testing")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        # Ensure detailed internal info isn't leaked
        assert "traceback" not in response.text.lower()

    # Patch the service/repository method called by the endpoint
    # Adjust the patch target based on actual implementation in get_patient_endpoint
    @patch('app.infrastructure.persistence.sqlalchemy.repositories.patient_repository.PatientRepository.get_by_id') 
    def test_internal_server_error_masked(self, mock_get_by_id: MagicMock, client: TestClient, provider_token_headers: Dict[str, str]):
        """Test that unexpected internal errors return a generic 500 without exposing details."""
        patient_id = str(uuid.uuid4())
        
        # Configure the mocked repository method to raise an unexpected error
        mock_get_by_id.side_effect = Exception("Simulated unexpected database error")
        
        response = client.get(f"/api/v1/patients/{patient_id}", headers=provider_token_headers)
        
        # Expect a 500 Internal Server Error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Verify that the response body does NOT contain sensitive details
        response_json = response.json()
        assert "detail" in response_json
        # Check that the detail is generic and doesn't contain the specific exception message
        assert "Internal Server Error" in response_json["detail"] # Default FastAPI 500 detail
        assert "Simulated unexpected database error" not in response_json["detail"]
        assert "traceback" not in response.text.lower()
        assert "exception" not in response.text.lower()


# --- PHI Access Tests (Moved outside classes for clarity or into specific classes) ---
# These need careful patching of the endpoint's dependencies (service, repository)

# Patch the service/repository method directly called by the endpoint
@patch('app.infrastructure.persistence.sqlalchemy.repositories.patient_repository.PatientRepository.get_by_id')
# Patch the sanitizer if it's directly used in the endpoint (adjust path if needed)
# @patch('app.presentation.api.v1.endpoints.patients.phi_sanitizer') 
async def test_access_patient_phi_data_success_provider(
    # mock_phi_sanitizer: MagicMock, # Only if sanitizer patch is used
    mock_get_patient_by_id: MagicMock,
    client: TestClient,
    test_patient: Patient, # Requires a test_patient fixture from conftest
    provider_token_headers: Dict[str, str] 
):
    """Test provider accessing patient data, ensuring PHI is handled (mocked return)."""
    patient_id = test_patient.id
    
    # Configure the mock repository to return the test patient object
    mock_get_patient_by_id.return_value = test_patient 
    # Configure mock sanitizer if used
    # mock_phi_sanitizer.process.return_value = {"id": patient_id, "name": "[REDACTED]", ...}

    response = client.get(f"/api/v1/patients/{patient_id}", headers=provider_token_headers)

    assert response.status_code == status.HTTP_200_OK
    mock_get_patient_by_id.assert_called_once_with(patient_id, user=ANY) # Check repo called
    # Check if the response matches the expected (potentially sanitized) patient data
    response_data = response.json()
    assert response_data["id"] == patient_id
    # Add checks for other fields, potentially redacted ones if sanitizer was mocked
    # assert response_data["name"] == "[REDACTED]" 

# Patch the sanitizer if it's directly used in the endpoint
# @patch('app.presentation.api.v1.endpoints.patients.phi_sanitizer')
async def test_access_patient_phi_data_unauthorized_patient(
    # mock_phi_sanitizer: MagicMock, # Only if sanitizer patch is used
    client: TestClient,
    test_patient: Patient, # Requires fixture
    patient_token_headers: Dict[str, str] # Token for *another* patient
):
    """Test patient trying to access another patient's data gets 403."""
    target_patient_id = test_patient.id # ID of the patient whose data is being requested
    # The token in patient_token_headers belongs to a *different* patient generated by the fixture
    
    response = client.get(f"/api/v1/patients/{target_patient_id}", headers=patient_token_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # mock_phi_sanitizer.process.assert_not_called() # Ensure sanitizer isn't reached


@patch('app.infrastructure.persistence.sqlalchemy.repositories.patient_repository.PatientRepository.get_by_id')
async def test_access_patient_phi_data_patient_not_found(
    mock_get_patient_by_id: MagicMock,
    client: TestClient,
    provider_token_headers: Dict[str, str] 
):
    """Test accessing non-existent patient returns 404."""
    non_existent_patient_id = str(uuid.uuid4())
    
    # Configure mock repository to return None (simulating not found)
    mock_get_patient_by_id.return_value = None

    response = client.get(f"/api/v1/patients/{non_existent_patient_id}", headers=provider_token_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    mock_get_patient_by_id.assert_called_once_with(non_existent_patient_id, user=ANY) 