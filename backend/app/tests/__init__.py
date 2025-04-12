"""
Novamind Digital Twin Platform Test Suite.

This package contains all tests for the Novamind Digital Twin Platform, organized by:
    1. Test type (unit, integration, security, e2e)
    2. Application layer (domain, application, infrastructure, api)
    3. Feature area (authentication, phi, digital twin, etc.)

    All tests follow SOLID principles and Clean Architecture guidelines, with proper
    separation of concerns and dependency injection for testability.
    """
    import os

    # Ensure test environment is set
    os.environ.setdefault("TESTING", "1")
    os.environ.setdefault("ENVIRONMENT", "testing")

    # Import common test fixtures and utilities
    from app.tests.fixtures.mock_db_fixture import MockAsyncSession

    __all__ = ["MockAsyncSession"]
