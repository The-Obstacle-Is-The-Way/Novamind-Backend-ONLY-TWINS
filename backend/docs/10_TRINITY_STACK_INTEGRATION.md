# Novamind Digital Twin Platform: Trinity Stack Integration

## Overview

This document provides detailed guidelines for the integration of the Trinity Stack components - MentalLLaMA, PAT (Pretrained Actigraphy Transformer), and XGBoost - into the refactored Novamind Digital Twin Platform. The Trinity Stack represents the core AI/ML functionality that powers the psychiatric digital twin, enabling advanced clinical insights, behavioral analysis, and treatment optimization.

## Trinity Stack Architecture

The Trinity Stack consists of three specialized AI/ML components that work together to provide a comprehensive psychiatric digital twin:

```
                       ┌───────────────────┐
                       │ Digital Twin Core │
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
    
    def create_feature_set(self, digital_twin_state: DigitalTwinState) -> Dict[str, Any]:
        """Create feature set from digital twin state."""
        features = {}
        
        # Extract brain region features
        for region, state in digital_twin_state.brain_regions.items():
            features[f"brain_region_{region.value}_activation"] = state.activation_level
            features[f"brain_region_{region.value}_confidence"] = state.confidence
        
        # Extract neurotransmitter features
        for nt, state in digital_twin_state.neurotransmitters.items():
            features[f"neurotransmitter_{nt.value}_level"] = state.level
            features[f"neurotransmitter_{nt.value}_confidence"] = state.confidence
        
        # Extract temporal pattern features
        for i, pattern in enumerate(digital_twin_state.temporal_patterns):
            features[f"temporal_pattern_{i}_strength"] = pattern.strength
            features[f"temporal_pattern_{i}_confidence"] = pattern.confidence
        
        return features
    
    def normalize_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize features for model input."""
        # ... normalization logic ...
        return normalized_features
    
    def encode_categorical_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Encode categorical features for model input."""
        # ... encoding logic ...
        return encoded_features
```

2. **Model Ensemble**:
   - Use multiple XGBoost models for different prediction tasks
   - Implement model ensembling for improved accuracy
   - Handle model selection based on available data

```python
class ModelEnsemble:
    """Ensemble of XGBoost models for prediction tasks."""
    
    def __init__(self, models: Dict[str, Any]):
        self.models = models
    
    def select_models(self, task: str, available_features: List[str]) -> List[str]:
        """Select appropriate models for a task based on available features."""
        # ... selection logic ...
        return selected_model_ids
    
    def predict_with_ensemble(self, features: Dict[str, Any], model_ids: List[str]) -> Dict[str, Any]:
        """Make predictions using an ensemble of models."""
        # ... prediction logic ...
        return ensemble_predictions
    
    def calculate_ensemble_confidence(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for ensemble prediction."""
        # ... confidence calculation logic ...
        return confidence_score
```

3. **Explanation Generation**:
   - Implement SHAP values for feature importance
   - Generate natural language explanations
   - Provide visualization data for front-end display

```python
class ExplanationGenerator:
    """Generator for model prediction explanations."""
    
    def calculate_shap_values(self, model: Any, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate SHAP values for feature importance."""
        # ... SHAP calculation logic ...
        return shap_values
    
    def generate_natural_language_explanation(self, 
                                             prediction: Dict[str, Any], 
                                             shap_values: Dict[str, float]) -> str:
        """Generate natural language explanation of prediction."""
        # ... explanation generation logic ...
        return explanation
    
    def generate_visualization_data(self, shap_values: Dict[str, float]) -> Dict[str, Any]:
        """Generate visualization data for front-end display."""
        # ... visualization data generation logic ...
        return visualization_data
```

## Cross-Component Integration

### Trinity State Mapper

A critical component for Trinity Stack integration is the `TrinityStateMapper` which handles the mapping of component outputs to the unified `DigitalTwinState`:

```python
class TrinityStateMapper:
    """Mapper for Trinity Stack component outputs to DigitalTwinState."""
    
    def map_mentalllama_outputs(self, 
                               outputs: Dict[str, Any], 
                               current_state: DigitalTwinState) -> DigitalTwinState:
        """Map MentalLLaMA outputs to DigitalTwinState."""
        # Extract brain regions
        brain_regions = current_state.brain_regions.copy()
        for region_data in outputs.get("brain_regions", []):
            region = BrainRegion(region_data["region"])
            brain_regions[region] = BrainRegionState(
                region=region,
                activation_level=region_data["activation_level"],
                confidence=region_data["confidence"],
                related_symptoms=region_data.get("related_symptoms", []),
                clinical_significance=ClinicalSignificance(region_data["significance"])
            )
        
        # Extract neurotransmitters
        neurotransmitters = current_state.neurotransmitters.copy()
        for nt_data in outputs.get("neurotransmitters", []):
            nt = Neurotransmitter(nt_data["neurotransmitter"])
            neurotransmitters[nt] = NeurotransmitterState(
                neurotransmitter=nt,
                level=nt_data["level"],
                confidence=nt_data["confidence"],
                clinical_significance=ClinicalSignificance(nt_data["significance"])
            )
        
        # Extract clinical insights
        insights = list(current_state.clinical_insights)
        for insight_data in outputs.get("clinical_insights", []):
            insights.append(ClinicalInsight.create(
                title=insight_data["title"],
                description=insight_data["description"],
                source="MentalLLaMA",
                confidence=insight_data["confidence"],
                clinical_significance=ClinicalSignificance(insight_data["significance"]),
                brain_regions=[BrainRegion(r) for r in insight_data.get("brain_regions", [])],
                neurotransmitters=[Neurotransmitter(n) for n in insight_data.get("neurotransmitters", [])],
                supporting_evidence=insight_data.get("supporting_evidence", []),
                recommended_actions=insight_data.get("recommended_actions", [])
            ))
        
        # Create new state with updated components
        return DigitalTwinState(
            reference_id=current_state.reference_id,
            timestamp=datetime.now(),
            brain_regions=brain_regions,
            neurotransmitters=neurotransmitters,
            neural_connections=current_state.neural_connections,
            clinical_insights=insights,
            temporal_patterns=current_state.temporal_patterns,
            update_source="MentalLLaMA",
            version=current_state.version + 1
        )
    
    def map_pat_outputs(self, 
                        outputs: Dict[str, Any], 
                        current_state: DigitalTwinState) -> DigitalTwinState:
        """Map PAT outputs to DigitalTwinState."""
        # ... similar mapping logic for PAT ...
        pass
    
    def map_xgboost_outputs(self, 
                           outputs: Dict[str, Any], 
                           current_state: DigitalTwinState) -> DigitalTwinState:
        """Map XGBoost outputs to DigitalTwinState."""
        # ... similar mapping logic for XGBoost ...
        pass
```

### Trinity Orchestrator

The `TrinityOrchestrator` coordinates the integration of all Trinity Stack components:

```python
class TrinityOrchestrator:
    """Orchestrator for Trinity Stack component integration."""
    
    def __init__(
        self,
        mentalllama_service: MentalLLaMAService,
        pat_service: PATService,
        xgboost_service: XGBoostService,
        state_mapper: TrinityStateMapper,
        state_repository: DigitalTwinStateRepository
    ):
        self.mentalllama_service = mentalllama_service
        self.pat_service = pat_service
        self.xgboost_service = xgboost_service
        self.state_mapper = state_mapper
        self.state_repository = state_repository
    
    async def perform_comprehensive_analysis(
        self,
        subject_id: UUID,
        clinical_data: Optional[Dict[str, Any]] = None,
        behavioral_data: Optional[Dict[str, Any]] = None,
        physiological_data: Optional[Dict[str, Any]] = None,
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> DigitalTwinState:
        """
        Perform comprehensive analysis using all Trinity Stack components.
        
        Args:
            subject_id: Subject identifier
            clinical_data: Optional clinical data
            behavioral_data: Optional behavioral data
            physiological_data: Optional physiological data
            analysis_options: Optional analysis options
            
        Returns:
            Updated DigitalTwinState
        """
        # Get current state
        current_state = await self.state_repository.get_latest_by_subject_id(subject_id)
        if not current_state:
            current_state = DigitalTwinState.create_initial(subject_id)
        
        # Process with MentalLLaMA if clinical data available
        if clinical_data:
            mentalllama_outputs = await self.mentalllama_service.analyze_clinical_text(
                text=clinical_data.get("text", ""),
                context=analysis_options,
                subject_id=subject_id
            )
            current_state = self.state_mapper.map_mentalllama_outputs(
                mentalllama_outputs, 
                current_state
            )
        
        # Process with PAT if behavioral/physiological data available
        if behavioral_data or physiological_data:
            pat_outputs = {}
            
            if behavioral_data:
                behavioral_insights = await self.pat_service.analyze_actigraphy_data(
                    actigraphy_data=behavioral_data,
                    subject_id=subject_id,
                    analysis_parameters=analysis_options
                )
                pat_outputs["behavioral_insights"] = behavioral_insights
            
            if physiological_data:
                temporal_patterns = await self.pat_service.detect_circadian_rhythms(
                    physiological_data=physiological_data,
                    subject_id=subject_id
                )
                pat_outputs["temporal_patterns"] = temporal_patterns
            
            current_state = self.state_mapper.map_pat_outputs(
                pat_outputs, 
                current_state
            )
        
        # Process with XGBoost for predictions
        treatments = analysis_options.get("treatments", [])
        if treatments:
            treatment_predictions = await self.xgboost_service.predict_treatment_outcomes(
                subject_id=subject_id,
                digital_twin_state=current_state,
                treatment_options=treatments
            )
            current_state = self.state_mapper.map_xgboost_outputs(
                {"treatment_predictions": treatment_predictions}, 
                current_state
            )
        
        # Save updated state
        await self.state_repository.save(current_state)
        
        return current_state
```

## Testing Guidelines

### Unit Testing

Each Trinity Stack component should have comprehensive unit tests:

1. **Service Interface Tests**:
   - Test each method with mocked dependencies
   - Verify input validation
   - Test error handling

```python
class TestMentalLLaMAService:
    """Tests for MentalLLaMAService."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.model_mock = Mock()
        self.prompt_template_mock = Mock()
        self.response_parser_mock = Mock()
        
        self.service = MentalLLaMAServiceImpl(
            model=self.model_mock,
            prompt_templates={
                "analyze_clinical_text": self.prompt_template_mock,
            },
            response_parser=self.response_parser_mock
        )
    
    @pytest.mark.asyncio
    async def test_analyze_clinical_text(self):
        """Test analyze_clinical_text method."""
        # Arrange
        text = "Patient reports symptoms of depression and anxiety."
        self.prompt_template_mock.format.return_value = "Formatted prompt"
        self.model_mock.generate.return_value = "Model response"
        self.response_parser_mock.parse_clinical_analysis.return_value = {
            "entities": ["depression", "anxiety"],
            "brain_regions": [
                {"region": "amygdala", "activation_level": 0.8, "confidence": 0.7, "significance": "high"}
            ]
        }
        
        # Act
        result = await self.service.analyze_clinical_text(text)
        
        # Assert
        self.prompt_template_mock.format.assert_called_once()
        self.model_mock.generate.assert_called_once_with("Formatted prompt")
        self.response_parser_mock.parse_clinical_analysis.assert_called_once_with("Model response")
        assert "entities" in result
        assert "brain_regions" in result
        assert result["entities"] == ["depression", "anxiety"]
        assert len(result["brain_regions"]) == 1
        assert result["brain_regions"][0]["region"] == "amygdala"
```

2. **Implementation Tests**:
   - Test specific implementation classes
   - Verify integration with ML models
   - Test data transformation logic

```python
class TestPromptTemplate:
    """Tests for PromptTemplate."""
    
    def test_format_valid_parameters(self):
        """Test format with valid parameters."""
        template = PromptTemplate(
            template="Analyze the following symptoms: {symptoms}",
            parameter_types={"symptoms": str}
        )
        
        result = template.format({"symptoms": "depression, anxiety"})
        
        assert result == "Analyze the following symptoms: depression, anxiety"
    
    def test_format_missing_parameter(self):
        """Test format with missing parameter."""
        template = PromptTemplate(
            template="Analyze the following symptoms: {symptoms}",
            parameter_types={"symptoms": str}
        )
        
        with pytest.raises(ValueError, match="Missing required parameter: symptoms"):
            template.format({})
    
    def test_format_invalid_parameter_type(self):
        """Test format with invalid parameter type."""
        template = PromptTemplate(
            template="Analyze the following symptoms: {symptoms}",
            parameter_types={"symptoms": str}
        )
        
        with pytest.raises(TypeError, match="Parameter symptoms should be of type <class 'str'>"):
            template.format({"symptoms": 123})
```

### Integration Testing

Integration tests should verify the coordinated functionality of Trinity Stack components:

1. **Component Integration Tests**:
   - Test integration between two components
   - Verify data transformation between components
   - Test error propagation

```python
class TestTrinityStateMapper:
    """Tests for TrinityStateMapper."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mapper = TrinityStateMapper()
        self.initial_state = DigitalTwinState.create_initial(UUID("00000000-0000-0000-0000-000000000000"))
    
    def test_map_mentalllama_outputs(self):
        """Test mapping MentalLLaMA outputs to DigitalTwinState."""
        # Arrange
        mentalllama_outputs = {
            "brain_regions": [
                {
                    "region": "amygdala",
                    "activation_level": 0.8,
                    "confidence": 0.7,
                    "significance": "high",
                    "related_symptoms": ["anxiety"]
                }
            ],
            "neurotransmitters": [
                {
                    "neurotransmitter": "serotonin",
                    "level": 0.4,
                    "confidence": 0.6,
                    "significance": "moderate"
                }
            ],
            "clinical_insights": [
                {
                    "title": "Anxiety Detection",
                    "description": "Signs of anxiety detected",
                    "confidence": 0.7,
                    "significance": "moderate",
                    "brain_regions": ["amygdala"],
                    "neurotransmitters": ["serotonin"],
                    "supporting_evidence": ["Reported worry"],
                    "recommended_actions": ["Consider assessment"]
                }
            ]
        }
        
        # Act
        result_state = self.mapper.map_mentalllama_outputs(mentalllama_outputs, self.initial_state)
        
        # Assert
        assert BrainRegion.AMYGDALA in result_state.brain_regions
        assert result_state.brain_regions[BrainRegion.AMYGDALA].activation_level == 0.8
        assert Neurotransmitter.SEROTONIN in result_state.neurotransmitters
        assert result_state.neurotransmitters[Neurotransmitter.SEROTONIN].level == 0.4
        assert len(result_state.clinical_insights) == 1
        assert result_state.clinical_insights[0].title == "Anxiety Detection"
        assert result_state.update_source == "MentalLLaMA"
        assert result_state.version == self.initial_state.version + 1
```

2. **Orchestrator Tests**:
   - Test the Trinity Orchestrator
   - Verify coordination of all components
   - Test end-to-end workflows

```python
class TestTrinityOrchestrator:
    """Tests for TrinityOrchestrator."""
    
    @pytest.fixture
    def setup(self):
        """Set up test dependencies."""
        self.mentalllama_service = AsyncMock(spec=MentalLLaMAService)
        self.pat_service = AsyncMock(spec=PATService)
        self.xgboost_service = AsyncMock(spec=XGBoostService)
        self.state_mapper = Mock(spec=TrinityStateMapper)
        self.state_repository = AsyncMock(spec=DigitalTwinStateRepository)
        
        self.orchestrator = TrinityOrchestrator(
            mentalllama_service=self.mentalllama_service,
            pat_service=self.pat_service,
            xgboost_service=self.xgboost_service,
            state_mapper=self.state_mapper,
            state_repository=self.state_repository
        )
        
        # Create initial state
        self.subject_id = UUID("00000000-0000-0000-0000-000000000000")
        self.initial_state = DigitalTwinState.create_initial(self.subject_id)
        self.state_repository.get_latest_by_subject_id.return_value = self.initial_state
        
        # Set up mapper return values
        self.state_mapper.map_mentalllama_outputs.return_value = self.initial_state
        self.state_mapper.map_pat_outputs.return_value = self.initial_state
        self.state_mapper.map_xgboost_outputs.return_value = self.initial_state
    
    @pytest.mark.asyncio
    async def test_perform_comprehensive_analysis_clinical_data(self, setup):
        """Test comprehensive analysis with clinical data."""
        # Arrange
        clinical_data = {"text": "Patient reports symptoms of depression."}
        mentalllama_output = {"brain_regions": [], "neurotransmitters": []}
        self.mentalllama_service.analyze_clinical_text.return_value = mentalllama_output
        
        # Act
        result = await self.orchestrator.perform_comprehensive_analysis(
            subject_id=self.subject_id,
            clinical_data=clinical_data
        )
        
        # Assert
        self.state_repository.get_latest_by_subject_id.assert_called_once_with(self.subject_id)
        self.mentalllama_service.analyze_clinical_text.assert_called_once()
        self.state_mapper.map_mentalllama_outputs.assert_called_once_with(
            mentalllama_output, 
            self.initial_state
        )
        self.state_repository.save.assert_called_once()
        assert result == self.initial_state
```

## Best Practices

### Error Handling

All Trinity Stack components should implement consistent error handling:

1. **Specific Exception Types**:
   - Use domain-specific exception classes
   - Include error context in exceptions
   - Document exception scenarios

```python
class MentalLLaMAError(Exception):
    """Base class for MentalLLaMA service errors."""
    pass

class ModelExecutionError(MentalLLaMAError):
    """Error during model execution."""
    pass

class ResponseParsingError(MentalLLaMAError):
    """Error parsing model response."""
    pass

class InputValidationError(MentalLLaMAError):
    """Error validating input."""
    pass
```

2. **Graceful Degradation**:
   - Implement fallback mechanisms
   - Handle component failures gracefully
   - Maintain partial functionality

```python
async def analyze_with_fallback(text, context, subject_id):
    """Analyze text with fallback mechanisms."""
    try:
        # Try primary analysis
        return await primary_analysis(text, context, subject_id)
    except ModelExecutionError as e:
        logger.warning(f"Primary analysis failed: {e}. Falling back to secondary analysis.")
        try:
            # Try secondary analysis
            return await secondary_analysis(text, context, subject_id)
        except Exception as e:
            logger.error(f"Secondary analysis failed: {e}. Falling back to basic analysis.")
            # Fall back to basic analysis
            return basic_analysis(text)
```

### Versioning

Proper versioning is critical for all Trinity Stack components:

1. **Model Versioning**:
   - Track model versions explicitly
   - Store version with all outputs
   - Support version compatibility checks

```python
@dataclass(frozen=True)
class ModelVersion:
    """Immutable model version information."""
    major: int
    minor: int
    patch: int
    hash: str
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}-{self.hash[:8]}"
    
    def is_compatible_with(self, other: "ModelVersion") -> bool:
        """Check if this version is compatible with another."""
        return self.major == other.major
```

2. **Input/Output Schemas**:
   - Define explicit schemas for all interfaces
   - Version schemas with components
   - Validate against schemas at runtime

```python
class InputValidator:
    """Validator for component inputs."""
    
    def __init__(self, schema_version: str):
        self.schema_version = schema_version
        self.schemas = self._load_schemas(schema_version)
    
    def _load_schemas(self, version: str) -> Dict[str, Any]:
        """Load schemas for specific version."""
        # ... loading logic ...
        return schemas
    
    def validate(self, input_name: str, input_data: Dict[str, Any]) -> None:
        """Validate input data against schema."""
        schema = self.schemas.get(input_name)
        if not schema:
            raise ValueError(f"Unknown input: {input_name}")
        
        # ... validation logic ...
        if validation_errors:
            raise InputValidationError(f"Invalid input: {validation_errors}")
```

### Performance Optimization

Trinity Stack components should include performance optimizations:

1. **Batched Processing**:
   - Process multiple inputs in batches
   - Optimize for throughput
   - Support parallel processing

```python
class BatchProcessor:
    """Processor for batched operations."""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    async def process_batch(self, inputs: List[Dict[str, Any]], processor_func) -> List[Dict[str, Any]]:
        """Process a batch of inputs in parallel."""
        # Split into batches
        batches = [inputs[i:i+self.batch_size] for i in range(0, len(inputs), self.batch_size)]
        
        # Process batches
        results = []
        for batch in batches:
            # Process items in batch concurrently
            tasks = [processor_func(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    results.append({"error": str(result)})
                else:
                    results.append(result)
        
        return results
```

2. **Caching**:
   - Cache expensive computations
   - Implement cache invalidation
   - Support distributed caching

```python
class ResultCache:
    """Cache for expensive computations."""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache."""
        if key not in self.cache:
            return None
        
        result, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            # Expired
            del self.cache[key]
            return None
        
        return result
    
    def set(self, key: str, result: Dict[str, Any]) -> None:
        """Set result in cache."""
        self.cache[key] = (result, time.time())
    
    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        if key in self.cache:
            del self.cache[key]
```

## Conclusion

The Trinity Stack Integration Guidelines provide a comprehensive framework for implementing and integrating the three core AI/ML components of the Novamind Digital Twin Platform. By following these guidelines, developers can ensure a clean, maintainable, and performance-optimized implementation that adheres to the architectural principles established for the platform.

The Trinity Stack represents the core intelligence of the digital twin, enabling advanced psychiatric modeling and clinical decision support. Through proper integration, these components work together to create a comprehensive psychiatric digital twin that provides unparalleled insights and predictions for mental health care.