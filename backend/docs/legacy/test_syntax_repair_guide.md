# Test Suite Syntax Repair Guide

This document provides guidance for fixing the syntax errors identified in our test suite during the migration process. Our analysis identified 134 test files with syntax errors that need to be addressed.

## Common Syntax Errors

The following patterns of errors were identified:

1. **Invalid Syntax in Function/Class Definitions**:
   - Missing colons after function declarations
   - Unexpected indentation
   - Improper class declaration

2. **Attribute Errors**:
   - Most common: `'Attribute' object has no attribute 'id'`
   - Likely caused by improper imports or missing mock objects

3. **Indentation Errors**:
   - Unexpected unindent
   - Expected indented block

## Repair Process

### Step 1: Run the Test Error Analysis

```bash
# Generate a comprehensive report of all test file errors
python backend/scripts/test/syntax_error_analyzer.py
```

### Step 2: Fix Common Patterns

#### Missing Colons

Look for functions and class definitions without colons:

```python
# Incorrect
def test_something()
    assert True

# Correct
def test_something():
    assert True
```

#### Indentation Issues

Fix indentation to follow consistent 4-space pattern:

```python
# Incorrect
def test_something():
assert True

# Correct
def test_something():
    assert True
```

#### Attribute Errors

Most `'Attribute' object has no attribute 'id'` errors are caused by:

1. Improper mocking:
```python
# Incorrect
mock_obj = Mock()
result = function_under_test(mock_obj.id)  # mock_obj.id doesn't exist yet

# Correct
mock_obj = Mock()
mock_obj.id = "test-id"
result = function_under_test(mock_obj.id)
```

2. Missing imports:
```python
# Correct imports for common objects
from unittest.mock import Mock, MagicMock, patch
import pytest
from pytest import raises, fixture
```

### Step 3: Specific File Categories

Based on our analysis, we can group the files with errors into categories:

#### 1. Simple Syntax Errors (Quick fixes)

Files with simple syntax errors like missing colons or indentation issues:

```
backend/app/tests/security/test_log_sanitization.py
backend/app/tests/unit/domain/entities/test_biometric_twin.py
backend/app/tests/unit/services/ml/pat/test_pat_service.py
```

#### 2. Complex Structural Errors (Need deeper review)

Files with more complex issues like multiple errors or logical issues:

```
backend/app/tests/security/test_hipaa_compliance.py
backend/app/tests/security/test_ml_phi_security.py
backend/app/tests/integration/test_temporal_neurotransmitter_integration.py
```

#### 3. Import/Dependency Errors

Files with issues related to imports or dependencies:

```
backend/app/tests/core/services/ml/xgboost/test_aws_xgboost_service.py
backend/app/tests/integration/test_mentallama_api.py
backend/app/tests/unit/core/services/ml/test_mock.py
```

### Step 4: Testing After Fixes

After fixing syntax errors in each file:

1. Run pytest on just that file to verify the syntax is correct:
   ```bash
   pytest backend/app/tests/path/to/fixed_file.py -v
   ```

2. If the test passes syntax checking but fails for other reasons, mark it with appropriate skip markers until those issues can be addressed:
   ```python
   @pytest.mark.skip(reason="Dependency on external service not available in test environment")
   def test_external_integration():
       ...
   ```

## Repair Script

We've created a script to help identify and fix common syntax errors:

```bash
# Run the repair script
python backend/scripts/test/repair_test_syntax.py
```

This script can automatically fix many common issues like:
- Adding missing colons
- Fixing indentation issues
- Adding missing imports
- Adding proper fixture declarations

For files that cannot be automatically fixed, the script will provide detailed error information to assist with manual repairs.

## Priority Order

Fix files in this order:

1. Standalone tests with syntax errors
2. Venv tests with syntax errors
3. Integration tests with syntax errors
4. Unknown classification tests with syntax errors

## Tracking Progress

Use the following command to track progress on syntax error fixes:

```bash
# Count remaining files with syntax errors
find backend/app/tests -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep "SyntaxError" | wc -l
```

## Reporting Issues

If you encounter test files with complex issues that need team discussion:

1. Document the issue in Jira with tag `test-suite-repair`
2. Include the file path, error message, and any attempted fixes
3. Mark the test with `@pytest.mark.skip` with a descriptive reason