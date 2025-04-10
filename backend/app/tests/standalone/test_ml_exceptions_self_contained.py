"""
Self-contained test for ML exceptions that doesn't require imports from other modules.

This file contains both the exception classes and tests in a single file for standalone testing.
"""
import sys
import traceback
from typing import Dict, Any, Optional


# ---- Exception Classes (Copy from app/domain/ml/exceptions.py) ----

class MentalLLaMABaseException(Exception):
    """Base exception for all MentalLLaMA-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception with a message and optional details.
        
        Args:
            message: The error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MentalLLaMAConnectionError(MentalLLaMABaseException):
    """Exception raised when connection to MentalLLaMA service fails."""
    
    def __init__(self, message: str, endpoint: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the connection error.
        
        Args:
            message: The error message
            endpoint: The API endpoint that failed
            details: Optional dictionary with additional error context
        """
        self.endpoint = endpoint
        super().__init__(message, details)


class MentalLLaMAAuthenticationError(MentalLLaMABaseException):
    """Exception raised when authentication with MentalLLaMA service fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the authentication error.
        
        Args:
            message: The error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message, details)


class MentalLLaMAInferenceError(MentalLLaMABaseException):
    """Exception raised when inference with MentalLLaMA model fails."""
    
    def __init__(self, 
                 message: str, 
                 model_name: str, 
                 inference_parameters: Optional[Dict[str, Any]] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize the inference error.
        
        Args:
            message: The error message
            model_name: The name of the model that failed
            inference_parameters: The parameters used for inference
            details: Optional dictionary with additional error context
        """
        self.model_name = model_name
        self.inference_parameters = inference_parameters or {}
        
        # Merge inference parameters into details
        combined_details = details or {}
        combined_details["model_name"] = model_name
        combined_details["inference_parameters"] = self.inference_parameters
        
        super().__init__(message, combined_details)


class MentalLLaMAValidationError(MentalLLaMABaseException):
    """Exception raised when input validation for MentalLLaMA fails."""
    
    def __init__(self, message: str, validation_errors: Dict[str, str], details: Optional[Dict[str, Any]] = None):
        """
        Initialize the validation error.
        
        Args:
            message: The error message
            validation_errors: Dictionary mapping field names to error messages
            details: Optional dictionary with additional error context
        """
        self.validation_errors = validation_errors
        
        # Merge validation errors into details
        combined_details = details or {}
        combined_details["validation_errors"] = validation_errors
        
        super().__init__(message, combined_details)


class MentalLLaMAQuotaExceededError(MentalLLaMABaseException):
    """Exception raised when API usage quota is exceeded."""
    
    def __init__(self, message: str, quota_limit: int, quota_used: int, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the quota exceeded error.
        
        Args:
            message: The error message
            quota_limit: The maximum allowed API calls
            quota_used: The current number of API calls made
            details: Optional dictionary with additional error context
        """
        self.quota_limit = quota_limit
        self.quota_used = quota_used
        
        # Merge quota information into details
        combined_details = details or {}
        combined_details["quota_limit"] = quota_limit
        combined_details["quota_used"] = quota_used
        combined_details["quota_remaining"] = max(0, quota_limit - quota_used)
        
        super().__init__(message, combined_details)


# ---- Test Code ----

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
        print("✅ test_base_exception passed")
    
    def test_base_exception_without_details(self):
        """Test MentalLLaMABaseException creation without details."""
        message = "Test base exception without details"
        
        exception = MentalLLaMABaseException(message)
        
        # Verify properties
        assert exception.message == message
        assert exception.details == {}
        assert str(exception) == message
        print("✅ test_base_exception_without_details passed")
    
    def test_connection_error(self):
        """Test MentalLLaMAConnectionError creation and properties."""
        message = "Failed to connect to MentalLLaMA API"
        endpoint = "/api/v1/inference"
        details = {
            "status_code": 503,
            "response": "Service Unavailable"
        }
        
        exception = MentalLLaMAConnectionError(message, endpoint, details)
        
        # Verify properties
        assert exception.message == message
        assert exception.endpoint == endpoint
        assert exception.details == details
        assert str(exception) == message
        print("✅ test_connection_error passed")
    
    def test_authentication_error(self):
        """Test MentalLLaMAAuthenticationError creation and properties."""
        message = "API key invalid or expired"
        details = {
            "status_code": 401,
            "response": "Unauthorized"
        }
        
        exception = MentalLLaMAAuthenticationError(message, details)
        
        # Verify properties
        assert exception.message == message
        assert exception.details == details
        assert str(exception) == message
        print("✅ test_authentication_error passed")
    
    def test_inference_error(self):
        """Test MentalLLaMAInferenceError creation and properties."""
        message = "Inference failed due to invalid input format"
        model_name = "mentalllama-13b-chat"
        inference_parameters = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "prompt": "Patient exhibits..."
        }
        details = {
            "status_code": 400,
            "error_type": "InputValidationError"
        }
        
        exception = MentalLLaMAInferenceError(
            message, 
            model_name, 
            inference_parameters, 
            details
        )
        
        # Verify properties
        assert exception.message == message
        assert exception.model_name == model_name
        assert exception.inference_parameters == inference_parameters
        
        # Verify details are merged with parameters
        assert "model_name" in exception.details
        assert exception.details["model_name"] == model_name
        assert "inference_parameters" in exception.details
        assert exception.details["inference_parameters"] == inference_parameters
        assert "status_code" in exception.details
        assert exception.details["status_code"] == 400
        print("✅ test_inference_error passed")
    
    def test_validation_error(self):
        """Test MentalLLaMAValidationError creation and properties."""
        message = "Input validation failed"
        validation_errors = {
            "patient_id": "Missing required field",
            "prompt": "Prompt exceeds maximum length of 4096 tokens"
        }
        details = {
            "request_id": "req-123456"
        }
        
        exception = MentalLLaMAValidationError(message, validation_errors, details)
        
        # Verify properties
        assert exception.message == message
        assert exception.validation_errors == validation_errors
        
        # Verify details are merged with validation errors
        assert "validation_errors" in exception.details
        assert exception.details["validation_errors"] == validation_errors
        assert "request_id" in exception.details
        assert exception.details["request_id"] == "req-123456"
        print("✅ test_validation_error passed")
    
    def test_quota_exceeded_error(self):
        """Test MentalLLaMAQuotaExceededError creation and properties."""
        message = "API call quota exceeded"
        quota_limit = 1000
        quota_used = 1001
        details = {
            "reset_time": "2025-04-11T00:00:00Z"
        }
        
        exception = MentalLLaMAQuotaExceededError(message, quota_limit, quota_used, details)
        
        # Verify properties
        assert exception.message == message
        assert exception.quota_limit == quota_limit
        assert exception.quota_used == quota_used
        
        # Verify details are merged with quota information
        assert "quota_limit" in exception.details
        assert exception.details["quota_limit"] == quota_limit
        assert "quota_used" in exception.details
        assert exception.details["quota_used"] == quota_used
        assert "quota_remaining" in exception.details
        assert exception.details["quota_remaining"] == 0
        assert "reset_time" in exception.details
        assert exception.details["reset_time"] == "2025-04-11T00:00:00Z"
        print("✅ test_quota_exceeded_error passed")
    
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
        exceptions = [
            base_exc, conn_exc, auth_exc, infer_exc, valid_exc, quota_exc
        ]
        
        for exc in exceptions:
            try:
                raise exc
            except MentalLLaMABaseException as caught_exc:
                assert caught_exc is exc
        
        print("✅ test_exception_inheritance passed")


def run_tests():
    """Run all tests and report results."""
    print("\n==== Running Self-Contained ML Exception Tests ====\n")
    
    test_instance = TestMentalLLaMAExceptions()
    test_methods = [
        test_instance.test_base_exception,
        test_instance.test_base_exception_without_details,
        test_instance.test_connection_error,
        test_instance.test_authentication_error,
        test_instance.test_inference_error,
        test_instance.test_validation_error,
        test_instance.test_quota_exceeded_error,
        test_instance.test_exception_inheritance
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_method()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_method.__name__} failed: {e}")
            print(traceback.format_exc())
        except Exception as e:
            failed += 1
            print(f"❌ {test_method.__name__} failed with unexpected error: {e}")
            print(traceback.format_exc())
    
    print("\n==== Test Results ====")
    print(f"✅ {passed} tests passed")
    
    if failed > 0:
        print(f"❌ {failed} tests failed")
        return 1
    else:
        print("All tests passed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(run_tests())