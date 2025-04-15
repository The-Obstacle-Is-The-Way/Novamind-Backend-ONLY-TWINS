# -*- coding: utf-8 -*-
"""
MentaLLaMA Service Module.

This module provides a HIPAA-compliant integration with the MentaLLaMA
mental health language models, optimized for clinical use.
"""

import os
import json
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union, cast
from enum import Enum
from pathlib import Path

import aiohttp
import backoff
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.presentation.api.schemas.ml_schemas import (
    ModelType,
    TaskType,
    MentaLLaMARequest,
    MentaLLaMAResponse
)
from app.core.config.ml_settings import MentaLLaMASettings
from app.core.exceptions.ml_exceptions import (
    MentaLLaMAException,
    MentaLLaMAConnectionError,
    MentaLLaMATimeoutError,
    MentaLLaMAInvalidInputError,
    MentaLLaMAAuthenticationError,
    MentaLLaMAQuotaExceededError
)
from app.core.utils.logging import get_logger
from app.infrastructure.ml.mentallama.model import MentalLlamaModel
from app.infrastructure.ml.mentallama.utils import preprocess_input, postprocess_output
from app.domain.entities.ml_model import MLModelInfo, MLModelStatus


# Setup logger
logger = get_logger(__name__)


class MentaLLaMAProvider(str, Enum):
    """MentaLLaMA provider types."""
    
    OPENAI = "openai"
    AZURE = "azure"
    LOCAL = "local"
    CUSTOM = "custom"


class MentaLLaMAService:
    """Service for interacting with MentaLLaMA models."""
    
    def __init__(self, settings: MentaLLaMASettings):
        """
        Initialize MentaLLaMA service.
        
        Args:
            settings: MentaLLaMA settings
        """
        self.settings = settings
        self.provider = settings.provider
        self.clients: Dict[str, Any] = {}
        
        # Initialize clients
        self._initialize_clients()
        
        logger.info(
            "Initialized MentaLLaMA service",
            extra={"provider": self.provider}
        )
    
    def _initialize_clients(self) -> None:
        """
        Initialize API clients for different providers.
        
        Raises:
            MentaLLaMAConnectionError: If client initialization fails
        """
        try:
            if self.provider == MentaLLaMAProvider.OPENAI:
                self._initialize_openai_client()
            elif self.provider == MentaLLaMAProvider.AZURE:
                self._initialize_azure_client()
            elif self.provider == MentaLLaMAProvider.LOCAL:
                self._initialize_local_client()
            elif self.provider == MentaLLaMAProvider.CUSTOM:
                self._initialize_custom_client()
            else:
                raise MentaLLaMAConnectionError(
                    message=f"Unsupported provider: {self.provider}",
                    details={"provider": self.provider}
                )
        except Exception as e:
            logger.error(
                f"Error initializing MentaLLaMA clients: {str(e)}",
                extra={"provider": self.provider}
            )
            raise MentaLLaMAConnectionError(
                message=f"Error initializing MentaLLaMA clients: {str(e)}",
                details={"provider": self.provider}
            )
    
    def _initialize_openai_client(self) -> None:
        """
        Initialize OpenAI client.
        
        Raises:
            MentaLLaMAConnectionError: If client initialization fails
        """
        try:
            # Check if API key is set
            if not self.settings.openai_api_key:
                raise MentaLLaMAConnectionError(
                    message="OpenAI API key is not set",
                    details={"provider": MentaLLaMAProvider.OPENAI}
                )
            
            # Initialize client
            self.clients["openai"] = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                organization=self.settings.openai_organization,
                timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout)
            )
            
            logger.info(
                "Initialized OpenAI client",
                extra={"provider": MentaLLaMAProvider.OPENAI}
            )
        except Exception as e:
            logger.error(
                f"Error initializing OpenAI client: {str(e)}",
                extra={"provider": MentaLLaMAProvider.OPENAI}
            )
            raise MentaLLaMAConnectionError(
                message=f"Error initializing OpenAI client: {str(e)}",
                details={"provider": MentaLLaMAProvider.OPENAI}
            )
    
    def _initialize_azure_client(self) -> None:
        """
        Initialize Azure OpenAI client.
        
        Raises:
            MentaLLaMAConnectionError: If client initialization fails
        """
        try:
            # Check if Azure API key is set
            if not self.settings.azure_api_key:
                raise MentaLLaMAConnectionError(
                    message="Azure API key is not set",
                    details={"provider": MentaLLaMAProvider.AZURE}
                )
            
            if not self.settings.azure_endpoint:
                raise MentaLLaMAConnectionError(
                    message="Azure endpoint is not set",
                    details={"provider": MentaLLaMAProvider.AZURE}
                )
            
            # Initialize client
            self.clients["azure"] = AsyncOpenAI(
                api_key=self.settings.azure_api_key,
                azure_endpoint=self.settings.azure_endpoint,
                azure_deployment=self.settings.azure_deployment,
                api_version=self.settings.azure_api_version,
                timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout)
            )
            
            logger.info(
                "Initialized Azure OpenAI client",
                extra={"provider": MentaLLaMAProvider.AZURE}
            )
        except Exception as e:
            logger.error(
                f"Error initializing Azure OpenAI client: {str(e)}",
                extra={"provider": MentaLLaMAProvider.AZURE}
            )
            raise MentaLLaMAConnectionError(
                message=f"Error initializing Azure OpenAI client: {str(e)}",
                details={"provider": MentaLLaMAProvider.AZURE}
            )
    
    def _initialize_local_client(self) -> None:
        """
        Initialize local client.
        
        Raises:
            MentaLLaMAConnectionError: If client initialization fails
        """
        try:
            # Check if local URL is set
            if not self.settings.local_url:
                raise MentaLLaMAConnectionError(
                    message="Local URL is not set",
                    details={"provider": MentaLLaMAProvider.LOCAL}
                )
            
            # Initialize HTTP client for local API
            self.clients["local"] = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout)
            )
            
            logger.info(
                "Initialized local client",
                extra={
                    "provider": MentaLLaMAProvider.LOCAL,
                    "url": self.settings.local_url
                }
            )
        except Exception as e:
            logger.error(
                f"Error initializing local client: {str(e)}",
                extra={"provider": MentaLLaMAProvider.LOCAL}
            )
            raise MentaLLaMAConnectionError(
                message=f"Error initializing local client: {str(e)}",
                details={"provider": MentaLLaMAProvider.LOCAL}
            )
    
    def _initialize_custom_client(self) -> None:
        """
        Initialize custom client.
        
        Raises:
            MentaLLaMAConnectionError: If client initialization fails
        """
        try:
            # Check if custom URL is set
            if not self.settings.custom_url:
                raise MentaLLaMAConnectionError(
                    message="Custom URL is not set",
                    details={"provider": MentaLLaMAProvider.CUSTOM}
                )
            
            # Initialize HTTP client for custom API
            self.clients["custom"] = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout)
            )
            
            logger.info(
                "Initialized custom client",
                extra={
                    "provider": MentaLLaMAProvider.CUSTOM,
                    "url": self.settings.custom_url
                }
            )
        except Exception as e:
            logger.error(
                f"Error initializing custom client: {str(e)}",
                extra={"provider": MentaLLaMAProvider.CUSTOM}
            )
            raise MentaLLaMAConnectionError(
                message=f"Error initializing custom client: {str(e)}",
                details={"provider": MentaLLaMAProvider.CUSTOM}
            )
    
    async def close(self) -> None:
        """Close all clients."""
        for provider, client in self.clients.items():
            if provider in ["local", "custom"] and isinstance(client, aiohttp.ClientSession):
                await client.close()
    
    @retry(
        retry=retry_if_exception_type(
            (aiohttp.ClientError, asyncio.TimeoutError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def process_request(self, request: MentaLLaMARequest) -> MentaLLaMAResponse:
        """
        Process a MentaLLaMA request.
        
        Args:
            request: MentaLLaMA request
            
        Returns:
            MentaLLaMA response
            
        Raises:
            MentaLLaMAInvalidInputError: If request is invalid
            MentaLLaMAConnectionError: If connection fails
            MentaLLaMATimeoutError: If request times out
            MentaLLaMAAuthenticationError: If authentication fails
            MentaLLaMAQuotaExceededError: If quota is exceeded
            MentaLLaMAException: For other errors
        """
        try:
            # Validate request
            self._validate_request(request)
            
            # Process based on provider
            if self.provider == MentaLLaMAProvider.OPENAI:
                response = await self._process_openai_request(request)
            elif self.provider == MentaLLaMAProvider.AZURE:
                response = await self._process_azure_request(request)
            elif self.provider == MentaLLaMAProvider.LOCAL:
                response = await self._process_local_request(request)
            elif self.provider == MentaLLaMAProvider.CUSTOM:
                response = await self._process_custom_request(request)
            else:
                raise MentaLLaMAException(
                    message=f"Unsupported provider: {self.provider}",
                    details={"provider": self.provider}
                )
            
            return response
        except MentaLLaMAException:
            # Re-raise known exceptions
            raise
        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise MentaLLaMAAuthenticationError(
                    message=f"Authentication failed: {str(e)}",
                    details={"status": e.status, "message": e.message}
                )
            elif e.status == 429:
                raise MentaLLaMAQuotaExceededError(
                    message=f"Rate limit exceeded: {str(e)}",
                    details={"status": e.status, "message": e.message}
                )
            else:
                raise MentaLLaMAConnectionError(
                    message=f"API request failed: {str(e)}",
                    details={"status": e.status, "message": e.message}
                )
        except (aiohttp.ClientError, aiohttp.ClientConnectionError) as e:
            raise MentaLLaMAConnectionError(
                message=f"Connection error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
        except asyncio.TimeoutError as e:
            raise MentaLLaMATimeoutError(
                message=f"Request timed out: {str(e)}",
                details={"timeout": self.settings.request_timeout}
            )
        except Exception as e:
            logger.error(
                f"Unexpected error processing MentaLLaMA request: {str(e)}",
                extra={"error_type": type(e).__name__}
            )
            raise MentaLLaMAException(
                message=f"Unexpected error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def _validate_request(self, request: MentaLLaMARequest) -> None:
        """
        Validate MentaLLaMA request.
        
        Args:
            request: MentaLLaMA request
            
        Raises:
            MentaLLaMAInvalidInputError: If request is invalid
        """
        if not request.prompt or len(request.prompt.strip()) < 3:
            raise MentaLLaMAInvalidInputError(
                message="Prompt is too short or empty",
                details={"prompt_length": len(request.prompt) if request.prompt else 0}
            )
        
        if request.max_tokens is not None and request.max_tokens <= 0:
            raise MentaLLaMAInvalidInputError(
                message="max_tokens must be positive",
                details={"max_tokens": request.max_tokens}
            )
        
        if request.temperature is not None and (request.temperature < 0.0 or request.temperature > 1.0):
            raise MentaLLaMAInvalidInputError(
                message="temperature must be between 0.0 and 1.0",
                details={"temperature": request.temperature}
            )
        
        if request.top_p is not None and (request.top_p < 0.0 or request.top_p > 1.0):
            raise MentaLLaMAInvalidInputError(
                message="top_p must be between 0.0 and 1.0",
                details={"top_p": request.top_p}
            )
    
    async def _process_openai_request(self, request: MentaLLaMARequest) -> MentaLLaMAResponse:
        """
        Process request using OpenAI client.
        
        Args:
            request: MentaLLaMA request
            
        Returns:
            MentaLLaMA response
            
        Raises:
            MentaLLaMAConnectionError: If API request fails
        """
        client = cast(AsyncOpenAI, self.clients.get("openai"))
        
        if not client:
            raise MentaLLaMAConnectionError(
                message="OpenAI client not initialized",
                details={"provider": MentaLLaMAProvider.OPENAI}
            )
        
        # Map MentaLLaMA model to OpenAI model
        model = self._map_model_to_openai(request.model)
        
        # Create system message based on task
        system_message = self._create_system_message(request.task, request.model)
        
        # Create messages
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": request.prompt}
        ]
        
        # Add context if provided
        if request.context:
            context_str = json.dumps(request.context)
            messages.insert(1, {"role": "system", "content": f"Context: {context_str}"})
        
        # Create request parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p
        }
        
        # Call OpenAI API
        try:
            start_time = time.time()
            completion: ChatCompletion = await client.chat.completions.create(**params)
            end_time = time.time()
            
            # Extract response
            message = completion.choices[0].message
            generated_text = message.content or ""
            
            # Create response
            response = MentaLLaMAResponse(
                model=request.model,
                task=request.task,
                generated_text=generated_text,
                usage=completion.usage.model_dump() if completion.usage else None
            )
            
            # Log performance (without sensitive data)
            logger.info(
                "OpenAI request completed",
                extra={
                    "model": model,
                    "duration_ms": int((end_time - start_time) * 1000),
                    "tokens": completion.usage.total_tokens if completion.usage else None
                }
            )
            
            return response
        except Exception as e:
            logger.error(
                f"Error calling OpenAI API: {str(e)}",
                extra={"model": model}
            )
            raise
    
    async def _process_azure_request(self, request: MentaLLaMARequest) -> MentaLLaMAResponse:
        """
        Process request using Azure OpenAI client.
        
        Args:
            request: MentaLLaMA request
            
        Returns:
            MentaLLaMA response
            
        Raises:
            MentaLLaMAConnectionError: If API request fails
        """
        client = cast(AsyncOpenAI, self.clients.get("azure"))
        
        if not client:
            raise MentaLLaMAConnectionError(
                message="Azure OpenAI client not initialized",
                details={"provider": MentaLLaMAProvider.AZURE}
            )
        
        # Map MentaLLaMA model to Azure deployment
        # Use the configured deployment or fallback to a mapping
        if self.settings.azure_deployment:
            model = self.settings.azure_deployment
        else:
            model = self._map_model_to_azure(request.model)
        
        # Create system message based on task
        system_message = self._create_system_message(request.task, request.model)
        
        # Create messages
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": request.prompt}
        ]
        
        # Add context if provided
        if request.context:
            context_str = json.dumps(request.context)
            messages.insert(1, {"role": "system", "content": f"Context: {context_str}"})
        
        # Create request parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p
        }
        
        # Call Azure API
        try:
            start_time = time.time()
            completion: ChatCompletion = await client.chat.completions.create(**params)
            end_time = time.time()
            
            # Extract response
            message = completion.choices[0].message
            generated_text = message.content or ""
            
            # Create response
            response = MentaLLaMAResponse(
                model=request.model,
                task=request.task,
                generated_text=generated_text,
                usage=completion.usage.model_dump() if completion.usage else None
            )
            
            # Log performance (without sensitive data)
            logger.info(
                "Azure OpenAI request completed",
                extra={
                    "model": model,
                    "duration_ms": int((end_time - start_time) * 1000),
                    "tokens": completion.usage.total_tokens if completion.usage else None
                }
            )
            
            return response
        except Exception as e:
            logger.error(
                f"Error calling Azure OpenAI API: {str(e)}",
                extra={"model": model}
            )
            raise
    
    async def _process_local_request(self, request: MentaLLaMARequest) -> MentaLLaMAResponse:
        """
        Process request using local client.
        
        Args:
            request: MentaLLaMA request
            
        Returns:
            MentaLLaMA response
            
        Raises:
            MentaLLaMAConnectionError: If API request fails
        """
        client = cast(aiohttp.ClientSession, self.clients.get("local"))
        
        if not client:
            raise MentaLLaMAConnectionError(
                message="Local client not initialized",
                details={"provider": MentaLLaMAProvider.LOCAL}
            )
        
        if not self.settings.local_url:
            raise MentaLLaMAConnectionError(
                message="Local URL not set",
                details={"provider": MentaLLaMAProvider.LOCAL}
            )
        
        # Prepare request payload
        payload = {
            "model": request.model.value,
            "task": request.task.value,
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }
        
        if request.context:
            payload["context"] = request.context
        
        # Call local API
        try:
            start_time = time.time()
            async with client.post(
                self.settings.local_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                end_time = time.time()
                
                # Raise for HTTP errors
                response.raise_for_status()
                
                # Parse response
                result = await response.json()
                
                # Create response
                response_obj = MentaLLaMAResponse(
                    model=request.model,
                    task=request.task,
                    generated_text=result.get("generated_text", ""),
                    usage=result.get("usage"),
                    warnings=result.get("warnings")
                )
                
                # Log performance (without sensitive data)
                logger.info(
                    "Local API request completed",
                    extra={
                        "model": request.model.value,
                        "duration_ms": int((end_time - start_time) * 1000),
                        "tokens": result.get("usage", {}).get("total_tokens") if result.get("usage") else None
                    }
                )
                
                return response_obj
        except aiohttp.ClientResponseError as e:
            logger.error(
                f"Error from local API: {str(e)}",
                extra={"status": e.status, "model": request.model.value}
            )
            raise
        except Exception as e:
            logger.error(
                f"Error calling local API: {str(e)}",
                extra={"model": request.model.value}
            )
            raise
    
    async def _process_custom_request(self, request: MentaLLaMARequest) -> MentaLLaMAResponse:
        """
        Process request using custom client.
        
        Args:
            request: MentaLLaMA request
            
        Returns:
            MentaLLaMA response
            
        Raises:
            MentaLLaMAConnectionError: If API request fails
        """
        client = cast(aiohttp.ClientSession, self.clients.get("custom"))
        
        if not client:
            raise MentaLLaMAConnectionError(
                message="Custom client not initialized",
                details={"provider": MentaLLaMAProvider.CUSTOM}
            )
        
        if not self.settings.custom_url:
            raise MentaLLaMAConnectionError(
                message="Custom URL not set",
                details={"provider": MentaLLaMAProvider.CUSTOM}
            )
        
        # Prepare request payload
        payload = {
            "model": request.model.value,
            "task": request.task.value,
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }
        
        if request.context:
            payload["context"] = request.context
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        
        # Add API key if set
        if self.settings.custom_api_key:
            headers["Authorization"] = f"Bearer {self.settings.custom_api_key}"
        
        # Call custom API
        try:
            start_time = time.time()
            async with client.post(
                self.settings.custom_url,
                json=payload,
                headers=headers
            ) as response:
                end_time = time.time()
                
                # Raise for HTTP errors
                response.raise_for_status()
                
                # Parse response
                result = await response.json()
                
                # Create response
                response_obj = MentaLLaMAResponse(
                    model=request.model,
                    task=request.task,
                    generated_text=result.get("generated_text", ""),
                    usage=result.get("usage"),
                    warnings=result.get("warnings")
                )
                
                # Log performance (without sensitive data)
                logger.info(
                    "Custom API request completed",
                    extra={
                        "model": request.model.value,
                        "duration_ms": int((end_time - start_time) * 1000),
                        "tokens": result.get("usage", {}).get("total_tokens") if result.get("usage") else None
                    }
                )
                
                return response_obj
        except aiohttp.ClientResponseError as e:
            logger.error(
                f"Error from custom API: {str(e)}",
                extra={"status": e.status, "model": request.model.value}
            )
            raise
        except Exception as e:
            logger.error(
                f"Error calling custom API: {str(e)}",
                extra={"model": request.model.value}
            )
            raise
    
    def _map_model_to_openai(self, model: ModelType) -> str:
        """
        Map MentaLLaMA model to OpenAI model.
        
        Args:
            model: MentaLLaMA model
            
        Returns:
            OpenAI model name
        """
        # Default mappings
        mappings = {
            ModelType.MENTALLAMA_CLINICAL: "gpt-4-turbo",
            ModelType.MENTALLAMA_PSYCHIATRY: "gpt-4",
            ModelType.MENTALLAMA_THERAPY: "gpt-4",
            ModelType.MENTALLAMA_ASSESSMENT: "gpt-4",
            ModelType.MENTALLAMA_RESEARCH: "gpt-4-turbo"
        }
        
        # Override with settings if available
        if self.settings.model_mappings and model.value in self.settings.model_mappings:
            return self.settings.model_mappings[model.value]
        
        return mappings.get(model, "gpt-4-turbo")
    
    def _map_model_to_azure(self, model: ModelType) -> str:
        """
        Map MentaLLaMA model to Azure deployment.
        
        Args:
            model: MentaLLaMA model
            
        Returns:
            Azure deployment name
        """
        # Default to the configured deployment
        if self.settings.azure_deployment:
            return self.settings.azure_deployment
        
        # Default mappings
        mappings = {
            ModelType.MENTALLAMA_CLINICAL: "gpt-4",
            ModelType.MENTALLAMA_PSYCHIATRY: "gpt-4",
            ModelType.MENTALLAMA_THERAPY: "gpt-4",
            ModelType.MENTALLAMA_ASSESSMENT: "gpt-4",
            ModelType.MENTALLAMA_RESEARCH: "gpt-4"
        }
        
        # Override with settings if available
        if self.settings.model_mappings and model.value in self.settings.model_mappings:
            return self.settings.model_mappings[model.value]
        
        return mappings.get(model, "gpt-4")
    
    def _create_system_message(self, task: TaskType, model: ModelType) -> str:
        """
        Create system message based on task and model.
        
        Args:
            task: Task type
            model: Model type
            
        Returns:
            System message
        """
        # Base instructions
        base_instructions = (
            "You are MentaLLaMA, an advanced clinical AI assistant specialized in mental health. "
            "Your responses are evidence-based, ethical, and patient-centered. "
            "You adhere to clinical best practices and maintain a professional tone. "
            "Your information is based on peer-reviewed literature and clinical guidelines. "
            "You clarify when information is speculative or when multiple perspectives exist. "
            "You DO NOT diagnose patients or replace professional medical advice. "
            "You maintain strict confidentiality and never share or reference patient information outside this conversation. "
            "You DO NOT make up information or references."
        )
        
        # Task-specific instructions
        task_instructions = {
            TaskType.SUMMARIZATION: (
                "Your task is to summarize clinical information into concise, structured formats. "
                "Highlight key patterns, concerns, and clinical observations. "
                "Maintain all clinically relevant details while eliminating redundancy."
            ),
            TaskType.ASSESSMENT: (
                "Your task is to help analyze assessment data and clinical observations. "
                "Provide structured analysis of findings based on clinical frameworks. "
                "Identify patterns and suggest areas for further clinical exploration."
            ),
            TaskType.DIAGNOSIS: (
                "Your task is to discuss diagnostic criteria and differential diagnoses based on DSM-5-TR or ICD-11. "
                "Present various diagnostic considerations based on the information provided. "
                "Highlight what additional information would be helpful for diagnostic clarification."
            ),
            TaskType.TREATMENT_RECOMMENDATION: (
                "Your task is to provide treatment options based on clinical guidelines and evidence-based practices. "
                "Include first-line and alternative approaches when appropriate. "
                "Discuss potential benefits, limitations, and considerations for each option."
            ),
            TaskType.RISK_ASSESSMENT: (
                "Your task is to help identify risk factors and protective factors from clinical information. "
                "Suggest evidence-based risk assessment frameworks that may be applicable. "
                "Emphasize the importance of clinical judgment in risk evaluation."
            ),
            TaskType.SESSION_NOTES: (
                "Your task is to help structure and organize clinical session notes. "
                "Follow SOAP or similar clinical documentation formats. "
                "Focus on objective observations while maintaining clinical relevance."
            ),
            TaskType.LITERATURE_REVIEW: (
                "Your task is to provide concise summaries of current research and clinical literature. "
                "Focus on high-quality evidence from peer-reviewed sources. "
                "Highlight consensus views as well as areas of ongoing research or debate."
            ),
            TaskType.PATIENT_EDUCATION: (
                "Your task is to create clear, accessible educational material for patients. "
                "Use plain language while maintaining clinical accuracy. "
                "Focus on empowerment and self-management strategies when appropriate."
            ),
            TaskType.CLINICAL_QUESTIONS: (
                "Your task is to answer clinical questions with evidence-based information. "
                "Provide nuanced responses that acknowledge clinical complexity. "
                "Cite relevant guidelines or research when applicable."
            ),
            TaskType.DIFFERENTIAL_DIAGNOSIS: (
                "Your task is to develop comprehensive differential diagnoses based on clinical presentations. "
                "Consider common and uncommon possibilities based on the provided information. "
                "Suggest diagnostic approaches to narrow the differential."
            ),
            TaskType.PREDICTION: (
                "Your task is to analyze clinical patterns and trends to identify potential trajectories. "
                "Base predictions on established clinical patterns and evidence. "
                "Emphasize that predictions are probabilistic and require clinical validation."
            ),
            TaskType.CUSTOM: (
                "Respond to the request with your clinical expertise while adhering to ethical guidelines. "
                "Provide structured and evidence-based information tailored to the specific request. "
                "Maintain professional boundaries and clinical best practices."
            )
        }
        
        # Model-specific adjustments
        model_adjustments = {
            ModelType.MENTALLAMA_CLINICAL: "Focus on general clinical mental health concepts and practices.",
            ModelType.MENTALLAMA_PSYCHIATRY: "Emphasize psychiatric perspectives including medication management considerations.",
            ModelType.MENTALLAMA_THERAPY: "Focus on psychotherapeutic approaches, interventions, and therapeutic relationships.",
            ModelType.MENTALLAMA_ASSESSMENT: "Specialize in psychological assessment, testing, and measurement concepts.",
            ModelType.MENTALLAMA_RESEARCH: "Emphasize research methodologies, statistical concepts, and current literature."
        }
        
        # Combine instructions
        instructions = [
            base_instructions,
            task_instructions.get(task, task_instructions[TaskType.CUSTOM]),
            model_adjustments.get(model, "")
        ]
        
        # Add HIPAA compliance reminder
        instructions.append(
            "IMPORTANT: Maintain strict HIPAA compliance. Never include PHI in your responses. "
            "Do not reference patient identifiers, dates, or location information."
        )
        
        return " ".join(instructions)