"""
Mock objects for security-related testing.

This module provides mock implementations for various security components
to be used in unit tests, ensuring isolation from real security services.
"""

from unittest.mock import MagicMock

# Mock Encryption Service
class MockEncryptionService:
    def __init__(self):
        self.encrypt = MagicMock(return_value="encrypted_data")
        self.decrypt = MagicMock(return_value="decrypted_data")

# Mock Auth Service
class MockAuthService:
    def __init__(self):
        self.create_token = MagicMock(return_value="mock_token")
        self.validate_token = MagicMock(return_value={"user_id": "test_user", "roles": ["user"]})
        self.has_role = MagicMock(return_value=True)
        self.refresh_token = MagicMock(return_value={"access_token": "new_mock_token", "refresh_token": "new_refresh_token"})

# Mock RBAC Service
class MockRBACService:
    def __init__(self):
        self.check_permission = MagicMock(return_value=True)
        self.add_role_permission = MagicMock()

# Mock Audit Logger
class MockAuditLogger:
    def __init__(self):
        self.log_phi_access = MagicMock()
        self.log_access_attempt = MagicMock()

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
    """
    Mock implementation of RoleBasedAccessControl for testing.
    """
    def __init__(self):
        self._roles = {}
        self.check_access = MagicMock(return_value=True)
        self.filter_data = MagicMock(return_value={'filtered_data': 'mocked'})

    def add_role(self, role: str):
        if role not in self._roles:
            self._roles[role] = set()

    def add_permission_to_role(self, role: str, permission: str) -> bool:
        if role in self._roles:
            self._roles[role].add(permission)
            return True
        return False

    def add_role_permission(self, role: str, permission: str) -> bool:
        """
        Add a permission to a role. Added for compatibility with tests.
        
        Args:
            role: The role to add permission to
            permission: The permission to add
            
        Returns:
            bool: True if added successfully
        """
        return self.add_permission_to_role(role, permission)

    def has_permission(self, role: str, permission: str) -> bool:
        return role in self._roles and permission in self._roles[role]

# Mock Entity Factory
class MockEntityFactory:
    def __init__(self):
        self.create_patient = MagicMock(return_value=MockPatient())
        self.create_user = MagicMock(return_value={'id': 'test_user', 'roles': ['user']})

# Mock PHI Auditor
class MockPHIAuditor:
    def __init__(self, app_dir=None):
        self.run_audit = MagicMock(return_value=True)
        self.generate_report = MagicMock(return_value='{"summary": {"issues_found": 0}}')
        self.findings = {"code_phi": [], "api_security": [], "configuration_issues": [], "logging_issues": []}

# Mock PHI Audit Result
class MockPHIAuditResult:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.phi_detected = []
        self.is_allowed = False

# Mock PHI Redaction Service
class PHIRedactionService:
    def __init__(self):
        self.redact_phi = MagicMock(return_value="[REDACTED]")
        self.detect_phi = MagicMock(return_value=[])
        self.redact = MagicMock(return_value="[REDACTED]")

# Mock Logger
class MockLogger:
    def __init__(self):
        self.info = MagicMock()
        self.warning = MagicMock()
        self.error = MagicMock()
        self.debug = MagicMock()
