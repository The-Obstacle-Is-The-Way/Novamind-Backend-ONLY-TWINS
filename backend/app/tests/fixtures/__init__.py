"""
Test Fixtures Package.

This package exports fixtures for database operations, authentication,
and other test utilities.
"""

# Re-export fixtures from the consolidated database fixture module
from .db_test_fixture import (
    db_session,
    db_transaction,
    transactional_test,
    override_get_session,
    override_db_dependencies,
    clear_tables,
    seed_test_data,
    TestDataFactory,
    TransactionalTestContext,
)

# Export env fixture
from .env_fixture import (
    test_env,
    mock_env_vars,
    TestEnvironment,
)

# Export auth fixtures
from .auth_fixtures import (
    test_user,
    admin_user,
)

# Export patient fixtures
from .patient_fixtures import (
    test_patient,
)

# Export all fixtures that should be available directly
__all__ = [
    # Database fixtures
    "db_session",
    "db_transaction", 
    "transactional_test",
    "override_get_session",
    "override_db_dependencies",
    "clear_tables",
    "seed_test_data",
    "TestDataFactory",
    "TransactionalTestContext",
    
    # Environment fixtures
    "test_env",
    "mock_env_vars",
    "TestEnvironment",
    
    # Auth fixtures
    "test_user",
    "admin_user",
    
    # Patient fixtures
    "test_patient",
]
