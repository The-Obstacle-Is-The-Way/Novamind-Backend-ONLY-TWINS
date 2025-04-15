# Test Dependency Level Guide

This guide explains how to work with the restructured test suite organized by dependency levels.

## Understanding Dependency Levels

Our test suite is organized into three primary dependency levels:

1. **Standalone Tests**: Pure unit tests with no external dependencies
2. **Venv Tests**: Tests with file system dependencies but no network/DB requirements
3. **Integration Tests**: Tests requiring external services, networks, or databases

## Running Tests by Level

### Standalone Tests

Standalone tests are the fastest and most reliable. Run them during development for quick feedback:

```bash
# Run all standalone tests
python -m pytest backend/app/tests/standalone/

# Run standalone tests for a specific domain
python -m pytest backend/app/tests/standalone/domain/

# Run standalone tests with verbose output
python -m pytest backend/app/tests/standalone/ -v
```

### Venv Tests

Venv tests require file system access but are still fairly quick:

```bash
# Run all venv tests
python -m pytest backend/app/tests/venv/

# Run venv tests for a specific component
python -m pytest backend/app/tests/venv/infrastructure/
```

### Integration Tests

Integration tests require external services and may take longer to run:

```bash
# Run all integration tests
python -m pytest backend/app/tests/integration/

# Run integration tests for API endpoints
python -m pytest backend/app/tests/integration/api/
```

## Using Markers

Tests are marked by their dependency level for easier filtering:

```bash
# Run all tests with the standalone marker
python -m pytest -m standalone backend/app/tests/

# Run all tests with the venv marker
python -m pytest -m venv backend/app/tests/

# Run all tests with the integration marker
python -m pytest -m integration backend/app/tests/

# Skip integration tests
python -m pytest -m "not integration" backend/app/tests/
```

## Custom Markers

We've defined additional markers for specific test categories:

```bash
# Run all security tests
python -m pytest -m security backend/app/tests/

# Run all HIPAA compliance tests
python -m pytest -m hipaa backend/app/tests/

# Run all performance tests
python -m pytest -m performance backend/app/tests/
```

## CI Pipeline Integration

The tests are integrated into the CI pipeline with different stages:

1. **Fast CI**: Runs standalone tests only
   ```bash
   python -m pytest backend/app/tests/standalone/
   ```

2. **Standard CI**: Runs standalone + venv tests
   ```bash
   python -m pytest backend/app/tests/standalone/ backend/app/tests/venv/
   ```

3. **Full CI**: Runs all tests including integration tests
   ```bash
   python -m pytest backend/app/tests/
   ```

## Working with Fixtures

Each dependency level has its own `conftest.py` file with fixtures appropriate for that level. To use fixtures from a specific level:

```python
# In a standalone test
@pytest.mark.standalone
def test_example(standalone_fixture):
    # Use standalone fixture

# In a venv test
@pytest.mark.venv
def test_example(venv_fixture, standalone_fixture):
    # Can use both venv and standalone fixtures

# In an integration test
@pytest.mark.integration
def test_example(integration_fixture, venv_fixture, standalone_fixture):
    # Can use fixtures from all levels
```

## Migrating Tests

When creating or migrating tests, follow these guidelines:

1. Identify the correct dependency level for your test
2. Place the test in the appropriate directory
3. Add the correct marker
4. Use the appropriate fixtures

Example:

```python
# A standalone test
@pytest.mark.standalone
def test_patient_model():
    patient = Patient(id="p1", name="Test Patient")
    assert patient.id == "p1"
    assert patient.name == "Test Patient"

# A venv test
@pytest.mark.venv
def test_config_loading(temp_dir):
    # Uses file system
    config_file = os.path.join(temp_dir, "config.json")
    with open(config_file, "w") as f:
        json.dump({"key": "value"}, f)
    
    config = ConfigLoader.load(config_file)
    assert config.key == "value"

# An integration test
@pytest.mark.integration
async def test_database_connection(test_db_connection):
    # Uses database
    repo = PatientRepository(test_db_connection)
    result = await repo.get_all()
    assert isinstance(result, list)
```

## Test Repair and Maintenance

To check for syntax errors in test files:

```bash
# Find all files with syntax errors
find backend/app/tests -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep "SyntaxError"

# Attempt to fix syntax errors automatically
python backend/scripts/test/tools/repair_test_syntax.py

# Fix a specific file
python backend/scripts/test/tools/repair_test_syntax.py --path backend/app/tests/path/to/file.py
```

## Coverage Reports

Generate and view coverage reports:

```bash
# Generate coverage report
python -m pytest --cov=backend/app backend/app/tests/ --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Test Suite Architecture](./test_suite_architecture.md)
- [Test Best Practices](./test_suite_best_practices.md)
- [Test Syntax Repair Guide](./test_syntax_repair_guide.md)