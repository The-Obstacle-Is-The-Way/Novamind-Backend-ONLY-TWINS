# Novamind Digital Twin Test Organization SSOT

## Introduction

This document defines the **Single Source of Truth (SSOT)** for organizing tests in the Novamind Digital Twin platform. It resolves the competing approaches of markers, dependencies, and directories to establish a clear, maintainable testing structure used by enterprise software teams.

## Best Practice Analysis

After evaluating industry best practices at organizations like Netflix, Google, Microsoft, and other enterprise HIPAA-compliant systems, we've identified that the most maintainable approach is:

### Directory Structure as SSOT

**Directory structure** provides the most robust organization method because:

1. **Physical enforcement** - Organization is enforced at the filesystem level
2. **Self-documenting** - New developers can immediately understand the structure
3. **IDE-friendly** - Easier navigation in modern IDEs
4. **Reduced configuration** - Less reliance on hidden pytest configuration
5. **Explicit dependencies** - Makes dependency requirements clear
6. **CI optimization** - Enables running tests in dependency order

## Test Organization

Tests are organized in a three-tier directory structure based on their dependency requirements:

```
app/tests/
├── standalone/  # No external dependencies
├── venv/        # Python package dependencies only
├── integration/ # External service dependencies
├── conftest.py  # Shared fixtures
└── helpers/     # Test utilities
```

### 1. Standalone Tests (`/app/tests/standalone/`)

Tests that require **no external dependencies** beyond Python standard library:

- Pure business logic tests
- Domain model validation
- Utility function tests
- Data transformation tests

These tests:
- Run extremely fast (milliseconds)
- Have no database, network, or external library dependencies
- Always run first in the CI pipeline

### 2. VENV Tests (`/app/tests/venv/`)

Tests that require **Python package dependencies but no external services**:

- Framework-dependent tests (FastAPI, SQLAlchemy) with mocked backends
- Tests using data science packages (numpy, pandas)
- Tests requiring specialized libraries

These tests:
- Run relatively quickly (seconds)
- Have no database or network dependencies
- Run after standalone tests in CI

### 3. Integration Tests (`/app/tests/integration/`)

Tests that require **external services** like databases and APIs:

- Repository tests against real databases
- API tests with real endpoints
- Tests requiring multiple services

These tests:
- Run more slowly (seconds to minutes)
- Require infrastructure setup (databases, services)
- Run last in CI, only if previous test levels pass

## Implementation Approach

### 1. Test Script Organization

All test runner scripts maintain and respect this directory-based organization:

```bash
# Run all tests in dependency order
python scripts/run_tests.py --all

# Run just standalone tests
python scripts/run_tests.py --standalone
```

### 2. Test Classification

The test classification system works directly with the directory structure:

```bash
# Get a report of test organization
python scripts/classify_tests.py --report

# Move tests to their correct directories
python scripts/organize_tests.py --execute
```

### 3. Marker Usage

We've **eliminated dependency-based markers** (`standalone`, `venv_only`, `db_required`) as they duplicate the directory structure. Markers are now reserved only for:

| Marker Name | Purpose |
|-------------|---------|
| `slow` | Tests that take > 1 second even in their category |
| `security` | Tests specifically checking security features |
| `flaky` | Tests with occasional failures being investigated |
| `smoke` | Core functionality tests for rapid verification |

Only these approved markers should be used in the codebase.

## Migration Plan

1. **Classify existing tests** using the `classify_tests.py` script
2. **Move tests** to appropriate directories with `organize_tests.py`
3. **Remove old markers** from test files
4. **Update CI pipeline** to use directory-based test discovery

## Benefits of This Approach

1. **Clearer organization** - One definitive way to categorize tests
2. **Faster CI/CD** - Tests run in dependency order for quicker feedback
3. **Easier maintenance** - New tests automatically go in the right place
4. **Better developer experience** - Structure is immediately obvious
5. **Reduced need for documentation** - Organization is self-evident
6. **Forward compatibility** - Structure works with future pytest versions

This SSOT approach represents the clean, forward-looking foundation for the Novamind test infrastructure, eliminating redundancy and legacy approaches.