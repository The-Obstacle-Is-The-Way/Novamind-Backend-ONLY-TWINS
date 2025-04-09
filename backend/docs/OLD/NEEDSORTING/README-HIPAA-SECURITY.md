# HIPAA Security & Compliance Framework

This document provides a comprehensive overview of the HIPAA security and compliance framework implemented in the Novamind Backend platform for concierge psychiatry.

## Architecture Overview

The Novamind platform implements a defense-in-depth strategy for HIPAA compliance with multiple layers of security controls:

1. **Authentication & Authorization Layer**
   * JWT-based authentication with role-based access control (patient/doctor/admin)
   * Multi-factor authentication support via AWS Cognito
   * Token expiration and rotation policies

2. **Data Protection Layer**
   * Field-level encryption for PHI at rest
   * Transport Layer Security (TLS) for data in transit
   * PHI sanitization in logs and error messages

3. **Access Control Layer**
   * Fine-grained permission system
   * Role-based access controls at the API level
   * Repository-level authorization checks

4. **Audit & Monitoring Layer**
   * Comprehensive access logging for all PHI
   * Tamper-resistant audit trails
   * Automated compliance monitoring

## Security Components

### PHI Middleware

The `PHISanitizationMiddleware` automatically redacts Protected Health Information (PHI) in API responses to prevent accidental exposure. It scans for common PHI patterns like:

* Social Security Numbers
* Email addresses
* Phone numbers
* Medical record numbers
* Credit card numbers

### JWT Authentication

The `JWTAuthMiddleware` provides secure authentication with:

* Role-based access control decorators
* Token validation and verification
* Automatic token expiration handling

### Repository Security

The repository layer implements:

* Transparent encryption/decryption of PHI fields
* Authorization checks before any data access
* Audit logging of all PHI access

### Encryption Service

Field-level encryption with:

* AES-256-GCM encryption for PHI fields
* Key rotation support
* Separate encryption contexts for different data types

## Testing Framework

### Automated Security Tests

The security testing framework includes:

1. **Unit Tests**
   * Test individual security components in isolation
   * Verify encryption/decryption functionality
   * Test authorization rules

2. **Integration Tests**
   * Test security components working together
   * Verify middleware and repository integration

3. **Security Scanning**
   * Static analysis for security vulnerabilities
   * Dependency vulnerability scanning
   * Compliance score calculation

### Running Security Tests

To run the complete security test suite:

```bash
# Windows
scripts\run_hipaa_security_tests.bat

# Linux/macOS
python -m pytest tests/security -v
python scripts/security_scanner.py --full --report
```

## Compliance Monitoring

Continuous monitoring of HIPAA compliance is performed through:

1. **GitHub Actions Workflow**
   * Runs security tests on every push and pull request
   * Performs dependency vulnerability scanning
   * Generates compliance reports

2. **Security Scanner**
   * Calculates a compliance score based on test results
   * Checks for security vulnerabilities in dependencies
   * Provides recommendations for improving compliance

## Security Requirements

The required security dependencies are defined in `requirements-security.txt` and include:

* `cryptography` - For encryption operations
* `pyjwt` - For JWT token handling
* `passlib` and `bcrypt` - For secure password hashing
* `safety` and `bandit` - For security scanning

## Development Guidelines

When developing new features:

1. **PHI Handling**
   * Never log PHI directly
   * Always use the encryption service for storing PHI
   * Validate authorization before accessing PHI

2. **API Development**
   * Apply appropriate role-based access controls
   * Use the PHI middleware for all endpoints returning patient data
   * Include audit logging for all PHI access

3. **Testing**
   * Write security tests for all new features
   * Verify authorization rules are correctly applied
   * Test error handling to ensure no PHI leakage

## Security-First Development Process

1. Run security tests frequently during development
2. Use the security scanner to check for regressions
3. Address all security warnings before merging code
4. Maintain a compliance score of at least 80%

## Reference Documentation

For more details on specific components:

* [JWT Authentication](docs/07_SECURITY_AND_COMPLIANCE.md)
* [PHI Protection](docs/10_SECURITY_IMPLEMENTATION.md)
* [Encryption](docs/16_ENCRYPTION_UTILITY.md)