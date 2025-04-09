# Novamind Digital Twin Platform: Target Architecture

## Overview

This document defines the target architecture for the Novamind Digital Twin Platform after refactoring. It presents a clean, forward-focused design that eliminates legacy dependencies while strengthening the core psychiatric Digital Twin model.

## Architectural Principles

The target architecture adheres to the following principles:

1. **Clean Architecture**: Strict separation of concerns between domain, application, and infrastructure layers
2. **Domain-Driven Design**: Rich domain model that captures psychiatric digital twin concepts with precision
3. **SOLID Principles**: Single responsibility, open-closed, Liskov substitution, interface segregation, and dependency inversion
4. **HIPAA Compliance**: Privacy by design, with security and audit controls built into the architecture
5. **Testability**: Architecture designed for comprehensive testing at all levels
6. **No Legacy Dependencies**: Complete elimination of patient/EHR dependencies in favor of the Digital Twin Subject abstraction

## Target Architecture Components

### Core Domain Layer

#### Digital Twin Subject

```
DigitalTwinSubject
├── subject_id: UUID (primary identifier)
├── identity_type: str (research, clinical, anonymous)
├── demographic_factors: Dict[str, Any] (age, sex, etc.)
├── clinical_factors: Dict[str, Any] (relevant clinical information)
├── creation_date: datetime
└── metadata: Dict[str, Any] (extensible metadata)
```

The `DigitalTwinSubject` completely replaces the traditional `Patient` model, providing a generalized identity that supports all use cases without direct PHI dependencies.

#### Digital Twin Core

```
DigitalTwin
├── subject_id: UUID (reference to DigitalTwinSubject)
├── brain_regions: Dict[BrainRegion, BrainRegionState]
├── neurotransmitters: Dict[Neurotransmitter, NeurotransmitterState]
├── neural_connections: List[NeuralConnection]
├── clinical_insights: List[ClinicalInsight]
├── temporal_patterns: List[TemporalPattern]
└── metadata: Dict[str, Any]
```

The `DigitalTwin` maintains its comprehensive modeling capabilities but operates exclusively on `DigitalTwinSubject` identities.

#### Temporal Dynamics

```
TemporalSequence
├── id: UUID
├── subject_id: UUID (reference to DigitalTwinSubject)
├── feature_names: List[str]
├── timestamps: List[datetime]
├── values: List[List[float]]
└── metadata: Dict[str, Any]
```

The `TemporalSequence` model remains largely the same but consistently uses `subject_id` instead of any patient references.

### Repository Layer

All repositories operate on the standardized domain entities:

```
DigitalTwinSubjectRepository
├── save(subject: DigitalTwinSubject) -> UUID
├── get_by_id(subject_id: UUID) -> Optional[DigitalTwinSubject]
├── list_by_type(identity_type: str) -> List[DigitalTwinSubject]
└── delete(subject_id: UUID) -> bool

DigitalTwinRepository
├── save(digital_twin: DigitalTwin) -> UUID
├── get_by_id(twin_id: UUID) -> Optional[DigitalTwin]
├── get_by_subject_id(subject_id: UUID) -> Optional[DigitalTwin]
└── delete(twin_id: UUID) -> bool

TemporalSequenceRepository
├── save(sequence: TemporalSequence) -> UUID
├── get_by_id(sequence_id: UUID) -> Optional[TemporalSequence]
├── get_latest_by_feature(subject_id: UUID, feature_name: str) -> Optional[TemporalSequence]
└── list_by_subject(subject_id: UUID) -> List[TemporalSequence]
```

### Application Services

The application services coordinate domain operations and enforce business rules:

```
DigitalTwinService
├── create_digital_twin(subject_id: UUID, **kwargs) -> UUID
├── update_twin_state(twin_id: UUID, **kwargs) -> None
├── analyze_twin_state(twin_id: UUID) -> List[ClinicalInsight]
└── get_twin_visualization(twin_id: UUID) -> Dict[str, Any]

TemporalNeurotransmitterService
├── generate_neurotransmitter_time_series(subject_id: UUID, **kwargs) -> UUID
├── analyze_neurotransmitter_levels(subject_id: UUID, **kwargs) -> Optional[NeurotransmitterEffect]
├── simulate_treatment_response(subject_id: UUID, **kwargs) -> Dict[Neurotransmitter, UUID]
└── get_visualization_data(sequence_id: UUID, **kwargs) -> Dict[str, Any]

MLPredictionService
├── predict_treatment_response(subject_id: UUID, **kwargs) -> Dict[str, Any]
├── analyze_temporal_patterns(subject_id: UUID, **kwargs) -> List[TemporalPattern]
└── get_prediction_explanations(prediction_id: UUID) -> Dict[str, Any]
```

### API Layer

The API layer exposes the application services through RESTful endpoints:

```
/api/v1/digital-twin-subjects/
  ├── POST / - Create new subject
  ├── GET /{subject_id} - Get subject details
  └── PUT /{subject_id} - Update subject

/api/v1/digital-twins/
  ├── POST /subjects/{subject_id} - Create digital twin for subject
  ├── GET /{twin_id} - Get digital twin state
  └── PUT /{twin_id} - Update digital twin state

/api/v1/temporal-neurotransmitters/
  ├── POST /subjects/{subject_id}/time-series - Generate time series
  ├── GET /sequences/{sequence_id} - Get sequence details
  └── POST /subjects/{subject_id}/simulate - Simulate treatment response
```

### Infrastructure Components

The infrastructure layer implements the architecture with concrete technologies:

1. **Database**: PostgreSQL for relational data with SqlAlchemy ORM
2. **Caching**: Redis for performance optimization
3. **Security**: JWT authentication, role-based authorization
4. **Observability**: OpenTelemetry integration for tracing and metrics
5. **Deployment**: Docker containerization with Kubernetes orchestration
6. **ML Integration**: Versioned model management for XGBoost and LLM integrations

## Detailed Refactoring Steps

### Phase 1: Core Identity Refactoring

#### Step 1.1: Finalize DigitalTwinSubject Entity
```python
# Enhance the digital_twin_subject.py to be the canonical identity model

@dataclass
class DigitalTwinSubject:
    """
    Consolidated subject identity representation that completely replaces patient dependencies.
    Core domain entity for all Digital Twin functionality.
    """
    subject_id: UUID
    identity_type: str  # "research", "clinical", "anonymous"
    demographic_factors: Dict[str, Any]  # Age, sex, etc. without direct PHI
    clinical_factors: Dict[str, Any]  # Diagnostic codes, medication classes, etc.
    creation_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    external_references: Dict[str, str] = field(default_factory=dict)  # For transitional code only
    
    # Utility methods for demographic/clinical factor access
    @property
    def age(self) -> Optional[int]:
        return self.demographic_factors.get("age")
        
    @property
    def sex(self) -> Optional[str]:
        return self.demographic_factors.get("sex")
    
    # Methods for secure serialization
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        # Implementation here
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DigitalTwinSubject":
        """Create from dictionary representation."""
        # Implementation here
```

#### Step 1.2: Update DigitalTwin Entity
```python
# Update digital_twin.py to use DigitalTwinSubject consistently

@dataclass
class DigitalTwin:
    """
    Comprehensive psychiatric digital twin model.
    Core domain entity that contains the complete mental health model.
    """
    subject_id: UUID  # Reference to DigitalTwinSubject, not patient_id
    timestamp: datetime
    brain_regions: Dict[BrainRegion, BrainRegionState] = field(default_factory=dict)
    neurotransmitters: Dict[Neurotransmitter, NeurotransmitterState] = field(default_factory=dict)
    neural_connections: List[NeuralConnection] = field(default_factory=list)
    clinical_insights: List[ClinicalInsight] = field(default_factory=list)
    temporal_patterns: List[TemporalPattern] = field(default_factory=list)
    update_source: Optional[str] = None
    version: int = 1
    
    # No patient-specific properties or methods
```

#### Step 1.3: Update Repository Interfaces
```python
# Update repository interfaces to use DigitalTwinSubject consistently

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
    async def delete(self, subject_id: UUID) -> bool:
        """Delete a subject."""
        pass
```

### Phase 2: Application Service Refactoring

#### Step 2.1: Update DigitalTwinService
```python
# Update digital_twin_service.py to use DigitalTwinSubject consistently

class DigitalTwinService:
    """
    Application service for Digital Twin operations.
    Coordinates domain logic for digital twin creation and analysis.
    """
    
    def __init__(
        self,
        subject_repository: DigitalTwinSubjectRepository,
        twin_repository: DigitalTwinRepository,
        audit_service: Optional[AuditService] = None
    ):
        """Initialize with required dependencies."""
        self.subject_repository = subject_repository
        self.twin_repository = twin_repository
        self.audit_service = audit_service
    
    async def create_digital_twin(
        self,
        subject_id: UUID,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Create a new digital twin for a subject.
        
        Args:
            subject_id: UUID of the subject identity
            initial_state: Optional initial state data
            
        Returns:
            UUID of the created digital twin
            
        Raises:
            ResourceNotFoundError: If subject doesn't exist
        """
        # Implementation here
```

#### Step 2.2: Update TemporalNeurotransmitterService
```python
# Build on the existing clean implementation in temporal_neurotransmitter_service.py

class TemporalNeurotransmitterService:
    """
    Application service for temporal neurotransmitter analysis.
    Coordinates domain logic for neurotransmitter simulation and analysis.
    """
    
    def __init__(
        self,
        sequence_repository: TemporalSequenceRepository,
        subject_repository: DigitalTwinSubjectRepository,
        event_repository: Optional[EventRepository] = None,
        # Other dependencies...
    ):
        """Initialize with required dependencies."""
        # Implementation here
    
    async def generate_neurotransmitter_time_series(
        self,
        subject_id: UUID,  # Consistently use subject_id throughout
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        time_range_days: int = 30,
        time_step_hours: int = 6
    ) -> UUID:
        """Generate a temporal sequence for a neurotransmitter."""
        # Implementation here
```

### Phase 3: Infrastructure Implementation

#### Step 3.1: Create Subject Repository Implementation
```python
# postgresql_digital_twin_subject_repository.py

class PostgreSQLDigitalTwinSubjectRepository(DigitalTwinSubjectRepository):
    """PostgreSQL implementation of the DigitalTwinSubject repository."""
    
    def __init__(self, session_factory: Callable[..., AsyncSession]):
        """Initialize with session factory."""
        self.session_factory = session_factory
    
    async def save(self, subject: DigitalTwinSubject) -> UUID:
        """Save a subject identity to PostgreSQL."""
        async with self.session_factory() as session:
            # Implementation here
    
    async def get_by_id(self, subject_id: UUID) -> Optional[DigitalTwinSubject]:
        """Retrieve a subject by ID from PostgreSQL."""
        async with self.session_factory() as session:
            # Implementation here
    
    # Other method implementations...
```

#### Step 3.2: Update API Routes
```python
# digital_twin_subject_router.py

router = APIRouter(prefix="/api/v1/digital-twin-subjects", tags=["Digital Twin Subjects"])

@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    subject_service: DigitalTwinSubjectService = Depends(get_subject_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new digital twin subject."""
    # Implementation here

@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: UUID,
    subject_service: DigitalTwinSubjectService = Depends(get_subject_service),
    current_user: User = Depends(get_current_user)
):
    """Get a digital twin subject by ID."""
    # Implementation here
```

### Phase 4: Testing and Validation

#### Step 4.1: Unit Tests for Core Entities
```python
# test_digital_twin_subject.py

def test_digital_twin_subject_creation():
    """Test DigitalTwinSubject entity creation and properties."""
    subject = DigitalTwinSubject(
        subject_id=uuid4(),
        identity_type="research",
        demographic_factors={"age": 35, "sex": "female"},
        clinical_factors={"diagnosis_codes": ["F32.1"]}
    )
    
    assert subject.age == 35
    assert subject.sex == "female"
    assert "F32.1" in subject.clinical_factors["diagnosis_codes"]

def test_digital_twin_subject_serialization():
    """Test DigitalTwinSubject serialization and deserialization."""
    subject = DigitalTwinSubject(
        subject_id=uuid4(),
        identity_type="research",
        demographic_factors={"age": 35, "sex": "female"},
        clinical_factors={"diagnosis_codes": ["F32.1"]}
    )
    
    data = subject.to_dict()
    reconstructed = DigitalTwinSubject.from_dict(data)
    
    assert subject.subject_id == reconstructed.subject_id
    assert subject.age == reconstructed.age
    assert subject.clinical_factors == reconstructed.clinical_factors
```

#### Step 4.2: Integration Tests for Repositories
```python
# test_digital_twin_subject_repository.py

@pytest.mark.asyncio
async def test_save_and_retrieve_subject(subject_repository):
    """Test saving and retrieving a subject from the repository."""
    subject = DigitalTwinSubject(
        subject_id=uuid4(),
        identity_type="research",
        demographic_factors={"age": 35, "sex": "female"},
        clinical_factors={"diagnosis_codes": ["F32.1"]}
    )
    
    # Save to repository
    subject_id = await subject_repository.save(subject)
    
    # Retrieve from repository
    retrieved = await subject_repository.get_by_id(subject_id)
    
    assert retrieved is not None
    assert retrieved.subject_id == subject.subject_id
    assert retrieved.demographic_factors == subject.demographic_factors
```

## Migration Strategy

To migrate from the current state to the target architecture, follow these steps:

1. **Create parallel implementations** using the new DigitalTwinSubject abstraction
2. **Implement conversion utilities** to map between legacy Patient and new DigitalTwinSubject models
3. **Gradually update API endpoints** to use the new abstractions
4. **Deprecate and eventually remove** all patient-centric code
5. **Maintain database compatibility** during the transition period

## Production Readiness Checklist

Before considering the refactored platform production-ready, ensure all items on this checklist are complete:

- [ ] All patient/EHR dependencies removed from codebase
- [ ] DigitalTwinSubject abstraction consistently used throughout
- [ ] Test coverage exceeds 90% for all core components
- [ ] HIPAA compliance validation completed
- [ ] Performance benchmarks meet or exceed requirements
- [ ] Documentation updated to reflect new architecture
- [ ] Deployment pipeline fully automated
- [ ] Monitoring and alerting in place for all critical components
- [ ] User authentication and authorization implemented
- [ ] Backup and disaster recovery procedures established

## Conclusion

This target architecture represents a clean, future-focused design for the Novamind Digital Twin Platform. By adhering to clean architecture principles and eliminating legacy dependencies, the platform will achieve greater maintainability, scalability, and extensibility while maintaining its innovative psychiatric digital twin capabilities.

The next document will provide a detailed implementation plan and timeline for realizing this target architecture.