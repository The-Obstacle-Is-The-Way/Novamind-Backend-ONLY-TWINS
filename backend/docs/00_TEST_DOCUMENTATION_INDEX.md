# Novamind Digital Twin Test Suite Documentation

## Overview

This documentation provides a comprehensive guide to the Novamind Digital Twin test infrastructure, organization, and best practices. The test suite follows a dependency-based Single Source of Truth (SSOT) approach, prioritizing clean architecture principles and dependency isolation.

## Table of Contents

1. [Test Suite Analysis](01_TEST_SUITE_ANALYSIS.md) - Detailed analysis of the current test suite
2. [Executive Summary](02_TEST_SUITE_EXECUTIVE_SUMMARY.md) - Concise overview of test suite status and recommendations
3. [Test Infrastructure SSOT](03_TEST_INFRASTRUCTURE_SSOT.md) - Canonical documentation of the dependency-based testing approach

## Key Principles

The Novamind Digital Twin test suite follows these key principles:

- **Dependency-Based Organization**: Tests are organized by their dependency requirements, not by architectural layers
- **Isolation First**: Tests are designed to run in isolation where possible
- **Progressive Execution**: Tests execute from least dependent to most dependent
- **Clean Architecture**: Test code follows the same clean architecture principles as production code
- **HIPAA Compliance**: Special attention to security and privacy considerations in test data

## Test Categories

Tests are organized into three primary dependency levels:

1. **Standalone Tests** (`/backend/app/tests/standalone/`)
   - Pure unit tests with no external dependencies
   - Use mocks and stubs for all external interactions
   - Run quickly and reliably in any environment

2. **VENV Tests** (`/backend/app/tests/venv/`)
   - Tests that require the Python virtual environment and installed packages
   - May use in-memory databases or file system
   - No external network or service dependencies

3. **Integration Tests** (`/backend/app/tests/integration/`)
   - Tests that require external services (databases, API, etc.)
   - End-to-end tests of complete system functionality
   - Environment-dependent tests

## Test Execution

The canonical way to run tests is through the `/backend/scripts/test/runners/run_tests.py` script, which supports running tests at different dependency levels:

```bash
# Run only standalone tests
python /backend/scripts/test/runners/run_tests.py --standalone

# Run standalone and venv tests
python /backend/scripts/test/runners/run_tests.py --venv

# Run all tests
python /backend/scripts/test/runners/run_tests.py --all

# Run tests with security markers
python /backend/scripts/test/runners/run_tests.py --security
```

## Test Creation

When creating new tests, determine the appropriate dependency level and place them in the corresponding directory. Use the existing tests as templates and follow the clean architecture principles and test organization patterns.

## Test Migrations

A migration tool is available to help organize existing tests into the dependency-based structure:

```bash
# Analyze the current test suite
python /backend/scripts/test/migrations/migrate_tests.py --analyze

# Migrate tests to appropriate directories
python /backend/scripts/test/migrations/migrate_tests.py --migrate