# HIPAA Compliance and Project Cleanup Instructions

This document provides step-by-step instructions for bringing the Novamind Backend platform up to HIPAA compliance standards (80% test coverage) and restoring the project structure to Clean Architecture principles.

## 📋 Prerequisites

- Python 3.8+ installed
- Pytest installed (`pip install pytest pytest-cov`)
- Project dependencies installed

## 🔄 Quick Reference

For the fastest path to compliance:

```bash
# Fix core PHI audit issues
python scripts/security_utils/fix_phi_audit_issues.py

# Cleanup project structure
python cleanup_project_structure.py

# Run coverage check to identify gaps
python scripts/check_test_coverage.py

# Alternative: Run all steps in sequence
python run_project_cleanup_and_check.py
```

## 🔍 Detailed Instructions

### Step 1: Fix Core PHI Audit Issues

The first step is to fix the core PHI audit functionality, which was causing test failures:

```bash
python scripts/security_utils/fix_phi_audit_issues.py
```

This script fixes three critical issues:
1. Incorrect clean_app directory handling in `_audit_passed` method
2. Improper SSN pattern detection
3. Issues with identifying PHI test files

Verify the fix by running the PHI audit tests:

```bash
python -m pytest tests/security/test_phi_audit.py -v
```

### Step 2: Clean Up Project Structure

Next, reorganize the project files to follow Clean Architecture principles:

```bash
python cleanup_project_structure.py
```

This script:
- Moves scripts to appropriate directories
- Properly organizes test files
- Cleans up temporary and backup files
- Structures config files correctly

The script will provide a detailed report of files moved and deleted.

### Step 3: Check Test Coverage

Check if the project meets the 80% test coverage requirement:

```bash
python scripts/check_test_coverage.py
```

This will:
- Run pytest with coverage analysis
- Generate an HTML coverage report in `coverage-reports/html/`
- Identify modules with less than 50% coverage
- Prioritize security-related modules
- Show if the 80% HIPAA requirement is met

If coverage is less than 80%, focus on writing tests for the high-priority modules identified in the report.

### Step 4: Run All Steps in Sequence

For convenience, you can run all steps in sequence with appropriate backup and verification:

```bash
python run_project_cleanup_and_check.py
```

This script will:
1. Create a backup of your project
2. Fix PHI audit issues
3. Reorganize project structure
4. Check test coverage
5. Verify the results

## 🧪 Adding Tests for Low Coverage Modules

If test coverage is below 80%, add tests for modules with low coverage:

1. Focus on high-priority modules first:
   - `app/infrastructure/security/`
   - `app/core/utils/`
   - `app/domain/entities/`
   - `app/domain/services/`

2. Create test files following the naming convention:
   ```
   app/infrastructure/security/log_sanitizer.py
   → tests/unit/infrastructure/security/test_log_sanitizer.py
   ```

3. Run tests and check coverage iteratively:
   ```bash
   # After adding tests
   python scripts/check_test_coverage.py
   ```

4. Format and lint all new test files:
   ```bash
   black tests/unit/path/to/test_file.py
   flake8 tests/unit/path/to/test_file.py
   ```

## 🔒 PHI Sanitization Testing

When testing PHI sanitization, follow these practices:

1. Use fabricated examples that look like PHI but aren't real:
   ```python
   # Good: Clearly fake test data
   fake_ssn = "123-45-6789"
   fake_name = "John Doe"
   
   # Bad: Using realistic data patterns
   real_looking_ssn = "531-72-8314"  # Don't do this!
   ```

2. Verify sanitization works correctly:
   ```python
   def test_ssn_sanitization():
       """Test that SSNs are properly sanitized."""
       original = "SSN: 123-45-6789"
       expected = "SSN: [REDACTED]"
       result = sanitizer.sanitize_text(original)
       assert result == expected
   ```

3. Always mark test files containing PHI patterns:
   ```python
   # This file contains fake PHI patterns for testing purposes
   # All patterns are fabricated and do not represent actual individuals
   ```

## 🧹 Maintaining Clean Project Structure

After compliance is achieved, maintain the clean structure:

1. Keep Python scripts organized:
   - General scripts → `scripts/`
   - Security utilities → `scripts/security_utils/`
   - Testing utilities → `scripts/test_utils/`

2. Follow test hierarchy:
   - Unit tests → `tests/unit/`
   - Integration tests → `tests/integration/`
   - Security tests → `tests/security/`
   - End-to-end tests → `tests/e2e/`

3. Keep the root directory clean:
   - Only core configuration files
   - Main application entry points
   - Essential documentation

## 📈 Regular Compliance Checks

Schedule regular compliance checks:

```bash
# Add to CI/CD pipeline or run weekly
python scripts/check_test_coverage.py
```

For a full compliance audit:

```bash
python run_project_cleanup_and_check.py
```

## 🏁 Final Verification

To verify that the project is fully compliant:

1. Ensure all tests pass:
   ```bash
   python -m pytest
   ```

2. Verify test coverage meets the 80% requirement:
   ```bash
   python scripts/check_test_coverage.py
   ```

3. Check for any remaining unorganized files:
   ```bash
   # Should not return unexpected Python files
   find . -maxdepth 1 -name "*.py" ! -name "main.py" ! -name "run_project_cleanup_and_check.py" ! -name "cleanup_project_structure.py"
   ```

## 📚 Additional Documentation

For more information, refer to:

- `HIPAA_TEST_COVERAGE_README.md` - Detailed explanation of test coverage requirements
- `docs/HIPAA_SECURITY_TESTING.md` - Security testing guidelines
- `docs/15_LOGGING_UTILITY.md` - PHI-safe logging practices
- `docs/16_ENCRYPTION_UTILITY.md` - Data encryption requirements

---

*This project follows Clean Architecture principles and adheres to HIPAA requirements for a concierge psychiatry platform that prioritizes patient privacy and data security.*