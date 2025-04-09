# Novamind Digital Twin Platform: Trinity Stack Integration

## Overview

This document provides detailed guidelines for the integration of the Trinity Stack components - MentalLLaMA, PAT (Pretrained Actigraphy Transformer), and XGBoost - into the refactored Novamind Digital Twin Platform. The Trinity Stack represents the core AI/ML functionality that powers the psychiatric digital twin, enabling advanced clinical insights, behavioral analysis, and treatment optimization.

## Trinity Stack Architecture

The Trinity Stack consists of three specialized AI/ML components that work together to provide a comprehensive psychiatric digital twin:

```
                       ┌───────────────────┐
                       │  Digital Twin Core │
                       └─────────┬─────────┘
                               ┌─┴─┐
            ┌──────────────────┤   ├───────────────────┐
            │                  │   │                   │
            ▼                  ▼   ▼                   ▼
┌─────────────────────┐ ┌───────────────┐ ┌──────────────────────┐
│   MentalLLaMA-33B   │ │      PAT      │ │  XGBoost Prediction  │
│   Language Model    │ │  Actigraphy   │ │       Engine         │
└─────────┬───────────┘ └───────┬───────┘ └──────────┬───────────┘
          │                     │                    │
          ▼                     ▼                    ▼
┌─────────────────────┐ ┌───────────────┐ ┌──────────────────────┐
│  Clinical Language  │ │  Behavioral   │ │    Treatment &       │
│    Understanding    │ │    Analysis   │ │  Outcome Prediction  │
└─────────────────────┘ └───────────────┘ └──────────────────────┘
```

### Component Roles

1. **MentalLLaMA-33B**: Advanced language model specialized for psychiatric text comprehension
   - Clinical language understanding
   - Symptom identification and classification
   - Neurotransmitter and brain region mapping from clinical descriptions

2. **PAT (Pretrained Actigraphy Transformer)**: Behavioral and physiological data analysis
   - Activity and sleep pattern analysis
   - Circadian rhythm detection
   - Behavioral anomaly identification

3. **XGBoost Prediction Engine**: Machine learning prediction system
   - Treatment outcome prediction
   - Risk factor identification
   - Digital twin state evolution forecasting

## Integration Principles

The Trinity Stack integration follows these core principles:

1. **Clean Interfaces**: Components interact through well-defined, standardized interfaces
2. **Domain-Driven Design**: Components emit and consume domain entities, not raw data
3. **Immutable Data Flow**: Data flows through immutable transformations between components
4. **PHI Isolation**: Components never process direct PHI, only working with de-identified data
5. **Versioned Models**: All models are explicitly versioned for reproducibility
6. **Explainable Results**: All component outputs include confidence and explanation metadata

## Service Interface Guidelines

All Trinity Stack components adhere to the following interface guidelines:

### Common Interface Patterns

All service interfaces should:

1. Use asynchronous methods (`async def`) to support high-throughput processing
2. Accept explicit `subject_id` parameters (never `patient_id`)
3. Return domain entities rather than raw data structures
4. Include confidence scores with all predictions
5. Support optional context parameters for operation tracing
6. Implement comprehensive error handling

### Interface Segregation

Each service interface should be segregated into focused functional areas:

1. **Core Analysis**: Primary analytical functions
2. **Model Management**: Model versioning and configuration
3. **Integration Support**: Functions specifically for cross-component coordination

## MentalLLaMA Integration

### Core Service Interface

```python
class MentalLLaMAService(ABC):
    """
    Service for MentalLLaMA language model operations.
    Core component of the Trinity Stack for clinical text understanding.
    """
    
    @abstractmethod
    async def analyze_clinical_text(
        self, 
        text: str,
        context: Optional[Dict[str, Any]] = None,
        subject_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Analyze clinical text to extract insights.
        
        Args:
            text: Clinical text to analyze
            context: Optional context information
            subject_id: Optional subject identifier
            
        Returns:
            Analysis results
        """
        pass
    
    @abstractmethod
    async def generate_clinical_insights(
        self,
        clinical_data: Dict[str, Any],
        digital_twin_state: Optional[DigitalTwinState] = None
    ) -> List[ClinicalInsight]:
        """
        Generate clinical insights from clinical data.
        
        Args:
            clinical_data: Clinical data to analyze
            digital_twin_state: Optional digital twin state
            
        Returns:
            List of clinical insights
        """
        pass
    
    @abstractmethod
    async def map_brain_regions(
        self,
        symptoms: List[str],
        intensity: Optional[Dict[str, float]] = None
    ) -> Dict[BrainRegion, float]:
        """
        Map symptoms to brain regions with activation levels.
        
        Args:
            symptoms: List of symptoms to map
            intensity: Optional dictionary of symptom intensities
            
        Returns:
            Dictionary mapping brain regions to activation levels
        """
        pass
```

### Implementation Guidelines

1. **Prompt Templates**:
   - Use parameterized prompt templates
   - Store templates in configuration
   - Validate input before prompt generation

```python
class PromptTemplate:
    """Template for generating LLM prompts from parameters."""
    
    def __init__(self, template: str, parameter_types: Dict[str, type]):
        self.template = template
        self.parameter_types = parameter_types
        
    def format(self, parameters: Dict[str, Any]) -> str:
        """Generate a prompt from parameters."""
        # Validate parameters against expected types
        for param_name, param_type in self.parameter_types.items():
            if param_name not in parameters:
                raise ValueError(f"Missing required parameter: {param_name}")
            
            if not isinstance(parameters[param_name], param_type):
                raise TypeError(f"Parameter {param_name} should be of type {param_type}")
        
        # Format the prompt
        return self.template.format(**parameters)
```

2. **Response Parsing**:
   - Use structured response formats
   - Implement robust error handling
   - Map raw responses to domain entities

```python
class ResponseParser:
    """Parser for structured responses from LLM."""
    
    def parse_clinical_insights(self, response: str) -> List[ClinicalInsight]:
        """Parse clinical insights from LLM response."""
        try:
            # Extract JSON structure from response
            # Map to domain entities
            # Validate results
            insights = []
            # ... parsing logic ...
            return insights
        except Exception as e:
            logger.error(f"Failed to parse clinical insights: {e}")
            raise ResponseParsingError(f"Failed to parse clinical insights: {e}")
```

3. **Model Selection**:
   - Support multiple model versions
   - Select models based on context
   - Fall back to simpler models when needed

```python
class ModelSelector:
    """Selector for appropriate LLM model version."""
    
    def select_model(self, task: str, context: Dict[str, Any]) -> str:
        """Select appropriate model version for task."""
        # Determine complexity of task
        # Check available resources
        # Select appropriate model version
        # ... selection logic ...
        return model_version
```

## PAT Integration

### Core Service Interface

```python
class PATService(ABC):
    """
    Service for PAT (Pretrained Actigraphy Transformer) operations.
    Core component of the Trinity Stack for behavioral and physiological analysis.
    """
    
    @abstractmethod
    async def analyze_actigraphy_data(
        self,
        actigraphy_data: Dict[str, Any],
        subject_id: Optional[UUID] = None,
        analysis_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze actigraphy data to extract features and patterns.
        
        Args:
            actigraphy_data: Raw actigraphy data
            subject_id: Optional subject identifier
            analysis_parameters: Optional parameters for the analysis
            
        Returns:
            Analysis results
        """
        pass
    
    @abstractmethod
    async def detect_circadian_rhythms(
        self,
        physiological_data: Dict[str, Any],
        data_types: Optional[List[str]] = None,
        minimum_days: int = 7,
        subject_id: Optional[UUID] = None
    ) -> List[TemporalPattern]:
        """
        Detect circadian rhythms from physiological data.
        
        Args:
            physiological_data: Physiological time series data
            data_types: Optional types of data to include in analysis
            minimum_days: Minimum days of data required
            subject_id: Optional subject identifier
            
        Returns:
            List of detected temporal patterns
        """
        pass
    
    @abstractmethod
    async def generate_behavioral_insights(
        self,
        behavioral_data: Dict[str, Any],
        physiological_data: Optional[Dict[str, Any]] = None,
        digital_twin_state: Optional[DigitalTwinState] = None,
        subject_id: Optional[UUID] = None
    ) -> List[ClinicalInsight]:
        """
        Generate clinical insights from behavioral and physiological data.
        
        Args:
            behavioral_data: Behavioral data
            physiological_data: Optional physiological data
            digital_twin_state: Optional Digital Twin state
            subject_id: Optional subject identifier
            
        Returns:
            List of clinical insights
        """
        pass
```

### Implementation Guidelines

1. **Time Series Preprocessing**:
   - Normalize data across different devices
   - Handle missing data points
   - Implement signal filtering 

```python
class TimeSeriesPreprocessor:
    """Preprocessor for time series data."""
    
    def normalize(self, time_series: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize time series data."""
        # ... normalization logic ...
        return normalized_data
    
    def handle_missing_data(self, time_series: Dict[str, Any]) -> Dict[str, Any]:
        """Handle missing data in time series."""
        # ... missing data handling logic ...
        return complete_data
    
    def filter_signals(self, time_series: Dict[str, Any]) -> Dict[str, Any]:
        """Apply filters to time series data."""
        # ... filtering logic ...
        return filtered_data
```

2. **Pattern Detection**:
   - Implement multi-scale pattern detection
   - Calculate pattern significance scores
   - Map patterns to domain entities

```python
class PatternDetector:
    """Detector for patterns in time series data."""
    
    def detect_patterns(self, time_series: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect patterns in time series data."""
        # ... detection logic ...
        return patterns
    
    def calculate_significance(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate significance scores for patterns."""
        # ... significance calculation logic ...
        return patterns_with_significance
    
    def map_to_temporal_patterns(self, patterns: List[Dict[str, Any]]) -> List[TemporalPattern]:
        """Map detected patterns to TemporalPattern domain entities."""
        # ... mapping logic ...
        return temporal_patterns
```

3. **Feature Extraction**:
   - Extract relevant behavioral features
   - Calculate derived metrics
   - Generate feature vectors for integration

```python
class FeatureExtractor:
    """Extractor for behavioral features from time series data."""
    
    def extract_features(self, time_series: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from time series data."""
        # ... extraction logic ...
        return features
    
    def calculate_metrics(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics from features."""
        # ... calculation logic ...
        return metrics
    
    def generate_feature_vector(self, metrics: Dict[str, Any]) -> List[float]:
        """Generate feature vector for machine learning models."""
        # ... vector generation logic ...
        return feature_vector
```

## XGBoost Integration

### Core Service Interface

```python
class XGBoostService(ABC):
    """
    Service for XGBoost prediction engine operations.
    Core component of the Trinity Stack for prediction and optimization.
    """
    
    @abstractmethod
    async def predict_treatment_outcomes(
        self,
        subject_id: UUID,
        digital_twin_state: DigitalTwinState,
        treatment_options: List[Dict[str, Any]],
        prediction_horizon: int = 90  # days
    ) -> Dict[str, Any]:
        """
        Predict outcomes for different treatment options.
        
        Args:
            subject_id: Subject identifier
            digital_twin_state: Current digital twin state
            treatment_options: Treatment options to evaluate
            prediction_horizon: Time horizon for predictions
            
        Returns:
            Predictions for each treatment option
        """
        pass
    
    @abstractmethod
    async def forecast_symptom_progression(
        self,
        subject_id: UUID,
        digital_twin_state: DigitalTwinState,
        symptoms: List[str],
        forecast_horizon: int = 90,  # days
        intervention: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Forecast the progression of symptoms over time.
        
        Args:
            subject_id: Subject identifier
            digital_twin_state: Current digital twin state
            symptoms: List of symptoms to forecast
            forecast_horizon: Time horizon for forecast
            intervention: Optional intervention to model
            
        Returns:
            Forecasted symptom trajectories
        """
        pass
    
    @abstractmethod
    async def explain_prediction(
        self,
        subject_id: UUID,
        digital_twin_state: DigitalTwinState,
        prediction_id: str,
        detail_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Provide an explanation for a specific prediction.
        
        Args:
            subject_id: Subject identifier
            digital_twin_state: Current digital twin state
            prediction_id: ID of the prediction to explain
            detail_level: Level of detail in explanation
            
        Returns:
            Explanation of the prediction
        """
        pass
```

### Implementation Guidelines

1. **Feature Engineering**:
   - Create comprehensive feature set from digital twin state
   - Implement feature normalization
   - Handle categorical features

```python
class FeatureEngineering:
    """Feature engineering for XGBoost models."""
    
