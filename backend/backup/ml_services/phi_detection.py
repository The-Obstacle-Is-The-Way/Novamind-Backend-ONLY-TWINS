# -*- coding: utf-8 -*-
"""
PHI Detection Service Implementation.

This module provides a real implementation of PHI detection services using AWS Comprehend Medical
to detect and redact Protected Health Information (PHI) in compliance with HIPAA regulations.
"""

import re
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from app.core.services.ml.interface import PHIDetectionInterface
from app.core.utils.logging import get_logger


# Create logger (no PHI logging)
logger = get_logger(__name__)


class AWSComprehendMedicalPHIDetection(PHIDetectionInterface):
    """
    AWS Comprehend Medical PHI Detection Service.
    
    This class provides a real implementation of PHI detection services using
    AWS Comprehend Medical to detect and redact Protected Health Information (PHI)
    in compliance with HIPAA regulations.
    """
    
    def __init__(self) -> None:
        """Initialize PHI detection service."""
        self._initialized = False
        self._config = None
        self._comprehend_medical_client = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration dictionary containing AWS credentials
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        try:
            self._config = config or {}
            
            # Extract configuration values
            aws_region = self._config.get("aws_region", "us-east-1")
            aws_access_key_id = self._config.get("aws_access_key_id")
            aws_secret_access_key = self._config.get("aws_secret_access_key")
            
            # Initialize AWS Comprehend Medical client
            if aws_access_key_id and aws_secret_access_key:
                self._comprehend_medical_client = boto3.client(
                    "comprehendmedical",
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # Use IAM role or credentials from environment
                self._comprehend_medical_client = boto3.client(
                    "comprehendmedical",
                    region_name=aws_region
                )
            
            self._initialized = True
            logger.info("PHI detection service initialized successfully")
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to initialize AWS Comprehend Medical client: {str(e)}")
            self._initialized = False
            self._config = None
            self._comprehend_medical_client = None
            raise InvalidConfigurationError(f"Failed to initialize AWS Comprehend Medical client: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to initialize PHI detection service: {str(e)}")
            self._initialized = False
            self._config = None
            self._comprehend_medical_client = None
            raise InvalidConfigurationError(f"Failed to initialize PHI detection service: {str(e)}")
    
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return self._initialized and self._comprehend_medical_client is not None
    
    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        self._initialized = False
        self._config = None
        self._comprehend_medical_client = None
        logger.info("PHI detection service shut down")
    
    def _check_service_initialized(self) -> None:
        """
        Check if the service is initialized.
        
        Raises:
            ServiceUnavailableError: If service is not initialized
        """
        if not self._initialized or not self._comprehend_medical_client:
            raise ServiceUnavailableError("PHI detection service is not initialized")
    
    def _validate_text(self, text: str) -> None:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            
        Raises:
            InvalidRequestError: If text is empty or invalid
        """
        if not text or not isinstance(text, str):
            raise InvalidRequestError("Text must be a non-empty string")
    
    def detect_phi(self, text: str) -> Dict[str, Any]:
        """
        Detect PHI in text.
        
        Args:
            text: Text to check for PHI
            
        Returns:
            Dictionary containing PHI detection results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        self._check_service_initialized()
        self._validate_text(text)
        
        try:
            # Call AWS Comprehend Medical to detect PHI
            response = self._comprehend_medical_client.detect_phi(Text=text)
            
            # Extract PHI entities
            phi_entities = response.get("Entities", [])
            
            # Check if any PHI was detected
            has_phi = len(phi_entities) > 0
            
            # Format results
            result = {
                "has_phi": has_phi,
                "phi_entities": phi_entities,
                "phi_count": len(phi_entities),
                "phi_types": list(set(entity["Type"] for entity in phi_entities)) if has_phi else []
            }
            
            # Do not log any PHI information
            if has_phi:
                logger.info(f"PHI detected: {len(phi_entities)} entities of types: {result['phi_types']}")
            else:
                logger.info("No PHI detected")
                
            return result
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error detecting PHI: {str(e)}")
            raise ServiceUnavailableError(f"Error detecting PHI: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during PHI detection: {str(e)}")
            raise ServiceUnavailableError(f"Unexpected error during PHI detection: {str(e)}")
    
    def redact_phi(self, text: str) -> Dict[str, Any]:
        """
        Redact PHI in text.
        
        Args:
            text: Text to redact PHI from
            
        Returns:
            Dictionary containing redacted text and redaction statistics
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        self._check_service_initialized()
        self._validate_text(text)
        
        try:
            # First detect PHI
            detection_result = self.detect_phi(text)
            phi_entities = detection_result.get("phi_entities", [])
            
            # If no PHI detected, return original text
            if not phi_entities:
                return {
                    "redacted_text": text,
                    "original_text_length": len(text),
                    "redacted_text_length": len(text),
                    "redaction_count": 0,
                    "redaction_types": []
                }
            
            # Sort entities by begin_offset in descending order to avoid indexing issues
            # when replacing text
            phi_entities.sort(key=lambda x: x["BeginOffset"], reverse=True)
            
            # Redact PHI entities
            redacted_text = text
            redaction_types = set()
            
            for entity in phi_entities:
                begin_offset = entity["BeginOffset"]
                end_offset = entity["EndOffset"]
                entity_type = entity["Type"]
                redaction_types.add(entity_type)
                
                # Replace entity with redaction marker
                redaction_marker = f"[REDACTED-{entity_type}]"
                redacted_text = (
                    redacted_text[:begin_offset] + 
                    redaction_marker + 
                    redacted_text[end_offset:]
                )
            
            # Prepare result
            result = {
                "redacted_text": redacted_text,
                "original_text_length": len(text),
                "redacted_text_length": len(redacted_text),
                "redaction_count": len(phi_entities),
                "redaction_types": list(redaction_types)
            }
            
            # Do not log any PHI information
            logger.info(
                f"Redacted {len(phi_entities)} PHI entities of types: {list(redaction_types)}"
            )
            
            return result
            
        except ServiceUnavailableError:
            # Pass through service errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PHI redaction: {str(e)}")
            raise ServiceUnavailableError(f"Unexpected error during PHI redaction: {str(e)}")