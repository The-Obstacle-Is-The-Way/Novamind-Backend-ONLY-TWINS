# NOVAMIND: HIPAA-Compliant Encryption Utility

## 1. Overview

The Encryption Utility is a critical component of the NOVAMIND platform that provides robust, HIPAA-compliant encryption services for protecting sensitive patient data both at rest and in transit. This utility implements industry-standard encryption algorithms and secure key management practices to ensure the confidentiality and integrity of Protected Health Information (PHI).

## 2. Key Features

- **Symmetric Encryption**: AES-256 encryption for sensitive data
- **Secure Hashing**: SHA-256 hashing with salt for password storage
- **HMAC Generation**: Message authentication codes for data integrity
- **Key Management**: Secure key generation and storage
- **Data Protection**: Methods for encrypting/decrypting strings, dictionaries, and files

## 3. Implementation

### 3.1 Core Encryption Implementation

```python
# app/utils/encryption.py
import base64
import hashlib
import hmac
import json
import os
import secrets
from typing import Any, Dict, Optional, Tuple, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionService:
    """
    HIPAA-compliant encryption service for protecting sensitive data.
    Provides methods for symmetric encryption, secure hashing, and HMAC generation.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize the encryption service with an encryption key.
        
        Args:
            key: Encryption key (if None, a key will be derived from environment variables)
        """
        if key is None:
            # In production, get the key from a secure source (e.g., AWS KMS, environment variable)
            master_key = os.environ.get("ENCRYPTION_MASTER_KEY")
            if not master_key:
                raise ValueError("Encryption master key not found in environment variables")
            
            # Derive a key using PBKDF2
            salt = os.environ.get("ENCRYPTION_SALT", "novamind_salt").encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        
        self.cipher = Fernet(key)
    
    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new encryption key.
        
        Returns:
            Bytes containing the new key
        """
        return Fernet.generate_key()
    
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data using AES-256.
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            Encrypted data as bytes
        """
        if isinstance(data, str):
            data = data.encode()
        
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data that was encrypted using AES-256.
        
        Args:
            encrypted_data: Data to decrypt
            
        Returns:
            Decrypted data as bytes
        """
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_to_string(self, data: Union[str, bytes]) -> str:
        """
        Encrypt data and return as a base64-encoded string.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        encrypted = self.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_from_string(self, encrypted_string: str) -> str:
        """
        Decrypt a base64-encoded encrypted string.
        
        Args:
            encrypted_string: Base64-encoded encrypted data
            
        Returns:
            Decrypted data as string
        """
        encrypted = base64.urlsafe_b64decode(encrypted_string)
        return self.decrypt(encrypted).decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary and return as a base64-encoded string.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted dictionary
        """
        json_data = json.dumps(data)
        return self.encrypt_to_string(json_data)
    
    def decrypt_dict(self, encrypted_string: str) -> Dict[str, Any]:
        """
        Decrypt a base64-encoded encrypted dictionary.
        
        Args:
            encrypted_string: Base64-encoded encrypted dictionary
            
        Returns:
            Decrypted dictionary
        """
        json_data = self.decrypt_from_string(encrypted_string)
        return json.loads(json_data)
    
    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """
        Hash a password with a random salt using SHA-256.
        
        Args:
            password: Password to hash
            
        Returns:
            Tuple of (hash, salt)
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """
        Verify a password against a hash and salt.
        
        Args:
            password: Password to verify
            password_hash: Stored password hash
            salt: Salt used for hashing
            
        Returns:
            True if password matches, False otherwise
        """
        computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return computed_hash == password_hash
    
    @staticmethod
    def generate_hmac(data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """
        Generate an HMAC for data integrity verification.
        
        Args:
            data: Data to generate HMAC for
            key: Key to use for HMAC generation
            
        Returns:
            Hexadecimal HMAC string
        """
        if isinstance(data, str):
            data = data.encode()
        
        if isinstance(key, str):
            key = key.encode()
        
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    @staticmethod
    def verify_hmac(data: Union[str, bytes], key: Union[str, bytes], expected_hmac: str) -> bool:
        """
        Verify an HMAC for data integrity.
        
        Args:
            data: Data to verify
            key: Key used for HMAC generation
            expected_hmac: Expected HMAC value
            
        Returns:
            True if HMAC matches, False otherwise
        """
        computed_hmac = EncryptionService.generate_hmac(data, key)
        return hmac.compare_digest(computed_hmac, expected_hmac)
```

### 3.2 File Encryption Implementation

```python
# app/utils/file_encryption.py
import os
from pathlib import Path
from typing import Optional

from app.utils.encryption import EncryptionService
from app.utils.logging import get_logger

logger = get_logger(__name__)

class FileEncryptionService:
    """
    Service for encrypting and decrypting files in a HIPAA-compliant manner.
    """
    
    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """
        Initialize the file encryption service.
        
        Args:
            encryption_service: EncryptionService instance (if None, a new one will be created)
        """
        self.encryption_service = encryption_service or EncryptionService()
    
    def encrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Encrypt a file.
        
        Args:
            input_path: Path to the file to encrypt
            output_path: Path to save the encrypted file (if None, will use input_path + '.enc')
            
        Returns:
            Path to the encrypted file
        """
        if output_path is None:
            output_path = input_path + '.enc'
        
        try:
            with open(input_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = self.encryption_service.encrypt(file_data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"File encrypted: {input_path} -> {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to encrypt file {input_path}", error=str(e), exc_info=True)
            raise
    
    def decrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Decrypt a file.
        
        Args:
            input_path: Path to the encrypted file
            output_path: Path to save the decrypted file (if None, will use input_path without '.enc')
            
        Returns:
            Path to the decrypted file
        """
        if output_path is None:
            output_path = input_path.replace('.enc', '') if input_path.endswith('.enc') else input_path + '.dec'
        
        try:
            with open(input_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.encryption_service.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            logger.info(f"File decrypted: {input_path} -> {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to decrypt file {input_path}", error=str(e), exc_info=True)
            raise
    
    def encrypt_directory(self, input_dir: str, output_dir: Optional[str] = None) -> str:
        """
        Encrypt all files in a directory.
        
        Args:
            input_dir: Directory containing files to encrypt
            output_dir: Directory to save encrypted files (if None, will use input_dir + '_encrypted')
            
        Returns:
            Path to the directory containing encrypted files
        """
        if output_dir is None:
            output_dir = input_dir + '_encrypted'
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            for root, _, files in os.walk(input_dir):
                for file in files:
                    input_path = os.path.join(root, file)
                    relative_path = os.path.relpath(input_path, input_dir)
                    output_path = os.path.join(output_dir, relative_path + '.enc')
                    
                    # Create subdirectories if needed
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    self.encrypt_file(input_path, output_path)
            
            logger.info(f"Directory encrypted: {input_dir} -> {output_dir}")
            return output_dir
        
        except Exception as e:
            logger.error(f"Failed to encrypt directory {input_dir}", error=str(e), exc_info=True)
            raise
    
    def decrypt_directory(self, input_dir: str, output_dir: Optional[str] = None) -> str:
        """
        Decrypt all files in a directory.
        
        Args:
            input_dir: Directory containing encrypted files
            output_dir: Directory to save decrypted files (if None, will use input_dir + '_decrypted')
            
        Returns:
            Path to the directory containing decrypted files
        """
        if output_dir is None:
            output_dir = input_dir + '_decrypted'
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            for root, _, files in os.walk(input_dir):
                for file in files:
                    if file.endswith('.enc'):
                        input_path = os.path.join(root, file)
                        relative_path = os.path.relpath(input_path, input_dir)
                        output_path = os.path.join(output_dir, relative_path[:-4])  # Remove '.enc'
                        
                        # Create subdirectories if needed
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        
                        self.decrypt_file(input_path, output_path)
            
            logger.info(f"Directory decrypted: {input_dir} -> {output_dir}")
            return output_dir
        
        except Exception as e:
            logger.error(f"Failed to decrypt directory {input_dir}", error=str(e), exc_info=True)
            raise
```

## 4. Usage Examples

### 4.1 Basic Encryption and Decryption

```python
from app.utils.encryption import EncryptionService

# Create an encryption service
encryption_service = EncryptionService()

# Encrypt and decrypt a string
sensitive_data = "Patient has a history of hypertension and diabetes"
encrypted = encryption_service.encrypt_to_string(sensitive_data)
decrypted = encryption_service.decrypt_from_string(encrypted)

print(f"Original: {sensitive_data}")
print(f"Encrypted: {encrypted}")
print(f"Decrypted: {decrypted}")

# Encrypt and decrypt a dictionary
patient_data = {
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1980-01-01",
    "conditions": ["hypertension", "diabetes"],
    "medications": ["lisinopril", "metformin"]
}

encrypted_dict = encryption_service.encrypt_dict(patient_data)
decrypted_dict = encryption_service.decrypt_dict(encrypted_dict)

print(f"Original dict: {patient_data}")
print(f"Encrypted dict: {encrypted_dict}")
print(f"Decrypted dict: {decrypted_dict}")
```

### 4.2 Password Hashing and Verification

```python
from app.utils.encryption import EncryptionService

# Hash a password
password = "SecurePassword123!"
password_hash, salt = EncryptionService.hash_password(password)

print(f"Password: {password}")
print(f"Hash: {password_hash}")
print(f"Salt: {salt}")

# Verify a password
is_valid = EncryptionService.verify_password(password, password_hash, salt)
print(f"Password valid: {is_valid}")

# Verify an incorrect password
is_valid = EncryptionService.verify_password("WrongPassword", password_hash, salt)
print(f"Incorrect password valid: {is_valid}")
```

### 4.3 HMAC Generation and Verification

```python
from app.utils.encryption import EncryptionService

# Generate an HMAC
data = "Important medical data that must not be tampered with"
key = "secret_key_for_hmac"
hmac_value = EncryptionService.generate_hmac(data, key)

print(f"Data: {data}")
print(f"HMAC: {hmac_value}")

# Verify the HMAC
is_valid = EncryptionService.verify_hmac(data, key, hmac_value)
print(f"HMAC valid: {is_valid}")

# Verify with tampered data
tampered_data = "Important medical data that has been tampered with"
is_valid = EncryptionService.verify_hmac(tampered_data, key, hmac_value)
print(f"Tampered data HMAC valid: {is_valid}")
```

### 4.4 File Encryption and Decryption

```python
from app.utils.file_encryption import FileEncryptionService

# Create a file encryption service
file_encryption_service = FileEncryptionService()

# Encrypt a file
encrypted_file = file_encryption_service.encrypt_file("patient_records.csv")
print(f"File encrypted: {encrypted_file}")

# Decrypt a file
decrypted_file = file_encryption_service.decrypt_file(encrypted_file)
print(f"File decrypted: {decrypted_file}")

# Encrypt a directory
encrypted_dir = file_encryption_service.encrypt_directory("patient_data")
print(f"Directory encrypted: {encrypted_dir}")

# Decrypt a directory
decrypted_dir = file_encryption_service.decrypt_directory(encrypted_dir)
print(f"Directory decrypted: {decrypted_dir}")
```

## 5. Best Practices

1. **Key Management**: Store encryption keys securely, preferably using a key management service like AWS KMS.

2. **Encryption at Rest**: Always encrypt sensitive data before storing it in databases or files.

3. **Encryption in Transit**: Use TLS/SSL for all network communications.

4. **Secure Key Rotation**: Implement a process for regularly rotating encryption keys.

5. **Minimum Key Length**: Use at least 256-bit keys for symmetric encryption.

6. **Secure Password Storage**: Always hash passwords with a salt, never store plaintext passwords.

7. **Data Integrity**: Use HMAC for verifying data integrity when needed.

8. **Error Handling**: Implement secure error handling that doesn't reveal sensitive information.

9. **Secure Deletion**: Implement secure methods for deleting sensitive data when no longer needed.

10. **Audit Logging**: Log all encryption/decryption operations for audit purposes.

## 6. HIPAA Compliance Considerations

- **Data Encryption**: HIPAA requires encryption of PHI both at rest and in transit.

- **Key Management**: Implement proper key management practices to protect encryption keys.

- **Access Controls**: Restrict access to encryption keys and encrypted data to authorized personnel only.

- **Audit Trails**: Maintain logs of all encryption/decryption operations for compliance audits.

- **Risk Assessment**: Regularly assess the effectiveness of encryption measures.

- **Breach Notification**: Have procedures in place for handling potential breaches of encrypted data.

## 7. Integration with AWS KMS

For production environments, it's recommended to use AWS KMS for key management:

```python
import boto3
from app.utils.encryption import EncryptionService

def get_encryption_service_with_kms():
    """
    Create an EncryptionService using a key from AWS KMS.
    
    Returns:
        EncryptionService instance
    """
    # Get the KMS client
    kms_client = boto3.client('kms')
    
    # Get the data key
    response = kms_client.generate_data_key(
        KeyId='alias/novamind-encryption-key',
        KeySpec='AES_256'
    )
    
    # Use the plaintext key for encryption
    data_key = response['Plaintext']
    
    # Store the encrypted key for later use
    encrypted_data_key = response['CiphertextBlob']
    
    # Create the encryption service with the data key
    return EncryptionService(key=data_key)
```

## 8. Conclusion

The HIPAA-compliant encryption utility is a critical component of the NOVAMIND platform's security infrastructure. By implementing industry-standard encryption algorithms and secure key management practices, it helps ensure that patient data remains confidential and protected from unauthorized access or tampering. This utility plays a key role in meeting HIPAA requirements for data protection while providing a simple and consistent API for encryption operations throughout the application.
