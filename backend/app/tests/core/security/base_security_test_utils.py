"""
Tests for the BaseSecurityTest class and authentication infrastructure.
"""
import pytest
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

, from app.core.security.authentication import authenticate_user, get_current_user
from app.core.security.rbac import RBACMiddleware, check_permission
from app.domain.entities.user import User
, from app.domain.enums.role import Role
from app.tests.fixtures.user_fixtures import test_user_id, test_roles


class BaseSecurityTest:
    """Base class for security and authentication tests."""
    
    # Default test user attributes
    test_user_id: UUID = uuid4()
    test_roles: List[Role] = [Role.USER]
    
    def setup_method(self):
        """Set up required attributes and mocks before each test."""
        # Override this in subclasses to add additional setup
        self.user = self._create_test_user()
    
    def _create_test_user(self, 
                          user_id: Optional[UUID] = None, 
                          roles: Optional[List[Role]] = None) -> User:
        """Create a test user for authentication testing."""
        return User(
            id=user_id or self.test_user_id,
            username="test_user",
            email="test@example.com",
            roles=roles or self.test_roles,
            is_active=True,
            full_name="Test User"
        )


class TestBaseSecurityTest:
    """Tests for the BaseSecurityTest class itself."""
    
    @pytest.mark.standalone()
    def test_init(self):
        """Test that BaseSecurityTest can be initialized."""
        security_test = BaseSecurityTest()
        security_test.setup_method()
        
        assert security_test.user is not None
        assert security_test.user.id  ==  security_test.test_user_id
        assert security_test.user.roles  ==  security_test.test_roles
    
    @pytest.mark.standalone()
    def test_create_custom_user(self):
        """Test that a custom user can be created."""
        security_test = BaseSecurityTest()
        
        custom_id = uuid4()
        custom_roles = [Role.ADMIN, Role.CLINICIAN]
        
        custom_user = security_test._create_test_user(
            user_id=custom_id, 
            roles=custom_roles
        )
        
        assert custom_user.id  ==  custom_id
        assert custom_user.roles  ==  custom_roles


class TestAuthenticationSystem(BaseSecurityTest):
    """Tests for the authentication system."""
    
    def setup_method(self):
        """Set up with admin role for testing."""
        self.test_roles = [Role.ADMIN]
        super().setup_method()
    
    @pytest.mark.standalone()
    def test_user_authentication(self, monkeypatch):
        """Test that user authentication works."""
        # Mock the authentication process
    def mock_authenticate(*args, **kwargs):
            return self.user
        
        monkeypatch.setattr("app.core.security.authentication.authenticate_user", mock_authenticate)
        
        # Test authentication
        authenticated_user = authenticate_user(username="test_user", password="password")
        
        assert authenticated_user is not None
        assert authenticated_user.id  ==  self.test_user_id
        assert Role.ADMIN in authenticated_user.roles
    
    @pytest.mark.standalone()
    def test_get_current_user(self, monkeypatch):
        """Test that the current user can be retrieved."""
        # Mock the token validation
    def mock_verify_token(*args, **kwargs):
            return {"sub": str(self.test_user_id), "roles": ["ADMIN"]}
        
        # Mock the user retrieval
    def mock_get_user(*args, **kwargs):
            return self.user
        
        monkeypatch.setattr("app.core.security.authentication._verify_token", mock_verify_token)
        monkeypatch.setattr("app.core.security.authentication._get_user_by_id", mock_get_user)
        
        # Test getting current user
        current_user = get_current_user(token="fake_token")
        
        assert current_user is not None
        assert current_user.id  ==  self.test_user_id
        assert Role.ADMIN in current_user.roles


class TestRBACSystem(BaseSecurityTest):
    """Tests for the RBAC system."""
    
    def setup_method(self):
        """Set up with clinician role for testing."""
        self.test_roles = [Role.CLINICIAN]
        super().setup_method()
    
    @pytest.mark.standalone()
    def test_permission_check_success(self):
        """Test that permission check succeeds for authorized roles."""
        # Should succeed because CLINICIAN has this permission
        check_permission(self.user, required_roles=[Role.CLINICIAN, Role.ADMIN])
        # No exception means the test passed
    
    @pytest.mark.standalone()
    def test_permission_check_failure(self):
        """Test that permission check fails for unauthorized roles."""
        # Should fail because user is not ADMIN
        with pytest.raises(HTTPException) as exc_info:
            check_permission(self.user, required_roles=[Role.ADMIN])
        
        assert exc_info.value.status_code  ==  403
    
    @pytest.mark.standalone()
    def test_rbac_middleware(self):
        """Test the RBAC middleware."""
        middleware = RBACMiddleware()
        
        # Create a request with our user
        class MockRequest:
            def __init__(self, user):
                self.state = type('obj', (object,), {'user': user})
                self.url = type('obj', (object,), {'path': '/api/v1/patients'})
        
        request = MockRequest(self.user)
        
        # Should raise an exception for admin-only endpoints
        with pytest.raises(HTTPException) as exc_info:
            middleware.check_access(request, required_roles=[Role.ADMIN])
        
        assert exc_info.value.status_code  ==  403