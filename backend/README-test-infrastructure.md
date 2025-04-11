# Novamind Digital Twin Test Infrastructure

This document provides an overview of the Novamind test infrastructure organization and tools. The test infrastructure follows a directory-based Single Source of Truth (SSOT) approach, organizing tests by their dependency requirements.

## Directory Organization (SSOT)

Tests are organized into three directories based on their dependency level:

```
app/tests/
├── standalone/  # No external dependencies beyond Python std lib
├── venv/        # Requires Python packages but no external services
└── integration/ # Requires databases or other external services
```

This directory-based organization provides several advantages:
- Clear dependency requirements for each test
- Faster feedback in CI/CD pipelines
- Simple discovery and execution rules
- Self-documenting structure

## Test Infrastructure Tools

### 1. Test Execution

The `run_tests.py` script executes tests based on the directory structure:

```bash
# Run all tests
python scripts/run_tests.py --all

# Run standalone tests only
python scripts/run_tests.py --standalone

# Run tests with coverage reporting
python scripts/run_tests.py --standalone --coverage
```

### 2. Test Organization

The `organize_tests.py` script helps organize tests into the correct directories:

```bash
# Analyze where tests should be located
python scripts/organize_tests.py --analyze

# Move tests to their correct directories
python scripts/organize_tests.py --execute
```

### 3. Migration from Markers

The `migrate_to_directory_ssot.py` script assists with migrating from marker-based organization:

```bash
# Generate a migration plan
python scripts/migrate_to_directory_ssot.py --analyze

# Execute the migration
python scripts/migrate_to_directory_ssot.py --execute
```

### 4. Fixing Failing Tests

The `fix_standalone_tests.py` script identifies and fixes common issues in standalone tests:

```bash
# Analyze failing tests
python scripts/fix_standalone_tests.py --analyze

# Fix failing tests
python scripts/fix_standalone_tests.py --fix
```

## CI/CD Integration

The test infrastructure integrates with our CI/CD pipeline via GitHub Actions:

1. The workflow runs tests in dependency order:
   - Code quality checks
   - Standalone tests
   - VENV tests (if standalone pass)
   - Integration tests (if VENV tests pass)

2. Coverage reports are generated and combined for all test levels

3. Security scans run in parallel with tests

## Getting Started

To get started with the test infrastructure:

1. **Set up the directory structure**:
   ```bash
   python scripts/organize_tests.py --execute
   ```

2. **Fix failing standalone tests**:
   ```bash
   python scripts/fix_standalone_tests.py --fix
   ```

3. **Run the tests**:
   ```bash
   python scripts/run_tests.py --all
   ```

## Documentation

For more detailed information, see the following documentation:

- [50_TESTING_STRATEGY.md](docs/50_TESTING_STRATEGY.md) - Overall testing strategy
- [51_TEST_ORGANIZATION_SSOT.md](docs/51_TEST_ORGANIZATION_SSOT.md) - Directory SSOT approach
- [52_TEST_SEPARATION_RATIONALE.md](docs/52_TEST_SEPARATION_RATIONALE.md) - Why we separate tests by dependency

## Test Coverage Goals

Our test coverage goals:

- Domain layer: 90% coverage
- Application layer: 85% coverage
- Infrastructure layer: 75% coverage
- Overall: 80% coverage

Current coverage can be viewed by running:
```bash
python scripts/run_tests.py --all --coverage