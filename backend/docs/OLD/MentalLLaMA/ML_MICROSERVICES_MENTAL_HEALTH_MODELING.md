# NOVAMIND: Mental Health Modeling with MentaLLaMA

## Introduction

This document outlines the comprehensive implementation strategy for integrating MentaLLaMA into NOVAMIND's Digital Twin architecture. MentaLLaMA is a specialized large language model designed specifically for mental health analysis and interpretable reasoning, making it an ideal candidate for our luxury concierge psychiatry platform's AI capabilities.

## Table of Contents

1. [MentaLLaMA Overview](#mentalllama-overview)
2. [Technical Architecture](#technical-architecture)
3. [Implementation Strategy](#implementation-strategy)
4. [HIPAA Compliance Measures](#hipaa-compliance-measures)
5. [Prompt Engineering](#prompt-engineering)
6. [Deployment Architecture](#deployment-architecture)
7. [Performance Optimization](#performance-optimization)
8. [Testing and Validation](#testing-and-validation)
9. [Clinical Integration Guidelines](#clinical-integration-guidelines)
10. [Implementation Roadmap](#implementation-roadmap)

## MentaLLaMA Overview

### What is MentaLLaMA?

MentaLLaMA is the first open-source large language model specifically fine-tuned for mental health analysis on social media and clinical text. Developed by researchers from the National Centre for Text Mining and the University of Manchester, it provides interpretable results across multiple mental health analysis tasks.

### Key Features

1. **Base Architecture**: Built on Vicuna-33B, an instruction-tuned version of Meta's LLaMA model
2. **Specialization**: Fine-tuned on the Interpretable Mental Health Instruction (IMHI) dataset with 105K instruction samples
3. **Efficiency**: Uses Low-Rank Adaptation (LoRA) for parameter-efficient fine-tuning
4. **Interpretability**: Uniquely designed to provide explanations/rationales for its assessments
5. **Multi-Task**: Trained on 8 mental health analysis tasks across 10 datasets

### Supported Mental Health Analysis Tasks

1. **Depression Detection**: Identifying signs of depression in text
2. **Stress Detection**: Analyzing text for stress indicators
3. **Mental Disorders Detection**: Recognizing various mental health conditions
4. **Stress Cause Detection**: Identifying potential causes of stress
5. **Depression/Suicide Cause Detection**: Analyzing factors related to depression or suicidal ideation
6. **Loneliness Detection**: Identifying indicators of loneliness
7. **Wellness Dimensions Detection**: Analyzing various dimensions of wellness
8. **Interpersonal Risk Factors Detection**: Identifying risk factors in interpersonal relationships

### Model Variants

For NOVAMIND's implementation, we will focus on the most robust variant:

- **MentaLLaMA-33B-lora**: The flagship model, fine-tuned from Vicuna-33B with LoRA. Provides the highest quality analysis and explanations, though with more demanding computational requirements.

Alternative options (for potential future consideration):
- **MentaLLaMA-chat-13B**: Built on LLaMA2-chat-13B, offering a balance of quality and resource efficiency
- **MentaLLaMA-chat-7B**: A more lightweight option based on LLaMA2-chat-7B

### Ethical Considerations

As stated by the MentaLLaMA authors:

> "This repository and its contents are provided for **non-clinical research only**. None of the material constitutes actual diagnosis or advice, and help-seekers should get assistance from professional psychiatrists or clinical practitioners."

For NOVAMIND's implementation:
1. All model outputs must be reviewed by qualified clinicians
2. Clear disclaimers must be included in any patient-facing applications
3. The system is positioned as a clinical decision support tool, not a diagnostic system
4. Robust safeguards must be implemented against over-reliance on automated analysis

## Technical Architecture

### Clean Architecture Integration

Following NOVAMIND's commitment to Clean Architecture principles, MentaLLaMA integration will adhere to strict layering:

1. **Domain Layer**
   - Pure business entities like `MentalHealthAnalysis`, `RiskAssessment`, `DepressionAnalysis`
   - Interface definitions (e.g., `MentalHealthAnalysisService`)
   - Value objects for various assessment types
   - Enums like `RiskLevel`, `AnalysisType`
   - **No dependencies on specific ML models or frameworks**

2. **Application Layer**
   - Use cases (e.g., `AnalyzeJournalEntryUseCase`, `AssessRiskLevelUseCase`)
   - Orchestration services that coordinate PHI sanitization, analysis, and result processing
   - Prompt construction and result parsing logic
   - Event handling for analysis completion

3. **Infrastructure Layer**
   - Model adapters (e.g., `MentaLLaMAAdapter`) implementing domain interfaces
   - PHI detection services (e.g., `AwsComprehendMedicalPhiService`)
   - GPU resource management
   - Caching mechanisms for analysis results
   - Client implementations for external services

4. **Presentation Layer**
   - API endpoints for triggering analysis
   - Request/response DTOs
   - Authorization and access control
   - Swagger/OpenAPI documentation

### Component Diagram

```
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│                                      │       │                                      │
│   Application Service                │       │   Domain Layer                       │
│   ┌──────────────────────────────┐   │       │   ┌──────────────────────────────┐   │
│   │                              │   │       │   │                              │   │
│   │  MentalHealthAnalyzerService │◄──┼───────┼───┤ MentalHealthAnalysisService  │   │
│   │                              │   │       │   │         (interface)          │   │
│   └───────────────┬──────────────┘   │       │   └──────────────────────────────┘   │
│                   │                  │       │                  ▲                   │
└───────────────────┼──────────────────┘       └──────────────────┼───────────────────┘
                    │                                             │
                    │                                             │
                    ▼                                             │
┌──────────────────────────────────────┐       ┌──────────────────┴───────────────────┐
│                                      │       │                                      │
│   Infrastructure Layer               │       │   Infrastructure Layer               │
│   ┌──────────────────────────────┐   │       │   ┌──────────────────────────────┐   │
│   │                              │   │       │   │                              │   │
│   │      PhiDetectionService     │◄──┼───────┼───┤      MentaLLaMAAdapter       │   │
│   │                              │   │       │   │                              │   │
│   └──────────────────────────────┘   │       │   └──────────────────────────────┘   │
│                                      │       │                                      │
└──────────────────────────────────────┘       └──────────────────────────────────────┘
```

### Analysis Flow

1. **Data Preparation**: Patient text data (e.g., journal entries, session notes) is collected through secure channels
2. **PHI Detection & Removal**: **All text undergoes automated PHI detection and masking *before* being sent to MentaLLaMA**
3. **Prompt Construction**: Appropriate prompts are generated based on the analysis type requested
4. **Model Inference**: Sanitized text and prompt are sent to the MentaLLaMA model for inference
5. **Result Processing**: Model outputs are parsed, structured, and validated
6. **Storage & Display**: Results are securely stored and displayed in the clinician dashboard

## Implementation Strategy

### Core Components

#### 1. MentaLLaMA Adapter

The adapter is responsible for loading the model and performing inference operations.

```python
# Infrastructure Layer: app/infrastructure/ml/mentalllama_adapter.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, PeftConfig
from app.core.utils.logging import logger
from app.core.config import settings


class MentaLLaMAAdapter:
    """Adapter for interacting with the MentaLLaMA-33B-lora model."""

    def __init__(self):
        """Initialize the adapter."""
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the base model and apply LoRA weights."""
        try:
            # Get model paths from settings
            base_path = settings.VICUNA_33B_PATH
            lora_path = settings.MENTALLAMA_LORA_PATH
            
            logger.info(f"Loading MentaLLaMA model: base='{base_path}', lora='{lora_path}'")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                base_path, 
                use_fast=False
            )
            
            # Load base model
            base_model = AutoModelForCausalLM.from_pretrained(
                base_path,
                torch_dtype=torch.float16,
                device_map="auto",  # Use all available GPUs
                trust_remote_code=True
            )
            
            # Apply LoRA weights
            self.model = PeftModel.from_pretrained(
                base_model, 
                lora_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            logger.info("MentaLLaMA-33B-lora model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load MentaLLaMA model: {e}", exc_info=True)
            raise RuntimeError(f"MentaLLaMA initialization failed: {e}")

    async def analyze_text(
        self, 
        prompt: str, 
        max_new_tokens: int = 256, 
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        Generate analysis based on the provided prompt.
        
        Args:
            prompt: The prompt to send to the model
            max_new_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (lower = more deterministic)
            top_p: Controls diversity via nucleus sampling
            
        Returns:
            Generated text analysis
            
        Raises:
            RuntimeError: If model inference fails
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("MentaLLaMA model not loaded")
            
        try:
            # Log prompt length but not content (could contain sanitized but sensitive data)
            logger.debug(f"Performing analysis with prompt length: {len(prompt)}")
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate output
            with torch.no_grad():
                output_tokens = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Extract only the generated part (excluding the prompt)
            generated_text = self.tokenizer.decode(
                output_tokens[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            logger.debug(f"Generated analysis of length: {len(generated_text)}")
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Error during MentaLLaMA inference: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate analysis: {e}")
```

#### 2. PHI Detection Service

Responsible for detecting and masking PHI in text before it is sent to the model.

```python
# Infrastructure Layer: app/infrastructure/services/phi_detection_service.py
import boto3
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.utils.logging import logger


class PhiDetectionService(ABC):
    """Abstract base class for PHI detection services."""
    
    @abstractmethod
    async def detect_and_mask_phi(self, text: str) -> str:
        """
        Detect and mask PHI in the provided text.
        
        Args:
            text: The text to scan for PHI
            
        Returns:
            Text with PHI masked/removed
        """
        pass


class AwsComprehendMedicalPhiService(PhiDetectionService):
    """PHI detection service using AWS Comprehend Medical."""
    
    def __init__(self):
        """Initialize AWS Comprehend Medical client."""
        self.client = boto3.client(
            'comprehendmedical',
            region_name=settings.AWS_COMPREHEND_REGION
        )
        logger.info(f"AWS Comprehend Medical PHI service initialized")
    
    async def detect_and_mask_phi(self, text: str) -> str:
        """
        Detect PHI using AWS Comprehend Medical and replace with mask tokens.
        
        Args:
            text: The text to scan for PHI
            
        Returns:
            Text with PHI masked
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
            
            # Sort entities by beginning offset (descending)
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
                # e.g., [NAME], [DATE], [ADDRESS], etc.
                mask_token = f"[{entity_type}]"
                
                # Replace the entity with mask token
                masked_text = masked_text[:begin] + mask_token + masked_text[end:]
            
            logger.info(f"Masked {len(entities)} PHI entities in text")
            return masked_text
            
        except Exception as e:
            logger.error(f"Error in PHI detection: {e}", exc_info=True)
            # In case of error, return a generic message rather than the original text
            # to prevent accidental PHI leakage
            raise RuntimeError(f"PHI detection failed: {e}")
```

#### 3. Mental Health Analysis Service

Coordinates the analysis flow, including prompt construction and result parsing.

```python
# Application Layer: app/application/services/mental_health_analyzer.py
from typing import Dict, Any, Optional
from app.core.exceptions import AnalysisError, PhiDetectionError
from app.core.utils.logging import logger
from app.infrastructure.ml.mentalllama_adapter import MentaLLaMAAdapter
from app.infrastructure.services.phi_detection_service import PhiDetectionService


class MentalHealthAnalyzerService:
    """Service for performing mental health analysis using MentaLLaMA."""

    def __init__(
        self, 
        mentalllama_adapter: MentaLLaMAAdapter,
        phi_detection_service: PhiDetectionService
    ):
        """Initialize with required dependencies."""
        self.adapter = mentalllama_adapter
        self.phi_service = phi_detection_service
        
    def _construct_prompt(self, analysis_type: str, sanitized_text: str) -> str:
        """
        Construct appropriate prompt based on analysis type.
        
        Args:
            analysis_type: Type of analysis to perform
            sanitized_text: PHI-masked text to analyze
            
        Returns:
            Constructed prompt for MentaLLaMA
            
        Raises:
            ValueError: If analysis type is not supported
        """
        prompts = {
            "risk_assessment": (
                f"Consider this text: \"{sanitized_text}\"\n\n"
                f"Question: Does the author show signs of suicide risk? "
                f"Please provide your assessment as risk_level (low, medium, high) "
                f"and explain your reasoning with specific references to the text."
            ),
            "depression_detection": (
                f"Consider this text: \"{sanitized_text}\"\n\n"
                f"Question: Does the author show signs of depression? "
                f"Please provide your assessment (yes/no/uncertain) and explain "
                f"your reasoning, citing specific language or patterns in the text "
                f"that support your conclusion."
            ),
            "sentiment_analysis": (
                f"Consider this text: \"{sanitized_text}\"\n\n"
                f"Question: What is the emotional sentiment expressed in this text? "
                f"Analyze as positive, negative, or neutral and explain your reasoning."
            ),
        }
        
        if analysis_type not in prompts:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
        return prompts[analysis_type]

    def _parse_result(self, analysis_type: str, raw_output: str) -> Dict[str, Any]:
        """
        Parse model output into structured result.
        
        Args:
            analysis_type: Type of analysis performed
            raw_output: Raw text output from MentaLLaMA
            
        Returns:
            Structured analysis result as a dictionary
            
        Raises:
            AnalysisError: If parsing fails
        """
        try:
            if analysis_type == "risk_assessment":
                # Extract risk level
                if "low" in raw_output.lower():
                    risk_level = "low"
                elif "medium" in raw_output.lower():
                    risk_level = "medium"
                elif "high" in raw_output.lower():
                    risk_level = "high"
                else:
                    risk_level = "undetermined"
                
                # Extract rationale
                if "reasoning:" in raw_output.lower():
                    rationale = raw_output.lower().split("reasoning:")[1].strip()
                else:
                    rationale = raw_output.strip()
                
                return {
                    "risk_level": risk_level,
                    "rationale": rationale,
                    "analysis_type": "risk_assessment"
                }
            
            elif analysis_type == "depression_detection":
                # Extract assessment
                if "yes" in raw_output.lower():
                    assessment = "yes"
                elif "no" in raw_output.lower():
                    assessment = "no"
                else:
                    assessment = "uncertain"
                
                # Extract rationale
                if "reasoning:" in raw_output.lower():
                    rationale = raw_output.lower().split("reasoning:")[1].strip()
                else:
                    rationale = raw_output.strip()
                
                return {
                    "depression_indicated": assessment,
                    "rationale": rationale,
                    "analysis_type": "depression_detection"
                }
            
            # Handle other analysis types similarly
            
            # Default fallback
            return {
                "raw_analysis": raw_output.strip(),
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            logger.error(f"Error parsing MentaLLaMA output: {e}", exc_info=True)
            raise AnalysisError(f"Failed to parse analysis result: {e}")

    async def perform_analysis(
        self, 
        text_content: str, 
        analysis_type: str,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """
        Perform mental health analysis on the provided text.
        
        Args:
            text_content: The text to analyze (will be sanitized of PHI)
            analysis_type: Type of analysis to perform
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing the structured analysis result
            
        Raises:
            PhiDetectionError: If PHI detection fails
            AnalysisError: If analysis generation or parsing fails
            ValueError: If analysis_type is not supported
        """
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
            raw_output = await self.adapter.analyze_text(
                prompt=prompt,
                max_new_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"MentaLLaMA analysis failed: {e}", exc_info=True)
            raise AnalysisError(f"Failed to generate analysis: {e}") from e
        
        # 4. Parse and structure the result
        result = self._parse_result(analysis_type, raw_output)
        
        # 5. Return structured analysis
        return result
```

#### 4. Domain Entities and Interfaces

```python
# Domain Layer: app/domain/interfaces/mental_health_analysis.py
from abc import ABC, abstractmethod
from typing import Dict, Any


class MentalHealthAnalysisService(ABC):
    """Interface for mental health analysis services."""
    
    @abstractmethod
    async def perform_analysis(
        self, 
        text_content: str, 
        analysis_type: str,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """
        Perform mental health analysis on text content.
        
        Args:
            text_content: Text to analyze
            analysis_type: Type of analysis to perform
            max_tokens: Maximum tokens to generate
            
        Returns:
            Analysis result
        """
        pass


# Domain Layer: app/domain/enums/mental_health.py
from enum import Enum, auto


class RiskLevel(Enum):
    """Risk level for suicide risk assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNDETERMINED = "undetermined"


class AnalysisType(Enum):
    """Types of mental health analysis supported."""
    RISK_ASSESSMENT = "risk_assessment"
    DEPRESSION_DETECTION = "depression_detection"
    STRESS_DETECTION = "stress_detection"
    MENTAL_DISORDER_DETECTION = "mental_disorder_detection"
    STRESS_CAUSE_DETECTION = "stress_cause_detection"
    DEPRESSION_CAUSE_DETECTION = "depression_cause_detection"
    LONELINESS_DETECTION = "loneliness_detection"
    WELLNESS_DIMENSION_DETECTION = "wellness_dimension_detection"
    INTERPERSONAL_RISK_DETECTION = "interpersonal_risk_detection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
```

#### 5. API Endpoint

```python
# Presentation Layer: app/api/routes/mental_health.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.api.schemas.mental_health import (
    MentalHealthAnalysisRequest,
    MentalHealthAnalysisResponse
)
from app.application.services.mental_health_analyzer import MentalHealthAnalyzerService
from app.core.exceptions import AnalysisError, PhiDetectionError
from app.api.dependencies.services import get_mental_health_analyzer_service
from app.api.dependencies.auth import get_current_clinician


router = APIRouter(prefix="/api/v1/mental-health", tags=["Mental Health"])


@router.post(
    "/analyze",
    response_model=MentalHealthAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze text for mental health insights",
    description="Analyze text (e.g., journal entries, notes) for mental health insights using MentaLLaMA."
)
async def analyze_text(
    request: MentalHealthAnalysisRequest,
    analyzer_service: MentalHealthAnalyzerService = Depends(get_mental_health_analyzer_service),
    _: Dict = Depends(get_current_clinician)  # Ensure only clinicians can access
) -> MentalHealthAnalysisResponse:
    """
    Analyze text for mental health insights.
    
    PHI is automatically detected and masked before sending to the model.
    """
    try:
        result = await analyzer_service.perform_analysis(
            text_content=request.text_content,
            analysis_type=request.analysis_type,
            max_tokens=request.generation_params.max_tokens
        )
        
        return MentalHealthAnalysisResponse(
            success=True,
            data={
                "patient_id": request.patient_id,
                "analysis_type": request.analysis_type,
                "result": result,
                "model_version": "MentaLLaMA-33B-lora"
            },
            error=None
        )
        
    except PhiDetectionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PHI detection failed: {str(e)}"
        )
    except AnalysisError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis generation failed: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
```

#### 6. Request/Response Schemas

```python
# Presentation Layer: app/api/schemas/mental_health.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID


class GenerationParams(BaseModel):
    """Parameters for controlling text generation."""
    max_tokens: int = Field(256, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Controls randomness (lower = more deterministic)")
    top_p: float = Field(0.9, description="Controls diversity via nucleus sampling")


class MentalHealthAnalysisRequest(BaseModel):
    """Request for mental health analysis."""
    patient_id: UUID = Field(..., description="Patient ID")
    text_content: str = Field(..., description="Text to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    generation_params: GenerationParams = Field(default_factory=GenerationParams)
    
    @validator("analysis_type")
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        valid_types = {
            "risk_assessment",
            "depression_detection",
            "stress_detection",
            "mental_disorder_detection",
            "stress_cause_detection",
            "depression_cause_detection",
            "loneliness_detection",
            "wellness_dimension_detection",
            "interpersonal_risk_detection",
            "sentiment_analysis"
        }
        if v not in valid_types:
            raise ValueError(f"Invalid analysis type. Must be one of: {', '.join(valid_types)}")
        return v
    
    @validator("text_content")
    def validate_text_content(cls, v):
        """Validate text content."""
        if not v or len(v.strip()) < 10:
            raise ValueError("Text content must be at least 10 characters")
        return v


class MentalHealthAnalysisResponse(BaseModel):
    """Response for mental health analysis."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if any")
```

## HIPAA Compliance Measures

### PHI Protection Strategy

1. **PHI Detection and Removal (Critical)**
   - All text undergoes automated PHI detection and masking **before** being sent to MentaLLaMA
   - Use AWS Comprehend Medical or similar specialized medical PHI detection service
   - Implement configurable entity types to mask (names, dates, locations, etc.)
   - Generate appropriate mask tokens (e.g., `[NAME]`, `[DATE]`, `[LOCATION]`)

2. **Secure Data Handling**
   - Encrypt all data at rest (KMS) and in transit (TLS)
   - Implement strict access controls to limit who can perform analysis
   - Keep logs sanitized (no PHI in log entries)
   - Audit all analysis requests and accesses

3. **Minimal Data Collection**
   - Only collect essential data for analysis
   - Implement configurable retention policies
   - Provide options for ephemeral analysis (no storage of raw text)

4. **Clear Documentation & Training**
   - Clearly document PHI handling procedures
   - Train all developers and clinicians on HIPAA requirements
   - Implement regular security reviews

## Prompt Engineering

### Prompt Design Principles

1. **Clear Instructions**: Provide explicit directions to the model
2. **Contextual Framework**: Set up the analysis context
3. **Output Structuring**: Guide the model to provide structured responses
4. **Clinical Focus**: Ensure prompts align with clinical best practices

### Example Prompts

#### 1. Risk Assessment

```
Consider this text: "[sanitized_text]"

Question: Does the author show signs of suicide risk?

Please provide your assessment as risk_level (low, medium, high) and explain your reasoning with specific references to the text.
```

#### 2. Depression Detection

```
Consider this text: "[sanitized_text]"

Question: Does the author show signs of depression?

Please provide your assessment (yes/no/uncertain) and explain your reasoning, citing specific language or patterns in the text that support your conclusion.
```

#### 3. Structured Output Format

```
Consider this text: "[sanitized_text]"

Question: Does the author show signs of depression?

Please structure your response as follows:
Assessment: [yes/no/uncertain]
Confidence: [high/medium/low]
Rationale: [your detailed explanation]
Key indicators: [bullet list of specific indicators from the text]
```

### Prompt Optimization

1. **Iteration**: Test prompts against sample PHI-free text
2. **Clinical Validation**: Have clinicians review prompt outputs
3. **Consistency**: Maintain consistent prompt structures for reliability
4. **Documentation**: Maintain a prompt library with versions and use cases

## Deployment Architecture

### AWS Deployment Options

#### Option 1: SageMaker Endpoint

Ideal for managed infrastructure with automatic scaling.

1. **Setup**:
   - Deploy MentaLLaMA to SageMaker using Hugging Face transformers
   - Configure instance type (e.g., `ml.g4dn.2xlarge` for testing, `ml.p3.2xlarge` or higher for production)
   - Use SageMaker's built-in scaling and monitoring

2. **Benefits**:
   - Fully managed service
   - Automatic scaling
   - Integrated monitoring
   - Simplified deployment

3. **Considerations**:
   - Higher cost compared to self-managed EC2
   - Less customization flexibility
   - 5-10 minute cold start time for model loading

#### Option 2: EC2 with Custom Inference Server

Ideal for maximum control and customization.

1. **Setup**:
   - Deploy on EC2 GPU instances (e.g., `g4dn.2xlarge` for testing, `p3.2xlarge` or higher for production)
   - Implement FastAPI-based inference server
   - Set up auto-scaling group based on CPU/GPU metrics

2. **Benefits**:
   - Maximum control over environment
   - Potentially lower cost for consistent workloads
   - Ability to implement custom optimizations

3. **Considerations**:
   - More operational overhead
   - Manual scaling configuration
   - Requires custom health monitoring

### Infrastructure Requirements

1. **GPU Specifications**:
   - For MentaLLaMA-33B-lora: NVIDIA V100 (16GB+) or A100 GPU
   - VRAM Requirements: 40GB+ for full precision, 20GB+ with 8-bit quantization, 10GB+ with 4-bit quantization

2. **Memory Requirements**:
   - System RAM: 32GB+ (to handle loading/preprocessing)
   - Storage: 60GB+ for model weights and dependencies

3. **Networking**:
   - Configure VPC for secure communication
   - Implement private endpoints for model inference
   - Set up API Gateway with authentication

## Performance Optimization

### Model Optimization Techniques

1. **Quantization**:
   - 8-bit Quantization (minimal quality impact): Reduces VRAM by ~50%
   - 4-bit Quantization (moderate quality impact): Reduces VRAM by ~75%
   - Implementation using `bitsandbytes` library

2. **LoRA Parameter Efficiency**:
   - MentaLLaMA already uses LoRA for efficient fine-tuning
   - Benefit from reduced parameter count during inference

3. **Batching Strategies**:
   - Implement request batching for improved throughput
   - Configure optimal batch sizes based on GPU capabilities
   - Handle varying input lengths efficiently

### Latency Optimization

1. **Caching**:
   - Implement result caching for identical (sanitized) inputs
   - Use Redis or similar for distributed caching
   - Configure TTL based on clinical requirements

2. **Streaming Generation**:
   - Implement token-by-token streaming for longer responses
   - Provides incremental results for better user experience

3. **Pipeline Parallelism**:
   - Implement parallel PHI detection and model preparation
   - Optimize task scheduling for concurrent requests

### Monitoring and Alerting

1. **Performance Metrics**:
   - Request latency (average, p95, p99)
   - GPU utilization and memory usage
   - Token throughput (tokens/second)
   - Cache hit rate

2. **Alerting Thresholds**:
   - High latency (e.g., p95 > 5 seconds)
   - GPU utilization > 90% for extended periods
   - Error rate > 1%
   - Abnormal token distribution

## Testing and Validation

### Unit Testing

1. **Component Tests**:
   - Test PHI detection with known patterns
   - Test prompt generation for different analysis types
   - Test result parsing from model outputs

2. **Integration Tests**:
   - Test end-to-end flow with mock model responses
   - Validate error handling and recovery

### Clinical Validation

1. **Expert Review**:
   - Have clinical experts review model outputs
   - Validate against clinical standards and guidelines
   - Document strengths and limitations

2. **Comparative Analysis**:
   - Compare model outputs to clinician assessments
   - Measure agreement rates and identify discrepancies
   - Refine prompts based on findings

### Ongoing Monitoring

1. **Output Quality Metrics**:
   - Track confidence scores and uncertainty indicators
   - Monitor distribution of classifications
   - Identify potential drift or anomalies

2. **Feedback Loop**:
   - Implement clinician feedback mechanism
   - Use feedback to improve prompts and processing
   - Document model limitations and edge cases

## Clinical Integration Guidelines

### Usage Recommendations

1. **Decision Support Only**:
   - Position as a clinical decision support tool
   - Not a replacement for clinical judgment
   - Always requires human oversight

2. **Appropriate Use Cases**:
   - Initial screening of patient-generated text
   - Identifying potential risk factors
   - Generating hypotheses for clinician consideration
   - Tracking sentiment and themes over time

3. **Limitations Awareness**:
   - Cultural and contextual nuances may be missed
   - May not account for non-textual indicators
   - Variable performance across different conditions

### Implementation Best Practices

1. **Clear Disclaimers**:
   - Clearly identify AI-generated content
   - Explain the system's role and limitations
   - Provide clinician contact information

2. **Clinician Training**:
   - Train clinicians on system capabilities and limitations
   - Provide guidance on interpreting model outputs
   - Establish protocols for handling concerning outputs

3. **Interpretation Guidelines**:
   - Context matters - consider all available information
   - Look for supporting evidence in the text
   - Consider alternative explanations
   - Pay attention to model uncertainty

## Implementation Roadmap

### Phase 1: Core Integration (Months 1-2)

1. **Infrastructure Setup**
   - Configure GPU instances (SageMaker or EC2)
   - Set up model deployment pipeline
   - Implement PHI detection service

2. **Basic Integration**
   - Implement MentaLLaMAAdapter
   - Create basic prompt templates
   - Develop result parsing logic

3. **Initial Testing**
   - Validate with sanitized sample data
   - Measure performance and resource usage
   - Document implementation details

### Phase 2: Feature Development (Months 3-4)

1. **Expand Analysis Types**
   - Implement all core analysis types
   - Refine prompt templates
   - Develop specialized result parsers

2. **UI Integration**
   - Design clinician-facing result displays
   - Implement feedback mechanisms
   - Create analysis request workflows

3. **Performance Optimization**
   - Implement caching strategy
   - Explore quantization options
   - Optimize batch processing

### Phase 3: Clinical Validation (Months 5-6)

1. **Clinical Testing**
   - Conduct structured validation with clinicians
   - Compare model outputs to expert assessments
   - Document limitations and strengths

2. **Refinement**
   - Adjust prompts based on clinical feedback
   - Improve result parsing accuracy
   - Enhance explanation quality

3. **Documentation**
   - Create clinical usage guidelines
   - Document model capabilities and limitations
   - Prepare training materials for clinicians

### Phase 4: Advanced Features (Months 7-8)

1. **Longitudinal Analysis**
   - Implement trend detection over time
   - Develop comparison visualizations
   - Create summary reports

2. **Advanced Prompt Engineering**
   - Explore few-shot prompt techniques
   - Develop more specialized analysis types
   - Implement structured output formats

3. **Production Hardening**
   - Finalize monitoring and alerting
   - Optimize for production scale
   - Complete security review

## Conclusion

The integration of MentaLLaMA into NOVAMIND's Digital Twin architecture represents a significant advancement in our concierge psychiatry platform's capabilities. By leveraging this specialized mental health LLM with strict adherence to Clean Architecture principles and HIPAA compliance, we will provide clinicians with unprecedented insights into patient mental states while maintaining the highest standards of data privacy and security.

The implementation roadmap outlined in this document provides a clear path forward, balancing technical sophistication with clinical rigor. Throughout the process, we will maintain our commitment to ethical AI use, ensuring that the technology augments rather than replaces human clinical judgment, and upholds our luxury standard of patient care.