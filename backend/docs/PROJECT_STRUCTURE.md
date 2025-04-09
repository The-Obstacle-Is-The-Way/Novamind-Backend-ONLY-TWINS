# Novamind Digital Twin Backend Project Structure

## Overview

This document describes the canonical project structure for the Novamind Digital Twin Backend project, which follows Clean Architecture principles. The organization optimizes for maintainability, HIPAA compliance, and scalability.

## Root Directory

The root directory contains only essential files and symlinks. All other files are organized into appropriate subdirectories:

- `app/` - Main application code 
- `config/` - Configuration files
- `deployment/` - Deployment scripts and configuration
- `docs/` - Documentation
- `logs/` - Log files 
- `scripts/` - Utility scripts
- `tests/` - Test files
- `main.py` - Entry point for FastAPI application
- `README.md` - Project overview
- `LICENSE` - Open source license

## Configuration `/config`

Configuration files are organized by function:

- `config/env/` - Environment variables and `.env` files
- `config/test/` - Testing configuration (pytest, etc.)
- `config/typescript/` - TypeScript configuration

## Deployment `/deployment`

All deployment-related files:

- `deployment/Dockerfile` - Docker container definition
- `deployment/docker-compose.yml` - Docker Compose services
- `deployment/*.sh` - Deployment scripts for different environments

## Documentation `/docs`

Project documentation:

- `docs/PROJECT_STRUCTURE.md` - This file
- `docs/DEPLOYMENT.md` - Deployment instructions
- `docs/TEMPORAL_NEUROTRANSMITTER_IMPLEMENTATION.md` - Feature documentation

## Application Code `/app`

The app directory follows Clean Architecture layering:

### Domain Layer `/app/domain`

Pure business logic with no external dependencies:

- `app/domain/entities/` - Domain models and value objects 
- `app/domain/services/` - Domain services
- `app/domain/repositories/` - Repository interfaces

### Application Layer `/app/application`

Orchestration of domain operations:

- `app/application/services/` - Application services
- `app/application/use_cases/` - Use case implementations

### Infrastructure Layer `/app/infrastructure`

External concerns implementation:

- `app/infrastructure/models/` - ORM models
- `app/infrastructure/repositories/` - Repository implementations
- `app/infrastructure/database/` - Database configuration
- `app/infrastructure/persistence/` - Persistence utilities
- `app/infrastructure/di/` - Dependency injection

### API Layer `/app/api`

FastAPI implementation:

- `app/api/routes/` - API routes
- `app/api/dependencies/` - FastAPI dependencies
- `app/api/schemas/` - Pydantic schemas 

### Core `/app/core`

Cross-cutting concerns:

- `app/core/config/` - Application configuration
- `app/core/security/` - Authentication and authorization
- `app/core/utils/` - Utility functions
- `app/core/auth/` - Authentication utilities

## Scripts `/scripts`

Utility scripts organized by function:

- `scripts/run_*.sh/py/bat` - Execution scripts
- `scripts/verify_*.py` - Verification scripts
- `scripts/update_*.py` - Update utilities
- `scripts/README.md` - Scripts documentation

## Logs `/logs` 

Standardized location for all log files, properly gitignored.

## Tests `/tests`

Tests organized by application layer:

- `tests/domain/` - Domain layer tests
- `tests/application/` - Application layer tests
- `tests/infrastructure/` - Infrastructure layer tests
- `tests/api/` - API layer tests

## Security Reports `/security-reports`

Security test results and audit reports.

## Benefits of This Structure

1. **Separation of Concerns**: Clear boundaries between business logic and infrastructure
2. **Testability**: Each layer can be tested independently 
3. **Maintainability**: New developers can quickly locate relevant code
4. **HIPAA Compliance**: Security concerns are isolated and properly managed
5. **Scalability**: Modular design facilitates expansion of features and services