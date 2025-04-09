# Novamind HIPAA Security Testing Framework

This repository contains a comprehensive HIPAA security testing framework for the Novamind concierge psychiatry platform. The framework performs a series of security checks, compliance validations, and vulnerability scans to ensure that the platform meets HIPAA security requirements.

## Overview

The HIPAA Security Testing Framework is designed to:

- Run security unit tests that validate encryption, authentication, authorization, and PHI protection
- Perform static code analysis to identify potential security vulnerabilities in the codebase
- Check dependencies for known security vulnerabilities
- Generate comprehensive reports for security audits and compliance documentation

## Cross-Platform Support

This testing framework is designed to work seamlessly across different environments:

- **Windows**: Native support using PowerShell script and Windows-compatible Python runner
- **Linux/WSL**: Full support via shell scripts and Python
- **macOS**: Compatible via Python runner

## Prerequisites

### Required Software

- **Python 3.8+**: The core testing framework runs on Python
- **PowerShell 5.1+**: For Windows users using the PowerShell wrapper
- **Bash shell**: For Linux/WSL/macOS users using the shell script

### Python Dependencies

The following Python packages are required:

- pytest
- pytest-html
- bandit
- pip-audit (or safety for Linux/WSL)

The PowerShell and Python scripts will attempt to install missing dependencies automatically.

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/your-org/novamind-backend.git
cd novamind-backend
```

### Windows Setup

Ensure Python 3.8+ is installed and available in your PATH. Then run:

```powershell
# Install required Python packages
pip install -r requirements-security.txt
```

### Linux/WSL/macOS Setup

```bash
# Ensure script is executable
chmod +x run_hipaa_tests.sh

# Install required Python packages
pip3 install -r requirements-security.txt
```

## Running the Tests

### Windows (PowerShell)

The PowerShell script provides an easy-to-use interface for Windows users:

```powershell
# Basic usage
.\Run-HIPAASecurityTests.ps1

# With additional options
.\Run-HIPAASecurityTests.ps1 -ReportDir "compliance-reports" -Verbose -ApiUrl "https://dev-api.novamind.com"
```

Available parameters:

- `-ReportDir`: Directory where reports will be saved (default: "security-reports")
- `-Verbose`: Enable detailed output
- `-SkipStatic`: Skip static code analysis
- `-SkipDependency`: Skip dependency vulnerability check
- `-ApiUrl`: Base URL of the API to test (default: "http://localhost:8000")

### Cross-Platform Python Script

The Python script works across all platforms:

```bash
# Windows
python run_hipaa_security_suite_windows.py

# Linux/WSL/macOS
python3 run_hipaa_security_suite_windows.py
```

Command-line arguments:

```
usage: run_hipaa_security_suite_windows.py [-h] [--api-url API_URL] [--report-dir REPORT_DIR] [--skip-static] [--skip-dependency] [--verbose]

HIPAA Security Testing Suite Runner

optional arguments:
  -h, --help           show this help message and exit
  --api-url API_URL    Base URL of the API to test
  --report-dir DIR     Directory to save reports
  --skip-static        Skip static code analysis
  --skip-dependency    Skip dependency vulnerability check
  --verbose            Enable verbose output
```

### Traditional Shell Script (Linux/WSL/macOS)

For Linux, WSL, or macOS users, the traditional shell script is also available:

```bash
# Basic usage
./run_hipaa_tests.sh

# With additional options
./run_hipaa_tests.sh --report-dir=compliance-reports --verbose --url=https://dev-api.novamind.com
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
          python run_hipaa_security_suite_windows.py --report-dir=security-reports
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: security-reports/
```

## Troubleshooting

### Common Issues

1. **Missing Python Dependencies**:
   - Error: "ModuleNotFoundError: No module named 'pytest'"
   - Solution: Run `pip install -r requirements-security.txt`

2. **Permission Issues (Linux/WSL/macOS)**:
   - Error: "Permission denied: './run_hipaa_tests.sh'"
   - Solution: Run `chmod +x run_hipaa_tests.sh`

3. **Path Issues in Windows**:
   - Error: "'python' is not recognized as an internal or external command"
   - Solution: Ensure Python is installed and added to PATH environment variable

4. **Test Failures**:
   - Error: Various test failures in security tests
   - Solution: Review the HTML reports for specific issues and fix the underlying code

### Support

For additional support or assistance with this framework, please contact the security team at security@novamind.com.

## License

This HIPAA Security Testing Framework is proprietary software owned by Novamind Inc. and is not licensed for redistribution or use outside of the organization.

## Security Policy

To report security vulnerabilities or concerns, please email security@novamind.com or use our responsible disclosure program at https://novamind.com/security.