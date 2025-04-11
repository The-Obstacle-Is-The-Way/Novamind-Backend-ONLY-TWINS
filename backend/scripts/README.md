# Novamind Backend Scripts

This directory contains utility scripts for the Novamind backend project. These scripts help with development, testing, and maintenance tasks.

## Testing Infrastructure

The Novamind test infrastructure is organized around three levels of test dependencies:

1. **Standalone Tests**: No dependencies beyond Python itself
   - Execute quickly, perfect for fast feedback loops
   - Isolated from external services and databases
   - Located in `/app/tests/standalone/`

2. **VENV-dependent Tests**: Require Python packages but no external services
   - Depend on Python packages but not on databases or external APIs
   - Still relatively fast and reliable
   - Majority of unit tests fall into this category

3. **DB/Service-dependent Tests**: Require database connections or other external services
   - Integration tests that need real databases or external services
   - Slower and require more setup, but test real interactions

## Test Utility Scripts

### Test Classification (`classify_tests.py`)

Analyzes test files and classifies them according to their dependency requirements.

```bash
# Analyze all tests and print a report
python scripts/classify_tests.py --mode analyze

# Generate a detailed report and save to file
python scripts/classify_tests.py --mode analyze --report --output test-report.txt

# Add appropriate pytest markers to test files based on their imports
python scripts/classify_tests.py --mode mark
```

### Dependency-based Test Runner (`run_dependency_tests.py`)

Runs tests based on their dependency requirements in the most efficient order.

```bash
# Run all tests in dependency order
python scripts/run_dependency_tests.py

# Run only standalone tests
python scripts/run_dependency_tests.py --levels standalone

# Run standalone and venv-only tests with coverage
python scripts/run_dependency_tests.py --levels standalone venv_only --coverage

# Run all tests with JUnit XML reports
python scripts/run_dependency_tests.py --junit test-reports

# Run all tests but continue even if one level fails
python scripts/run_dependency_tests.py --skip-failed

# Run tests with additional pytest arguments
python scripts/run_dependency_tests.py --extra-args "--maxfail=5 -k not_slow"
```

## CI/CD Integration

For CI/CD pipelines, use these scripts to run tests in the most efficient order:

```yaml
# Example GitHub Actions workflow step
- name: Run Standalone Tests
  run: python backend/scripts/run_dependency_tests.py --levels standalone --junit test-reports

- name: Run VENV Tests
  if: success() || failure()  # Run even if previous step failed
  run: python backend/scripts/run_dependency_tests.py --levels venv_only --junit test-reports

- name: Run DB Tests
  if: success() || failure()  # Run even if previous step failed
  run: python backend/scripts/run_dependency_tests.py --levels db_required --junit test-reports
```

## Adding New Tests

When adding new tests to the codebase:

1. Consider which dependency level is appropriate:
   - Can it run with no external dependencies? → Standalone
   - Needs Python packages but no services? → VENV-only
   - Requires database or external APIs? → DB-required

2. Add the appropriate pytest marker to your test:
   ```python
   @pytest.mark.standalone
   def test_something_standalone():
       pass
       
   @pytest.mark.venv_only
   def test_something_with_packages():
       pass
       
   @pytest.mark.db_required
   def test_something_with_database():
       pass
   ```

3. Use the classification script to verify:
   ```bash
   python scripts/classify_tests.py --mode analyze
   ```

## Best Practices

- Always favor standalone tests when possible - they're faster and more reliable
- Use mock objects (like our `patient_mock.py` example) to create standalone versions of tests
- Run `classify_tests.py` periodically to ensure tests are correctly categorized
- Use the dependency runner in development to get fast feedback from standalone tests
