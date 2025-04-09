# Novamind HIPAA Security Testing Framework

This repository contains a comprehensive HIPAA security testing framework for the Novamind concierge psychiatry platform. The framework performs a series of security checks, compliance validations, and vulnerability scans to ensure that the platform meets HIPAA security requirements.

## Overview

The HIPAA Security Testing Framework is designed to:

- Run security unit tests that validate encryption, authentication, authorization, and PHI protection
- Perform static code analysis to identify potential security vulnerabilities in the codebase
- Check dependencies for known security vulnerabilities
- Generate comprehensive reports for security audits and compliance documentation

## Unified WSL2-Based Testing Architecture

To ensure consistency across all environments, this framework now uses a unified WSL2-based approach:

- **Consistent Environment**: All tests run within WSL2 Ubuntu 22.04, even when triggered from Windows
- **Normalized Paths**: Automatic path handling between Windows and WSL2 environments
- **Standardized Tools**: Using the same tools across platforms (pytest, bandit, pip-audit/safety)
- **Seamless Report Generation**: Reports are accessible from both Windows and WSL2

## Prerequisites

### Required Software

- **WSL2 with Ubuntu 22.04**: Required for consistent test execution
- **Python 3.8+**: The core testing framework runs on Python
- **PowerShell 5.1+**: For Windows users preferring PowerShell
- **Bash shell**: Available in WSL2 environment

### Python Dependencies

The following Python packages are required and will be automatically installed if missing:

- pytest
- pytest-html
- bandit
- pip-audit (or safety for Linux/WSL)

## Running the Tests

### Windows Users

Run the batch script (which uses WSL2 under the hood):

```cmd
# Basic usage
scripts\run_hipaa_security.bat

# With additional options
scripts\run_hipaa_security.bat --report-dir=security-reports --verbose
```

Available parameters:

- `--report-dir=DIR`: Directory where reports will be saved (default: "security-reports")
- `--verbose`: Enable detailed output
- `--skip-static`: Skip static code analysis
- `--skip-dependency`: Skip dependency vulnerability check
- `--skip-phi`: Skip PHI pattern detection
- `--help`: Show help message

### WSL/Linux Users

Use the shell script directly:

```bash
# Ensure script is executable
chmod +x scripts/run_hipaa_security.sh

# Basic usage
./scripts/run_hipaa_security.sh

# With additional options
./scripts/run_hipaa_security.sh --report-dir=security-reports --verbose
```

The parameters are the same as for the Windows batch script.

### For PowerShell Users (Legacy)

The PowerShell script is still available but uses the same unified approach:

```powershell
# Basic usage
.\Run-HIPAASecurityTests.ps1

# With additional options
.\Run-HIPAASecurityTests.ps1 -ReportDir "security-reports" -Verbose
```

## Understanding the Results

After running the tests, several reports will be generated in the specified report directory:

### Security Test Report

- `security-report.html`: Comprehensive HTML report of all security tests
- `security-test-output.log`: Raw output from the security tests

### Static Analysis Report

- `static-analysis-{timestamp}.json`: JSON report of static code analysis findings
- `static-analysis-{timestamp}.html`: HTML report of static code analysis findings

### Dependency Vulnerability Report

- `dependency-check-requirements.txt.json`: JSON report of vulnerabilities in main requirements
- `dependency-check-requirements-dev.txt.json`: JSON report of vulnerabilities in dev requirements
- `dependency-check-requirements-security.txt.json`: JSON report of vulnerabilities in security requirements

### PHI Pattern Detection Report

- `phi-pattern-detection.log`: Results of scanning for potential PHI patterns in code

### Consolidated Report

- `security-report.md`: Markdown summary of all test results
- `security-report.html`: HTML version of the summary report (if pandoc is installed)

## Compliance Status

The framework categorizes compliance status as follows:

- **COMPLIANT**: All tests pass, no vulnerabilities detected
- **PARTIALLY COMPLIANT**: Some tests pass, but vulnerabilities or issues exist
- **NON-COMPLIANT**: Critical tests fail or high-severity vulnerabilities detected

## Integrating with CI/CD

The framework can be integrated into CI/CD pipelines using GitHub Actions, Jenkins, or similar CI/CD tools. Sample GitHub Actions workflow:

```yaml
name: HIPAA Security Checks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  security-tests:
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
          pip install -r requirements-security.txt
      - name: Run HIPAA security tests
        run: |
          python scripts/hipaa_security_runner.py --report-dir=security-reports
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: security-reports/
```

## Troubleshooting

### Common Issues

1. **WSL2 Not Available**:
   - Error: "WSL is not available..."
   - Solution: Install WSL2 with Ubuntu 22.04 using `wsl --install -d Ubuntu-22.04`

2. **Missing Python Dependencies**:
   - Error: "ModuleNotFoundError: No module named 'pytest'"
   - Solution: The script will attempt to install missing dependencies automatically

3. **Permission Issues (Linux/WSL)**:
   - Error: "Permission denied: './run_hipaa_security.sh'"
   - Solution: Run `chmod +x scripts/run_hipaa_security.sh`

4. **Path Issues Between Windows and WSL**:
   - Error: "No such file or directory"
   - Solution: The runner uses path normalization automatically, but if issues persist, check relative paths

5. **Test Failures**:
   - Error: Various test failures in security tests
   - Solution: Review the HTML reports for specific issues and fix the underlying code

### Support

For additional support or assistance with this framework, please contact the security team at security@novamind.com.

## License

This HIPAA Security Testing Framework is proprietary software owned by Novamind Inc. and is not licensed for redistribution or use outside of the organization.

## Security Policy

To report security vulnerabilities or concerns, please email security@novamind.com or use our responsible disclosure program at https://novamind.com/security.