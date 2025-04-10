"""
Standalone Tests Package for Novamind Digital Twin Platform.

This package contains all tests that can run without external dependencies such as:
- Databases
- External APIs
- Other services

Tests in this package:
- Should be fast and reliable
- Should use mocks for any external dependencies
- Should focus on business logic, domain models, and utilities
- Should not require network access or actual database connections

These tests are run as the first phase of the CI/CD pipeline before
integration tests are executed.
"""