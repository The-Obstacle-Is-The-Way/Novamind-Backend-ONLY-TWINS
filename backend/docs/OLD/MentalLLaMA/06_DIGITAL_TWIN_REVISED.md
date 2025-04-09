# NOVAMIND: Digital Twin

## Introduction to Psychiatric Digital Twins

The NOVAMIND Digital Twin is a computational representation of a patient's psychiatric state that enables personalized medicine at an unprecedented level of precision. Unlike traditional psychiatric approaches that rely solely on subjective assessments, the Digital Twin integrates multimodal data sources to create a dynamic, evolving model of each patient's mental health.

At the core of our Digital Twin architecture is **MentaLLaMA**, a specialized large language model designed specifically for mental health analysis. This advanced AI system provides interpretable results across multiple mental health tasks including depression detection, risk assessment, and sentiment analysis—all within a HIPAA-compliant framework.

## Core Digital Twin Components

| Component | Purpose | Primary Model | Implementation |
|-----------|---------|---------------|----------------|
| Mental Health Analysis & Insights | Analyze patient text (notes, journals) for risk assessment, sentiment, psycho-linguistic indicators, and generate interpretable rationales. | MentaLLaMA-33B-lora | Prompt-based inference via Transformers/PEFT on GPU instances |
| (Future) Biometric-Mental Correlation | Link physiological markers to mental states | TBD | TBD |
| (Future) Precision Medication Modeling | Personalize medication selection based on genetics and history | TBD | TBD |

### System Architecture Overview

```
┌─────────────────────────┐       ┌─────────────────────────┐
│                         │       │                         │
│  Data Integration Layer │◄─────►│  Digital Twin Core      │
│                         │       │                         │
└───────────┬─────────────┘       └───────────┬─────────────┘
            │                                 │
            │                                 │
            ▼                                 ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│                         │       │                         │
│  Wearable & EHR         │       │  MentaLLaMA ML Model    │
│  Integration Services   │       │ Inference Service (GPU) │
│                         │       │                         │
└───────────┬─────────────┘       └───────────┬─────────────┘
            │                                 │
            │                                 │
            ▼                                 ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│                         │       │                         │
│  Event-Driven Update    │◄─────►│  Clinical Application   │
│  Pipeline               │       │  Services               │
│                         │       │                         │
└─────────────────────────┘       └─────────────────────────┘
```

## Clean Architecture Implementation

The Digital Twin subsystem adheres to the NOVAMIND Clean Architecture principles:

### Domain Layer
- Pure business logic representing psychiatric concepts
- Model-agnostic interfaces for analysis services (e.g., `MentalHealthAnalysisService` interface)
- Value objects for various psychiatric assessments and biometric measures
- No dependencies on specific AI models or frameworks

### Application Layer
- Digital Twin orchestration services
- Use cases for clinical applications (e.g., `AnalyzePatientJournalUseCase`, `AssessRiskLevelUseCase`)
- Logic for constructing prompts and interpreting model outputs
- PHI detection and sanitization orchestration (before text analysis)
- Responsible for processing model outputs into domain entities

### Infrastructure Layer
- AI model adapters (e.g., `MentaLLaMAAdapter`) implementing domain interfaces
- GPU resource management (via SageMaker/EC2)
- Model loading and inference logic (using Transformers/PEFT)
- PHI detection services (e.g., AWS Comprehend Medical adapter)
- Wearable data integration services (if/when added)

### Presentation Layer
- RESTful API for Digital Twin interaction (e.g., triggering analysis)
- Clinical dashboard data endpoints (displaying analysis results)
- Mobile app integration endpoints
- Pydantic schemas for input/output validation

## Key Differentiators

1. **Specialized Mental Health LLM**: Leverages MentaLLaMA, a model specifically fine-tuned for mental health analysis, providing clinical-grade insights beyond general-purpose LLMs.
2. **Interpretable Explanations**: MentaLLaMA provides clear rationales for its assessments, enhancing clinical transparency and trustworthiness.
3. **Longitudinal Analysis**: Continuously evolves as new data (including text analysis) is incorporated.
4. **Multimodal Integration**: Combines AI-driven text analysis with other clinical data, and in the future, objective biometric data.
5. **HIPAA-Compliant By Design**: Built with multi-layer PHI protection, ensuring patient data is secure throughout the analysis pipeline.

## MentaLLaMA: Mental Health Analysis Engine

### Model Overview

MentaLLaMA is the first open-source large language model specifically fine-tuned for mental health analysis, providing interpretable results across multiple mental health tasks. It was developed by researchers from the National Centre for Text Mining and the University of Manchester.

**Key Specifications**:
- **Base Architecture**: Built on Vicuna-33B, an instruction-tuned version of Meta's LLaMA
- **Specialization**: Fine-tuned on the Interpretable Mental Health Instruction (IMHI) dataset with 105K instruction samples
- **Efficiency**: Uses Low-Rank Adaptation (LoRA) for parameter-efficient fine-tuning
- **Interpretability**: Uniquely designed to provide explanations/rationales for its assessments

### Analysis Capabilities

MentaLLaMA can perform the following mental health analysis tasks:

1. **Depression Detection**: Identifying signs of depression in text
2. **Stress Detection**: Analyzing text for stress indicators
3. **Mental Disorders Detection**: Recognizing various mental health conditions
4. **Stress Cause Detection**: Identifying potential causes of stress
5. **Depression/Suicide Cause Detection**: Analyzing factors related to depression or suicidal ideation
6. **Loneliness Detection**: Identifying indicators of loneliness
7. **Wellness Dimensions Detection**: Analyzing various dimensions of wellness
8. **Interpersonal Risk Factors Detection**: Identifying risk factors in interpersonal relationships

Each analysis comes with interpretable explanations that provide rationales for the model's conclusions.

### Technical Implementation

#### Infrastructure Requirements

- **GPU Resources**: MentaLLaMA-33B-lora requires high-end GPU capabilities
  - Recommended: AWS EC2 instances with NVIDIA V100/A100 GPUs (e.g., `p3.2xlarge` or larger) or equivalent SageMaker endpoints
  - Memory Optimization: Use 8-bit or 4-bit quantization to reduce VRAM requirements
- **Software Stack**:
  - Python 3.9+
  - PyTorch 2.0+ with CUDA support
  - Hugging Face `transformers` (4.28+)
  - PEFT (Parameter-Efficient Fine-Tuning) library
  - `bitsandbytes` for quantization (optional)

### HIPAA-Compliant Analysis Flow

The mental health analysis process follows these steps to ensure HIPAA compliance:

1. **Data Preparation**: Patient text data (e.g., journal entries, session notes) is collected through secure channels
2. **PHI Detection & Removal**: **All text undergoes automated PHI detection and masking *before* being sent to MentaLLaMA**
3. **Prompt Construction**: Appropriate prompts are generated based on the analysis type requested
4. **Model Inference**: Sanitized text and prompt are sent to the MentaLLaMA model for inference
5. **Result Processing**: Model outputs are parsed, structured, and validated
6. **Storage & Display**: Results are securely stored and displayed in the clinician dashboard

For complete details on MentaLLaMA implementation, see `docs/MentalLLaMA/01_MENTAL_HEALTH_MODELING.md` and `docs/MentalLLaMA/02_AWS_DEPLOYMENT_HIPAA.md`.

## Implementation Roadmap

| Phase | Focus | Timeline | Key Deliverable |
|-------|-------|----------|-----------------|
| 1 | MentaLLaMA Integration | Month 1-2 | MentaLLaMA-33B-lora inference service setup (GPU instance), basic prompt-based analysis API |
| 2 | Core Analysis Features | Month 3-4 | Integration of MentaLLaMA for risk assessment, sentiment analysis, and rationale generation into application services |
| 3 | Dashboard Integration | Month 5-6 | Displaying MentaLLaMA insights (risk levels, sentiment trends, rationales) in clinician dashboards |
| 4 | Advanced Features & Refinement | Month 7-8 | Exploring further MentaLLaMA use cases (e.g., summarization), prompt engineering, performance optimization |

## Digital Twin API

### API Design Principles

The Digital Twin API follows these core principles:

1. **Clean Architecture**: Presentation layer is separate from business logic
2. **HIPAA Compliance**: Authentication, authorization, and audit logging for all endpoints
3. **RESTful Design**: Resource-oriented endpoints with appropriate HTTP methods
4. **Versioning**: Explicit versioning to support backwards compatibility
5. **Documentation**: OpenAPI/Swagger documentation for all endpoints

### API Endpoints

#### Mental Health Analysis API

```
POST /api/v1/digital-twin/{patient_id}/mental-health-analysis
```

Performs mental health analysis on patient text using the MentaLLaMA model. PHI is automatically detected and removed before sending to the model.

**Request Body:**

```json
{
  "text_content": "Patient text to analyze...",
  "analysis_type": "risk_assessment", 
  "generation_params": {
    "max_tokens": 256,
    "temperature": 0.7
  }
}
```

**Response Example (Risk Assessment):**

```json
{
  "success": true,
  "data": {
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "analysis_type": "risk_assessment",
    "result": {
      "risk_level": "medium",
      "rationale": "The text mentions feelings of hopelessness and social withdrawal, consistent with moderate risk indicators. No explicit suicidal ideation mentioned.",
      "confidence": 0.85
    },
    "model_version": "klyang/MentaLLaMA-33B-lora_v1.0",
    "generated_at": "2025-03-28T01:05:00Z"
  },
  "error": null
}
```

For detailed API documentation, see `docs/08_ML_MICROSERVICES_API.md`.

## HIPAA Compliance Summary

| Component | HIPAA Requirement | Implementation Approach |
|-----------|-------------------|-------------------------|
| Data Storage | Encryption at rest | AWS S3/RDS with server-side encryption (SSE-KMS) |
| Data Transmission | Encryption in transit | TLS 1.3 for all API communications |
| Model Inference | Minimum necessary use | PHI is masked/removed *before* sending text to MentaLLaMA. Use AWS Comprehend Medical or similar for PHI detection. |
| Access Controls | Role-based authorization | Fine-grained permissions for model interactions and data access. |
| Audit Logging | Comprehensive tracking | All model operations logged with user, time, purpose (without PHI in logs). |

### Enhanced PHI Protection for MentaLLaMA

A multi-layered approach to PHI protection is implemented:

1. **Primary Layer**: AWS Comprehend Medical PHI detection
2. **Secondary Layer**: Custom regex patterns for domain-specific identifiers
3. **Tertiary Layer**: Specialized NER model for mental health text (optional)

All detected PHI is masked with standardized tokens before being sent to the model, ensuring HIPAA compliance while preserving the semantic structure of the text for analysis.

For complete details on our HIPAA-compliant AWS deployment, see `docs/MentalLLaMA/02_AWS_DEPLOYMENT_HIPAA.md`.

## Performance Optimization

### Model Optimization Techniques

1. **Quantization**:
   - 8-bit Quantization: Reduces VRAM by ~50% with minimal quality impact
   - 4-bit Quantization: Reduces VRAM by ~75% with moderate quality impact
   - Implementation using `bitsandbytes` library

2. **Caching Strategy**:
   - Cache MentaLLaMA analysis results for identical sanitized inputs/prompts
   - Use Redis or similar for distributed caching
   - Configure TTL based on clinical requirements

3. **Inference Optimization**:
   - On-demand GPU provisioning to minimize costs
   - Batch processing for multiple analyses when possible
   - Parallel PHI detection and prompt construction

## Clinical Integration Guidelines

While MentaLLaMA provides powerful analysis capabilities, it is essential to remember:

1. **Human Oversight**: All model outputs must be reviewed by qualified clinicians
2. **Decision Support Only**: The system is positioned as a clinical decision support tool, not a diagnostic system
3. **Clear Disclaimers**: Any patient-facing applications must include clear disclaimers
4. **Ongoing Validation**: Regular clinical validation of model outputs should be conducted

### Implementation Best Practices

1. **Appropriate Use Cases**:
   - Initial screening of patient-generated text
   - Identifying potential risk factors
   - Generating hypotheses for clinician consideration
   - Tracking sentiment and themes over time

2. **Clinician Training**:
   - Train clinicians on system capabilities and limitations
   - Provide guidance on interpreting model outputs
   - Establish protocols for handling concerning outputs

## Conclusion

The NOVAMIND Digital Twin, powered by MentaLLaMA-33B-lora, represents a significant advancement in concierge psychiatric care. By leveraging state-of-the-art AI specifically fine-tuned for mental health analysis, while maintaining strict HIPAA compliance, the platform provides clinicians with unprecedented insights into patient mental states and helps deliver truly personalized care.

The integration of MentaLLaMA enables interpretable, clinically relevant analysis of patient-generated text, augmenting clinical decision-making while ensuring that the human clinician remains at the center of the therapeutic relationship.