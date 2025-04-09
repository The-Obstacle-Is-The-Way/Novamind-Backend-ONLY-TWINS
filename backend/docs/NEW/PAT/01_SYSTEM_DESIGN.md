# PAT (Pretrained Actigraphy Transformer): System Design

## Overview

The Pretrained Actigraphy Transformer (PAT) is a specialized AI system for analyzing actigraphy data from wearable devices, forming a critical component of the Novamind Digital Twin platform. PAT processes movement patterns, sleep metrics, and other biometric data to provide insights into patients' physical behaviors and their relationship to mental health states.

## Core Principles

PAT is designed around several core principles:

1. **Movement Analysis**: Extracts meaningful patterns from raw accelerometer data
2. **Sleep Characterization**: Identifies sleep quality, duration, and disruption patterns
3. **Activity Recognition**: Classifies different physical activities and their intensities
4. **Temporal Modeling**: Tracks changes in biometric patterns over time
5. **Multimodal Integration**: Combines wearable data with other patient information
6. **HIPAA Compliance**: Ensures security and privacy of sensitive biometric data

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   PAT SYSTEM ARCHITECTURE                           │
│                                                                     │
│  ┌───────────────┐   ┌─────────────────┐   ┌────────────────────┐   │
│  │               │   │                 │   │                    │   │
│  │ Data          │   │ Transformer     │   │ Feature            │   │
│  │ Ingestion     │◄─►│ Model           │◄─►│ Extraction        │   │
│  │               │   │                 │   │                    │   │
│  └───────┬───────┘   └─────────┬───────┘   └────────┬───────────┘   │
│          │                     │                    │               │
│          ▼                     ▼                    ▼               │
│  ┌───────────────┐   ┌─────────────────┐   ┌────────────────────┐   │
│  │               │   │                 │   │                    │   │
│  │ Pattern       │   │ Sleep           │   │ Anomaly            │   │
│  │ Recognition   │◄─►│ Analysis        │◄─►│ Detection          │   │
│  │               │   │                 │   │                    │   │
│  └───────┬───────┘   └─────────┬───────┘   └────────┬───────────┘   │
│          │                     │                    │               │
│          └─────────────────────┼────────────────────┘               │
│                                │                                    │
│                                ▼                                    │
│  ┌───────────────┐   ┌─────────────────┐   ┌────────────────────┐   │
│  │               │   │                 │   │                    │   │
│  │ Digital Twin  │   │ Clinician       │   │ Research           │   │
│  │ Integration   │   │ Dashboard       │   │ Analytics          │   │
│  │               │   │                 │   │                    │   │
│  └───────────────┘   └─────────────────┘   └────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

1. **Data Ingestion**
   - Processes raw data from various wearable devices (smartwatches, fitness trackers)
   - Standardizes input formats from different manufacturers
   - Handles real-time streaming and batch uploads
   - Performs initial data validation and cleaning

2. **Transformer Model**
   - Implements the core pretrained transformer architecture
   - Processes time-series actigraphy data sequence
   - Applies self-attention mechanisms to identify temporal patterns
   - Trained on large-scale NHANES actigraphy datasets (~29k participants)

3. **Feature Extraction**
   - Derives meaningful features from raw accelerometer data
   - Calculates activity metrics (intensity, duration, type)
   - Extracts circadian rhythm indicators
   - Identifies movement signatures associated with mental health states

4. **Pattern Recognition**
   - Classifies physical activity types and intensities
   - Identifies behavioral patterns (e.g., restlessness, agitation)
   - Recognizes routine deviations and habit changes
   - Correlates movement patterns with psychological states

5. **Sleep Analysis**
   - Identifies sleep onset and wake times
   - Characterizes sleep quality and disruptions
   - Detects sleep architecture based on movement patterns
   - Analyzes consistency of sleep-wake schedules

6. **Anomaly Detection**
   - Identifies unusual activity or sleep patterns
   - Detects significant deviations from patient baselines
   - Flags patterns associated with clinical deterioration
   - Provides early warning of behavior changes requiring attention

7. **Digital Twin Integration**
   - Feeds processed biometric insights into Digital Twin model
   - Receives contextual information about medications and treatments
   - Synchronizes with other Digital Twin components
   - Updates behavioral representations in real-time

## Actigraphy Analysis Capabilities

PAT provides sophisticated analysis of wearable device data:

### Activity Analysis

| Analysis Type | Description | Features | Clinical Relevance |
|--------------|-------------|----------|-------------------|
| Activity Levels | Quantification of overall movement | Daily counts, intensity minutes | Energy levels, psychomotor changes |
| Behavioral Patterns | Recognition of routine activities | Pattern consistency, time spent in activities | Executive function, behavioral activation |
| Movement Quality | Analysis of movement characteristics | Smoothness, variability, acceleration | Psychomotor agitation/retardation |
| Circadian Rhythms | 24-hour activity patterns | Rhythm stability, amplitude, phase | Mood disorders, sleep-wake disruption |

### Sleep Analysis

| Analysis Type | Description | Features | Clinical Relevance |
|--------------|-------------|----------|-------------------|
| Sleep Duration | Total time spent sleeping | Total sleep time, efficiency | Insomnia, hypersomnia |
| Sleep Quality | Characteristics of sleep periods | Fragmentation, WASO, sleep latency | Sleep disorders, medication effects |
| Sleep-Wake Patterns | Consistency of sleep timing | Bedtime variability, regularity | Circadian rhythm disorders |
| Sleep Architecture | Inference of sleep stages | Movement signatures of sleep phases | Sleep quality assessment |

### Behavioral Analysis

| Analysis Type | Description | Features | Clinical Relevance |
|--------------|-------------|----------|-------------------|
| Social Rhythms | Timing of daily activities | Routine consistency, social timing | Bipolar disorder, depression |
| Behavioral Activation | Level of engagement in activities | Activity variety, intensity | Depression, behavioral interventions |
| Stress Signatures | Movement patterns during stress | Micro-movements, restlessness | Anxiety, stress reactivity |
| Environmental Interaction | Context-specific behaviors | Location-based activity profiles | Avoidance, engagement patterns |

## Transformer Model Architecture

PAT implements a specialized transformer architecture for actigraphy analysis:

### Model Specifications

```
┌───────────────────────────────────────────────────────────────┐
│                 TRANSFORMER ARCHITECTURE                      │
│                                                               │
│  ┌─────────────┐                                              │
│  │             │                                              │
│  │ Raw         │                                              │
│  │ Actigraphy  │                                              │
│  │ Input       │                                              │
│  └──────┬──────┘                                              │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐                                              │
│  │             │                                              │
│  │ Positional  │                                              │
│  │ Encoding    │                                              │
│  │             │                                              │
│  └──────┬──────┘                                              │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │                  Transformer Encoder                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │  │             │  │             │  │             │     │  │
│  │  │ Multi-Head  │  │ Feed        │  │ Layer       │     │  │
│  │  │ Attention   │──►│ Forward     │──►│ Norm       │────┐│  │
│  │  │             │  │             │  │             │    ││  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││  │
│  │                                                       ▼│  │
│  │  ┌──────────────────────────────────────────────────┐ ││  │
│  │  │                                                  │ ││  │
│  │  │              Nx Encoder Layers                   │ ││  │
│  │  │                                                  │ ││  │
│  │  └──────────────────────────────────────────────────┘ ││  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐      ┌────────────────┐                     │
│  │             │      │                │                     │
│  │ Feature     │◄────►│ Feature        │                     │
│  │ Vectors     │      │ Pooling        │                     │
│  │             │      │                │                     │
│  └──────┬──────┘      └────────────────┘                     │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐      ┌────────────────┐                     │
│  │             │      │                │                     │
│  │ Task-       │◄────►│ Classification │                     │
│  │ Specific    │      │ Regression     │                     │
│  │ Heads       │      │ Embedding      │                     │
│  └─────────────┘      └────────────────┘                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

1. **PAT-S (Small)**:
   - 6 transformer layers
   - 128-dimensional embeddings
   - 4 attention heads
   - 15M parameters
   - Suitable for edge deployment

2. **PAT-M (Medium)**:
   - 12 transformer layers
   - 256-dimensional embeddings
   - 8 attention heads
   - 63M parameters
   - Balance of performance and resource use

3. **PAT-L (Large)**:
   - 24 transformer layers
   - 512-dimensional embeddings
   - 16 attention heads
   - 230M parameters
   - Highest accuracy for complex patterns

### Pre-training Approach

PAT is pre-trained on actigraphy data using several self-supervised tasks:

1. **Masked Activity Prediction**: 
   - Randomly mask segments of activity data
   - Train model to reconstruct masked regions
   - Helps model learn activity patterns and transitions

2. **Contrastive Learning**:
   - Create positive pairs from same user, different time windows
   - Create negative pairs from different users
   - Train model to minimize distance between positive pairs

3. **Future Activity Prediction**:
   - Predict activity patterns in future time windows
   - Encourages learning of temporal dependencies and rhythms

4. **Activity Classification**:
   - Classify segments into sleep, sedentary, light, moderate, vigorous activity
   - Uses partially labeled data from NHANES and research datasets

## Integration with Digital Twin

### Data Flow 

```
┌────────────────────────────────────────────────────────────────────┐
│                 PAT-DIGITAL TWIN INTEGRATION                       │
│                                                                    │
│  ┌────────────────┐                          ┌────────────────┐    │
│  │                │                          │                │    │
│  │ Wearable       │                          │ Digital Twin   │    │
│  │ Device         │◄────────────────────────►│ Context        │    │
│  │                │                          │                │    │
│  └───────┬────────┘                          └────────┬───────┘    │
│          │                                            │            │
│          ▼                                            ▼            │
│  ┌────────────────┐                          ┌────────────────┐    │
│  │                │                          │                │    │
│  │ Data           │                          │ Patient        │    │
│  │ Ingestion      │◄────────────────────────►│ History        │    │
│  │                │                          │                │    │
│  └───────┬────────┘                          └────────────────┘    │
│          │                                                         │
│          ▼                                                         │
│  ┌────────────────┐                          ┌────────────────┐    │
│  │                │                          │                │    │
│  │ PAT            │                          │ Past           │    │
│  │ Processing     │◄────────────────────────►│ Activity       │    │
│  │                │                          │ Data           │    │
│  └───────┬────────┘                          └────────────────┘    │
│          │                                                         │
│          ▼                                                         │
│  ┌────────────────┐                          ┌────────────────┐    │
│  │                │                          │                │    │
│  │ Feature        │───────────────────────┬─►│ Digital Twin   │    │
│  │ Extraction     │                       │  │ Update         │    │
│  │                │                       │  │                │    │
│  └───────┬────────┘                       │  └────────────────┘    │
│          │                                │                        │
│          ▼                                │                        │
│  ┌────────────────┐                       │  ┌────────────────┐    │
│  │                │                       │  │                │    │
│  │ Insight        │                       └─►│ ML Model       │    │
│  │ Generation     │                          │ Training       │    │
│  │                │                          │                │    │
│  └───────┬────────┘                          └────────────────┘    │
│          │                                                         │
│          ▼                                                         │
│  ┌────────────────┐                          ┌────────────────┐    │
│  │                │                          │                │    │
│  │ Clinician      │                          │ Visualization  │    │
│  │ Dashboard      │◄────────────────────────►│ Engine         │    │
│  │                │                          │                │    │
│  └────────────────┘                          └────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Key Integration Points

1. **Contextual Processing**:
   - Digital Twin provides medication information to interpret activity changes
   - Patient history informs baseline expectations for activity patterns
   - Treatment context helps distinguish therapeutic vs. adverse changes

2. **Real-time Model Updates**:
   - Activity insights immediately update Digital Twin model
   - Anomalous patterns trigger model recalibration
   - Longitudinal data enhances prediction accuracy

3. **Bidirectional Information Flow**:
   - Digital Twin provides context for movement pattern interpretation
   - Activity results inform Digital Twin parameters
   - Changes in Digital Twin state trigger focused activity monitoring

4. **Clinical Decision Support**:
   - Combined insights guide treatment recommendations
   - Activity trends highlight areas for behavioral intervention
   - Patient-specific activity signatures inform personalized care

## Technical Implementation

### AWS Architecture

PAT is implemented on AWS with the following components:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AWS IMPLEMENTATION                              │
│                                                                     │
│  ┌────────────────┐   ┌─────────────────┐   ┌────────────────────┐  │
│  │                │   │                 │   │                    │  │
│  │ IoT Core       │   │ Kinesis         │   │ S3                 │  │
│  │ (Device Conn)  │──►│ (Data Streams)  │──►│ (Raw Data)         │  │
│  │                │   │                 │   │                    │  │
│  └────────────────┘   └─────────┬───────┘   └────────────────────┘  │
│                                 │                                    │
│                                 ▼                                    │
│  ┌────────────────┐   ┌─────────────────┐   ┌────────────────────┐  │
│  │                │   │                 │   │                    │  │
│  │ Lambda         │   │ SageMaker       │   │ DynamoDB           │  │
│  │ (Processing)   │◄──┤ (PAT Model)     │◄──┤ (Feature Store)    │  │
│  │                │   │                 │   │                    │  │
│  └───────┬────────┘   └─────────────────┘   └────────────────────┘  │
│          │                                                           │
│          ▼                                                           │
│  ┌────────────────┐   ┌─────────────────┐   ┌────────────────────┐  │
│  │                │   │                 │   │                    │  │
│  │ EventBridge    │   │ Step Functions  │   │ Aurora             │  │
│  │ (Event Bus)    │◄──┤ (Workflows)     │◄──┤ (Relationship DB)  │  │
│  │                │   │                 │   │                    │  │
│  └────────────────┘   └─────────────────┘   └────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

1. **Data Processing**:
   - Python with NumPy/SciPy for signal processing
   - Pandas for time-series handling
   - PyTorch for model implementation
   - ONNX for model deployment

2. **Backend**:
   - FastAPI for REST endpoints
   - SQLAlchemy for database access
   - Pydantic for data validation
   - Redis for caching

3. **Database**:
   - DynamoDB for time-series data
   - Amazon Aurora for relational data
   - S3 for raw data storage
   - Efficient time-series indexing

4. **Security**:
   - End-to-end encryption for all PHI
   - Role-based access control
   - AWS Cognito for authentication
   - Comprehensive audit logging
   - PHI detection and protection

## Code Architecture

The PAT system follows clean architecture principles:

```
app/
├── domain/
│   ├── entities/
│   │   ├── actigraphy_reading.py
│   │   ├── activity_pattern.py
│   │   └── sleep_profile.py
│   ├── value_objects/
│   │   ├── activity_metrics.py
│   │   └── sleep_metrics.py
│   └── interfaces/
│       ├── repositories/
│       └── services/
├── application/
│   ├── use_cases/
│   │   ├── process_actigraphy_data.py
│   │   ├── analyze_sleep_patterns.py
│   │   └── detect_anomalies.py
│   ├── services/
│   │   ├── actigraphy_service.py
│   │   ├── pattern_recognition_service.py
│   │   └── digital_twin_integration_service.py
│   └── dto/
│       ├── actigraphy_dto.py
│       └── insight_dto.py
├── infrastructure/
│   ├── repositories/
│   │   ├── dynamo_actigraphy_repository.py
│   │   └── s3_raw_data_repository.py
│   ├── external/
│   │   ├── digital_twin_client.py
│   │   └── wearable_device_client.py
│   └── persistence/
│       ├── models/
│       └── mappers/
└── presentation/
    ├── api/
    │   ├── rest/
    │   │   ├── actigraphy_controller.py
    │   │   └── insight_controller.py
    │   └── graphql/
    │       ├── schema/
    │       └── resolvers/
    └── dto/
        ├── requests/
        └── responses/
```

## Data Processing Pipeline

The PAT data processing pipeline has the following stages:

1. **Data Collection**:
   - Receive raw data from wearable devices
   - Handle various sampling rates (30-100 Hz typical)
   - Support batch uploads and real-time streaming
   - Store raw data with backup and versioning

2. **Preprocessing**:
   - Filter noise and artifacts from raw signals
   - Normalize across different device specifications
   - Segment data into analysis windows
   - Apply signal processing techniques

3. **Feature Extraction**:
   - Calculate time-domain features (mean, variance, etc.)
   - Extract frequency-domain features via FFT
   - Compute derived metrics (jerk, energy, entropy)
   - Generate domain-specific features (rest periods, active periods)

4. **Pattern Analysis**:
   - Apply transformer model to extract temporal patterns
   - Identify activity types and transitions
   - Detect sleep periods and characteristics
   - Recognize daily routines and deviations

5. **Clinical Insight Generation**:
   - Correlate activity patterns with clinical states
   - Generate sleep quality metrics
   - Identify behavioral activation levels
   - Flag anomalous patterns for clinical attention

6. **Digital Twin Integration**:
   - Update activity components of Digital Twin
   - Correlate with other data sources
   - Generate visualizations for clinical dashboard
   - Provide data for prediction models

## Future Development

PAT's roadmap includes the following enhancements:

1. **Advanced Features**:
   - Multi-modal sensor fusion (heart rate, GPS, temperature)
   - Contextual awareness through phone sensors
   - Enhanced stress detection algorithms
   - Personalized baseline adaptation

2. **Technology Improvements**:
   - Edge computing deployment for lower latency
   - Battery optimization for continuous monitoring
   - Improved transfer learning for new device types
   - Smaller models for resource-constrained environments

3. **Clinical Enhancements**:
   - Expanded psychiatric condition signatures
   - Medication response monitoring
   - Early relapse detection for various conditions
   - Integration with ecological momentary assessment

## References

- [Digital Twin Integration Guide](../DigitalTwin/02_DATA_INTEGRATION.md)
- [MentalLLaMA NLP Integration](../MentalLLaMA/02_INTEGRATION.md)
- [XGBoost Prediction Engine](../XGBoost/01_PREDICTION_ENGINE.md)
- [AWS Implementation](../AWS/01_INFRASTRUCTURE.md)