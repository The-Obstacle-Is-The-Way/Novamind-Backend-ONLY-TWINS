# NOVAMIND DIGITAL TWIN: MENTALLLAMA IMPLEMENTATION

## Overview

This document provides the technical implementation guide for NOVAMIND's AI-powered Digital Twin functionality, leveraging the **MentaLLaMA-33B-lora** model for interpretable mental health analysis. This implementation follows Clean Architecture principles, ensuring separation of concerns, maintainability, and strict HIPAA compliance while delivering a luxury concierge psychiatry experience.

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [MentaLLaMA Model Implementation](#mentalllama-model-implementation)
3. [Core Components Implementation](#core-components-implementation)
4. [PHI Protection Pipeline](#phi-protection-pipeline)
5. [Deployment Architecture](#deployment-architecture)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Testing Strategy](#testing-strategy)
8. [Error Handling](#error-handling)
9. [Configuration Management](#configuration-management)
10. [Security and HIPAA Compliance](#security-and-hipaa-compliance)
11. [Implementation Roadmap](#implementation-roadmap)

## Architecture Principles

### Clean Architecture

The ML implementation strictly adheres to Clean Architecture principles:

1. **Domain Layer Independence**: Contains business rules and entities (e.g., `AnalysisResult`, `RiskLevel`), with no dependencies on specific ML models or infrastructure. Defines interfaces for analysis services.
2. **Dependency Rule**: Dependencies point inward. Infrastructure (model adapters) depends on domain interfaces, never the reverse.
3. **Interface Segregation**: Domain interfaces define contracts (e.g., `MentalHealthAnalysisService` interface).
4. **Separation of Concerns**: The core application logic is separate from the ML model loading and inference details.

### Layer Responsibilities

- **Domain Layer**:
  - Defines pure interfaces like `MentalHealthAnalysisService` 
  - Contains value objects for analysis results (`MentalHealthAnalysisResult`, `RiskAssessmentResult`)
  - Includes domain-specific exceptions (e.g., `AnalysisError`)
  - No external dependencies or framework references

- **Application Layer**:
  - Implements use cases (e.g., `AnalyzePatientJournalUseCase`) using domain interfaces
  - Orchestrates PHI removal, prompt construction, adapter calls, and result processing
  - Converts infrastructure-level data to domain objects
  - Handles business logic around analysis results

- **Infrastructure Layer**:
  - Contains `MentaLLaMAAdapter` implementing domain interfaces
  - Manages model loading using `transformers`/`peft`
  - Handles GPU resource access and optimizations
  - Implements PHI detection services and external API clients

- **Presentation Layer**:
  - FastAPI endpoints receiving analysis requests
  - Pydantic schemas for input/output validation
  - Uses `Depends()` for dependency injection of application services
  - Handles authentication and authorization

### HIPAA Compliance Architecture

The architecture implements these critical HIPAA safeguards:

1. **PHI Sanitization**: All text data has PHI removed/masked *before* being sent to the MentaLLaMA model through a multi-layered detection system.
2. **Secure Logging**: No PHI in logs. Log analysis request metadata only (e.g., analysis type, timestamp).
3. **Data Encryption**: All data encrypted at rest (KMS) and in transit (TLS).
4. **Access Controls**: Role-based access control for all analysis endpoints.
5. **Audit Trails**: Comprehensive logging of all operations, excluding PHI.

## MentaLLaMA Model Implementation

### Technical Stack

The MentaLLaMA implementation requires:

1. **Core Libraries**:
   - `torch>=2.0.0`: PyTorch with CUDA support
   - `transformers>=4.28.0`: Hugging Face Transformers
   - `peft>=0.4.0`: Parameter-Efficient Fine-Tuning
   - `accelerate>=0.20.0`: For device management and optimization
   - `bitsandbytes>=0.39.0`: For model quantization (optional)
   - `safetensors>=0.3.1`: For secure model loading

2. **Hardware Requirements**:
   - GPU: NVIDIA V100/A100 with at least 16GB VRAM (for 8-bit quantization)
   - CPU: 8+ cores
   - RAM: 32GB+ system memory

3. **Model Assets**:
   - Base Vicuna-33B model (Hugging Face format)
   - MentaLLaMA-33B-lora adapter weights

### Model Loading Implementation

```python
# app/infrastructure/ml/mentalllama_adapter.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from bitsandbytes.nn import Linear8bitLt
from app.core.config import settings
from app.core.utils.logging import logger
from app.domain.interfaces.ml_service import MentalHealthAnalysisService
from app.domain.entities.analysis_result import MentalHealthAnalysisResult
from app.domain.exceptions import ModelLoadingError, ModelInferenceError


class MentaLLaMAModelLoader:
    """Responsible for loading and initializing the MentaLLaMA model."""
    
    @staticmethod
    def load_model(
        base_path: str, 
        lora_path: str, 
        quantization: str = "none",
        device_map: str = "auto"
    ):
        """
        Loads the MentaLLaMA model with appropriate optimizations.
        
        Args:
            base_path: Path to base Vicuna model
            lora_path: Path to MentaLLaMA LoRA weights
            quantization: Quantization level ("none", "8bit", "4bit")
            device_map: Device mapping strategy
            
        Returns:
            Tuple of (tokenizer, model)
            
        Raises:
            ModelLoadingError: If model loading fails
        """
        try:
            logger.info(f"Loading MentaLLaMA model: base='{base_path}', lora='{lora_path}'")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                base_path, 
                use_fast=False,
                trust_remote_code=True
            )
            
            # Configure model loading parameters
            load_kwargs = {
                "device_map": device_map,
                "trust_remote_code": True,
            }
            
            # Add quantization if requested
            if quantization == "8bit":
                load_kwargs["load_in_8bit"] = True
                logger.info("Using 8-bit quantization")
            elif quantization == "4bit":
                load_kwargs["load_in_4bit"] = True
                load_kwargs["bnb_4bit_compute_dtype"] = torch.float16
                load_kwargs["bnb_4bit_quant_type"] = "nf4"
                logger.info("Using 4-bit quantization")
            else:
                load_kwargs["torch_dtype"] = torch.float16
                logger.info("Using FP16 precision (no quantization)")
            
            # Load base model
            base_model = AutoModelForCausalLM.from_pretrained(
                base_path,
                **load_kwargs
            )
            logger.info("Base Vicuna model loaded successfully")
            
            # Load LoRA weights using PEFT
            model = PeftModel.from_pretrained(
                base_model, 
                lora_path,
                is_trainable=False
            )
            logger.info("LoRA weights applied successfully")
            
            # Set model to evaluation mode
            model.eval()
            
            return tokenizer, model
            
        except Exception as e:
            logger.error(f"Failed to load MentaLLaMA model: {e}", exc_info=True)
            raise ModelLoadingError(f"MentaLLaMA model initialization failed: {e}")
```

### Model Adapter Implementation

```python
# app/infrastructure/ml/mentalllama_adapter.py (continued)

class MentaLLaMAAdapter(MentalHealthAnalysisService):
    """Adapter for interacting with the MentaLLaMA-33B-lora model."""

    def __init__(self, model_loader=None):
        """
        Initialize the MentaLLaMA adapter.
        
        Args:
            model_loader: Optional custom model loader (for testing/dependency injection)
        """
        self.tokenizer = None
        self.model = None
        self.model_loader = model_loader or MentaLLaMAModelLoader()
        self._load_model()
        
    def _load_model(self):
        """Loads the MentaLLaMA model using the model loader."""
        try:
            self.tokenizer, self.model = self.model_loader.load_model(
                base_path=settings.VICUNA_33B_PATH,
                lora_path=settings.MENTALLAMA_LORA_PATH,
                quantization=settings.MENTALLAMA_QUANTIZATION
            )
        except Exception as e:
            logger.error(f"Failed to load MentaLLaMA model: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None
            raise ModelLoadingError(f"MentaLLaMA model initialization failed: {e}")

    async def analyze_text(
        self, 
        prompt: str, 
        max_new_tokens: int = 256, 
        temperature: float = 0.7, 
        top_p: float = 0.9
    ) -> str:
        """
        Generates analysis based on the provided prompt.
        
        Args:
            prompt: The text prompt for analysis
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated text response
        
        Raises:
            ModelInferenceError: If inference fails
        """
        if not self.model or not self.tokenizer:
            logger.error("MentaLLaMA model not loaded, cannot perform analysis")
            raise ModelInferenceError("MentaLLaMA model not loaded")

        # Log with length only, no content (PHI protection)
        logger.debug(f"Received analysis prompt (length: {len(prompt)})")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate response
            with torch.no_grad():
                output_tokens = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # Decode only the generated part, not the input prompt
            generated_text = self.tokenizer.decode(
                output_tokens[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            # Log length only, not content (PHI protection)
            logger.debug(f"MentaLLaMA raw output (length: {len(generated_text)})")
            return generated_text.strip()

        except Exception as e:
            logger.error(f"Error during MentaLLaMA inference: {e}", exc_info=True)
            raise ModelInferenceError(f"Failed to generate analysis: {e}")
```

## Core Components Implementation

### MentalHealthAnalyzerService

```python
# app/application/services/mental_health_analyzer.py

from typing import Dict, Any, Optional
from uuid import UUID
from app.domain.interfaces.ml_service import MentalHealthAnalysisService
from app.domain.interfaces.phi_service import PhiDetectionService
from app.domain.entities.analysis_result import MentalHealthAnalysisResult
from app.domain.exceptions import AnalysisError, PhiDetectionError
from app.domain.entities.analysis_types import AnalysisType, RiskLevel
from app.core.utils.logging import logger


class MentalHealthAnalyzerService:
    """
    Service for performing mental health analysis using MentaLLaMA.
    
    This is an application service that combines PHI detection/removal
    with MentaLLaMA analysis to provide HIPAA-compliant mental health insights.
    """

    def __init__(
        self, 
        analysis_service: MentalHealthAnalysisService,
        phi_detection_service: PhiDetectionService,
    ):
        """
        Initialize the mental health analyzer service.
        
        Args:
            analysis_service: Service for ML analysis
            phi_detection_service: Service for PHI detection and removal
        """
        self.analysis_service = analysis_service
        self.phi_service = phi_detection_service
        self.prompt_templates = self._initialize_prompt_templates()
        
    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """Initialize prompt templates for different analysis types."""
        return {
            AnalysisType.RISK_ASSESSMENT: (
                "You are a mental health professional assessing potential risk.\n\n"
                "Consider this text: \"{text}\"\n\n"
                "Question: Does the author show signs of suicide or self-harm risk? "
                "Provide your assessment as risk_level (low, medium, high) and explain your reasoning.\n\n"
                "Format your response as:\n"
                "Risk Level: [low/medium/high]\n"
                "Rationale: [Your detailed explanation]\n"
                "Key Indicators: [Specific concerning phrases or themes]"
            ),
            AnalysisType.DEPRESSION_DETECTION: (
                "You are a mental health professional specializing in depression assessment.\n\n"
                "Consider this text: \"{text}\"\n\n"
                "Question: Does the author show signs of depression? "
                "Analyze the text, indicate whether depression is likely present, and provide your reasoning.\n\n"
                "Format your response as:\n"
                "Depression Indicated: [yes/no/possible]\n"
                "Confidence: [high/medium/low]\n"
                "Rationale: [Your detailed explanation]\n"
                "Key Indicators: [Specific phrases or themes that support your assessment]"
            ),
            AnalysisType.SENTIMENT_ANALYSIS: (
                "You are a mental health professional analyzing emotional sentiment.\n\n"
                "Consider this text: \"{text}\"\n\n"
                "Question: What is the emotional sentiment expressed in this text? "
                "Analyze as positive, negative, neutral or mixed and explain your reasoning.\n\n"
                "Format your response as:\n"
                "Sentiment: [positive/negative/neutral/mixed]\n"
                "Rationale: [Your detailed explanation]\n"
                "Emotional Themes: [Key emotional themes identified]"
            ),
        }
        
    def _construct_prompt(self, analysis_type: str, sanitized_text: str) -> str:
        """
        Constructs appropriate prompt based on analysis type.
        
        Args:
            analysis_type: Type of analysis to perform
            sanitized_text: PHI-free text to analyze
            
        Returns:
            Formatted prompt for the specified analysis type
            
        Raises:
            ValueError: If analysis_type is not supported
        """
        prompt_template = self.prompt_templates.get(analysis_type)
        if not prompt_template:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
        return prompt_template.format(text=sanitized_text)
    
    def _parse_risk_assessment(self, raw_output: str) -> Dict[str, Any]:
        """Parse risk assessment output into structured format."""
        result = {"risk_level": "unknown", "rationale": "", "key_indicators": []}
        
        # Extract risk level
        if "risk level:" in raw_output.lower():
            risk_level_line = [line for line in raw_output.lower().split('\n') 
                              if "risk level:" in line][0]
            if "low" in risk_level_line:
                result["risk_level"] = RiskLevel.LOW
            elif "medium" in risk_level_line:
                result["risk_level"] = RiskLevel.MEDIUM
            elif "high" in risk_level_line:
                result["risk_level"] = RiskLevel.HIGH
        
        # Extract rationale
        if "rationale:" in raw_output.lower():
            rationale_sections = raw_output.lower().split("rationale:")
            if len(rationale_sections) > 1:
                rationale_text = rationale_sections[1].split("key indicators:")[0].strip()
                result["rationale"] = rationale_text
        
        # Extract key indicators
        if "key indicators:" in raw_output.lower():
            indicators_section = raw_output.lower().split("key indicators:")[1].strip()
            # Split by newlines or commas to get individual indicators
            indicators = [i.strip() for i in indicators_section.replace('\n', ',').split(',')]
            result["key_indicators"] = [i for i in indicators if i]
        
        return result
        
    def _parse_result(self, analysis_type: str, raw_output: str) -> Dict[str, Any]:
        """
        Parse the model output into a structured result.
        
        Args:
            analysis_type: Type of analysis performed
            raw_output: Raw text output from the model
            
        Returns:
            Dictionary with structured analysis results
            
        Raises:
            AnalysisError: If parsing fails
        """
        try:
            if analysis_type == AnalysisType.RISK_ASSESSMENT:
                return self._parse_risk_assessment(raw_output)
            
            # Handle other analysis types similarly
            # Default fallback - return raw output
            return {"analysis": raw_output.strip()}
            
        except Exception as e:
            logger.error(f"Error parsing MentaLLaMA output: {e}", exc_info=True)
            raise AnalysisError(f"Failed to parse analysis result: {e}")

    async def perform_analysis(
        self, 
        patient_id: UUID,
        text_content: str, 
        analysis_type: str,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> MentalHealthAnalysisResult:
        """
        Performs mental health analysis on the provided text.
        
        Args:
            patient_id: UUID of the patient (for audit tracking only)
            text_content: The text to analyze (will be sanitized of PHI)
            analysis_type: Type of analysis to perform
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for text generation
            
        Returns:
            MentalHealthAnalysisResult containing the structured analysis
            
        Raises:
            PhiDetectionError: If PHI detection fails
            AnalysisError: If analysis generation or parsing fails
            ValueError: If analysis_type is not supported
        """
        # Log operation start (without PHI)
        logger.info(f"Starting mental health analysis (type: {analysis_type}, patient_id: {patient_id})")
        
        # 1. Remove PHI from text - CRITICAL HIPAA STEP
        try:
            sanitized_text = await self.phi_service.detect_and_mask_phi(text_content)
            logger.info(f"PHI detection completed for analysis request (type: {analysis_type})")
        except Exception as e:
            logger.error(f"PHI detection failed: {e}", exc_info=True)
            raise PhiDetectionError("Failed to perform PHI detection and masking") from e
        
        # 2. Construct appropriate prompt
        prompt = self._construct_prompt(analysis_type, sanitized_text)
        
        # 3. Call MentaLLaMA adapter for inference
        try:
            raw_output = await self.analysis_service.analyze_text(
                prompt=prompt,
                max_new_tokens=max_tokens,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"MentaLLaMA analysis failed: {e}", exc_info=True)
            raise AnalysisError(f"Failed to generate analysis: {e}") from e
        
        # 4. Parse and structure the result
        parsed_result = self._parse_result(analysis_type, raw_output)
        
        # 5. Create domain entity
        result = MentalHealthAnalysisResult(
            patient_id=patient_id,
            analysis_type=analysis_type,
            result=parsed_result,
            model_version=settings.MENTALLAMA_MODEL_VERSION,
        )
        
        logger.info(f"Completed mental health analysis for patient {patient_id}")
        return result
```

### API Endpoint Implementation

```python
# app/presentation/api/endpoints/mental_health_analysis.py

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.schemas.mental_health import (
    MentalHealthAnalysisRequest, 
    MentalHealthAnalysisResponse
)
from app.application.services.mental_health_analyzer import MentalHealthAnalyzerService
from app.core.dependencies import get_mental_health_analyzer, get_current_clinician
from app.domain.exceptions import AnalysisError, PhiDetectionError
from app.core.utils.logging import logger

router = APIRouter()

@router.post(
    "/{patient_id}/mental-health-analysis",
    response_model=MentalHealthAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform mental health analysis on patient text",
    description="Analyzes patient text for mental health indicators using MentaLLaMA. "
                "PHI is automatically detected and removed before analysis."
)
async def analyze_mental_health(
    patient_id: UUID,
    request: MentalHealthAnalysisRequest,
    analyzer_service: MentalHealthAnalyzerService = Depends(get_mental_health_analyzer),
    clinician = Depends(get_current_clinician)  # Ensures only clinicians can access
):
    """
    Endpoint for mental health analysis of patient text.
    
    Args:
        patient_id: UUID of the patient
        request: Analysis request with text content and parameters
        analyzer_service: Injected analyzer service
        clinician: Current authenticated clinician user
        
    Returns:
        Analysis results
        
    Raises:
        HTTPException: On analysis error or permission issues
    """
    try:
        # Check permissions - ensure clinician has access to this patient
        # Implementation would depend on your authorization system
        
        # Call analyzer service
        result = await analyzer_service.perform_analysis(
            patient_id=patient_id,
            text_content=request.text_content,
            analysis_type=request.analysis_type,
            max_tokens=request.generation_params.max_tokens,
            temperature=request.generation_params.temperature
        )
        
        # Return formatted response
        return MentalHealthAnalysisResponse(
            success=True,
            data={
                "patient_id": str(result.patient_id),
                "analysis_type": result.analysis_type,
                "result": result.result,
                "model_version": result.model_version,
                "generated_at": result.timestamp.isoformat()
            },
            error=None
        )
        
    except PhiDetectionError as e:
        logger.error(f"PHI detection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process text due to PHI detection issues"
        )
        
    except AnalysisError as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate mental health analysis"
        )
        
    except ValueError as e:
        logger.error(f"Invalid analysis parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in mental health analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during analysis"
        )
```

### PYDANTIC SCHEMAS

```python
# app/presentation/schemas/mental_health.py

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class GenerationParameters(BaseModel):
    """Parameters for controlling text generation."""
    
    max_tokens: int = Field(
        default=256,
        ge=1,
        le=1024,
        description="Maximum number of tokens to generate"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="Temperature for controlling randomness (higher = more random)"
    )
    top_p: Optional[float] = Field(
        default=0.9,
        ge=0.1,
        le=1.0,
        description="Nucleus sampling parameter"
    )


class MentalHealthAnalysisRequest(BaseModel):
    """Request schema for mental health analysis."""
    
    text_content: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Text content to analyze (will be sanitized of PHI)"
    )
    analysis_type: str = Field(
        ...,
        description="Type of analysis to perform (e.g., risk_assessment, sentiment_analysis)"
    )
    generation_params: GenerationParameters = Field(
        default_factory=GenerationParameters,
        description="Parameters for controlling response generation"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "text_content": "Patient text to analyze...",
                "analysis_type": "risk_assessment", 
                "generation_params": {
                    "max_tokens": 256,
                    "temperature": 0.7
                }
            }
        }


class MentalHealthAnalysisResponse(BaseModel):
    """Response schema for mental health analysis."""
    
    success: bool = Field(
        ..., 
        description="Whether the analysis was successful"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Analysis results when successful"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if analysis failed"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                    "analysis_type": "risk_assessment",
                    "result": {
                        "risk_level": "medium",
                        "rationale": "The text mentions feelings of hopelessness and social withdrawal, consistent with moderate risk indicators. No explicit suicidal ideation mentioned.",
                        "key_indicators": [
                            "feelings of hopelessness",
                            "social withdrawal",
                            "sleep disturbance"
                        ]
                    },
                    "model_version": "klyang/MentaLLaMA-33B-lora_v1.0",
                    "generated_at": "2025-03-28T01:05:00Z"
                },
                "error": None
            }
        }
```

### Domain Layer Interfaces and Entities

```python
# app/domain/interfaces/ml_service.py

from abc import ABC, abstractmethod


class MentalHealthAnalysisService(ABC):
    """Interface for mental health analysis services."""
    
    @abstractmethod
    async def analyze_text(
        self, 
        prompt: str, 
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        Analyze text and generate response based on prompt.
        
        Args:
            prompt: Formatted prompt for analysis
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated text response
        """
        pass


# app/domain/interfaces/phi_service.py

from abc import ABC, abstractmethod


class PhiDetectionService(ABC):
    """Interface for PHI detection and masking services."""
    
    @abstractmethod
    async def detect_and_mask_phi(self, text: str) -> str:
        """
        Detect and mask Protected Health Information in text.
        
        Args:
            text: Text that may contain PHI
            
        Returns:
            Text with PHI replaced by mask tokens
        """
        pass


# app/domain/entities/analysis_result.py

from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional


class MentalHealthAnalysisResult:
    """Entity representing a mental health analysis result."""
    
    def __init__(
        self,
        patient_id: UUID,
        analysis_type: str,
        result: Dict[str, Any],
        model_version: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize a mental health analysis result.
        
        Args:
            patient_id: UUID of the patient
            analysis_type: Type of analysis performed
            result: Structured analysis result
            model_version: Version identifier of the model used
            timestamp: When the analysis was generated (defaults to now)
        """
        self.patient_id = patient_id
        self.analysis_type = analysis_type
        self.result = result
        self.model_version = model_version
        self.timestamp = timestamp or datetime.utcnow()


# app/domain/entities/analysis_types.py

class AnalysisType:
    """Constants for supported analysis types."""
    RISK_ASSESSMENT = "risk_assessment"
    DEPRESSION_DETECTION = "depression_detection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    STRESS_DETECTION = "stress_detection"
    WELLNESS_DIMENSIONS = "wellness_dimensions"


class RiskLevel:
    """Constants for risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# app/domain/exceptions.py

class DigitalTwinError(Exception):
    """Base exception for Digital Twin related errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AnalysisError(DigitalTwinError):
    """Exception raised when analysis generation fails."""
    pass


class PhiDetectionError(DigitalTwinError):
    """Exception raised when PHI detection and masking fails."""
    pass


class ModelLoadingError(DigitalTwinError):
    """Exception raised when model loading fails."""
    pass


class ModelInferenceError(DigitalTwinError):
    """Exception raised during model inference."""
    pass


class ResultParsingError(DigitalTwinError):
    """Exception raised when parsing model output fails."""
    pass
```

## PHI Protection Pipeline

### AWS Comprehend Medical Implementation

```python
# app/infrastructure/services/phi_detection_service.py

import boto3
from typing import List, Dict, Any
import re
from app.domain.interfaces.phi_service import PhiDetectionService
from app.domain.exceptions import PhiDetectionError
from app.core.config import settings
from app.core.utils.logging import logger


class AwsComprehendMedicalPhiService(PhiDetectionService):
    """PHI detection service using AWS Comprehend Medical."""
    
    def __init__(self):
        """Initialize AWS Comprehend Medical client."""
        self.client = boto3.client(
            'comprehendmedical',
            region_name=settings.AWS_COMPREHEND_REGION
        )
        logger.info(f"AWS Comprehend Medical PHI detection service initialized (region: {settings.AWS_COMPREHEND_REGION})")
    
    async def detect_and_mask_phi(self, text: str) -> str:
        """
        Detect PHI using AWS Comprehend Medical and replace with mask tokens.
        
        Args:
            text: The text to scan for PHI
            
        Returns:
            Text with PHI masked
            
        Raises:
            PhiDetectionError: If PHI detection fails
        """
        if not text:
            return text
            
        try:
            # Call AWS Comprehend Medical PHI detection
            response = self.client.detect_phi(Text=text)
            
            # If no entities found, return original text
            if not response.get('Entities'):
                logger.info("No PHI entities detected in text")
                return text
            
            # Sort entities by beginning offset (descending) to avoid offset changes when replacing
            entities = sorted(
                response.get('Entities', []),
                key=lambda x: x['BeginOffset'],
                reverse=True
            )
            
            # Create a mutable copy of the text
            masked_text = text
            
            # Replace each entity with a mask token
            for entity in entities:
                entity_type = entity['Type']
                begin = entity['BeginOffset']
                end = entity['EndOffset']
                
                # Create appropriate mask token based on entity type
                # E.g., [NAME], [DATE], [ADDRESS], etc.
                mask_token = f"[{entity_type}]"
                
                # Replace the entity with mask token
                masked_text = masked_text[:begin] + mask_token + masked_text[end:]
            
            # Log metadata about the PHI detection (not the content)
            entity_types = list(set(entity['Type'] for entity in entities))
            logger.info(f"Masked {len(entities)} PHI entities of types: {entity_types}")
            
            return masked_text
            
        except Exception as e:
            logger.error(f"Error in PHI detection: {e}", exc_info=True)
            raise PhiDetectionError(f"PHI detection failed: {e}")


class CustomRegexPhiService(PhiDetectionService):
    """
    Custom PHI detection service using regular expressions.
    
    Can be used as a fallback or complementary service to AWS Comprehend Medical.
    """
    
    def __init__(self):
        """Initialize regex patterns for PHI detection."""
        # Simplified example patterns - real implementation would be more comprehensive
        self.patterns = {
            "PHONE": r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "MRN": r'\b[A-Z]{2}\d{6,8}\b',  # Example medical record number format
            "URL": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\??[/\w\.-=&%]*'
        }
        logger.info("Custom regex PHI detection service initialized")
    
    async def detect_and_mask_phi(self, text: str) -> str:
        """
        Detect PHI using regex patterns and replace with mask tokens.
        
        Args:
            text: The text to scan for PHI
            
        Returns:
            Text with PHI masked
            
        Raises:
            PhiDetectionError: If PHI detection fails
        """
        if not text:
            return text
        
        try:
            masked_text = text
            entity_count = 0
            
            # Apply each pattern
            for entity_type, pattern in self.patterns.items():
                # Find all matches
                matches = list(re.finditer(pattern, masked_text))
                # Process matches in reverse to preserve offsets
                for match in reversed(matches):
                    start, end = match.span()
                    masked_text = masked_text[:start] + f"[{entity_type}]" + masked_text[end:]
                    entity_count += 1
            
            if entity_count > 0:
                logger.info(f"Masked {entity_count} PHI entities using regex patterns")
            
            return masked_text
            
        except Exception as e:
            logger.error(f"Error in regex PHI detection: {e}", exc_info=True)
            raise PhiDetectionError(f"Regex PHI detection failed: {e}")


class MultiLayerPhiService(PhiDetectionService):
    """
    Multi-layer PHI detection service that combines multiple detection methods.
    
    This implements a defense-in-depth approach to PHI detection:
    1. Primary detection using AWS Comprehend Medical
    2. Secondary detection using custom regex patterns
    """
    
    def __init__(self):
        """Initialize the component PHI detection services."""
        self.comprehend_service = AwsComprehendMedicalPhiService()
        self.regex_service = CustomRegexPhiService()
        logger.info("Multi-layer PHI detection service initialized")
    
    async def detect_and_mask_phi(self, text: str) -> str:
        """
        Apply multiple layers of PHI detection and masking.
        
        Args:
            text: The text to scan for PHI
            
        Returns:
            Text with PHI masked by all detection layers
            
        Raises:
            PhiDetectionError: If PHI detection fails
        """
        if not text:
            return text
        
        try:
            # Layer 1: AWS Comprehend Medical
            masked_text = await self.comprehend_service.detect_and_mask_phi(text)
            
            # Layer 2: Custom regex patterns
            masked_text = await self.regex_service.detect_and_mask_phi(masked_text)
            
            # Additional layers could be added here (e.g., NER model)
            
            return masked_text
            
        except Exception as e:
            logger.error(f"Error in multi-layer PHI detection: {e}", exc_info=True)
            raise PhiDetectionError(f"Multi-layer PHI detection failed: {e}")


# Factory function to get the appropriate PHI service
def get_phi_detection_service() -> PhiDetectionService:
    """Factory function to create PHI detection service based on config."""
    service_type = settings.PHI_DETECTION_SERVICE.lower()
    
    if service_type == "aws_comprehend":
        return AwsComprehendMedicalPhiService()
    elif service_type == "regex":
        return CustomRegexPhiService()
    elif service_type == "multi_layer":
        return MultiLayerPhiService()
    else:
        raise ValueError(f"Unknown PHI detection service: {service_type}")
```

## Deployment Architecture

### Deployment Options

The MentaLLaMA service can be deployed in two primary configurations:

#### 1. SageMaker Asynchronous Inference Endpoint

This option provides serverless scaling for cost-effective deployment:

```bash
# Create SageMaker model from MentaLLaMA artifacts
aws sagemaker create-model \
    --model-name mentalllama-model \
    --primary-container '{
        "Image": "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-gpu-py39-cu117-ubuntu20.04",
        "ModelDataUrl": "s3://novamind-ml-models/mentalllama-33b-lora-model.tar.gz",
        "Environment": {
            "SAGEMAKER_PROGRAM": "inference.py",
            "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code",
            "SAGEMAKER_CONTAINER_LOG_LEVEL": "20",
            "HUGGINGFACE_HUB_CACHE": "/tmp/huggingface",
            "QUANTIZATION": "8bit"
        }
    }' \
    --execution-role-arn "arn:aws:iam::account-id:role/SageMakerExecutionRole"

# Create asynchronous endpoint configuration
aws sagemaker create-endpoint-config \
    --endpoint-config-name mentalllama-async-config \
    --async-inference-config '{
        "OutputConfig": {
            "S3OutputPath": "s3://novamind-ml-results/",
            "NotificationConfig": {
                "SuccessTopic": "arn:aws:sns:region:account-id:mentalllama-success",
                "ErrorTopic": "arn:aws:sns:region:account-id:mentalllama-errors"
            }
        },
        "ClientConfig": {
            "MaxConcurrentInvocationsPerInstance": 4
        }
    }' \
    --production-variants '[{
        "VariantName": "GPUVariant",
        "ModelName": "mentalllama-model",
        "InitialInstanceCount": 0,
        "InstanceType": "ml.g5.2xlarge",
        "VolumeSizeInGB": 100,
        "ModelDataDownloadTimeoutInSeconds": 900,
        "ContainerStartupHealthCheckTimeoutInSeconds": 600
    }]'

# Create the endpoint
aws sagemaker create-endpoint \
    --endpoint-name mentalllama-async-endpoint \
    --endpoint-config-name mentalllama-async-config

# Configure autoscaling
aws application-autoscaling register-scalable-target \
    --service-namespace sagemaker \
    --resource-id endpoint/mentalllama-async-endpoint/variant/GPUVariant \
    --scalable-dimension sagemaker:variant:DesiredInstanceCount \
    --min-capacity 0 \
    --max-capacity 5
```

#### 2. Kubernetes Deployment (EKS)

For more control and potentially lower costs with predictable workloads:

```yaml
# Example Kubernetes deployment for MentaLLaMA inference service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mentalllama-inference-service
  namespace: novamind-ml
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mentalllama-inference
  template:
    metadata:
      labels:
        app: mentalllama-inference
    spec:
      containers:
      - name: mentalllama-inference
        image: novamind/mentalllama-inference:1.0.0
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "90Gi"
            cpu: "8"
          requests:
            nvidia.com/gpu: 1
            memory: "80Gi"
            cpu: "4"
        env:
        - name: MODEL_BASE_PATH
          value: "/models/vicuna-33b"
        - name: LORA_ADAPTER_PATH
          value: "/models/mentalllama-lora"
        - name: QUANTIZATION
          value: "8bit"
        volumeMounts:
        - name: model-storage
          mountPath: /models
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 180
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 190
          periodSeconds: 10
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: efs-model-pvc
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-V100
```

### Service Connectivity

When using the SageMaker option, implement the external inference service adapter:

```python
# app/infrastructure/ml/sagemaker_mentalllama_adapter.py

import boto3
import json
import base64
import asyncio
from typing import Dict, Any
from app.domain.interfaces.ml_service import MentalHealthAnalysisService
from app.domain.exceptions import ModelInferenceError
from app.core.config import settings
from app.core.utils.logging import logger


class SageMakerMentaLLaMAAdapter(MentalHealthAnalysisService):
    """
    Adapter for interacting with MentaLLaMA deployed on SageMaker.
    
    This adapter supports both synchronous and asynchronous inference.
    """
    
    def __init__(self):
        """Initialize the SageMaker client for MentaLLaMA inference."""
        self.client = boto3.client('sagemaker-runtime', region_name=settings.AWS_REGION)
        self.endpoint_name = settings.MENTALLAMA_INFERENCE_ENDPOINT
        self.async_enabled = settings.MENTALLAMA_ASYNC_INFERENCE
        logger.info(f"SageMaker MentaLLaMA adapter initialized (endpoint: {self.endpoint_name}, async: {self.async_enabled})")
    
    async def analyze_text(
        self, 
        prompt: str, 
        max_new_tokens: int = 256, 
        temperature: float = 0.7, 
        top_p: float = 0.9
    ) -> str:
        """
        Send prompt to SageMaker endpoint for inference.
        
        Args:
            prompt: The text prompt for analysis
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated text response
        
        Raises:
            ModelInferenceError: If inference fails
        """
        try:
            # Prepare payload for inference
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": True
                }
            }
            
            # Log query parameters (not content)
            logger.debug(
                f"Sending inference request to SageMaker (prompt length: {len(prompt)}, "
                f"max_tokens: {max_new_tokens}, temperature: {temperature})"
            )
            
            # Choose between sync and async inference
            if self.async_enabled:
                return await self._async_inference(payload)
            else:
                return await self._sync_inference(payload)
                
        except Exception as e:
            logger.error(f"SageMaker inference error: {e}", exc_info=True)
            raise ModelInferenceError(f"SageMaker inference failed: {e}")
    
    async def _sync_inference(self, payload: Dict[str, Any]) -> str:
        """Execute synchronous SageMaker inference."""
        # Run in executor to avoid blocking
        response = await asyncio.to_thread(
            self.client.invoke_endpoint,
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        # Parse response
        response_body = json.loads(response['Body'].read().decode())
        
        # Extract generated text from response
        if isinstance(response_body, list):
            # Handle Hugging Face Inference Server response format
            return response_body[0].get('generated_text', '')
        elif isinstance(response_body, dict):
            # Handle standard response format
            return response_body.get('generated_text', '')
        else:
            # Handle raw text output
            return str(response_body)
    
    async def _async_inference(self, payload: Dict[str, Any]) -> str:
        """
        Execute asynchronous SageMaker inference with polling.
        
        This method starts an async inference job and polls for completion.
        """
        # Start async inference job
        response = await asyncio.to_thread(
            self.client.invoke_endpoint_async,
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            InputLocation=f"s3://{settings.S3_REQUEST_BUCKET}/{settings.S3_REQUEST_PREFIX}/{uuid.uuid4()}.json"
        )
        
        # Get output location
        output_location = response['OutputLocation']
        
        # Poll for completion (with timeout)
        start_time = time.time()
        while (time.time() - start_time) < settings.ASYNC_INFERENCE_TIMEOUT:
            # Check if result is available
            try:
                # Extract output file from S3
                s3_client = boto3.client('s3')
                bucket, key = self._parse_s3_uri(output_location)
                
                # Download result
                response = await asyncio.to_thread(
                    s3_client.get_object,
                    Bucket=bucket,
                    Key=key
                )
                
                # Parse response
                response_body = json.loads(response['Body'].read().decode())
                
                # Extract generated text
                if isinstance(response_body, dict):
                    return response_body.get('generated_text', '')
                else:
                    return str(response_body)
                    
            except s3_client.exceptions.NoSuchKey:
                # Result not ready yet, wait and retry
                await asyncio.sleep(2)
                
        # Timeout reached
        raise ModelInferenceError(f"Async inference timed out after {settings.ASYNC_INFERENCE_TIMEOUT} seconds")
    
    @staticmethod
    def _parse_s3_uri(uri: str) -> tuple:
        """Parse S3 URI into bucket and key components."""
        parts = uri.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ''
        return bucket, key
```

## Monitoring and Observability

### Prometheus Metrics Setup

```python
# app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from typing import Callable, Any

# Define metrics
PHI_ENTITIES_DETECTED = Counter(
    'novamind_phi_entities_detected_total',
    'Total number of PHI entities detected and masked',
    ['entity_type']
)

ANALYSIS_REQUESTS = Counter(
    'novamind_mental_health_analysis_total', 
    'Total number of mental health analysis requests',
    ['analysis_type', 'status']
)

ANALYSIS_LATENCY = Histogram(
    'novamind_analysis_latency_seconds',
    'Latency of mental health analysis requests',
    ['analysis_type'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

MODEL_INFERENCE_LATENCY = Histogram(
    'novamind_model_inference_latency_seconds',
    'Latency of MentaLLaMA model inference',
    ['model_version'],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

PHI_DETECTION_LATENCY = Histogram(
    'novamind_phi_detection_latency_seconds',
    'Latency of PHI detection and masking',
    ['service_type'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

GPU_MEMORY_USAGE = Gauge(
    'novamind_gpu_memory_usage_bytes',
    'Current GPU memory usage for MentaLLaMA',
    ['device']
)


def track_inference_latency(model_version: str) -> Callable:
    """
    Decorator to track model inference latency.
    
    Args:
        model_version: Version identifier for the model
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                ANALYSIS_REQUESTS.labels(
                    analysis_type=kwargs.get('analysis_type', 'unknown'),
                    status='success'
                ).inc()
                return result
            except Exception as e:
                ANALYSIS_REQUESTS.labels(
                    analysis_type=kwargs.get('analysis_type', 'unknown'),
                    status='failure'
                ).inc()
                raise e
            finally:
                end_time = time.time()
                MODEL_INFERENCE_LATENCY.labels(
                    model_version=model_version
                ).observe(end_time - start_time)
        return wrapper
    return decorator


def track_analysis_latency(analysis_type: str) -> Callable:
    """
    Decorator to track end-to-end analysis latency.
    
    Args:
        analysis_type: Type of analysis being performed
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end_time = time.time()
                ANALYSIS_LATENCY.labels(
                    analysis_type=analysis_type
                ).observe(end_time - start_time)
        return wrapper
    return decorator


def update_gpu_memory_usage(device_id: int, memory_bytes: int) -> None:
    """
    Update GPU memory usage metric.
    
    Args:
        device_id: GPU device identifier
        memory_bytes: Memory usage in bytes
    """
    GPU_MEMORY_USAGE.labels(device=f"cuda:{device_id}").set(memory_bytes)


def record_phi_entity(entity_type: str) -> None:
    """
    Record detection of a PHI entity.
    
    Args:
        entity_type: Type of PHI entity detected
    """
    PHI_ENTITIES_DETECTED.labels(entity_type=entity_type).inc()
```

### CloudWatch Integration

```python
# app/infrastructure/monitoring/cloudwatch_exporter.py

import boto3
import time
import threading
from typing import Dict, Any, List
from prometheus_client import REGISTRY
from app.core.config import settings
from app.core.utils.logging import logger


class CloudWatchMetricsExporter:
    """
    Exports Prometheus metrics to CloudWatch.
    
    This class periodically collects metrics from the Prometheus registry
    and exports them to CloudWatch.
    """
    
    def __init__(self, interval: int = 60):
        """
        Initialize the CloudWatch metrics exporter.
        
        Args:
            interval: Reporting interval in seconds
        """
        self.client = boto3.client(
            'cloudwatch',
            region_name=settings.AWS_REGION
        )
        self.namespace = settings.CLOUDWATCH_METRICS_NAMESPACE
        self.interval = interval
        self.running = False
        self.thread = None
        logger.info(f"CloudWatch metrics exporter initialized (namespace: {self.namespace})")
    
    def start(self) -> None:
        """Start the metrics reporting thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._report_metrics_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"CloudWatch metrics reporting started (interval: {self.interval}s)")
    
    def stop(self) -> None:
        """Stop the metrics reporting thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
        logger.info("CloudWatch metrics reporting stopped")
    
    def _report_metrics_loop(self) -> None:
        """Background thread function for periodic metric reporting."""
        while self.running:
            try:
                self._collect_and_send_metrics()
            except Exception as e:
                logger.error(f"Error reporting metrics to CloudWatch: {e}", exc_info=True)
                
            # Sleep until next reporting interval
            time.sleep(self.interval)
    
    def _collect_and_send_metrics(self) -> None:
        """Collect metrics from Prometheus and send to CloudWatch."""
        metric_data = []
        
        # Collect metrics from registry
        for metric in REGISTRY.collect():
            for sample in metric.samples:
                # Convert Prometheus sample to CloudWatch metric
                metric_data.append({
                    'MetricName': sample.name,
                    'Dimensions': [
                        {'Name': k, 'Value': v}
                        for k, v in sample.labels.items()
                    ],
                    'Value': float(sample.value),
                    'Unit': self._determine_unit(sample.name),
                    'Timestamp': datetime.datetime.utcnow()
                })
                
                # CloudWatch has a limit of 20 metrics per request
                if len(metric_data) >= 20:
                    self._send_metrics_batch(metric_data)
                    metric_data = []
        
        # Send any remaining metrics
        if metric_data:
            self._send_metrics_batch(metric_data)
    
    def _send_metrics_batch(self, metric_data: List[Dict[str, Any]]) -> None:
        """
        Send a batch of metrics to CloudWatch.
        
        Args:
            metric_data: List of CloudWatch metric data points
        """
        self.client.put_metric_data(
            Namespace=self.namespace,
            MetricData=metric_data
        )
    
    @staticmethod
    def _determine_unit(metric_name: str) -> str:
        """
        Determine appropriate CloudWatch unit based on metric name.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            CloudWatch unit string
        """
        if 'latency' in metric_name and 'seconds' in metric_name:
            return 'Seconds'
        elif 'bytes' in metric_name:
            return 'Bytes'
        elif 'count' in metric_name or 'total' in metric_name:
            return 'Count'
        else:
            return 'None'


# app/main.py - Add to application startup
cloudwatch_exporter = CloudWatchMetricsExporter(interval=60)
cloudwatch_exporter.start()
```

## Testing Strategy

### Unit Testing

```python
# tests/unit/infrastructure/ml/test_mentalllama_adapter.py

import pytest
from unittest.mock import MagicMock, patch
import torch
from app.infrastructure.ml.mentalllama_adapter import MentaLLaMAAdapter, MentaLLaMAModelLoader
from app.domain.exceptions import ModelLoadingError, ModelInferenceError


@pytest.fixture
def mock_model_loader():
    """Fixture for mocked model loader."""
    loader = MagicMock()
    tokenizer = MagicMock()
    model = MagicMock()
    loader.load_model.return_value = (tokenizer, model)
    return loader


@pytest.fixture
def mock_tokenizer():
    """Fixture for mocked tokenizer."""
    tokenizer = MagicMock()
    tokenizer.eos_token_id = 2
    tokenizer.decode.return_value = "Generated analysis response"
    return tokenizer


@pytest.fixture
def mock_model():
    """Fixture for mocked model."""
    model = MagicMock()
    # Mock the device property
    model.device = torch.device("cuda:0")
    # Mock generate method
    model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    return model


class TestMentaLLaMAAdapter:
    """Test suite for MentaLLaMAAdapter."""
    
    def test_init_success(self, mock_model_loader):
        """Test successful initialization."""
        adapter = MentaLLaMAAdapter(model_loader=mock_model_loader)
        assert adapter.tokenizer is not None
        assert adapter.model is not None
        mock_model_loader.load_model.assert_called_once()
    
    def test_init_failure(self):
        """Test initialization failure."""
        failing_loader = MagicMock()
        failing_loader.load_model.side_effect = Exception("Model loading failed")
        
        with pytest.raises(ModelLoadingError):
            MentaLLaMAAdapter(model_loader=failing_loader)
    
    @pytest.mark.asyncio
    async def test_analyze_text_success(self, mock_model_loader, mock_tokenizer, mock_model):
        """Test successful text analysis."""
        # Setup
        mock_model_loader.load_model.return_value = (mock_tokenizer, mock_model)
        adapter = MentaLLaMAAdapter(model_loader=mock_model_loader)
        
        # Execute
        result = await adapter.analyze_text("Test prompt", max_new_tokens=100)
        
        # Verify
        assert result == "Generated analysis response"
        mock_tokenizer.assert_called_once()
        mock_model.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_text_model_error(self, mock_model_loader, mock_tokenizer, mock_model):
        """Test error during text analysis."""
        # Setup
        mock_model_loader.load_model.return_value = (mock_tokenizer, mock_model)
        mock_model.generate.side_effect = RuntimeError("Inference error")
        adapter = MentaLLaMAAdapter(model_loader=mock_model_loader)
        
        # Execute and Verify
        with pytest.raises(ModelInferenceError):
            await adapter.analyze_text("Test prompt")


# tests/unit/application/services/test_mental_health_analyzer.py

import pytest
from unittest.mock import MagicMock, patch
from app.application.services.mental_health_analyzer import MentalHealthAnalyzerService
from app.domain.entities.analysis_types import AnalysisType, RiskLevel
from app.domain.exceptions import AnalysisError, PhiDetectionError
from uuid import UUID


@pytest.fixture
def mock_analysis_service():
    """Fixture for mocked analysis service."""
    service = MagicMock()
    service.analyze_text.return_value = "Risk Level: medium\nRationale: The text shows signs of distress.\nKey Indicators: feeling hopeless, social withdrawal"
    return service


@pytest.fixture
def mock_phi_service():
    """Fixture for mocked PHI detection service."""
    service = MagicMock()
    service.detect_and_mask_phi.return_value = "I am feeling [NAME] today."
    return service


@pytest.fixture
def analyzer_service(mock_analysis_service, mock_phi_service):
    """Fixture for MentalHealthAnalyzerService with mocked dependencies."""
    return MentalHealthAnalyzerService(
        analysis_service=mock_analysis_service,
        phi_detection_service=mock_phi_service
    )


class TestMentalHealthAnalyzerService:
    """Test suite for MentalHealthAnalyzerService."""
    
    def test_constructor(self, mock_analysis_service, mock_phi_service):
        """Test service initialization."""
        service = MentalHealthAnalyzerService(
            analysis_service=mock_analysis_service,
            phi_detection_service=mock_phi_service
        )
        
        assert service.analysis_service == mock_analysis_service
        assert service.phi_service == mock_phi_service
        assert len(service.prompt_templates) > 0
    
    def test_construct_prompt(self, analyzer_service):
        """Test prompt construction."""
        prompt = analyzer_service._construct_prompt(
            AnalysisType.RISK_ASSESSMENT,
            "Test text"
        )
        
        assert "Test text" in prompt
        assert "suicide or self-harm risk" in prompt.lower()
    
    def test_construct_prompt_invalid_type(self, analyzer_service):
        """Test prompt construction with invalid analysis type."""
        with pytest.raises(ValueError) as excinfo:
            analyzer_service._construct_prompt("invalid_type", "Test text")
        
        assert "Unsupported analysis type" in str(excinfo.value)
    
    def test_parse_risk_assessment(self, analyzer_service):
        """Test parsing risk assessment output."""
        output = "Risk Level: medium\nRationale: Shows signs of distress\nKey Indicators: feeling hopeless, social withdrawal"
        
        result = analyzer_service._parse_risk_assessment(output)
        
        assert result["risk_level"] == RiskLevel.MEDIUM
        assert "signs of distress" in result["rationale"]
        assert len(result["key_indicators"]) == 2
    
    @pytest.mark.asyncio
    async def test_perform_analysis_success(self, analyzer_service, mock_analysis_service, mock_phi_service):
        """Test successful analysis performance."""
        patient_id = UUID("00000000-0000-0000-0000-000000000000")
        
        result = await analyzer_service.perform_analysis(
            patient_id=patient_id,
            text_content="Original text with PHI",
            analysis_type=AnalysisType.RISK_ASSESSMENT
        )
        
        # Verify PHI detection was called
        mock_phi_service.detect_and_mask_phi.assert_called_once_with("Original text with PHI")
        
        # Verify analysis service was called with sanitized text
        mock_analysis_service.analyze_text.assert_called_once()
        
        # Verify result properties
        assert result.patient_id == patient_id
        assert result.analysis_type == AnalysisType.RISK_ASSESSMENT
        assert result.result["risk_level"] == RiskLevel.MEDIUM
        assert "signs of distress" in result.result["rationale"]
    
    @pytest.mark.asyncio
    async def test_perform_analysis_phi_error(self, analyzer_service, mock_phi_service):
        """Test analysis with PHI detection error."""
        mock_phi_service.detect_and_mask_phi.side_effect = Exception("PHI detection failed")
        
        with pytest.raises(PhiDetectionError):
            await analyzer_service.perform_analysis(
                patient_id=UUID("00000000-0000-0000-0000-000000000000"),
                text_content="Text with PHI",
                analysis_type=AnalysisType.RISK_ASSESSMENT
            )
    
    @pytest.mark.asyncio
    async def test_perform_analysis_inference_error(self, analyzer_service, mock_analysis_service):
        """Test analysis with inference error."""
        mock_analysis_service.analyze_text.side_effect = Exception("Inference failed")
        
        with pytest.raises(AnalysisError):
            await analyzer_service.perform_analysis(
                patient_id=UUID("00000000-0000-0000-0000-000000000000"),
                text_content="Test text",
                analysis_type=AnalysisType.RISK_ASSESSMENT
            )
```

### Integration Testing

```python
# tests/integration/api/test_mental_health_analysis_endpoint.py

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.domain.entities.analysis_types import AnalysisType, RiskLevel
from uuid import uuid4, UUID
from app.presentation.schemas.mental_health import MentalHealthAnalysisResponse


@pytest.fixture
def analysis_response():
    """Fixture for mock analysis response."""
    return {
        "patient_id": str(uuid4()),
        "analysis_type": AnalysisType.RISK_ASSESSMENT,
        "result": {
            "risk_level": RiskLevel.LOW,
            "rationale": "No significant risk indicators in text.",
            "key_indicators": []
        },
        "model_version": "klyang/MentaLLaMA-33B-lora_v1.0",
        "generated_at": "2025-03-28T01:05:00Z"
    }


@pytest.fixture
def mock_analyzer_service():
    """Fixture for mocked analyzer service."""
    mock = AsyncMock()
    mock.perform_analysis.return_value = Mock(
        patient_id=UUID("00000000-0000-0000-0000-000000000000"),
        analysis_type=AnalysisType.RISK_ASSESSMENT,
        result={
            "risk_level": RiskLevel.LOW,
            "rationale": "No significant risk indicators in text.",
            "key_indicators": []
        },
        model_version="klyang/MentaLLaMA-33B-lora_v1.0",
        timestamp="2025-03-28T01:05:00Z"
    )
    return mock


@pytest.mark.asyncio
@patch("app.core.dependencies.get_mental_health_analyzer")
@patch("app.core.dependencies.get_current_clinician")
async def test_analyze_mental_health_success(
    mock_get_clinician, 
    mock_get_analyzer,
    mock_analyzer_service,
    analysis_response
):
    """Test successful mental health analysis API call."""
    # Setup mocks
    mock_get_analyzer.return_value = mock_analyzer_service
    mock_get_clinician.return_value = {"id": "clinician-id", "role": "clinician"}
    
    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Call the endpoint
        patient_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(
            f"/api/v1/digital-twin/{patient_id}/mental-health-analysis",
            json={
                "text_content": "Test patient text",
                "analysis_type": AnalysisType.RISK_ASSESSMENT,
                "generation_params": {
                    "max_tokens": 256,
                    "temperature": 0.7
                }
            }
        )
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["data"]["patient_id"] == patient_id
        assert response_data["data"]["analysis_type"] == AnalysisType.RISK_ASSESSMENT
        assert response_data["data"]["result"]["risk_level"] == RiskLevel.LOW


@pytest.mark.asyncio
@patch("app.core.dependencies.get_mental_health_analyzer")
@patch("app.core.dependencies.get_current_clinician")
async def test_analyze_mental_health_phi_error(
    mock_get_clinician, 
    mock_get_analyzer,
    mock_analyzer_service
):
    """Test mental health analysis with PHI detection error."""
    # Setup mocks
    mock_analyzer_service.perform_analysis.side_effect = PhiDetectionError("PHI detection failed")
    mock_get_analyzer.return_value = mock_analyzer_service
    mock_get_clinician.return_value = {"id": "clinician-id", "role": "clinician"}
    
    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Call the endpoint
        patient_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(
            f"/api/v1/digital-twin/{patient_id}/mental-health-analysis",
            json={
                "text_content": "Test patient text",
                "analysis_type": AnalysisType.RISK_ASSESSMENT,
                "generation_params": {
                    "max_tokens": 256,
                    "temperature": 0.7
                }
            }
        )
        
        # Verify response
        assert response.status_code == 500
        response_data = response.json()
        assert "PHI detection" in response_data["detail"]
```

## Error Handling

```python
# app/domain/exceptions.py

class DigitalTwinError(Exception):
    """Base exception for Digital Twin related errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AnalysisError(DigitalTwinError):
    """Exception raised when analysis generation fails."""
    pass


class PhiDetectionError(DigitalTwinError):
    """Exception raised when PHI detection and masking fails."""
    pass


class ModelLoadingError(DigitalTwinError):
    """Exception raised when model loading fails."""
    pass


class ModelInferenceError(DigitalTwinError):
    """Exception raised during model inference."""
    pass


class ResultParsingError(DigitalTwinError):
    """Exception raised when parsing model output fails."""
    pass
```

## Configuration Management

```python
# app/core/config.py

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Project base settings
    PROJECT_NAME: str = Field(default="NOVAMIND", description="Project name")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version 1 prefix")
    
    # AWS settings
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_COMPREHEND_REGION: str = Field(default="us-east-1", description="AWS Comprehend Medical region")
    
    # MentaLLaMA Configuration
    VICUNA_33B_PATH: str = Field(
        default="./models/vicuna-33b-v1.3",
        description="Path to base Vicuna-33B model weights"
    )
    MENTALLAMA_LORA_PATH: str = Field(
        default="./models/mentallama-33b-lora",
        description="Path to MentaLLaMA LoRA adapter weights"
    )
    MENTALLAMA_MODEL_VERSION: str = Field(
        default="klyang/MentaLLaMA-33B-lora_v1.0",
        description="Version identifier for the MentaLLaMA model"
    )
    MENTALLAMA_QUANTIZATION: str = Field(
        default="none",
        description="Quantization level for MentaLLaMA (none, 8bit, 4bit)"
    )
    
    # PHI Detection Configuration
    PHI_DETECTION_SERVICE: str = Field(
        default="multi_layer",
        description="Service to use for PHI detection (aws_comprehend, regex, multi_layer)"
    )
    
    # External Inference Service (if applicable)
    MENTALLAMA_INFERENCE_ENDPOINT: str | None = Field(
        default=None,
        description="URL for external MentaLLaMA inference service (if using)"
    )
    MENTALLAMA_ASYNC_INFERENCE: bool = Field(
        default=False,
        description="Whether to use async inference (applicable for SageMaker)"
    )
    ASYNC_INFERENCE_TIMEOUT: int = Field(
        default=300,
        description="Timeout for async inference in seconds"
    )
    
    # S3 bucket configuration (for async inference)
    S3_REQUEST_BUCKET: str | None = Field(
        default=None,
        description="S3 bucket for async inference requests"
    )
    S3_REQUEST_PREFIX: str = Field(
        default="mentalllama-requests",
        description="S3 prefix for async inference requests"
    )
    
    # Monitoring configuration
    PROMETHEUS_METRICS_ENABLED: bool = Field(
        default=True,
        description="Whether to enable Prometheus metrics"
    )
    CLOUDWATCH_METRICS_ENABLED: bool = Field(
        default=False,
        description="Whether to enable CloudWatch metrics export"
    )
    CLOUDWATCH_METRICS_NAMESPACE: str = Field(
        default="NOVAMIND/MentalLLaMA",
        description="CloudWatch metrics namespace"
    )
    
    class Config:
        env_prefix = "NOVAMIND_"
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

## Security and HIPAA Compliance

### PHI Protection Overview

The NOVAMIND MentaLLaMA implementation adheres to strict HIPAA compliance requirements:

1. **Multi-Layer PHI Detection**: Three-tier approach:
   - AWS Comprehend Medical for clinical entity recognition
   - Custom regex patterns for domain-specific identifiers
   - Optional NER model for mental health-specific PHI

2. **PHI Masking**: Replace detected entities with standardized tokens
   - Maintains text structure for analysis
   - Consistent format (e.g., `[NAME]`, `[DATE]`)

3. **Secure Communication**: All API communication uses TLS 1.3
   - VPC endpoints for AWS services
   - Private networking for model inference

4. **Access Controls**: Role-based access to all functionality
   - AWS Cognito authentication and authorization
   - Fine-grained permission management
   - Clinician-only access to analysis endpoints

5. **Audit Logging**: Comprehensive logging without PHI
   - Request metadata (timestamp, user, action type)
   - No logging of raw text or full analysis content

### AWS Security Configuration

```json
// IAM Policy for MentalLLaMA Analysis Service
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "comprehendmedical:DetectPHI"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:InvokeEndpoint",
        "sagemaker:InvokeEndpointAsync"
      ],
      "Resource": "arn:aws:sagemaker:*:*:endpoint/mentalllama-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::novamind-ml-models/*",
        "arn:aws:s3:::novamind-ml-results/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:*:*:key/phi-encryption-key-id"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "NOVAMIND/MentalLLaMA"
        }
      }
    }
  ]
}
```

## Implementation Roadmap

### Phase 1: MentaLLaMA Core Integration (Month 1-2)

1. **Infrastructure Setup**:
   - Configure GPU infrastructure (SageMaker or EC2)
   - Set up model storage and version management
   - Establish secure networking and access controls

2. **Core Adapters**:
   - Implement `MentaLLaMAAdapter` for model interaction
   - Develop PHI detection service integration
   - Build prompt engineering framework

3. **Basic API Integration**:
   - Create mental health analysis API endpoint
   - Implement domain entities and interfaces
   - Set up basic error handling and validation

### Phase 2: Core Analysis Features (Month 3-4)

1. **Analysis Enhancements**:
   - Refine prompts for core analysis types
   - Implement robust result parsing
   - Add quality monitoring mechanisms

2. **Performance Optimization**:
   - Implement model quantization
   - Add caching layer for identical requests
   - Configure optimal GPU resource allocation

3. **Monitoring & Observability**:
   - Set up metrics collection and dashboards
   - Implement comprehensive logging
   - Configure alerts for quality and performance

### Phase 3: Dashboard Integration (Month 5-6)

1. **Clinical Visualization**:
   - Integrate analysis results into clinician dashboards
   - Develop longitudinal tracking of patient metrics
   - Implement analysis result comparison views

2. **Security Enhancements**:
   - Conduct security review and penetration testing
   - Optimize PHI detection and handling
   - Establish analysis audit trails

3. **Validation & Refinement**:
   - Conduct clinical validation with psychiatrists
   - Refine prompts based on clinical feedback
   - Optimize analysis for clinical utility

### Phase 4: Advanced Features (Month 7-8)

1. **Additional Analysis Types**:
   - Expand to include all MentaLLaMA capabilities
   - Implement summarization features
   - Add therapeutic recommendation generation

2. **Model Optimization**:
   - Explore fine-tuning for specific practice needs
   - Implement smaller model variants for specific tasks
   - Develop optimization for non-critical features

3. **Multi-Patient Analytics**:
   - Add population-level trend analysis
   - Implement practice-wide analytics
   - Develop anonymized reporting capabilities

## Conclusion

This implementation guide provides a comprehensive approach to integrating MentaLLaMA-33B-lora into NOVAMIND's Digital Twin architecture using Clean Architecture principles. By following this approach, we can leverage powerful mental health AI insights while maintaining strict HIPAA compliance, performance, and scalability.

The MentaLLaMA integration enables NOVAMIND to offer unprecedented mental health analysis capabilities to clinicians, enhancing the concierge psychiatry experience while maintaining the highest standards of patient privacy and clinical quality.

For additional details, refer to these complementary documents:
- [MentaLLaMA Mental Health Modeling](./MentalLLaMA/01_MENTAL_HEALTH_MODELING.md)
- [MentaLLaMA AWS Deployment & HIPAA Compliance](./MentalLLaMA/02_AWS_DEPLOYMENT_HIPAA.md)
- [MentaLLaMA Clinical Implementation Guide](./MentalLLaMA/03_CLINICAL_IMPLEMENTATION_GUIDE.md)