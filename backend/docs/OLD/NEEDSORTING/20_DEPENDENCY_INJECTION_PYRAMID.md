# DEPENDENCY INJECTION PYRAMID

## Overview

This document outlines the foundational dependency injection pyramid for the NOVAMIND platform, providing a comprehensive source of truth for all modules and their dependencies. This pyramid serves as a guide for AI agents and developers to understand how components are wired together, ensuring consistent and maintainable code.

## 1. Dependency Injection Pyramid Structure

The NOVAMIND platform follows a clean architecture approach with strict layering, where dependencies flow inward from the outer layers to the inner layers. The dependency injection pyramid reflects this architecture, with the domain layer at the core and the presentation layer at the outermost level.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     APPLICATION LAYER                           │    │
│  │                                                                 │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │                     DOMAIN LAYER                        │    │    │
│  │  │                                                         │    │    │
│  │  │   ┌─────────────────────────────────────────────────┐   │    │    │
│  │  │   │             CORE ENTITIES & VALUE OBJECTS       │   │    │    │
│  │  │   └─────────────────────────────────────────────────┘   │    │    │
│  │  │                                                         │    │    │
│  │  │   ┌─────────────────────────────────────────────────┐   │    │    │
│  │  │   │           DOMAIN REPOSITORY INTERFACES          │   │    │    │
│  │  │   └─────────────────────────────────────────────────┘   │    │    │
│  │  │                                                         │    │    │
│  │  │   ┌─────────────────────────────────────────────────┐   │    │    │
│  │  │   │               DOMAIN SERVICES                   │   │    │    │
│  │  │   └─────────────────────────────────────────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │                                                                 │    │
│  │   ┌─────────────────────────────────────────────────────────┐   │    │
│  │   │                     USE CASES                           │   │    │
│  │   └─────────────────────────────────────────────────────────┘   │    │
│  │                                                                 │    │
│  │   ┌─────────────────────────────────────────────────────────┐   │    │
│  │   │               APPLICATION SERVICES                      │   │    │
│  │   └─────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     API ENDPOINTS                               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     SCHEMAS & VALIDATORS                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       INFRASTRUCTURE LAYER                              │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │               REPOSITORY IMPLEMENTATIONS                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │               EXTERNAL SERVICE ADAPTERS                         │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │               DEPENDENCY INJECTION CONTAINER                    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

1. **Core Entities & Value Objects**: The foundational domain models that represent the business concepts.
2. **Domain Repository Interfaces**: Abstract interfaces defining data access operations.
3. **Domain Services**: Services that encapsulate complex domain logic.
4. **Use Cases**: Application-specific business logic that orchestrates domain entities and services.
5. **Application Services**: Services that coordinate use cases and provide additional application-level functionality.
6. **API Endpoints**: FastAPI route handlers that expose the application's functionality.
7. **Schemas & Validators**: Pydantic models for request/response validation.
8. **Repository Implementations**: Concrete implementations of the domain repository interfaces.
9. **External Service Adapters**: Adapters for external services like AWS, OpenAI, etc.
10. **Dependency Injection Container**: The container that manages all dependencies and their lifecycles.

## 2. Dependency Flow

The dependency flow in the NOVAMIND platform follows the Dependency Inversion Principle, where high-level modules depend on abstractions, not concrete implementations. This is achieved through constructor injection at all levels of the application.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEPENDENCY FLOW                                  │
│                                                                         │
│   API Endpoints                                                         │
│        │                                                                │
│        ▼                                                                │
│   Use Cases / Application Services                                      │
│        │                                                                │
│        ▼                                                                │
│   Domain Services                                                       │
│        │                                                                │
│        ▼                                                                │
│   Repository Interfaces                                                 │
│        │                                                                │
│        ▼                                                                │
│   Repository Implementations                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3. Dependency Injection Container

The Dependency Injection Container is responsible for creating and managing all dependencies in the application. It is implemented in the `app/infrastructure/di/container.py` file and follows these principles:

1. **Constructor Injection**: All dependencies are injected through constructors.
2. **No Singletons**: No hidden global state or singletons are used.
3. **Explicit Dependencies**: All dependencies are explicitly declared.
4. **Lifecycle Management**: The container manages the lifecycle of all dependencies.

## 4. FastAPI Integration

FastAPI's dependency injection system is used to wire up the dependencies at the API level. This is done using the `Depends()` function, which creates a dependency that can be injected into route handlers.

```python
from fastapi import APIRouter, Depends

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.infrastructure.di.container import get_container

router = APIRouter()

@router.post("/patients")
async def create_patient(
    patient_data: PatientCreate,
    use_case: CreatePatientUseCase = Depends(get_container().get_create_patient_use_case)
):
    return await use_case.execute(patient_data.dict())
```

In this example, the `get_container().get_create_patient_use_case` function returns a factory that creates a new instance of the `CreatePatientUseCase` with all its dependencies injected.