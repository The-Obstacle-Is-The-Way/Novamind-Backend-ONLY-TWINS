# -*- coding: utf-8 -*-
"""
Multi-Factor Authentication Service

This module provides MFA capabilities for the platform, enhancing security
beyond basic password authentication.
"""

import base64
import hmac
import logging
import os
import time
from enum import Enum
from typing import Dict, Optional, Tuple, List, Any
import uuid

import pyotp
import qrcode
from io import BytesIO

from app.core.config import settings
from app.core.utils.enhanced_phi_detector import enhanced_phi_secure_logger as logger


class MFAType(Enum):
    """Types of multi-factor authentication supported by the system."""
    
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"    # SMS-based verification code
    EMAIL = "email"  # Email-based verification code
    APP = "app"    # Authenticator app (TOTP)


class MFAException(Exception):
    """Base exception for MFA-related errors."""
    pass


class MFASetupException(MFAException):
    """Exception raised during MFA setup."""
    pass


class MFAVerificationException(MFAException):
    """Exception raised during MFA verification."""
    pass


class MFAService:
    """
    Service for managing multi-factor authentication.
    
    This service provides methods for setting up and verifying different types
    of multi-factor authentication, enhancing security for sensitive operations.
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        issuer_name: Optional[str] = None,
        totp_digits: int = 6,
        totp_interval: int = 30,
        sms_code_length: int = 6,
        email_code_length: int = 8,
        verification_timeout_seconds: int = 300  # 5 minutes
    ):
        """
        Initialize the MFA service.
        
        Args:
            secret_key: Secret key for HMAC operations
            issuer_name: Name of the issuer for TOTP
            totp_digits: Number of digits in TOTP codes
            totp_interval: Interval in seconds for TOTP codes
            sms_code_length: Length of SMS verification codes
            email_code_length: Length of email verification codes
            verification_timeout_seconds: Timeout for verification codes
        """
        self.secret_key = secret_key or settings.security.MFA_SECRET_KEY
        self.issuer_name = issuer_name or settings.security.MFA_ISSUER_NAME
        self.totp_digits = totp_digits
        self.totp_interval = totp_interval
        self.sms_code_length = sms_code_length
        self.email_code_length = email_code_length
        self.verification_timeout_seconds = verification_timeout_seconds
    
    def generate_secret_key(self) -> str:
        """
        Generate a new random secret key for MFA.
        
        Returns:
            Base32-encoded secret key
        """
        return pyotp.random_base32()
    
    def setup_totp(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """
        Set up TOTP-based MFA for a user.
        
        Args:
            user_id: User identifier
            user_email: User email address
            
        Returns:
            Dictionary with setup information including secret key and QR code
            
        Raises:
            MFASetupException: If setup fails
        """
        try:
            # Generate a secret key
            secret_key = self.generate_secret_key()
            
            # Create a TOTP object
            totp = pyotp.TOTP(
                secret_key,
                digits=self.totp_digits,
                interval=self.totp_interval
            )
            
            # Generate the provisioning URI for QR code
            provisioning_uri = totp.provisioning_uri(
                name=user_email,
                issuer_name=self.issuer_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert image to bytes
            buffer = BytesIO()
            img.save(buffer)
            qr_code_bytes = buffer.getvalue()
            qr_code_base64 = base64.b64encode(qr_code_bytes).decode()
            
            # Return setup information
            return {
                "secret_key": secret_key,
                "qr_code_base64": qr_code_base64,
                "provisioning_uri": provisioning_uri,
                "mfa_type": MFAType.TOTP.value
            }
            
        except Exception as e:
            logger.error(f"Error setting up TOTP for user: {str(e)}")
            raise MFASetupException(f"Failed to set up TOTP: {str(e)}")
    
    def verify_totp(self, secret_key: str, code: str) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            secret_key: User's TOTP secret key
            code: TOTP code to verify
            
        Returns:
            True if code is valid, False otherwise
            
        Raises:
            MFAVerificationException: If verification fails
        """
        try:
            # Create a TOTP object
            totp = pyotp.TOTP(
                secret_key,
                digits=self.totp_digits,
                interval=self.totp_interval
            )
            
            # Verify the code
            return totp.verify(code)
            
        except Exception as e:
            logger.error(f"Error verifying TOTP code: {str(e)}")
            raise MFAVerificationException(f"Failed to verify TOTP code: {str(e)}")
    
    def generate_verification_code(self, length: int) -> str:
        """
        Generate a random verification code.
        
        Args:
            length: Length of the code
            
        Returns:
            Random verification code
        """
        # Generate a random code of specified length
        import random
        digits = "0123456789"
        return "".join(random.choice(digits) for _ in range(length))
    
    def setup_sms_mfa(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """
        Set up SMS-based MFA for a user.
        
        Args:
            user_id: User identifier
            phone_number: User's phone number
            
        Returns:
            Dictionary with setup information
            
        Raises:
            MFASetupException: If setup fails
        """
        try:
            # Generate a verification code
            verification_code = self.generate_verification_code(self.sms_code_length)
            
            # In a real implementation, this would send the code via SMS
            # For now, we'll just return the code for testing
            
            return {
                "phone_number": phone_number,
                "verification_code": verification_code,  # In production, don't return this
                "expires_at": int(time.time()) + self.verification_timeout_seconds,
                "mfa_type": MFAType.SMS.value
            }
            
        except Exception as e:
            logger.error(f"Error setting up SMS MFA for user: {str(e)}")
            raise MFASetupException(f"Failed to set up SMS MFA: {str(e)}")
    
    def setup_email_mfa(self, user_id: str, email: str) -> Dict[str, Any]:
        """
        Set up email-based MFA for a user.
        
        Args:
            user_id: User identifier
            email: User's email address
            
        Returns:
            Dictionary with setup information
            
        Raises:
            MFASetupException: If setup fails
        """
        try:
            # Generate a verification code
            verification_code = self.generate_verification_code(self.email_code_length)
            
            # In a real implementation, this would send the code via email
            # For now, we'll just return the code for testing
            
            return {
                "email": email,
                "verification_code": verification_code,  # In production, don't return this
                "expires_at": int(time.time()) + self.verification_timeout_seconds,
                "mfa_type": MFAType.EMAIL.value
            }
            
        except Exception as e:
            logger.error(f"Error setting up email MFA for user: {str(e)}")
            raise MFASetupException(f"Failed to set up email MFA: {str(e)}")
    
    def verify_code(self, code: str, expected_code: str, expires_at: int) -> bool:
        """
        Verify a verification code.
        
        Args:
            code: Code to verify
            expected_code: Expected code
            expires_at: Expiration timestamp
            
        Returns:
            True if code is valid and not expired, False otherwise
        """
        # Check if code has expired
        if int(time.time()) > expires_at:
            return False
        
        # Check if code matches
        return code == expected_code
    
    def get_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for MFA recovery.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate a unique code
            code = str(uuid.uuid4()).replace("-", "")[:10].upper()
            codes.append(code)
        
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage.
        
        Args:
            code: Backup code to hash
            
        Returns:
            Hashed backup code
        """
        # Create an HMAC with the secret key
        h = hmac.new(
            self.secret_key.encode(),
            code.encode(),
            digestmod="sha256"
        )
        
        # Return the hex digest
        return h.hexdigest()
    
    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> bool:
        """
        Verify a backup code.
        
        Args:
            code: Backup code to verify
            hashed_codes: List of hashed backup codes
            
        Returns:
            True if code is valid, False otherwise
        """
        # Hash the provided code
        hashed_code = self.hash_backup_code(code)
        
        # Check if the hashed code is in the list
        return hashed_code in hashed_codes


class MFAStrategyFactory:
    """
    Factory for creating MFA strategy objects.
    
    This factory creates the appropriate MFA strategy based on the MFA type,
    following the Strategy pattern.
    """
    
    @staticmethod
    def create_strategy(mfa_type: MFAType, mfa_service: MFAService) -> 'MFAStrategy':
        """
        Create an MFA strategy based on the MFA type.
        
        Args:
            mfa_type: Type of MFA
            mfa_service: MFA service instance
            
        Returns:
            MFA strategy instance
            
        Raises:
            ValueError: If MFA type is not supported
        """
        if mfa_type == MFAType.TOTP:
            return TOTPStrategy(mfa_service)
        elif mfa_type == MFAType.SMS:
            return SMSStrategy(mfa_service)
        elif mfa_type == MFAType.EMAIL:
            return EmailStrategy(mfa_service)
        else:
            raise ValueError(f"Unsupported MFA type: {mfa_type}")


class MFAStrategy:
    """Base class for MFA strategies."""
    
    def __init__(self, mfa_service: MFAService):
        """
        Initialize the MFA strategy.
        
        Args:
            mfa_service: MFA service instance
        """
        self.mfa_service = mfa_service
    
    def setup(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Set up MFA for a user.
        
        Args:
            user_id: User identifier
            **kwargs: Additional setup parameters
            
        Returns:
            Setup information
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement setup method")
    
    def verify(self, **kwargs) -> bool:
        """
        Verify MFA.
        
        Args:
            **kwargs: Verification parameters
            
        Returns:
            True if verification succeeds, False otherwise
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement verify method")


class TOTPStrategy(MFAStrategy):
    """Strategy for TOTP-based MFA."""
    
    def setup(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Set up TOTP-based MFA for a user.
        
        Args:
            user_id: User identifier
            **kwargs: Additional setup parameters
            
        Returns:
            Setup information
        """
        user_email = kwargs.get("email")
        if not user_email:
            raise MFASetupException("Email is required for TOTP setup")
        
        return self.mfa_service.setup_totp(user_id, user_email)
    
    def verify(self, **kwargs) -> bool:
        """
        Verify TOTP code.
        
        Args:
            **kwargs: Verification parameters
            
        Returns:
            True if verification succeeds, False otherwise
        """
        secret_key = kwargs.get("secret_key")
        code = kwargs.get("code")
        
        if not secret_key or not code:
            raise MFAVerificationException("Secret key and code are required for TOTP verification")
        
        return self.mfa_service.verify_totp(secret_key, code)


class SMSStrategy(MFAStrategy):
    """Strategy for SMS-based MFA."""
    
    def setup(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Set up SMS-based MFA for a user.
        
        Args:
            user_id: User identifier
            **kwargs: Additional setup parameters
            
        Returns:
            Setup information
        """
        phone_number = kwargs.get("phone_number")
        if not phone_number:
            raise MFASetupException("Phone number is required for SMS MFA setup")
        
        return self.mfa_service.setup_sms_mfa(user_id, phone_number)
    
    def verify(self, **kwargs) -> bool:
        """
        Verify SMS code.
        
        Args:
            **kwargs: Verification parameters
            
        Returns:
            True if verification succeeds, False otherwise
        """
        code = kwargs.get("code")
        expected_code = kwargs.get("expected_code")
        expires_at = kwargs.get("expires_at")
        
        if not code or not expected_code or not expires_at:
            raise MFAVerificationException("Code, expected code, and expiration are required for SMS verification")
        
        return self.mfa_service.verify_code(code, expected_code, expires_at)


class EmailStrategy(MFAStrategy):
    """Strategy for email-based MFA."""
    
    def setup(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Set up email-based MFA for a user.
        
        Args:
            user_id: User identifier
            **kwargs: Additional setup parameters
            
        Returns:
            Setup information
        """
        email = kwargs.get("email")
        if not email:
            raise MFASetupException("Email is required for email MFA setup")
        
        return self.mfa_service.setup_email_mfa(user_id, email)
    
    def verify(self, **kwargs) -> bool:
        """
        Verify email code.
        
        Args:
            **kwargs: Verification parameters
            
        Returns:
            True if verification succeeds, False otherwise
        """
        code = kwargs.get("code")
        expected_code = kwargs.get("expected_code")
        expires_at = kwargs.get("expires_at")
        
        if not code or not expected_code or not expires_at:
            raise MFAVerificationException("Code, expected code, and expiration are required for email verification")
        
        return self.mfa_service.verify_code(code, expected_code, expires_at)