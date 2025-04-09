# NOVAMIND HIPAA Security Testing Suite

## Overview

The NOVAMIND HIPAA Security Testing Suite is a comprehensive set of tools designed to validate HIPAA compliance and ensure robust security controls throughout the NOVAMIND concierge psychiatry platform. This suite provides automated testing, vulnerability scanning, compliance checking, and documentation generation to maintain the highest standards of patient data protection.

## Components

The HIPAA Security Testing Suite includes the following components:

1. **Security Scanner** - Comprehensive code analysis for security vulnerabilities
2. **HIPAA Compliance Tests** - Specific tests for HIPAA technical safeguards
3. **Security Test Runner** - Orchestrates all security tests with detailed reporting
4. **Dependency Security Checker** - Identifies vulnerable dependencies
5. **HIPAA Compliance CLI** - Unified command-line interface for all security operations

## Installation

### Prerequisites

- Python 3.9+
- Pip package manager
- Pytest testing framework

### Setup

1. Install required dependencies:

```bash
# Install security testing dependencies
pip install -r requirements-security.txt
```

2. Make scripts executable (Linux/WSL):

```bash
# For Linux/WSL environments
chmod +x scripts/security_scanner.py
chmod +x scripts/run_security_tests.py
chmod +x scripts/hipaa_compliance_check.sh
chmod +x scripts/novamind_hipaa.py
```

3. For Windows environments, run the Python scripts directly:

```powershell
# For Windows environments
python scripts/security_scanner.py
python scripts/run_security_tests.py
python scripts/novamind_hipaa.py test
```

## Usage

### Security Scanner

The security scanner examines your codebase for potential security vulnerabilities, with special focus on HIPAA-relevant issues.

```bash
# Linux/WSL
./scripts/security_scanner.py --verbose

# Windows
python scripts/security_scanner.py --verbose
```

### HIPAA Compliance Shell Script

For Linux/WSL users, this shell script provides a convenient way to run the full compliance suite:

```bash
# Run with HTML report generation
./scripts/hipaa_compliance_check.sh --html-report

# Skip vulnerability scanning (faster)
./scripts/hipaa_compliance_check.sh --skip-scan

# Show detailed output
./scripts/hipaa_compliance_check.sh --verbose
```

### HIPAA Compliance CLI

The HIPAA CLI tool provides a comprehensive interface to all security testing features:

```bash
# Run HIPAA compliance tests
python scripts/novamind_hipaa.py test --html

# Scan codebase for security vulnerabilities
python scripts/novamind_hipaa.py scan --verbose

# Check dependencies for security vulnerabilities
python scripts/novamind_hipaa.py check-deps

# Run full compliance audit with comprehensive report
python scripts/novamind_hipaa.py audit

# Attempt to fix common security issues
python scripts/novamind_hipaa.py fix --all

# Generate compliance documentation
python scripts/novamind_hipaa.py doc
```

## HIPAA Compliance Testing

The suite includes specific tests to validate HIPAA compliance requirements:

```bash
# Run HIPAA-specific compliance tests
python -m pytest tests/security/test_hipaa_compliance.py -v
```

## Continuous Integration

To integrate the HIPAA security testing in your CI/CD pipeline, add this step to your workflow:

```yaml
steps:
  - name: Run HIPAA Compliance Tests
    run: |
      pip install -r requirements-security.txt
      python scripts/novamind_hipaa.py audit
```

## Reports

Security test reports are generated in the `reports/security/` directory:

- **HTML Reports**: Detailed HTML reports showing test results
- **Audit Reports**: Comprehensive compliance audit reports
- **Vulnerability Reports**: Identified security vulnerabilities

## Best Practices

1. **Run Before Deployments**: Always run the full compliance suite before deploying to production.
2. **Review Reports**: Carefully review generated reports for any security issues.
3. **Fix All Issues**: Address all identified security vulnerabilities before releasing code.
4. **Regular Audits**: Schedule regular security audits (at least monthly).

## HIPAA Technical Safeguards Tested

The suite verifies compliance with HIPAA technical safeguards:

1. **Access Controls** (§164.312(a)(1))
   - Authentication mechanisms
   - Authorization controls
   - Automatic logoff
   - Encryption and decryption

2. **Audit Controls** (§164.312(b))
   - Logging of activity in systems containing PHI
   - Recording of access attempts

3. **Integrity Controls** (§164.312(c)(1))
   - Mechanisms to ensure PHI is not improperly altered or destroyed
   - Data validation controls

4. **Transmission Security** (§164.312(e)(1))
   - Encryption of data in transit
   - Integrity verification

## Documentation

For more detailed information, please refer to:

- [HIPAA Compliance Testing Framework](HIPAA_COMPLIANCE_TESTING.md): Comprehensive guide to the testing framework
- [Security Controls Implementation](hipaa/SECURITY_CONTROLS_IMPLEMENTATION.md): Detailed information on security controls
- [HIPAA Risk Assessment](hipaa/HIPAA_RISK_ASSESSMENT_TEMPLATE.md): Template for conducting risk assessments

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure you've installed all dependencies with `pip install -r requirements-security.txt`
2. **Permission denied**: Make sure scripts are executable (Linux/WSL) with `chmod +x scripts/*.py scripts/*.sh`
3. **Test failures**: Review the detailed HTML reports to understand specific test failures

### Getting Help

If you encounter issues with the HIPAA Security Testing Suite, please contact the security team for assistance.

---

**Last Updated**: March 27, 2025