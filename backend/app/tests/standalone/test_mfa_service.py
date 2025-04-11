"""
Tests for the MFA service.
"""

import time
import pytest
from unittest.mock import MagicMock, patch

from app.infrastructure.security.mfa_service import (
    MFAService,  
    MFAType,  
    MFAException,  
    MFASetupException,  
    MFAVerificationException,  
    MFAStrategyFactory,  
    TOTPStrategy,  
    SMSStrategy,  
    EmailStrategy
)


@pytest.fixture
def mfa_service():
    """Fixture for MFA service."""
    with patch('app.core.config.settings') as mock_settings:
        # Mock the settings
        mock_settings.security.MFA_SECRET_KEY = "test_secret_key"
        mock_settings.security.MFA_ISSUER_NAME = "Novamind Psychiatry"
        
        # Create the service
        service = MFAService(
            secret_key="test_secret_key",
            issuer_name="Novamind Psychiatry",
            totp_digits=6,
            totp_interval=30,
            sms_code_length=6,
            email_code_length=8,
            verification_timeout_seconds=300
        )
        
        return service


class TestMFAService:
    """Tests for the MFAService class."""
    
    # Corrected indentation for this method and all subsequent methods/decorators
    @pytest.mark.standalone()
    def test_generate_secret_key(self, mfa_service):
        """Test generating a secret key."""
        secret_key = mfa_service.generate_secret_key()
        
        # Secret key should be a string
        assert isinstance(secret_key, str)
        
        # Secret key should be non-empty
        assert len(secret_key) > 0
    
    @patch('pyotp.TOTP')
    @patch('qrcode.QRCode')
    @pytest.mark.standalone()
    def test_setup_totp(self, mock_qrcode, mock_totp, mfa_service):
        """Test setting up TOTP."""
        # Mock the TOTP object
        mock_totp_instance = mock_totp.return_value
        mock_totp_instance.provisioning_uri.return_value = "otpauth://totp/Novamind%20Psychiatry:test%40example.com?secret=ABCDEFGH&issuer=Novamind%20Psychiatry"
        
        # Mock the QR code
        mock_qrcode_instance = mock_qrcode.return_value
        mock_qrcode_instance.make_image.return_value.save.side_effect = lambda buffer: buffer.write(b"fake_qr_code")
        
        # Mock the secret key generation
        with patch.object(mfa_service, 'generate_secret_key', return_value="ABCDEFGH"):
            # Set up TOTP
            result = mfa_service.setup_totp("user123", "test@example.com")
            
            # Check the result
            assert result["secret_key"] == "ABCDEFGH"
            assert "qr_code_base64" in result
            assert "provisioning_uri" in result
            assert result["mfa_type"] == MFAType.TOTP.value
    
    @patch('pyotp.TOTP')
    @pytest.mark.standalone()
    def test_verify_totp_valid(self, mock_totp, mfa_service):
        """Test verifying a valid TOTP code."""
        # Mock the TOTP object
        mock_totp_instance = mock_totp.return_value
        mock_totp_instance.verify.return_value = True
        
        # Verify the code
        result = mfa_service.verify_totp("ABCDEFGH", "123456")
        
        # Check the result
        assert result is True
        mock_totp_instance.verify.assert_called_once_with("123456")
    
    @patch('pyotp.TOTP')
    @pytest.mark.standalone()
    def test_verify_totp_invalid(self, mock_totp, mfa_service):
        """Test verifying an invalid TOTP code."""
        # Mock the TOTP object
        mock_totp_instance = mock_totp.return_value
        mock_totp_instance.verify.return_value = False
        
        # Verify the code
        result = mfa_service.verify_totp("ABCDEFGH", "123456")
        
        # Check the result
        assert result is False
        mock_totp_instance.verify.assert_called_once_with("123456")
    
    @patch('random.choice')
    @pytest.mark.standalone()
    def test_generate_verification_code(self, mock_choice, mfa_service):
        """Test generating a verification code."""
        # Mock the random choice
        mock_choice.side_effect = lambda digits: digits[0]
        
        # Generate a code
        code = mfa_service.generate_verification_code(6)
        
        # Check the code
        assert len(code) == 6
        assert code  ==  "000000"  # All zeros due to our mock
    
    @patch('time.time')
    @pytest.mark.standalone()
    def test_setup_sms_mfa(self, mock_time, mfa_service):
        """Test setting up SMS MFA."""
        # Mock the time
        mock_time.return_value = 1000
        
        # Mock the verification code generation
        with patch.object(mfa_service, 'generate_verification_code', return_value="123456"):
            # Set up SMS MFA
            result = mfa_service.setup_sms_mfa("user123", "+1234567890")
            
            # Check the result
            assert result["phone_number"] == "+1234567890"
            assert result["verification_code"] == "123456"
            assert result["expires_at"] == 1300  # 1000 + 300
            assert result["mfa_type"] == MFAType.SMS.value
    
    @patch('time.time')
    @pytest.mark.standalone()
    def test_setup_email_mfa(self, mock_time, mfa_service):
        """Test setting up email MFA."""
        # Mock the time
        mock_time.return_value = 1000
        
        # Mock the verification code generation
        with patch.object(mfa_service, 'generate_verification_code', return_value="12345678"):
            # Set up email MFA
            result = mfa_service.setup_email_mfa("user123", "test@example.com")
            
            # Check the result
            assert result["email"] == "test@example.com"
            assert result["verification_code"] == "12345678"
            assert result["expires_at"] == 1300  # 1000 + 300
            assert result["mfa_type"] == MFAType.EMAIL.value
    
    @patch('time.time')
    @pytest.mark.standalone()
    def test_verify_code_valid(self, mock_time, mfa_service):
        """Test verifying a valid code."""
        # Mock the time
        mock_time.return_value = 1000
        
        # Verify the code
        result = mfa_service.verify_code("123456", "123456", 1300)
        
        # Check the result
        assert result is True
    
    @patch('time.time')
    @pytest.mark.standalone()
    def test_verify_code_expired(self, mock_time, mfa_service):
        """Test verifying an expired code."""
        # Mock the time
        mock_time.return_value = 1500
        
        # Verify the code
        result = mfa_service.verify_code("123456", "123456", 1300)
        
        # Check the result
        assert result is False
    
    @patch('time.time')
    @pytest.mark.standalone()
    def test_verify_code_invalid(self, mock_time, mfa_service):
        """Test verifying an invalid code."""
        # Mock the time
        mock_time.return_value = 1000
        
        # Verify the code
        result = mfa_service.verify_code("123456", "654321", 1300)
        
        # Check the result
        assert result is False
    
    @patch('uuid.uuid4')
    @pytest.mark.standalone()
    def test_get_backup_codes(self, mock_uuid, mfa_service):
        """Test generating backup codes."""
        # Create a mock UUID object that returns a specific string representation
        mock_uuid_instance = MagicMock()
        mock_uuid_instance.__str__.return_value = "abcdef12-3456-7890-abcd-ef1234567890"
        mock_uuid.return_value = mock_uuid_instance
        
        # Generate backup codes
        codes = mfa_service.get_backup_codes(3)
        
        # Check the codes
        assert len(codes) == 3
        assert all(len(code) == 10 for code in codes)
        assert all(code == "ABCDEF1234" for code in codes)  # First 10 chars of UUID hex, uppercase
    
    @pytest.mark.standalone()
    def test_hash_backup_code(self, mfa_service):
        """Test hashing a backup code."""
        # Hash a code
        hashed_code = mfa_service.hash_backup_code("ABCDEF1234")
        
        # Check the hashed code
        assert isinstance(hashed_code, str)
        assert len(hashed_code) > 0
    
    @pytest.mark.standalone()
    def test_verify_backup_code_valid(self, mfa_service):
        """Test verifying a valid backup code."""
        # Hash a code
        hashed_code = mfa_service.hash_backup_code("ABCDEF1234")
        
        # Verify the code
        result = mfa_service.verify_backup_code("ABCDEF1234", [hashed_code])
        
        # Check the result
        assert result is True
    
    @pytest.mark.standalone()
    def test_verify_backup_code_invalid(self, mfa_service):
        """Test verifying an invalid backup code."""
        # Hash a code
        hashed_code = mfa_service.hash_backup_code("ABCDEF1234")
        
        # Verify a different code
        result = mfa_service.verify_backup_code("ZYXWVU9876", [hashed_code])
        
        # Check the result
        assert result is False


class TestMFAStrategyFactory:
    """Tests for the MFAStrategyFactory class."""
    
    @pytest.mark.standalone()
    def test_create_totp_strategy(self, mfa_service):
        """Test creating a TOTP strategy."""
        strategy = MFAStrategyFactory.create_strategy(MFAType.TOTP, mfa_service)
        assert isinstance(strategy, TOTPStrategy)
    
    @pytest.mark.standalone()
    def test_create_sms_strategy(self, mfa_service):
        """Test creating an SMS strategy."""
        strategy = MFAStrategyFactory.create_strategy(MFAType.SMS, mfa_service)
        assert isinstance(strategy, SMSStrategy)
    
    @pytest.mark.standalone()
    def test_create_email_strategy(self, mfa_service):
        """Test creating an email strategy."""
        strategy = MFAStrategyFactory.create_strategy(MFAType.EMAIL, mfa_service)
        assert isinstance(strategy, EmailStrategy)
    
    @pytest.mark.standalone()
    def test_create_invalid_strategy(self, mfa_service):
        """Test creating an invalid strategy."""
        with pytest.raises(ValueError):
            MFAStrategyFactory.create_strategy("invalid", mfa_service)


class TestTOTPStrategy:
    """Tests for the TOTPStrategy class."""
    
    @pytest.mark.standalone()
    def test_setup(self, mfa_service):
        """Test setting up TOTP."""
        # Create the strategy
        strategy = TOTPStrategy(mfa_service)
        
        # Mock the setup_totp method
        with patch.object(mfa_service, 'setup_totp', return_value={"result": "success"}):
            # Set up TOTP
            result = strategy.setup("user123", email="test@example.com")
            
            # Check the result
            assert result  ==  {"result": "success"}
            mfa_service.setup_totp.assert_called_once_with("user123", "test@example.com")
    
    @pytest.mark.standalone()
    def test_setup_missing_email(self, mfa_service):
        """Test setting up TOTP without an email."""
        # Create the strategy
        strategy = TOTPStrategy(mfa_service)
        
        # Set up TOTP without an email
        with pytest.raises(MFASetupException):
            strategy.setup("user123")
    
    @pytest.mark.standalone()
    def test_verify(self, mfa_service):
        """Test verifying TOTP."""
        # Create the strategy
        strategy = TOTPStrategy(mfa_service)
        
        # Mock the verify_totp method
        with patch.object(mfa_service, 'verify_totp', return_value=True):
            # Verify TOTP
            result = strategy.verify(secret_key="ABCDEFGH", code="123456")
            
            # Check the result
            assert result is True
            mfa_service.verify_totp.assert_called_once_with("ABCDEFGH", "123456")
    
    @pytest.mark.standalone()
    def test_verify_missing_parameters(self, mfa_service):
        """Test verifying TOTP without required parameters."""
        # Create the strategy
        strategy = TOTPStrategy(mfa_service)
        
        # Verify TOTP without parameters
        with pytest.raises(MFAVerificationException):
            strategy.verify()


class TestSMSStrategy:
    """Tests for the SMSStrategy class."""
    
    @pytest.mark.standalone()
    def test_setup(self, mfa_service):
        """Test setting up SMS MFA."""
        # Create the strategy
        strategy = SMSStrategy(mfa_service)
        
        # Mock the setup_sms_mfa method
        with patch.object(mfa_service, 'setup_sms_mfa', return_value={"result": "success"}):
            # Set up SMS MFA
            result = strategy.setup("user123", phone_number="+1234567890")
            
            # Check the result
            assert result  ==  {"result": "success"}
            mfa_service.setup_sms_mfa.assert_called_once_with("user123", "+1234567890")
    
    @pytest.mark.standalone()
    def test_setup_missing_phone_number(self, mfa_service):
        """Test setting up SMS MFA without a phone number."""
        # Create the strategy
        strategy = SMSStrategy(mfa_service)
        
        # Set up SMS MFA without a phone number
        with pytest.raises(MFASetupException):
            strategy.setup("user123")
    
    @pytest.mark.standalone()
    def test_verify(self, mfa_service):
        """Test verifying SMS code."""
        # Create the strategy
        strategy = SMSStrategy(mfa_service)
        
        # Mock the verify_code method
        with patch.object(mfa_service, 'verify_code', return_value=True):
            # Verify SMS code
            result = strategy.verify(
                code="123456",
                expected_code="123456",
                expires_at=1300
            )
            
            # Check the result
            assert result is True
            mfa_service.verify_code.assert_called_once_with("123456", "123456", 1300)
    
    @pytest.mark.standalone()
    def test_verify_missing_parameters(self, mfa_service):
        """Test verifying SMS code without required parameters."""
        # Create the strategy
        strategy = SMSStrategy(mfa_service)
        
        # Verify SMS code without parameters
        with pytest.raises(MFAVerificationException):
            strategy.verify()


class TestEmailStrategy:
    """Tests for the EmailStrategy class."""
    
    @pytest.mark.standalone()
    def test_setup(self, mfa_service):
        """Test setting up email MFA."""
        # Create the strategy
        strategy = EmailStrategy(mfa_service)
        
        # Mock the setup_email_mfa method
        with patch.object(mfa_service, 'setup_email_mfa', return_value={"result": "success"}):
            # Set up email MFA
            result = strategy.setup("user123", email="test@example.com")
            
            # Check the result
            assert result  ==  {"result": "success"}
            mfa_service.setup_email_mfa.assert_called_once_with("user123", "test@example.com")
    
    @pytest.mark.standalone()
    def test_setup_missing_email(self, mfa_service):
        """Test setting up email MFA without an email."""
        # Create the strategy
        strategy = EmailStrategy(mfa_service)
        
        # Set up email MFA without an email
        with pytest.raises(MFASetupException):
            strategy.setup("user123")
    
    @pytest.mark.standalone()
    def test_verify(self, mfa_service):
        """Test verifying email code."""
        # Create the strategy
        strategy = EmailStrategy(mfa_service)
        
        # Mock the verify_code method
        with patch.object(mfa_service, 'verify_code', return_value=True):
            # Verify email code
            result = strategy.verify(
                code="12345678",
                expected_code="12345678",
                expires_at=1300
            )
            
            # Check the result
            assert result is True
            mfa_service.verify_code.assert_called_once_with("12345678", "12345678", 1300)
    
    @pytest.mark.standalone()
    def test_verify_missing_parameters(self, mfa_service):
        """Test verifying email code without required parameters."""
        # Create the strategy
        strategy = EmailStrategy(mfa_service)
        
        # Verify email code without parameters
        with pytest.raises(MFAVerificationException):
            strategy.verify()