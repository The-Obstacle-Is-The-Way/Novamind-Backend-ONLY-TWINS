"""
Field-level encryption for HIPAA-compliant PHI protection.

This module provides surgical field-level encryption for sensitive patient data
following HIPAA requirements while maintaining clean architectural principles.
"""

import copy
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

# Update import to use the refactored BaseEncryptionService
from .base_encryption_service import BaseEncryptionService 

# Configure logger
logger = logging.getLogger(__name__)


class FieldEncryptor:
    """HIPAA-compliant field-level encryption for PHI data.
    
    Implements selective encryption/decryption of sensitive fields within complex 
    nested data structures (dictionaries and lists) using dot notation paths.
    """
    
    def __init__(self, encryption_service: BaseEncryptionService):
        """Initialize with an instance of the BaseEncryptionService.
        
        Args:
            encryption_service: Service instance for encrypting/decrypting values.
        """
        if not isinstance(encryption_service, BaseEncryptionService):
             raise TypeError("encryption_service must be an instance of BaseEncryptionService")
        self._encryption = encryption_service
        # Remove test mode check
        # self._test_mode = hasattr(encryption_service, 'is_test_mode') and encryption_service.is_test_mode
    
    def encrypt_fields(self, data: Union[Dict[str, Any], List[Any]], fields: List[str]) -> Union[Dict[str, Any], List[Any]]:
        """Encrypt specific fields in a data structure (dict or list).
        
        Args:
            data: Data structure (dict or list) containing fields to encrypt.
            fields: List of field paths in dot notation (e.g., 'user.profile.email').
            
        Returns:
            A deep copy of the data structure with specified fields encrypted.
        """
        if not data or not fields:
            return data
            
        # Make a deep copy to avoid modifying the original
        result = copy.deepcopy(data)
        
        # Remove test-specific original value storage
        # if self._test_mode:
        #     result['_test_original_values'] = {}
        #     if "demographics" in result and "address" in result["demographics"]:
        #         ...
        
        # Process each field path for encryption
        for field_path in fields:
            # Remove test-specific original value storage call
            # if self._test_mode:
            #     self._store_original_value(result, field_path, result.get('_test_original_values', {}))
                
            self._process_field(result, field_path, encrypt=True)
            
        return result
    
    def decrypt_fields(self, data: Union[Dict[str, Any], List[Any]], fields: List[str]) -> Union[Dict[str, Any], List[Any]]:
        """Decrypt specific fields in a data structure (dict or list).
        
        Args:
            data: Data structure (dict or list) with encrypted fields.
            fields: List of field paths in dot notation.
            
        Returns:
            A deep copy of the data structure with specified fields decrypted.
        """
        if not data or not fields:
            return data
            
        # Make a deep copy to avoid modifying the original
        result = copy.deepcopy(data)
        
        # Remove test mode restoration logic
        # if self._test_mode and '_test_original_values' in result:
        #     original_values = result['_test_original_values']
        #     ...
        #     del result['_test_original_values']
        
        # Process each field path for decryption
        for field_path in fields:
            self._process_field(result, field_path, encrypt=False)
            
        return result
    
    # Remove test-specific helper methods
    # def _is_patient_record_test_case(self, data: Dict[str, Any]) -> bool:
    #     ...
    
    # def _store_original_value(self, data: Dict[str, Any], field_path: str, storage: Dict[str, Any]) -> None:
    #     ...
    
    # def _restore_original_value(self, data: Dict[str, Any], field_path: str, storage: Dict[str, Any]) -> None:
    #     ...
    
    def _process_field(self, data: Union[Dict[str, Any], List[Any]], field_path: str, encrypt: bool) -> None:
        """Recursively process a field path for encryption or decryption.

        Handles nested dictionaries and lists.
        
        Args:
            data: Current data structure segment (dict or list) being processed.
            field_path: Remaining field path in dot notation.
            encrypt: If True, encrypt the field; otherwise decrypt.
        """
        if not field_path:
            return
            
        parts = field_path.split('.', 1) # Split only the first part
        current_key = parts[0]
        remaining_path = parts[1] if len(parts) > 1 else None

        if isinstance(data, dict):
            if current_key in data:
                if remaining_path:
                    # Navigate deeper
                    self._process_field(data[current_key], remaining_path, encrypt)
                else:
                    # Reached the target field
                    value = data[current_key]
                    self._encrypt_or_decrypt_value(data, current_key, value, encrypt)
            # else: field not found in this dict, continue silently

        elif isinstance(data, list):
            # If the current key is a specific index
            if current_key.isdigit():
                index = int(current_key)
                if 0 <= index < len(data):
                    if remaining_path:
                         # Navigate deeper into the list element
                        self._process_field(data[index], remaining_path, encrypt)
                    else:
                         # Reached the target element (leaf node)
                        value = data[index]
                        # Use a temporary dict wrapper for _encrypt_or_decrypt_value 
                        # or modify _encrypt_or_decrypt_value to handle lists
                        temp_wrapper = {'value': value}
                        self._encrypt_or_decrypt_value(temp_wrapper, 'value', value, encrypt)
                        data[index] = temp_wrapper['value']
            else:
                 # Apply the entire path to each element if the key is not an index
                 # This handles cases like "items.name" where items is a list of dicts.
                 logger.debug(f"Applying path '{field_path}' to elements of list.")
                 for item in data:
                     if isinstance(item, (dict, list)): # Only process containers
                         self._process_field(item, field_path, encrypt)
        
        # else: data is not a dict or list, cannot navigate further

    def _encrypt_or_decrypt_value(self, obj: Dict[str, Any], field: str, value: Any, encrypt: bool) -> None:
        """Encrypt or decrypt a specific field's value using the BaseEncryptionService.
        
        Modifies the `obj` dictionary in place.

        Args:
            obj: Dictionary containing the field.
            field: Field name to process.
            value: Current field value.
            encrypt: Whether to encrypt or decrypt.
        """
        if value is None:
            # Do not encrypt/decrypt None values
            return 
            
        # Remove test-specific conditional logic
        # if self._test_mode and field == "medical_record_number":
        #     ...
        
        try:
            if encrypt:
                 # Encrypt only if it's not already encrypted (basic check)
                 # More robust checks might be needed depending on requirements
                 if not (isinstance(value, str) and value.startswith(self._encryption.VERSION_PREFIX)):
                    encrypted_value = self._encryption.encrypt(value)
                    if encrypted_value is not None: # Check if encryption returned None
                        obj[field] = encrypted_value
                    else:
                        # Handle case where encryption returns None (e.g., input was None initially)
                        # Keep original value or set to None? Setting to None seems safer.
                        obj[field] = None 
                 else:
                     logger.debug(f"Value for field '{field}' appears already encrypted, skipping encryption.")
            else: # Decrypt
                if isinstance(value, str) and value.startswith(self._encryption.VERSION_PREFIX):
                    obj[field] = self._encryption.decrypt(value)
                # else: Value is not a string or doesn't have the prefix, assume not encrypted
                # Keep the original value

        except (ValueError, TypeError) as e:
            op = "Encryption" if encrypt else "Decryption"
            logger.error(f"{op} error for field '{field}': {e}. Keeping original value.")
            # Keep original value in case of error during processing
            pass # Keep obj[field] as it was

    # Remove _process_nested_dict and _process_nested_list as _process_field handles recursion
    # def _process_nested_dict(self, data: Dict[str, Any], encrypt: bool) -> None:
    #     ...
    # def _process_nested_list(self, data: List[Any], encrypt: bool) -> None:
    #     ...