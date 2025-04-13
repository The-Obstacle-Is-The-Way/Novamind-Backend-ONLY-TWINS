# Docker Test Environment SSOT

## Overview

This document serves as the definitive Single Source of Truth (SSOT) for the Docker-based test environment in the Novamind Digital Twin backend. It details the setup, configuration, and execution of tests in Docker containers with proper database connectivity.

## Architecture

The Docker test environment consists of the following services:

1. **novamind-db-test**: PostgreSQL database for testing
2. **novamind-redis-test**: Redis instance for caching and session management
3. **novamind-pgadmin-test**: PgAdmin for database management (optional)
4. **novamind-test-runner**: Container that runs the test suite

These services are defined in `backend/docker-compose.test.yml`.

## Test Runner Script

The primary test runner is `scripts/run_tests_by_level.py`, which:

1. Routes to the actual implementation in `scripts/test/runners/legacy/run_tests_by_level.py`
2. Configures environment variables based on Docker parameters
3. Supports different test levels: standalone, venv_only, db_required
4. Accepts command-line arguments like `--docker`, `--xml`, `--cleanup`

## Database Configuration

The test database is configured through the following mechanism:

1. Docker-compose sets the `TEST_DATABASE_URL` environment variable
2. The run_tests_by_level.py script parses this URL and sets DB_ environment variables
3. The Database class in the application respects these settings during testing

### Connection String

The Docker test database connection string is:
```
postgresql+asyncpg://postgres:postgres@novamind-db-test:5432/novamind_test
```

## Running Tests in Docker

To run the full test suite in Docker:

```bash
cd backend
docker-compose -f docker-compose.test.yml up --build
```

To run specific test levels:

```bash
# Standalone tests only
docker-compose -f docker-compose.test.yml run --rm novamind-test-runner python -m scripts.run_tests_by_level standalone --docker

# Database-required tests only
docker-compose -f docker-compose.test.yml run --rm novamind-test-runner python -m scripts.run_tests_by_level db_required --docker
```

## Environment Variables

The following environment variables control the Docker test environment:

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| TEST_DATABASE_URL | Database connection string | postgresql+asyncpg://postgres:postgres@novamind-db-test:5432/novamind_test |
| TEST_REDIS_URL | Redis connection string | redis://novamind-redis-test:6379/0 |
| TESTING | Flag to indicate test mode | 1 |
| TEST_MODE | Additional test mode flag | 1 |
| PYTEST_ADDOPTS | Additional pytest options | --color=yes --cov=app |

## Test Result Artifacts

Test results are stored in the `/app/test-results` directory, which is mounted as a volume to preserve results after container termination:

- JUnit XML reports: `/app/test-results/*.xml`
- Coverage report: `/app/test-results/coverage.xml`
- HTML coverage report: `/app/test-results/htmlcov/`

## Integration Test Verification

A database connectivity test `app/tests/integration/test_database_docker_connection.py` validates that the test runner can successfully connect to the PostgreSQL container. This test ensures:

1. The Docker network is properly configured
2. Database credentials are correct
3. The test database is accessible and operational

## Troubleshooting

### Common Issues:

1. **Database Connection Failures**:
   - Check that all services are healthy with `docker-compose -f docker-compose.test.yml ps`
   - Verify environment variables are correctly set in the test runner
   - Check for network connectivity between containers

2. **Missing Test Results**:
   - Ensure the test_results volume is properly mounted
   - Check file permissions in the container

3. **Test Script Issues**:
   - Verify that `scripts/run_tests_by_level.py` exists and is executable
   - Check that it correctly imports from `scripts/test/runners/legacy/run_tests_by_level.py`

## Maintenance

The Docker test environment should be regularly updated to match changes in:

1. Database schema (through Alembic migrations)
2. Test dependencies (in requirements-test.txt)
3. Configuration parameters (environment variables)

Following this guide ensures consistent and reliable execution of the test suite in a containerized environment, eliminating "it works on my machine" issues while maintaining proper isolation between tests.
