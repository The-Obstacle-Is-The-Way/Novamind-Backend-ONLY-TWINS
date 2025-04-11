# Storage and Data Model Architecture

This document provides a comprehensive overview of the storage architecture and data models used in the Novamind Digital Twin Platform. It consolidates information from multiple source documents to create a unified reference.

## Table of Contents

1. [Overview](#overview)
2. [Persistence Architecture](#persistence-architecture)
   - [Database Selection](#database-selection)
   - [Storage Layers](#storage-layers)
   - [Persistence Patterns](#persistence-patterns)
3. [Data Access Patterns](#data-access-patterns)
   - [Repository Pattern](#repository-pattern)
   - [Unit of Work](#unit-of-work)
   - [Query Objects](#query-objects)
4. [Domain Models](#domain-models)
   - [Core Domain Models](#core-domain-models)
   - [Digital Twin Models](#digital-twin-models)
   - [Clinical Models](#clinical-models)
5. [Data Lifecycle Management](#data-lifecycle-management)
   - [Data Creation](#data-creation)
   - [Data Retention](#data-retention)
   - [Data Archiving](#data-archiving)
   - [Data Deletion](#data-deletion)
6. [Security and Compliance](#security-and-compliance)
   - [Data Encryption](#data-encryption)
   - [Access Controls](#access-controls)
   - [Audit Logging](#audit-logging)
7. [Scalability and Performance](#scalability-and-performance)
   - [Scaling Strategies](#scaling-strategies)
   - [Performance Optimizations](#performance-optimizations)
   - [Monitoring](#monitoring)
8. [Implementation Details](#implementation-details)
   - [Technology Stack](#technology-stack)
   - [Schema Management](#schema-management)
   - [Migration Strategy](#migration-strategy)

## Overview

The Novamind Digital Twin Platform employs a sophisticated persistence architecture designed to support the complex, temporal nature of psychiatric digital twins. The storage architecture addresses several key requirements:

1. **Temporal Data Management**: Tracking state changes over time
2. **Multi-Modal Data Integration**: Storing diverse data types from various sources
3. **HIPAA Compliance**: Ensuring security and privacy of sensitive health information
4. **Scalability**: Supporting growth in data volume and user base
5. **Performance**: Enabling real-time analytics and interactions

The architecture follows domain-driven design principles, with a clear separation between domain models and their persistence representations. This approach ensures that business logic remains independent of storage concerns while enabling efficient data access patterns.

## Persistence Architecture

### Database Selection

The platform employs multiple database technologies, each optimized for specific data types and access patterns:

1. **Primary Relational Database (PostgreSQL)**
   - Core patient records
   - User and authentication data
   - Clinical relationship management
   - Treatment records
   - Structured clinical data

2. **Temporal Graph Database (Neo4j)**
   - Digital Twin state representation
   - State transitions and evolution
   - Relationship modeling
   - Causal inference

3. **Time Series Database (TimescaleDB)**
   - Biometric measurements
   - Activity monitoring data
   - Continuous monitoring signals
   - Temporal patterns

4. **Document Database (MongoDB)**
   - Clinical notes and unstructured documents
   - Assessment results
   - Rich text content
   - Flexible schema data

5. **Search Engine (Elasticsearch)**
   - Full-text search
   - Clinical content indexing
   - Semantic search capabilities
   - Aggregate analytics

### Storage Layers

The storage architecture is organized into logical layers:

```
┌───────────────────────────────────────────────┐
│              Application Layer                │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│              Repository Layer                 │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│              Persistence Layer                │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│              Storage Engines                  │
└───────────────────────────────────────────────┘
```

1. **Application Layer**
   - Domain models and business logic
   - Use cases and application services
   - No direct persistence dependencies

2. **Repository Layer**
   - Abstract repositories implementing domain interfaces
   - Query objects and specifications
   - Domain-to-persistence mapping

3. **Persistence Layer**
   - Concrete repository implementations
   - ORM configurations
   - Transaction management
   - Database connection handling

4. **Storage Engines**
   - Physical database instances
   - Cloud storage services
   - Data encryption at rest
   - Backup and redundancy

### Persistence Patterns

The platform implements the following persistence patterns:

1. **Event Sourcing**
   - Used for the Digital Twin core
   - All state changes captured as events
   - Current state reconstructed from event history
   - Enables temporal replay and analysis

2. **CQRS (Command Query Responsibility Segregation)**
   - Separate write and read models
   - Optimized query projections
   - Event-driven synchronization
   - Enhanced scalability and performance

3. **Temporal Tables**
   - Versioned records with validity periods
   - Point-in-time querying capabilities
   - Historical state reconstruction
   - Non-destructive updates

4. **Sharding**
   - Patient-based data partitioning
   - Geographical partitioning for multi-region deployments
   - Tenant isolation for multi-tenant deployments
   - Scalable data distribution

## Data Access Patterns

### Repository Pattern

The platform uses the Repository pattern to abstract data access:

```python
# Domain repository interface
class PatientRepository(Protocol):
    def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        ...
    
    def save(self, patient: Patient) -> None:
        ...
    
    def find_by_criteria(self, criteria: PatientSearchCriteria) -> List[Patient]:
        ...

# Concrete implementation using PostgreSQL
class PostgreSQLPatientRepository(PatientRepository):
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory
    
    def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        with self.session_factory() as session:
            patient_record = session.query(PatientRecord).filter(
                PatientRecord.id == patient_id
            ).first()
            
            return patient_record.to_domain() if patient_record else None
```

Key aspects of the Repository implementation:

1. **Domain-Centric Interface**
   - Repositories operate on domain objects
   - Storage details are abstracted away
   - Methods reflect domain operations

2. **Persistence Mapping**
   - Conversion between domain and persistence models
   - Handling of complex object graphs
   - Lazy loading strategies

3. **Query Encapsulation**
   - Domain-specific query methods
   - Protection from storage implementation details
   - Optimization for common access patterns

### Unit of Work

The Unit of Work pattern manages transaction boundaries:

```python
class UnitOfWork:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory
        self.session = None
    
    def __enter__(self):
        self.session = self.session_factory()
        self.patients = PostgreSQLPatientRepository(self.session)
        self.treatments = PostgreSQLTreatmentRepository(self.session)
        self.digital_twins = Neo4jDigitalTwinRepository(self.session)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        
        self.session.close()
    
    def commit(self):
        self.session.commit()
    
    def rollback(self):
        self.session.rollback()
```

Benefits of the Unit of Work pattern:

1. **Transaction Integrity**
   - Atomic operations across multiple repositories
   - Consistent transaction boundaries
   - Automatic rollback on exceptions

2. **Repository Coordination**
   - Coordinated access to multiple repositories
   - Shared transaction context
   - Consistent view of data

3. **Resource Management**
   - Controlled session lifecycle
   - Connection pooling optimization
   - Automatic cleanup of resources

### Query Objects

Complex queries are encapsulated in Query objects:

```python
class PatientSearchQuery:
    def __init__(
        self,
        diagnosis: Optional[str] = None,
        age_range: Optional[Tuple[int, int]] = None,
        medication: Optional[str] = None,
        treatment_status: Optional[TreatmentStatus] = None
    ):
        self.diagnosis = diagnosis
        self.age_range = age_range
        self.medication = medication
        self.treatment_status = treatment_status
    
    def execute(self, session: Session) -> List[PatientRecord]:
        query = session.query(PatientRecord)
        
        if self.diagnosis:
            query = query.join(DiagnosisRecord).filter(
                DiagnosisRecord.code == self.diagnosis
            )
        
        if self.age_range:
            min_age, max_age = self.age_range
            query = query.filter(
                func.date_part('year', func.age(PatientRecord.birth_date)) 
                    .between(min_age, max_age)
            )
        
        # Additional filters...
        
        return query.all()
```

Advantages of Query objects:

1. **Query Reusability**
   - Encapsulated query logic
   - Parameterized execution
   - Composition of filtering criteria

2. **Optimized Data Access**
   - Database-specific optimizations
   - Efficient join strategies
   - Pagination and result limiting

3. **Separation of Concerns**
   - Query logic isolated from repositories
   - Specialized query objects for complex scenarios
   - Clear responsibility boundaries

## Domain Models

### Core Domain Models

The core domain models represent the fundamental entities in the psychiatric domain:

#### Patient

The Patient model represents individuals receiving psychiatric care:

```python
@dataclass
class Patient:
    id: UUID
    medical_record_number: str
    first_name: str
    last_name: str
    birth_date: date
    sex: BiologicalSex
    gender: Gender
    contact_information: ContactInformation
    diagnoses: List[Diagnosis]
    medications: List[Medication]
    treatments: List[Treatment]
    clinical_relationships: List[ClinicalRelationship]
```

Key aspects of the Patient model:
- Unique identification through UUID and medical record number
- Demographic information
- Clinical history through related entities
- Clinical relationships for access control

#### Clinician

The Clinician model represents mental health professionals:

```python
@dataclass
class Clinician:
    id: UUID
    license_number: str
    first_name: str
    last_name: str
    specializations: List[Specialization]
    credentials: List[Credential]
    contact_information: ContactInformation
    patients: List[ClinicalRelationship]
    organization: Organization
```

Key aspects of the Clinician model:
- Professional identification and credentials
- Specialization information
- Patient relationships for access control
- Organizational affiliation

#### Treatment

The Treatment model represents therapeutic interventions:

```python
@dataclass
class Treatment:
    id: UUID
    type: TreatmentType
    name: str
    status: TreatmentStatus
    start_date: date
    end_date: Optional[date]
    prescriber: Clinician
    patient: Patient
    dosage: Optional[str]
    frequency: Optional[str]
    notes: List[TreatmentNote]
    responses: List[TreatmentResponse]
```

Key aspects of the Treatment model:
- Categorization by treatment type
- Temporal attributes (start/end dates)
- Association with prescriber and patient
- Documentation of responses and outcomes

### Digital Twin Models

The Digital Twin models represent the computational psychiatric state:

#### DigitalTwin

The core Digital Twin model:

```python
@dataclass
class DigitalTwin:
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    state_history: List[DigitalTwinState]
    current_state: DigitalTwinState
    predictions: List[DigitalTwinPrediction]
```

Key aspects of the Digital Twin model:
- Link to patient identity
- Temporal tracking of state changes
- Current state representation
- Predictive forecasts

#### DigitalTwinState

The state representation at a point in time:

```python
@dataclass
class DigitalTwinState:
    id: UUID
    digital_twin_id: UUID
    timestamp: datetime
    symptom_state: SymptomState
    neurotransmitter_state: NeurotransmitterState
    behavioral_state: BehavioralState
    functional_state: FunctionalState
    risk_state: RiskState
    confidence: float
    source_events: List[SourceEvent]
```

Key aspects of the Digital Twin State model:
- Temporal anchoring with timestamp
- Multi-dimensional state representation
- Confidence assessment
- Provenance tracking through source events

#### NeurotransmitterState

The neurotransmitter simulation state:

```python
@dataclass
class NeurotransmitterState:
    id: UUID
    serotonin_level: float
    dopamine_level: float
    norepinephrine_level: float
    gaba_level: float
    glutamate_level: float
    acetylcholine_level: float
    medication_effects: List[MedicationEffect]
    confidence: float
```

Key aspects of the Neurotransmitter State model:
- Quantitative neurotransmitter levels
- Medication influence tracking
- Confidence assessment for simulation quality

### Clinical Models

The clinical models represent psychiatric assessment and observation:

#### Diagnosis

The Diagnosis model represents clinical conditions:

```python
@dataclass
class Diagnosis:
    id: UUID
    code: str
    name: str
    classification_system: ClassificationSystem
    severity: Optional[Severity]
    onset_date: Optional[date]
    resolution_date: Optional[date]
    diagnosing_clinician: Clinician
    notes: str
    supporting_observations: List[ClinicalObservation]
```

Key aspects of the Diagnosis model:
- Standard coding through classification systems
- Temporal attributes (onset/resolution)
- Severity assessment
- Supporting clinical evidence

#### ClinicalObservation

The Clinical Observation model captures specific clinical findings:

```python
@dataclass
class ClinicalObservation:
    id: UUID
    patient_id: UUID
    clinician_id: UUID
    timestamp: datetime
    observation_type: ObservationType
    value: Any
    unit: Optional[str]
    notes: str
    source: ObservationSource
    reliability: float
```

Key aspects of the Clinical Observation model:
- Temporal anchoring with timestamp
- Typed observation categorization
- Quantitative or qualitative values
- Source tracking for provenance
- Reliability assessment

#### Assessment

The Assessment model represents structured clinical evaluations:

```python
@dataclass
class Assessment:
    id: UUID
    patient_id: UUID
    clinician_id: UUID
    assessment_type: AssessmentType
    timestamp: datetime
    completed: bool
    total_score: Optional[float]
    subscale_scores: Dict[str, float]
    responses: Dict[str, Any]
    interpretation: Optional[str]
    recommendations: List[str]
```

Key aspects of the Assessment model:
- Structured assessment typing
- Temporal anchoring
- Quantitative scoring
- Detailed response capturing
- Clinical interpretation and recommendations

## Data Lifecycle Management

### Data Creation

Data creation follows these patterns:

1. **Transactional Creation**
   - Domain objects created in application layer
   - Passed to repositories for persistence
   - Transaction boundaries defined by Unit of Work
   - Validation before persistence

2. **Event-Driven Creation**
   - Events trigger creation of derived data
   - Asynchronous processing through event handlers
   - Eventual consistency guarantees
   - Idempotent creation operations

3. **Bulk Creation**
   - Optimized pathways for batch operations
   - Data transformation pipelines
   - Validation in streaming fashion
   - Transaction management for large datasets

### Data Retention

Data retention policies include:

1. **Clinical Data**
   - Retained according to regulatory requirements (7+ years)
   - Full history maintained for active patients
   - Compliance with medical record retention laws
   - Preservation of treatment decision context

2. **Digital Twin States**
   - Full history maintained for active patients
   - Temporal decimation for older states
   - Statistical summarization of historical data
   - Retention based on clinical relevance

3. **Raw Measurements**
   - High-fidelity retention for recent data
   - Progressive downsampling of older data
   - Statistical aggregation for long-term storage
   - Retention based on analytical requirements

### Data Archiving

Archiving strategies include:

1. **Tiered Storage**
   - Hot storage for active data
   - Warm storage for recent inactive data
   - Cold storage for archived data
   - Glacier storage for compliance-only data

2. **Archival Process**
   - Scheduled archival based on data access patterns
   - Metadata preservation for searchability
   - Integrity verification before archival
   - Secure, encrypted archival storage

3. **Retrieval Capabilities**
   - On-demand restoration from archive
   - Searchable archive metadata
   - Partial restoration capabilities
   - Prioritized restoration for clinical needs

### Data Deletion

Deletion processes include:

1. **Soft Deletion**
   - Logical deletion with retention of data
   - Accessibility restrictions on deleted data
   - Automated purging based on retention policies
   - Audit trails of deletion operations

2. **Physical Deletion**
   - Secure erasure of PHI on request
   - Compliance with "right to be forgotten" regulations
   - Cryptographic deletion through key destruction
   - Certificate of destruction for compliance

3. **Selective Deletion**
   - Fine-grained deletion of specific PHI elements
   - Preservation of non-identifiable research data
   - De-identification rather than complete erasure
   - Configurable deletion rules by data category

## Security and Compliance

### Data Encryption

Encryption strategies include:

1. **Encryption at Rest**
   - AES-256 encryption for all stored data
   - Transparent data encryption at database level
   - File-level encryption for document storage
   - Key rotation policies

2. **Application-Level Encryption**
   - Field-level encryption for sensitive attributes
   - Different encryption keys by data category
   - Key management through secure key vault
   - Encryption key access controls

3. **Encryption Key Management**
   - HSM-backed key management
   - Key rotation schedules
   - Key access auditing
   - Backup key recovery procedures

### Access Controls

Data access controls include:

1. **Row-Level Security**
   - Patient-level access restrictions
   - Clinical relationship-based filtering
   - Organizational boundaries enforcement
   - Time-bound access limitations

2. **Column-Level Security**
   - Attribute-based access control
   - Dynamic masking of sensitive fields
   - Role-based column visibility
   - Purpose-based data access

3. **Query Controls**
   - Query authorization checks
   - Result set filtering
   - Rate limiting and complexity controls
   - Query auditing and monitoring

### Audit Logging

Audit mechanisms include:

1. **Data Access Logging**
   - All read operations on PHI
   - Purpose of access documentation
   - User and system identification
   - Timestamp and access context

2. **Data Modification Logging**
   - Before and after states
   - Modification reason documentation
   - Authorization information
   - Modification metadata

3. **Audit Storage**
   - Immutable audit logs
   - Cryptographic verification
   - Tamper-evident storage
   - Retention according to compliance requirements

## Scalability and Performance

### Scaling Strategies

The platform scales through:

1. **Horizontal Scaling**
   - Stateless application services
   - Database read replicas
   - Sharding by patient or organization
   - Load balancing across instances

2. **Vertical Scaling**
   - Resource allocation based on workload
   - Memory optimization for high-throughput processing
   - CPU scaling for computational workloads
   - Storage throughput optimization

3. **Microservice Decomposition**
   - Service boundaries aligned with data boundaries
   - Independent scaling of services
   - Data synchronization through events
   - Service-specific persistence optimization

### Performance Optimizations

Performance is optimized through:

1. **Query Optimization**
   - Tailored indexes for common queries
   - Denormalization for read performance
   - Query result caching
   - Execution plan monitoring

2. **Caching Strategies**
   - Multi-level caching architecture
   - Entity caching for frequent access
   - Query result caching
   - Distributed cache for scalability

3. **Asynchronous Processing**
   - Background processing for non-critical operations
   - Task queuing for workload management
   - Event-driven architecture for decoupling
   - Prioritization of critical path operations

### Monitoring

The platform is monitored through:

1. **Performance Metrics**
   - Query execution times
   - Storage I/O metrics
   - Cache hit/miss rates
   - Transaction throughput

2. **Resource Utilization**
   - CPU, memory, and storage utilization
   - Database connection pools
   - Network bandwidth consumption
   - Query resource consumption

3. **Alerting**
   - Performance degradation alerts
   - Resource exhaustion warnings
   - Error rate monitoring
   - SLA compliance tracking

## Implementation Details

### Technology Stack

The storage layer leverages the following technologies:

1. **Primary Database**
   - PostgreSQL 14+ with TimescaleDB extension
   - Configured with high availability
   - Point-in-time recovery capabilities
   - Optimized for mixed workloads

2. **Object-Relational Mapping**
   - SQLAlchemy Core and ORM
   - Pydantic for data validation
   - Custom type mappings for domain concepts
   - Performance-optimized query generation

3. **Graph Database**
   - Neo4j 4.4+ Enterprise Edition
   - Causal cluster configuration
   - APOC library for advanced operations
   - Graph Data Science library for analytics

4. **Document Database**
   - MongoDB 5.0+ with Atlas
   - Document versioning
   - Full-text search capabilities
   - Time series collections

### Schema Management

Schema is managed through:

1. **Migration Framework**
   - Alembic for relational database migrations
   - Version-controlled schema evolution
   - Automatic migration generation
   - Rollback capabilities

2. **Schema Validation**
   - JSON Schema for document validation
   - Database constraints for data integrity
   - Programmatic validation in repositories
   - Migration testing framework

3. **Schema Documentation**
   - Automated schema documentation
   - Relationship diagrams
   - Data dictionary generation
   - Schema version tracking

### Migration Strategy

Data migration is handled through:

1. **Zero-Downtime Migrations**
   - Backward compatible schema changes
   - Multi-phase migration approach
   - Feature toggles for transitional periods
   - Data replication during transitions

2. **ETL Processes**
   - Extract-transform-load pipelines
   - Data quality validation during migration
   - Performance-optimized bulk operations
   - Reconciliation reporting

3. **Legacy System Integration**
   - Adapters for legacy data sources
   - Transformation layers for data normalization
   - Identity mapping and resolution
   - Incremental migration capabilities

## Conclusion

The storage and data model architecture of the Novamind Digital Twin Platform is designed to support the unique requirements of psychiatric digital twins. By implementing domain-driven design principles, advanced persistence patterns, and comprehensive security controls, the architecture enables the sophisticated temporal modeling required for psychiatric state tracking while ensuring HIPAA compliance and scalability.

This architecture provides a solid foundation for the platform's ambitious goals, supporting the integration of diverse data sources, complex analytical processing, and personalized treatment optimization while maintaining the highest standards of data protection and privacy.