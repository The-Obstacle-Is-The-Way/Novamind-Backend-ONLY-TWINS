# Digital Twin Core Architecture

## Overview

The Digital Twin Core is the central nervous system of the Novamind platform, providing a comprehensive virtual representation of a patient's mental health state. It integrates data from multiple sources and ML models to create a dynamic, multi-dimensional model of the patient that evolves over time.

## Architectural Principles

The Digital Twin Core is built on the following principles:

1. **Clean Architecture**: Strict separation of concerns with domain-driven design
2. **Event-Driven**: Components communicate via events for loose coupling
3. **HIPAA-First**: PHI protection is built into every layer
4. **Real-Time Ready**: Designed for immediate updates and low-latency interaction
5. **ML-Augmented**: Leverages multiple ML models for enhanced insight

## System Layers

```
┌────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                             │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │                │  │                │  │                    │    │
│  │ REST API       │  │ GraphQL API    │  │ WebSocket API      │    │
│  │                │  │                │  │                    │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
└───────────────────────────┬────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────────┐
│                     APPLICATION LAYER                              │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │                │  │                │  │                    │    │
│  │ Patient        │  │ Assessment     │  │ Treatment          │    │
│  │ Service        │  │ Service        │  │ Service            │    │
│  │                │  │                │  │                    │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │                │  │                │  │                    │    │
│  │ Digital Twin   │  │ Notification   │  │ Analysis           │    │
│  │ Service        │  │ Service        │  │ Service            │    │
│  │                │  │                │  │                    │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
└───────────────────────────┬────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────────┐
│                     DOMAIN LAYER                                   │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │                │  │                │  │                    │    │
│  │ Patient        │  │ Assessment     │  │ Treatment          │    │
│  │ Entities       │  │ Entities       │  │ Entities           │    │
│  │                │  │                │  │                    │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │                │  │                │  │                    │    │
│  │ Digital Twin   │  │ Risk           │  │ Clinical           │    │
│  │ Entities       │  │ Entities       │  │ Entities           │    │
│  │                │  │                │  │                    │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
└───────────────────────────┬────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                           │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │                │  │                │  │                    │    │
│  │ Database       │  │ ML Model       │  │ Event Bus          │    │
│  │ Repository     │  │ Client         │  │                    │    │
│  │                │  │                │  │                    │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │                │  │                │  │                    │    │
│  │ External       │  │ Authentication │  │ Notification       │    │
│  │ APIs           │  │ Service        │  │ Service            │    │
│  │                │  │                │  │                    │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

## Domain Model

### Core Entities

1. **Patient**: The individual receiving care
   - Demographics, contact information, preferences
   - Medical history and current conditions
   - Privacy preferences and consent settings

2. **DigitalTwin**: The virtual representation of a patient
   - Current mental state snapshot
   - Historical states and trajectories
   - Predicted future states and risks
   - Multi-dimensional clinical profile

3. **Assessment**: Clinical evaluation results
   - Standardized measures (PHQ-9, GAD-7, etc.)
   - Clinician observations and ratings
   - Patient self-reports
   - Objective measurements

4. **Treatment**: Therapeutic interventions
   - Medication management
   - Psychotherapy approaches
   - Behavioral interventions
   - Lifestyle modifications

5. **ClinicalInsight**: AI-generated clinical observations
   - ML-derived risk assessments
   - NLP-extracted patterns
   - Treatment recommendations
   - Pattern identification

## Event-Driven Communication

The Digital Twin uses an event-driven architecture for real-time updates:

### Key Events

1. **PatientDataUpdated**: Triggered when any patient data changes
2. **AssessmentCompleted**: Fired when a new assessment is completed
3. **TreatmentModified**: Signals a change in treatment protocol
4. **RiskLevelChanged**: Indicates a change in patient risk status
5. **DigitalTwinUpdated**: Broadcast when the twin model is refreshed

### Event Flow Example

```
├── Patient completes PHQ-9
│   └── AssessmentCompleted event fired
│       ├── DigitalTwinService receives event
│       │   └── Updates Digital Twin model
│       │       └── DigitalTwinUpdated event fired
│       │           ├── Analysis Service receives event
│       │           │   └── Runs risk prediction model
│       │           │       └── RiskLevelChanged event fired (if applicable)
│       │           │           └── Notification Service receives event
│       │           │               └── Alerts clinician if high risk
│       │           └── Visualization Service receives event
│       │               └── Updates 3D brain visualization
```

## Data Flow

### Inbound Data Processing

1. **Data Collection**: Multiple sources feed into the Digital Twin
   - PAT assessments (structured data)
   - Clinical notes (unstructured data)
   - Patient journals (semi-structured data)
   - External integrations (EHR data, wearables)

2. **PHI Protection**: All data undergoes PHI detection and masking
   - Regex-based pattern matching
   - ML-enhanced PHI detection
   - Tokenization and masking
   - Audit logging

3. **Pre-processing Pipeline**: Data normalization and preparation
   - Format standardization
   - Missing data handling
   - Temporal alignment
   - Feature extraction

4. **Model Integration**: Data is processed by ML components
   - MentalLLaMA-33B NLP analysis
   - XGBoost prediction engine
   - Anomaly detection
   - Temporal pattern recognition

### Information Generation

1. **DigitalTwin Synthesis**: Creating a unified patient representation
   - Current state aggregation
   - Historical trajectory analysis
   - Prediction generation
   - Confidence scoring

2. **Clinical Insight Extraction**: Deriving actionable insights
   - Risk factor identification
   - Treatment recommendation generation
   - Outcome prediction
   - Pattern detection

3. **Visualization Preparation**: Data transformation for UI rendering
   - 3D brain region mapping
   - Temporal data sequencing
   - Interactive data structuring
   - Level-of-detail optimization

## Security Architecture

The Digital Twin implements a comprehensive security model:

1. **Encryption**: All data is encrypted at rest and in transit
   - TLS 1.3 for all communications
   - AES-256 for data at rest
   - Encrypted database columns
   - Secure key management

2. **Authentication & Authorization**: Role-based access control
   - JWT token authentication
   - OAuth 2.0 and OpenID Connect
   - Fine-grained permission system
   - Context-aware authorization

3. **PHI Protection**: Multiple layers of PHI safeguards
   - Data minimization principle
   - Automatic PHI detection
   - Tokenization for identifiers
   - Secure audit logging

4. **Compliance**: HIPAA and regulatory adherence
   - BAA with all service providers
   - Comprehensive audit trails
   - Regular security assessments
   - Incident response procedures

## Technical Implementation

### AWS Service Architecture

The Digital Twin is implemented using AWS services:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS IMPLEMENTATION                               │
│                                                                     │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │                │   │                │   │                    │   │
│  │ API Gateway    │   │ AppSync        │   │ WebSocket API     │   │
│  │ (REST API)     │   │ (GraphQL)      │   │ (Real-time)       │   │
│  │                │   │                │   │                    │   │
│  └───────┬────────┘   └────────┬───────┘   └──────────┬─────────┘   │
│          │                     │                      │             │
│          ▼                     ▼                      ▼             │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │                │   │                │   │                    │   │
│  │ Lambda         │   │ Lambda         │   │ Lambda             │   │
│  │ (Services)     │   │ (Resolvers)    │   │ (Notifications)    │   │
│  │                │   │                │   │                    │   │
│  └───────┬────────┘   └────────┬───────┘   └──────────┬─────────┘   │
│          │                     │                      │             │
│          ▼                     ▼                      ▼             │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │                │   │                │   │                    │   │
│  │ EventBridge    │   │ SQS            │   │ SNS                │   │
│  │ (Event Bus)    │   │ (Queues)       │   │ (Notifications)    │   │
│  │                │   │                │   │                    │   │
│  └───────┬────────┘   └────────┬───────┘   └──────────┬─────────┘   │
│          │                     │                      │             │
│          ▼                     ▼                      ▼             │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │                │   │                │   │                    │   │
│  │ SageMaker      │   │ ECS/Fargate    │   │ Lambda             │   │
│  │ (ML Models)    │   │ (Services)     │   │ (Processing)       │   │
│  │                │   │                │   │                    │   │
│  └───────┬────────┘   └────────┬───────┘   └──────────┬─────────┘   │
│          │                     │                      │             │
│          ▼                     ▼                      ▼             │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │                │   │                │   │                    │   │
│  │ DynamoDB       │   │ Aurora         │   │ S3                 │   │
│  │ (NoSQL)        │   │ (PostgreSQL)   │   │ (Object Storage)   │   │
│  │                │   │                │   │                    │   │
│  └────────────────┘   └────────────────┘   └────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Code Organization

The Digital Twin components follow the clean architecture pattern:

```
app/
├── domain/
│   ├── entities/
│   │   ├── patient.py
│   │   ├── digital_twin.py
│   │   ├── assessment.py
│   │   └── treatment.py
│   ├── value_objects/
│   │   ├── risk_level.py
│   │   └── clinical_insight.py
│   └── interfaces/
│       ├── repositories/
│       └── services/
├── application/
│   ├── use_cases/
│   │   ├── create_digital_twin.py
│   │   ├── update_digital_twin.py
│   │   └── generate_insights.py
│   ├── services/
│   │   ├── digital_twin_service.py
│   │   ├── risk_assessment_service.py
│   │   └── notification_service.py
│   └── dto/
│       ├── patient_dto.py
│       └── assessment_dto.py
├── infrastructure/
│   ├── repositories/
│   │   ├── dynamo_patient_repository.py
│   │   └── postgres_assessment_repository.py
│   ├── external/
│   │   ├── mental_llama_client.py
│   │   └── xgboost_client.py
│   └── messaging/
│       ├── event_bus.py
│       └── notification_provider.py
└── presentation/
    ├── api/
    │   ├── rest/
    │   │   ├── patient_controller.py
    │   │   └── assessment_controller.py
    │   └── graphql/
    │       ├── schema/
    │       └── resolvers/
    ├── websocket/
    └── dto/
        ├── requests/
        └── responses/
```

## References

- [ML Integration Guide](../MentalLLaMA/02_INTEGRATION.md)
- [XGBoost Prediction Engine](../XGBoost/01_PREDICTION_ENGINE.md)
- [PAT Integration](../PAT/03_INTEGRATION.md)
- [AWS Infrastructure](../AWS/01_INFRASTRUCTURE.md)
- [HIPAA Compliance](../AWS/03_HIPAA_COMPLIANCE.md)