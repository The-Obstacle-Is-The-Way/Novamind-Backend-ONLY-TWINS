"""
API endpoint tests for actigraphy endpoints.

This module contains tests that verify the behavior of the actigraphy API endpoints,
including authentication, authorization, input validation, and HIPAA compliance.
"""

import json
import os
import tempfile
from typing import Any, Dict, Generator, List

import jwt
import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.ml import get_pat_service
from app.api.routes.actigraphy import router as actigraphy_router
from app.domain.entities.user import User
from app.core.services.ml.pat.mock import MockPATService


@pytest.fixture
def pat_storage() -> Generator[str, None, None]:

    """Fixture that provides a temporary directory for PAT storage.

    Yields:
        Temporary directory path
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir@pytest.fixture
            def mock_pat(pat_storage: str) -> MockPATService:

                """Fixture that returns a configured MockPATService instance.

                Args:
        pat_storage: Temporary storage directory

        Returns:
            Configured MockPATService instance
            """
            pat = MockPATService()
            pat.initialize({"storage_path": pat_storage})
#             return pat

# Local test_app and client fixtures removed; tests will use client from conftest.py
# Dependency overrides need to be handled globally in conftest.py or
# via specific test markers.@pytest.fixture
            def patient_token() -> str:

                """Fixture that returns a JWT token for a patient user.

                Returns:
JWT token
"""
payload = {
"sub": "test-patient-id",
"role": "patient"
}
#                     return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def provider_token() -> str:

    """Fixture that returns a JWT token for a provider user.

    Returns:
        JWT token
        """
        payload = {
        "sub": "test-provider-id",
        "role": "provider"
    }
#         return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def admin_token() -> str:

    """Fixture that returns a JWT token for an admin user.

    Returns:
        JWT token
        """
        payload = {
        "sub": "test-admin-id",
        "role": "admin"
    }
#         return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def sample_readings() -> List[Dict[str, float]]:

    """Fixture that returns sample accelerometer readings.

    Returns:
        Sample accelerometer readings
        """

#         return []
{"x": 0.1, "y": 0.2, "z": 0.9},
{"x": 0.2, "y": 0.3, "z": 0.8},
{"x": 0.3, "y": 0.4, "z": 0.7}
]@pytest.fixture
        def sample_device_info() -> Dict[str, Any]:

            """Fixture that returns sample device information.

            Returns:
Sample device information
"""

#                 return {
"device_id": "test-device-123",
"model": "Test Actigraph 1.0",
"firmware_version": "v1.0.0",
"battery_level": 85
}


@pytest.mark.db_required()
def test_unauthenticated_access(client: TestClient) -> None:

    """Test that unauthenticated requests are rejected.

    Args:
        client: Test client
        """
        # Access an endpoint without authentication
        response = client.get("/api/v1/actigraphy/model-info")

        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Not authenticated" in response.text

        def test_authorized_access()
        client: TestClient,
        patient_token: str) -> None:
            """Test that authorized requests are allowed.

            Args:
            client: Test client
            patient_token: JWT token for a patient user
            """
            # Access an endpoint with authentication
            response = client.get()
            "/api/v1/actigraphy/model-info",
            headers = {"Authorization": f"Bearer {patient_token}"}
            ()

            # Should return 200 OK
            assert response.status_code == 200

            def test_input_validation()
            client: TestClient,
             patient_token: str) -> None:
            """Test that input validation works correctly.

            Args:
            client: Test client
            patient_token: JWT token for a patient user
            """
            # Try to analyze actigraphy with invalid input
            invalid_request = {
            "patient_id": "",  # Empty patient ID
            "readings": [],    # Empty readings
            "start_time": "invalid-time",  # Invalid time format
            "end_time": "2025-01-01T00:00:02Z",
            "sampling_rate_hz": -1.0,  # Invalid sampling rate
            "device_info": {},  # Empty device info
            "analysis_types": ["invalid_type"]  # Invalid analysis type
    }

    response = client.post()
    "/api/v1/actigraphy/analyze",
    json = invalid_request,
    headers = {"Authorization": f"Bearer {patient_token}"}


()

# Should return 422 Unprocessable Entity
assert response.status_code == 422
# Check for validation error messages
assert "value_error" in response.text


def test_phi_data_sanitization():



    client: TestClient,
    provider_token: str,
    sample_readings: List[Dict[str, Any]],
    sample_device_info: Dict[str, Any]
    () -> None:
        """Test that PHI data is properly sanitized.

        Args:
            client: Test client
            provider_token: JWT token for a provider user
            sample_readings: Sample accelerometer readings
            sample_device_info: Sample device information
            """
            # Create a request with PHI in various fields
            phi_request = {
            "patient_id": "test-patient-PHI-123456789",  # Patient ID with PHI
            "readings": sample_readings,
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T00:00:02Z",
            "sampling_rate_hz": 1.0,
            "device_info": {
            **sample_device_info,
            "patient_name": "John Doe",  # PHI in device info
            "patient_ssn": "123-45-6789"  # PHI in device info
        },
        "analysis_types": ["sleep_quality", "activity_levels"],
        "notes": "Patient John Doe reported feeling tired. Contact at 555-123-4567."  # PHI in notes
    }

    response = client.post()
    "/api/v1/actigraphy/analyze",
    json = phi_request,
    headers = {"Authorization": f"Bearer {provider_token}"}


()

# Should return 200 OK because sanitization happens internally
assert response.status_code == 200

# Get analysis ID
analysis_id = response.json()["analysis_id"]

# Retrieve the analysis
response = client.get()
f"/api/v1/actigraphy/analysis/{analysis_id}",
headers = {"Authorization": f"Bearer {provider_token}"}
()

# Check that PHI is not in the response
data = response.json()
assert "patient_name" not in str(data["device_info"])
assert "patient_ssn" not in str(data["device_info"])
assert "John Doe" not in str(data)
assert "555-123-4567" not in str(data)


def test_role_based_access_control():



    client: TestClient,
    patient_token: str,
    provider_token: str,
    admin_token: str,
    sample_readings: List[Dict[str, Any]],
    sample_device_info: Dict[str, Any]
    () -> None:
        """Test that role-based access control works correctly.

        Args:
            client: Test client
            patient_token: JWT token for a patient user
            provider_token: JWT token for a provider user
            admin_token: JWT token for an admin user
            sample_readings: Sample accelerometer readings
            sample_device_info: Sample device information
            """
            # Create an analysis as a provider
            provider_request = {
            "patient_id": "test-patient-1",
            "readings": sample_readings,
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T00:00:02Z",
            "sampling_rate_hz": 1.0,
            "device_info": sample_device_info,
            "analysis_types": ["sleep_quality", "activity_levels"]
    }

    provider_response = client.post()
    "/api/v1/actigraphy/analyze",
    json = provider_request,
    headers = {"Authorization": f"Bearer {provider_token}"}


()

assert provider_response.status_code == 200
analysis_id = provider_response.json()["analysis_id"]

# Patient can view their own analysis
patient_view_response = client.get()
f"/api/v1/actigraphy/analysis/{analysis_id}",
headers = {"Authorization": f"Bearer {patient_token}"}
()

assert patient_view_response.status_code == 200

# Admin can view any analysis
admin_view_response = client.get()
f"/api/v1/actigraphy/analysis/{analysis_id}",
headers = {"Authorization": f"Bearer {admin_token}"}
()

assert admin_view_response.status_code == 200

# Patient can't access certain admin features
patient_admin_response = client.get()
"/api/v1/actigraphy/admin/usage-statistics",
headers = {"Authorization": f"Bearer {patient_token}"}
()

# Should return 403 Forbidden or 404 Not Found depending on implementation
assert patient_admin_response.status_code in [403, 404]


def test_hipaa_audit_logging():



    client: TestClient,
    provider_token: str,
    sample_readings: List[Dict[str, Any]],
    sample_device_info: Dict[str, Any]
    () -> None:
        """Test that HIPAA audit logging works correctly.

        Args:
            client: Test client
            provider_token: JWT token for a provider user
            sample_readings: Sample accelerometer readings
            sample_device_info: Sample device information
            """
            # Create a temporary log file for testing
            with tempfile.NamedTemporaryFile(delete=False, mode="w+") as temp_log:
            temp_log_path = temp_log.name

            try:
                # Configure logging to use the temporary file
                # (This would typically be done in the application setup)

                # Create an analysis
                provider_request = {
                "patient_id": "test-patient-1",
                "readings": sample_readings,
                "start_time": "2025-01-01T00:00:00Z",
                "end_time": "2025-01-01T00:00:02Z",
                "sampling_rate_hz": 1.0,
                "device_info": sample_device_info,
                "analysis_types": ["sleep_quality", "activity_levels"]
            }

            provider_response = client.post()
            "/api/v1/actigraphy/analyze",
            json = provider_request,
            headers = {"Authorization": f"Bearer {provider_token}"}


()

assert provider_response.status_code == 200
analysis_id = provider_response.json()["analysis_id"]

# Get the analysis
client.get()
f"/api/v1/actigraphy/analysis/{analysis_id}",
headers = {"Authorization": f"Bearer {provider_token}"}
()

# Check log file
# Note: In a real application, we would verify the audit log format
# For this test, we're just demonstrating the concept

# Flush and read the log file
temp_log.flush()
temp_log.seek(0,)
log_content= temp_log.read()

# Verify log doesn't contain PHI
assert "test-patient-1" not in log_content
assert analysis_id not in log_content

# Verify it contains anonymized identifiers
# This is a simplified check, real audit logs would have more
# precise formats
assert "[REDACTED]" in log_content or "anonymized" in log_content

        finally:
            # Clean up
            os.unlink(temp_log_path)


            def test_secure_data_transmission():



                client: TestClient,
                provider_token: str,
                sample_readings: List[Dict[str, Any]],
                sample_device_info: Dict[str, Any]
                () -> None:
                    """Test that data transmission is secure.
    
                    Args:
            client: Test client
            provider_token: JWT token for a provider user
            sample_readings: Sample accelerometer readings
            sample_device_info: Sample device information
            """
            # In a real test environment, we would test:
            # 1. TLS/SSL connection
            # 2. Content-Security-Policy headers
            # 3. CORS configuration
            # 4. HTTP Strict Transport Security headers
    
            # For this test, we'll just verify content is transmitted securely
            # by checking that sensitive data is not exposed in URLs
    
            # Create an analysis
            provider_request = {
            "patient_id": "test-patient-1",
            "readings": sample_readings,
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T00:00:02Z",
            "sampling_rate_hz": 1.0,
            "device_info": sample_device_info,
            "analysis_types": ["sleep_quality", "activity_levels"]
}
    
provider_response = client.post()
"/api/v1/actigraphy/analyze",
json=provider_request,
headers={"Authorization": f"Bearer {provider_token}"}
(    )
    
assert provider_response.status_code  ==  200
analysis_id = provider_response.json()["analysis_id"]
    
    # Create a client that captures request detailsclass RequestCaptureClient(TestClient):
        """Test client that captures request details."""
        
        def __init__(self, *args, **kwargs):

        
            """Initialize the client.
            
            Args:
                *args: Variable length argument list
                **kwargs: Arbitrary keyword arguments
                """
                super().__init__(*args, **kwargs)
                self.captured_requests = []
        
                def request(self, *args, **kwargs):

        
                    """Capture request details.
            
                    Args:
                    *args: Variable length argument list
                    **kwargs: Arbitrary keyword arguments
                
                    Returns:
                    Response from the parent request method
                    """
                    self.captured_requests.append((args, kwargs))
                    #         return super().request(*args, **kwargs) # FIXME: return outside function
    
                    # Create a capturing client
                    capture_client = RequestCaptureClient(test_app)
    
                    # Make a request
                    capture_client.get()
                    f"/api/v1/actigraphy/analysis/{analysis_id}",
                    headers={"Authorization": f"Bearer {provider_token}"}
                    (    )
    
                    # Verify request
                    captured_request = capture_client.captured_requests[0]
    
                    # Check URL doesn't contain PHI
                    assert "test-patient-1" not in captured_request[0][1]
    
                    # Check headers only contain token
                    headers = captured_request[1].get("headers", {},)
                    auth_header= headers.get("Authorization", "")
                    assert "Bearer " in auth_header
    
                    # Verify no PHI in query parameters
                    query_params = captured_request[1].get("params", {})
                    assert not any("test-patient" in str(v) for v in query_params.values())


                    def test_api_response_structure():



                        client: TestClient,
                    provider_token: str,
                    sample_readings: List[Dict[str, Any]],
                    sample_device_info: Dict[str, Any]
                    () -> None:
                    """Test the structure of API responses.
    
                    Args:
                    client: Test client
                    provider_token: JWT token for a provider user
                    sample_readings: Sample accelerometer readings
                    sample_device_info: Sample device information
                    """
                    # Create an analysis
                    request_data = {
                    "patient_id": "test-patient-1",
                    "readings": sample_readings,
                    "start_time": "2025-01-01T00:00:00Z",
                    "end_time": "2025-01-01T00:00:02Z",
                    "sampling_rate_hz": 1.0,
                    "device_info": sample_device_info,
                    "analysis_types": ["sleep_quality", "activity_levels"]
}
    
response = client.post()
"/api/v1/actigraphy/analyze",
json=request_data,
headers={"Authorization": f"Bearer {provider_token}"}
(    )
    
# Check response structure
data = response.json()
    
# Check required fields are present
assert "analysis_id" in data
assert "patient_id" in data
assert "timestamp" in data
assert "device_info" in data
assert "analysis_period" in data
assert "sampling_info" in data
assert "sleep_metrics" in data
assert "activity_levels" in data
    
# Check nested structures
assert "start_time" in data["analysis_period"]
assert "end_time" in data["analysis_period"]
assert "rate_hz" in data["sampling_info"]
assert "sample_count" in data["sampling_info"]
    
# Get the analysis ID
analysis_id = data["analysis_id"]
    
# Get analysis by ID
response = client.get()
f"/api/v1/actigraphy/analysis/{analysis_id}",
headers={"Authorization": f"Bearer {provider_token}"}
(    )
    
# Check response matches the original
get_data = response.json()
assert get_data["analysis_id"] == data["analysis_id"]
assert get_data["patient_id"] == data["patient_id"]
assert get_data["timestamp"] == data["timestamp"]