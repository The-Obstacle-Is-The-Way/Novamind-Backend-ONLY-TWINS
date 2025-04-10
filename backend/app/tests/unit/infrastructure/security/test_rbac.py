# -*- coding: utf-8 -*-
"""Unit tests for Role-Based Access Control functionality.

This module tests the RBAC system which ensures that users can only access
information appropriate to their role, a critical requirement for HIPAA compliance.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.infrastructure.security.rbac.role_manager import (
    RoleBasedAccessControl, # Corrected class name
    RBACConfig,
    Permission,
    Role,
    RoleDefinition,
    ResourceType,
    Action,
    AccessRequest,
    AccessContext,
    RBACDecision,
    AccessDeniedError, # Keep original exceptions for now
    RoleNotFoundError,
    PermissionNotFoundError
)


@pytest.fixture
def rbac_config():
    """Create an RBAC configuration for testing."""
    return RBACConfig(
        enabled=True,
        roles_path="rbac_roles.yaml",
        enforce_strict_checking=True,
        default_deny=True,
        audit_access_decisions=True,
        cache_decisions=True,
        cache_ttl_seconds=300,
        require_explicit_roles=True,
        allow_role_inheritance=True,
        allow_context_based_permissions=True,
        patient_relationship_path="$.user.authorized_patients[*]",
        role_hierarchy={
            "admin": ["psychiatrist", "nurse", "receptionist"],
            "psychiatrist": ["nurse"],
            "nurse": ["receptionist"]
        }
    )


@pytest.fixture
def role_definitions():
    """Create sample role definitions for testing."""
    return {
        "admin": RoleDefinition(
            name="admin",
            description="System administrator with full access",
            permissions=["*"],  # Wildcard for all permissions
            inherits=[]
        ),
        "psychiatrist": RoleDefinition(
            name="psychiatrist",
            description="Psychiatrist with clinical access",
            permissions=[
                "read:patient:*",
                "write:patient:*",
                "read:clinical_note:*",
                "write:clinical_note:*",
                "read:medication:*",
                "write:medication:*",
                "read:appointment:*",
                "write:appointment:*"
            ],
            inherits=[]
        ),
        "nurse": RoleDefinition(
            name="nurse",
            description="Nurse with limited clinical access",
            permissions=[
                "read:patient:*",
                "read:clinical_note:*",
                "read:medication:*",
                "read:appointment:*",
                "write:appointment:*"
            ],
            inherits=[]
        ),
        "patient": RoleDefinition(
            name="patient",
            description="Patient with access to own records only",
            permissions=[
                "read:patient:own",
                "read:clinical_note:own",
                "read:medication:own",
                "read:appointment:own",
                "write:appointment:own"
            ],
            inherits=[]
        ),
        "receptionist": RoleDefinition(
            name="receptionist",
            description="Receptionist with scheduling access",
            permissions=[
                "read:patient:basic",
                "read:appointment:*",
                "write:appointment:*"
            ],
            inherits=[]
        )
    }


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger for testing."""
    return MagicMock()


@pytest.fixture
def role_manager(rbac_config, role_definitions, mock_audit_logger):
    """Create a role manager for testing."""
    manager = RoleManager(config=rbac_config)
    
    # Manually set the role definitions
    manager._roles = role_definitions
    manager.audit_logger = mock_audit_logger
    
    # Initialize permission cache
    manager._initialize_permission_cache()
    
    return manager


class TestRoleManager:
    """Test suite for the role manager."""
    
    def test_has_permission_admin(self, role_manager):
        """Test that admin role has access to all permissions."""
        # Check admin access to various resources
        permissions_to_check = [
            "read:patient:*",
            "write:patient:*",
            "read:clinical_note:*",
            "write:clinical_note:*",
            "read:medication:*",
            "write:medication:*",
            "admin:system:*"
        ]
        
        for perm in permissions_to_check:
            # Admin should have access to all permissions
            assert role_manager.has_permission("admin", perm) is True
    
    def test_has_permission_psychiatrist(self, role_manager):
        """Test that psychiatrist role has appropriate permissions."""
        # Permissions psychiatrist should have
        permitted = [
            "read:patient:*",
            "write:patient:*",
            "read:clinical_note:*",
            "write:clinical_note:*",
            "read:medication:*",
            "write:medication:*"
        ]
        
        # Permissions psychiatrist should not have
        denied = [
            "admin:system:*",
            "admin:users:*",
            "billing:process:*"
        ]
        
        # Check permissions
        for perm in permitted:
            assert role_manager.has_permission("psychiatrist", perm) is True
        
        for perm in denied:
            assert role_manager.has_permission("psychiatrist", perm) is False
    
    def test_has_permission_nurse(self, role_manager):
        """Test that nurse role has appropriate permissions."""
        # Permissions nurse should have
        permitted = [
            "read:patient:*",
            "read:clinical_note:*",
            "read:medication:*",
            "read:appointment:*",
            "write:appointment:*"
        ]
        
        # Permissions nurse should not have
        denied = [
            "write:patient:*",
            "write:clinical_note:*",
            "write:medication:*",
            "admin:system:*"
        ]
        
        # Check permissions
        for perm in permitted:
            assert role_manager.has_permission("nurse", perm) is True
        
        for perm in denied:
            assert role_manager.has_permission("nurse", perm) is False
    
    def test_has_permission_patient(self, role_manager):
        """Test that patient role has 'own' resource permissions only."""
        # Permissions patient should have (only on own resources)
        permitted = [
            "read:patient:own",
            "read:clinical_note:own",
            "read:medication:own",
            "read:appointment:own",
            "write:appointment:own"
        ]
        
        # Permissions patient should not have
        denied = [
            "read:patient:*",
            "write:patient:*",
            "read:clinical_note:*",
            "write:clinical_note:*",
            "read:medication:*",
            "write:medication:*"
        ]
        
        # Check permissions
        for perm in permitted:
            assert role_manager.has_permission("patient", perm) is True
        
        for perm in denied:
            assert role_manager.has_permission("patient", perm) is False
    
    def test_role_inheritance(self, role_manager):
        """Test that role inheritance works correctly."""
        # Configure inheritance (admin inherits all)
        role_manager._role_hierarchy = {
            "admin": ["psychiatrist", "nurse", "receptionist"],
            "psychiatrist": ["nurse"],
            "nurse": ["receptionist"]
        }
        
        # Admin should inherit all permissions from psychiatrist
        psychiatrist_perms = [
            "read:patient:*",
            "write:patient:*",
            "read:clinical_note:*",
            "write:clinical_note:*"
        ]
        
        for perm in psychiatrist_perms:
            assert role_manager.has_permission("admin", perm) is True
        
        # Psychiatrist should inherit nurse permissions
        nurse_perms = [
            "read:patient:*",
            "read:clinical_note:*",
            "read:medication:*"
        ]
        
        for perm in nurse_perms:
            assert role_manager.has_permission("psychiatrist", perm) is True
        
        # Nurse should inherit receptionist permissions
        receptionist_perms = [
            "read:patient:basic",
            "read:appointment:*"
        ]
        
        for perm in receptionist_perms:
            assert role_manager.has_permission("nurse", perm) is True
        
        # Patient should not inherit anything
        assert "patient" not in role_manager._role_hierarchy
    
    def test_wildcard_permissions(self, role_manager):
        """Test that wildcard permissions work correctly."""
        # Test generic wildcards
        assert role_manager.has_permission("admin", "*") is True
        assert role_manager.has_permission("admin", "read:*") is True
        assert role_manager.has_permission("admin", "read:patient:*") is True
        
        # Test wildcards with roles other than admin
        assert role_manager.has_permission("psychiatrist", "read:patient:*") is True
        assert role_manager.has_permission("nurse", "read:patient:*") is True
        assert role_manager.has_permission("patient", "read:patient:*") is False  # Patient can only read own
    
    def test_permission_parsing(self, role_manager):
        """Test that permission strings are parsed correctly."""
        # Parse a permission string
        permission = role_manager.parse_permission("read:patient:own")
        
        # Verify components
        assert permission.action == "read"
        assert permission.resource_type == "patient"
        assert permission.resource_qualifier == "own"
        
        # Parse a wildcard permission
        wildcard = role_manager.parse_permission("read:*:*")
        
        # Verify components
        assert wildcard.action == "read"
        assert wildcard.resource_type == "*"
        assert wildcard.resource_qualifier == "*"
    
    def test_check_access_with_context(self, role_manager):
        """Test access checking with context information."""
        # Create an access request with context
        request = AccessRequest(
            roles=["patient"],
            resource_type="patient",
            resource_id="PT12345",
            action="read"
        )
        
        # Create context with patient relationship
        context = AccessContext(
            user={
                "id": "patient123",
                "name": "John Smith",
                "authorized_patients": ["PT12345"]  # User is related to this patient
            },
            request_path="/api/patients/PT12345",
            method="GET"
        )
        
        # Check access with context
        decision = role_manager.check_access(request, context)
        
        # Verify decision
        assert decision.granted is True
        assert decision.reason == "Patient has permission to access own record"
        
        # Now try with a different patient ID (not authorized)
        unauthorized_request = AccessRequest(
            roles=["patient"],
            resource_type="patient",
            resource_id="PT67890",  # Different patient
            action="read"
        )
        
        # Check access with context
        decision = role_manager.check_access(unauthorized_request, context)
        
        # Verify decision
        assert decision.granted is False
        assert "not authorized to access" in decision.reason
    
    def test_check_access_for_clinician(self, role_manager):
        """Test access checking for clinical staff roles."""
        # Create an access request for a psychiatrist
        request = AccessRequest(
            roles=["psychiatrist"],
            resource_type="clinical_note",
            resource_id="CN12345",
            action="write"
        )
        
        # Create context
        context = AccessContext(
            user={
                "id": "doctor123",
                "name": "Dr. Jane Smith",
                "roles": ["psychiatrist"]
            },
            request_path="/api/clinical-notes/CN12345",
            method="POST"
        )
        
        # Check access
        decision = role_manager.check_access(request, context)
        
        # Verify decision
        assert decision.granted is True
        assert "Psychiatrist has permission" in decision.reason
        
        # Test with a different role with insufficient permissions
        receptionist_request = AccessRequest(
            roles=["receptionist"],
            resource_type="clinical_note",
            resource_id="CN12345",
            action="write"
        )
        
        # Create context
        receptionist_context = AccessContext(
            user={
                "id": "receptionist123",
                "name": "Bob Johnson",
                "roles": ["receptionist"]
            },
            request_path="/api/clinical-notes/CN12345",
            method="POST"
        )
        
        # Check access
        decision = role_manager.check_access(receptionist_request, receptionist_context)
        
        # Verify decision
        assert decision.granted is False
        assert "does not have permission" in decision.reason
    
    def test_check_access_admin_override(self, role_manager):
        """Test that admin role can override access restrictions."""
        # Create an access request for admin
        request = AccessRequest(
            roles=["admin"],
            resource_type="system",
            resource_id="config",
            action="admin"
        )
        
        # Create context
        context = AccessContext(
            user={
                "id": "admin123",
                "name": "Admin User",
                "roles": ["admin"]
            },
            request_path="/api/admin/system/config",
            method="PUT"
        )
        
        # Check access
        decision = role_manager.check_access(request, context)
        
        # Verify decision
        assert decision.granted is True
        assert "Admin has permission" in decision.reason
    
    def test_audit_logging(self, role_manager, mock_audit_logger):
        """Test that access decisions are properly logged."""
        # Enable auditing
        role_manager.config.audit_access_decisions = True
        
        # Create an access request
        request = AccessRequest(
            roles=["nurse"],
            resource_type="medication",
            resource_id="MED12345",
            action="read"
        )
        
        # Create context
        context = AccessContext(
            user={
                "id": "nurse123",
                "name": "Nurse Johnson",
                "roles": ["nurse"]
            },
            request_path="/api/medications/MED12345",
            method="GET"
        )
        
        # Check access
        role_manager.check_access(request, context)
        
        # Verify audit log was called
        mock_audit_logger.log_rbac_decision.assert_called_once()
        
        # Get the audit log call arguments
        log_call = mock_audit_logger.log_rbac_decision.call_args[1]
        
        # Verify log contains relevant information
        assert log_call["user_id"] == "nurse123"
        assert log_call["roles"] == ["nurse"]
        assert log_call["resource_type"] == "medication"
        assert log_call["resource_id"] == "MED12345"
        assert log_call["action"] == "read"
        assert log_call["decision"] is not None
        
        # Check logging of denied access
        mock_audit_logger.reset_mock()
        
        # Create a denied request
        denied_request = AccessRequest(
            roles=["receptionist"],
            resource_type="medication",
            resource_id="MED12345",
            action="write"  # Receptionists can't write medications
        )
        
        # Check access (should be denied)
        role_manager.check_access(denied_request, context)
        
        # Verify audit log was called with denial
        mock_audit_logger.log_rbac_decision.assert_called_once()
        denied_log_call = mock_audit_logger.log_rbac_decision.call_args[1]
        assert denied_log_call["decision"].granted is False
    
    def test_permission_caching(self, role_manager):
        """Test that permission decisions are properly cached."""
        # Enable caching
        role_manager.config.cache_decisions = True
        
        # Create a spy on the _check_permission method
        original_check = role_manager._check_permission
        check_calls = 0
        
        def spy_check(*args, **kwargs):
            nonlocal check_calls
            check_calls += 1
            return original_check(*args, **kwargs)
        
        role_manager._check_permission = spy_check
        
        # Check the same permission multiple times
        for _ in range(5):
            role_manager.has_permission("psychiatrist", "read:patient:*")
        
        # Verify the check was only performed once due to caching
        assert check_calls == 1
        
        # Check a different permission
        role_manager.has_permission("psychiatrist", "write:patient:*")
        
        # Verify a new check was performed
        assert check_calls == 2
    
    def test_enforce_strict_checking(self, role_manager):
        """Test strict permission checking."""
        # Enable strict checking
        role_manager.config.enforce_strict_checking = True
        
        # Test with invalid role
        with pytest.raises(RoleNotFoundError):
            role_manager.has_permission("non_existent_role", "read:patient:*")
        
        # Test with valid role but non-existent permission
        with pytest.raises(PermissionNotFoundError):
            role_manager.has_permission("psychiatrist", "non_existent:permission")
        
        # Disable strict checking
        role_manager.config.enforce_strict_checking = False
        
        # Now the same checks should return False instead of raising
        assert role_manager.has_permission("non_existent_role", "read:patient:*") is False
        assert role_manager.has_permission("psychiatrist", "non_existent:permission") is False
    
    def test_default_deny_policy(self, role_manager):
        """Test the default deny policy."""
        # Enable default deny
        role_manager.config.default_deny = True
        
        # Check a permission that isn't explicitly defined
        assert role_manager.has_permission("nurse", "admin:system:config") is False
        
        # Disable default deny (although this is not recommended for HIPAA)
        role_manager.config.default_deny = False
        
        # Now define a permissive method for testing
        def permissive_check(*args):
            return True
        
        # Replace the check method temporarily
        original_check = role_manager._check_permission
        role_manager._check_permission = permissive_check
        
        # Check the same permission
        assert role_manager.has_permission("nurse", "admin:system:config") is True
        
        # Restore the original method
        role_manager._check_permission = original_check
    
    def test_permission_composition(self, role_manager):
        """Test permission composition using multiple roles."""
        # Create an access request with multiple roles
        request = AccessRequest(
            roles=["nurse", "receptionist"],  # User has both roles
            resource_type="appointment",
            resource_id="APT12345",
            action="write"
        )
        
        # Create context
        context = AccessContext(
            user={
                "id": "user123",
                "name": "Jane Smith",
                "roles": ["nurse", "receptionist"]
            },
            request_path="/api/appointments/APT12345",
            method="PUT"
        )
        
        # Check access
        decision = role_manager.check_access(request, context)
        
        # Verify decision (should be granted as both nurse and receptionist can write appointments)
        assert decision.granted is True
        
        # Try a case where only one role has permission
        medication_request = AccessRequest(
            roles=["nurse", "receptionist"],
            resource_type="medication",
            resource_id="MED12345",
            action="read"
        )
        
        # Check access
        decision = role_manager.check_access(medication_request, context)
        
        # Verify decision (should be granted as nurse can read medications)
        assert decision.granted is True
        assert "Nurse has permission" in decision.reason
    
    def test_contextual_permission_evaluation(self, role_manager):
        """Test evaluation of permissions that depend on request context."""
        # Configure a special rule for context-based evaluation
        def special_context_rule(request, context):
            # Special rule: Nurses can write clinical notes only during weekday business hours
            if (request.roles == ["nurse"] and 
                request.resource_type == "clinical_note" and 
                request.action == "write" and
                context.request_metadata.get("is_business_hours", False)):
                return RBACDecision(granted=True, reason="Nurse can write clinical notes during business hours")
            return None  # Defer to standard rules
        
        # Add the special rule
        role_manager.add_contextual_rule(special_context_rule)
        
        # Create an access request for nurse writing clinical note
        request = AccessRequest(
            roles=["nurse"],
            resource_type="clinical_note",
            resource_id="CN12345",
            action="write"  # Normally nurses can't write clinical notes
        )
        
        # Create context with business hours
        business_context = AccessContext(
            user={"id": "nurse123", "name": "Nurse Johnson", "roles": ["nurse"]},
            request_path="/api/clinical-notes/CN12345",
            method="POST",
            request_metadata={"is_business_hours": True}
        )
        
        # Check access during business hours
        decision = role_manager.check_access(request, business_context)
        
        # Verify decision (should be granted due to special rule)
        assert decision.granted is True
        assert "during business hours" in decision.reason
        
        # Create non-business hours context
        non_business_context = AccessContext(
            user={"id": "nurse123", "name": "Nurse Johnson", "roles": ["nurse"]},
            request_path="/api/clinical-notes/CN12345",
            method="POST",
            request_metadata={"is_business_hours": False}
        )
        
        # Check access outside business hours
        decision = role_manager.check_access(request, non_business_context)
        
        # Verify decision (should be denied as regular rules apply)
        assert decision.granted is False
        assert "does not have permission" in decision.reason
    
    def test_ensure_loaded_roles(self, role_manager):
        """Test that roles are properly loaded."""
        # Check that all expected roles are loaded
        expected_roles = ["admin", "psychiatrist", "nurse", "patient", "receptionist"]
        
        for role_name in expected_roles:
            assert role_name in role_manager._roles
            assert isinstance(role_manager._roles[role_name], RoleDefinition)
            assert role_manager._roles[role_name].name == role_name
    
    def test_require_explicit_roles(self, role_manager):
        """Test enforcement of explicit role requirement."""
        # Enable require explicit roles
        role_manager.config.require_explicit_roles = True
        
        # Create an access request with empty roles
        request = AccessRequest(
            roles=[],  # No roles specified
            resource_type="patient",
            resource_id="PT12345",
            action="read"
        )
        
        # Create context
        context = AccessContext(
            user={"id": "user123", "name": "User"},
            request_path="/api/patients/PT12345",
            method="GET"
        )
        
        # Check access
        decision = role_manager.check_access(request, context)
        
        # Verify decision (should be denied as no roles specified)
        assert decision.granted is False
        assert "No roles specified" in decision.reason
    
    def test_check_access_with_no_matching_permission(self, role_manager):
        """Test access check when no matching permission exists."""
        # Create an access request for a resource type not defined in permissions
        request = AccessRequest(
            roles=["psychiatrist"],
            resource_type="billing",  # No billing permissions defined
            resource_id="INV12345",
            action="process"
        )
        
        # Create context
        context = AccessContext(
            user={"id": "doctor123", "name": "Dr. Jane Smith", "roles": ["psychiatrist"]},
            request_path="/api/billing/INV12345",
            method="POST"
        )
        
        # Check access
        decision = role_manager.check_access(request, context)
        
        # Verify decision (should be denied as no matching permission)
        assert decision.granted is False
        assert "does not have permission" in decision.reason
    
    def test_role_assignment_validation(self, role_manager):
        """Test validation of role assignments."""
        # Test valid role assignment
        valid_roles = ["admin", "psychiatrist", "nurse"]
        assert role_manager.validate_roles(valid_roles) is True
        
        # Test with an invalid role
        invalid_roles = ["admin", "non_existent_role"]
        
        # With strict checking, this should raise an error
        role_manager.config.enforce_strict_checking = True
        with pytest.raises(RoleNotFoundError):
            role_manager.validate_roles(invalid_roles)
        
        # With strict checking disabled, it should return False
        role_manager.config.enforce_strict_checking = False
        assert role_manager.validate_roles(invalid_roles) is False
    
    def test_dynamic_permission_evaluation(self, role_manager):
        """Test dynamic evaluation of permissions based on context."""
        # Create a dynamic permission evaluator
        def evaluate_own_resource(request, context):
            # Check if user is trying to access their own resource
            if (request.resource_qualifier == "own" and 
                context.user and 
                "id" in context.user):
                
                # For patients, check if the resource belongs to them
                if "patient" in request.roles:
                    authorized_patients = context.user.get("authorized_patients", [])
                    if request.resource_id in authorized_patients:
                        return True
            
            # Defer to standard rules
            return None
        
        # Register the evaluator
        role_manager.register_dynamic_evaluator("own_resource", evaluate_own_resource)
        
        # Create patient request for own resource
        request = AccessRequest(
            roles=["patient"],
            resource_type="clinical_note",
            resource_id="PT12345",
            action="read",
            resource_qualifier="own"
        )
        
        # Create context with matching patient ID
        context = AccessContext(
            user={
                "id": "patient123",
                "name": "John Smith",
                "authorized_patients": ["PT12345"]
            },
            request_path="/api/patients/PT12345/clinical-notes",
            method="GET"
        )
        
        # Check access
        decision = role_manager.check_access(request, context)
        
        # Verify decision
        assert decision.granted is True