# Novamind Digital Twin: Test Infrastructure Canonical SSOT

This document serves as the definitive Single Source of Truth (SSOT) for the Novamind Digital Twin test infrastructure, incorporating the core principles of clean architecture, SOLID principles, and forward-focused engineering without any legacy constraints.

## Core Architecture

The test infrastructure follows a layered architecture mirroring the core application:

1. **Domain Layer**: Tests for pure business logic, neurotransmitter models, and clinical rules without external dependencies
2. **Application Layer**: Tests for services, use cases, and state management
3. **Infrastructure Layer**: Tests for databases, external services, and persistence mechanisms
4. **API Layer**: Tests for endpoints, request validation, and response handling

All tests are further organized by their dependency requirements, creating a robust matrix that ensures complete coverage without unnecessary coupling.

## Test Classification

Tests are classified by the following dependency levels:


| Level       | Description                                              | Directory                |
|-------------|----------------------------------------------------------|--------------------------|
| Standalone  | Pure business logic, no external dependencies            | app/tests/standalone/    |
| VENV Only   | Requires Python packages but no external services        | app/tests/venv_only/     |
| DB Required | Requires database connections and other external services | app/tests/integration/   |

This organization ensures:
1. Tests run from least to most integrated
2. Pipeline failures are isolated by dependency level
3. Developers can run appropriate subset of tests based on changes

## Docker Test Environment

### Container Architecture

The Docker test environment consists of these services defined in `backend/docker-compose.test.yml`:

1. **novamind-db-test**: PostgreSQL database for testing
2. **novamind-redis-test**: Redis instance for caching and session management
3. **novamind-pgadmin-test**: PgAdmin for database management (optional)
4. **novamind-test-runner**: Container that runs the test suite

### Environment Variables

```env
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@novamind-db-test:5432/novamind_test
TEST_REDIS_URL=redis://novamind-redis-test:6379/0
TESTING=1
TEST_MODE=1
```

### Execution Process

The test runner script (`scripts/run_tests_by_level.py`) is the SSOT for test execution. It:

1. Automatically detects Docker environment
2. Configures database connections using environment variables
3. Runs tests by dependency level in the correct sequence
4. Produces standardized test reports

### Database Connection Mechanism

The test database connection follows a clean architecture pattern:

1. Environment variables set configuration parameters
2. Database settings component reads parameters
3. SQLAlchemy engine configured using these settings
4. Repository implementations use the engine via dependency injection

## Test Execution

### Local Development

To run tests in your local environment:

```bash
# Running standalone tests (no external dependencies)
pytest app/tests/standalone

# Running tests that only require Python environment
pytest app/tests/venv_only

# Running integration tests that require database
pytest app/tests/integration
```

### Docker Environment

```bash
# Start all test services and run full suite
cd backend
docker-compose -f docker-compose.test.yml up --build

# Run specific test levels
docker-compose -f docker-compose.test.yml run --rm novamind-test-runner python -m scripts.run_tests_by_level standalone --docker
docker-compose -f docker-compose.test.yml run --rm novamind-test-runner python -m scripts.run_tests_by_level db_required --docker
```

## Artifact Management

### Test Results

Test results are managed in a consistent format across all environments:

1. JUnit XML reports: `/app/test-results/*.xml`
2. Coverage report: `/app/test-results/coverage.xml`
3. HTML coverage report: `/app/test-results/htmlcov/`

### Validation Mechanism

Each test level includes validation mechanisms:

1. **Standalone**: Validates domain logic and business rules
2. **VENV Only**: Validates application layer without external services
3. **Integration**: Validates full system behavior with external dependencies
4. **Docker Connection**: Validates database connectivity in containerized environment

## Test Design Principles

Following the clean architecture and SOLID principles:

1. **Single Responsibility**: Each test verifies one specific aspect
2. **Open/Closed**: Tests are open for extension but closed for modification
3. **Liskov Substitution**: Interfaces are tested independently of implementations
4. **Interface Segregation**: Tests target specific interfaces, not entire modules
5. **Dependency Inversion**: Tests use dependency injection to isolate components

## HIPAA Compliance

Tests handling PHI (Protected Health Information) follow strict guidelines:

1. No real PHI used in test fixtures
2. All test data is synthetic and generated using Faker with medical extensions
3. Test databases are ephemeral and destroyed after test completion
4. Coverage reports exclude sensitive data
5. Error messages are sanitized to prevent data leakage

## Best Practices

1. **Test Isolation**: Each test must function independently
2. **Arrange-Act-Assert**: Follow the AAA pattern in all tests
3. **No Test Dependencies**: Tests should never depend on other tests
4. **Meaningful Naming**: Test names should describe the scenario and expected outcome
5. **Clean Setup/Teardown**: Tests should leave no side effects
6. **Fast Execution**: Tests should be optimized for speed
7. **Deterministic Results**: Tests should always yield the same result given the same code
8. **One Assertion Focus**: Each test should focus on one primary assertion

## Troubleshooting

### Common Issues

1. **Database Connection Failures**:
   - Verify environment variables match Docker Compose configuration
   - Check container health status with `docker-compose ps`
   - Verify network connectivity between containers

2. **Test Discovery Issues**:
   - Ensure test file names match pattern `test_*.py`
   - Verify `conftest.py` is in the correct location
   - Check pytest configuration in `pytest.ini`

3. **Docker Build Failures**:
   - Verify Docker image has all required dependencies
   - Check for compatibility issues between packages
   - Validate Dockerfile steps execute successfully

## Implementation Roadmap

The test infrastructure continues to evolve following these principles:

1. **Complete Automation**: CI/CD pipeline for all test levels
2. **Parallel Execution**: Optimized test execution across multiple processes
3. **Performance Metrics**: Tracking of test speed, coverage, and reliability
4. **Self-Testing**: The test infrastructure tests itself
5. **Zero Technical Debt**: No legacy code or backward compatibility hacks

This document supersedes all previous test documentation and serves as the canonical source of truth for the Novamind Digital Twin test infrastructure.
