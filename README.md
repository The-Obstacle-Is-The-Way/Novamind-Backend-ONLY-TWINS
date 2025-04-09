# NOVAMIND Digital Twin: Concierge Psychiatry Platform - Backend Only

A cutting-edge psychiatric platform with Digital Twin technology for personalized treatment planning and visualization. This repository contains only the backend components.

## Project Structure

This project follows a clean architecture with clear separation of concerns:

```
novamind-backend/
├── backend/             # All backend code and configuration
│   ├── app/             # FastAPI application
│   │   ├── api/         # API endpoints
│   │   ├── application/ # Application services and use cases
│   │   ├── core/        # Core utilities and configuration
│   │   ├── domain/      # Domain models and business logic
│   │   └── infrastructure/ # External services integration
│   ├── alembic/         # Database migration scripts
│   ├── docs/            # Backend documentation
│   ├── tests/           # Test suite
│   ├── main.py          # FastAPI application entry point
│   └── requirements.txt # Python dependencies
│
├── deployment/          # Deployment scripts and configurations
├── reports/             # Generated reports
├── security-reports/    # Security audit reports
├── tools/               # Shared tools and utilities
│
└── README.md            # This file
```

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized deployment)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-security.txt
pip install -r requirements-analytics.txt

# Run the FastAPI application
uvicorn app.main:app --reload
```

The backend API will be available at http://localhost:8000.

### Docker Deployment

```bash
# Build and start the containers
docker-compose -f deployment/docker-compose.yml up -d

# To stop the containers
docker-compose -f deployment/docker-compose.yml down
```

## Development Guidelines

### Backend

- Follow clean architecture principles
- Keep domain logic pure and framework-agnostic
- Use type hints and docstrings
- Write tests for all new features
- Implement proper error handling

## HIPAA Compliance

This application handles sensitive patient data and must comply with HIPAA regulations:

- No PHI in URLs (use POST only for sensitive data)
- Implement proper authentication and authorization
- Log all data access for audit trails
- Encrypt all data in transit and at rest
- Implement proper session timeouts and auto-logout
- Regular security audits and vulnerability testing

## License

See the [LICENSE](LICENSE) file for details.
