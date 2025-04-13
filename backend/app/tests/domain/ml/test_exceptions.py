"""
Tests for the ML exceptions module.

This module tests the custom exception classes for machine learning operations,
particularly the MentalLLaMA inference system exceptions.
"""

import pytest
from app.domain.ml.exceptions import ()
MentalLLaMAAuthenticationError,
MentalLLaMABaseException,
MentalLLaMAConnectionError,
MentalLLaMAInferenceError,
MentalLLaMAQuotaExceededError,
MentalLLaMAValidationError,



@pytest.mark.db_required()
class TestMentalLLaMAExceptions:
    """Tests for the MentalLLaMA exception classes."""

    def test_base_exception(self):
        """Test MentalLLaMABaseException creation and properties."""
        # Create a basic exception
        message = "Test base exception"
        details = {"source": "test", "severity": "low"}

        exception = MentalLLaMABaseException(message, details)

        # Verify properties
        assert exception.message == message
        assert exception.details == details
        assert str(exception) == message

        def test_base_exception_without_details(self):
        """Test MentalLLaMABaseException creation without details."""
        message = "Test base exception without details"

        exception = MentalLLaMABaseException(message)

        # Verify properties
        assert exception.message == message
        assert exception.details == {}
        assert str(exception) == message

        def test_connection_error(self):
        """Test MentalLLaMAConnectionError creation and properties."""
        message = "Failed to connect to MentalLLaMA API"
        endpoint = "/api/v1/inference"
        details = {"status_code": 503, "response": "Service Unavailable"}

        exception = MentalLLaMAConnectionError(message, endpoint, details)

        # Verify properties
        assert exception.message == message
        assert exception.endpoint == endpoint
        assert exception.details == details
        assert str(exception).startswith(message)
        assert endpoint in str(exception)

        def test_connection_error_without_details(self):
        """Test MentalLLaMAConnectionError creation without details."""
        message = "Failed to connect to MentalLLaMA API"
        endpoint = "/api/v1/inference"

        exception = MentalLLaMAConnectionError(message, endpoint)

        # Verify properties
        assert exception.message == message
        assert exception.endpoint == endpoint
        assert exception.details == {}
        assert str(exception).startswith(message)
        assert endpoint in str(exception)

        def test_authentication_error(self):
        """Test MentalLLaMAAuthenticationError creation and properties."""
        message = "Authentication failed"
        details = {"error_code": "invalid_token"}

        exception = MentalLLaMAAuthenticationError(message, details)

        # Verify properties
        assert exception.message == message
        assert exception.details == details
        assert str(exception) == message

        def test_inference_error(self):
        """Test MentalLLaMAInferenceError creation and properties."""
        message = "Inference failed"
        model = "gpt-4-psychiatric"
        details = {"error_type": "model_overloaded", "retry_after": 30}

        exception = MentalLLaMAInferenceError(message, model, details)

        # Verify properties
        assert exception.message == message
        assert exception.model == model
        assert exception.details == details
        assert str(exception).startswith(message)
        assert model in str(exception)

        def test_inference_error_without_details(self):
        """Test MentalLLaMAInferenceError creation without details."""
        message = "Inference failed"
        model = "gpt-4-psychiatric"

        exception = MentalLLaMAInferenceError(message, model)

        # Verify properties
        assert exception.message == message
        assert exception.model == model
        assert exception.details == {}
        assert str(exception).startswith(message)
        assert model in str(exception)

        def test_validation_error(self):
        """Test MentalLLaMAValidationError creation and properties."""
        message = "Validation failed"
        validation_errors = {
        "prompt": "Prompt is too long (max 4096 tokens)",
        "temperature": "Temperature must be between 0 and 1",
        }
        details = {"request_id": "req-123456"}

        exception = MentalLLaMAValidationError(message, validation_errors, details)

        # Verify properties
        assert exception.message == message
        assert exception.validation_errors == validation_errors
        assert exception.details == details
        assert str(exception).startswith(message)
        # Check that validation errors are included in string representation
            for field, error in validation_errors.items():
                assert field in str(exception)
                assert error in str(exception)

            def test_quota_exceeded_error(self):
        """Test MentalLLaMAQuotaExceededError creation and properties."""
        message = "API quota exceeded"
        quota_limit = 1000
        quota_used = 1001
        details = {"user_id": "user-123", "plan": "basic"}

        exception = MentalLLaMAQuotaExceededError(message, quota_limit, quota_used, details)

        # Verify properties
        assert exception.message == message
        assert exception.quota_limit == quota_limit
        assert exception.quota_used == quota_used
        assert exception.details["user_id"] == "user-123"
        assert exception.details["plan"] == "basic"
        assert str(exception).startswith(message)
        assert str(quota_limit) in str(exception)
        assert str(quota_used) in str(exception)

        # Verify details are merged with quota information
        assert "quota_limit" in exception.details
        assert exception.details["quota_limit"] == quota_limit
        assert "quota_used" in exception.details
        assert exception.details["quota_used"] == quota_used
        assert "quota_remaining" in exception.details
        assert exception.details["quota_remaining"] == 0
        assert "reset_time" in exception.details
        assert exception.details["reset_time"] == "2025-04-11T00:00:00Z"

        def test_exception_inheritance(self):
        """Test that all exceptions inherit from MentalLLaMABaseException."""
        # Create instances of all exception types
        base_exc = MentalLLaMABaseException("Base error")
        conn_exc = MentalLLaMAConnectionError("Connection error", "/api/v1/endpoint")
        auth_exc = MentalLLaMAAuthenticationError("Auth error")
        infer_exc = MentalLLaMAInferenceError("Inference error", "model-name")
        valid_exc = MentalLLaMAValidationError("Validation error", {"field": "error"})
        quota_exc = MentalLLaMAQuotaExceededError("Quota error", 100, 101)

        # Verify that all exceptions are instances of MentalLLaMABaseException
        assert isinstance(base_exc, MentalLLaMABaseException)
        assert isinstance(conn_exc, MentalLLaMABaseException)
        assert isinstance(auth_exc, MentalLLaMABaseException)
        assert isinstance(infer_exc, MentalLLaMABaseException)
        assert isinstance(valid_exc, MentalLLaMABaseException)
        assert isinstance(quota_exc, MentalLLaMABaseException)

        # Verify that all exceptions can be caught as MentalLLaMABaseException
        exceptions = []
        base_exc,
        conn_exc,
        auth_exc,
        infer_exc,
        valid_exc,
        quota_exc
        

            for exc in exceptions:
            try:
                raise exc
            except MentalLLaMABaseException as caught_exc:
                assert caught_exc is exc