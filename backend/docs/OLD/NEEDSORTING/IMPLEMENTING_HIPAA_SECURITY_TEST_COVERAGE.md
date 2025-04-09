# Implementing HIPAA Security Test Coverage

This document provides comprehensive guidance on implementing test coverage for HIPAA security requirements in a healthcare application, specifically focusing on the security modules identified by the `check_security_coverage.py` script.

## Core Security Modules Requiring Tests

Based on the current coverage report, the following modules need test coverage:

1. `app/infrastructure/security/log_sanitizer.py` - PHI sanitization in logs
2. `app/infrastructure/security/encryption.py` - Data encryption utilities 
3. `app/infrastructure/security/jwt_service.py` - JWT authentication
4. `app/infrastructure/security/auth_middleware.py` - Authentication middleware
5. `app/infrastructure/security/phi_middleware.py` - PHI protection middleware
6. `app/infrastructure/security/rbac/role_manager.py` - Role-based access control
7. `app/infrastructure/security/password/password_handler.py` - Password security
8. `app/core/utils/phi_sanitizer.py` - PHI detection and sanitization utilities

## Test Structure and Implementation

### General Testing Principles for HIPAA Security

For each security component, tests should verify:

1. **Correctness** - Does the component correctly implement its security function?
2. **Robustness** - Does it handle edge cases and invalid inputs?
3. **Security** - Does it prevent unauthorized access and protect sensitive data?
4. **Compliance** - Does it adhere to HIPAA requirements?

### Required Test Directory Structure

Ensure the following test directory structure exists:

```
tests/
  unit/
    infrastructure/
      security/
        test_log_sanitizer.py
        test_encryption.py
        test_jwt_service.py
        test_auth_middleware.py
        test_phi_middleware.py
        rbac/
          test_role_manager.py
        password/
          test_password_handler.py
    core/
      utils/
        test_phi_sanitizer.py
```

### Testing Approaches for Each Module

#### 1. Log Sanitizer (`test_log_sanitizer.py`)

The log sanitizer test should verify:

- PHI detection in various formats
- Proper sanitization of PHI while preserving non-PHI
- Configuration options work correctly
- Handling of nested data structures

Example test structure:

```python
import pytest
from app.infrastructure.security.log_sanitizer import LogSanitizer, RedactionMode

class TestLogSanitizer:
    
    @pytest.fixture
    def log_sanitizer(self):
        """Create a log sanitizer instance for testing."""
        return LogSanitizer()
    
    def test_sensitive_key_detection(self, log_sanitizer):
        """Test detection and sanitization based on sensitive key names."""
        # Dictionary with sensitive keys
        data = {
            "user_id": "user123",  # Not sensitive
            "ssn": "123-45-6789",  # Sensitive key
            "nested": {
                "dob": "1980-05-15",  # Sensitive key
                "regular_field": "regular value"  # Not sensitive
            }
        }
        
        # Sanitize the dictionary
        sanitized = log_sanitizer.sanitize_dict(data)
        
        # Verify sensitive keys were sanitized
        assert sanitized["ssn"] != "123-45-6789"
        assert sanitized["nested"]["dob"] != "1980-05-15"
        
        # Verify non-sensitive keys were preserved
        assert sanitized["user_id"] == "user123"
        assert sanitized["nested"]["regular_field"] == "regular value"
    
    def test_pattern_based_detection(self, log_sanitizer):
        """Test detection and sanitization based on PHI patterns."""
        # String with various PHI patterns but no sensitive keys
        log_message = """
        User login: admin
        Action: Viewed patient with ID PT654321
        Note: Please contact the patient at john.doe@example.com or (555) 987-6543
        """
        
        # Sanitize the message
        sanitized = log_sanitizer.sanitize(log_message)
        
        # Verify PHI patterns were sanitized
        assert "PT654321" not in sanitized
        assert "john.doe@example.com" not in sanitized
        assert "(555) 987-6543" not in sanitized
        
        # Verify non-PHI was preserved
        assert "User login: admin" in sanitized
    
    def test_partial_redaction(self, log_sanitizer):
        """Test partial redaction of PHI."""
        # Configure for partial redaction
        log_sanitizer.config.redaction_mode = RedactionMode.PARTIAL
        log_sanitizer.config.partial_redaction_length = 4
        
        # Test with SSN
        test_string = "Patient SSN: 123-45-6789"
        sanitized = log_sanitizer.sanitize(test_string)
        
        # Should show only last 4 digits
        assert "6789" in sanitized
        assert "123-45" not in sanitized
```

#### 2. Encryption (`test_encryption.py`)

Encryption tests should verify:

- Proper encryption and decryption of PHI
- Key management security
- Algorithm strength
- Handling of edge cases

Example test structure:

```python
import pytest
from app.infrastructure.security.encryption import EncryptionService

class TestEncryption:
    
    @pytest.fixture
    def encryption_service(self):
        """Create an encryption service for testing."""
        return EncryptionService()
    
    def test_encrypt_decrypt(self, encryption_service):
        """Test basic encryption and decryption."""
        original_text = "Patient has hypertension"
        
        # Encrypt the text
        encrypted = encryption_service.encrypt(original_text)
        
        # Verify encrypted text is different from original
        assert encrypted != original_text
        
        # Decrypt and verify it matches original
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == original_text
    
    def test_deterministic_encryption(self, encryption_service):
        """Test deterministic encryption mode."""
        text = "Prescription: Lisinopril 10mg"
        
        # Enable deterministic mode
        encryption_service.deterministic = True
        
        encrypted1 = encryption_service.encrypt(text)
        encrypted2 = encryption_service.encrypt(text)
        
        # Same text should encrypt to same ciphertext
        assert encrypted1 == encrypted2
```

#### 3. JWT Service (`test_jwt_service.py`)

JWT tests should verify:

- Token creation with proper claims
- Token validation and verification
- Handling of expired or invalid tokens
- Role-based claims

Example test structure:

```python
import pytest
import time
from app.infrastructure.security.jwt_service import JWTService

class TestJWTService:
    
    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service for testing."""
        return JWTService(secret_key="test_secret")
    
    def test_token_creation(self, jwt_service):
        """Test JWT token creation."""
        user_id = "user123"
        role = "doctor"
        
        token = jwt_service.create_token(
            subject=user_id,
            claims={"role": role}
        )
        
        # Verify token was created
        assert token is not None
        assert isinstance(token, str)
    
    def test_token_validation(self, jwt_service):
        """Test JWT token validation."""
        user_id = "user123"
        
        token = jwt_service.create_token(subject=user_id)
        payload = jwt_service.validate_token(token)
        
        # Verify payload contains expected data
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_expired_token(self, jwt_service):
        """Test handling of expired tokens."""
        # Create token that expires immediately
        token = jwt_service.create_token(
            subject="user123",
            expires_in=1  # 1 second
        )
        
        # Wait for token to expire
        time.sleep(2)
        
        # Validation should fail
        with pytest.raises(Exception):
            jwt_service.validate_token(token)
```

## Mocking Dependencies for Testing

When testing security modules, you should mock external dependencies to ensure tests run in isolation and don't actually access sensitive systems:

```python
from unittest.mock import patch, MagicMock

@patch('app.infrastructure.security.encryption.get_kms_client')
def test_encryption_with_kms(mock_kms_client, encryption_service):
    """Test encryption using mocked KMS client."""
    mock_kms = MagicMock()
    mock_kms_client.return_value = mock_kms
    mock_kms.encrypt.return_value = {"CiphertextBlob": b"encrypted_data"}
    mock_kms.decrypt.return_value = {"Plaintext": b"decrypted_data"}
    
    # Test encryption/decryption using the mock
    result = encryption_service.encrypt_with_kms("sensitive data")
    assert result is not None
```

## Setting Up Test Data

For testing security modules, create well-defined test fixtures that include:

1. Sample PHI data
2. Sample authentication credentials
3. Various user roles and permissions

Example:

```python
@pytest.fixture
def sample_phi_data():
    """Sample PHI data for testing."""
    return {
        "patient": {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1980-01-15",
            "ssn": "123-45-6789",
            "mrn": "PT12345678",
            "address": "123 Main St, Anytown, CA 12345",
            "phone": "(555) 123-4567",
            "email": "john.doe@example.com"
        },
        "clinical": {
            "diagnosis": "Hypertension, Diabetes Type II",
            "medications": ["Lisinopril 10mg", "Metformin 500mg"],
            "vitals": {"bp": "120/80", "hr": 72, "temp": 98.6}
        }
    }
```

## Test Coverage Requirements

Per HIPAA Security Rule compliance:

1. **Minimum 80% test coverage** for all security modules
2. **100% coverage for critical functions** including:
   - Encryption/decryption
   - Authentication
   - Authorization
   - PHI detection/sanitization

## Automating Security Test Coverage

Use the coverage reports to identify untested code paths. For each module with low coverage:

1. Identify untested functions and branches
2. Prioritize by security risk
3. Implement tests for high-risk functions first
4. Gradually build coverage for lower-risk areas

## Integration with CI/CD Pipeline

Add security test coverage checks to your CI/CD pipeline:

```yaml
name: HIPAA Security Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  security-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install -r requirements-security.txt
      - name: Run security tests with coverage
        run: |
          pytest tests/unit/infrastructure/security --cov=app.infrastructure.security --cov-report=xml
      - name: Check coverage threshold
        run: |
          python scripts/security/check_security_coverage.py
```

## Testing Security Without Breaking Security

Security testing should never:

1. Store real PHI, even in test code
2. Expose real credentials or keys
3. Connect to production resources
4. Bypass security controls for convenience

Use environment-specific configurations:

```python
# app/core/config.py
class TestConfig:
    """Configuration for test environment."""
    ENCRYPTION_KEY = "test_encryption_key"
    JWT_SECRET = "test_jwt_secret"
    ALLOW_TEST_ACCOUNTS = True
```

## References

1. [NIST SP 800-66: Implementing the HIPAA Security Rule](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-66r1.pdf)
2. [OCR Guidance on Risk Analysis](https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html)
3. [HITRUST CSF](https://hitrustalliance.net/product-tool/hitrust-csf/)
4. [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)