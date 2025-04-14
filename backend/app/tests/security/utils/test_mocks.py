"""
Mock objects for security-related testing.

This module provides mock implementations for various security components
to be used in unit tests, ensuring isolation from real security services.
"""

from unittest.mock import MagicMock

# Mock Encryption Service
class MockEncryptionService:
    def __init__(self):
        self.encrypt = MagicMock(return_value='encrypted_data')
        self.decrypt = MagicMock(return_value='decrypted_data')

# Mock Authentication Service
class MockAuthService:
    def __init__(self):
        self.validate_token = MagicMock(return_value=True)
        self.get_current_user = MagicMock(return_value={'id': 'test_user', 'roles': ['user']})

# Mock Database Session
class MockDBSession:
    def __init__(self):
        self.commit = MagicMock()
        self.rollback = MagicMock()
        self.add = MagicMock()
        self.query = MagicMock()

# Mock Async Database Session
class MockAsyncSession:
    def __init__(self):
        self.commit = MagicMock()
        self.rollback = MagicMock()
        self.add = MagicMock()
        self.query = MagicMock()

# Mock Patient Model
class MockPatient:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Mock PHI Detection Service
class MockPHIDetection:
    def __init__(self):
        self.detect_phi = MagicMock(return_value={'has_phi': False, 'redacted_text': 'redacted'})

# Mock Role-Based Access Control
class RoleBasedAccessControl:
    def __init__(self):
        self.check_access = MagicMock(return_value=True)
        self.filter_data = MagicMock(return_value={'filtered_data': 'mocked'})

# Mock Logger
class MockLogger:
    def __init__(self):
        self.info = MagicMock()
        self.warning = MagicMock()
        self.error = MagicMock()
        self.debug = MagicMock()
