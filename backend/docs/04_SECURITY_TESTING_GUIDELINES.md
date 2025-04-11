# Security Testing Guidelines

## Overview

This document defines the security testing guidelines for the Novamind Digital Twin platform. Given the HIPAA-regulated nature of the system and the sensitivity of the data being processed, security testing is a critical component of the overall test strategy.

## Security Testing Principles

All security testing in the Novamind platform must adhere to these core principles:

1. **100% Coverage** - All security-critical code must have 100% test coverage
2. **Defense in Depth** - Security must be tested at multiple levels (unit, integration, system)
3. **Negative Testing** - Explicitly test security failures and boundary conditions
4. **No Live PHI** - All security tests must use synthetic PHI data
5. **Automated Verification** - Security requirements must be automatically verified in CI/CD

## Security Test Categories

Security tests are organized into the following categories:

### 1. PHI Protection Tests

Tests that verify Protected Health Information (PHI) is properly safeguarded:

- **PHI Sanitization** - Verify PHI is properly sanitized in logs, errors, and outputs
- **PHI Detection** - Verify PHI detection algorithms correctly identify sensitive data
- **PHI Masking** - Verify PHI masking functions correctly hide sensitive information
- **PHI Audit** - Verify PHI access is properly audited and tracked

#### Example Test Cases:

```python
def test_phi_sanitizer_removes_patient_name():
    """Verify PHI sanitizer removes patient names from logs."""
    log_entry = "Processing data for patient John Smith"
    sanitized = phi_sanitizer.sanitize_log_entry(log_entry)
    assert "John Smith" not in sanitized
    assert "[PATIENT_NAME]" in sanitized

def test_phi_detection_identifies_ssn():
    """Verify PHI detection identifies SSNs in text."""
    text = "Patient SSN is 123-45-6789"
    detected = phi_detector.detect_phi(text)
    assert "123-45-6789" in detected
    assert detected["123-45-6789"] == "SSN"
```

### 2. Authentication and Authorization Tests

Tests that verify proper authentication and authorization controls:

- **Authentication** - Verify user identity is properly validated
- **JWT Generation/Validation** - Verify JWT tokens are secure and properly validated
- **Password Security** - Verify password hashing and validation
- **Role-Based Access Control** - Verify access is limited based on user roles
- **Session Management** - Verify sessions are secure and properly managed

#### Example Test Cases:

```python
def test_invalid_credentials_rejected():
    """Verify that invalid login credentials are rejected."""
    result = auth_service.authenticate("user@example.com", "wrong_password")
    assert result.is_authenticated is False
    assert "Invalid credentials" in result.error_message

def test_provider_cannot_access_admin_endpoint():
    """Verify that providers cannot access admin-only endpoints."""
    token = auth_service.generate_token(user_id="123", role="provider")
    result = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert result.status_code == 403
```

### 3. Encryption and Data Security Tests

Tests that verify data is properly encrypted and secured:

- **Data Encryption** - Verify sensitive data is encrypted at rest
- **Transport Security** - Verify data is secured in transit
- **Key Management** - Verify encryption keys are properly managed
- **Database Security** - Verify database access is secure and parameterized

#### Example Test Cases:

```python
def test_patient_data_encrypted_in_database():
    """Verify patient data is encrypted in the database."""
    patient = Patient(name="John Doe", ssn="123-45-6789")
    repository.save(patient)
    
    # Verify data is encrypted in database
    raw_data = repository.get_raw_data(patient.id)
    assert "John Doe" not in raw_data
    assert "123-45-6789" not in raw_data
    
    # Verify data can be decrypted properly
    retrieved = repository.get(patient.id)
    assert retrieved.name == "John Doe"
    assert retrieved.ssn == "123-45-6789"

def test_sql_injection_prevented():
    """Verify SQL injection attacks are prevented."""
    malicious_input = "'; DROP TABLE patients; --"
    # This should not raise an exception or execute the malicious SQL
    result = repository.search_patients(malicious_input)
    assert isinstance(result, list)
    # Verify database integrity
    assert repository.table_exists("patients")
```

### 4. Audit Logging Tests

Tests that verify all security-relevant events are properly logged:

- **Login/Logout Events** - Verify authentication events are logged
- **PHI Access** - Verify PHI access is logged
- **Administrative Actions** - Verify admin actions are logged
- **Security Events** - Verify security violations are logged

#### Example Test Cases:

```python
def test_successful_login_creates_audit_log():
    """Verify successful logins create appropriate audit logs."""
    result = auth_service.authenticate("user@example.com", "correct_password")
    assert result.is_authenticated is True
    
    # Check audit log was created
    audit_logs = audit_repository.get_logs(
        event_type="LOGIN", 
        user_email="user@example.com"
    )
    assert len(audit_logs) >= 1
    assert audit_logs[0].status == "SUCCESS"
    assert audit_logs[0].ip_address is not None

def test_phi_access_creates_audit_log():
    """Verify PHI access creates appropriate audit logs."""
    patient_id = "123"
    user_id = "456"
    
    patient_service.get_patient(patient_id, user_id=user_id)
    
    # Check audit log was created
    audit_logs = audit_repository.get_logs(
        event_type="PHI_ACCESS", 
        user_id=user_id,
        resource_id=patient_id
    )
    assert len(audit_logs) >= 1
    assert audit_logs[0].resource_type == "PATIENT"
```

### 5. Security Boundary Tests

Tests that verify security boundaries between components:

- **API Security** - Verify API endpoints enforce proper security
- **Service Boundaries** - Verify service-to-service communications are secure
- **External Integration Security** - Verify external service integrations are secure

#### Example Test Cases:

```python
def test_unauthenticated_api_request_rejected():
    """Verify unauthenticated API requests are rejected."""
    response = client.get("/api/patients")
    assert response.status_code == 401

def test_external_service_validates_authentication():
    """Verify external service integration validates authentication."""
    # Test with invalid credentials
    service = ExternalServiceClient(api_key="invalid_key")
    with pytest.raises(AuthenticationError):
        service.fetch_data()
```

## Security Test Organization

Security tests should be organized according to the dependency-based directory structure:

### Standalone Security Tests

Place in `backend/app/tests/standalone/security/`:

- PHI sanitization algorithm tests
- Password hashing algorithm tests
- Token generation/validation logic tests
- Security utility function tests

### VENV Security Tests

Place in `backend/app/tests/venv/security/`:

- Framework-level security tests
- Middleware security tests with mocked backends
- Authentication flow tests with mocked repositories
- Audit logging logic tests

### Integration Security Tests

Place in `backend/app/tests/integration/security/`:

- End-to-end authentication flows
- Database encryption tests
- API security tests
- Security boundary tests

## Security Test Coverage Requirements

Security tests must achieve specific coverage targets:

| Category                 | Test Coverage Target |
|--------------------------|----------------------|
| Authentication code      | 100%                 |
| Authorization code       | 100%                 |
| PHI handling code        | 100%                 |
| Encryption/decryption    | 100%                 |
| Input validation         | 100%                 |
| Audit logging            | 100%                 |

## Security Test Fixtures

Standard fixtures for security testing:

```python
@pytest.fixture
def mock_user_with_role(role="user"):
    """Create a mock user with the specified role."""
    return User(
        id="user_123",
        email="test@example.com",
        name="Test User",
        role=role,
        is_active=True
    )

@pytest.fixture
def auth_token(mock_user_with_role):
    """Generate a valid authentication token for testing."""
    return jwt_service.generate_token(
        user_id=mock_user_with_role.id,
        role=mock_user_with_role.role
    )

@pytest.fixture
def mock_phi_data():
    """Create a set of mock PHI data for testing."""
    return {
        "patient_name": "John Doe",
        "dob": "1980-01-01",
        "ssn": "123-45-6789",
        "medical_record_number": "MRN12345",
        "address": "123 Main St, Anytown, USA",
        "phone": "555-123-4567",
        "email": "patient@example.com"
    }
```

## Security Test Markers

Security tests should use the `security` marker for identification:

```python
@pytest.mark.security
def test_phi_sanitization():
    # Test implementation
    pass
```

## Running Security Tests

Security tests can be run specifically with:

```bash
# Run all security tests
python -m pytest backend/app/tests/ -m security

# Run standalone security tests only
python -m pytest backend/app/tests/standalone/security/

# Run with coverage
python -m pytest backend/app/tests/ -m security --cov=app.security
```

## Automated Security Testing in CI/CD

The CI/CD pipeline should include dedicated steps for security testing:

1. Run security tests separately with detailed reporting
2. Enforce 100% coverage requirement for security code
3. Perform static analysis security checks
4. Run security dependency scanning

## Security Test Documentation

All security tests must include detailed documentation:

1. **Purpose** - What security requirement is being verified
2. **Approach** - How the test verifies the requirement
3. **Security Control** - Which security control is being tested
4. **HIPAA Requirement** - Which HIPAA requirement is addressed (if applicable)

Example:

```python
def test_session_timeout():
    """
    Test that user sessions timeout after the configured idle period.
    
    Security Control: Session Management
    HIPAA Requirement: §164.312(a)(2)(iii) - Automatic logoff
    """
    # Test implementation
    pass
```

## Security Testing Best Practices

1. **Test for the absence of vulnerabilities** - Verify common vulnerabilities (OWASP Top 10) are mitigated
2. **Test both positive and negative cases** - Verify both valid and invalid scenarios
3. **Test with realistic data** - Use realistic synthetic PHI for testing
4. **Test all security boundaries** - Verify all trust boundaries between components
5. **Update tests when vulnerabilities are found** - Add regression tests for any discovered vulnerabilities

## Conclusion

Security testing is a critical component of the Novamind test strategy. Following these guidelines ensures that security requirements are properly verified and that the platform maintains HIPAA compliance and protects sensitive patient data.