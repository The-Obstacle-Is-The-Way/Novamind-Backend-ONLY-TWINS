# HIPAA Compliance Testing Suite

This directory contains a comprehensive HIPAA compliance testing suite for the NOVAMIND Concierge Psychiatry Platform. The testing framework is designed to validate that our application meets all HIPAA Security Rule requirements and best practices for protecting electronic Protected Health Information (ePHI).

## Overview

Our HIPAA compliance testing strategy covers several key areas:

1. **API Security** - Verifies authentication, authorization, input validation, rate limiting, and secure communication
2. **PHI Protection** - Tests proper handling, redaction, and security of Protected Health Information
3. **Encryption** - Validates our encryption mechanisms for data at rest and in transit
4. **Audit Logging** - Ensures comprehensive logging of all PHI access events
5. **Dependency Security** - Checks for vulnerabilities in third-party dependencies
6. **Static Analysis** - Identifies security issues in the codebase

## Test Components

### ML Encryption Tests (`test_ml_encryption.py`)

Tests focused on ensuring our ML models and data are properly encrypted according to HIPAA standards:

- Model file encryption/decryption
- Batch prediction data security
- Model weights encryption
- Patient data isolation
- Encryption key management
- Model integrity verification

### ML PHI Security Tests (`test_ml_phi_security.py`)

Tests for PHI handling in machine learning components:

- PHI anonymization in ML pipelines
- De-identification of training data
- Secure model storage
- Access controls for ML predictions
- Secure feature extraction

### API Security Tests (`test_api_security.py`)

Tests to validate API security controls:

- Authentication mechanisms
- Authorization and role-based access
- Input validation and sanitization
- Rate limiting
- PHI protection in requests/responses
- Secure headers
- Error handling without leaking sensitive information

### Audit Logging Tests (`test_audit_logging.py`)

Tests to verify HIPAA-compliant audit logging:

- Comprehensive event logging
- Required HIPAA fields in logs
- Failed access logging
- Tamper-resistant logs
- Log file rotation and security
- PHI exclusion from logs

## Running the Tests

We provide several ways to run the HIPAA compliance tests:

### Cross-Platform Python Script (Recommended)

```bash
python scripts/run_hipaa_tests.py
```

Options:
- `--skip-deps` - Skip dependency installation

### Linux/MacOS Shell Script

```bash
chmod +x scripts/run_hipaa_tests.sh
./scripts/run_hipaa_tests.sh
```

### Windows Batch File

```
scripts\run_hipaa_tests.bat
```

### Running Individual Test Suites

To run a specific test suite:

```bash
python -m pytest tests/security/test_api_security.py -v
```

With coverage:

```bash
python -m pytest tests/security/test_api_security.py -v --cov=app.infrastructure.security --cov-report=html:coverage/security/api
```

## Test Reports and Artifacts

After running the tests, several reports are generated:

- **Coverage Reports**: `coverage/security/[component]/index.html`
- **Security Analysis**: `reports/bandit-report.html` 
- **Dependency Vulnerabilities**: `reports/dependency-audit.json`
- **Comprehensive Security Report**: `reports/full-security-report.html`

## HIPAA Compliance Coverage

Our tests are designed to validate compliance with the key HIPAA Security Rule requirements:

| HIPAA Requirement | Test Coverage |
|-------------------|---------------|
| Access Controls (§164.312(a)(1)) | API security tests, authentication tests |
| Audit Controls (§164.312(b)) | Audit logging tests |
| Integrity (§164.312(c)(1)) | Encryption tests, ML integrity tests |
| Person or Entity Authentication (§164.312(d)) | API security tests, JWT tests |
| Transmission Security (§164.312(e)(1)) | API tests, encryption tests |
| Device and Media Controls (§164.308(a)(1)) | Encryption of stored data tests |
| Risk Analysis (§164.308(a)(1)(ii)(A)) | Static analysis, dependency checks |

## Adding New Security Tests

When adding new security tests:

1. Create a new test file following the naming convention `test_[component]_[aspect].py`
2. Include comprehensive docstrings explaining the test purpose
3. Ensure tests mock external dependencies appropriately
4. Add the new test to the appropriate test runners
5. Update this README if adding a new testing category

## Security Test Environment

The test suite automatically creates a clean test environment with:

- Temporary environment variables
- Virtual environment with required dependencies
- Generated test reports

## Continuous Integration

These tests are integrated into our CI/CD pipeline to ensure security is maintained with every code change.

## References

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [NIST Guide to HIPAA Security Rule](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-66r1.pdf)
- [OWASP Healthcare Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)