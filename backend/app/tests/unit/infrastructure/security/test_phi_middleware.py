# -*- coding: utf-8 -*-
"""Unit tests for PHI Middleware functionality.

This module tests the PHI middleware which ensures Protected Health Information (PHI)
is properly handled in HTTP requests and responses, a critical requirement for HIPAA compliance.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from app.infrastructure.security.phi_middleware import (
    PHIMiddleware,
    PHIConfig,
    PHIAccessControl,
    PHIField,
    Sensitivity,
    AccessRecord,
    PHIAccessReason,
    RequestContext,
    PHIAccessException,
    UnauthorizedPHIAccessException,
    DataMaskingService
)


@pytest.fixture
def phi_config():
    """Create a PHI middleware configuration for testing."""
    return PHIConfig(
        enabled=True,
        audit_phi_access=True,
        mask_sensitive_data_in_responses=True,
        require_phi_access_reason=True,
        require_patient_relationship=True,
        patient_id_parameter="patient_id",
        enforce_minimum_necessary=True,
        enforce_path_based_restrictions=True,
        exempt_paths=["/health", "/docs", "/openapi.json"],
        phi_fields=[
            PHIField(name="patient_name", sensitivity=Sensitivity.HIGH, pattern=r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),
            PHIField(name="ssn", sensitivity=Sensitivity.VERY_HIGH, pattern=r"\d{3}-\d{2}-\d{4}"),
            PHIField(name="dob", sensitivity=Sensitivity.HIGH, pattern=r"\d{4}-\d{2}-\d{2}"),
            PHIField(name="email", sensitivity=Sensitivity.MEDIUM, pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            PHIField(name="phone", sensitivity=Sensitivity.MEDIUM, pattern=r"\(\d{3}\) \d{3}-\d{4}"),
            PHIField(name="address", sensitivity=Sensitivity.HIGH, pattern=r"\d+ [A-Za-z]+ [A-Za-z]+, [A-Za-z]+, [A-Z]{2} \d{5}")
        ],
        log_phi_redactions=True,
        mask_phi_in_urls=True,
        request_body_size_limit_kb=1024,
        phi_paths={
            "/api/patients": ["patient_name", "ssn", "dob", "email", "phone", "address"],
            "/api/clinical-notes": ["patient_name", "dob", "clinical_content"]
        },
        check_phi_in_query_params=True,
        phi_validation_level="strict"
    )


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()


@pytest.fixture
def mock_log_sanitizer():
    """Create a mock log sanitizer for testing."""
    mock_sanitizer = MagicMock()
    mock_sanitizer.sanitize.side_effect = lambda x: x.replace("123-45-6789", "[REDACTED_SSN]").replace("John Smith", "[REDACTED_NAME]")
    return mock_sanitizer


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger for testing."""
    mock_logger = MagicMock()
    return mock_logger


@pytest.fixture
def mock_masking_service():
    """Create a mock data masking service for testing."""
    mock_service = MagicMock(spec=DataMaskingService)
    
    # Configure mock masking behavior
    def mock_mask_phi(data):
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key == "ssn":
                    result[key] = "XXX-XX-6789"
                elif key == "patient_name" or key == "name":
                    result[key] = "J*** S****"
                elif key == "dob":
                    result[key] = "XXXX-XX-XX"
                elif key == "email":
                    result[key] = "j***@e******.com"
                elif key == "phone":
                    result[key] = "(XXX) XXX-XXXX"
                elif key == "address":
                    result[key] = "XXX Main St, A*****, XX XXXXX"
                elif isinstance(value, (dict, list)):
                    result[key] = mock_mask_phi(value)
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [mock_mask_phi(item) for item in data]
        return data
    
    mock_service.mask_phi.side_effect = mock_mask_phi
    return mock_service


@pytest.fixture
def phi_middleware(app, phi_config, mock_log_sanitizer, mock_audit_logger, mock_masking_service):
    """Create a PHI middleware for testing."""
    middleware = PHIMiddleware(
        app=app,
        config=phi_config
    )
    middleware.log_sanitizer = mock_log_sanitizer
    middleware.audit_logger = mock_audit_logger
    middleware.masking_service = mock_masking_service
    middleware.access_control = PHIAccessControl(config=phi_config)
    return middleware


@pytest.fixture
def authenticated_request():
    """Create a mock request with a valid authentication token and PHI access reason."""
    mock_request = MagicMock(spec=Request)
    
    # Setup request properties
    mock_request.method = "GET"
    mock_request.url.path = "/api/patients"
    mock_request.query_params = {}
    mock_request.headers = Headers({
        "Authorization": "Bearer valid.jwt.token",
        "X-PHI-Access-Reason": "treatment",
        "Content-Type": "application/json"
    })
    
    # Setup state with authentication info
    mock_request.state = MagicMock()
    mock_request.state.authenticated = True
    mock_request.state.user = {
        "sub": "user123",
        "name": "Dr. Jane Smith",
        "roles": ["psychiatrist"],
        "permissions": ["read:patient", "write:clinical_note"]
    }
    
    # Mock body reading
    async def mock_body():
        return json.dumps({
            "patient_id": "PT12345",
            "patient_name": "John Smith",
            "dob": "1980-05-15",
            "ssn": "123-45-6789",
            "contact": {
                "email": "john.smith@example.com",
                "phone": "(555) 123-4567"
            }
        }).encode()
    
    mock_request.body = AsyncMock(side_effect=mock_body)
    
    return mock_request


@pytest.mark.db_required
class TestPHIMiddleware:
    """Test suite for the PHI middleware."""
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_phi_detection_in_request(self, phi_middleware, authenticated_request, mock_audit_logger):
        """Test detection of PHI in request body."""
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            # The request state should include PHI access info
            assert hasattr(request.state, "phi_access")
            assert request.state.phi_access.resource_type == "patients"
            assert request.state.phi_access.patient_id == "PT12345"
            assert request.state.phi_access.reason == PHIAccessReason.TREATMENT
            
            return JSONResponse(content={"status": "success"})
        
        # Process the request through middleware
        response = await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify the response
        assert response.status_code == 200
        
        # Verify PHI access was logged
        mock_audit_logger.log_phi_access.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_phi_masking_in_response(self, phi_middleware, authenticated_request, mock_masking_service):
        """Test masking of PHI in response body."""
        # Configure middleware to mask sensitive data
        phi_middleware.config.mask_sensitive_data_in_responses = True
        
        # Create a response with PHI
        patient_data = {
            "patient_id": "PT12345",
            "patient_name": "John Smith",
            "dob": "1980-05-15",
            "ssn": "123-45-6789",
            "email": "john.smith@example.com",
            "phone": "(555) 123-4567",
            "medical_history": [
                {"date": "2022-01-15", "diagnosis": "F41.1", "notes": "Patient reports anxiety symptoms"}
            ]
        }
        
        # Setup the next middleware in the chain to return PHI
        async def mock_call_next(request):
            return JSONResponse(content=patient_data)
        
        # Process the request through middleware
        response = await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify the response
        assert response.status_code == 200
        
        # Parse the response body
        response_data = json.loads(response.body)
        
        # Verify PHI was masked
        assert response_data["patient_name"] != "John Smith"
        assert response_data["ssn"] != "123-45-6789"
        assert response_data["dob"] != "1980-05-15"
        assert response_data["email"] != "john.smith@example.com"
        assert response_data["phone"] != "(555) 123-4567"
        
        # Verify masking service was called
        mock_masking_service.mask_phi.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_missing_phi_access_reason(self, phi_middleware, authenticated_request):
        """Test handling of request without PHI access reason."""
        # Remove the PHI access reason header
        authenticated_request.headers = Headers({
            "Authorization": "Bearer valid.jwt.token",
            "Content-Type": "application/json"
        })
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should raise exception)
        with pytest.raises(PHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify failed access was logged
        phi_middleware.audit_logger.log_phi_violation.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_invalid_phi_access_reason(self, phi_middleware, authenticated_request):
        """Test handling of request with invalid PHI access reason."""
        # Set an invalid PHI access reason
        authenticated_request.headers = Headers({
            "Authorization": "Bearer valid.jwt.token",
            "X-PHI-Access-Reason": "invalid_reason",
            "Content-Type": "application/json"
        })
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should raise exception)
        with pytest.raises(PHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify failed access was logged
        phi_middleware.audit_logger.log_phi_violation.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_exempt_path(self, phi_middleware, authenticated_request):
        """Test that exempt paths bypass PHI processing."""
        # Modify the request to use an exempt path
        authenticated_request.url.path = "/health"
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            # For exempt paths, the state should indicate PHI exempt
            assert hasattr(request.state, "phi_exempt")
            assert request.state.phi_exempt is True
            
            return JSONResponse(content={"status": "healthy"})
        
        # Process the request through middleware
        response = await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify the response was allowed through
        assert response.status_code == 200
        assert json.loads(response.body) == {"status": "healthy"}
        
        # Verify no PHI processing was performed
        phi_middleware.audit_logger.log_phi_access.assert_not_called()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_disabled_middleware(self, phi_config, app, authenticated_request):
        """Test behavior when middleware is disabled."""
        # Create disabled middleware
        disabled_config = phi_config
        disabled_config.enabled = False
        
        disabled_middleware = PHIMiddleware(
            app=app,
            config=disabled_config
        )
        disabled_middleware.audit_logger = MagicMock()
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            # For disabled middleware, no PHI checks should happen
            return JSONResponse(content={"status": "success"})
        
        # Process the request through middleware
        response = await disabled_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify the response was allowed through
        assert response.status_code == 200
        assert json.loads(response.body) == {"status": "success"}
        
        # Verify no PHI processing was performed
        disabled_middleware.audit_logger.log_phi_access.assert_not_called()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_patient_relationship_validation(self, phi_middleware, authenticated_request):
        """Test validation of provider-patient relationship."""
        # Configure middleware to require patient relationship
        phi_middleware.config.require_patient_relationship = True
        
        # Modify the user claims to include patient relationship
        authenticated_request.state.user["authorized_patients"] = ["PT12345", "PT67890"]
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should succeed as patient ID matches)
        response = await phi_middleware.dispatch(authenticated_request, mock_call_next)
        assert response.status_code == 200
        
        # Now attempt with an unauthorized patient
        authenticated_request_body = await authenticated_request.body()
        authenticated_request_json = json.loads(authenticated_request_body)
        authenticated_request_json["patient_id"] = "PT99999"  # Not in authorized list
        authenticated_request.body = AsyncMock(return_value=json.dumps(authenticated_request_json).encode())
        
        # Process the request (should raise exception)
        with pytest.raises(UnauthorizedPHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_phi_detection_in_url(self, phi_middleware, authenticated_request):
        """Test detection of PHI in URL path/query."""
        # Modify the request to include PHI in URL
        authenticated_request.url.path = "/api/patients/123-45-6789"  # SSN in URL
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should raise exception if enabled)
        phi_middleware.config.mask_phi_in_urls = True
        
        with pytest.raises(PHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify violation was logged
        phi_middleware.audit_logger.log_phi_violation.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_minimum_necessary_principle(self, phi_middleware, authenticated_request):
        """Test enforcement of minimum necessary principle."""
        # Configure middleware to enforce minimum necessary
        phi_middleware.config.enforce_minimum_necessary = True
        
        # Modify the request body to include excessive PHI
        authenticated_request_body = await authenticated_request.body()
        authenticated_request_json = json.loads(authenticated_request_body)
        authenticated_request_json["unnecessary_field1"] = "123-45-6789"  # SSN
        authenticated_request_json["unnecessary_field2"] = "John Smith"  # Name
        authenticated_request.body = AsyncMock(return_value=json.dumps(authenticated_request_json).encode())
        
        # Setup the access control to consider these fields unnecessary
        phi_middleware.access_control.check_minimum_necessary = MagicMock(return_value=(False, ["unnecessary_field1", "unnecessary_field2"]))
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should raise exception)
        with pytest.raises(PHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify violation was logged
        phi_middleware.audit_logger.log_phi_violation.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_sensitive_query_parameters(self, phi_middleware, authenticated_request):
        """Test detection of PHI in query parameters."""
        # Modify the request to include PHI in query params
        authenticated_request.url.path = "/api/patients"
        authenticated_request.query_params = {"ssn": "123-45-6789", "name": "John Smith"}
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should raise exception)
        phi_middleware.config.check_phi_in_query_params = True
        
        with pytest.raises(PHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify violation was logged
        phi_middleware.audit_logger.log_phi_violation.assert_called_once()
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_phi_response_handling(self, phi_middleware, authenticated_request):
        """Test proper handling of PHI in responses."""
        # Configure middleware
        phi_middleware.config.mask_sensitive_data_in_responses = True
        
        # Prepare a response with PHI
        sensitive_response_data = {
            "patient_id": "PT12345",
            "medical_records": [
                {
                    "record_id": "MR001",
                    "doctor": "Dr. Jane Smith",
                    "patient": "John Smith",
                    "ssn": "123-45-6789",
                    "diagnosis": "F41.1",
                    "notes": "Patient exhibits signs of anxiety disorder",
                    "contact": {
                        "email": "john.smith@example.com",
                        "phone": "(555) 123-4567"
                    }
                }
            ]
        }
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content=sensitive_response_data)
        
        # Process the request and get masked response
        response = await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify the response status
        assert response.status_code == 200
        
        # Parse the response body
        response_data = json.loads(response.body)
        
        # Verify all PHI was masked
        assert "John Smith" not in str(response_data)
        assert "123-45-6789" not in str(response_data)
        assert "john.smith@example.com" not in str(response_data)
        assert "(555) 123-4567" not in str(response_data)
        
        # Verify non-PHI fields were preserved
        assert response_data["patient_id"] == "PT12345"
        assert response_data["medical_records"][0]["diagnosis"] == "F41.1"
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_access_record_creation(self, phi_middleware, authenticated_request):
        """Test creation of proper PHI access records."""
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request
        await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify access record was created and logged
        phi_middleware.audit_logger.log_phi_access.assert_called_once()
        
        # Get the access record from the log call
        log_call = phi_middleware.audit_logger.log_phi_access.call_args
        access_record = log_call[1]["phi_access"]
        
        # Verify access record contains required information
        assert access_record.resource_type == "patients"
        assert access_record.patient_id == "PT12345"
        assert access_record.reason == PHIAccessReason.TREATMENT
        assert access_record.action is not None
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_large_request_handling(self, phi_middleware, authenticated_request):
        """Test handling of large requests with PHI."""
        # Configure size limit
        phi_middleware.config.request_body_size_limit_kb = 1  # 1KB limit
        
        # Create a large request body (>1KB)
        large_body = {
            "patient_id": "PT12345",
            "patient_name": "John Smith",
            "ssn": "123-45-6789",
            "large_field": "A" * 1500  # Add 1500 'A's to exceed the limit
        }
        
        authenticated_request.body = AsyncMock(return_value=json.dumps(large_body).encode())
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should raise exception)
        with pytest.raises(HTTPException) as exc_info:
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify correct exception and status code
        assert exc_info.value.status_code == 413  # Request Entity Too Large
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_role_based_access_control(self, phi_middleware, authenticated_request):
        """Test role-based PHI access control."""
        # Set up different roles with varying PHI access permissions
        phi_middleware.config.role_phi_access = {
            "psychiatrist": ["patient_name", "ssn", "dob", "email", "phone", "address", "diagnosis", "notes"],
            "nurse": ["patient_name", "dob", "diagnosis"],
            "admin": ["patient_name", "email", "phone"]
        }
        
        # Test with psychiatrist role (should have full access)
        authenticated_request.state.user["roles"] = ["psychiatrist"]
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should succeed)
        response = await phi_middleware.dispatch(authenticated_request, mock_call_next)
        assert response.status_code == 200
        
        # Test with nurse role (limited access)
        authenticated_request.state.user["roles"] = ["nurse"]
        
        # Create body with fields a nurse shouldn't access
        restricted_body = {
            "patient_id": "PT12345",
            "patient_name": "John Smith",
            "dob": "1980-05-15",
            "ssn": "123-45-6789",  # Nurses shouldn't access SSN
            "diagnosis": "F41.1"
        }
        
        authenticated_request.body = AsyncMock(return_value=json.dumps(restricted_body).encode())
        
        # Setup access control to detect this violation
        phi_middleware.access_control.check_role_based_access = MagicMock(return_value=(False, ["ssn"]))
        
        # Process the request (should raise exception)
        with pytest.raises(UnauthorizedPHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
    
    @pytest.mark.asyncio
    async @pytest.mark.db_required
def test_purpose_specific_access(self, phi_middleware, authenticated_request):
        """Test purpose-specific PHI access controls."""
        # Configure purpose-specific access rules
        phi_middleware.config.purpose_based_access = {
            PHIAccessReason.TREATMENT: ["patient_name", "dob", "diagnosis", "notes"],
            PHIAccessReason.PAYMENT: ["patient_name", "dob", "billing_code"],
            PHIAccessReason.OPERATIONS: ["patient_name", "appointment_time"]
        }
        
        # Set purpose to payment but include treatment data
        authenticated_request.headers = Headers({
            "Authorization": "Bearer valid.jwt.token",
            "X-PHI-Access-Reason": "payment",
            "Content-Type": "application/json"
        })
        
        # Create body with fields not appropriate for payment purpose
        restricted_body = {
            "patient_id": "PT12345",
            "patient_name": "John Smith",
            "dob": "1980-05-15",
            "diagnosis": "F41.1",  # Not needed for payment
            "notes": "Patient exhibits signs of anxiety",  # Not needed for payment
            "billing_code": "99214"
        }
        
        authenticated_request.body = AsyncMock(return_value=json.dumps(restricted_body).encode())
        
        # Setup access control to detect this violation
        phi_middleware.access_control.check_purpose_based_access = MagicMock(return_value=(False, ["diagnosis", "notes"]))
        
        # Setup the next middleware in the chain
        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})
        
        # Process the request (should raise exception)
        with pytest.raises(PHIAccessException):
            await phi_middleware.dispatch(authenticated_request, mock_call_next)
        
        # Verify violation was logged
        phi_middleware.audit_logger.log_phi_violation.assert_called_once()