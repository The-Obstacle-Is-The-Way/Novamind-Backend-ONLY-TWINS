# Novamind Digital Twin Platform: Canonical Architecture

## Overview

This document establishes the canonical architecture for the Novamind Digital Twin Platform. It serves as the definitive source of truth for all architectural decisions, providing clear standards for implementing a clean, forward-focused codebase that aligns with SOLID principles and achieves production readiness.

All existing and future code must adhere to these architectural standards. Any code that conflicts with these standards should be refactored or replaced during the implementation phase.

## Guiding Principles

1. **Clean Architecture**: Strict separation between domain, application, and infrastructure layers
2. **No Legacy Dependencies**: Complete elimination of patient/EHR dependencies
3. **Single Identity Abstraction**: Consolidation on DigitalTwinSubject as the canonical identity model
4. **Trinity Stack Integration**: Standardized integration of MentalLLaMA, PAT, and XGBoost
5. **HIPAA Compliance by Design**: Security, privacy, and audit controls built into the architecture
6. **Production Excellence**: Comprehensive testing, monitoring, and deployment capabilities

## Core Domain Model

### Identity Abstraction

The `DigitalTwinSubject` is the canonical identity model for all Digital Twin functionality:

```python
@dataclass(frozen=True)
class DigitalTwinSubject:
    """
    Subject identity for the Digital Twin platform.
    Core domain entity that represents an individual subject.
    """
    subject_id: UUID
    identity_type: str  # "research", "clinical", "anonymous"
    demographic_factors: Dict[str, Any]  # Age, sex, etc. without direct PHI
    clinical_factors: Dict[str, Any]  # Diagnostic codes, medication classes, etc.
    creation_date: datetime
    last_updated: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Factory methods
    @classmethod
    def create_research_subject(cls, **kwargs) -> "DigitalTwinSubject":
        """Create a research subject with appropriate defaults."""
        # Implementation
    
    @classmethod
    def create_clinical_subject(cls, **kwargs) -> "DigitalTwinSubject":
        """Create a clinical subject with appropriate defaults."""
        # Implementation
    
    @classmethod
    def create_anonymous_subject(cls, **kwargs) -> "DigitalTwinSubject":
        """Create an anonymous subject with minimal information."""
        # Implementation
```

Key characteristics:
- Immutable (frozen dataclass)
- No direct PHI fields
- No patient references
- Standardized demographic and clinical factors

### Digital Twin State

The `DigitalTwinState` is the core model representing the complete psychiatric digital twin:

```python
@dataclass(frozen=True)
class DigitalTwinState:
    """
    Core representation of the Digital Twin state.
    Comprehensive snapshot of a subject's mental health model.
    """
    subject_id: UUID  # Reference to DigitalTwinSubject
    timestamp: datetime
    state_id: UUID
    brain_regions: Dict[BrainRegion, BrainRegionState]
    neurotransmitters: Dict[Neurotransmitter, NeurotransmitterState]
    neural_connections: List[NeuralConnection]
    clinical_insights: List[ClinicalInsight]
    temporal_patterns: List[TemporalPattern]
    update_source: Optional[str] = None
    version: int = 1
    
    # Factory methods
    @classmethod
    def create_initial(cls, subject_id: UUID) -> "DigitalTwinState":
        """Create initial state with default values."""
        # Implementation
    
    # Utility methods
    def with_updated_brain_regions(self, regions: Dict[BrainRegion, BrainRegionState]) -> "DigitalTwinState":
        """Create new state with updated brain regions."""
        # Implementation
```

Key characteristics:
- Immutable (frozen dataclass)
- References subject_id instead of patient_id
- Comprehensive representation of psychiatric state
- Factory and utility methods to create new states

### Supporting Domain Entities

```python
@dataclass(frozen=True)
class BrainRegionState:
    """State of a specific brain region in the Digital Twin."""
    region: BrainRegion
    activation_level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    related_symptoms: List[str]
    clinical_significance: ClinicalSignificance

@dataclass(frozen=True)
class NeurotransmitterState:
    """State of a specific neurotransmitter in the Digital Twin."""
    neurotransmitter: Neurotransmitter
    level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    clinical_significance: ClinicalSignificance

@dataclass(frozen=True)
class ClinicalInsight:
    """Clinical insight derived from Digital Twin analysis."""
    id: UUID
    title: str
    description: str
    source: str  # e.g., "PAT", "MentalLLaMA", "XGBoost"
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    clinical_significance: ClinicalSignificance
    brain_regions: List[BrainRegion]
    neurotransmitters: List[Neurotransmitter]
    supporting_evidence: List[str]
    recommended_actions: List[str]

@dataclass(frozen=True)
class TemporalSequence:
    """Time series data for physiological or behavioral measurements."""
    id: UUID
    subject_id: UUID  # Reference to DigitalTwinSubject
    feature_names: List[str]
    timestamps: List[datetime]
    values: List[List[float]]
    metadata: Dict[str, Any]
```

Key characteristics:
- All entities immutable (frozen dataclasses)
- No direct patient references
- Comprehensive psychiatric modeling
- Clear separation of concerns

## Repository Interfaces

### DigitalTwinSubjectRepository

```python
class DigitalTwinSubjectRepository(ABC):
    """Repository interface for Digital Twin Subject persistence."""
    
    @abstractmethod
    async def save(self, subject: DigitalTwinSubject) -> UUID:
        """Save a subject identity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, subject_id: UUID) -> Optional[DigitalTwinSubject]:
        """Retrieve a subject by ID."""
        pass
    
    @abstractmethod
    async def list_by_type(self, identity_type: str) -> List[DigitalTwinSubject]:
        """List all subjects of a specific type."""
        pass
    
    @abstractmethod
    async def get_by_demographic_factors(
        self, 
        factors: Dict[str, Any]
    ) -> List[DigitalTwinSubject]:
        """Find subjects matching demographic factors."""
        pass
    
    @abstractmethod
    async def delete(self, subject_id: UUID) -> bool:
        """Delete a subject."""
        pass
```

### DigitalTwinStateRepository

```python
class DigitalTwinStateRepository(ABC):
    """Repository interface for Digital Twin State persistence."""
    
    @abstractmethod
    async def save(self, state: DigitalTwinState) -> UUID:
        """Save a digital twin state."""
        pass
    
    @abstractmethod
    async def get_by_id(self, state_id: UUID) -> Optional[DigitalTwinState]:
        """Retrieve a state by ID."""
        pass
    
    @abstractmethod
    async def get_latest_by_subject_id(
        self, 
        subject_id: UUID
    ) -> Optional[DigitalTwinState]:
        """Get the latest state for a subject."""
        pass
    
    @abstractmethod
    async def get_history_by_subject_id(
        self, 
        subject_id: UUID, 
        limit: int = 10
    ) -> List[DigitalTwinState]:
        """Get state history for a subject."""
        pass
    
    @abstractmethod
    async def delete(self, state_id: UUID) -> bool:
        """Delete a state."""
        pass
```

### TemporalSequenceRepository

```python
class TemporalSequenceRepository(ABC):
    """Repository interface for Temporal Sequence persistence."""
    
    @abstractmethod
    async def save(self, sequence: TemporalSequence) -> UUID:
        """Save a temporal sequence."""
        pass
    
    @abstractmethod
    async def get_by_id(self, sequence_id: UUID) -> Optional[TemporalSequence]:
        """Retrieve a sequence by ID."""
        pass
    
    @abstractmethod
    async def get_by_subject_and_features(
        self, 
        subject_id: UUID, 
        features: List[str],
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[TemporalSequence]:
        """Get sequences for a subject and features."""
        pass
    
    @abstractmethod
    async def delete(self, sequence_id: UUID) -> bool:
        """Delete a sequence."""
        pass
```

## Trinity Stack Service Interfaces

### MentalLLaMAService

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
    
    # Additional methods as in the refactored interface...
```

### PATService

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
            analysis_parameters: Optional analysis parameters
            
        Returns:
            Analysis results
        """
        pass
    
    # Additional methods as in the refactored interface...
```

### XGBoostService

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
    
    # Additional methods as in the refactored interface...
```

## Application Services

### DigitalTwinService

```python
class DigitalTwinService:
    """
    Application service for Digital Twin operations.
    Coordinates domain logic for digital twin creation and analysis.
    """
    
    def __init__(
        self,
        subject_repository: DigitalTwinSubjectRepository,
        state_repository: DigitalTwinStateRepository,
        mentalllama_service: Optional[MentalLLaMAService] = None,
        pat_service: Optional[PATService] = None,
        xgboost_service: Optional[XGBoostService] = None,
        audit_service: Optional[AuditService] = None
    ):
        """Initialize with required dependencies."""
        self.subject_repository = subject_repository
        self.state_repository = state_repository
        self.mentalllama_service = mentalllama_service
        self.pat_service = pat_service
        self.xgboost_service = xgboost_service
        self.audit_service = audit_service
    
    async def create_digital_twin(
        self,
        subject_id: UUID,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Create a new digital twin for a subject.
        
        Args:
            subject_id: Subject identifier
            initial_data: Optional initial data
            
        Returns:
            State ID of the created digital twin
        """
        # Implementation
    
    async def update_digital_twin(
        self,
        subject_id: UUID,
        update_data: Dict[str, Any],
        source: str
    ) -> UUID:
        """
        Update a digital twin with new data.
        
        Args:
            subject_id: Subject identifier
            update_data: Data for the update
            source: Source of the update
            
        Returns:
            State ID of the updated digital twin
        """
        # Implementation
    
    async def analyze_with_trinity_stack(
        self,
        subject_id: UUID,
        clinical_data: Optional[Dict[str, Any]] = None,
        actigraphy_data: Optional[Dict[str, Any]] = None,
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze digital twin using the Trinity Stack.
        
        Args:
            subject_id: Subject identifier
            clinical_data: Optional clinical data
            actigraphy_data: Optional actigraphy data
            analysis_options: Optional analysis options
            
        Returns:
            Combined analysis results
        """
        # Implementation
```

### TemporalAnalysisService

```python
class TemporalAnalysisService:
    """
    Application service for temporal analysis operations.
    Coordinates domain logic for time series analysis and pattern detection.
    """
    
    def __init__(
        self,
        sequence_repository: TemporalSequenceRepository,
        subject_repository: DigitalTwinSubjectRepository,
        pat_service: Optional[PATService] = None,
        xgboost_service: Optional[XGBoostService] = None,
        audit_service: Optional[AuditService] = None
    ):
        """Initialize with required dependencies."""
        # Implementation
    
    async def create_temporal_sequence(
        self,
        subject_id: UUID,
        feature_names: List[str],
        timestamps: List[datetime],
        values: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Create a new temporal sequence.
        
        Args:
            subject_id: Subject identifier
            feature_names: Names of the features
            timestamps: Sequence timestamps
            values: Sequence values
            metadata: Optional metadata
            
        Returns:
            ID of the created sequence
        """
        # Implementation
    
    async def detect_patterns(
        self,
        subject_id: UUID,
        features: List[str],
        time_range: Optional[Tuple[datetime, datetime]] = None,
        detection_options: Optional[Dict[str, Any]] = None
    ) -> List[TemporalPattern]:
        """
        Detect patterns in temporal sequences.
        
        Args:
            subject_id: Subject identifier
            features: Features to analyze
            time_range: Optional time range
            detection_options: Optional detection options
            
        Returns:
            Detected temporal patterns
        """
        # Implementation
```

## API Design

### RESTful Endpoints

All API endpoints follow these conventions:

1. **Versioning**: All endpoints are under `/api/v1`
2. **Resource-Based**: Endpoints are organized around resources
3. **HTTP Methods**: Use appropriate HTTP methods (GET, POST, PUT, DELETE)
4. **Request Validation**: All requests validated with Pydantic models
5. **Response Consistency**: Consistent response format
6. **Error Handling**: Structured error responses

Example endpoint structure:

```
/api/v1/digital-twin-subjects
├── POST /                         # Create subject
├── GET /{subject_id}              # Get subject
└── PUT /{subject_id}              # Update subject

/api/v1/digital-twins
├── POST /subjects/{subject_id}    # Create digital twin
├── GET /{twin_state_id}           # Get digital twin state
└── PUT /subjects/{subject_id}     # Update digital twin

/api/v1/temporal-sequences
├── POST /subjects/{subject_id}    # Create sequence
├── GET /{sequence_id}             # Get sequence
└── GET /subjects/{subject_id}     # List sequences for subject
```

### Request/Response Models

All API requests and responses use Pydantic models:

```python
class SubjectCreate(BaseModel):
    """Request model for creating a Digital Twin Subject."""
    identity_type: str
    demographic_factors: Dict[str, Any]
    clinical_factors: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class SubjectResponse(BaseModel):
    """Response model for Digital Twin Subject operations."""
    subject_id: UUID
    identity_type: str
    demographic_factors: Dict[str, Any]
    clinical_factors: Dict[str, Any]
    creation_date: datetime
    last_updated: datetime
    metadata: Dict[str, Any]
```

## Infrastructure Components

### Database

1. **PostgreSQL**: Primary relational database
2. **SQLAlchemy**: ORM for database access
3. **Alembic**: Database migrations

### Caching

1. **Redis**: In-memory cache for performance
2. **Caching Strategies**: TTL-based, invalidation-based

### Security

1. **JWT Authentication**: Token-based authentication
2. **Role-Based Authorization**: Fine-grained access control
3. **PHI Protection**: Middleware for PHI protection
4. **Encryption**: Data encryption at rest and in transit
5. **Audit Logging**: Comprehensive audit logging

### Monitoring

1. **OpenTelemetry**: Tracing and metrics
2. **Health Checks**: API endpoint health monitoring
3. **Logging**: Structured logging with context

### Deployment

1. **Docker**: Containerization
2. **Kubernetes**: Container orchestration
3. **CI/CD Pipeline**: GitHub Actions

## Production Readiness Requirements

### Testing Standards

1. **Unit Tests**: 90%+ coverage for domain and application layers
2. **Integration Tests**: Comprehensive API endpoint testing
3. **Security Tests**: Authentication, authorization, and PHI protection
4. **Performance Tests**: Load testing for critical endpoints

### Documentation Standards

1. **API Documentation**: OpenAPI/Swagger
2. **Code Documentation**: Docstrings for all public methods
3. **Architecture Documentation**: Up-to-date architecture documentation

### Monitoring Standards

1. **Metrics Collection**: Key performance indicators
2. **Alerting**: Alerts for critical issues
3. **Dashboards**: Operational dashboards

## Implementation Strategy

The implementation will follow a phased approach:

1. **Core Domain Implementation**: DigitalTwinSubject, DigitalTwinState
2. **Repository Implementation**: Subject, State, and Sequence repositories
3. **Trinity Stack Integration**: MentalLLaMA, PAT, XGBoost services
4. **API Implementation**: RESTful endpoints and Pydantic models
5. **Infrastructure Implementation**: Database, security, monitoring
6. **Testing and Documentation**: Comprehensive tests and documentation

## Conclusion

This document establishes the canonical architecture for the Novamind Digital Twin Platform. All implementation work should adhere to these standards to create a clean, maintainable, and production-ready codebase.

The architecture completely eliminates legacy patient/EHR dependencies while maintaining the rich domain modeling and advanced analytical capabilities of the psychiatric digital twin concept. By standardizing on the DigitalTwinSubject abstraction and the Trinity Stack integration, the platform achieves a clean, forward-focused design that will support long-term evolution and enhancement.