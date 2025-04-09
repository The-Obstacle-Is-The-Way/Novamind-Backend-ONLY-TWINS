# HIPAA Security Testing Framework

This documentation describes the unified HIPAA security testing framework for Novamind's concierge psychiatry platform. The framework provides a consistent interface for running HIPAA security tests across both Windows and WSL2 environments.

## Overview

The security testing framework performs comprehensive assessment of the platform's security posture, with a focus on HIPAA compliance. It includes:

1. **Static code analysis** - Using Bandit to identify potential security vulnerabilities in the codebase
2. **Dependency vulnerability checks** - Using pip-audit to scan dependencies for known vulnerabilities
3. **PHI pattern detection** - Custom scanning to identify potential PHI exposure patterns in the code

## Directory Structure

```
scripts/
  ├── run_hipaa_security_suite.py   # Core Python implementation
  ├── run_hipaa_security.sh         # WSL2/Linux shell wrapper
  ├── run_hipaa_security.bat        # Windows batch file wrapper
  └── Run-HIPAASecurityTests.ps1    # PowerShell wrapper (legacy support)
```

## Running Security Tests

### From Windows

You can run the security tests using any of these methods:

1. **Using Batch File (Recommended)**:
   ```
   scripts\run_hipaa_security.bat [options]
   ```

2. **Using PowerShell**:
   ```powershell
   .\scripts\Run-HIPAASecurityTests.ps1 [options]
   ```

### From WSL2

```bash
./scripts/run_hipaa_security.sh [options]
```

### Options

All interfaces support the same options:

- `--verbose` - Enable verbose output
- `--skip-static` - Skip static code analysis
- `--skip-dependency` - Skip dependency vulnerability checks
- `--skip-phi` - Skip PHI pattern detection
- `--report-dir=DIR` - Directory to save reports (default: `security-reports`)

## Reports

Reports are saved to the specified output directory (default: `security-reports/`). The following reports are generated:

- `static-analysis-{timestamp}.html` - HTML report from static code analysis
- `static-analysis-{timestamp}.json` - JSON report from static code analysis
- `dependency-report-{timestamp}.json` - Aggregated results from dependency checks
- `dependency-check-requirements*.json` - Detailed dependency check results per requirements file
- `hipaa_security_report_{timestamp}.json` - PHI pattern detection results
- `security-report.html` - Summary HTML report with overall results
- `security-report.json` - Summary JSON report with overall results
- `security-report.md` - Summary Markdown report with overall results

## Requirements

The framework requires Python 3.7+ and the following tools in the WSL2 environment:

- `bandit` - For static code analysis
- `pip-audit` - For dependency vulnerability checks

You can install these tools using:

```bash
pip install bandit pip-audit
```

## Implementation Details

### Cross-Platform Compatibility

The framework is designed to work across Windows and WSL2/Linux environments:

- Windows scripts automatically convert paths to WSL2 format using `wslpath`
- All testing is performed in the WSL2 environment for consistency
- Reports are stored in a location accessible from both environments

### WSL2 Integration

The system uses WSL2 to execute security tests even when launched from Windows. This ensures:

1. Consistent testing environment regardless of launch method
2. Access to Linux security tools not easily available on Windows
3. Portable testing between development and CI/CD environments

## CI/CD Integration

This framework can be integrated into CI/CD pipelines for automated security testing. The exit code of all scripts indicates success (0) or failure (non-zero) based on security findings.

Example GitHub Actions integration:

```yaml
name: HIPAA Security Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  hipaa-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bandit pip-audit
          if [ -f requirements-security.txt ]; then pip install -r requirements-security.txt; fi
      - name: Run HIPAA Security Tests
        run: |
          ./scripts/run_hipaa_security.sh
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: security-reports/
```

## Extending the Framework

To add new security checks, modify the `run_hipaa_security_suite.py` script and add new test functions. Follow the pattern of existing tests and update the `main()` function to include your new test.