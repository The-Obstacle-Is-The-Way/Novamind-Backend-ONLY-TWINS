# DEPENDENCY INJECTION GLOSSARY

## Overview

This document provides a comprehensive glossary of all dependency injections in the NOVAMIND platform. It serves as a reference for AI agents and developers to understand the complete dependency tree, making it easier to maintain and extend the system.

## Domain Layer Dependencies

### Domain Entities

Domain entities are the core business objects that represent the fundamental concepts in the system. They typically don't have dependencies injected into them, as they are created using constructors or factory methods.

| Entity | Description | Dependencies |
|--------|-------------|--------------|
| `Patient` | Represents a patient in the concierge psychiatry practice | None |
| `Provider` | Represents a healthcare provider | None |
| `Appointment` | Represents a scheduled appointment | None |
| `ClinicalNote` | Represents a clinical note | None |
| `Medication` | Represents a medication | None |
| `DigitalTwin` | Represents a patient's digital twin | None |

### Domain Services

Domain services encapsulate complex business logic that doesn't naturally fit within a single entity.

| Service | Description | Dependencies |
|---------|-------------|--------------|
| `PatientService` | Manages patient-related business logic | `PatientRepository`, `ProviderRepository`, `AppointmentRepository`, `ClinicalNoteRepository` |
| `AppointmentService` | Manages appointment-related business logic | `AppointmentRepository`, `PatientRepository`, `ProviderRepository` |
| `ClinicalDocumentationService` | Manages clinical documentation | `ClinicalNoteRepository`, `PatientRepository` |
| `MedicationService` | Manages medication-related business logic | `MedicationRepository`, `PatientRepository` |
| `ProviderService` | Manages provider-related business logic | `ProviderRepository` |
| `DigitalTwinService` | Manages digital twin-related business logic | `DigitalTwinRepository`, `PatientRepository` |
| `AIAssistantService` | Manages AI-assisted features | `MLServiceInterface` |
| `AnalyticsService` | Manages analytics and reporting | Various repositories |

## Application Layer Dependencies

### Use Cases

Use cases represent the application-specific business logic that orchestrates domain entities and services.

| Use Case | Description | Dependencies |
|----------|-------------|--------------|
| `CreatePatientUseCase` | Creates a new patient | `PatientRepository` |
| `CreateAppointmentUseCase` | Creates a new appointment | `AppointmentRepository`, `PatientRepository`, `ProviderRepository` |
| `GenerateDigitalTwinUseCase` | Generates a digital twin for a patient | `DigitalTwinService`, `PatientRepository` |

### Application Services

Application services coordinate use cases and provide additional application-level functionality.

| Service | Description | Dependencies |
|---------|-------------|--------------|
| `PatientService` (Application) | Orchestrates patient-related operations | `PatientRepository` |
| `DigitalTwinService` (Application) | Orchestrates digital twin operations | `DigitalTwinRepository`, `PatientRepository` |

## Infrastructure Layer Dependencies

### Repository Implementations

Repository implementations provide concrete data access mechanisms for the domain repositories.

| Repository | Description | Dependencies |
|------------|-------------|--------------|
| `SQLAlchemyPatientRepository` | SQLAlchemy implementation of `PatientRepository` | `Database` |
| `SQLAlchemyAppointmentRepository` | SQLAlchemy implementation of `AppointmentRepository` | `Database` |
| `SQLAlchemyClinicalNoteRepository` | SQLAlchemy implementation of `ClinicalNoteRepository` | `Database` |
| `SQLAlchemyMedicationRepository` | SQLAlchemy implementation of `MedicationRepository` | `Database` |
| `SQLAlchemyProviderRepository` | SQLAlchemy implementation of `ProviderRepository` | `Database` |
| `SQLAlchemyDigitalTwinRepository` | SQLAlchemy implementation of `DigitalTwinRepository` | `Database` |
| `SQLAlchemyUserRepository` | SQLAlchemy implementation of `UserRepository` | `Database` |

### External Service Adapters

External service adapters provide interfaces to external services like AWS, OpenAI, etc.

| Adapter | Description | Dependencies |
|---------|-------------|--------------|
| `S3Client` | Adapter for AWS S3 | AWS credentials |
| `GPTClient` | Adapter for OpenAI GPT | OpenAI API key |
| `EmailService` | Adapter for email services | Email configuration |
| `SMSService` | Adapter for SMS services | SMS configuration |
| `TokenHandler` | Adapter for JWT token handling | JWT configuration |
| `PasswordHandler` | Adapter for password hashing | None |
| `RoleManager` | Adapter for role-based access control | None |

### ML Services

ML services provide machine learning capabilities to the application.

| Service | Description | Dependencies |
|---------|-------------|--------------|
| `BiometricCorrelationService` | Correlates biometric data | ML models |
| `DigitalTwinIntegrationService` | Integrates digital twin data | ML models |
| `PharmacogenomicsService` | Provides pharmacogenomics insights | ML models |
| `SymptomForecastingService` | Forecasts symptoms | ML models |

## Presentation Layer Dependencies

### API Endpoints

API endpoints expose the application's functionality through HTTP endpoints.

| Endpoint | Description | Dependencies |
|----------|-------------|--------------|
| `PatientsEndpoint` | Handles patient-related requests | `CreatePatientUseCase`, `PatientService` |
| `AppointmentsEndpoint` | Handles appointment-related requests | `CreateAppointmentUseCase`, `AppointmentService` |
| `DigitalTwinsEndpoint` | Handles digital twin-related requests | `GenerateDigitalTwinUseCase`, `DigitalTwinService` |
| `AuthEndpoint` | Handles authentication requests | `TokenHandler`, `UserRepository` |

## Dependency Injection Container

The dependency injection container is responsible for creating and managing all dependencies in the application.

| Component | Description | Dependencies |
|-----------|-------------|--------------|
| `Container` | Manages all dependencies | None |
| `get_container` | Factory function for the container | None |

## Dependency Resolution Tree

The dependency resolution tree shows how dependencies are resolved from the top level (API endpoints) down to the lowest level (repositories and external services).

```
PatientsEndpoint
├── CreatePatientUseCase
│   └── PatientRepository
│       └── SQLAlchemyPatientRepository
│           └── Database
└── PatientService (Application)
    └── PatientRepository
        └── SQLAlchemyPatientRepository
            └── Database

AppointmentsEndpoint
├── CreateAppointmentUseCase
│   ├── AppointmentRepository
│   │   └── SQLAlchemyAppointmentRepository
│   │       └── Database
│   ├── PatientRepository
│   │   └── SQLAlchemyPatientRepository
│   │       └── Database
│   └── ProviderRepository
│       └── SQLAlchemyProviderRepository
│           └── Database
└── AppointmentService
    ├── AppointmentRepository
    │   └── SQLAlchemyAppointmentRepository
    │       └── Database
    ├── PatientRepository
    │   └── SQLAlchemyPatientRepository
    │       └── Database
    └── ProviderRepository
        └── SQLAlchemyProviderRepository
            └── Database

DigitalTwinsEndpoint
├── GenerateDigitalTwinUseCase
│   ├── DigitalTwinService
│   │   └── DigitalTwinRepository
│   │       └── SQLAlchemyDigitalTwinRepository
│   │           └── Database
│   └── PatientRepository
│       └── SQLAlchemyPatientRepository
│           └── Database
└── DigitalTwinService (Application)
    ├── DigitalTwinRepository
    │   └── SQLAlchemyDigitalTwinRepository
    │       └── Database
    └── PatientRepository
        └── SQLAlchemyPatientRepository
            └── Database

AuthEndpoint
├── TokenHandler
│   └── JWT configuration
└── UserRepository
    └── SQLAlchemyUserRepository
        └── Database
```

This tree illustrates how dependencies are resolved from the top level (API endpoints) down to the lowest level (repositories and external services). Each level depends on the level below it, with the container managing the creation and lifecycle of all components.