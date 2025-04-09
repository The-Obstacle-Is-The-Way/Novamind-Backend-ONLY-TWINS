# SECURITY_IMPLEMENTATION

## Overview

This document provides a comprehensive guide to the security implementation in the NOVAMIND platform, focusing on authentication, authorization, audit logging, and data encryption. All implementations adhere to HIPAA compliance requirements and follow Clean Architecture principles.

## Authentication System

### AWS Cognito Integration

NOVAMIND uses AWS Cognito for secure user authentication with the following HIPAA-compliant configuration:

```python
# app/infrastructure/security/cognito/cognito_service.py
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional

from app.core.config import settings
from app.core.utils.logging import logger

class CognitoService:
    """Service for AWS Cognito operations with HIPAA compliance."""
    
    def __init__(
        self,
        user_pool_id: Optional[str] = None,
        client_id: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize the Cognito service.
        
        Args:
            user_pool_id: AWS Cognito User Pool ID
            client_id: AWS Cognito App Client ID
            region: AWS Region
        """
        self.user_pool_id = user_pool_id or settings.AWS_COGNITO_USER_POOL_ID
        self.client_id = client_id or settings.AWS_COGNITO_CLIENT_ID
        self.region = region or settings.AWS_REGION
        
        # Initialize Cognito Identity Provider client
        self.client = boto3.client(
            'cognito-idp',
            region_name=self.region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    async def register_user(self, email: str, password: str, attributes: Dict) -> Dict:
        """
        Register a new user in Cognito.
        
        Args:
            email: User's email address
            password: User's password
            attributes: Additional user attributes
            
        Returns:
            Registration response
        """
        try:
            # Ensure no PHI in attributes
            sanitized_attributes = self._sanitize_attributes(attributes)
            
            # Convert attributes to Cognito format
            user_attributes = [
                {'Name': key, 'Value': value}
                for key, value in sanitized_attributes.items()
            ]
            
            # Add email to attributes
            user_attributes.append({'Name': 'email', 'Value': email})
            
            # Register user
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=user_attributes
            )
            
            logger.info(f"User registered successfully: {email}")
            return {
                'user_id': response['UserSub'],
                'email': email,
                'status': 'CONFIRMATION_PENDING'
            }
            
        except ClientError as e:
            logger.error(f"Error registering user: {str(e)}")
            raise
    
    async def authenticate(self, email: str, password: str) -> Dict:
        """
        Authenticate a user with Cognito.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Authentication response
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            # Check if MFA is required
            if response.get('ChallengeName') == 'SOFTWARE_TOKEN_MFA':
                logger.info(f"MFA required for user: {email}")
                return {
                    'status': 'MFA_REQUIRED',
                    'session': response['Session']
                }
            
            # Authentication successful
            tokens = response['AuthenticationResult']
            logger.info(f"User authenticated successfully: {email}")
            
            return {
                'status': 'AUTHENTICATED',
                'access_token': tokens['AccessToken'],
                'id_token': tokens['IdToken'],
                'refresh_token': tokens['RefreshToken'],
                'expires_in': tokens['ExpiresIn']
            }
            
        except ClientError as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise
    
    def _sanitize_attributes(self, attributes: Dict) -> Dict:
        """
        Sanitize user attributes to ensure no PHI is stored.
        
        Args:
            attributes: User attributes
            
        Returns:
            Sanitized attributes
        """
        # Define allowed non-PHI attributes
        allowed_attributes = {
            'given_name', 'family_name', 'preferred_username',
            'locale', 'timezone', 'picture', 'gender'
        }
        
        return {
            key: value for key, value in attributes.items()
            if key in allowed_attributes
        }
```

#### Cognito Configuration for HIPAA Compliance

1. **Multi-Factor Authentication (MFA)**
   - Required for all users
   - Software token (TOTP) preferred over SMS

2. **Password Policy**
   - Minimum length: 12 characters
   - Require uppercase, lowercase, numbers, and special characters
   - Password expiration: 90 days
   - No password reuse (remember last 5 passwords)

3. **Advanced Security Features**
   - Compromised credential checking
   - Adaptive authentication
   - Risk-based challenges
   
4. **User Pool Configuration**
   - Advanced Security: Enable to detect compromised credentials
   - Account Recovery: Email only, no phone recovery
   - Sign-in Options: Email (no username option to prevent PHI in usernames)

5. **App Client Settings**
   - OAuth 2.0: Authorization code grant flow
   - Callback URL: HTTPS only endpoints
   - Sign out URL: Configured for proper session termination
   - Identity Providers: Email/password only initially

6. **HIPAA Compliance Considerations**
   - Automatic Session Timeouts: Set Cognito session timeouts to 15 minutes of inactivity
   - Audit Logging: Log all auth-related events (login, logout, token refresh) in a HIPAA-compliant manner
   - Failed Login Attempts: Lock accounts after 5 failed login attempts
   - Password Rotation: Enforce 90-day password rotation policy
   - MFA Enforcement: Require MFA for all user types (patients, providers, admins)

### JWT Token Management

NOVAMIND uses JWT tokens for maintaining authentication state with the following HIPAA-compliant implementation:

```python
# app/infrastructure/security/jwt/token_handler.py
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from app.core.config import settings
from app.core.utils.logging import logger

class JWTHandler:
    """Handler for JWT token operations with HIPAA-compliant settings."""
    
    def __init__(self):
        """Initialize the JWT handler."""
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(
        self, 
        subject: Union[str, Dict], 
        scopes: Optional[list] = None
    ) -> str:
        """
        Create a HIPAA-compliant access token with short expiry time.
        
        Args:
            subject: User identity (typically user_id or email)
            scopes: Optional list of permission scopes
            
        Returns:
            JWT access token
        """
        # Create token data
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode = {
            'exp': expires.timestamp(),
            'iat': now.timestamp(),
            'sub': str(subject) if not isinstance(subject, dict) else subject,
            'jti': self._generate_jti(),
            'iss': settings.JWT_ISSUER
        }
        
        # Add scopes if provided
        if scopes:
            to_encode['scopes'] = scopes
        
        # Encode token
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
            
        Raises:
            InvalidTokenError: If token is invalid
            ExpiredSignatureError: If token has expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={'verify_signature': True}
            )
            
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
            
        except InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise
    
    def create_refresh_token(self, subject: Union[str, Dict]) -> str:
        """
        Create a refresh token with longer expiry time.
        
        Args:
            subject: User identity
            
        Returns:
            JWT refresh token
        """
        now = datetime.utcnow()
        expires = now + timedelta(days=self.refresh_token_expire_days)
        
        to_encode = {
            'exp': expires.timestamp(),
            'iat': now.timestamp(),
            'sub': str(subject) if not isinstance(subject, dict) else subject,
            'jti': self._generate_jti(),
            'iss': settings.JWT_ISSUER,
            'token_type': 'refresh'
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def _generate_jti(self) -> str:
        """
        Generate a unique JWT ID.
        
        Returns:
            Unique JWT ID
        """
        import uuid
        return str(uuid.uuid4())
```

#### JWT Configuration for HIPAA Compliance

1. **Token Expiration**
   - Access tokens: 15-30 minutes (HIPAA requirement)
   - Refresh tokens: 7 days maximum with rotation

2. **Token Security**
   - RS256 (RSA Signature with SHA-256) algorithm
   - Secure key storage in AWS KMS
   - Token blacklisting for revocation

3. **Token Claims**
   - `iss` (issuer): Identifies the token issuer
   - `sub` (subject): Identifies the user
   - `exp` (expiration time): Token expiry timestamp
   - `jti` (JWT ID): Unique token identifier for revocation
   - `iat` (issued at): Token issuance timestamp

### Authentication Middleware

```python
# app/infrastructure/middleware/auth_middleware.py
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.infrastructure.services.jwt_service import JWTService
from app.utils.logger import get_logger

logger = get_logger(__name__)
jwt_service = JWTService()
security = HTTPBearer()


class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT token verification"""

    async def dispatch(self, request: Request, call_next):
        # Paths that don't require authentication
        open_paths = [
            "/api/v1/auth/token",
            "/api/v1/auth/register",
            "/api/v1/auth/confirm",
            "/api/v1/auth/refresh",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
        ]

        # Skip authentication for open paths
        if request.url.path in open_paths:
            return await call_next(request)

        # Extract token from authorization header
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Verify token
            payload = jwt_service.decode_token(token)

            # Add payload to request state for use in endpoint handlers
            request.state.user = payload

            # Audit logging for HIPAA compliance (omit sensitive data)
            logger.info(
                "Authenticated access",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "user_id": payload.get("sub"),
                    # Do not log IP addresses or full tokens for HIPAA compliance
                }
            )

            return await call_next(request)

        except Exception as e:
            logger.warning(
                f"Authentication failed: {str(e)}",
                extra={"path": request.url.path, "method": request.method}
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
```

### Token Blacklisting for HIPAA Compliance

```python
# app/infrastructure/services/token_blacklist_service.py
import time
from datetime import datetime
from typing import Optional

import redis

from app.config.settings import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TokenBlacklistService:
    """Service for JWT token blacklisting (revocation)"""

    def __init__(self):
        # Connect to Redis
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL,
            decode_responses=True,
        )
        self.key_prefix = "token:blacklist:"

    async def blacklist_token(self, jti: str, expires_at: Optional[int] = None) -> bool:
        """
        Add a token to the blacklist

        Args:
            jti: JWT ID to blacklist
            expires_at: Token expiration timestamp

        Returns:
            Success status
        """
        try:
            # Calculate time to live (TTL) for Redis key
            ttl = None
            if expires_at:
                now = int(time.time())
                ttl = max(0, expires_at - now)  # Ensure positive TTL

            # Add token to blacklist
            key = f"{self.key_prefix}{jti}"
            if ttl:
                self.redis_client.setex(key, ttl, "1")
            else:
                # Default to 24 hours if no expiration provided
                self.redis_client.setex(key, 86400, "1")

            logger.info(f"Token blacklisted: {jti}")
            return True

        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            return False

    async def is_blacklisted(self, jti: str) -> bool:
        """
        Check if a token is blacklisted

        Args:
            jti: JWT ID to check

        Returns:
            True if token is blacklisted
        """
        try:
            key = f"{self.key_prefix}{jti}"
            return bool(self.redis_client.exists(key))

        except Exception as e:
            logger.error(f"Failed to check blacklisted token: {str(e)}")
            # Default to allowing the token if Redis is down
            # This is a security risk, but prevents complete system failure
            return False

    async def clear_expired_tokens(self) -> int:
        """
        Remove expired tokens from the blacklist (maintenance task)

        Returns:
            Number of tokens removed
        """
        # Redis automatically handles expiration with TTL
        # This method is mostly a placeholder for future extension
        return 0
```

### Token Lifecycle Management

#### Complete Token Flow

1. **Login**: User authenticates via Cognito, receives JWT tokens
2. **Token Usage**: Access token for API calls (short-lived)
3. **Token Refresh**: Refresh token used to get new access token
4. **Token Invalidation**: Blacklist tokens on logout for security

#### Implementing Token Logout

```python
# app/presentation/api/v1/endpoints/auth.py (extension)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token_blacklist: TokenBlacklistService = Depends(get_token_blacklist_service),
    current_user: dict = Depends(get_current_user),
):
    """Logout user by blacklisting current token"""
    # Get token from request header
    token = request.headers.get("Authorization").split()[1]

    # Decode to get the JTI and expiration
    token_data = jwt_service.decode_token(token)
    jti = token_data.get("jti")
    exp = token_data.get("exp")

    # Blacklist the token
    await token_blacklist.blacklist_token(jti, exp)

    # Also blacklist refresh token if stored in session
    refresh_jti = token_data.get("refresh_jti")
    if refresh_jti:
        await token_blacklist.blacklist_token(refresh_jti)

    return None
```

### JWT Security Best Practices

1. **Signature Algorithm**: Use RS256 (asymmetric) over HS256 (symmetric) for production
2. **Critical Claims**: Include `nbf` (not before) and `aud` (audience) claims
3. **JWK Rotation**: Implement key rotation for production environments
4. **Token Size**: Keep token size small by minimizing custom claims
5. **Refresh Token Encryption**: Store refresh tokens with additional encryption
6. **Key Security**: Use AWS KMS for managing JWT signing keys in production
7. **Token Lifetime**: Keep access tokens short-lived (15-30 minutes max)
8. **Sensitive Claims**: Never store PHI/PII in JWT claims
9. **Token Storage**: Store tokens securely with appropriate HTTP-only cookies and secure flags
10. **Audit Trail**: Log all token operations for HIPAA compliance (issuance, refresh, invalidation)
11. **Automatic Session Timeout**: Implement inactive session timeout after 15 minutes

### Authentication Routes and Schemas

The following routes and schemas are implemented for authentication:

```python
# app/presentation/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.infrastructure.services.cognito_service import CognitoService
from app.presentation.schemas.auth import (
    RegisterUserRequest,
    ConfirmRegistrationRequest,
    AuthResponse,
    MFARequest,
    RefreshTokenRequest,
)

router = APIRouter()
cognito_service = CognitoService()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterUserRequest):
    """Register a new user"""
    try:
        result = await cognito_service.register_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/confirm", response_model=dict)
async def confirm_registration(request: ConfirmRegistrationRequest):
    """Confirm user registration with confirmation code"""
    try:
        result = await cognito_service.confirm_registration(
            email=request.email,
            confirmation_code=request.confirmation_code,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/token", response_model=AuthResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, get an access token for future requests"""
    try:
        result = await cognito_service.authenticate_user(
            email=form_data.username,  # OAuth2 uses username field for email
            password=form_data.password,
        )

        # Check if MFA is required
        if result.get("status") == "MFA_REQUIRED":
            return {
                "status": "MFA_REQUIRED",
                "session": result.get("session"),
            }

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/verify-mfa", response_model=AuthResponse)
async def verify_mfa(request: MFARequest):
    """Verify MFA code to complete authentication"""
    try:
        result = await cognito_service.verify_mfa(
            session=request.session,
            email=request.email,
            mfa_code=request.mfa_code,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        result = await cognito_service.refresh_tokens(
            refresh_token=request.refresh_token,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
```

```python
# app/presentation/schemas/auth.py
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterUserRequest(BaseModel):
    """Schema for user registration request"""
    email: EmailStr
    password: str = Field(..., min_length=12)
    first_name: str
    last_name: str


class ConfirmRegistrationRequest(BaseModel):
    """Schema for confirming user registration"""
    email: EmailStr
    confirmation_code: str = Field(..., min_length=6, max_length=6)


class MFARequest(BaseModel):
    """Schema for MFA verification request"""
    email: EmailStr
    session: str
    mfa_code: str = Field(..., min_length=6, max_length=6)


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class AuthResponse(BaseModel):
    """Schema for authentication response"""
    status: str
    access_token: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    session: Optional[str] = None
```

### Authentication Flow Testing

The authentication flow follows these steps:

1. Register a new user
2. Confirm registration with the verification code
3. Login to receive MFA challenge
4. Complete MFA verification to get tokens
5. Use access token for authenticated API calls
6. Refresh token when expired

This authentication flow uses AWS Cognito best practices and is designed to meet all HIPAA requirements for healthcare applications.

## Role-Based Access Control (RBAC)

### RBAC System Architecture

NOVAMIND implements a comprehensive RBAC system with the following role hierarchy:

```text
SuperAdmin
├── Administrator
│   └── OfficeManager
│       └── Staff
└── Psychiatrist
    └── Therapist
        └── Patient
```

Each role inherits permissions from roles below it in the hierarchy and grants additional specific permissions.

### Domain Models

```python
# app/domain/entities/rbac.py
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Permission(Enum):
    """Enumeration of system permissions"""
    # Patient record permissions
    VIEW_PATIENT = "view_patient"
    CREATE_PATIENT = "create_patient"
    UPDATE_PATIENT = "update_patient"
    DELETE_PATIENT = "delete_patient"

    # Appointment permissions
    VIEW_APPOINTMENT = "view_appointment"
    CREATE_APPOINTMENT = "create_appointment"
    UPDATE_APPOINTMENT = "update_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"

    # Billing permissions
    VIEW_BILLING = "view_billing"
    CREATE_BILLING = "create_billing"
    UPDATE_BILLING = "update_billing"
    PROCESS_PAYMENT = "process_payment"

    # Prescription permissions
    VIEW_PRESCRIPTION = "view_prescription"
    CREATE_PRESCRIPTION = "create_prescription"
    UPDATE_PRESCRIPTION = "update_prescription"

    # Treatment permissions
    VIEW_TREATMENT = "view_treatment"
    CREATE_TREATMENT = "create_treatment"
    UPDATE_TREATMENT = "update_treatment"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOG = "view_audit_log"
    SYSTEM_CONFIGURATION = "system_configuration"


class Role(Enum):
    """System roles with increasing privilege levels"""
    PATIENT = "patient"
    THERAPIST = "therapist"
    PSYCHIATRIST = "psychiatrist"
    STAFF = "staff"
    OFFICE_MANAGER = "office_manager"
    ADMINISTRATOR = "administrator"
    SUPER_ADMIN = "super_admin"


class RolePermissionMapping(BaseModel):
    """Maps roles to their assigned permissions"""
    role: Role
    permissions: List[Permission]

    class Config:
        from_attributes = True


class UserRole(BaseModel):
    """Represents a role assigned to a user"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: Role
    assigned_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### RBAC Service Implementation

NOVAMIND implements a comprehensive RBAC system to control access to resources:

```python
# app/infrastructure/security/rbac/role_manager.py
from typing import Dict, List, Optional, Set

from app.core.config import settings
from app.core.utils.logging import logger
from app.domain.entities.user import User
from app.domain.value_objects.permission import Permission

class RoleManager:
    """Manager for role-based access control."""
    
    def __init__(self):
        """Initialize the role manager."""
        # Define role hierarchy
        self.role_hierarchy = {
            'admin': ['provider', 'staff', 'patient'],
            'provider': ['staff', 'patient'],
            'staff': ['patient'],
            'patient': []
        }
        
        # Define role permissions
        self.role_permissions = {
            'admin': {
                'user:create', 'user:read', 'user:update', 'user:delete',
                'patient:create', 'patient:read', 'patient:update', 'patient:delete',
                'provider:create', 'provider:read', 'provider:update', 'provider:delete',
                'appointment:create', 'appointment:read', 'appointment:update', 'appointment:delete',
                'digital_twin:create', 'digital_twin:read', 'digital_twin:update', 'digital_twin:delete',
                'billing:create', 'billing:read', 'billing:update', 'billing:delete',
                'audit:read'
            },
            'provider': {
                'patient:read', 'patient:update',
                'appointment:create', 'appointment:read', 'appointment:update', 'appointment:delete',
                'digital_twin:read',
                'clinical_note:create', 'clinical_note:read', 'clinical_note:update',
                'medication:create', 'medication:read', 'medication:update'
            },
            'staff': {
                'patient:read',
                'appointment:create', 'appointment:read', 'appointment:update',
                'billing:create', 'billing:read'
            },
            'patient': {
                'appointment:read',
                'digital_twin:read',
                'clinical_note:read',
                'medication:read'
            }
        }
    
    def get_user_permissions(self, user: User) -> Set[str]:
        """
        Get all permissions for a user based on their role.
        
        Args:
            user: User entity
            
        Returns:
            Set of permission strings
        """
        if not user or not user.role:
            return set()
        
        # Get direct permissions for user's role
        permissions = set(self.role_permissions.get(user.role, set()))
        
        # Add permissions from inherited roles
        for inherited_role in self._get_inherited_roles(user.role):
            permissions.update(self.role_permissions.get(inherited_role, set()))
        
        return permissions
    
    def has_permission(self, user: User, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user: User entity
            permission: Permission string to check
            
        Returns:
            True if user has permission, False otherwise
        """
        if not user or not user.role:
            return False
        
        user_permissions = self.get_user_permissions(user)
        
        # Check for exact permission match
        if permission in user_permissions:
            return True
        
        # Check for wildcard permissions
        resource = permission.split(':')[0]
        wildcard_permission = f"{resource}:*"
        
        return wildcard_permission in user_permissions
    
    def _get_inherited_roles(self, role: str) -> List[str]:
        """
        Get all roles inherited by the given role.
        
        Args:
            role: Role name
            
        Returns:
            List of inherited role names
        """
        if role not in self.role_hierarchy:
            return []
        
        inherited_roles = []
        
        # Add direct inherited roles
        for inherited_role in self.role_hierarchy.get(role, []):
            inherited_roles.append(inherited_role)
            
            # Add transitively inherited roles
            inherited_roles.extend(self._get_inherited_roles(inherited_role))
        
        return inherited_roles
```

### Permission Checks in FastAPI

```python
# app/presentation/api/dependencies/auth.py

from fastapi import Depends, HTTPException, Request, status
from typing import List, Optional

from app.domain.entities.rbac import Permission, Role
from app.infrastructure.services.jwt_service import JWTService
from app.infrastructure.services.rbac_service import RBACService
from app.utils.logger import get_logger

logger = get_logger(__name__)
jwt_service = JWTService()
rbac_service = RBACService()


def get_current_user(request: Request) -> dict:
    """Dependency to extract current user from request state"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user


def requires_permission(permission: Permission):
    """
    Dependency factory to check for a specific permission

    Args:
        permission: Required permission

    Returns:
        Dependency function that checks the permission
    """
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        # Extract roles from user info
        user_roles = current_user.get("roles", [])

        # Convert string roles to Role enum
        roles = [Role(role) for role in user_roles if role in [r.value for r in Role]]

        # Check if user has the required permission
        if not rbac_service.has_permission(roles, permission):
            # HIPAA-compliant audit logging
            logger.warning(
                "Permission denied",
                extra={
                    "user_id": current_user.get("sub"),
                    "permission": permission.value,
                    "roles": user_roles,
                }
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}"
            )

        return current_user

    return dependency


def requires_role(role: Role):
    """
    Dependency factory to check for a specific role

    Args:
        role: Required role

    Returns:
        Dependency function that checks the role
    """
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        # Extract roles from user info
        user_roles = current_user.get("roles", [])

        # Check if user has the required role
        if role.value not in user_roles:
            # HIPAA-compliant audit logging
            logger.warning(
                "Role access denied",
                extra={
                    "user_id": current_user.get("sub"),
                    "required_role": role.value,
                    "user_roles": user_roles,
                }
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}"
            )

        return current_user

    return dependency
```

### HIPAA-Compliant RBAC Audit Logging

```python
# app/utils/audit_logger.py

import json
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from app.config.settings import get_settings
from app.infrastructure.database.models.audit import AuditLogModel
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def log_rbac_action(
    session,
    action: str,
    user_id: str,
    target_user_id: Optional[str] = None,
    role: Optional[str] = None,
    permission: Optional[str] = None,
    success: bool = True,
    additional_data: Optional[Dict[str, Any]] = None,
):
    """
    Log RBAC-related actions for HIPAA compliance

    Args:
        session: Database session
        action: Action performed (e.g., 'assign_role', 'check_permission')
        user_id: ID of user performing the action
        target_user_id: ID of user affected by the action (if applicable)
        role: Role involved (if applicable)
        permission: Permission involved (if applicable)
        success: Whether the action succeeded
        additional_data: Any additional data to log
    """
    try:
        # Create sanitized metadata
        metadata = {
            "action": action,
            "success": success,
        }

        if role:
            metadata["role"] = role

        if permission:
            metadata["permission"] = permission

        if additional_data:
            # Ensure no PHI is included in additional data
            safe_additional_data = {
                k: v for k, v in additional_data.items()
                if k not in settings.PHI_FIELDS
            }
            metadata.update(safe_additional_data)

        # Create audit log entry
        audit_log = AuditLogModel(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            target_user_id=target_user_id,
            action=action,
            metadata=json.dumps(metadata),
        )

        session.add(audit_log)
        await session.commit()

    except Exception as e:
        # Fallback to regular logging if database logging fails
        logger.error(
            f"Failed to create RBAC audit log: {str(e)}",
            extra={
                "action": action,
                "user_id": user_id,
                "target_user_id": target_user_id,
            }
        )
```

### Client-Side RBAC Implementation

```typescript
// frontend/src/services/rbacService.ts

import { useAuth } from '../contexts/AuthContext';

// Permission enum (must match backend)
export enum Permission {
  VIEW_PATIENT = 'view_patient',
  CREATE_PATIENT = 'create_patient',
  UPDATE_PATIENT = 'update_patient',
  DELETE_PATIENT = 'delete_patient',
  // ... other permissions
}

// Role enum (must match backend)
export enum Role {
  PATIENT = 'patient',
  THERAPIST = 'therapist',
  PSYCHIATRIST = 'psychiatrist',
  STAFF = 'staff',
  OFFICE_MANAGER = 'office_manager',
  ADMINISTRATOR = 'administrator',
  SUPER_ADMIN = 'super_admin',
}

// Role hierarchy definition
const roleHierarchy: Record<Role, Role[]> = {
  [Role.SUPER_ADMIN]: [Role.ADMINISTRATOR],
  [Role.ADMINISTRATOR]: [Role.OFFICE_MANAGER],
  [Role.OFFICE_MANAGER]: [Role.STAFF],
  [Role.PSYCHIATRIST]: [Role.THERAPIST],
  [Role.THERAPIST]: [Role.PATIENT],
  [Role.STAFF]: [],
  [Role.PATIENT]: [],
};

// Role permission mapping
const rolePermissions: Record<Role, Permission[]> = {
  [Role.PATIENT]: [
    Permission.VIEW_APPOINTMENT,
    Permission.CREATE_APPOINTMENT,
    // ... other permissions
  ],
  // ... other role permissions
};

// Helper to get all permissions for a role
const getRolePermissions = (role: Role): Set<Permission> => {
  const permissions = new Set<Permission>(rolePermissions[role] || []);

  // Add inherited permissions
  const addInheritedPermissions = (currentRole: Role) => {
    const childRoles = roleHierarchy[currentRole] || [];
    for (const childRole of childRoles) {
      const childPermissions = rolePermissions[childRole] || [];
      childPermissions.forEach(p => permissions.add(p));
      addInheritedPermissions(childRole);
    }
  };

  addInheritedPermissions(role);
  return permissions;
};

// React hook for permission checks
export const usePermission = () => {
  const { user } = useAuth();

  const hasPermission = (permission: Permission): boolean => {
    if (!user || !user.roles) return false;

    // Check each user role
    for (const roleStr of user.roles) {
      try {
        const role = roleStr as Role;
        const permissions = getRolePermissions(role);
        if (permissions.has(permission)) return true;
      } catch (e) {
        console.error(`Invalid role: ${roleStr}`);
      }
    }

    return false;
  };

  const hasRole = (role: Role): boolean => {
    if (!user || !user.roles) return false;
    return user.roles.includes(role);
  };

  return { hasPermission, hasRole };
};

// Permission-based rendering component
export const PermissionGate: React.FC<{
  permission: Permission;
  children: React.ReactNode;
}> = ({ permission, children }) => {
  const { hasPermission } = usePermission();

  if (!hasPermission(permission)) return null;
  return <>{children}</>;
};

// Role-based rendering component
export const RoleGate: React.FC<{
  role: Role;
  children: React.ReactNode;
}> = ({ role, children }) => {
  const { hasRole } = usePermission();

  if (!hasRole(role)) return null;
  return <>{children}</>;
};
```

### RBAC Implementation Details

1. **Role Hierarchy**
   - Admin: Full system access
   - Provider: Clinical access to patient data
   - Staff: Administrative access
   - Patient: Limited access to own data

2. **Permission Structure**
   - Format: `resource:action`
   - Examples: `patient:read`, `appointment:create`
   - Wildcards: `resource:*` for all actions on a resource

3. **Access Control Enforcement**
   - API endpoint protection with permission checks
   - Data filtering based on user role
   - Audit logging of access attempts

### Best Practices for HIPAA-Compliant RBAC

1. **Principle of Least Privilege**: Assign the minimum permissions necessary for each role.
2. **Separation of Duties**: Critical operations should require multiple roles.
3. **Regular Access Reviews**: Audit role assignments periodically.
4. **Context-Aware Permissions**: Consider implementing additional checks based on patient relationships.
5. **Attribute-Based Access Control (ABAC)**: Extend RBAC with attributes like time, location, and patient relationship.
6. **Role Rotation**: Change administrative roles periodically.
7. **Monitor and Alert**: Set up alerts for suspicious permission usage patterns.
8. **User Interface Protection**: Hide UI elements for unauthorized actions, but always enforce permissions on the server.

## Audit Logging

### HIPAA Audit Requirements

According to HIPAA Security Rule § 164.312(b):

> "Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information."

The audit logging system must track:

- **Access Events**: All access to PHI
- **Authorization Events**: Login attempts, role changes
- **Security Events**: Configuration changes, failed logins
- **User Events**: Account creation, modification, deletion
- **System Events**: Startup, shutdown, updates

### Audit Data Retention

- Retention period: 6 years minimum
- Immutable storage (tamper-proof)
- Encrypted at rest and in transit

### Audit Architecture

NOVAMIND implements a multi-layered audit logging strategy:

1. **Application Level**: Detailed events within the application
2. **Database Level**: Data access and changes
3. **Infrastructure Level**: Network and system events
4. **Storage Level**: S3/CloudWatch secure storage

### Core Components

#### Audit Domain Model

```python
# app/domain/entities/audit.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid


class AuditEventType(Enum):
    """Types of events that can be audited"""
    # PHI access events
    PHI_ACCESS = "phi_access"
    PHI_CREATE = "phi_create"
    PHI_UPDATE = "phi_update"
    PHI_DELETE = "phi_delete"

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"

    # Authorization events
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"

    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DISABLED = "user_disabled"
    USER_ENABLED = "user_enabled"

    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_CONFIGURATION_CHANGE = "system_configuration_change"

    # API events
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"

    # Data export events
    DATA_EXPORT = "data_export"
    REPORT_GENERATED = "report_generated"


class AuditEvent(BaseModel):
    """Represents an auditable event in the system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AuditEventType
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    status: str  # 'success', 'failure', 'error'
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
```

#### Audit Database Model

```python
# app/infrastructure/database/models/audit.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class AuditLog(Base):
    """Database model for audit logs"""
    __tablename__ = "audit_logs"

    id = sa.Column(sa.String(36), primary_key=True)
    timestamp = sa.Column(sa.DateTime, nullable=False, index=True)
    event_type = sa.Column(sa.String(50), nullable=False, index=True)
    user_id = sa.Column(sa.String(36), sa.ForeignKey("users.id"), nullable=True, index=True)
    ip_address = sa.Column(sa.String(40), nullable=True)
    user_agent = sa.Column(sa.String(500), nullable=True)
    resource_type = sa.Column(sa.String(50), nullable=True, index=True)
    resource_id = sa.Column(sa.String(36), nullable=True, index=True)
    action = sa.Column(sa.String(100), nullable=False)
    status = sa.Column(sa.String(20), nullable=False, index=True)
    metadata = sa.Column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        # Index for efficient access pattern queries
        sa.Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
        sa.Index("ix_audit_logs_resource_timestamp", "resource_type", "resource_id", "timestamp"),
        sa.Index("ix_audit_logs_event_type_timestamp", "event_type", "timestamp"),
    )
```

### Audit Service Implementation

```python
# app/infrastructure/services/audit_service.py
import json
from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, Request
from pydantic import BaseModel
import boto3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.config.settings import get_settings
from app.domain.entities.audit import AuditEvent, AuditEventType
from app.infrastructure.database.dependencies import get_db
from app.infrastructure.database.models.audit import AuditLog
from app.utils.logger import get_logger
from app.utils.sanitize import sanitize_phi

settings = get_settings()
logger = get_logger(__name__)


class AuditService:
    """Service for creating and managing audit logs"""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

        # Optional AWS CloudWatch integration for redundant logging
        if settings.CLOUDWATCH_ENABLED:
            self.cloudwatch = boto3.client(
                'logs',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.log_group = settings.CLOUDWATCH_LOG_GROUP
            self.log_stream = f"novamind-audit-{datetime.utcnow().strftime('%Y-%m-%d')}"
        else:
            self.cloudwatch = None

    async def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> AuditEvent:
        """
        Log an audit event

        Args:
            event_type: Type of audit event
            action: Description of the action
            user_id: ID of user who performed the action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            status: Outcome status (success, failure, error)
            metadata: Additional data about the event
            request: FastAPI request object (for extracting IP, user agent)

        Returns:
            Created audit event
        """
        try:
            # Extract request details if available
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")

            # Sanitize metadata to remove PHI
            safe_metadata = {}
            if metadata:
                safe_metadata = sanitize_phi(metadata, settings.PHI_FIELDS)

            # Create audit event
            event = AuditEvent(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                status=status,
                metadata=safe_metadata,
            )

            # Save to database
            db_event = AuditLog(
                id=event.id,
                timestamp=event.timestamp,
                event_type=event.event_type.value,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                action=event.action,
                status=event.status,
                metadata=event.metadata,
            )

            self.db.add(db_event)
            await self.db.commit()

            # Also log to CloudWatch if enabled
            if self.cloudwatch:
                self._log_to_cloudwatch(event)

            return event

        except Exception as e:
            # Fallback to regular logging if audit logging fails
            logger.error(
                f"Failed to create audit log: {str(e)}",
                extra={
                    "event_type": event_type.value,
                    "action": action,
                    "user_id": user_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                }
            )
            # Re-raise to allow calling code to handle the error
            raise

    def _log_to_cloudwatch(self, event: AuditEvent):
        """Log an event to AWS CloudWatch (non-async backup)"""
        try:
            # Ensure log stream exists
            try:
                self.cloudwatch.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
            except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
                pass  # Stream already exists

            # Convert event to JSON string
            event_dict = event.dict()
            event_dict["event_type"] = event.event_type.value
            event_json = json.dumps(event_dict)

            # Send to CloudWatch
            self.cloudwatch.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        'timestamp': int(event.timestamp.timestamp() * 1000),
                        'message': event_json
                    }
                ]
            )

        except Exception as e:
            # Failure to log to CloudWatch should not break the application
            logger.error(f"Failed to log to CloudWatch: {str(e)}")

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        event_type: Optional[Union[AuditEventType, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """
        Query audit logs with filters

        Args:
            user_id: Filter by user ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of matching audit events
        """
        query = select(AuditLog)

        # Apply filters
        filters = []
        if user_id:
            filters.append(AuditLog.user_id == user_id)

        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)

        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)

        if event_type:
            if isinstance(event_type, AuditEventType):
                filters.append(AuditLog.event_type == event_type.value)
            else:
                filters.append(AuditLog.event_type == event_type)

        if start_time:
            filters.append(AuditLog.timestamp >= start_time)

        if end_time:
            filters.append(AuditLog.timestamp <= end_time)

        # Combine filters and apply pagination
        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(AuditLog.timestamp.desc())
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        audit_logs = result.scalars().all()

        # Convert to domain entities
        return [
            AuditEvent(
                id=log.id,
                timestamp=log.timestamp,
                event_type=AuditEventType(log.event_type),
                user_id=log.user_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action=log.action,
                status=log.status,
                metadata=log.metadata or {},
            )
            for log in audit_logs
        ]
```

### Audit Middleware for API Requests

```python
# app/infrastructure/middleware/audit_middleware.py
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.domain.entities.audit import AuditEventType
from app.infrastructure.services.audit_service import AuditService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for auditing all API requests"""

    def __init__(self, app, audit_service: AuditService):
        super().__init__(app)
        self.audit_service = audit_service

        # Paths that should not be audited (to avoid noise)
        self.skip_paths = [
            "/api/healthcheck",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auditing for excluded paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Try to extract user ID from request state
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("sub")

        # Create response and catch exceptions
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            logger.error(f"Exception in request: {str(e)}")
            # Let the exception propagate after logging
            raise
        finally:
            # Calculate request duration
            duration_ms = round((time.time() - start_time) * 1000)

            # Determine status based on status code
            status = "success" if 200 <= status_code < 400 else "failure"

            # Log the request
            try:
                await self.audit_service.log_event(
                    event_type=AuditEventType.API_REQUEST,
                    action=f"{request.method} {request.url.path}",
                    user_id=user_id,
                    status=status,
                    metadata={
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "query_params": str(request.query_params),
                        "method": request.method,
                        # Do not log request bodies or headers for HIPAA compliance
                    },
                    request=request
                )
            except Exception as e:
                logger.error(f"Failed to audit request: {str(e)}")
```

### Audit Log Retention and Archiving

```python
# app/infrastructure/tasks/audit_retention.py
import datetime
from typing import List

import boto3
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.infrastructure.database.dependencies import get_db
from app.infrastructure.database.models.audit import AuditLog
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def archive_audit_logs(db: AsyncSession = Depends(get_db)):
    """
    Archive audit logs older than the retention period

    This moves logs to S3 for long-term HIPAA-compliant storage
    """
    try:
        # Calculate cutoff date (default 90 days for active DB, 6 years total)
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(
            days=settings.AUDIT_ACTIVE_RETENTION_DAYS
        )

        # Query logs older than cutoff date
        query = select(AuditLog).where(AuditLog.timestamp < cutoff_date)
        result = await db.execute(query)
        old_logs = result.scalars().all()

        if not old_logs:
            logger.info("No audit logs to archive")
            return

        # Connect to S3
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # Process in batches to avoid memory issues
        batch_size = 1000
        for i in range(0, len(old_logs), batch_size):
            batch = old_logs[i:i+batch_size]

            # Archive to S3
            archive_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
            archive_key = f"audit-archives/{archive_date}/batch-{i}.json"

            # Convert logs to JSON
            logs_json = json.dumps([
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "user_id": log.user_id,
                    "ip_address": log.ip_address,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "action": log.action,
                    "status": log.status,
                    "metadata": log.metadata,
                }
                for log in batch
            ], default=str)

            # Upload to S3 with encryption
            s3_client.put_object(
                Bucket=settings.AUDIT_ARCHIVE_BUCKET,
                Key=archive_key,
                Body=logs_json,
                ServerSideEncryption='AES256'
            )

            # Delete archived logs
            for log in batch:
                await db.delete(log)

            await db.commit()

            logger.info(f"Archived {len(batch)} audit logs to S3: {archive_key}")

    except Exception as e:
        logger.error(f"Failed to archive audit logs: {str(e)}")
        raise
```

### Audit Log Reporting and Analysis

```python
# app/presentation/api/v1/endpoints/audit.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.domain.entities.rbac import Permission
from app.domain.entities.audit import AuditEvent, AuditEventType
from app.infrastructure.services.audit_service import AuditService
from app.presentation.api.dependencies.auth import requires_permission
from app.presentation.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get(
    "/logs",
    response_model=List[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    description="Get audit logs (requires VIEW_AUDIT_LOG permission)"
)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Pagination offset"),
    current_user: dict = Depends(requires_permission(Permission.VIEW_AUDIT_LOG)),
    audit_service: AuditService = Depends(),
):
    """Get audit logs with filters"""
    audit_logs = await audit_service.get_audit_logs(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    return [AuditLogResponse.from_orm(log) for log in audit_logs]


@router.get(
    "/logs/patient/{patient_id}",
    response_model=List[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    description="Get all access logs for a specific patient"
)
async def get_patient_audit_logs(
    patient_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    current_user: dict = Depends(requires_permission(Permission.VIEW_AUDIT_LOG)),
    audit_service: AuditService = Depends(),
):
    """Get all access logs for a specific patient"""
    audit_logs = await audit_service.get_audit_logs(
        resource_type="patient",
        resource_id=patient_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    return [AuditLogResponse.from_orm(log) for log in audit_logs]
```

### Best Practices for HIPAA-Compliant Audit Logging

1. **Record Complete Histories**: Log all create, read, update, delete (CRUD) operations on PHI.
2. **Log Failed Access Attempts**: Record failed login attempts and unauthorized access attempts.
3. **Never Log PHI**: Audit logs should reference resource IDs but not include actual PHI.
4. **Immutable Logs**: Ensure logs cannot be modified or deleted by users.
5. **Secure Transmission**: Encrypt logs during transmission to storage.
6. **Secure Storage**: Store logs in encrypted, access-controlled storage.
7. **Regular Reviews**: Establish a process for regular review of audit logs.
8. **Alerts for Suspicious Activity**: Set up alerts for unusual access patterns.
9. **Separation of Duties**: Ensure administrators can't modify their own audit trails.
10. **Automated Reporting**: Create regular compliance reports for review.

### Integration with Other Systems

For larger practices or healthcare systems, integrate with Security Information and Event Management (SIEM) systems:

```python
# app/infrastructure/services/siem_service.py
import json
import requests
from typing import Dict, Any

from app.config.settings import get_settings
from app.domain.entities.audit import AuditEvent
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class SIEMService:
    """Service for sending audit events to SIEM"""

    def __init__(self):
        self.enabled = settings.SIEM_ENABLED
        self.endpoint = settings.SIEM_ENDPOINT
        self.api_key = settings.SIEM_API_KEY

    async def send_event(self, event: AuditEvent) -> bool:
        """
        Send an audit event to SIEM

        Args:
            event: Audit event to send

        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            # Convert event to SIEM format
            siem_event = {
                "event_id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "action": event.action,
                "status": event.status,
                "ip_address": event.ip_address,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "metadata": event.metadata,
                "source_application": "novamind",
                "environment": settings.ENVIRONMENT,
            }

            # Send to SIEM
            response = requests.post(
                self.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.api_key,
                },
                json=siem_event,
                timeout=5,  # Short timeout to avoid blocking
            )

            if response.status_code != 200:
                logger.warning(
                    f"Failed to send event to SIEM: {response.status_code} {response.text}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error sending event to SIEM: {str(e)}")
            return False
```
            db_session.rollback()

def _sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize audit details to remove PHI.
    
    Args:
        details: Audit details
        
    Returns:
        Sanitized details
    """
    # Define PHI fields to redact
    phi_fields = {
        'name', 'first_name', 'last_name', 'email', 'phone', 'address',
        'dob', 'date_of_birth', 'ssn', 'social_security_number',
        'medical_record_number', 'mrn'
    }
    
    sanitized = {}
    
    for key, value in details.items():
        if key.lower() in phi_fields:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_details(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_details(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized
```

### Audit Logging Implementation Details

1. **Logged Events**
   - Authentication events (login, logout, failed attempts)
   - Data access events (view, create, update, delete)
   - Administrative actions (user management, configuration changes)
   - Security events (permission changes, role assignments)

2. **Logged Information**
   - Timestamp (UTC)
   - User ID and role
   - Action performed
   - Resource type and ID
   - IP address and user agent
   - Success/failure status

3. **Storage and Retention**
   - Database storage for structured querying
   - File-based logging for backup
   - 6-year retention period (HIPAA requirement)
   - Tamper-proof storage with integrity checks

## Data Encryption

### HIPAA Requirements for Encryption

The HIPAA Security Rule (§ 164.312(a)(2)(iv) and § 164.312(e)(2)(ii)) establishes encryption as an "addressable" implementation specification:

> "Implement a mechanism to encrypt and decrypt electronic protected health information."

While addressable, encryption is effectively required for any modern healthcare application to demonstrate compliance with HIPAA's requirement to implement "reasonable and appropriate" safeguards.

### Multi-Layered Encryption Architecture

NOVAMIND implements a defense-in-depth encryption strategy with multiple layers:

1. **Transport Layer Security**: HTTPS/TLS 1.3 for all communications
2. **Database Encryption**: Transparent Data Encryption (TDE) for the entire database
3. **Field-Level Encryption**: Selective encryption of sensitive PHI fields
4. **Encryption Key Management**: AWS KMS for secure key storage and rotation
5. **Client-Side Encryption**: Additional encryption for highly sensitive data

### Transport Layer Security

```python
# app/main.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Include API routers and other setup...

if __name__ == "__main__":
    # Development-only direct execution
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="./certs/key.pem",
        ssl_certfile="./certs/cert.pem",
        ssl_ca_certs="./certs/ca.pem",
        ssl_ciphers="TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256",
        ssl_version=2,  # TLS 1.3
    )
```

#### Secure Cookies Configuration

```python
# app/presentation/api/dependencies/auth.py
from fastapi import Response

# Set secure cookie
def set_auth_cookie(response: Response, token: str):
    """Set secure HTTP-only cookie with JWT token"""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="strict",  # Protect against CSRF
        max_age=1800,  # 30 minutes
        expires=1800,
        path="/",
    )
```

### Database Encryption

```python
# app/infrastructure/database/base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.settings import get_settings

settings = get_settings()

# Configure database connection with SSL
DATABASE_URL = settings.DATABASE_URL
ssl_args = {
    "sslmode": "require",
    "sslrootcert": settings.DB_CA_CERT_PATH,
    "sslcert": settings.DB_CLIENT_CERT_PATH,
    "sslkey": settings.DB_CLIENT_KEY_PATH,
}

engine = create_async_engine(
    DATABASE_URL,
    connect_args=ssl_args,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
)

# Create session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Declarative base for models
Base = declarative_base()

# Dependency for getting DB session
async def get_db():
    """Dependency for getting DB session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### RDS Configuration with AWS

```python
# Infrastructure as Code example (Terraform)
resource "aws_db_instance" "novamind_db" {
  allocated_storage       = 100
  storage_type            = "gp3"
  engine                  = "postgres"
  engine_version          = "14.5"
  instance_class          = "db.m6g.large"
  db_name                 = "novamind"
  username                = "novamind_app"
  password                = var.db_password
  parameter_group_name    = aws_db_parameter_group.postgres14-hipaa.name
  db_subnet_group_name    = aws_db_subnet_group.private.name
  vpc_security_group_ids  = [aws_security_group.db_sg.id]
  storage_encrypted       = true                  # Enable TDE
  kms_key_id              = aws_kms_key.db_key.arn # Use custom KMS key
  backup_retention_period = 35                    # HIPAA requires long retention
  copy_tags_to_snapshot   = true
  deletion_protection     = true
  multi_az                = true                  # High availability
  monitoring_interval     = 60
  performance_insights_enabled = true
  skip_final_snapshot     = false

  # Enable TLS/SSL
  iam_database_authentication_enabled = true
  enabled_cloudwatch_logs_exports     = ["postgresql", "upgrade"]
}
```

### Field-Level Encryption

```python
# app/infrastructure/services/encryption_service.py
import base64
import os
from typing import Any, Dict, List, Optional, Union

import boto3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config.settings import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class EncryptionService:
    """Service for field-level encryption of sensitive data"""

    def __init__(self):
        self.use_kms = settings.USE_AWS_KMS

        if self.use_kms:
            # Initialize AWS KMS client
            self.kms_client = boto3.client(
                'kms',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.data_key_id = settings.KMS_DATA_KEY_ID
        else:
            # Local encryption key for development
            salt = base64.b64decode(settings.ENCRYPTION_SALT)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(settings.ENCRYPTION_MASTER_KEY.encode())
            )
            self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext data

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return plaintext

        try:
            if self.use_kms:
                # Encrypt with AWS KMS
                response = self.kms_client.encrypt(
                    KeyId=self.data_key_id,
                    Plaintext=plaintext.encode('utf-8')
                )
                ciphertext = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
            else:
                # Encrypt with local Fernet key
                ciphertext = self.cipher.encrypt(plaintext.encode('utf-8')).decode('utf-8')

            return ciphertext

        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext data

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext
        """
        if not ciphertext:
            return ciphertext

        try:
            if self.use_kms:
                # Decrypt with AWS KMS
                response = self.kms_client.decrypt(
                    CiphertextBlob=base64.b64decode(ciphertext)
                )
                plaintext = response['Plaintext'].decode('utf-8')
            else:
                # Decrypt with local Fernet key
                plaintext = self.cipher.decrypt(ciphertext.encode('utf-8')).decode('utf-8')

            return plaintext

        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise

    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: List[str]) -> Dict[str, Any]:
        """
        Encrypt specified fields in a dictionary

        Args:
            data: Dictionary with data to encrypt
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        if not data:
            return data

        encrypted_data = data.copy()

        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                # Only encrypt strings
                if isinstance(encrypted_data[field], str):
                    encrypted_data[field] = self.encrypt(encrypted_data[field])

        return encrypted_data

    def decrypt_dict(self, data: Dict[str, Any], fields_to_decrypt: List[str]) -> Dict[str, Any]:
        """
        Decrypt specified fields in a dictionary

        Args:
            data: Dictionary with encrypted data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        if not data:
            return data

        decrypted_data = data.copy()

        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                # Only decrypt strings
                if isinstance(decrypted_data[field], str):
                    decrypted_data[field] = self.decrypt(decrypted_data[field])

        return decrypted_data
```

### SQLAlchemy Type for Encrypted Fields

```python
# app/infrastructure/database/types.py
import json
from typing import Any, Dict, Optional, Type

from sqlalchemy import String, TypeDecorator

from app.infrastructure.services.encryption_service import EncryptionService
from app.utils.logger import get_logger

logger = get_logger(__name__)
encryption_service = EncryptionService()


class EncryptedString(TypeDecorator):
    """SQLAlchemy type for encrypted string fields"""

    impl = String

    def process_bind_parameter(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Encrypt string before saving to database"""
        if value is not None:
            return encryption_service.encrypt(value)
        return value

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Decrypt string when loading from database"""
        if value is not None:
            return encryption_service.decrypt(value)
        return value


class EncryptedJSON(TypeDecorator):
    """SQLAlchemy type for encrypted JSON fields"""

    impl = String

    def process_bind_parameter(self, value: Optional[Dict[str, Any]], dialect: Any) -> Optional[str]:
        """Encrypt JSON before saving to database"""
        if value is not None:
            json_str = json.dumps(value)
            return encryption_service.encrypt(json_str)
        return value

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[Dict[str, Any]]:
        """Decrypt JSON when loading from database"""
        if value is not None:
            json_str = encryption_service.decrypt(value)
            return json.loads(json_str)
        return value
```

### Using Encrypted Fields in Models

```python
# app/infrastructure/database/models/patient.py
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base
from app.infrastructure.database.types import EncryptedString, EncryptedJSON


class Patient(Base):
    """Database model for patients with encrypted PHI fields"""
    __tablename__ = "patients"

    id = sa.Column(sa.String(36), primary_key=True)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)

    # Regular fields (not encrypted)
    status = sa.Column(sa.String(20), nullable=False, index=True)

    # Encrypted PHI fields
    first_name = sa.Column(EncryptedString(100), nullable=False)
    last_name = sa.Column(EncryptedString(100), nullable=False)
    date_of_birth = sa.Column(EncryptedString(10), nullable=False)
    ssn = sa.Column(EncryptedString(11), nullable=True)
    email = sa.Column(EncryptedString(255), nullable=False)
    phone = sa.Column(EncryptedString(20), nullable=False)

    # Encrypted address
    address_line1 = sa.Column(EncryptedString(255), nullable=True)
    address_line2 = sa.Column(EncryptedString(255), nullable=True)
    city = sa.Column(EncryptedString(100), nullable=True)
    state = sa.Column(EncryptedString(50), nullable=True)
    postal_code = sa.Column(EncryptedString(20), nullable=True)
    country = sa.Column(EncryptedString(50), nullable=True)

    # Encrypted JSON field for additional data
    additional_info = sa.Column(EncryptedJSON, nullable=True)

    # Foreign keys and relationships
    user_id = sa.Column(sa.String(36), sa.ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="patient")

    # Searchable fields (duplicated for search)
    search_name = sa.Column(sa.String(255), nullable=False, index=True)
    search_email = sa.Column(sa.String(255), nullable=False, index=True)

    __table_args__ = (
        sa.Index("ix_patients_search", "search_name", "search_email"),
    )
```

### Encryption Key Management

```python
# app/config/settings.py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # KMS configuration
    USE_AWS_KMS: bool = Field(True, env="USE_AWS_KMS")
    AWS_REGION: str = Field(..., env="AWS_REGION")
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    KMS_DATA_KEY_ID: str = Field(..., env="KMS_DATA_KEY_ID")

    # Local encryption fallback (for development only)
    ENCRYPTION_MASTER_KEY: str = Field("", env="ENCRYPTION_MASTER_KEY")
    ENCRYPTION_SALT: str = Field("", env="ENCRYPTION_SALT")

    # Fields that should be encrypted
    PHI_FIELDS: list = [
        "first_name", "last_name", "date_of_birth", "ssn",
        "email", "phone", "address_line1", "address_line2",
        "city", "state", "postal_code", "country",
        "diagnosis", "medication", "treatment_notes"
    ]

    class Config:
        env_file = ".env"
```

### Key Rotation Strategy

```python
# app/infrastructure/tasks/key_rotation.py
from datetime import datetime
import boto3
from typing import List, Tuple

from app.config.settings import get_settings
from app.infrastructure.database.dependencies import get_db
from app.infrastructure.services.encryption_service import EncryptionService
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def rotate_encryption_keys(old_key_id: str, new_key_id: str):
    """
    Rotate encryption keys by re-encrypting all sensitive data

    Args:
        old_key_id: Current KMS key ID
        new_key_id: New KMS key ID
    """
    try:
        # Initialize AWS KMS client
        kms_client = boto3.client(
            'kms',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # Initialize encryption service with old key
        old_encryption_service = EncryptionService()

        # Create a new encryption service with new key
        new_encryption_service = EncryptionService()
        new_encryption_service.data_key_id = new_key_id

        # Get database session
        async with get_db() as db:
            # Re-encrypt patient data (process in batches)
            await _reencrypt_patient_data(
                db, old_encryption_service, new_encryption_service
            )

            # Re-encrypt other sensitive data tables...
            # [similar implementation for other tables]

        logger.info(f"Successfully rotated encryption keys from {old_key_id} to {new_key_id}")

    except Exception as e:
        logger.error(f"Failed to rotate encryption keys: {str(e)}")
        raise
```

### Client-Side Encryption

For additional security of highly sensitive data:

```typescript
// frontend/src/utils/encryption.ts
import CryptoJS from 'crypto-js';

/**
 * Encrypt sensitive data on the client side before sending to server
 * Used for highest-sensitivity fields as an additional security layer
 */
export const clientEncrypt = (
  data: string,
  key: string
): string => {
  if (!data) return data;
  return CryptoJS.AES.encrypt(data, key).toString();
};

/**
 * Decrypt client-encrypted data
 */
export const clientDecrypt = (
  encryptedData: string,
  key: string
): string => {
  if (!encryptedData) return encryptedData;
  const bytes = CryptoJS.AES.decrypt(encryptedData, key);
  return bytes.toString(CryptoJS.enc.Utf8);
};

/**
 * Derive encryption key from user password
 * Uses key stretching with PBKDF2
 */
export const deriveEncryptionKey = (
  password: string,
  salt: string
): string => {
  return CryptoJS.PBKDF2(password, salt, {
    keySize: 256 / 32,
    iterations: 10000
  }).toString();
};
```

### Searchable Encryption

To enable searching on encrypted fields:

```python
# app/infrastructure/repositories/patient_repository.py
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.domain.entities.patient import Patient as PatientEntity
from app.infrastructure.database.models.patient import Patient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PatientRepository:
    """Repository for patient data with searchable encryption"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_patient(self, patient: PatientEntity) -> PatientEntity:
        """Create a new patient record"""
        # Create search fields for encrypted data
        search_name = f"{patient.first_name} {patient.last_name}".lower()
        search_email = patient.email.lower()

        db_patient = Patient(
            id=patient.id,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            status=patient.status,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            ssn=patient.ssn,
            email=patient.email,
            phone=patient.phone,
            address_line1=patient.address_line1,
            address_line2=patient.address_line2,
            city=patient.city,
            state=patient.state,
            postal_code=patient.postal_code,
            country=patient.country,
            additional_info=patient.additional_info,
            user_id=patient.user_id,
            # Searchable fields (not encrypted)
            search_name=search_name,
            search_email=search_email,
        )

        self.session.add(db_patient)
        await self.session.commit()
        await self.session.refresh(db_patient)

        # Convert to domain entity
        return self._to_entity(db_patient)

    async def search_patients(self, search_term: str) -> List[PatientEntity]:
        """
        Search patients by name or email

        Uses searchable non-encrypted fields for performance
        """
        # Normalize search term
        search_term = f"%{search_term.lower()}%"

        # Search using non-encrypted search fields
        query = select(Patient).where(
            (Patient.search_name.like(search_term)) |
            (Patient.search_email.like(search_term))
        )

        result = await self.session.execute(query)
        patients = result.scalars().all()

        # Convert to domain entities
        return [self._to_entity(p) for p in patients]
```

### Backup Encryption

```python
# app/infrastructure/tasks/backup.py
import boto3
import json
from datetime import datetime
from sqlalchemy import select
from typing import Dict, List

from app.config.settings import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def backup_encrypted_data():
    """Create encrypted backup of database data"""
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # Generate backup timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        # Get database session
        async with get_db() as db:
            # Backup patients (with encrypted fields)
            await _backup_table(db, s3_client, "patients", timestamp)

            # Backup other tables
            # [similar implementation for other tables]

        logger.info(f"Successfully created encrypted backup at {timestamp}")

    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        raise
```

### Encryption Implementation Details

1. **Data at Rest**
   - Field-level encryption for PHI in database
   - Transparent Data Encryption (TDE) for database files
   - Encrypted backups with separate key management

2. **Data in Transit**
   - TLS 1.3 for all communications
   - Certificate pinning for API clients
   - Secure WebSockets for real-time data

3. **Key Management**
   - AWS KMS for key storage and rotation
   - Separate keys for different data categories
   - Automatic key rotation every 90 days

### Best Practices for HIPAA-Compliant Encryption

1. **Defense in Depth**: Implement multiple layers of encryption
2. **Key Management**: Use a robust key management system (AWS KMS)
3. **Field-Level Encryption**: Encrypt PHI at the field level
4. **Key Rotation**: Regularly rotate encryption keys
5. **No PHI in Logs**: Ensure PHI is never logged, even in encrypted form
6. **Secure Key Storage**: Never store encryption keys alongside encrypted data
7. **Minimal Access**: Restrict access to encryption keys
8. **Encryption in Transit**: Always use TLS 1.3 for data transmission
9. **Backup Encryption**: Ensure all backups are encrypted
10. **Documentation**: Maintain documentation of encryption methods for HIPAA audits

## API Security

NOVAMIND implements comprehensive API security measures:

```python
# app/presentation/middleware/security_middleware.py
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.utils.logging import logger

def setup_security_middleware(app: FastAPI) -> None:
    """Configure security middleware for the application."""
    # CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        
        return response
```

### API Security Implementation Details

1. **Authentication**
   - JWT-based authentication for all API endpoints
   - Token validation and signature verification
   - Short-lived tokens with refresh mechanism

2. **Authorization**
   - Role-based access control for all endpoints
   - Resource-level permissions
   - Data filtering based on user role

3. **Input Validation**
   - Strict schema validation for all requests
   - Input sanitization to prevent injection attacks
   - Rate limiting to prevent abuse

4. **Security Headers**
   - Content Security Policy (CSP)
   - HTTP Strict Transport Security (HSTS)
   - X-Content-Type-Options
   - X-Frame-Options
   - X-XSS-Protection

## Implementation Guidelines

### Security Best Practices

1. **Defense in Depth**
   - Implement multiple layers of security controls
   - Assume breach mentality in security design
   - Regular security testing and validation

2. **Least Privilege**
   - Grant minimal permissions needed for each role
   - Regularly review and audit permissions
   - Time-bound elevated access for administrative tasks

3. **Secure Development**
   - Security code reviews for all changes
   - Static application security testing (SAST)
   - Dynamic application security testing (DAST)
   - Regular dependency scanning for vulnerabilities

### HIPAA Compliance Checklist

1. **Administrative Safeguards**
   - Security management process
   - Assigned security responsibility
   - Workforce security
   - Information access management
   - Security awareness and training
   - Security incident procedures
   - Contingency plan
   - Evaluation
   - Business associate contracts

2. **Physical Safeguards**
   - Facility access controls
   - Workstation use
   - Workstation security
   - Device and media controls

3. **Technical Safeguards**
   - Access control
   - Audit controls
   - Integrity controls
   - Transmission security
   - Authentication

### Security Monitoring and Incident Response

1. **Monitoring**
   - Real-time monitoring of authentication events
   - Anomaly detection for unusual access patterns
   - Regular review of audit logs
   - Automated alerts for security events

2. **Incident Response**
   - Documented incident response plan
   - Defined roles and responsibilities
   - Regular tabletop exercises
   - Post-incident analysis and improvement

3. **Breach Notification**
   - Documented breach notification procedures
   - Risk assessment process
   - Notification templates and communication plan
   - Documentation and reporting requirements

## Authentication API Endpoints

### Authentication Flow

The NOVAMIND platform implements a multi-stage authentication flow:

1. **Registration**: User provides email and creates password
2. **Confirmation**: Email verification via confirmation code
3. **Login**: Credentials validated, tokens issued
4. **Token Refresh**: Access token refreshed using refresh token
5. **Password Reset**: Secure password recovery flow
6. **MFA**: Multi-factor authentication for enhanced security

### User Registration

```python
# app/presentation/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.domain.exceptions.auth import UserAlreadyExistsError
from app.infrastructure.services.cognito_service import CognitoService
from app.presentation.schemas.auth import RegisterUserRequest, RegisterUserResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
   "/register",
   response_model=RegisterUserResponse,
   status_code=status.HTTP_201_CREATED,
   description="Register a new user with email and password"
)
async def register_user(
   request: RegisterUserRequest,
   cognito_service: CognitoService = Depends(),
):
   """
   Register a new user in the system

   - Validates email format and password requirements
   - Creates user in Cognito user pool
   - Sends confirmation code to user's email
   - Returns confirmation status and next steps

   HIPAA Compliance:
   - No PHI stored during registration
   - Secured with HTTPS
   - Password policy enforced via Cognito
   """
   try:
       # Register user with Cognito
       result = await cognito_service.register_user(
           email=request.email,
           password=request.password,
           first_name=request.first_name,
           last_name=request.last_name
       )

       # HIPAA-compliant audit logging (omitting sensitive data)
       logger.info(
           "User registration attempt",
           extra={
               "email_domain": request.email.split('@')[1],
               "status": "success"
           }
       )

       # Return success response with next steps
       return RegisterUserResponse(
           message="User registration successful. Please check your email for confirmation code.",
           user_id=result["user_id"],
           requires_confirmation=True
       )

   except UserAlreadyExistsError as e:
       # Log the error (without exposing personal data)
       logger.warning(
           "User registration failed - email already exists",
           extra={
               "email_domain": request.email.split('@')[1],
           }
       )

       # Return user-friendly error
       raise HTTPException(
           status_code=status.HTTP_409_CONFLICT,
           detail="A user with this email already exists."
       )

   except Exception as e:
       # Generic error logging (for debugging, without PHI)
       logger.error(
           f"User registration failed: {str(e)}",
           extra={
               "email_domain": request.email.split('@')[1],
           }
       )

       # Return generic error to avoid information disclosure
       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail="An error occurred during registration. Please try again later."
       )
```

### User Confirmation

```python
@router.post(
   "/confirm",
   status_code=status.HTTP_200_OK,
   description="Confirm user registration with code from email"
)
async def confirm_registration(
   user_id: str,
   confirmation_code: str,
   cognito_service: CognitoService = Depends(),
):
   """
   Confirm user registration with verification code

   - Validates confirmation code sent to user's email
   - Activates user account if code is valid
   - Returns confirmation success message

   HIPAA Compliance:
   - Secured with HTTPS
   - Audit logging of confirmation attempts
   """
   try:
       # Confirm registration with Cognito
       await cognito_service.confirm_registration(
           user_id=user_id,
           confirmation_code=confirmation_code
       )

       # HIPAA-compliant audit logging
       logger.info(
           "User confirmation successful",
           extra={
               "user_id": user_id,
               "status": "success"
           }
       )

       # Return success response
       return {"message": "User confirmed successfully. You can now login."}

   except Exception as e:
       # Log the error
       logger.warning(
           f"User confirmation failed: {str(e)}",
           extra={
               "user_id": user_id,
               "status": "failure"
           }
       )

       # Return user-friendly error
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail="Invalid confirmation code. Please try again."
       )
```

### User Login

```python
@router.post(
   "/token",
   status_code=status.HTTP_200_OK,
   description="Login with email and password to receive JWT tokens"
)
async def login(
   form_data: OAuth2PasswordRequestForm = Depends(),
   cognito_service: CognitoService = Depends(),
   jwt_service: JWTService = Depends(),
):
   """
   Authenticate user and issue JWT tokens

   - Validates user credentials against Cognito
   - Issues access and refresh tokens
   - Returns tokens and user information

   HIPAA Compliance:
   - Secured with HTTPS
   - Audit logging of login attempts
   - Short-lived access tokens (15-30 minutes)
   - No PHI in token claims
   """
   try:
       # Authenticate user with Cognito
       auth_result = await cognito_service.login_user(
           username=form_data.username,
           password=form_data.password
       )

       # Extract user info from Cognito response
       user_id = auth_result["user_id"]
       email = auth_result["email"]

       # Get user roles from database
       user_roles = await role_service.get_user_roles(user_id)

       # Create token payload with claims
       token_data = {
           "sub": user_id,
           "email": email,
           "roles": [role.value for role in user_roles]
       }

       # Generate JWT tokens
       access_token = jwt_service.create_access_token(token_data)
       refresh_token = jwt_service.create_refresh_token(token_data)

       # HIPAA-compliant audit logging
       logger.info(
           "User login successful",
           extra={
               "user_id": user_id,
               "roles": [role.value for role in user_roles],
               "status": "success"
           }
       )

       # Return tokens and user info
       return {
           "access_token": access_token,
           "refresh_token": refresh_token,
           "token_type": "bearer",
           "user": {
               "id": user_id,
               "email": email,
               "roles": [role.value for role in user_roles]
           }
       }

   except Exception as e:
       # Log the error (without exposing credentials)
       logger.warning(
           f"Login failed: {str(e)}",
           extra={
               "username_domain": form_data.username.split('@')[1] if '@' in form_data.username else None,
               "status": "failure"
           }
       )

       # Return user-friendly error
       raise HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Invalid credentials",
           headers={"WWW-Authenticate": "Bearer"},
       )
```

### Token Refresh

```python
@router.post(
   "/refresh",
   status_code=status.HTTP_200_OK,
   description="Refresh access token using refresh token"
)
async def refresh_token(
   refresh_token: str,
   jwt_service: JWTService = Depends(),
   token_blacklist: TokenBlacklistService = Depends(),
):
   """
   Refresh access token using refresh token

   - Validates refresh token
   - Issues new access token
   - Optionally rotates refresh token
   - Returns new tokens

   HIPAA Compliance:
   - Secured with HTTPS
   - Audit logging of token refresh
   - Token blacklisting for revoked tokens
   """
   try:
       # Verify refresh token
       token_data = jwt_service.decode_token(refresh_token)

       # Check if token is blacklisted
       jti = token_data.get("jti")
       if await token_blacklist.is_blacklisted(jti):
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Token has been revoked",
               headers={"WWW-Authenticate": "Bearer"},
           )

       # Verify token type
       if token_data.get("token_type") != "refresh":
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid token type",
               headers={"WWW-Authenticate": "Bearer"},
           )

       # Create new token payload
       user_id = token_data.get("sub")
       new_token_data = {
           "sub": user_id,
           "email": token_data.get("email"),
           "roles": token_data.get("roles", []),
           "refresh_jti": jti  # Link to original refresh token
       }

       # Generate new tokens
       new_access_token = jwt_service.create_access_token(new_token_data)

       # Optionally rotate refresh token for enhanced security
       new_refresh_token = jwt_service.create_refresh_token(new_token_data)

       # Blacklist old refresh token (token rotation)
       await token_blacklist.blacklist_token(jti, token_data.get("exp"))

       # HIPAA-compliant audit logging
       logger.info(
           "Token refresh successful",
           extra={
               "user_id": user_id,
               "status": "success"
           }
       )

       # Return new tokens
       return {
           "access_token": new_access_token,
           "refresh_token": new_refresh_token,
           "token_type": "bearer"
       }

   except Exception as e:
       # Log the error
       logger.warning(
           f"Token refresh failed: {str(e)}",
           extra={
               "status": "failure"
           }
       )

       # Return user-friendly error
       raise HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Invalid refresh token",
           headers={"WWW-Authenticate": "Bearer"},
       )
```

### Password Reset

```python
@router.post(
   "/reset-password-request",
   status_code=status.HTTP_200_OK,
   description="Request password reset via email"
)
async def request_password_reset(
   email: str,
   cognito_service: CognitoService = Depends(),
):
   """
   Request password reset code

   - Sends reset code to user's email
   - Returns success message

   HIPAA Compliance:
   - Secured with HTTPS
   - Audit logging of reset requests
   - No information disclosure on whether email exists
   """
   try:
       # Request password reset from Cognito
       await cognito_service.forgot_password(email)

       # HIPAA-compliant audit logging
       logger.info(
           "Password reset requested",
           extra={
               "email_domain": email.split('@')[1],
               "status": "initiated"
           }
       )

       # Return success message
       # Note: Always return success even if email doesn't exist
       # This prevents user enumeration attacks
       return {
           "message": "If your email exists in our system, you will receive a password reset code."
       }

   except Exception as e:
       # Log the error
       logger.warning(
           f"Password reset request failed: {str(e)}",
           extra={
               "email_domain": email.split('@')[1],
               "status": "failure"
           }
       )

       # Always return the same message to prevent user enumeration
       return {
           "message": "If your email exists in our system, you will receive a password reset code."
       }
```

### Password Reset Confirmation

```python
@router.post(
   "/reset-password-confirm",
   status_code=status.HTTP_200_OK,
   description="Complete password reset with code and new password"
)
async def confirm_password_reset(
   email: str,
   reset_code: str,
   new_password: str,
   cognito_service: CognitoService = Depends(),
):
   """
   Confirm password reset with verification code

   - Validates reset code
   - Sets new password
   - Returns success message

   HIPAA Compliance:
   - Secured with HTTPS
   - Audit logging of password changes
   - Password complexity requirements enforced
   """
   try:
       # Confirm password reset with Cognito
       await cognito_service.confirm_forgot_password(
           email=email,
           confirmation_code=reset_code,
           new_password=new_password
       )

       # HIPAA-compliant audit logging
       logger.info(
           "Password reset completed",
           extra={
               "email_domain": email.split('@')[1],
               "status": "success"
           }
       )

       # Return success message
       return {"message": "Password has been reset successfully. You can now login with your new password."}

   except Exception as e:
       # Log the error
       logger.warning(
           f"Password reset confirmation failed: {str(e)}",
           extra={
               "email_domain": email.split('@')[1],
               "status": "failure"
           }
       )

       # Return user-friendly error
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail="Invalid reset code or password. Please try again."
       )
```

### Logout

```python
@router.post(
   "/logout",
   status_code=status.HTTP_204_NO_CONTENT,
   description="Logout user by blacklisting tokens"
)
async def logout(
   token_blacklist: TokenBlacklistService = Depends(),
   current_user: dict = Depends(get_current_user),
   request: Request = None,
):
   """
   Logout user by blacklisting current tokens

   - Blacklists current access token
   - Blacklists associated refresh token if available
   - Returns no content on success

   HIPAA Compliance:
   - Secured with HTTPS
   - Audit logging of logout events
   - Complete session termination
   """
   try:
       # Get token from authorization header
       auth_header = request.headers.get("Authorization")
       token = auth_header.split()[1] if auth_header else None

       if token:
           # Get token data
           token_data = jwt_service.decode_token(token)
           jti = token_data.get("jti")
           exp = token_data.get("exp")

           # Blacklist the current token
           await token_blacklist.blacklist_token(jti, exp)

           # Also blacklist the refresh token if linked
           refresh_jti = token_data.get("refresh_jti")
           if refresh_jti:
               await token_blacklist.blacklist_token(refresh_jti)

       # HIPAA-compliant audit logging
       logger.info(
           "User logout",
           extra={
               "user_id": current_user.get("sub"),
               "status": "success"
           }
       )

       # Return no content for successful logout
       return None

   except Exception as e:
       # Log the error
       logger.warning(
           f"Logout failed: {str(e)}",
           extra={
               "user_id": current_user.get("sub") if current_user else None,
               "status": "failure"
           }
       )

       # Still return success to client
       # This is to ensure session appears terminated to user
       return None
```

### Request/Response Schemas

```python
# app/presentation/schemas/auth.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, SecretStr, validator


class RegisterUserRequest(BaseModel):
   """Schema for user registration request"""
   email: EmailStr = Field(..., description="User's email address")
   password: SecretStr = Field(..., description="User's password")
   first_name: str = Field(..., description="User's first name")
   last_name: str = Field(..., description="User's last name")

   @validator('password')
   def password_strength(cls, v):
       """Validate password strength"""
       password = v.get_secret_value()
       if len(password) < 8:
           raise ValueError("Password must be at least 8 characters long")
       if not any(c.isupper() for c in password):
           raise ValueError("Password must contain at least one uppercase letter")
       if not any(c.islower() for c in password):
           raise ValueError("Password must contain at least one lowercase letter")
       if not any(c.isdigit() for c in password):
           raise ValueError("Password must contain at least one digit")
       if not any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~" for c in password):
           raise ValueError("Password must contain at least one special character")
       return v


class RegisterUserResponse(BaseModel):
   """Schema for user registration response"""
   message: str
   user_id: str
   requires_confirmation: bool


class TokenResponse(BaseModel):
   """Schema for token response"""
   access_token: str
   refresh_token: str
   token_type: str
   user: dict
```

### HIPAA Compliance Measures

The authentication system implements these HIPAA-compliant security measures:

1. **Secure Transmission**: All endpoints require HTTPS
2. **Password Policies**: Enforced complexity and expiration
3. **MFA**: Multi-factor authentication for all clinical users
4. **Audit Logging**: Comprehensive logging of all authentication events
5. **Session Management**: Short-lived access tokens (15-30 min)
6. **Token Blacklisting**: Immediate invalidation of logged-out sessions
7. **Failed Attempt Tracking**: Lockout after multiple failed attempts
8. **Information Disclosure Prevention**: Generic error messages
9. **Account Recovery**: Secure password reset flow
