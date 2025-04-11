# Novamind Digital Twin Testing Framework

## Overview

This document serves as the comprehensive index to the Novamind Digital Twin testing infrastructure documentation. It provides an organized guide to our testing architecture, implementation, and best practices.

## Documentation Structure

Our test documentation follows a logical progression from high-level concepts to detailed implementation:

| # | Document | Description |
|---|----------|-------------|
| 00 | [Test Documentation Index](00_TEST_DOCUMENTATION_INDEX.md) | This document - main navigation hub |
| 01 | [Test Suite Analysis](01_TEST_SUITE_ANALYSIS.md) | Analysis of the current test suite structure |
| 02 | [Test Suite Executive Summary](02_TEST_SUITE_EXECUTIVE_SUMMARY.md) | High-level overview and strategic approach |
| 03 | [Test Infrastructure SSOT](03_TEST_INFRASTRUCTURE_SSOT.md) | Canonical definition of directory-based test organization |
| 04 | [Test Scripts Cleanup Plan](04_TEST_SCRIPTS_CLEANUP_PLAN.md) | Plan for reorganizing test scripts directory |
| 05 | [Test Suite Current State Analysis](05_TEST_SUITE_CURRENT_STATE_ANALYSIS.md) | Detailed analysis of existing test suite |
| 06 | [Test Suite Implementation Roadmap](06_TEST_SUITE_IMPLEMENTATION_ROADMAP.md) | Step-by-step implementation plan with code examples |
| 07 | [Security Testing Guidelines](07_SECURITY_TESTING_GUIDELINES.md) | HIPAA compliance and security testing requirements |
| 08 | [Test Scripts Implementation](08_TEST_SCRIPTS_IMPLEMENTATION.md) | Detailed implementation of test runners and tools |

## Testing Philosophy

The Novamind Digital Twin project follows these core testing principles:

- **Clean Tests**: Tests should be readable, maintainable, and follow SOLID principles
- **Fast Feedback**: Tests should run quickly to provide rapid developer feedback
- **Isolation**: Tests should be independent and not rely on other tests
- **Deterministic**: Tests should produce the same result every time they run
- **Comprehensive**: Tests should cover business logic, security, and integration points

Our testing strategy is built on a "shift-left" approach, where testing begins early in the development cycle and defects are caught before they reach production.

## Directory-Based SSOT Approach

We organize tests using a directory-based Single Source of Truth (SSOT) approach, where tests are categorized by their external dependencies:

```
backend/app/tests/
├── standalone/     # Tests with no external dependencies (fastest)
├── venv/           # Tests requiring Python packages but no external services
├── integration/    # Tests requiring external services like databases
└── conftest.py     # Shared test fixtures
```

This organization allows for efficient test execution, starting with the fastest, most isolated tests and progressively moving to more integrated tests.

## Test Categories

| Category | Dependencies | Examples | Run Time |
|----------|--------------|----------|----------|
| Standalone | None beyond Python standard library | Domain models, utilities | Fastest (ms) |
| VENV | Python packages (FastAPI, SQLAlchemy) | Service layer with mocks | Medium (s) |
| Integration | External services (DB, Redis) | Repositories, API endpoints | Slowest (min) |

## Running Tests

### Using the Canonical Test Runner

```bash
# Run standalone tests only
python backend/scripts/test/runners/run_tests.py --standalone

# Run all tests
python backend/scripts/test/runners/run_tests.py --all

# Run with coverage
python backend/scripts/test/runners/run_tests.py --all --coverage
```

### Using pytest Directly

```bash
# Run a specific test file
pytest backend/app/tests/standalone/test_patient_model.py

# Run tests matching a pattern
pytest backend/app/tests/standalone/ -k "patient"

# Run tests with specific markers
pytest backend/app/tests/ -m "security"
```

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Determine Dependency Level**: Identify whether your test is standalone, venv, or integration
2. **Place in Correct Directory**: Add the test file to the appropriate directory
3. **Follow Naming Conventions**: Name test files with `test_` prefix
4. **Add Appropriate Markers**: Use pytest markers for orthogonal concerns only
5. **Use Fixtures Correctly**: Leverage existing fixtures; create new ones if needed
6. **Ensure Independence**: Tests should not depend on other tests

## HIPAA Compliance in Testing

Special considerations for HIPAA compliance:

- **Synthetic Data**: All test data must be synthetic, never real PHI
- **Data Sanitization**: Test output must be sanitized to avoid accidental PHI exposure
- **Comprehensive Coverage**: Security tests must cover all HIPAA requirements
- **PHI Handling**: Tests must verify proper encryption, access controls, and audit logging

See [Security Testing Guidelines](07_SECURITY_TESTING_GUIDELINES.md) for detailed information.

## CI/CD Integration

Our CI/CD pipeline runs tests progressively:

1. **Stage 1**: Standalone tests
2. **Stage 2**: VENV tests (if standalone pass)
3. **Stage 3**: Integration tests (if VENV pass)
4. **Stage 4**: Security tests & reporting

## Implementation Roadmap

To achieve production readiness, we recommend a phased approach to implementation:

### Phase 1: Foundation (Weeks 1-2)

1. **Scripts Cleanup**
   - Reorganize the `/scripts` directory
   - Implement canonical test runners
   - Create test migration tools

2. **Test Classification**
   - Analyze all tests for proper categorization
   - Document test dependencies
   - Prepare for migration

### Phase 2: Migration & Quality (Weeks 3-4)

1. **Test Migration**
   - Move tests to appropriate directories
   - Update imports and references
   - Fix broken tests after migration

2. **Test Quality**
   - Fix isolation issues
   - Standardize test patterns
   - Refactor common test code

### Phase 3: Coverage & CI/CD (Weeks 5-6)

1. **Coverage Improvement**
   - Add tests for infrastructure (+10%)
   - Add tests for security components (+25%)
   - Add tests for error handling (+18%)

2. **CI/CD Integration**
   - Update CI/CD pipelines
   - Implement standardized reporting
   - Add performance tracking

For detailed implementation steps, see [Test Suite Implementation Roadmap](06_TEST_SUITE_IMPLEMENTATION_ROADMAP.md).