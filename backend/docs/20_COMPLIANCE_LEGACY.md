# SECURITY_AND_COMPLIANCE

## Overview

The NOVAMIND platform implements comprehensive security measures and HIPAA compliance controls to protect patient data. This document outlines the security architecture, encryption mechanisms, access controls, and audit logging required for a compliant psychiatric platform.

## Security Architecture Overview

```python
┌─────────────────────────────────────────────────────────────────────┐
│                        SECURITY ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐    │
│  │             │     │             │     │                     │    │
│  │    User     │────▶│ AWS Cognito │────▶│  JWT Authentication │    │
│  │             │     │    + MFA    │     │                     │    │
│  └─────────────┘     └─────────────┘     └─────────────────────┘    │
│        │                                           │                │
│        ▼                                           ▼                │
│  ┌─────────────┐                         ┌─────────────────────┐    │
│  │             │                         │                     │    │
│  │   HTTPS     │                         │  Role-Based Access  │    │
│  │ Encryption  │                         │     Control         │    │
│  │             │                         │                     │    │
│  └─────────────┘                         └─────────────────────┘    │
│                                                     │                │
│                                                     ▼                │
│                                          ┌─────────────────────┐    │
│                                          │                     │    │
│                                          │  Data Encryption    │    │
│                                          │  at Rest & Transit  │    │
│                                          │                     │    │
│                                          └─────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Security Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Authentication | AWS Cognito | User management, MFA, password policies |
| Authorization | JWT-based RBAC | Role-based access control for APIs |
| Transport Security | HTTPS/TLS | Secure data transmission |
| Data Security | Field-level encryption | Protection of sensitive PHI |
| Audit Logging | Custom middleware | Track all access to PHI |
| Session Management | Short-lived JWTs | Prevent unauthorized access |

## HIPAA Compliance Requirements

### Protected Health Information (PHI)

The following data elements are considered PHI and require special protection:

1. Patient names and identifiers
2. Contact information (address, phone, email)
3. Medical record numbers
4. Health plan beneficiary numbers
5. Dates directly related to a patient
6. Biometric identifiers
7. Full-face photographic images
8. Any other unique identifying characteristics

### Required Safeguards

1. **Administrative Safeguards**
   - Security management process
   - Security personnel
   - Information access management
   - Workforce training and management
   - Evaluation

2. **Physical Safeguards**
   - Facility access controls
   - Workstation and device security

3. **Technical Safeguards**
   - Access control
   - Audit controls
   - Integrity controls
   - Transmission security

### HIPAA Security Implementation

| HIPAA Requirement | Implementation |
|-------------------|----------------|
| Access Controls (§164.312(a)(1)) | Role-based access control with AWS Cognito |
| Audit Controls (§164.312(b)) | Comprehensive audit logging for all PHI access |
| Integrity (§164.312(c)(1)) | SHA-256 hashing to verify data integrity |
| Person/Entity Authentication (§164.312(d)) | Multi-factor authentication with Cognito |
| Transmission Security (§164.312(e)(1)) | TLS 1.2+ for all data in transit |

## Authentication and Authorization

```python
# app/core/security/auth.py
from datetime import datetime, timedelta
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.domain.entities.user import User
from app.application.dtos.auth_dto import TokenPayload
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.core.utils.logging import logger, log_audit

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, int], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repository: UserRepository = Depends()
) -> User:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise credentials_exception
            
    except (JWTError, ValidationError):
        logger.error("JWT validation error", exc_info=True)
        raise credentials_exception
        
    user = await user_repository.get_by_email(token_data.sub)
    
    if user is None:
        raise credentials_exception
        
    log_audit(
        user_id=str(user.id),
        action="authenticate",
        resource_type="user",
        resource_id=str(user.id),
        details={"method": "jwt"}
    )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Check if user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user"
        )
    return current_user

class RoleChecker:
    """Role-based access control."""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
        
    async def __call__(
        self, 
        current_user: User = Depends(get_current_active_user)
    ):
        """Check if user has required role."""
        if current_user.role not in self.allowed_roles:
            logger.warning(
                f"User {current_user.email} with role {current_user.role} "
                f"attempted to access endpoint requiring roles {self.allowed_roles}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
            
        return current_user
```

## Encryption

```python
# app/core/security/encryption.py
import base64
import os
from typing import Any, Dict, List, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.core.utils.logging import logger

class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with key from environment."""
        # Get encryption key from environment or generate one
        encryption_key = settings.ENCRYPTION_KEY
        
        if encryption_key:
            self.key = base64.urlsafe_b64decode(encryption_key)
        else:
            # Generate a key from password and salt
            password = settings.ENCRYPTION_PASSWORD.encode()
            salt = settings.ENCRYPTION_SALT.encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Initialize Fernet cipher
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64-encoded string."""
        if isinstance(data, str):
            data = data.encode()
        
        encrypted_data = self.cipher.encrypt(data)
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        """Decrypt base64-encoded encrypted data."""
        if isinstance(encrypted_data, str):
            encrypted_data = base64.urlsafe_b64decode(encrypted_data)
        
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return decrypted_data.decode()
    
    def encrypt_dict(self, data: Dict[str, Any], keys_to_encrypt: List[str]) -> Dict[str, Any]:
        """Encrypt specific keys in a dictionary."""
        result = {}
        
        for key, value in data.items():
            if key in keys_to_encrypt and value is not None:
                if isinstance(value, (str, bytes)):
                    result[key] = self.encrypt(value)
                else:
                    # Convert to string if not already
                    result[key] = self.encrypt(str(value))
            elif isinstance(value, dict):
                result[key] = self.encrypt_dict(value, keys_to_encrypt)
            else:
                result[key] = value
        
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], keys_to_decrypt: List[str]) -> Dict[str, Any]:
        """Decrypt specific keys in a dictionary."""
        result = {}
        
        for key, value in data.items():
            if key in keys_to_decrypt and value is not None and isinstance(value, str):
                try:
                    result[key] = self.decrypt(value)
                except Exception as e:
                    logger.warning(f"Failed to decrypt key {key}: {str(e)}")
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self.decrypt_dict(value, keys_to_decrypt)
            else:
                result[key] = value
        
        return result

# Create singleton instance
encryption_service = EncryptionService()
```

## Audit Logging

```python
# app/core/utils/audit.py
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.utils.logging import logger
from app.infrastructure.persistence.models.audit_log_model import AuditLogModel

def log_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    db_session: Optional[Session] = None
) -> None:
    """
    Log audit event for HIPAA compliance.
    
    Args:
        user_id: ID of the user performing the action
        action: Action being performed (e.g., "view", "create", "update", "delete")
        resource_type: Type of resource being accessed (e.g., "patient", "appointment")
        resource_id: ID of the resource being accessed
        details: Additional details about the action
        db_session: Optional database session for persistence
    """
    timestamp = datetime.utcnow()
    audit_id = str(uuid.uuid4())
    
    audit_data = {
        "id": audit_id,
        "timestamp": timestamp.isoformat(),
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "ip_address": None,  # Will be set by middleware
        "user_agent": None,  # Will be set by middleware
    }
    
    # Log to file
    logger.info(f"AUDIT: {json.dumps(audit_data)}")
    
    # Persist to database if session provided
    if db_session:
        try:
            audit_log = AuditLogModel(
                id=audit_id,
                timestamp=timestamp,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=None,
                user_agent=None
            )
            
            db_session.add(audit_log)
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to persist audit log: {str(e)}")
            db_session.rollback()
```

## Middleware

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

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request information."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- IP: {client_ip} "
                f"- Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            logger.error(
                f"Request error: {request.method} {request.url.path} "
                f"- IP: {client_ip} "
                f"- Error: {str(e)}"
            )
            raise
```

## Data Anonymization

```python
# app/core/utils/anonymization.py
import hashlib
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

def anonymize_patient_data(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize patient data for research and analytics.
    
    Args:
        patient_data: Patient data to anonymize
        
    Returns:
        Anonymized patient data
    """
    # Create a copy to avoid modifying the original
    anonymized = patient_data.copy()
    
    # Hash identifiers
    if "id" in anonymized:
        anonymized["id"] = hashlib.sha256(str(anonymized["id"]).encode()).hexdigest()
    
    # Remove directly identifiable information
    for field in ["first_name", "last_name", "email", "phone", "ssn"]:
        if field in anonymized:
            del anonymized[field]
    
    # Generalize date of birth to year only
    if "date_of_birth" in anonymized and anonymized["date_of_birth"]:
        if isinstance(anonymized["date_of_birth"], str):
            try:
                dob = datetime.strptime(anonymized["date_of_birth"], "%Y-%m-%d").date()
                anonymized["birth_year"] = dob.year
            except ValueError:
                anonymized["birth_year"] = None
        elif isinstance(anonymized["date_of_birth"], (date, datetime)):
            anonymized["birth_year"] = anonymized["date_of_birth"].year
        
        del anonymized["date_of_birth"]
    
    # Remove or generalize address
    if "address" in anonymized and anonymized["address"]:
        if isinstance(anonymized["address"], dict):
            # Keep only state and first 3 digits of ZIP code
            if "state" in anonymized["address"]:
                anonymized["address"] = {"state": anonymized["address"]["state"]}
            
            if "zip_code" in anonymized["address"]:
                zip_code = anonymized["address"]["zip_code"]
                if isinstance(zip_code, str) and len(zip_code) >= 3:
                    anonymized["address"]["zip_code_prefix"] = zip_code[:3]
            
            # Remove specific address fields
            for field in ["street1", "street2", "city"]:
                if field in anonymized["address"]:
                    del anonymized["address"][field]
        else:
            del anonymized["address"]
    
    # Remove insurance details
    if "insurance" in anonymized:
        del anonymized["insurance"]
    
    # Remove emergency contact
    if "emergency_contact" in anonymized:
        del anonymized["emergency_contact"]
    
    return anonymized

def redact_phi(text: str) -> str:
    """
    Redact PHI from text.
    
    Args:
        text: Text to redact
        
    Returns:
        Redacted text
    """
    # Patterns to redact
    patterns = [
        # Names (this is simplistic, would need more sophisticated NER in production)
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
        # Email addresses
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        # Phone numbers
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        # SSNs
        r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
        # Dates
        r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        # ZIP codes
        r'\b\d{5}(?:[-\s]\d{4})?\b',
        # IP addresses
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    ]
    
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, '[REDACTED]', redacted)
    
    return redacted
```

## Security Configuration

```python
# app/core/config.py
import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, PostgresDsn, validator

class SecuritySettings(BaseSettings):
    """Security-specific settings."""
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Encryption settings
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")
    ENCRYPTION_PASSWORD: str = os.getenv("ENCRYPTION_PASSWORD", "")
    ENCRYPTION_SALT: str = os.getenv("ENCRYPTION_SALT", "")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Password policy
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Session settings
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 100  # requests per minute
    RATE_LIMIT_LOGIN: int = 5  # login attempts per minute
    
    # HIPAA settings
    HIPAA_COMPLIANT: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 365 * 6  # 6 years
    
    # AWS settings for secure storage
    AWS_S3_SECURE_BUCKET: Optional[str] = os.getenv("AWS_S3_SECURE_BUCKET")
    AWS_KMS_KEY_ID: Optional[str] = os.getenv("AWS_KMS_KEY_ID")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Include in main settings
class Settings(BaseSettings):
    """Application settings."""
    
    # ... other settings ...
    
    # Include security settings
    security: SecuritySettings = SecuritySettings()
    
    # ... other settings ...
```

## Implementation Guidelines

### Authentication and Authorization

1. **Multi-Factor Authentication**: Implement MFA for all provider accounts
2. **Password Policy**: Enforce strong password requirements
3. **Session Management**: Implement secure session handling with timeouts
4. **Role-Based Access Control**: Restrict access based on user roles
5. **Least Privilege**: Grant minimal permissions needed for each role

### Data Protection

1. **Encryption at Rest**: Encrypt all PHI stored in the database
2. **Encryption in Transit**: Use TLS 1.3 for all communications
3. **Key Management**: Implement secure key rotation and management
4. **Data Minimization**: Collect only necessary PHI
5. **Data Retention**: Implement appropriate data retention policies

### Audit and Monitoring

1. **Comprehensive Logging**: Log all access to PHI
2. **Intrusion Detection**: Monitor for unauthorized access attempts
3. **Anomaly Detection**: Identify unusual access patterns
4. **Regular Reviews**: Conduct periodic reviews of audit logs
5. **Automated Alerts**: Set up alerts for security events

### Incident Response

1. **Response Plan**: Develop and document an incident response plan
2. **Breach Notification**: Implement procedures for breach notification
3. **Recovery Procedures**: Document steps for system recovery
4. **Testing**: Regularly test the incident response plan
5. **Documentation**: Maintain records of all security incidents