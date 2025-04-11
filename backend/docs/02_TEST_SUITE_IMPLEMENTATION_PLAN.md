# Novamind Digital Twin Test Suite: Implementation Plan

This document provides a detailed, step-by-step guide for implementing the dependency-based test suite organization. It explains how to use the tools we've created and outlines the migration process in detail.

## Prerequisites

Before beginning the migration, ensure you have:

1. A complete backup of the codebase
2. All current tests passing in CI
3. Access to test environments for validation
4. Python 3.8+ with all dependencies installed

## Migration Tools

We've developed several tools to assist with the migration process:

### 1. Test Analyzer

Located at: `backend/scripts/test/tools/test_analyzer.py`

This tool analyzes the current test suite and categorizes tests by dependency level based on:
- Import statements
- Test markers
- File location
- Test content

**Usage:**
```bash
python backend/scripts/test/tools/test_analyzer.py --output-file test_analysis_results.json
```

### 2. Test Migrator

Located at: `backend/scripts/test/migrations/migrate_tests.py`

This tool physically moves test files to their new locations based on the analyzer results.

**Usage:**
```bash
python backend/scripts/test/migrations/migrate_tests.py --analysis-file test_analysis_results.json
python backend/scripts/test/migrations/migrate_tests.py --analysis-file test_analysis_results.json --dry-run
python backend/scripts/test/migrations/migrate_tests.py --analysis-file test_analysis_results.json --force
```

### 3. Test Suite Cleanup Master Script

Located at: `backend/scripts/test/test_suite_cleanup.py`

This script orchestrates the entire process, including:
- Running the analyzer
- Setting up directory structure
- Migrating tests
- Verifying migration
- Fixing common issues

**Usage:**
```bash
# Run all steps
python backend/scripts/test/test_suite_cleanup.py --all

# Run specific step
python backend/scripts/test/test_suite_cleanup.py --step 1

# Run multiple steps
python backend/scripts/test/test_suite_cleanup.py --steps 1,2,3
```

## Detailed Migration Steps

### Step 1: Analysis

Run the test analyzer to categorize existing tests:

```bash
python backend/scripts/test/tools/test_analyzer.py --output-file test_analysis_results.json
```

**Expected Output:**
- JSON file containing all test files categorized by dependency level
- Console summary showing counts for each dependency level
- List of files with syntax errors or other issues

**Review the Results:**
- Check that standalone tests don't have external dependencies
- Verify that integration tests are properly identified
- Review any syntax errors or issues

### Step 2: Directory Structure Setup

Create the new dependency-based directory structure:

```bash
python backend/scripts/test/test_suite_cleanup.py --step 2
```

This will create:
```
/backend/app/tests/
├── standalone/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── api/
│   └── core/
├── venv/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── api/
│   └── core/
└── integration/
    ├── domain/
    ├── application/
    ├── infrastructure/
    ├── api/
    └── core/
```

### Step 3: Prepare for Migration

This step creates necessary conftest.py files and prepares for migration:

```bash
python backend/scripts/test/test_suite_cleanup.py --step 3 --analysis-file test_analysis_results.json
```

**Key Tasks:**
- Creates conftest.py files in each dependency level
- Identifies fixtures that need to be moved
- Prepares import statements for updating

### Step 4: Migration

Move tests to their new locations:

```bash
# Dry run first to see what will happen
python backend/scripts/test/test_suite_cleanup.py --step 4 --analysis-file test_analysis_results.json --dry-run

# Actual migration
python backend/scripts/test/test_suite_cleanup.py --step 4 --analysis-file test_analysis_results.json
```

**Process:**
1. Tests are copied to their new location
2. Import statements are updated
3. Required fixtures are copied to the appropriate conftest.py
4. __init__.py files are created as needed

### Step 5: Verification

Verify that migrated tests still pass:

```bash
python backend/scripts/test/test_suite_cleanup.py --step 5
```

This will:
1. Run standalone tests
2. Run venv tests
3. Run integration tests
4. Generate a report of passing/failing tests

### Step 6: Import Path Updates

Fix any remaining import path issues:

```bash
python backend/scripts/test/test_suite_cleanup.py --step 6
```

This step:
1. Scans all migrated test files
2. Updates relative imports to absolute imports
3. Fixes any incorrect paths

### Step 7: Fix Broken Tests

Address any tests that failed after migration:

```bash
python backend/scripts/test/test_suite_cleanup.py --step 7
```

This will:
1. Generate a list of failing tests
2. Attempt to fix common issues automatically
3. Create a report of tests that need manual attention

### Step 8: Final Cleanup (Optional)

Once you've verified all tests are working correctly, you can clean up the original test files:

```bash
# This is a manual step that requires confirmation
python backend/scripts/test/test_suite_cleanup.py --step 8
```

**Warning:** Only perform this step after thoroughly validating that all migrated tests work correctly.

## Handling Special Cases

### Tests with Mixed Dependencies

Some tests may have mixed dependencies. Use these guidelines to categorize them:

1. **Standalone Tests with Mock External Services**
   - If all external dependencies are properly mocked, this is a standalone test
   - Replace any direct imports with mock imports

2. **Tests Using Temporary Files**
   - These should be VENV tests, not standalone
   - Move file operations to setup/teardown methods

3. **Tests with Optional Database Connections**
   - These should be integration tests
   - Use pytest's skipif to conditionally run based on available resources

### Managing Fixtures

Follow these guidelines for fixture management:

1. **Standalone Fixtures**
   - No file system or network access
   - In-memory data structures only
   - Pure function implementations

2. **VENV Fixtures**
   - Can use file system
   - Can use environment variables
   - No external services or network

3. **Integration Fixtures**
   - Database connections
   - API clients
   - External service mocks

### Marker Usage

All tests should have one of these markers:

```python
@pytest.mark.standalone
def test_standalone_feature():
    pass

@pytest.mark.venv
def test_venv_feature():
    pass

@pytest.mark.integration
def test_integration_feature():
    pass
```

Additional markers can be used for categorization:

```python
@pytest.mark.standalone
@pytest.mark.domain
def test_domain_feature():
    pass

@pytest.mark.integration
@pytest.mark.security
def test_security_feature():
    pass
```

## Continuous Integration Updates

After migration, update CI pipelines to run tests in stages:

1. **Stage 1: Standalone Tests**
   ```yaml
   standalone-tests:
     script:
       - python -m pytest backend/app/tests/standalone/
   ```

2. **Stage 2: VENV Tests**
   ```yaml
   venv-tests:
     script:
       - python -m pytest backend/app/tests/venv/
     needs:
       - standalone-tests
   ```

3. **Stage 3: Integration Tests**
   ```yaml
   integration-tests:
     script:
       - python -m pytest backend/app/tests/integration/
     needs:
       - venv-tests
   ```

## Test Writing Guidelines

For all new tests, follow these guidelines:

### Standalone Tests

```python
import pytest
from backend.app.domain.models import Patient

@pytest.mark.standalone
def test_patient_validation():
    """Test that a patient cannot be created with invalid data."""
    with pytest.raises(ValueError):
        Patient(name="", age=-1)
```

### VENV Tests

```python
import pytest
import os
import tempfile

@pytest.mark.venv
def test_config_loading():
    """Test loading configuration from a file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('{"key": "value"}')
        config_path = f.name
    
    try:
        # Test code here
        pass
    finally:
        os.unlink(config_path)
```

### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.mark.integration
def test_api_endpoint(db_session):
    """Test API endpoint with database session."""
    client = TestClient(app)
    response = client.get("/api/patients")
    assert response.status_code == 200
```

## Validation Checklist

Before considering the migration complete, verify:

- [ ] All tests pass in the new structure
- [ ] Test coverage remains the same or better
- [ ] CI pipeline successfully runs all test levels
- [ ] No test fixtures are duplicated across levels
- [ ] All tests have appropriate markers
- [ ] Documentation is updated to reflect new structure
- [ ] Team members understand the new organization

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Check relative vs. absolute imports
   - Verify __init__.py files exist
   - Ensure import paths are correct

2. **Missing Fixtures**
   - Look for fixtures in the original location
   - Check if fixtures were moved to conftest.py
   - Verify fixture dependencies

3. **Permission Errors**
   - Check file permissions on new test directories
   - Ensure write permissions for temporary files

4. **Skipped Tests**
   - Review skipif conditions
   - Check for environment-specific skip markers

### Getting Help

If you encounter issues not covered in this document:

1. Check the logs in the `backend/logs/test_migration/` directory
2. Run the problematic test with the `-v` flag for more detail
3. Use the `--debug` flag on migration tools for verbose output
4. Consult the test suite documentation for specific guidance

## Conclusion

Following this implementation plan will help ensure a smooth migration to the dependency-based test structure. The result will be a more maintainable, faster, and more reliable test suite that supports the continued development of the Novamind Digital Twin platform.