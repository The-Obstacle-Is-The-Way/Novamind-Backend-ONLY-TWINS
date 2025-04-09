# Psychiatric Digital Twin Platform

A state-of-the-art psychiatric digital twin system implementing the Trinity Stack architecture: MentalLLaMA (LLM for clinical inference), PAT (Pattern Analysis Technology), and XGBoost (treatment optimization).

## 🧠 Overview

The Psychiatric Digital Twin Platform is a groundbreaking system that creates virtual models of psychiatric patients, enabling clinicians and researchers to simulate treatment responses, predict outcomes, and optimize care. The platform integrates multiple data sources, applies advanced machine learning techniques, and adheres to strict HIPAA compliance requirements.

### The Trinity Stack

Our architecture is built on three powerful AI/ML pillars:

1. **MentalLLaMA**: Large Language Model specialized for psychiatric inference from clinical notes, assessments, and other text-based data
2. **PAT (Pattern Analysis Technology)**: Time-series analysis engine that identifies temporal patterns in behavioral and physiological data
3. **XGBoost**: Gradient-boosted decision tree ensemble for treatment optimization and outcome prediction

## 🏗️ Architecture

The platform follows Clean Architecture principles, with a strict separation of concerns:

- **Domain Layer**: Core business logic and entities, free from external dependencies
- **Application Layer**: Use cases that orchestrate domain entities to fulfill business requirements
- **Infrastructure Layer**: External services, repositories, and adapters
- **API Layer**: FastAPI endpoints with proper validation and documentation
- **Core Layer**: Cross-cutting concerns like security, logging, and configuration

## 🔒 HIPAA Compliance & Security

The platform incorporates comprehensive security features for HIPAA compliance:

- Robust authentication and authorization with role-based access control
- Comprehensive audit logging of all data access
- PHI sanitization to prevent exposure of sensitive information
- Encrypted data storage and TLS for data in transit
- Session timeout and automatic logout mechanisms
- Input validation and parameterized queries to prevent injection attacks

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- MongoDB 4.4+
- PostgreSQL 13+
- Redis 6.0+ (optional, for caching)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/psychiatric-digital-twin.git
   cd psychiatric-digital-twin
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r backend/requirements-dev.txt  # For development
   ```

4. Set up environment variables (create a .env file):
   ```
   ENVIRONMENT=development
   DEBUG=true
   
   # Database
   DB_MONGODB_URI=mongodb://localhost:27017
   DB_MONGODB_DATABASE=digital_twin
   DB_POSTGRES_SERVER=localhost
   DB_POSTGRES_PORT=5432
   DB_POSTGRES_USER=postgres
   DB_POSTGRES_PASSWORD=postgres
   DB_POSTGRES_DB=digital_twin
   
   # Security
   SECURITY_SECRET_KEY=your-secret-key-here
   SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=30
   SECURITY_AUTH_REQUIRED=true
   ```

5. Initialize the database:
   ```bash
   cd backend
   alembic upgrade head
   ```

6. Run the application:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

7. Access the API documentation at http://localhost:8000/docs

## 📚 Directory Structure

```
backend/
├── alembic/                 # Database migrations
├── app/
│   ├── api/                 # API layer
│   │   └── v1/              # API version 1
│   │       ├── endpoints/   # API endpoints
│   │       └── schemas/     # Request/response schemas
│   ├── application/         # Application layer
│   │   └── use_cases/       # Application services and use cases
│   ├── core/                # Core functionality
│   │   └── security/        # Authentication and security
│   ├── domain/              # Domain layer
│   │   └── refactored/      # Refactored domain model
│   │       ├── entities/    # Domain entities
│   │       ├── repositories/# Repository interfaces
│   │       └── services/    # Domain services
│   └── infrastructure/      # Infrastructure layer
│       └── repositories/    # Repository implementations
├── docs/                    # Documentation
└── tests/                   # Tests
```

## ⚙️ Key Components

### Digital Twin Subject

The core entity representing a subject for whom a digital twin is created. Subjects can be research, clinical, or anonymous, with different levels of demographic and clinical information.

### Digital Twin State

Represents the state of a digital twin at a specific point in time, including brain region activity, neurotransmitter levels, clinical insights, and temporal patterns.

### Trinity Stack Components

- **MentalLLaMA Service**: Interprets clinical text and generates insights
- **PAT Service**: Analyzes time-series data to identify meaningful patterns
- **XGBoost Service**: Predicts outcomes and optimizes treatment plans

## 🧪 Testing

Run tests with pytest:

```bash
cd backend
pytest
```

For test coverage:

```bash
cd backend
pytest --cov=app
```

## 📝 API Documentation

The API is documented using OpenAPI/Swagger. After starting the application, access:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📊 Project Status

This project is in active development. The core architecture and domain model have been implemented, with ongoing work on enhancing the Trinity Stack components and extending API functionality.
