# Novamind Digital Twin Test Infrastructure

This document outlines the test infrastructure for the Novamind Digital Twin backend, focusing on test organization, dependency management, and execution strategies.

## Test Dependency Levels

The Novamind testing infrastructure organizes tests into distinct dependency levels:

1. **Standalone Tests** 
   - No dependencies beyond Python itself
   - Located in `app/tests/standalone/`
   - Marked with `@pytest.mark.standalone`
   - Fastest to run, ideal for core domain logic and utilities
   - Great for CI/CD early feedback

2. **VENV-Only Tests**
   - Require Python packages but no external services
   - Located in `app/tests/venv_only/`
   - Marked with `@pytest.mark.venv_only`
   - Medium execution speed
   - Good for testing code with package dependencies

3. **DB-Required Tests**
   - Require database connections or other external services
   - Marked with `@pytest.mark.db_required`
   - Slowest to run, require a fully configured environment
   - Necessary for testing persistence and integration

## Test Scripts and Tools

### 1. Dependency-Based Test Runner

```bash
# Run standalone tests
python scripts/run_dependency_tests.py --level standalone

# Run VENV-only tests  
python scripts/run_dependency_tests.py --level venv

# Run DB-required tests
python scripts/run_dependency_tests.py --level db

# Generate a test dependency report
python scripts/run_dependency_tests.py --report
```

### 2. Shell Wrapper

```bash
# Run standalone tests
./scripts/run_tests.sh standalone

# Run VENV-only tests
./scripts/run_tests.sh venv  

# Run DB-required tests 
./scripts/run_tests.sh db

# Run all tests in dependency order
./scripts/run_tests.sh all

# Generate a dependency report
./scripts/run_tests.sh report

# Find standalone test candidates
./scripts/run_tests.sh candidates
```

### 3. Test Candidate Identifier

```bash
# Find potential standalone test candidates
python scripts/identify_standalone_candidates.py

# Save results to a file
python scripts/identify_standalone_candidates.py --output candidates.txt

# Show detailed information
python scripts/identify_standalone_candidates.py --verbose
```

### 4. Test Failure Debugger

```bash
# Debug standalone test failures
python scripts/debug_test_failures.py --category standalone

# Debug failures in a specific module
python scripts/debug_test_failures.py --module patient

# Search for specific error type
python scripts/debug_test_failures.py --search "sanitize_text"

# Save analysis to a file
python scripts/debug_test_failures.py --output debug_report.txt
```

## Adding New Tests

### Creating Standalone Tests

Standalone tests have no external dependencies and run in complete isolation:

```python
import pytest

@pytest.mark.standalone
def test_my_standalone_function():
    # Test implementation
    assert True
```

Characteristics of good standalone tests:
- Test pure domain logic
- Use mocks for all external dependencies
- No database or network operations
- No file I/O dependencies
- No complex third-party package requirements

### Creating VENV-Only Tests

VENV-only tests may depend on installed packages but not external services:

```python
import pytest
import pandas as pd  # External package dependency

@pytest.mark.venv_only
def test_my_venv_only_function():
    # Test with package dependencies
    df = pd.DataFrame({"a": [1, 2, 3]})
    assert len(df) == 3
```

### Creating DB-Required Tests

DB-required tests interact with databases or external services:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.db_required
async def test_my_db_function(async_session: AsyncSession):
    # Test with database operations
    result = await async_session.execute("SELECT 1")
    assert result is not None
```

## CI/CD Pipeline Integration

The test infrastructure is designed to integrate with CI/CD pipelines, running tests in dependency order:

1. **Stage 1: Linting & Standalone Tests** (Fast feedback)
   - Code linting
   - Standalone tests

2. **Stage 2: VENV Tests** (Medium complexity)
   - Tests requiring package dependencies

3. **Stage 3: DB Tests** (Full environment)
   - Database-dependent tests
   - Integration tests

This strategy allows for early feedback on simple issues while preserving resources for more complex tests.

## Test Analytics

Use the reporting tools to understand your test distribution:

```bash
python scripts/run_dependency_tests.py --report
```

Example report metrics:
- Total test count and distribution
- Percentage of tests by dependency level
- Unmarked tests that need categorization
- Recommendations for improving test organization

## Converting Unit Tests to Standalone

The `identify_standalone_candidates.py` script helps identify unit tests that could be converted to standalone tests:

1. Run the script to identify candidates
2. Create a copy of the test file in the standalone directory
3. Add `@pytest.mark.standalone` to test functions
4. Verify the tests pass in standalone mode

Converting unit tests to standalone improves CI/CD performance and provides faster feedback on core logic.

## Debugging Test Failures

The test failure debugger categorizes failing tests:

- **Interface Mismatches**: Changes to class interfaces, parameters, etc.
- **Behavior Mismatches**: Changes to expected behavior or logic
- **Validation Errors**: Issues with validation or constraints
- **Missing Dependencies**: Missing imports or dependencies

Use the debug tool to categorize and address test failures systematically.

## Best Practices

1. **Mark all tests with the appropriate dependency level**
2. **Aim for a higher percentage of standalone tests** (target: 30%+)
3. **Run tests in dependency order** for efficiency
4. **Mock external dependencies** in standalone and venv-only tests
5. **Use test fixtures** to reduce duplication
6. **Add new standalone tests** for all core domain logic
7. **Keep test markers and directories in sync**