# Test Suite Implementation Plan

This document outlines the concrete steps to transition from the current fragmented test suite to the ideal unified test architecture for the Novamind Digital Twin Platform.

## Migration Strategy Overview

The migration will follow these three phases:

1. **Preparation Phase**: Create directory structure and update configuration
2. **Migration Phase**: Organize and move tests
3. **Enhancement Phase**: Improve coverage and add missing tests

## Phase 1: Preparation

### Step 1.1: Create Missing Directory Structure

First, create the missing directory structure in `/backend/app/tests/`:

```bash
# Create main test category directories
mkdir -p backend/app/tests/unit
mkdir -p backend/app/tests/integration
mkdir -p backend/app/tests/security
mkdir -p backend/app/tests/e2e
mkdir -p backend/app/tests/enhanced

# Create subdirectories for unit tests
mkdir -p backend/app/tests/unit/domain/{entities,value_objects,services}
mkdir -p backend/app/tests/unit/application/{use_cases,services}
mkdir -p backend/app/tests/unit/core/{config,services}
mkdir -p backend/app/tests/unit/infrastructure/{security,persistence,logging}

# Create security test subdirectories
mkdir -p backend/app/tests/security/{audit,encryption,auth,jwt,phi,hipaa}
```

### Step 1.2: Update Test Configuration

Update the `pytest.ini` file to ensure it recognizes tests in all directories:

```ini
# backend/pytest.ini
[pytest]
testpaths =
    backend/app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    security: Security tests
    e2e: End-to-end tests
    slow: Slow running tests
    phi: PHI-related tests
addopts = --strict-markers
```

### Step 1.3: Update Test Runner Script

Update the `run_tests.py` script to recognize the new test paths:

```python
# In run_tests.py, update the _run_unit_tests method
def run_unit_tests(self, coverage=False, verbose=False, 
                  fail_under=80, html=False, 
                  xml=False, json=False) -> bool:
    print("\n" + "="*80)
    print("Running Unit Tests")
    print("="*80 + "\n")
    
    # Updated path to use the unified structure
    test_paths = [str(self.test_dir / "unit")]
    
    success, results = self._run_pytest(
        test_paths=test_paths,
        coverage=coverage,
        verbose=verbose,
        fail_under=fail_under,
        html=html,
        xml=xml,
        json=json,
        markers="unit",
    )
    
    self.results["unit"] = results
    return success

# Similar updates for run_integration_tests, run_security_tests, etc.
```

## Phase 2: Migration

### Step 2.1: Create Base Test Classes

Create base test classes for each test category to ensure consistent test structure:

```python
# backend/app/tests/unit/base_test.py
import pytest
from unittest import TestCase

class BaseUnitTest(TestCase):
    """Base class for all unit tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        pass
        
    def tearDown(self):
        """Tear down test fixtures."""
        pass

# backend/app/tests/security/base_test.py
class BaseSecurityTest(TestCase):
    """Base class for all security tests."""
    
    def setUp(self):
        """Set up test fixtures with enhanced security context."""
        # Setup enhanced security fixtures
        pass
```

### Step 2.2: Create Core Fixtures

Create shared fixtures in conftest.py files:

```python
# backend/app/tests/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_settings():
    """Create a mock settings object."""
    settings = MagicMock()
    settings.AUDIT_LOG_LEVEL = "INFO"
    settings.AUDIT_LOG_TO_FILE = False
    settings.JWT_SECRET_KEY = "test_secret_key"
    settings.JWT_TOKEN_EXPIRE_MINUTES = 30
    return settings

@pytest.fixture
def test_patient_data():
    """Create test patient data without real PHI."""
    return {
        "id": "test-patient-123",
        "name": "Anonymous Patient",
        "dob": "1990-01-01",
        "medical_record_number": "MRN12345"
    }
```

### Step 2.3: Migrate ML Mock Tests

These tests are already working, so migrate them to the new structure maintaining their current functionality:

```python
# Copy from backend/app/tests/core/services/ml/test_mock.py to
# backend/app/tests/unit/core/services/ml/test_mock.py

# Make sure imports are updated if needed
```

### Step 2.4: Migrate Security Tests

Copy security tests from `/backend/tests/security/` to `/backend/app/tests/security/`:

```bash
# Use cp command to copy each test while preserving structure
cp backend/tests/security/test_encryption.py backend/app/tests/security/encryption/test_encryption.py
cp backend/tests/security/test_jwt_service.py backend/app/tests/security/jwt/test_jwt_service.py
# ... etc for other security tests
```

Update imports in the copied files to ensure they work in the new location.

### Step 2.5: Create Core-to-Infrastructure Bridge Tests

Create adapters that bridge between expected locations and actual implementations:

```python
# backend/app/tests/unit/core/audit/test_audit_bridge.py
import pytest
from app.infrastructure.security.audit import AuditLogger

class TestAuditBridge:
    """Tests that verify the audit functionality works regardless of location."""
    
    def test_audit_logger_logs_phi_access(self):
        """Test that PHI access is logged."""
        # Test using the implementation in infrastructure
        logger = AuditLogger()
        logger.log_phi_access(
            user_id="test-user",
            action="view",
            resource_type="patient",
            resource_id="test-patient-123",
            details={"reason": "test"}
        )
        # Assert based on logger behavior
```

## Phase 3: Enhancement

### Step 3.1: Create Missing Security Tests

Create any missing security tests based on the HIPAA requirements:

```python
# backend/app/tests/security/phi/test_phi_redaction.py
import pytest
from app.infrastructure.security.log_sanitizer import PHISanitizer

class TestPHIRedaction:
    """Tests for PHI redaction functionality."""
    
    def test_phi_redacted_from_logs(self):
        """Test that PHI is properly redacted from logs."""
        sanitizer = PHISanitizer()
        original = "Patient John Smith (DOB: 01/01/1980) reports symptoms."
        sanitized = sanitizer.sanitize(original)
        
        assert "John Smith" not in sanitized
        assert "01/01/1980" not in sanitized
        assert "reports symptoms" in sanitized
```

### Step 3.2: Update Coverage Configuration

Create a comprehensive `.coveragerc` file:

```ini
# backend/.coveragerc
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */settings/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError
```

### Step 3.3: Create Enhanced Test Wrapper Script

Create a script that runs all tests and generates a comprehensive report:

```python
# backend/scripts/run_comprehensive_tests.py
#!/usr/bin/env python3
"""
Comprehensive Test Runner that generates detailed reports.
"""
import os
import subprocess
import datetime

# Define test categories
categories = [
    {"name": "Unit Tests", "flag": "--unit"},
    {"name": "Integration Tests", "flag": "--integration"},
    {"name": "Security Tests", "flag": "--security"},
    {"name": "ML Mock Tests", "flag": "--ml-mock"}
]

# Run all test categories with coverage
results = {}
for category in categories:
    print(f"Running {category['name']}...")
    cmd = ["./run-tests.sh", category["flag"], "--coverage", "--verbose"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    results[category["name"]] = {
        "success": proc.returncode == 0,
        "output": proc.stdout,
        "error": proc.stderr
    }

# Generate a consolidated report
report_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = f"reports/test_report_{report_date}.md"
os.makedirs("reports", exist_ok=True)

with open(report_path, "w") as f:
    f.write("# Comprehensive Test Report\n\n")
    f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Summary table
    f.write("## Summary\n\n")
    f.write("| Test Category | Status | Notes |\n")
    f.write("|--------------|--------|-------|\n")
    
    for category, result in results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        f.write(f"| {category} | {status} | |\n")
    
    # Detailed results
    f.write("\n## Detailed Results\n\n")
    for category, result in results.items():
        f.write(f"### {category}\n\n")
        f.write("```\n")
        f.write(result["output"])
        f.write("\n```\n\n")
        
        if result["error"]:
            f.write("#### Errors\n\n")
            f.write("```\n")
            f.write(result["error"])
            f.write("\n```\n\n")

print(f"Comprehensive test report generated at {report_path}")
```

## Phase-by-Phase Implementation

### Implementation Order

1. **Week 1**: Complete Preparation Phase
   - Create directory structure
   - Update configuration files
   - Create base test classes and fixtures

2. **Week 2**: Complete Migration Phase (Part 1)
   - Migrate ML mock tests
   - Create bridge tests for core components

3. **Week 3**: Complete Migration Phase (Part 2)
   - Migrate security tests
   - Update imports and fix any issues

4. **Week 4**: Complete Enhancement Phase
   - Create missing security tests
   - Implement enhanced reporting
   - Achieve coverage targets

### Validation

After each phase, run the following validation:

```bash
# Run all tests to verify nothing broke
./run-tests.sh --all --verbose

# Generate coverage report
./scripts/generate_test_coverage.py --html

# Verify directory structure
find backend/app/tests -type d | sort
```

## Conclusion

This implementation plan provides a clear, step-by-step approach to transitioning from the current fragmented test architecture to a clean, unified structure. Following this plan will ensure that the Novamind Digital Twin Platform has comprehensive test coverage that meets HIPAA requirements and maintains the highest standards of software quality.