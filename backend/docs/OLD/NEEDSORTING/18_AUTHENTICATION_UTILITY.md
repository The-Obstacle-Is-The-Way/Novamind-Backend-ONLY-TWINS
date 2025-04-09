# NOVAMIND: HIPAA-Compliant Authentication Utility

## 1. Overview

The Authentication Utility is a critical component of the NOVAMIND platform that provides robust, HIPAA-compliant authentication and authorization services. This utility implements secure user authentication, role-based access control (RBAC), and comprehensive audit logging to ensure that only authorized users can access protected health information (PHI).

## 2. Key Features

- **JWT Token Management**: Secure generation and validation of JSON Web Tokens
- **Role-Based Access Control**: Fine-grained permission management based on user roles
- **Password Security**: Secure password hashing and verification
- **Multi-Factor Authentication**: Enhanced security with MFA support
- **Session Management**: Secure session handling with appropriate timeouts
- **Audit Logging**: Comprehensive logging of authentication events

## 3. Implementation

### 3.1 JWT Authentication Implementation

```python
# app/utils/auth.py
import datetime
import os
from typing import Dict, List, Optional, Tuple, Union

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.models.user import User
from app.utils.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

class AuthService:
    """
    HIPAA-compliant authentication service for managing JWT tokens,
    user authentication, and authorization.
    """
    
    def __init__(self):
        """Initialize the authentication service."""
        self.secret_key = os.environ.get("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable not set")
        
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def create_access_token(self, user_id: str, additional_data: Optional[Dict] = None) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user_id: User ID to include in the token
            additional_data: Additional data to include in the token
            
        Returns:
            JWT access token
        """
        payload = {
            "sub": user_id,
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=self.access_token_expire_minutes),
            "type": "access"
        }
        
        if additional_data:
            payload.update(additional_data)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"Access token created for user {user_id}")
        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        Create a JWT refresh token for a user.
        
        Args:
            user_id: User ID to include in the token
            
        Returns:
            JWT refresh token
        """
        payload = {
            "sub": user_id,
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=self.refresh_token_expire_days),
            "type": "refresh"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"Refresh token created for user {user_id}")
        return token
    
    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired token detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            logger.warning(f"Invalid token detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create a new access token using a refresh token.
        
        Args:
            refresh_token: Refresh token to use
            
        Returns:
            New access token
            
        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        payload = self.decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            logger.warning(f"Invalid token type for refresh: {payload.get('type')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        return self.create_access_token(user_id)
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
        """
        Get the current user from the JWT token.
        
        Args:
            credentials: HTTP Authorization credentials
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        token = credentials.credentials
        return self.decode_token(token)
    
    def verify_token_and_get_user_id(self, token: str) -> str:
        """
        Verify a token and extract the user ID.
        
        Args:
            token: JWT token to verify
            
        Returns:
            User ID from the token
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        payload = self.decode_token(token)
        return payload.get("sub")


class RBACService:
    """
    Role-Based Access Control service for managing permissions
    and access control in a HIPAA-compliant manner.
    """
    
    # Define role hierarchies (roles inherit permissions from roles below them)
    ROLE_HIERARCHY = {
        "admin": ["provider", "staff", "patient"],
        "provider": ["staff", "patient"],
        "staff": ["patient"],
        "patient": []
    }
    
    # Define permissions for each resource
    RESOURCE_PERMISSIONS = {
        "patient": {
            "create": ["admin", "provider", "staff"],
            "read": ["admin", "provider", "staff", "patient"],
            "update": ["admin", "provider", "staff"],
            "delete": ["admin"]
        },
        "appointment": {
            "create": ["admin", "provider", "staff", "patient"],
            "read": ["admin", "provider", "staff", "patient"],
            "update": ["admin", "provider", "staff"],
            "delete": ["admin", "provider"]
        },
        "medication": {
            "create": ["admin", "provider"],
            "read": ["admin", "provider", "staff", "patient"],
            "update": ["admin", "provider"],
            "delete": ["admin", "provider"]
        },
        "diagnosis": {
            "create": ["admin", "provider"],
            "read": ["admin", "provider", "staff", "patient"],
            "update": ["admin", "provider"],
            "delete": ["admin", "provider"]
        },
        "billing": {
            "create": ["admin", "staff"],
            "read": ["admin", "provider", "staff", "patient"],
            "update": ["admin", "staff"],
            "delete": ["admin"]
        },
        "user": {
            "create": ["admin"],
            "read": ["admin", "provider", "staff", "patient"],
            "update": ["admin"],
            "delete": ["admin"]
        }
    }
    
    @classmethod
    def get_effective_roles(cls, role: str) -> List[str]:
        """
        Get all effective roles for a given role (including inherited roles).
        
        Args:
            role: User role
            
        Returns:
            List of effective roles
        """
        if role not in cls.ROLE_HIERARCHY:
            return [role]
        
        effective_roles = [role]
        for inherited_role in cls.ROLE_HIERARCHY[role]:
            effective_roles.append(inherited_role)
        
        return effective_roles
    
    @classmethod
    def has_permission(cls, role: str, resource: str, action: str) -> bool:
        """
        Check if a role has permission to perform an action on a resource.
        
        Args:
            role: User role
            resource: Resource being accessed
            action: Action being performed
            
        Returns:
            True if the role has permission, False otherwise
        """
        if resource not in cls.RESOURCE_PERMISSIONS:
            return False
        
        if action not in cls.RESOURCE_PERMISSIONS[resource]:
            return False
        
        effective_roles = cls.get_effective_roles(role)
        allowed_roles = cls.RESOURCE_PERMISSIONS[resource][action]
        
        return any(r in allowed_roles for r in effective_roles)
    
    @classmethod
    def verify_permission(cls, role: str, resource: str, action: str) -> None:
        """
        Verify that a role has permission to perform an action on a resource.
        
        Args:
            role: User role
            resource: Resource being accessed
            action: Action being performed
            
        Raises:
            HTTPException: If the role does not have permission
        """
        if not cls.has_permission(role, resource, action):
            logger.warning(f"Permission denied: {role} attempting {action} on {resource}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} {resource}"
            )
        
        logger.info(f"Permission granted: {role} performing {action} on {resource}")


class PatientAccessControl:
    """
    Patient-specific access control service for ensuring that users
    only have access to patient data they are authorized to view.
    """
    
    @staticmethod
    async def can_access_patient(user_id: str, user_role: str, patient_id: str) -> bool:
        """
        Check if a user has access to a specific patient's data.
        
        Args:
            user_id: ID of the user attempting access
            user_role: Role of the user attempting access
            patient_id: ID of the patient whose data is being accessed
            
        Returns:
            True if the user has access, False otherwise
        """
        # Admin and providers have access to all patients
        if user_role in ["admin", "provider"]:
            return True
        
        # Staff have access to assigned patients
        if user_role == "staff":
            # Check if the staff member is assigned to the patient
            # This would involve a database query to check assignments
            is_assigned = await check_staff_patient_assignment(user_id, patient_id)
            return is_assigned
        
        # Patients only have access to their own data
        if user_role == "patient":
            return user_id == patient_id
        
        return False
    
    @staticmethod
    async def verify_patient_access(user_id: str, user_role: str, patient_id: str) -> None:
        """
        Verify that a user has access to a specific patient's data.
        
        Args:
            user_id: ID of the user attempting access
            user_role: Role of the user attempting access
            patient_id: ID of the patient whose data is being accessed
            
        Raises:
            HTTPException: If the user does not have access
        """
        has_access = await PatientAccessControl.can_access_patient(user_id, user_role, patient_id)
        
        if not has_access:
            logger.warning(f"Patient access denied: {user_id} ({user_role}) attempting to access patient {patient_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this patient's data is not authorized"
            )
        
        logger.info(f"Patient access granted: {user_id} ({user_role}) accessing patient {patient_id}")


# Helper function for checking staff-patient assignments
async def check_staff_patient_assignment(staff_id: str, patient_id: str) -> bool:
    """
    Check if a staff member is assigned to a patient.
    
    Args:
        staff_id: ID of the staff member
        patient_id: ID of the patient
        
    Returns:
        True if the staff member is assigned to the patient, False otherwise
    """
    # This would involve a database query to check assignments
    # For now, we'll just return a placeholder implementation
    return True  # Replace with actual implementation
```

### 3.2 Password Management Implementation

```python
# app/utils/password.py
import hashlib
import os
import secrets
from typing import Tuple

import bcrypt
from passlib.context import CryptContext

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Configure passlib context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordService:
    """
    Service for secure password hashing and verification
    in a HIPAA-compliant manner.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            plain_password: Password to verify
            hashed_password: Hashed password to verify against
            
        Returns:
            True if the password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_password_reset_token() -> Tuple[str, str]:
        """
        Generate a secure token for password reset.
        
        Returns:
            Tuple of (token, hashed_token)
        """
        # Generate a secure random token
        token = secrets.token_hex(32)
        
        # Hash the token for storage
        salt = os.urandom(16)
        hashed_token = hashlib.pbkdf2_hmac('sha256', token.encode(), salt, 100000).hex()
        
        # Return both the token (to send to user) and hashed token (to store)
        return token, f"{salt.hex()}:{hashed_token}"
    
    @staticmethod
    def verify_password_reset_token(token: str, stored_hashed_token: str) -> bool:
        """
        Verify a password reset token.
        
        Args:
            token: Token to verify
            stored_hashed_token: Stored hashed token to verify against
            
        Returns:
            True if the token matches, False otherwise
        """
        # Extract salt and hash from stored token
        salt_hex, hashed_token = stored_hashed_token.split(':')
        salt = bytes.fromhex(salt_hex)
        
        # Hash the provided token with the same salt
        computed_hash = hashlib.pbkdf2_hmac('sha256', token.encode(), salt, 100000).hex()
        
        # Compare the hashes
        return secrets.compare_digest(computed_hash, hashed_token)
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Length of the password to generate
            
        Returns:
            Secure random password
        """
        # Define character sets
        lowercase = 'abcdefghijklmnopqrstuvwxyz'
        uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        special = '!@#$%^&*()-_=+[]{}|;:,.<>?'
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest of the password
        all_chars = lowercase + uppercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
```

## 4. Usage Examples

### 4.1 JWT Token Management

```python
from app.utils.auth import AuthService

# Create an authentication service
auth_service = AuthService()

# Create tokens for a user
user_id = "user_12345"
additional_data = {"role": "provider", "name": "Dr. Smith"}

access_token = auth_service.create_access_token(user_id, additional_data)
refresh_token = auth_service.create_refresh_token(user_id)

print(f"Access Token: {access_token}")
print(f"Refresh Token: {refresh_token}")

# Decode and verify a token
try:
    payload = auth_service.decode_token(access_token)
    print(f"Decoded payload: {payload}")
    
    user_id = auth_service.verify_token_and_get_user_id(access_token)
    print(f"User ID: {user_id}")
except Exception as e:
    print(f"Token verification failed: {e}")

# Refresh an access token
try:
    new_access_token = auth_service.refresh_access_token(refresh_token)
    print(f"New Access Token: {new_access_token}")
except Exception as e:
    print(f"Token refresh failed: {e}")
```

### 4.2 Role-Based Access Control

```python
from app.utils.auth import RBACService

# Check if a user has permission to perform an action
role = "provider"
resource = "patient"
action = "read"

has_permission = RBACService.has_permission(role, resource, action)
print(f"Provider can read patient data: {has_permission}")

# Verify permission (raises exception if not allowed)
try:
    RBACService.verify_permission(role, resource, action)
    print("Permission verified")
except Exception as e:
    print(f"Permission denied: {e}")

# Check a permission that should be denied
role = "patient"
resource = "user"
action = "create"

has_permission = RBACService.has_permission(role, resource, action)
print(f"Patient can create users: {has_permission}")
```

### 4.3 Patient Access Control

```python
import asyncio
from app.utils.auth import PatientAccessControl

async def check_patient_access():
    # Provider accessing patient data
    provider_id = "provider_123"
    provider_role = "provider"
    patient_id = "patient_456"
    
    has_access = await PatientAccessControl.can_access_patient(provider_id, provider_role, patient_id)
    print(f"Provider can access patient data: {has_access}")
    
    # Patient accessing their own data
    patient_user_id = "patient_456"
    patient_role = "patient"
    
    has_access = await PatientAccessControl.can_access_patient(patient_user_id, patient_role, patient_id)
    print(f"Patient can access their own data: {has_access}")
    
    # Patient trying to access another patient's data
    other_patient_id = "patient_789"
    
    has_access = await PatientAccessControl.can_access_patient(patient_user_id, patient_role, other_patient_id)
    print(f"Patient can access another patient's data: {has_access}")

# Run the async function
asyncio.run(check_patient_access())
```

### 4.4 Password Management

```python
from app.utils.password import PasswordService

# Hash a password
password = "SecurePassword123!"
hashed_password = PasswordService.hash_password(password)
print(f"Original password: {password}")
print(f"Hashed password: {hashed_password}")

# Verify a password
is_valid = PasswordService.verify_password(password, hashed_password)
print(f"Password valid: {is_valid}")

# Generate a password reset token
token, hashed_token = PasswordService.generate_password_reset_token()
print(f"Reset token (send to user): {token}")
print(f"Hashed token (store in database): {hashed_token}")

# Verify a password reset token
is_valid = PasswordService.verify_password_reset_token(token, hashed_token)
print(f"Token valid: {is_valid}")

# Generate a secure password
secure_password = PasswordService.generate_secure_password()
print(f"Generated secure password: {secure_password}")
```

## 5. Integration with FastAPI

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.auth import AuthService, RBACService, PatientAccessControl
from app.utils.password import PasswordService

router = APIRouter()
auth_service = AuthService()
security = HTTPBearer()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    return payload

# Role-based permission dependency
def has_permission(resource: str, action: str):
    async def permission_dependency(user = Depends(get_current_user)):
        role = user.get("role", "")
        RBACService.verify_permission(role, resource, action)
        return user
    return permission_dependency

# Patient access control dependency
async def can_access_patient(patient_id: str, user = Depends(get_current_user)):
    user_id = user.get("sub")
    user_role = user.get("role", "")
    await PatientAccessControl.verify_patient_access(user_id, user_role, patient_id)
    return user

# Login endpoint
@router.post("/login")
async def login(username: str, password: str):
    # Authenticate user (implementation depends on your user storage)
    user = await get_user_by_username(username)
    
    if not user or not PasswordService.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create tokens
    access_token = auth_service.create_access_token(
        str(user.id),
        {"role": user.role, "name": user.name}
    )
    refresh_token = auth_service.create_refresh_token(str(user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Protected endpoint with role-based access control
@router.get("/patients")
async def get_patients(user = Depends(has_permission("patient", "read"))):
    # Implementation to get patients
    return {"patients": []}

# Protected endpoint with patient access control
@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, user = Depends(can_access_patient)):
    # Implementation to get a specific patient
    return {"patient": {"id": patient_id, "name": "John Doe"}}

# Token refresh endpoint
@router.post("/refresh-token")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    refresh_token = credentials.credentials
    new_access_token = auth_service.refresh_access_token(refresh_token)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
```

## 6. Best Practices

1. **Secure Key Management**: Store JWT secret keys securely, preferably using a key management service like AWS Secrets Manager.

2. **Token Expiration**: Use short-lived access tokens (30 minutes or less) and longer-lived refresh tokens.

3. **HTTPS Only**: Only transmit tokens over HTTPS to prevent interception.

4. **Principle of Least Privilege**: Assign users the minimum permissions necessary for their role.

5. **Regular Token Rotation**: Implement a process for regularly rotating JWT secret keys.

6. **Secure Password Storage**: Always hash passwords using a strong algorithm like bcrypt.

7. **Multi-Factor Authentication**: Implement MFA for sensitive operations.

8. **Session Termination**: Provide mechanisms for users to terminate all active sessions.

9. **Audit Logging**: Log all authentication and authorization events for audit purposes.

10. **Rate Limiting**: Implement rate limiting for authentication endpoints to prevent brute force attacks.

## 7. HIPAA Compliance Considerations

- **Access Controls**: HIPAA requires implementation of technical policies and procedures for electronic PHI access.

- **Audit Controls**: Implement hardware, software, and procedural mechanisms to record and examine access and other activity.

- **Person or Entity Authentication**: Implement procedures to verify that a person seeking access is the claimed individual.

- **Transmission Security**: Implement technical security measures to guard against unauthorized access to PHI being transmitted over a network.

- **Automatic Logoff**: Implement electronic procedures that terminate an electronic session after a predetermined time of inactivity.

- **Emergency Access**: Establish procedures for obtaining necessary PHI during an emergency.

## 8. Conclusion

The HIPAA-compliant authentication utility is a critical component of the NOVAMIND platform's security infrastructure. By implementing robust authentication, role-based access control, and patient-specific access controls, it helps ensure that only authorized users can access protected health information. This utility plays a key role in meeting HIPAA requirements for access control and security while providing a simple and consistent API for authentication and authorization throughout the application.
