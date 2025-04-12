"""
Field-level encryption for HIPAA-compliant data protection.

This module provides selective encryption/decryption for specific fields
within complex data structures to protect sensitive patient information 
while maintaining application functionality.
"""

import json
import logging
from typing import Dict, List, Any, Union, Optional

from app.core.security.encryption import EncryptionService

# Configure logger
logger = logging.getLogger(__name__)


class FieldEncryptor:
    """Field-level encryption service for protecting specific data elements.
    
    This class enables selective encryption of fields within nested data structures,
    allowing the system to protect sensitive PHI (Protected Health Information)
    while leaving non-sensitive data in clear text for processing.
    
    Follows clean architecture principles by depending on abstractions (EncryptionService)
    rather than concrete implementations.
    """
    
    def __init__(self, encryption_service: EncryptionService):
        """Initialize the field encryptor with an encryption service.
        
        Args:
            encryption_service: The encryption service to use for crypto operations
        """
        self._encryption = encryption_service
    
    def encrypt_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a data structure.
        
        Args:
            data: The data structure containing fields to encrypt
            fields: List of dot-notation paths to fields that should be encrypted
                   Example: ["patient.name", "patient.ssn"]
        
        Returns:
            A new data structure with specified fields encrypted
        """
        if not data or not fields:
            return data
            
        result = data.copy()  # Create a copy to avoid mutating the original
        
        for field_path in fields:
            self._process_field(result, field_path, encrypt=True)
            
        return result
    
    def decrypt_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a data structure.
        
        Args:
            data: The data structure containing fields to decrypt
            fields: List of dot-notation paths to fields that should be decrypted
                   Example: ["patient.name", "patient.ssn"]
        
        Returns:
            A new data structure with specified fields decrypted
        """
        if not data or not fields:
            return data
            
        result = data.copy()  # Create a copy to avoid mutating the original
        
        for field_path in fields:
            self._process_field(result, field_path, encrypt=False)
            
        return result
    
    def _process_field(self, data: Dict[str, Any], field_path: str, encrypt: bool) -> None:
        """Process (encrypt/decrypt) a field within a nested structure.
        
        Args:
            data: The data structure to modify
            field_path: Dot-notation path to the field
            encrypt: True for encryption, False for decryption
        """
        if not field_path or not data:
            return
            
        path_parts = field_path.split('.')
        current = data
        
        # For simple non-nested paths or wildcard paths (which are just the field name)
        if len(path_parts) == 1:
            field = path_parts[0]
            if field in current:
                # Process the simple field directly
                self._encrypt_or_decrypt_value(current, field, encrypt)
            return
        
        # Navigate to the parent of the target field
        for i, part in enumerate(path_parts[:-1]):
            if part not in current:
                # Path doesn't exist in the data, nothing to process
                return
                
            # Handle the case where we encounter a list along the path
            if isinstance(current[part], list):
                # Process each item in the list
                for item in current[part]:
                    if isinstance(item, dict):
                        # Create a sub-path for the remaining parts
                        sub_path = '.'.join(path_parts[i+1:])
                        self._process_field(item, sub_path, encrypt)
                return
                
            # Continue navigating the path
            if not isinstance(current[part], dict):
                # Cannot navigate further, not a dict
                return
                
            current = current[part]
            
        # Process the target field
        last_part = path_parts[-1]
        
        # Check if the target exists
        if last_part not in current:
            return
        
        # Handle the field value
        self._encrypt_or_decrypt_value(current, last_part, encrypt)
    
    def _encrypt_or_decrypt_value(self, data_dict: Dict[str, Any], field: str, encrypt: bool) -> None:
        """Encrypt or decrypt a specific field value in a dictionary.
        
        Args:
            data_dict: Dictionary containing the field
            field: Field name to process
            encrypt: True for encryption, False for decryption
        """
        if field not in data_dict:
            return
            
        # Handle different data types
        if isinstance(data_dict[field], dict):
            # For dictionaries, serialize to JSON first
            if encrypt:
                json_str = json.dumps(data_dict[field])
                data_dict[field] = self._encryption.encrypt(json_str)
            else:
                if isinstance(data_dict[field], str) and data_dict[field].startswith("v1:"):
                    json_str = self._encryption.decrypt(data_dict[field])
                    data_dict[field] = json.loads(json_str)
        
        elif isinstance(data_dict[field], list):
            # For lists, encrypt/decrypt each item
            if encrypt:
                json_str = json.dumps(data_dict[field])
                data_dict[field] = self._encryption.encrypt(json_str)
            else:
                if isinstance(data_dict[field], str) and data_dict[field].startswith("v1:"):
                    json_str = self._encryption.decrypt(data_dict[field])
                    data_dict[field] = json.loads(json_str)
        
        else:
            # For primitive types
            if encrypt:
                # Convert to string for encryption
                value_str = str(data_dict[field])
                data_dict[field] = self._encryption.encrypt(value_str)
            else:
                # Only decrypt if it appears to be encrypted
                if isinstance(data_dict[field], str) and data_dict[field].startswith("v1:"):
                    data_dict[field] = self._encryption.decrypt(data_dict[field])