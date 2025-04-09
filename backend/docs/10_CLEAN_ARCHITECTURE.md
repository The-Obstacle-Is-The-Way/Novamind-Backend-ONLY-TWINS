# Clean Architecture Overview

This document provides an overview of the Novamind Digital Twin Platform's clean architecture implementation. It serves as the foundational architectural reference that guides all development and establishes the principles, patterns, and practices that ensure maintainability, testability, and scalability.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
   - [Domain Layer](#domain-layer)
   - [Application Layer](#application-layer)
   - [Infrastructure Layer](#infrastructure-layer)
   - [API Layer](#api-layer)
   - [Core Layer](#core-layer)
3. [Dependency Rule](#dependency-rule)
4. [Component Interaction](#component-interaction)
5. [Design Patterns](#design-patterns)
6. [Folder Structure](#folder-structure)
7. [Implementation Guidelines](#implementation-guidelines)

## Overview

The Novamind Digital Twin Platform adopts Robert C. Martin's Clean Architecture principles to create a system that is:

1. **Framework-independent**: The core business logic does not depend on any external frameworks
2. **Testable**: Business rules can be tested without external elements like UI, database, or web server
3. **UI-independent**: The UI can change without affecting the rest of the system
4. **Database-independent**: Business rules are not bound to a specific database implementation
5. **External agency-independent**: Business rules don't know anything about the outside world

These principles enable the platform to remain adaptable to changing requirements, technologies, and integration needs while maintaining a stable core that embodies the essential domain logic of a psychiatric digital twin.

## Architecture Layers

The platform is organized into concentric layers, with dependencies pointing inward. Each layer has a specific responsibility and well-defined boundaries.

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌───────────────────────────────────────────────────────┐   │
│  │                                                       │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │                                                │   │   │
│  │  │  ┌─────────────────────────────────────────┐   │   │   │
│  │  │  │                                         │   │   │   │
│  │  │  │  ┌─────────────────────────────────┐    │   │   │   │
│  │  │  │  │                                 │    │   │   │   │
│  │  │  │  │          Domain Layer           │    │   │   │   │
│  │  │  │  │                                 │    │   │   │   │
│  │  │  │  └─────────────────────────────────┘    │   │   │   │
│  │  │  │           Application Layer             │   │   │   │
│  │  │  │                                         │   │   │   │
│  │  │  └─────────────────────────────────────────┘   │   │   │
│  │  │              Infrastructure Layer              │   │   │
│  │  │                                                │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  │                    API Layer                          │   │
│  │                                                       │   │
│  └───────────────────────────────────────────────────────┘   │
│                       Core Layer                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Domain Layer

The domain layer represents the heart of the system and contains the core business logic and entities.

**Key Components**:

1. **Entities**: Business objects that encapsulate the most general and high-level rules
   - Patient
   - Clinician
   - Treatment
   - Assessment
   - DigitalTwin (central entity)
   - Neurotransmitter
   - MentalState

2. **Value Objects**: Immutable objects that represent descriptive aspects of the domain
   - MedicalIdentifier
   - ContactInformation
   - TreatmentDosage
   - AssessmentScore

3. **Domain Services**: Stateless operations that don't naturally fit within an entity
   - DigitalTwinAnalysisService
   - NeurotransmitterModelingService
   - TreatmentEfficacyService

4. **Domain Events**: Representations of something that happened in the domain
   - TreatmentAdministered
   - AssessmentCompleted
   - DigitalTwinUpdated

5. **Aggregates**: Clusters of domain objects treated as a single unit
   - PatientAggregate (root: Patient)
   - TreatmentPlanAggregate (root: TreatmentPlan)
   - DigitalTwinAggregate (root: DigitalTwin)

6. **Repository Interfaces**: Abstractions for data access
   - PatientRepository
   - TreatmentRepository
   - DigitalTwinRepository

**Implementation Principles**:

- All domain entities use primitive types, other entities, or value objects
- No dependencies on frameworks, databases, or external services
- Business rules and logic are self-contained
- Rich domain model with behavior, not an anemic data model

```python
# Example of a domain entity
from datetime import date
from typing import List, Optional
from uuid import UUID

from app.domain.value_objects import ContactInformation, MedicalIdentifier
from app.domain.models.enums import Gender
from app.domain.models.assessment import Assessment
from app.domain.models.treatment import Treatment
from app.domain.models.digital_twin import DigitalTwin

class Patient:
    def __init__(
        self,
        id: UUID,
        first_name: str,
        last_name: str,
        birth_date: date,
        gender: Gender,
        medical_identifier: Optional[MedicalIdentifier] = None,
        contact_information: Optional[ContactInformation] = None,
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.gender = gender
        self.medical_identifier = medical_identifier
        self.contact_information = contact_information
        self.treatments: List[Treatment] = []
        self.assessments: List[Assessment] = []
        self.digital_twin: Optional[DigitalTwin] = None
        
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def age(self, reference_date: Optional[date] = None) -> int:
        ref_date = reference_date or date.today()
        age = ref_date.year - self.birth_date.year
        if (ref_date.month, ref_date.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age

    def add_treatment(self, treatment: Treatment) -> None:
        if treatment not in self.treatments:
            self.treatments.append(treatment)
            
    def add_assessment(self, assessment: Assessment) -> None:
        if assessment not in self.assessments:
            self.assessments.append(assessment)
            
    def create_digital_twin(self) -> DigitalTwin:
        if self.digital_twin is None:
            self.digital_twin = DigitalTwin(patient_id=self.id)
        return self.digital_twin
```

### Application Layer

The application layer orchestrates the flow of data to and from domain entities and directs them to perform their business logic.

**Key Components**:

1. **Use Cases/Services**: Implementations of application-specific business rules
   - PatientService
   - TreatmentService
   - AssessmentService
   - DigitalTwinService

2. **DTOs (Data Transfer Objects)**: Simple objects for data passing between layers
   - PatientDTO
   - TreatmentDTO
   - AssessmentDTO
   - DigitalTwinDTO

3. **Application Interfaces**: Abstractions of infrastructure services needed by the application
   - AuthenticationService
   - NotificationService
   - AuditService

4. **Command/Query Handlers**: Implementation of the Command Query Responsibility Segregation (CQRS) pattern
   - RegisterPatientCommand
   - AddTreatmentCommand
   - GetPatientByIdQuery
   - GetDigitalTwinReportQuery

**Implementation Principles**:

- Thin layer coordinating the domain objects
- Implements use case-specific workflows
- Translates between domain entities and external representations
- No domain business rules in this layer
- Depends on domain layer and application interfaces

```python
# Example of an application service
from typing import List, Optional
from uuid import UUID

from app.domain.models.patient import Patient
from app.domain.repositories.patient_repository import PatientRepository
from app.application.interfaces.authentication_service import AuthenticationService
from app.application.interfaces.audit_service import AuditService
from app.application.dtos.patient_dto import PatientDTO, PatientDetailsDTO
from app.application.exceptions import NotAuthorizedException, NotFoundException

class PatientService:
    def __init__(
        self, 
        patient_repository: PatientRepository,
        authentication_service: AuthenticationService,
        audit_service: AuditService
    ):
        self.patient_repository = patient_repository
        self.authentication_service = authentication_service
        self.audit_service = audit_service
        
    def get_patient_by_id(self, patient_id: UUID, user_id: UUID) -> PatientDetailsDTO:
        # Check authorization
        if not self.authentication_service.can_access_patient(user_id, patient_id):
            self.audit_service.log_unauthorized_access(
                user_id=user_id,
                resource_id=str(patient_id),
                resource_type="patient",
                action="read"
            )
            raise NotAuthorizedException("Not authorized to access this patient")
            
        # Log authorized access
        self.audit_service.log_phi_access(
            user_id=user_id,
            resource_id=str(patient_id),
            resource_type="patient",
            action="read"
        )
        
        # Retrieve patient
        patient = self.patient_repository.get_by_id(patient_id)
        if not patient:
            raise NotFoundException(f"Patient with ID {patient_id} not found")
            
        # Return DTO
        return PatientDetailsDTO.from_entity(patient)
        
    def get_patients(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        name_filter: Optional[str] = None
    ) -> List[PatientDTO]:
        # Check authorization
        if not self.authentication_service.can_list_patients(user_id):
            raise NotAuthorizedException("Not authorized to list patients")
            
        # Get patients with filtering
        patients = self.patient_repository.get_patients_for_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            name_filter=name_filter
        )
        
        # Convert to DTOs
        return [PatientDTO.from_entity(patient) for patient in patients]
```

### Infrastructure Layer

The infrastructure layer implements interfaces defined by the application layer and provides concrete implementations for data access, external services, and technical capabilities.

**Key Components**:

1. **Repository Implementations**: Concrete implementations of domain repository interfaces
   - SQLAlchemyPatientRepository
   - MongoDBAssessmentRepository
   - RedisDigitalTwinRepository

2. **External Service Adapters**: Implementations of application interfaces for external services
   - SMTPEmailService
   - TwilioSMSService
   - GoogleCalendarService

3. **ORM Entities**: Database-specific models for object-relational mapping
   - PatientORMEntity
   - TreatmentORMEntity
   - AssessmentORMEntity

4. **Data Access**: Database connection and transaction management
   - DatabaseSession
   - TransactionManager
   - ConnectionPool

5. **Infrastructure Services**: Technical services not related to business logic
   - CacheService
   - StorageService
   - LoggingService
   - TokenService

**Implementation Principles**:

- Implements technical details and infrastructure concerns
- Adapts external libraries and frameworks to the application
- Isolates external dependencies from the domain and application
- Concrete implementations of interfaces defined in inner layers

```python
# Example of a repository implementation
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.models.patient import Patient
from app.domain.repositories.patient_repository import PatientRepository
from app.infrastructure.db.models.patient import PatientModel
from app.infrastructure.db.mappers.patient_mapper import PatientMapper

class SQLAlchemyPatientRepository(PatientRepository):
    def __init__(self, session: Session):
        self.session = session
        self.mapper = PatientMapper()
        
    def get_by_id(self, id: UUID) -> Optional[Patient]:
        patient_model = self.session.query(PatientModel).filter(PatientModel.id == id).first()
        if not patient_model:
            return None
        return self.mapper.to_entity(patient_model)
        
    def save(self, patient: Patient) -> Patient:
        patient_model = self.session.query(PatientModel).filter(
            PatientModel.id == patient.id
        ).first()
        
        if patient_model:
            # Update existing
            patient_model = self.mapper.update_model(patient_model, patient)
        else:
            # Create new
            patient_model = self.mapper.to_model(patient)
            self.session.add(patient_model)
            
        self.session.flush()
        return self.mapper.to_entity(patient_model)
        
    def get_patients_for_user(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        name_filter: Optional[str] = None
    ) -> List[Patient]:
        query = self.session.query(PatientModel)
        
        # Apply filters for user access
        # (This would involve joining with clinical_relationship or similar table)
        query = query.join(ClinicalRelationshipModel).filter(
            ClinicalRelationshipModel.clinician_id == user_id
        )
        
        # Apply name filter if provided
        if name_filter:
            query = query.filter(
                PatientModel.first_name.ilike(f"%{name_filter}%") | 
                PatientModel.last_name.ilike(f"%{name_filter}%")
            )
            
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Map to domain entities
        return [self.mapper.to_entity(model) for model in query.all()]
```

### API Layer

The API layer exposes the application's functionality to external clients through well-defined interfaces such as REST APIs, GraphQL, or RPC.

**Key Components**:

1. **API Controllers/Routers**: Handle HTTP requests and responses
   - PatientController
   - TreatmentController
   - AssessmentController
   - DigitalTwinController

2. **Request/Response Models**: Data models for API input and output
   - PatientRequest
   - PatientResponse
   - TreatmentRequest
   - AssessmentResponse

3. **API Middleware**: Cross-cutting concerns for API requests
   - AuthenticationMiddleware
   - LoggingMiddleware
   - ErrorHandlingMiddleware
   - RateLimitingMiddleware

4. **API Documentation**: Specifications for API endpoints
   - OpenAPI/Swagger definitions
   - API versioning
   - Endpoint documentation

**Implementation Principles**:

- Thin controllers that delegate to application services
- Request validation before processing
- Consistent error handling and response formats
- API versioning for backward compatibility
- Clear separation between API models and domain entities

```python
# Example of an API controller using FastAPI
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import get_current_user
from app.api.models.patient import (
    PatientCreate, 
    PatientResponse, 
    PatientListResponse, 
    PatientUpdate
)
from app.application.services.patient_service import PatientService
from app.application.exceptions import NotAuthorizedException, NotFoundException
from app.domain.models.user import User

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/", response_model=List[PatientListResponse])
async def get_patients(
    name: Optional[str] = Query(None, description="Filter by patient name"),
    skip: int = Query(0, ge=0, description="Skip the first N results"),
    limit: int = Query(100, ge=1, le=100, description="Limit the number of results"),
    current_user: User = Depends(get_current_user),
    patient_service: PatientService = Depends()
):
    """
    Get a list of patients that the current user has access to.
    """
    try:
        patients = patient_service.get_patients(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            name_filter=name
        )
        return patients
    except NotAuthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    patient_service: PatientService = Depends()
):
    """
    Get detailed information about a specific patient.
    """
    try:
        patient = patient_service.get_patient_by_id(
            patient_id=patient_id,
            user_id=current_user.id
        )
        return patient
    except NotAuthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

### Core Layer

The core layer contains cross-cutting concerns and shared utilities used across the entire application.

**Key Components**:

1. **Error Handling**: Global error types and handling mechanisms
   - ApplicationException
   - DomainException
   - ValidationException
   - AuthorizationException

2. **Logging**: Centralized logging infrastructure
   - LoggerFactory
   - LogFormatter
   - ContextualLogger

3. **Configuration**: Application configuration management
   - ConfigurationProvider
   - EnvironmentSettings
   - FeatureFlags

4. **Common Utilities**: Shared utility functions and helpers
   - DateTimeUtils
   - StringUtils
   - IdGenerator
   - ValidationUtils

5. **Security Utilities**: Security-related functionality
   - PasswordHasher
   - TokenGenerator
   - EncryptionService
   - PHISanitizer

**Implementation Principles**:

- Modular and reusable components
- No domain-specific logic
- Used across all other layers
- Technical implementation details separate from business concerns

```python
# Example of a core utility
from datetime import datetime, timezone
from typing import Optional
import re
import hashlib
import base64
import uuid

class SecurityUtils:
    @staticmethod
    def generate_secure_id() -> str:
        """Generate a cryptographically secure identifier."""
        return str(uuid.uuid4())
        
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash a password with a salt using PBKDF2."""
        if not salt:
            salt = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
            
        # Use PBKDF2 with 100,000 iterations
        key = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        )
        password_hash = base64.b64encode(key).decode('utf-8')
        
        return password_hash, salt
        
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify a password against a stored hash and salt."""
        calculated_hash, _ = SecurityUtils.hash_password(password, salt)
        return calculated_hash == stored_hash
        
    @staticmethod
    def sanitize_phi(text: str) -> str:
        """
        Remove potential PHI from text using pattern matching.
        This is a simple example and would need to be more comprehensive in practice.
        """
        # Remove potential SSNs
        text = re.sub(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', '[REDACTED SSN]', text)
        
        # Remove potential phone numbers
        text = re.sub(r'\b\(\d{3}\)\s?\d{3}[-\s]?\d{4}\b', '[REDACTED PHONE]', text)
        text = re.sub(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b', '[REDACTED PHONE]', text)
        
        # Remove potential emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     '[REDACTED EMAIL]', text)
        
        return text
```

## Dependency Rule

The fundamental rule of clean architecture is that dependencies can only point inward. Inner layers must not know about outer layers. This means:

1. **Domain layer** has no dependencies on any other layer
2. **Application layer** depends only on the domain layer
3. **Infrastructure layer** depends on domain and application layers
4. **API layer** depends on application and sometimes infrastructure layers
5. **Core layer** is used by all other layers but depends on none

This dependency rule is enforced through several mechanisms:

1. **Interfaces**: Inner layers define interfaces that outer layers implement
2. **Dependency Injection**: Dependencies are injected rather than directly imported
3. **DTOs**: Data Transfer Objects for crossing layer boundaries
4. **Mappers**: Convert between domain entities and infrastructure/API models

```
┌────────────────┐        ┌────────────────┐        ┌────────────────┐
│                │        │                │        │                │
│  Domain Layer  │◄───────│  Application   │◄───────│ Infrastructure │
│                │        │     Layer      │        │     Layer      │
└────────────────┘        └────────────────┘        └────────────────┘
                                  ▲                         ▲
                                  │                         │
                                  │                         │
                          ┌───────┴───────┐                 │
                          │               │                 │
                          │   API Layer   │─────────────────┘
                          │               │
                          └───────────────┘

                                  ▲
                                  │
                                  │
                          ┌───────┴───────┐
                          │               │
                          │  Core Layer   │
                          │               │
                          └───────────────┘
```

## Component Interaction

Components interact across layers through well-defined interfaces and boundaries:

### Request Flow Example

1. **API Layer**:
   - Receives HTTP request
   - Validates request format and data
   - Maps to application DTO or command
   - Calls appropriate application service

2. **Application Layer**:
   - Receives command/query from API layer
   - Performs application-level validation
   - Retrieves entities through repository interfaces
   - Executes business logic by coordinating domain entities
   - Returns results to API layer

3. **Domain Layer**:
   - Contains business logic executed by application services
   - Entities perform domain-specific operations
   - Domain services execute complex business rules
   - No knowledge of persistence or external systems

4. **Infrastructure Layer**:
   - Implements repository interfaces from domain layer
   - Maps between domain entities and database models
   - Handles database transactions and connections
   - Integrates with external services and APIs

### Example: Registering a New Patient

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ API Controller│    │ Patient       │    │ Patient       │    │ Patient       │
│               │    │ Service       │    │ Entity        │    │ Repository    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │                    │
        │  Create Patient    │                    │                    │
        │ ───────────────►   │                    │                    │
        │                    │                    │                    │
        │                    │ Create Domain Entity                    │
        │                    │ ───────────────►   │                    │
        │                    │                    │                    │
        │                    │                    │  Entity Created    │
        │                    │                    │ ◄───────────────   │
        │                    │                    │                    │
        │                    │ Save Patient       │                    │
        │                    │ ─────────────────────────────────────►  │
        │                    │                    │                    │
        │                    │                    │                    │ Store in DB
        │                    │                    │                    │ ──────────►
        │                    │                    │                    │
        │                    │                    │                    │ Entity Saved
        │                    │                    │                    │ ◄──────────
        │                    │ Patient Saved      │                    │
        │                    │ ◄─────────────────────────────────────  │
        │                    │                    │                    │
        │  Return Response   │                    │                    │
        │ ◄───────────────   │                    │                    │
        │                    │                    │                    │
```

## Design Patterns

The Novamind Digital Twin Platform utilizes several design patterns to implement clean architecture effectively:

1. **Repository Pattern**: Abstracts data access logic
   - Decouples domain from data storage
   - Allows swapping data sources
   - Enables testing with mock repositories

2. **Dependency Injection**: Manages dependencies between components
   - Inversion of control
   - Easier testing through dependency substitution
   - Decoupling of component creation and usage

3. **Factory Pattern**: Creates complex objects
   - Encapsulates object creation logic
   - Centralizes instantiation logic
   - Simplifies testing with object creation

4. **Mediator Pattern**: Manages component communication
   - Reduces direct dependencies between components
   - Centralizes communication logic
   - Implements command/query handling

5. **Specification Pattern**: Encapsulates business rules
   - Composable business rules
   - Reusable validation logic
   - Domain-focused rule expression

6. **Mapper Pattern**: Transforms objects between layers
   - Maintains layer isolation
   - Handles object transformation
   - Separates domain from persistence models

7. **Unit of Work Pattern**: Manages transactions
   - Coordinates multiple repository operations
   - Ensures all-or-nothing transactions
   - Simplifies transaction management

## Folder Structure

The Novamind Digital Twin Platform follows this folder structure to implement clean architecture:

```
/app
  /api                # API Layer
    /v1               # API version 1
      /controllers    # API controllers (routes)
      /models         # API request/response models
      /middleware     # API middleware components
    /dependencies     # Dependency injection for API
    
  /application        # Application Layer
    /services         # Application services (use cases)
    /dtos             # Data transfer objects
    /commands         # Command objects (CQRS)
    /queries          # Query objects (CQRS)
    /handlers         # Command and query handlers
    /interfaces       # Interfaces for infrastructure
    /exceptions       # Application-specific exceptions
    
  /domain             # Domain Layer
    /models           # Domain entities and value objects
      /patient        # Patient-related domain models
      /treatment      # Treatment-related domain models
      /assessment     # Assessment-related domain models
      /digital_twin   # Digital twin domain models
    /repositories     # Repository interfaces
    /services         # Domain services
    /events           # Domain events
    /exceptions       # Domain-specific exceptions
    
  /infrastructure     # Infrastructure Layer
    /repositories     # Repository implementations
    /db               # Database-specific code
      /models         # ORM models
      /migrations     # Database migrations
      /mappers        # Entity-to-model mappers
    /services         # External service implementations
    /auth             # Authentication infrastructure
    /messaging        # Messaging infrastructure
    /storage          # File storage infrastructure
    
  /core               # Core Layer
    /config           # Configuration management
    /logging          # Logging utilities
    /security         # Security utilities
    /utils            # Common utilities
    /exceptions       # Base exceptions
    
  /main.py            # Application entry point
```

## Implementation Guidelines

When implementing the clean architecture in the Novamind Digital Twin Platform, follow these guidelines:

### General Guidelines

1. **Single Responsibility Principle**: Each module, class, and function should have one responsibility
2. **Dependency Inversion**: High-level modules should not depend on low-level modules
3. **Interface Segregation**: Many client-specific interfaces are better than one general-purpose interface
4. **Open/Closed Principle**: Software entities should be open for extension but closed for modification
5. **Liskov Substitution Principle**: Objects should be replaceable with instances of their subtypes

### Domain Layer Guidelines

1. **Rich Domain Model**: Implement behavior in entities, not just data
2. **Value Objects**: Use immutable value objects for descriptive aspects
3. **Domain Services**: Create domain services for operations that don't fit in entities
4. **Aggregate Roots**: Define clear boundaries and access rules
5. **Repository Interfaces**: Define repository interfaces for data access

### Application Layer Guidelines

1. **Thin Services**: Keep application services focused on orchestration
2. **Use Cases**: Implement one service method per use case
3. **DTOs**: Use DTOs for data transfer across boundaries
4. **CQRS When Appropriate**: Separate commands and queries when beneficial
5. **Validation**: Validate inputs at the application layer

### Infrastructure Layer Guidelines

1. **Implementation Isolation**: Keep infrastructure implementations isolated
2. **Dependency Injection**: Use DI to provide implementations to upper layers
3. **Transaction Management**: Manage transactions at the infrastructure level
4. **Performance Optimization**: Implement performance optimizations here
5. **External Integration**: Isolate external system integration

### API Layer Guidelines

1. **Thin Controllers**: Keep controllers focused on HTTP concerns
2. **Input Validation**: Validate all inputs at the API boundary
3. **Documentation**: Document all API endpoints thoroughly
4. **Versioning**: Implement proper API versioning
5. **Error Handling**: Implement consistent error handling

### Testing Guidelines

1. **Domain Tests**: Test domain logic in isolation
2. **Service Tests**: Test application services with mock repositories
3. **Integration Tests**: Test infrastructure components with real dependencies
4. **API Tests**: Test API endpoints with mock services
5. **End-to-End Tests**: Test complete workflows

## Conclusion

The clean architecture approach provides the Novamind Digital Twin Platform with a solid foundation for building a complex healthcare system that remains maintainable, testable, and adaptable over time. By adhering to these principles and guidelines, the platform can evolve while keeping its core business logic stable and protected from technical changes.

This architecture enables the Novamind Digital Twin Platform to:

1. Adapt to changing requirements and technologies
2. Support comprehensive testing at all levels
3. Maintain clear separation of concerns
4. Scale individual components independently
5. Ensure security and compliance by design

Teams working on the platform should use this document as a reference for understanding the architectural principles and making implementation decisions aligned with the clean architecture approach.