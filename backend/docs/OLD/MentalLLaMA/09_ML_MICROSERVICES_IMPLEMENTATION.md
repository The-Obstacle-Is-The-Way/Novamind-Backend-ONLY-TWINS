# NOVAMIND ML Microservices Implementation: MentaLLaMA Integration

## Overview

This document provides comprehensive implementation guidance for integrating the MentaLLaMA-33B-lora model into NOVAMIND's ML microservices architecture. It covers code structure, deployment patterns, data flow, PHI protection, and testing strategies with concrete examples to enable a robust, HIPAA-compliant implementation.

## System Architecture

### High-Level Component Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                      NOVAMIND ML MICROSERVICES ARCHITECTURE                   │
│                                                                               │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐                │
│  │               │     │               │     │               │                │
│  │ API Gateway   │────►│ API Service   │────►│ Analysis      │                │
│  │ Layer         │     │ Orchestration │     │ Orchestrator  │                │
│  │               │     │               │     │               │                │
│  └───────┬───────┘     └───────┬───────┘     └───────┬───────┘                │
│          │                     │                     │                        │
│          │                     │                     │                        │
│          │                     │                     │                        │
│          │                     │                     │                        │
│  ┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐                │
│  │               │     │               │     │               │                │
│  │ Security &    │     │ PHI Detection │     │ MentaLLaMA    │                │
│  │ Authentication│     │ Service       │     │ Service       │                │
│  │               │     │               │     │               │                │
│  └───────────────┘     └───────────────┘     └───────┬───────┘                │
│                                                      │                        │
│                                                      │                        │
│                                             ┌────────▼────────┐               │
│                                             │                 │               │
│                                             │ Result Storage  │               │
│                                             │ & Processing    │               │
│                                             │                 │               │
│                                             └─────────────────┘               │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **API Gateway Layer**: API routing, rate limiting, initial request validation
2. **API Service Orchestration**: Request processing, workflow management, response formatting
3. **Analysis Orchestrator**: Coordination of analysis tasks, batching, and sequencing
4. **Security & Authentication**: JWT validation, role-based access control, audit logging
5. **PHI Detection Service**: Detection and masking of Protected Health Information
6. **MentaLLaMA Service**: Core AI model inference and result generation
7. **Result Storage & Processing**: Secure storage and post-processing of analysis results

## Code Structure

The microservices follow a standardized structure based on Clean Architecture patterns:

```
ml_microservices/
├── api/                  # API Gateway and service endpoints
│   ├── gateway/          # API Gateway implementation
│   ├── routes/           # FastAPI route definitions
│   └── schemas/          # Pydantic request/response models
├── core/                 # Core domain logic
│   ├── entities/         # Domain entities
│   ├── interfaces/       # Abstract interfaces (ports)
│   └── services/         # Domain service implementations
├── infrastructure/       # External integrations
│   ├── aws/              # AWS service integrations
│   ├── database/         # Database access layer
│   ├── messaging/        # Message queue integration
│   └── storage/          # Object storage integration
├── mentallama/           # MentaLLaMA model implementation
│   ├── inference/        # Model inference logic
│   ├── preprocessing/    # Text preprocessing
│   ├── postprocessing/   # Result processing
│   └── validation/       # Input/output validation
├── phi_detection/        # PHI detection and masking
│   ├── detectors/        # PHI detection algorithms
│   ├── masking/          # PHI masking strategies
│   └── validation/       # PHI detection validation
├── security/             # Security components
│   ├── authentication/   # Authentication logic
│   ├── authorization/    # Authorization rules
│   └── encryption/       # Encryption utilities
└── utils/                # Shared utilities
    ├── logging/          # Secure logging
    ├── monitoring/       # Monitoring and alerting
    └── validation/       # Common validation logic
```

## MentaLLaMA Integration

### 1. Model Loading and Initialization

```python
# ml_microservices/mentallama/inference/model_loader.py
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from typing import Dict, Any, Optional, Tuple

class MentaLLaMAModel:
    """MentaLLaMA model manager handling initialization and inference."""
    
    def __init__(
        self, 
        base_model_path: str, 
        lora_adapter_path: str,
        device_map: str = "auto",
        load_in_8bit: bool = True,
        torch_dtype: torch.dtype = torch.float16
    ):
        """
        Initialize the MentaLLaMA model.
        
        Args:
            base_model_path: Path to base Vicuna model
            lora_adapter_path: Path to MentaLLaMA LoRA adapter weights
            device_map: Device mapping strategy ("auto", "balanced", "sequential", etc.)
            load_in_8bit: Whether to load in 8-bit quantization
            torch_dtype: Data type for model weights
        """
        self.base_model_path = base_model_path
        self.lora_adapter_path = lora_adapter_path
        self.device_map = device_map
        self.load_in_8bit = load_in_8bit
        self.torch_dtype = torch_dtype
        self.tokenizer = None
        self.model = None
        
        # Initialize the model
        self._initialize_model()
        
    def _initialize_model(self) -> None:
        """Load the model and tokenizer."""
        try:
            # 1. Load the tokenizer from the base model
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_path,
                use_fast=False
            )
            
            # 2. Load the base model
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                torch_dtype=self.torch_dtype,
                device_map=self.device_map,
                load_in_8bit=self.load_in_8bit
            )
            
            # 3. Load and apply LoRA adapter
            self.model = PeftModel.from_pretrained(
                base_model,
                self.lora_adapter_path,
                torch_dtype=self.torch_dtype,
                device_map=self.device_map
            )
            
            # 4. Optional: Merge weights for faster inference
            if os.environ.get("MERGE_LORA_WEIGHTS", "False").lower() == "true":
                self.model = self.model.merge_and_unload()
                
        except Exception as e:
            # In production, use a proper logger here
            raise RuntimeError(f"Failed to initialize MentaLLaMA model: {str(e)}")
    
    def generate(
        self, 
        prompt: str, 
        generation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text from the model based on the provided prompt.
        
        Args:
            prompt: The prompt text to generate from
            generation_config: Configuration for text generation
            
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not initialized")
            
        # Set default generation config if not provided
        if generation_config is None:
            generation_config = {
                "max_new_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
                "num_return_sequences": 1
            }
            
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate text
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                **generation_config
            )
            
        # Decode and return generated text
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the prompt from the generated text
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
            
        return generated_text
```

### 2. MentaLLaMA Service Implementation

```python
# ml_microservices/mentallama/service.py
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from ml_microservices.mentallama.inference.model_loader import MentaLLaMAModel
from ml_microservices.mentallama.preprocessing.text_processor import TextPreprocessor
from ml_microservices.mentallama.postprocessing.result_parser import ResultParser
from ml_microservices.phi_detection.service import PHIDetectionService
from ml_microservices.core.interfaces.analysis_service import AnalysisService
from ml_microservices.core.entities.analysis_request import AnalysisRequest
from ml_microservices.core.entities.analysis_result import AnalysisResult
from ml_microservices.security.encryption.result_encryptor import ResultEncryptor
from ml_microservices.utils.logging.secure_logger import SecureLogger

logger = SecureLogger(__name__)

class MentaLLaMAService(AnalysisService):
    """Service for mental health analysis using MentaLLaMA."""
    
    def __init__(
        self,
        model: MentaLLaMAModel,
        phi_service: PHIDetectionService,
        text_preprocessor: TextPreprocessor,
        result_parser: ResultParser,
        result_encryptor: ResultEncryptor
    ):
        """
        Initialize the MentaLLaMA service.
        
        Args:
            model: MentaLLaMA model instance
            phi_service: PHI detection service for text sanitization
            text_preprocessor: Text preprocessing service
            result_parser: Result parsing service
            result_encryptor: Result encryption service
        """
        self.model = model
        self.phi_service = phi_service
        self.text_preprocessor = text_preprocessor
        self.result_parser = result_parser
        self.result_encryptor = result_encryptor
        
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Analyze text using MentaLLaMA.
        
        Args:
            request: Analysis request containing text and parameters
            
        Returns:
            Analysis result
        """
        try:
            # Generate unique request ID for tracking
            request_id = str(uuid.uuid4())
            
            # Log request (without PHI content)
            logger.info(
                f"Processing analysis request {request_id}",
                extra={
                    "request_id": request_id,
                    "analysis_type": request.analysis_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # 1. Detect and mask PHI in the input text
            sanitized_text, phi_metadata = await self.phi_service.detect_and_mask(
                request.text_content
            )
            
            # 2. Preprocess the sanitized text
            processed_text = self.text_preprocessor.preprocess(
                sanitized_text, 
                analysis_type=request.analysis_type
            )
            
            # 3. Construct prompt based on analysis type
            prompt = self._construct_prompt(
                analysis_type=request.analysis_type,
                text_content=processed_text,
                parameters=request.parameters
            )
            
            # 4. Generate inference from model
            generation_config = self._get_generation_config(request.parameters)
            generated_text = self.model.generate(prompt, generation_config)
            
            # 5. Parse the generated text into structured result
            parsed_result = self.result_parser.parse(
                generated_text, 
                analysis_type=request.analysis_type
            )
            
            # 6. Build and encrypt the final result
            result = AnalysisResult(
                request_id=request_id,
                analysis_type=request.analysis_type,
                result=parsed_result,
                model_version="MentaLLaMA-33B-lora-v1.0",
                phi_detected=phi_metadata.get("phi_detected", False),
                timestamp=datetime.utcnow().isoformat()
            )
            
            # 7. Encrypt sensitive parts of the result if needed
            if request.parameters.get("encrypt_result", False):
                result = self.result_encryptor.encrypt(result)
                
            # Log success (without PHI content)
            logger.info(
                f"Successfully processed analysis request {request_id}",
                extra={
                    "request_id": request_id,
                    "analysis_type": request.analysis_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return result
            
        except Exception as e:
            # Log error (without PHI content)
            logger.error(
                f"Error processing analysis request: {str(e)}",
                extra={
                    "request_id": request_id if 'request_id' in locals() else "unknown",
                    "analysis_type": request.analysis_type,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            raise
            
    def _construct_prompt(
        self, 
        analysis_type: str, 
        text_content: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Construct an appropriate prompt based on analysis type.
        
        Args:
            analysis_type: Type of analysis to perform
            text_content: Preprocessed and sanitized text content
            parameters: Additional parameters for analysis
            
        Returns:
            Formatted prompt for the model
        """
        # Implementation based on the MentaLLaMA Mental Health Modeling document
        if analysis_type == "depression_detection":
            return f"""You are a mental health professional analyzing text for signs of depression.

Consider this text: "{text_content}"

Question: Does the author show signs of depression? Provide your assessment and explain your reasoning.

Format your response as:
Depression Indicated: [yes/no/possible]
Confidence: [high/medium/low]
Rationale: [Your detailed explanation]
Key Indicators: [Specific phrases or themes]"""

        elif analysis_type == "risk_assessment":
            return f"""You are a mental health professional evaluating risk level.

Consider this text: "{text_content}"

Question: What is the suicide/self-harm risk level? Provide your assessment as low, medium, or high risk, and explain your reasoning.

Format your response as:
Risk Level: [low/medium/high]
Rationale: [Your detailed explanation]
Key Risk Indicators: [Specific concerning phrases]
Protective Factors: [Any positive elements]"""

        elif analysis_type == "sentiment_analysis":
            return f"""You are a mental health professional analyzing emotional sentiment.

Consider this text: "{text_content}"

Question: What is the emotional sentiment expressed? Analyze as positive, negative, neutral or mixed and explain your reasoning.

Format your response as:
Sentiment: [positive/negative/neutral/mixed]
Rationale: [Your detailed explanation]
Emotional Themes: [Key emotional themes identified]"""

        elif analysis_type == "wellness_dimensions":
            dimensions = parameters.get("dimensions", ["emotional", "social", "physical", "intellectual", "occupational"])
            dimensions_str = ", ".join(dimensions)
            
            return f"""You are a mental health professional analyzing text across wellness dimensions.

Consider this text: "{text_content}"

Question: Analyze this text across key wellness dimensions ({dimensions_str}). Identify areas of strength and potential improvement.

Format your response as:
Dimension Analysis:
{"; ".join([f"- {dim}: [assessment]" for dim in dimensions])}
Areas of Strength: [list strengths]
Areas for Improvement: [list areas]"""

        # Default prompt for unknown analysis types
        return f"""You are a mental health professional analyzing the following text:

"{text_content}"

Please provide a detailed mental health analysis."""
            
    def _get_generation_config(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get generation configuration based on request parameters.
        
        Args:
            parameters: Request parameters
            
        Returns:
            Generation configuration for the model
        """
        # Default configuration
        config = {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "num_return_sequences": 1
        }
        
        # Override with provided parameters if available
        if "max_tokens" in parameters:
            config["max_new_tokens"] = parameters["max_tokens"]
            
        if "temperature" in parameters:
            config["temperature"] = parameters["temperature"]
            
        if "top_p" in parameters:
            config["top_p"] = parameters["top_p"]
        
        return config
```

### 3. PHI Detection Implementation

```python
# ml_microservices/phi_detection/service.py
import re
import boto3
import json
from typing import Dict, Any, List, Tuple, Optional
import os

from ml_microservices.utils.logging.secure_logger import SecureLogger
from ml_microservices.core.interfaces.phi_detection_service import PHIDetectionService

logger = SecureLogger(__name__)

class AWSComprehendMedicalPHIDetection(PHIDetectionService):
    """PHI detection using AWS Comprehend Medical."""
    
    def __init__(
        self, 
        region_name: str = "us-east-1",
        custom_patterns: Optional[Dict[str, str]] = None
    ):
        """
        Initialize AWS Comprehend Medical PHI detection.
        
        Args:
            region_name: AWS region
            custom_patterns: Additional regex patterns for PHI detection
        """
        self.region_name = region_name
        self.comprehend_medical = boto3.client(
            'comprehendmedical', 
            region_name=region_name
        )
        
        # Compile regex patterns
        self.regex_patterns = self._compile_regex_patterns(custom_patterns)
        
    def _compile_regex_patterns(
        self, 
        custom_patterns: Optional[Dict[str, str]] = None
    ) -> Dict[str, re.Pattern]:
        """
        Compile regex patterns for additional PHI detection.
        
        Args:
            custom_patterns: Additional regex patterns
            
        Returns:
            Compiled regex patterns
        """
        patterns = {
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE": r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "URL": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\??[/\w\.-=&%]*',
            "IP_ADDRESS": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "MRNS": r'\b[A-Z]{2}\d{6,8}\b'
        }
        
        # Add custom patterns if provided
        if custom_patterns:
            patterns.update(custom_patterns)
            
        # Compile all patterns
        return {key: re.compile(pattern) for key, pattern in patterns.items()}
        
    async def detect_and_mask(
        self, 
        text: str, 
        mask_format: str = "token"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Detect and mask PHI in text through multiple layers.
        
        Args:
            text: Text that may contain PHI
            mask_format: Format for masking ("token" or "redaction")
            
        Returns:
            Tuple of (masked_text, metadata)
        """
        if not text:
            return text, {"phi_detected": False, "entity_count": 0}
        
        # Initialize tracking
        metadata = {
            "phi_detected": False,
            "entity_count": 0,
            "entity_types": {}
        }
        
        # Layer 1: AWS Comprehend Medical
        masked_text, comprehend_metadata = await self._apply_comprehend_medical(text, mask_format)
        
        # Update tracking metadata
        if comprehend_metadata["phi_detected"]:
            metadata["phi_detected"] = True
            metadata["entity_count"] += comprehend_metadata["entity_count"]
            metadata["entity_types"].update(comprehend_metadata["entity_types"])
        
        # Layer 2: Custom regex patterns
        masked_text, regex_metadata = self._apply_regex_patterns(masked_text, mask_format)
        
        # Update tracking metadata
        if regex_metadata["phi_detected"]:
            metadata["phi_detected"] = True
            metadata["entity_count"] += regex_metadata["entity_count"]
            metadata["entity_types"].update(regex_metadata["entity_types"])
        
        return masked_text, metadata
    
    async def _apply_comprehend_medical(
        self, 
        text: str, 
        mask_format: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply AWS Comprehend Medical for PHI detection.
        
        Args:
            text: Text to analyze
            mask_format: Format for masking
            
        Returns:
            Tuple of (masked_text, metadata)
        """
        try:
            response = self.comprehend_medical.detect_phi(Text=text)
            
            if not response.get('Entities'):
                return text, {"phi_detected": False, "entity_count": 0, "entity_types": {}}
            
            # Sort entities by beginning offset (descending) to avoid offset changes
            entities = sorted(
                response.get('Entities', []),
                key=lambda x: x['BeginOffset'],
                reverse=True
            )
            
            # Create a mutable copy of the text
            masked_text = text
            entity_types = {}
            
            # Replace each entity with a mask token
            for entity in entities:
                entity_type = entity['Type']
                begin = entity['BeginOffset']
                end = entity['EndOffset']
                
                # Track entity types
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1
                
                # Create appropriate mask token
                if mask_format == "token":
                    mask_token = f"[{entity_type}]"
                else:  # redaction
                    mask_token = "[REDACTED]"
                
                # Replace the entity with mask token
                masked_text = masked_text[:begin] + mask_token + masked_text[end:]
            
            return masked_text, {
                "phi_detected": True,
                "entity_count": len(entities),
                "entity_types": entity_types
            }
            
        except Exception as e:
            # Log error but do not expose PHI in logs
            logger.error(
                f"Error in Comprehend Medical PHI detection: {str(e)}",
                extra={
                    "error_type": type(e).__name__,
                    "service": "comprehend_medical"
                }
            )
            # If Comprehend fails, return original text and log warning
            return text, {"phi_detected": False, "entity_count": 0, "entity_types": {}}
    
    def _apply_regex_patterns(
        self, 
        text: str, 
        mask_format: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply custom regex patterns for additional PHI detection.
        
        Args:
            text: Text to analyze
            mask_format: Format for masking
            
        Returns:
            Tuple of (masked_text, metadata)
        """
        masked_text = text
        entity_count = 0
        entity_types = {}
        
        # Apply each pattern
        for entity_type, pattern in self.regex_patterns.items():
            # Find all matches
            matches = list(re.finditer(pattern, masked_text))
            
            # Process matches in reverse to preserve offsets
            for match in reversed(matches):
                entity_count += 1
                start, end = match.span()
                
                # Create appropriate mask token
                if mask_format == "token":
                    mask_token = f"[{entity_type}]"
                else:  # redaction
                    mask_token = "[REDACTED]"
                
                masked_text = masked_text[:start] + mask_token + masked_text[end:]
                
                # Track entity types
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1
        
        return masked_text, {
            "phi_detected": entity_count > 0,
            "entity_count": entity_count,
            "entity_types": entity_types
        }
```

### 4. Analysis Orchestrator Implementation

```python
# ml_microservices/core/services/analysis_orchestrator.py
import asyncio
import uuid
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ml_microservices.core.entities.analysis_request import AnalysisRequest
from ml_microservices.core.entities.analysis_result import AnalysisResult
from ml_microservices.core.entities.analysis_task import AnalysisTask
from ml_microservices.core.interfaces.analysis_service import AnalysisService
from ml_microservices.core.interfaces.result_storage import ResultStorage
from ml_microservices.core.interfaces.task_queue import TaskQueue
from ml_microservices.utils.logging.secure_logger import SecureLogger

logger = SecureLogger(__name__)

class AnalysisOrchestrator:
    """Orchestrates analysis tasks across multiple services."""
    
    def __init__(
        self,
        analysis_services: Dict[str, AnalysisService],
        result_storage: ResultStorage,
        task_queue: Optional[TaskQueue] = None
    ):
        """
        Initialize the analysis orchestrator.
        
        Args:
            analysis_services: Dictionary mapping analysis types to services
            result_storage: Storage service for analysis results
            task_queue: Optional queue for asynchronous processing
        """
        self.analysis_services = analysis_services
        self.result_storage = result_storage
        self.task_queue = task_queue
        
    async def process_request(
        self, 
        request: AnalysisRequest
    ) -> Union[AnalysisResult, str]:
        """
        Process an analysis request either synchronously or asynchronously.
        
        Args:
            request: Analysis request
            
        Returns:
            Analysis result or task ID for asynchronous processing
        """
        # Check if async processing is requested
        if request.processing_mode == "async" and self.task_queue is not None:
            # Create a task
            task_id = str(uuid.uuid4())
            task = AnalysisTask(
                task_id=task_id,
                request=request,
                status="queued",
                created_at=datetime.utcnow().isoformat()
            )
            
            # Queue the task
            await self.task_queue.enqueue(task)
            
            # Log task creation (without PHI)
            logger.info(
                f"Queued analysis task {task_id}",
                extra={
                    "task_id": task_id,
                    "analysis_type": request.analysis_type,
                    "processing_mode": "async"
                }
            )
            
            # Return the task ID
            return task_id
        else:
            # Process synchronously
            return await self._execute_analysis(request)
    
    async def process_task(self, task: AnalysisTask) -> None:
        """
        Process a queued analysis task.
        
        Args:
            task: Analysis task to process
        """
        try:
            # Update task status
            task.status = "processing"
            task.started_at = datetime.utcnow().isoformat()
            await self.task_queue.update(task)
            
            # Execute analysis
            result = await self._execute_analysis(task.request)
            
            # Store result
            result_id = await self.result_storage.store(result)
            
            # Update task status
            task.status = "completed"
            task.completed_at = datetime.utcnow().isoformat()
            task.result_id = result_id
            await self.task_queue.update(task)
            
            # Log completion (without PHI)
            logger.info(
                f"Completed analysis task {task.task_id}",
                extra={
                    "task_id": task.task_id,
                    "result_id": result_id,
                    "analysis_type": task.request.analysis_type
                }
            )
            
        except Exception as e:
            # Update task status on failure
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.utcnow().isoformat()
            await self.task_queue.update(task)
            
            # Log error (without PHI)
            logger.error(
                f"Failed analysis task {task.task_id}: {str(e)}",
                extra={
                    "task_id": task.task_id,
                    "analysis_type": task.request.analysis_type,
                    "error": str(e)
                }
            )
    
    async def _execute_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Execute analysis for a single request.
        
        Args:
            request: Analysis request
            
        Returns:
            Analysis result
        """
        # Get the appropriate service for the analysis type
        service = self.analysis_services.get(request.analysis_type)
        if not service:
            raise ValueError(f"Unsupported analysis type: {request.analysis_type}")
        
        # Execute analysis
        result = await service.analyze(request)
        
        # Store result if not async (async processing stores result after completion)
        if request.processing_mode != "async" and self.task_queue is not None:
            await self.result_storage.store(result)
        
        return result
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of an analysis task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status information
        """
        if self.task_queue is None:
            raise RuntimeError("Task queue not configured")
            
        task = await self.task_queue.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
            
        status_info = {
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at
        }
        
        if task.started_at:
            status_info["started_at"] = task.started_at
            
        if task.completed_at:
            status_info["completed_at"] = task.completed_at
            
        if task.result_id:
            status_info["result_id"] = task.result_id
            
        if task.error:
            status_info["error"] = task.error
            
        # Calculate progress if processing
        if task.status == "processing" and task.started_at:
            # Calculate estimated progress based on typical processing time
            start_time = datetime.fromisoformat(task.started_at)
            current_time = datetime.utcnow()
            elapsed_seconds = (current_time - start_time).total_seconds()
            
            # Assume average processing time of 30 seconds
            progress = min(int((elapsed_seconds / 30) * 100), 99)
            status_info["progress"] = progress
            
        return status_info
    
    async def get_result(self, result_id: str) -> AnalysisResult:
        """
        Get an analysis result.
        
        Args:
            result_id: Result ID
            
        Returns:
            Analysis result
        """
        result = await self.result_storage.retrieve(result_id)
        if not result:
            raise ValueError(f"Result not found: {result_id}")
            
        return result
        
    async def process_digital_twin_analysis(
        self, 
        request: AnalysisRequest
    ) -> Dict[str, Any]:
        """
        Process a comprehensive Digital Twin analysis with multiple analysis types.
        
        Args:
            request: Analysis request
            
        Returns:
            Digital Twin analysis result
        """
        # Extract the required analysis types
        analysis_types = request.parameters.get("analysis_types", [])
        if not analysis_types:
            raise ValueError("No analysis types specified for Digital Twin analysis")
            
        # Create individual requests for each analysis type
        individual_requests = []
        for analysis_type in analysis_types:
            individual_request = AnalysisRequest(
                analysis_type=analysis_type,
                text_content=request.text_content,
                parameters=request.parameters,
                processing_mode="sync"  # Force sync processing for sub-tasks
            )
            individual_requests.append(individual_request)
            
        # Process all requests concurrently
        tasks = [self._execute_analysis(req) for req in individual_requests]
        results = await asyncio.gather(*tasks)
        
        # Combine results into a comprehensive Digital Twin analysis
        combined_result = {
            "request_id": str(uuid.uuid4()),
            "patient_id": request.parameters.get("patient_id"),
            "analysis_types": analysis_types,
            "timestamp": datetime.utcnow().isoformat(),
            "results": {}
        }
        
        # Add individual results
        for result in results:
            combined_result["results"][result.analysis_type] = result.result
            
        # Add comprehensive insights
        combined_result["comprehensive_insights"] = self._generate_comprehensive_insights(results)
        
        # Store the combined result
        result_id = await self.result_storage.store(combined_result)
        combined_result["result_id"] = result_id
        
        return combined_result
    
    def _generate_comprehensive_insights(
        self, 
        results: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights from multiple analysis results.
        
        Args:
            results: List of individual analysis results
            
        Returns:
            Comprehensive insights
        """
        # This is a simple placeholder implementation
        # In a real implementation, this would integrate insights from different analyses
        # and potentially call another MentaLLaMA task to synthesize findings
        
        insights = {
            "summary": "Analysis complete across multiple dimensions.",
            "notable_patterns": [],
            "suggested_focus_areas": []
        }
        
        # Extract key findings from depression detection
        depression_result = next((r for r in results if r.analysis_type == "depression_detection"), None)
        if depression_result and depression_result.result.get("depression_indicated"):
            insights["notable_patterns"].append("Signs of depression detected")
            insights["suggested_focus_areas"].append("Mood assessment")
            
        # Extract key findings from risk assessment
        risk_result = next((r for r in results if r.analysis_type == "risk_assessment"), None)
        if risk_result and risk_result.result.get("risk_level") != "low":
            insights["notable_patterns"].append(f"{risk_result.result.get('risk_level', 'Elevated')} risk detected")
            insights["suggested_focus_areas"].append("Safety planning")
            
        # Extract key findings from sentiment analysis
        sentiment_result = next((r for r in results if r.analysis_type == "sentiment_analysis"), None)
        if sentiment_result:
            insights["notable_patterns"].append(
                f"Overall sentiment: {sentiment_result.result.get('overall_sentiment', 'mixed')}"
            )
            
        # Extract key findings from wellness dimensions
        wellness_result = next((r for r in results if r.analysis_type == "wellness_dimensions"), None)
        if wellness_result and wellness_result.result.get("areas_for_improvement"):
            for area in wellness_result.result.get("areas_for_improvement", [])[:2]:
                insights["suggested_focus_areas"].append(area)
                
        return insights
```

### 5. API Endpoint Implementation

```python
# ml_microservices/api/routes/mental_health.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
import json
import time

from ml_microservices.api.schemas.mental_health import (
    DepressionDetectionRequest,
    DepressionDetectionResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    WellnessDimensionsRequest,
    WellnessDimensionsResponse
)
from ml_microservices.core.entities.analysis_request import AnalysisRequest
from ml_microservices.core.services.analysis_orchestrator import AnalysisOrchestrator
from ml_microservices.security.authentication.token_validator import validate_token
from ml_microservices.utils.logging.secure_logger import SecureLogger

# Create router
router = APIRouter(prefix="/api/v1/ml/mental-health", tags=["mental-health"])
security = HTTPBearer()
logger = SecureLogger(__name__)

# Dependency to get the orchestrator
async def get_orchestrator():
    # In a real application, this would be injected from a factory or service container
    # Here we use a placeholder
    from ml_microservices.container import get_container
    container = get_container()
    return container.get(AnalysisOrchestrator)

# Dependency for authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    token = credentials.credentials
    user = await validate_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Depression Detection endpoint
@router.post("/depression-detection", response_model=DepressionDetectionResponse)
async def depression_detection(
    request: DepressionDetectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    """Analyze text for signs of depression."""
    # Check permissions
    if "clinician" not in current_user.get("roles", []) and "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not authorized to access this endpoint")
    
    # Measure processing time
    start_time = time.time()
    
    try:
        # Convert API request to domain request
        analysis_request = AnalysisRequest(
            analysis_type="depression_detection",
            text_content=request.text_content,
            parameters={
                "include_rationale": request.analysis_parameters.include_rationale,
                "severity_assessment": request.analysis_parameters.severity_assessment
            },
            processing_mode=request.processing_mode
        )
        
        # Process the request
        result = await orchestrator.process_request(analysis_request)
        
        # Handle async mode
        if request.processing_mode == "async":
            return DepressionDetectionResponse(
                request_id=result,  # task_id in this case
                status="processing",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Format the result for synchronous mode
        return DepressionDetectionResponse(
            request_id=result.request_id,
            status="completed",
            result=result.result,
            model_version=result.model_version,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    except Exception as e:
        # Log error (without PHI)
        logger.error(
            f"Error processing depression detection request: {str(e)}",
            extra={
                "user_id": current_user.get("sub"),
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail=str(e))

# Risk Assessment endpoint
@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def risk_assessment(
    request: RiskAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    """Evaluate text for potential self-harm or suicide risk."""
    # Check permissions
    if "clinician" not in current_user.get("roles", []) and "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not authorized to access this endpoint")
    
    # Measure processing time
    start_time = time.time()
    
    try:
        # Convert API request to domain request
        analysis_request = AnalysisRequest(
            analysis_type="risk_assessment",
            text_content=request.text_content,
            parameters={
                "include_key_phrases": request.analysis_parameters.include_key_phrases,
                "include_suggested_actions": request.analysis_parameters.include_suggested_actions
            },
            processing_mode=request.processing_mode
        )
        
        # Process the request
        result = await orchestrator.process_request(analysis_request)
        
        # Handle async mode
        if request.processing_mode == "async":
            return RiskAssessmentResponse(
                request_id=result,  # task_id in this case
                status="processing",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Format the result for synchronous mode
        return RiskAssessmentResponse(
            request_id=result.request_id,
            status="completed",
            result=result.result,
            model_version=result.model_version,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    except Exception as e:
        # Log error (without PHI)
        logger.error(
            f"Error processing risk assessment request: {str(e)}",
            extra={
                "user_id": current_user.get("sub"),
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail=str(e))

# Additional endpoints for sentiment_analysis and wellness_dimensions would follow the same pattern
```

## Deployment Configuration

### Docker Configuration

```dockerfile
# Dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04 as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TRANSFORMERS_CACHE=/app/.cache \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3.10-venv python3-pip \
    build-essential git curl wget \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app /app/.cache && \
    chown -R appuser:appuser /app

# Use the non-root user
USER appuser
WORKDIR /app

# Set up a virtual environment
ENV PATH="/app/venv/bin:$PATH"
RUN python3.10 -m venv /app/venv

# Install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create model directory
RUN mkdir -p /app/models

# Allow Hugging Face to cache models in the container
ENV HF_HOME=/app/.cache

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "ml_microservices.api.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Kubernetes Deployment

```yaml
# kubernetes/mentallama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mentallama-service
  namespace: ml-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mentallama-service
  template:
    metadata:
      labels:
        app: mentallama-service
    spec:
      securityContext:
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
        - name: mentallama
          image: ${ECR_REPO}/mentallama-service:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
          env:
            - name: MODEL_BASE_PATH
              value: "/app/models/vicuna-33b-v1.3"
            - name: LORA_ADAPTER_PATH
              value: "/app/models/mentallama-33b-lora"
            - name: AWS_REGION
              value: "us-east-1"
            - name: LOG_LEVEL
              value: "INFO"
            - name: PHI_DETECTION_ENABLED
              value: "true"
            - name: MERGE_LORA_WEIGHTS
              value: "false"
          resources:
            limits:
              nvidia.com/gpu: 1
              memory: "32Gi"
              cpu: "8"
            requests:
              nvidia.com/gpu: 1
              memory: "30Gi"
              cpu: "4"
          volumeMounts:
            - name: models-volume
              mountPath: /app/models
              readOnly: true
            - name: config-volume
              mountPath: /app/config
              readOnly: true
            - name: cache-volume
              mountPath: /app/.cache
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 300
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 300
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            capabilities:
              drop:
              - ALL
      volumes:
        - name: models-volume
          persistentVolumeClaim:
            claimName: mentallama-models-pvc
        - name: config-volume
          configMap:
            name: mentallama-config
        - name: cache-volume
          emptyDir: {}
      nodeSelector:
        accelerator: gpu
      tolerations:
        - key: "nvidia.com/gpu"
          operator: "Exists"
          effect: "NoSchedule"
---
apiVersion: v1
kind: Service
metadata:
  name: mentallama-service
  namespace: ml-services
spec:
  selector:
    app: mentallama-service
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mentallama-config
  namespace: ml-services
data:
  config.json: |
    {
      "generation_config": {
        "max_new_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.9,
        "do_sample": true
      },
      "phi_detection": {
        "use_comprehend_medical": true,
        "additional_patterns": {
          "CREDIT_CARD": "\\b(?:\\d{4}[- ]){3}\\d{4}\\b",
          "PASSPORT": "\\b[A-Z]{1,2}[0-9]{6,9}\\b"
        }
      }
    }
```

## Testing Approach

### Unit Testing

```python
# tests/unit/mentallama/test_model_loader.py
import pytest
from unittest.mock import patch, MagicMock, ANY
import torch

from ml_microservices.mentallama.inference.model_loader import MentaLLaMAModel

@pytest.fixture
def mock_tokenizer():
    tokenizer = MagicMock()
    tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]]), "attention_mask": torch.tensor([[1, 1, 1]])}
    tokenizer.decode.return_value = "Generated text response"
    return tokenizer

@pytest.fixture
def mock_model():
    model = MagicMock()
    model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    model.device = "cuda:0"
    return model

@pytest.fixture
def mock_peft_model():
    with patch("ml_microservices.mentallama.inference.model_loader.PeftModel") as mock:
        mock.from_pretrained.return_value = MagicMock()
        yield mock

@pytest.fixture
def mock_auto_tokenizer():
    with patch("ml_microservices.mentallama.inference.model_loader.AutoTokenizer") as mock:
        yield mock

@pytest.fixture
def mock_auto_model():
    with patch("ml_microservices.mentallama.inference.model_loader.AutoModelForCausalLM") as mock:
        yield mock

class TestMentaLLaMAModel:
    
    def test_initialization(self, mock_auto_tokenizer, mock_auto_model, mock_peft_model):
        """Test model initialization."""
        # Arrange
        base_model_path = "/path/to/base/model"
        lora_adapter_path = "/path/to/lora/adapter"
        
        # Act
        model = MentaLLaMAModel(base_model_path, lora_adapter_path)
        
        # Assert
        mock_auto_tokenizer.from_pretrained.assert_called_once_with(
            base_model_path,
            use_fast=False
        )
        mock_auto_model.from_pretrained.assert_called_once_with(
            base_model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True
        )
        mock_peft_model.from_pretrained.assert_called_once_with(
            mock_auto_model.from_pretrained.return_value,
            lora_adapter_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    def test_generate(self, mock_auto_tokenizer, mock_auto_model, mock_peft_model):
        """Test text generation."""
        # Arrange
        base_model_path = "/path/to/base/model"
        lora_adapter_path = "/path/to/lora/adapter"
        prompt = "Analyze this text for depression"
        
        # Set up mock tokenizer and model
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer.decode.return_value = prompt + " Generated response"
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
        
        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor([[4, 5, 6]])
        mock_model.device = torch.device("cuda:0")
        mock_peft_model.from_pretrained.return_value = mock_model
        
        # Act
        model = MentaLLaMAModel(base_model_path, lora_adapter_path)
        result = model.generate(prompt)
        
        # Assert
        mock_tokenizer.assert_called_once_with(prompt, return_tensors="pt")
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once_with(mock_model.generate.return_value[0], skip_special_tokens=True)
        assert result == " Generated response"  # Only the generated part (prompt removed)
    
    def test_initialization_error(self, mock_auto_tokenizer, mock_auto_model):
        """Test error handling during initialization."""
        # Arrange
        base_model_path = "/path/to/base/model"
        lora_adapter_path = "/path/to/lora/adapter"
        mock_auto_tokenizer.from_pretrained.side_effect = Exception("Model loading error")
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            MentaLLaMAModel(base_model_path, lora_adapter_path)
        
        assert "Failed to initialize MentaLLaMA model" in str(exc_info.value)
    
    def test_generation_with_custom_config(self, mock_auto_tokenizer, mock_auto_model, mock_peft_model):
        """Test generation with custom configuration."""
        # Arrange
        base_model_path = "/path/to/base/model"
        lora_adapter_path = "/path/to/lora/adapter"
        prompt = "Analyze this text for depression"
        generation_config = {
            "max_new_tokens": 100,
            "temperature": 0.8,
            "top_p": 0.95,
            "do_sample": True,
            "num_return_sequences": 1
        }
        
        # Set up mock tokenizer and model
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer.decode.return_value = prompt + " Generated custom response"
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
        
        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor([[4, 5, 6]])
        mock_model.device = torch.device("cuda:0")
        mock_peft_model.from_pretrained.return_value = mock_model
        
        # Act
        model = MentaLLaMAModel(base_model_path, lora_adapter_path)
        result = model.generate(prompt, generation_config)
        
        # Assert
        mock_tokenizer.assert_called_once_with(prompt, return_tensors="pt")
        mock_model.generate.assert_called_once()
        # Verify custom config was used
        args, kwargs = mock_model.generate.call_args
        for key, value in generation_config.items():
            assert kwargs.get(key) == value
            
        assert result == " Generated custom response"  # Only the generated part (prompt removed)
```

### Integration Testing

```python
# tests/integration/test_analysis_flow.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from ml_microservices.core.entities.analysis_request import AnalysisRequest
from ml_microservices.mentallama.service import MentaLLaMAService
from ml_microservices.phi_detection.service import AWSComprehendMedicalPHIDetection
from ml_microservices.core.services.analysis_orchestrator import AnalysisOrchestrator

@pytest.fixture
def mock_model():
    with patch("ml_microservices.mentallama.inference.model_loader.MentaLLaMAModel") as mock:
        model_instance = MagicMock()
        model_instance.generate.return_value = """
Depression Indicated: yes
Confidence: high
Rationale: The text contains multiple references to persistent low mood, sleep disturbance, and loss of interest in previously enjoyed activities, which are key indicators of depression.
Key Indicators: persistent low mood, sleep disturbance, loss of interest
"""
        mock.return_value = model_instance
        yield model_instance

@pytest.fixture
def mock_phi_detection():
    with patch("ml_microservices.phi_detection.service.AWSComprehendMedicalPHIDetection") as mock:
        service_instance = MagicMock()
        service_instance.detect_and_mask.return_value = (
            "Yesterday I told Dr. [NAME] at [LOCATION] that I've been feeling very sad for the past 3 weeks. I can't sleep well and don't enjoy activities anymore.",
            {"phi_detected": True, "entity_count": 2, "entity_types": {"NAME": 1, "LOCATION": 1}}
        )
        mock.return_value = service_instance
        yield service_instance

@pytest.fixture
def mock_result_storage():
    with patch("ml_microservices.infrastructure.storage.result_storage.S3ResultStorage") as mock:
        storage_instance = MagicMock()
        storage_instance.store.return_value = "result-id-123"
        storage_instance.retrieve.return_value = {"status": "completed", "result": {"depression_indicated": True}}
        mock.return_value = storage_instance
        yield storage_instance

@pytest.mark.asyncio
async def test_depression_detection_flow(mock_model, mock_phi_detection, mock_result_storage):
    """Test the entire depression detection analysis flow."""
    # Arrange
    # Create the necessary components
    text_preprocessor = MagicMock()
    text_preprocessor.preprocess.return_value = "Processed text"
    
    result_parser = MagicMock()
    result_parser.parse.return_value = {
        "depression_indicated": True,
        "confidence": "high",
        "severity": "moderate",
        "rationale": "The text contains multiple references to persistent low mood, sleep disturbance, and loss of interest in previously enjoyed activities, which are key indicators of depression.",
        "key_indicators": [
            "persistent low mood",
            "sleep disturbance",
            "loss of interest"
        ]
    }
    
    result_encryptor = MagicMock()
    result_encryptor.encrypt.side_effect = lambda x: x  # Just return the input
    
    # Create the MentaLLaMA service
    mentallama_service = MentaLLaMAService(
        model=mock_model,
        phi_service=mock_phi_detection,
        text_preprocessor=text_preprocessor,
        result_parser=result_parser,
        result_encryptor=result_encryptor
    )
    
    # Create analysis services dictionary
    analysis_services = {
        "depression_detection": mentallama_service
    }
    
    # Create the analysis orchestrator
    orchestrator = AnalysisOrchestrator(
        analysis_services=analysis_services,
        result_storage=mock_result_storage
    )
    
    # Create the analysis request
    request = AnalysisRequest(
        analysis_type="depression_detection",
        text_content="Yesterday I told Dr. Smith at Chicago Memorial that I've been feeling very sad for the past 3 weeks. I can't sleep well and don't enjoy activities anymore.",
        parameters={
            "include_rationale": True,
            "severity_assessment": True
        },
        processing_mode="sync"
    )
    
    # Act
    result = await orchestrator.process_request(request)
    
    # Assert
    # Verify PHI detection was called
    mock_phi_detection.detect_and_mask.assert_called_once()
    
    # Verify text preprocessing
    text_preprocessor.preprocess.assert_called_once()
    
    # Verify model generation
    mock_model.generate.assert_called_once()
    
    # Verify result parsing
    result_parser.parse.assert_called_once()
    
    # Verify result storage
    mock_result_storage.store.assert_called_once()
    
    # Verify the final result
    assert result.analysis_type == "depression_detection"
    assert result.result["depression_indicated"] is True
    assert result.result["confidence"] == "high"
    assert result.result["severity"] == "moderate"
    assert len(result.result["key_indicators"]) == 3
```

### End-to-End Testing

```python
# tests/e2e/test_api_endpoints.py
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from ml_microservices.api.main import app
from ml_microservices.core.services.analysis_orchestrator import AnalysisOrchestrator

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_orchestrator():
    with patch.object(app, "dependency_overrides", {}) as dependency_overrides:
        orchestrator = MagicMock(spec=AnalysisOrchestrator)
        
        async def get_mock_orchestrator():
            return orchestrator
        
        dependency_overrides[app.dependency_overrides["get_orchestrator"]] = get_mock_orchestrator
        yield orchestrator

@pytest.fixture
def mock_token_validator():
    with patch("ml_microservices.security.authentication.token_validator.validate_token") as mock:
        mock.return_value = {
            "sub": "user-123",
            "roles": ["clinician"],
            "exp": 9999999999
        }
        yield mock

def test_depression_detection_sync(client, mock_orchestrator, mock_token_validator):
    """Test the depression detection endpoint in synchronous mode."""
    # Arrange
    mock_orchestrator.process_request.return_value = {
        "request_id": "request-123",
        "status": "completed",
        "result": {
            "depression_indicated": True,
            "confidence": "high",
            "severity": "moderate",
            "rationale": "The text contains multiple references to persistent low mood, sleep disturbance, and loss of interest in previously enjoyed activities, which are key indicators of depression.",
            "key_indicators": [
                "persistent low mood",
                "sleep disturbance",
                "loss of interest"
            ]
        },
        "model_version": "MentaLLaMA-33B-lora-v1.0"
    }
    
    request_data = {
        "text_content": "I've been feeling very sad for the past 3 weeks. I can't sleep well and don't enjoy activities anymore.",
        "analysis_parameters": {
            "include_rationale": True,
            "severity_assessment": True
        },
        "processing_mode": "sync"
    }
    
    # Act
    response = client.post(
        "/api/v1/ml/mental-health/depression-detection",
        json=request_data,
        headers={"Authorization": "Bearer token123"}
    )
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert result["result"]["depression_indicated"] is True
    assert result["result"]["confidence"] == "high"
    assert result["result"]["severity"] == "moderate"
    assert len(result["result"]["key_indicators"]) == 3
    assert result["model_version"] == "MentaLLaMA-33B-lora-v1.0"
    assert "processing_time_ms" in result

def test_depression_detection_async(client, mock_orchestrator, mock_token_validator):
    """Test the depression detection endpoint in asynchronous mode."""
    # Arrange
    mock_orchestrator.process_request.return_value = "task-123"
    
    request_data = {
        "text_content": "I've been feeling very sad for the past 3 weeks. I can't sleep well and don't enjoy activities anymore.",
        "analysis_parameters": {
            "include_rationale": True,
            "severity_assessment": True
        },
        "processing_mode": "async"
    }
    
    # Act
    response = client.post(
        "/api/v1/ml/mental-health/depression-detection",
        json=request_data,
        headers={"Authorization": "Bearer token123"}
    )
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "processing"
    assert result["request_id"] == "task-123"
    assert "processing_time_ms" in result

def test_depression_detection_unauthorized(client, mock_token_validator):
    """Test the depression detection endpoint with unauthorized user."""
    # Arrange
    mock_token_validator.return_value = {
        "sub": "user-123",
        "roles": ["patient"],  # Not a clinician
        "exp": 9999999999
    }
    
    request_data = {
        "text_content": "I've been feeling very sad for the past 3 weeks.",
        "analysis_parameters": {
            "include_rationale": True,
            "severity_assessment": True
        },
        "processing_mode": "sync"
    }
    
    # Act
    response = client.post(
        "/api/v1/ml/mental-health/depression-detection",
        json=request_data,
        headers={"Authorization": "Bearer token123"}
    )
    
    # Assert
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

def test_depression_detection_invalid_token(client, mock_token_validator):
    """Test the depression detection endpoint with invalid token."""
    # Arrange
    mock_token_validator.return_value = None  # Invalid token
    
    request_data = {
        "text_content": "I've been feeling very sad for the past 3 weeks.",
        "analysis_parameters": {
            "include_rationale": True,
            "severity_assessment": True
        },
        "processing_mode": "sync"
    }
    
    # Act
    response = client.post(
        "/api/v1/ml/mental-health/depression-detection",
        json=request_data,
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    # Assert
    assert response.status_code == 401
    assert "Invalid authentication" in response.json()["detail"]
```

## Security and HIPAA Compliance

### Security Measures

1. **Authentication and Authorization**
   - JWT-based authentication with AWS Cognito
   - Role-based access control (clinician, admin, patient)
   - Token validation and refresh

2. **Data Protection**
   - PHI detection and masking before analysis
   - Encryption of data at rest using AWS KMS
   - TLS 1.3 for data in transit

3. **Logging and Auditing**
   - Secure logging without PHI
   - Comprehensive audit trails
   - Activity monitoring and alerting

4. **Container Security**
   - Non-root user for container execution
   - Limited capabilities
   - Immutable containers

5. **Network Security**
   - Private networking
   - Network policies
   - API Gateway with WAF protection

### HIPAA Compliance Considerations

1. **BAA Requirements**
   - AWS BAA for all used services
   - Vendor BAAs for third-party components

2. **Minimum Necessary Principle**
   - Only collect and process required data
   - PHI detection and masking
   - Time-limited data retention

3. **Access Controls**
   - Role-based permissions
   - Audit logging
   - Multi-factor authentication

4. **Breach Notification**
   - Monitoring and alerting
   - Incident response procedures
   - Documentation requirements

## Performance Optimization

### Model Optimization Techniques

1. **Quantization**
   - 8-bit quantization for inference
   - Reduced memory footprint
   - Faster inference speed

2. **Batching**
   - Process multiple requests in batches
   - Optimize GPU utilization
   - Reduce per-request overhead

3. **Caching**
   - Cache common prompts and responses
   - Redis for result caching
   - Expiration policies for data freshness

4. **GPU Resource Management**
   - Multi-model loading
   - Dynamic scaling
   - Memory optimization

### Scaling Strategies

1. **Horizontal Scaling**
   - Auto-scaling based on queue depth
   - Kubernetes HPA configuration
   - Resource-based scaling triggers

2. **Vertical Scaling**
   - GPU instance selection
   - Memory optimization
   - CPU allocation

3. **Asynchronous Processing**
   - Queue-based processing
   - Background tasks
   - Result polling or webhook notifications

## Conclusion

This implementation guide provides a comprehensive blueprint for integrating MentaLLaMA-33B-lora into the NOVAMIND platform. By following the provided code patterns, deployment configurations, and security practices, teams can build a robust, HIPAA-compliant mental health analysis service that enhances clinical care while maintaining the highest standards of privacy and security.

Key takeaways:

1. **Clean Architecture**: Strict separation of concerns with domain-driven design
2. **Security First**: PHI protection and HIPAA compliance at every layer
3. **Performance Optimization**: Techniques for efficient model usage
4. **Scalability**: Deployment patterns for handling variable workloads
5. **Testing**: Comprehensive test coverage across all layers

For additional details, refer to the companion documents:
- [MentaLLaMA Mental Health Modeling](./MentalLLaMA/01_MENTAL_HEALTH_MODELING.md)
- [MentaLLaMA AWS Deployment & HIPAA Compliance](./MentalLLaMA/02_AWS_DEPLOYMENT_HIPAA.md)
- [MentaLLaMA Clinical Implementation](./MentalLLaMA/03_CLINICAL_IMPLEMENTATION.md)