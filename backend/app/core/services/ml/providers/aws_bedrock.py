# -*- coding: utf-8 -*-
"""
AWS Bedrock Provider for MentaLLaMA.

This module provides AWS Bedrock implementation for MentaLLaMA service.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings
settings = get_settings()
from app.core.exceptions import (
    InvalidConfigurationError, 
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)
from app.core.services.ml.mentalllama import MentaLLaMA as BaseMentaLLaMA # Import correct class, alias for compatibility if needed
from app.core.utils.logging import get_logger

# Create logger (no PHI logging)
logger = get_logger(__name__)


class AWSBedrockMentaLLaMA(BaseMentaLLaMA):
    """
    AWS Bedrock implementation for MentaLLaMA service.
    
    This class provides AWS Bedrock-specific implementation
    for mental health analysis capabilities.
    """
    
    def _initialize_provider(self) -> None:
        """
        Initialize AWS Bedrock-specific resources.
        
        Raises:
            InvalidConfigurationError: If AWS configuration is invalid
            ServiceUnavailableError: If initialization fails
        """
        try:
            # Check required AWS configuration
            aws_config = self._config.get("aws", {})
            
            # Set up AWS session
            self._session_kwargs = {}
            
            # Add region if provided
            if aws_config.get("region"):
                self._session_kwargs["region_name"] = aws_config["region"]
            
            # Add credentials if provided
            if aws_config.get("access_key") and aws_config.get("secret_key"):
                self._session_kwargs["aws_access_key_id"] = aws_config["access_key"]
                self._session_kwargs["aws_secret_access_key"] = aws_config["secret_key"]
            
            # Add profile if provided
            if aws_config.get("profile"):
                self._session_kwargs["profile_name"] = aws_config["profile"]
            
            # Create boto3 session
            self._session = boto3.Session(**self._session_kwargs)
            
            # Create Bedrock Runtime client
            self._bedrock_runtime = self._session.client(
                service_name="bedrock-runtime",
                **{k: v for k, v in self._session_kwargs.items() if k != "profile_name"}
            )
            
            # Initialize default model mappings
            model_mappings = self._config.get("model_mappings", {})
            self._model_mappings = {
                "default": model_mappings.get("default", "anthropic.claude-3-sonnet-20240229-v1:0"),
                "risk_assessment": model_mappings.get("risk_assessment", "anthropic.claude-3-sonnet-20240229-v1:0"),
                "depression_detection": model_mappings.get("depression_detection", "anthropic.claude-3-sonnet-20240229-v1:0"),
                "sentiment_analysis": model_mappings.get("sentiment_analysis", "anthropic.claude-3-sonnet-20240229-v1:0"),
                "wellness_dimensions": model_mappings.get("wellness_dimensions", "anthropic.claude-3-sonnet-20240229-v1:0"),
            }
            
            # Populate available models
            self._available_models = {
                model_id: {"provider": "aws_bedrock"} 
                for model_id in set(self._model_mappings.values())
            }
            
            # Test connection
            self._test_connection()
            
            logger.info("AWS Bedrock MentaLLaMA service initialized")
        
        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS Bedrock initialization failed: {str(e)}")
            raise ServiceUnavailableError(
                f"AWS Bedrock initialization failed: {str(e)}",
                service_name="mentalllama"
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock MentaLLaMA service: {str(e)}")
            raise ServiceUnavailableError(
                f"Failed to initialize AWS Bedrock MentaLLaMA service: {str(e)}",
                service_name="mentalllama"
            )
    
    def _test_connection(self) -> None:
        """
        Test AWS Bedrock connection.
        
        Raises:
            ServiceUnavailableError: If connection test fails
        """
        try:
            # Get default model
            model_id = self._model_mappings["default"]
            
            # Create minimal prompt for test
            test_prompt = "Hello, testing connection. Respond with 'OK'."
            
            # Create Claude request format
            if "anthropic.claude" in model_id:
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [
                        {"role": "user", "content": test_prompt}
                    ],
                    "temperature": 0.0
                }
            # Amazon Titan format
            elif "amazon.titan" in model_id:
                request_body = {
                    "inputText": test_prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 10,
                        "temperature": 0.0,
                        "topP": 0.9
                    }
                }
            # Mistral format
            elif "mistral" in model_id:
                request_body = {
                    "prompt": test_prompt,
                    "max_tokens": 10,
                    "temperature": 0.0,
                    "top_p": 0.9
                }
            # Llama format
            elif "meta.llama" in model_id:
                request_body = {
                    "prompt": test_prompt,
                    "max_gen_len": 10,
                    "temperature": 0.0,
                    "top_p": 0.9
                }
            else:
                # Unknown model
                raise InvalidConfigurationError(f"Unsupported model: {model_id}")
            
            # Invoke model
            response = self._bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            body = json.loads(response.get("body").read())
            
            logger.info("AWS Bedrock connection test successful")
        
        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS Bedrock connection test failed: {str(e)}")
            raise ServiceUnavailableError(
                f"AWS Bedrock connection test failed: {str(e)}",
                service_name="mentalllama"
            )
    
    def _generate(
        self,
        prompt: str,
        model: str = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using AWS Bedrock models.
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Dict containing generated text and metadata
            
        Raises:
            ServiceUnavailableError: If generation fails
            ModelNotFoundError: If model is not available
        """
        try:
            # Start generation time
            start_time = time.time()
            
            # Set default values
            model = model or self._model_mappings["default"]
            max_tokens = max_tokens or 1024
            temperature = temperature if temperature is not None else 0.7
            
            # Create request body based on model type
            # Anthropic Claude models
            if "anthropic.claude" in model:
                request_body = self._create_claude_request(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            # Amazon Titan models
            elif "amazon.titan" in model:
                request_body = self._create_titan_request(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            # Mistral models
            elif "mistral" in model:
                request_body = self._create_mistral_request(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            # Meta Llama models
            elif "meta.llama" in model:
                request_body = self._create_llama_request(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            else:
                raise ModelNotFoundError(
                    f"Model {model} is not supported", 
                    model_id=model
                )
            
            # Invoke model
            response = self._bedrock_runtime.invoke_model(
                modelId=model,
                body=json.dumps(request_body)
            )
            
            # Parse response
            body = json.loads(response.get("body").read())
            
            # Extract text based on model type
            if "anthropic.claude" in model:
                text = body.get("content", [{}])[0].get("text", "")
            elif "amazon.titan" in model:
                text = body.get("results", [{}])[0].get("outputText", "")
            elif "mistral" in model:
                text = body.get("outputs", [{}])[0].get("text", "")
            elif "meta.llama" in model:
                text = body.get("generation", "")
            else:
                text = ""
            
            # End generation time
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate tokens (estimated)
            input_tokens = len(prompt.split()) * 1.3  # rough estimate
            output_tokens = len(text.split()) * 1.3  # rough estimate
            tokens_used = int(input_tokens + output_tokens)
            
            # Create result
            result = {
                "text": text,
                "processing_time": processing_time,
                "tokens_used": tokens_used,
                "metadata": {
                    "model": model,
                    "provider": "aws_bedrock",
                    "confidence": 0.9 if temperature < 0.3 else (0.8 if temperature < 0.7 else 0.7)
                }
            }
            
            return result
            
        except ModelNotFoundError:
            # Re-raise model not found
            raise
        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS Bedrock generation failed: {str(e)}")
            raise ServiceUnavailableError(
                f"AWS Bedrock generation failed: {str(e)}",
                service_name="mentalllama"
            )
    
    def _create_claude_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create request body for Anthropic Claude models.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Request body for Claude model
        """
        # Get additional parameters
        top_p = kwargs.get("top_p", 0.9)
        
        # Create request body
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        return request_body
    
    def _create_titan_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create request body for Amazon Titan models.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Request body for Titan model
        """
        # Get additional parameters
        top_p = kwargs.get("top_p", 0.9)
        
        # Create request body
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": top_p,
                "stopSequences": kwargs.get("stop_sequences", [])
            }
        }
        
        return request_body
    
    def _create_mistral_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create request body for Mistral models.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Request body for Mistral model
        """
        # Get additional parameters
        top_p = kwargs.get("top_p", 0.9)
        
        # Create request body
        request_body = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop": kwargs.get("stop", [])
        }
        
        return request_body
    
    def _create_llama_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create request body for Meta Llama models.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Request body for Llama model
        """
        # Get additional parameters
        top_p = kwargs.get("top_p", 0.9)
        
        # Create request body
        request_body = {
            "prompt": prompt,
            "max_gen_len": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        return request_body