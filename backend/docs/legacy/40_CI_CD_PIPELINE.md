# CI/CD Pipeline for Novamind Digital Twin Backend

## Overview

This document outlines the continuous integration and continuous deployment (CI/CD) pipeline for the Novamind Digital Twin Backend, with a specific focus on testing architecture. The pipeline is designed to ensure code quality, maintain test coverage, and validate changes before they are merged and deployed.

## Current Testing Architecture Issues

An analysis of the current repository structure has revealed several critical issues:

1. **Fragmented Test Structure**: Tests are scattered across different directories (`/backend/app/tests/` and `/backend/tests/`), causing confusion and inconsistent test execution.

2. **Unclear Test Dependencies**: There is no clear separation between standalone tests (which run without external dependencies) and integration tests (which require databases, external services, etc.).

3. **Inadequate CI Pipeline**: The current CI pipeline is not properly configured to run different types of tests in the appropriate environments, leading to false positives/negatives.

4. **Incomplete Coverage Tracking**: Test coverage is not adequately tracked or enforced, resulting in potential quality issues.

5. **Directory Path Confusion**: The mixture of `/backend/app/tests/` and `/backend/tests/` creates import path confusion and makes test discovery unreliable.

## Test Categorization Strategy

To address these issues, we're implementing a clear test categorization strategy:

### 1. Standalone Tests
- **Location**: `/backend/app/tests/standalone/`
- **Characteristics**: 
  - No external dependencies (database, network, etc.)
  - Fast execution
  - Reliable deterministic results
  - Pure unit tests, mock-based tests
- **Examples**: 
  - Domain model tests
  - Service tests with mocked dependencies
  - Utility function tests
  - ML exception classes tests
  - PHI sanitization utility tests

### 2. Integration Tests
- **Location**: `/backend/app/tests/integration/`
- **Characteristics**:
  - Require external dependencies
  - May be slower to execute
  - Test multiple components working together
- **Examples**:
  - API endpoint tests
  - Database repository tests
  - External service integration tests

### 3. Security Tests
- **Location**: `/backend/app/tests/security/`
- **Characteristics**:
  - Focus on HIPAA compliance and security measures
  - May include both standalone and integration tests
- **Examples**:
  - Authentication tests
  - Authorization tests
  - Audit logging tests
  - PHI protection tests

## CI/CD Pipeline Implementation

The CI/CD pipeline will be implemented using GitHub Actions with a multi-stage approach:

### Stage 1: Standalone Tests
- **Purpose**: Run all tests that don't require external dependencies
- **Trigger**: On every push and pull request
- **Environment**: Simple container without additional services
- **Steps**:
  1. Checkout code
  2. Set up Python environment
  3. Install dependencies
  4. Run standalone tests with coverage tracking
  5. Upload coverage reports
  6. Fail fast if standalone tests fail

### Stage 2: Integration Tests
- **Purpose**: Run tests that require external dependencies
- **Trigger**: On successful completion of standalone tests
- **Environment**: Docker-based with required services (PostgreSQL, Redis, etc.)
- **Steps**:
  1. Start required services using docker-compose
  2. Wait for services to be ready
  3. Run integration tests
  4. Upload test results
  5. Fail if integration tests fail

### Stage 3: Security Tests
- **Purpose**: Validate security measures and HIPAA compliance
- **Trigger**: On successful completion of integration tests
- **Environment**: Same Docker-based environment as integration tests
- **Steps**:
  1. Run security-specific tests
  2. Run static security analysis tools
  3. Validate audit logging
  4. Verify PHI protection
  5. Report security test results

### Stage 4: Deployment (for main branch only)
- **Purpose**: Deploy the application to the appropriate environment
- **Trigger**: On successful completion of all test stages for the main branch
- **Steps**:
  1. Build deployment artifacts
  2. Deploy to staging environment
  3. Run smoke tests
  4. Deploy to production environment (with approval)
  5. Run post-deployment validation

## Directory Structure and Convention

To avoid confusion, we are standardizing on the following directory structure:

```
/backend/
  ├── app/
  │   ├── tests/
  │   │   ├── standalone/    # Tests with no external dependencies
  │   │   ├── integration/   # Tests requiring external services
  │   │   ├── security/      # Security-focused tests
  │   │   ├── e2e/           # End-to-end tests
  │   │   ├── fixtures/      # Shared test fixtures
  │   │   └── conftest.py    # Global test configuration
  ├── .github/
  │   └── workflows/
  │       ├── standalone-tests.yml   # Workflow for standalone tests
  │       ├── integration-tests.yml  # Workflow for integration tests
  │       └── deploy.yml             # Workflow for deployment
```

## Implementation Plan

### Phase 1: Fix Standalone Tests
1. Ensure all standalone tests are properly located in the `/backend/app/tests/standalone/` directory
2. Configure pytest to correctly discover and run these tests
3. Implement the standalone-tests.yml GitHub Actions workflow
4. Set up coverage reporting for standalone tests

### Phase 2: Containerize Integration Tests
1. Update docker-compose.test.yml for the required services
2. Move integration tests to the `/backend/app/tests/integration/` directory
3. Implement the integration-tests.yml GitHub Actions workflow
4. Ensure proper service initialization before running tests

### Phase 3: Enhance Security Tests
1. Organize security tests in the `/backend/app/tests/security/` directory
2. Implement security testing tools and checks
3. Add security checks to the CI pipeline
4. Configure proper PHI data protection testing

## Coverage Requirements

Minimum coverage requirements for different components:

- **Domain models**: 90% line coverage
- **Application services**: 85% line coverage
- **API endpoints**: 85% line coverage
- **Security components**: 95% line coverage
- **Overall project**: 80% line coverage

## Test Markers

To facilitate selective test execution, we use pytest markers:

- `@pytest.mark.standalone`: Tests that don't require external dependencies
- `@pytest.mark.integration`: Tests that require external services
- `@pytest.mark.security`: Security-focused tests
- `@pytest.mark.slow`: Tests that take longer to execute
- `@pytest.mark.phi`: Tests related to PHI handling

## Current Status and Next Steps

Currently:
- Standalone tests in `/backend/app/tests/standalone/` are working correctly
- ML exception tests and PHI sanitizer tests have 100% coverage
- CI pipeline configuration is incomplete

Next steps:
1. Create and implement the standalone-tests.yml workflow
2. Verify all core domain tests are properly categorized
3. Set up GitHub Actions secrets for required environment variables
4. Implement integration test workflow with Docker
5. Configure security scanning tools

## Conclusion

Properly implementing this CI/CD pipeline will significantly improve code quality, maintainability, and compliance with HIPAA regulations. The clear separation between standalone and integration tests ensures that:

1. Tests run in the appropriate environments
2. Fast standalone tests provide quick feedback
3. CI pipeline accurately reports test and coverage results
4. The deployment process is automated and reliable

This architecture supports both the immediate needs of the Novamind Digital Twin project and provides a scalable foundation as the codebase grows.