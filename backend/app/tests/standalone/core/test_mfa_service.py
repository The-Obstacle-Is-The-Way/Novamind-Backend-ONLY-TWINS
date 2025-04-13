"""
Tests for the MFA service.
"""

import time
import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.infrastructure.security.mfa_service import ()
MFAService,
MFAType,
MFAException,
MFASetupException,
MFAVerificationException,
MFAStrategyFactory,
TOTPStrategy,
SMSStrategy,
EmailStrategy



@pytest.fixture
def mfa_service():
    """Fixture for MFA service."""
    with patch('app.core.config.settings') as mock_settings:
        # Mock the settings
        mock_settings.security.MFA_SECRET_KEY = "test_secret_key"
        mock_settings.security.MFA_ISSUER_NAME = "Novamind Psychiatry"

        # Create the service
        service = MFAService()
        secret_key="test_secret_key",
        issuer_name="Novamind Psychiatry",
        totp_digits=6,
        totp_interval=30,
        sms_code_length=6,
        email_code_length=8,
        verification_timeout_seconds=300
        
#         return service


class TestMFAService:
    """Tests for the MFAService class."""

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
    assert code == "000000"  # All zeros due to our mock

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
    # First 10 chars of UUID hex, uppercase
    assert all(code == "ABCDEF1234" for code in codes)

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

    @pytest.fixture
    def totp_strategy(self, mfa_service):
        """Fixture for TOTP strategy."""
        return TOTPStrategy(mfa_service)

    @patch.object(MFAService, 'setup_totp')
    @pytest.mark.standalone()
        def test_setup(self, mock_setup_totp, totp_strategy):
    """Test setting up TOTP."""
    # Mock the setup_totp method
    mock_setup_totp.return_value = {
    "secret_key": "ABCDEFGH",
    "qr_code_base64": "base64_encoded_qr_code",
    "provisioning_uri": "otpauth://totp/Novamind%20Psychiatry:test%40example.com?secret=ABCDEFGH&issuer=Novamind%20Psychiatry",
    "mfa_type": MFAType.TOTP.value
    }

    # Set up TOTP
    result = totp_strategy.setup("user123", {"email": "test@example.com"})

    # Check the result
    assert result == mock_setup_totp.return_value
    mock_setup_totp.assert_called_once_with("user123", "test@example.com")

    @pytest.mark.standalone()
        def test_setup_missing_email(self, totp_strategy):
    """Test setting up TOTP without an email."""
    # Set up TOTP without an email
        with pytest.raises(MFASetupException):
            totp_strategy.setup("user123", {})

    @patch.object(MFAService, 'verify_totp')
    @pytest.mark.standalone()
            def test_verify(self, mock_verify_totp, totp_strategy):
    """Test verifying TOTP."""
    # Mock the verify_totp method
    mock_verify_totp.return_value = True

    # Verify TOTP
    result = totp_strategy.verify({)
    "secret_key": "ABCDEFGH",
    "code": "123456"
    }

    # Check the result
    assert result is True
    mock_verify_totp.assert_called_once_with("ABCDEFGH", "123456")

    @pytest.mark.standalone()
        def test_verify_missing_parameters(self, totp_strategy):
    """Test verifying TOTP without required parameters."""
    # Verify TOTP without secret_key
        with pytest.raises(MFAVerificationException):
            totp_strategy.verify({"code": "123456"})

    # Verify TOTP without code
        with pytest.raises(MFAVerificationException):
            totp_strategy.verify({"secret_key": "ABCDEFGH"})


class TestSMSStrategy:
    """Tests for the SMSStrategy class."""

    @pytest.fixture
    def sms_strategy(self, mfa_service):
        """Fixture for SMS strategy."""
        return SMSStrategy(mfa_service)

    @patch.object(MFAService, 'setup_sms_mfa')
    @pytest.mark.standalone()
        def test_setup(self, mock_setup_sms, sms_strategy):
    """Test setting up SMS MFA."""
    # Mock the setup_sms_mfa method
    mock_setup_sms.return_value = {
    "phone_number": "+1234567890",
    "verification_code": "123456",
    "expires_at": 1300,
    "mfa_type": MFAType.SMS.value
    }

    # Set up SMS MFA
    result = sms_strategy.setup("user123", {"phone_number": "+1234567890"})

    # Check the result
    assert result == mock_setup_sms.return_value
    mock_setup_sms.assert_called_once_with("user123", "+1234567890")

    @pytest.mark.standalone()
        def test_setup_missing_phone_number(self, sms_strategy):
    """Test setting up SMS MFA without a phone number."""
    # Set up SMS MFA without a phone number
        with pytest.raises(MFASetupException):
            sms_strategy.setup("user123", {})

    @patch.object(MFAService, 'verify_code')
    @pytest.mark.standalone()
            def test_verify(self, mock_verify_code, sms_strategy):
    """Test verifying SMS code."""
    # Mock the verify_code method
    mock_verify_code.return_value = True

    # Verify SMS code
    result = sms_strategy.verify({)
    "code": "123456",
    "expected_code": "123456",
    "expires_at": 1300
    }

    # Check the result
    assert result is True
    mock_verify_code.assert_called_once_with("123456", "123456", 1300)

    @pytest.mark.standalone()
        def test_verify_missing_parameters(self, sms_strategy):
    """Test verifying SMS code without required parameters."""
    # Verify SMS code without code
        with pytest.raises(MFAVerificationException):
            sms_strategy.verify({)
            "expected_code": "123456",
            "expires_at": 1300
            }

    # Verify SMS code without expected_code
        with pytest.raises(MFAVerificationException):
            sms_strategy.verify({)
            "code": "123456",
            "expires_at": 1300
            }

    # Verify SMS code without expires_at
        with pytest.raises(MFAVerificationException):
            sms_strategy.verify({)
            "code": "123456",
            "expected_code": "123456"
            }


class TestEmailStrategy:
    """Tests for the EmailStrategy class."""

    @pytest.fixture
    def email_strategy(self, mfa_service):
        """Fixture for Email strategy."""
        return EmailStrategy(mfa_service)

    @patch.object(MFAService, 'setup_email_mfa')
    @pytest.mark.standalone()
        def test_setup(self, mock_setup_email, email_strategy):
    """Test setting up email MFA."""
    # Mock the setup_email_mfa method
    mock_setup_email.return_value = {
    "email": "test@example.com",
    "verification_code": "12345678",
    "expires_at": 1300,
    "mfa_type": MFAType.EMAIL.value
    }

    # Set up email MFA
    result = email_strategy.setup("user123", {"email": "test@example.com"})

    # Check the result
    assert result == mock_setup_email.return_value
    mock_setup_email.assert_called_once_with("user123", "test@example.com")

    @pytest.mark.standalone()
        def test_setup_missing_email(self, email_strategy):
    """Test setting up email MFA without an email."""
    # Set up email MFA without an email
        with pytest.raises(MFASetupException):
            email_strategy.setup("user123", {})

    @patch.object(MFAService, 'verify_code')
    @pytest.mark.standalone()
            def test_verify(self, mock_verify_code, email_strategy):
    """Test verifying email code."""
    # Mock the verify_code method
    mock_verify_code.return_value = True

    # Verify email code
    result = email_strategy.verify({)
    "code": "12345678",
    "expected_code": "12345678",
    "expires_at": 1300
    }

    # Check the result
    assert result is True
    mock_verify_code.assert_called_once_with("12345678", "12345678", 1300)

    @pytest.mark.standalone()
        def test_verify_missing_parameters(self, email_strategy):
    """Test verifying email code without required parameters."""
    # Verify email code without code
        with pytest.raises(MFAVerificationException):
            email_strategy.verify({)
            "expected_code": "12345678",
            "expires_at": 1300
            }

    # Verify email code without expected_code
        with pytest.raises(MFAVerificationException):
            email_strategy.verify({)
            "code": "12345678",
            "expires_at": 1300
            }

    # Verify email code without expires_at
        with pytest.raises(MFAVerificationException):
            email_strategy.verify({)
            "code": "12345678",
            "expected_code": "12345678"
            }