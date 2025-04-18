# NovaMind Digital Twin Backend

> A HIPAA‑compliant, ML‑driven backend for creating and managing "digital twins" of patients—aggregating wearable data, surfacing analytics, automating alerts, and drafting clinical documentation to augment psychiatric care.

## Table of Contents

1. [Features](#features)  
2. [Architecture Overview](#architecture-overview)  
3. [Getting Started](#getting-started)  
   - [Prerequisites](#prerequisites)  
   - [Installation](#installation)  
   - [Configuration](#configuration)  
   - [Database Migrations](#database-migrations)  
   - [Run Locally](#run-locally)  
4. [Usage Examples](#usage-examples)  
5. [Testing & Quality](#testing--quality)  
6. [Security & Audits](#security--audits)  
7. [Tools & Scripts](#tools--scripts)  
8. [Docker & Deployment](#docker--deployment)  
9. [Configuration Reference](#configuration-reference)  
10. [Contributing](#contributing)  
11. [License](#license)  

## Features

- **Patient Management**: CRUD APIs for encrypted, PHI‑safe patient records.  
- **Biometric Ingestion**: High‑frequency wearable/event streams (actigraphy, HR, sleep).  
- **Digital Twin Generation**: Aggregate time‑series into unified patient profiles.  
- **Predictive Analytics**: XGBoost, LSTM, and LLM‑driven risk insights.  
- **Rule‑Based Alerts**: Dynamic clinical rule engine for threshold/anomaly notifications.  
- **Clinical Documentation**: Auto‑draft encounter notes via OpenAI LLM.  
- **Secure Messaging**: SMS/email reminders & alerts (Twilio/SES).  
- **PHI Sanitization & Audit**: Middleware that strips/logs PHI access events.  
- **Auth & RBAC**: JWT authentication, role‑based access control, rate limiting.  

## Architecture Overview

```ascii
┌───────────────────┐      ┌───────────────────┐
│  Presentation     │─▶───▶│  Application      │
│ (FastAPI + Schemas│      │ (Use‑Cases)       │
│  + Middleware)    │      └───────────────────┘
└───────────────────┘              │
        ▲                          ▼
        │                  ┌───────────────────┐
┌───────────────────┐      │  Domain           │
│ Infrastructure    │◀────▶│ (Pydantic Models) │
│ (DB, ML, Cache,   │      └───────────────────┘
│  Messaging, Auth) │
└───────────────────┘
```

- **Hexagonal/Clean** layering:  
  - Business core in `app/domain` & `app/application`  
  - Adapters in `app/infrastructure`  
  - HTTP in `app/presentation`

## Getting Started

### Prerequisites

- **Git**  
- **Python 3.10+**  
- **PostgreSQL 13+**  
- **Redis**  
- **Docker & Docker Compose** (optional)  
- **AWS Credentials** (S3)  
- **OpenAI API Key**  

### Installation

```bash
git clone https://github.com/your-org/NovaMind-DigitalTwin-Backend.git
cd NovaMind-DigitalTwin-Backend
```

### Configuration

This project uses Pydantic V2's BaseSettings. You must set the following environment variables (or load them via your own .env):

1. **Core**
   - `ENVIRONMENT`: development/test/staging/production
   - `DATABASE_URL`: Postgres DSN (postgres://user:pass@host:5432/db)
   - `REDIS_URL`: Redis URI (redis://host:6379/0)
   - `JWT_SECRET_KEY`: Secret for signing JWTs

2. **AWS & Storage**
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - `S3_BUCKET`: for any attachments

3. **OpenAI**
   - `OPENAI_API_KEY`
   - `MENTALLAMA_MODEL_MAPPINGS`: JSON string mapping LLM model names

4. **XGBoost Models**
   - `XGBOOST_TREATMENT_RESPONSE_MODEL_PATH`
   - `XGBOOST_OUTCOME_PREDICTION_MODEL_PATH`
   - `XGBOOST_RISK_PREDICTION_MODEL_PATH`

5. **Feature Flags**
   - `RATE_LIMITING_ENABLED`: true/false
   - `PHI_SANITIZATION_ENABLED`: true/false

(See [Configuration Reference](#configuration-reference) for full details.)

### Database Migrations

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### Run Locally

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.

## Usage Examples

Replace `<TOKEN>` with a valid JWT from `/api/v1/auth/login`.

```bash
# Create Patient
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{ "first_name": "Alice", "last_name": "Smith", "date_of_birth":"1985-07-20" }'

# Ingest Biometric Event
curl -X POST http://localhost:8000/api/v1/biometric-events \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{ "patient_id":"<UUID>", "data_type":"heart_rate", "timestamp":"2025-04-17T14:23:00Z", "data":{"bpm":72} }'

# Generate Digital Twin
curl -X POST http://localhost:8000/api/v1/digital-twins/generate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{ "patient_id":"<UUID>" }'

# Retrieve Aggregated Analytics
curl -G http://localhost:8000/api/v1/analytics/aggregated \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "patient_id=<UUID>"
```

## Testing & Quality

### Unit Tests

```bash
cd backend
pytest app/tests/unit
```

### Integration Tests

```bash
docker-compose -f deployment/docker-compose.test.yml up -d
pytest app/tests/integration
```

### Lint & Type

```bash
flake8 app
black --check app
isort --check-only --profile black app
mypy app
```

### Coverage

```bash
pytest --cov=app
```

## Security & Audits

- PHI Audits: see `reports/` & `security-reports/`

### Run PHI Audit

```bash
python tools/security/run_phi_audit_only.py
```

### Dependency Scans

```bash
python tools/security/bandit-runner.py
```

## Tools & Scripts

- **Maintenance**: `tools/maintenance/` (refactor, migration helpers)
- **Prompt Templates**: `prompt-templates/`
- **Demo Scripts**: `demo/`
- **Architecture Docs**: `docs/`

## Docker & Deployment

```bash
docker-compose -f deployment/docker-compose.yml up --build
```

Services: FastAPI API, Postgres, Redis, (optional) Traefik ingress.

For production CI/CD:

- One pipeline for lint/tests/security
- One pipeline for build/push Docker & helm/k8s deploy
- Health checks & auto‑migrations on startup

## Configuration Reference

| Env Var | Description | Example |
|---------|-------------|---------|
| `ENVIRONMENT` | development/test/staging/production | `production` |
| `DATABASE_URL` | Postgres DSN | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | Redis URI | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing secret | `supersecretjwtkey` |
| `AWS_ACCESS_KEY_ID` | AWS IAM key | `AKIA…` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret | `wJalrXUtnFEMI/K7…` |
| `S3_BUCKET` | S3 bucket name for attachments | `novamind-backend-prod` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-…` |
| `MENTALLAMA_MODEL_MAPPINGS` | JSON mapping of LLM model identifiers | `{"clinical":"gpt-4","psychiatry":"gpt-4"}` |
| `XGBOOST_TREATMENT_RESPONSE_MODEL_PATH` | Path to XGBoost treatment response model | `/models/treatment_response.xgb` |
| `XGBOOST_OUTCOME_PREDICTION_MODEL_PATH` | Path to outcome prediction model | `/models/outcome_prediction.xgb` |
| `XGBOOST_RISK_PREDICTION_MODEL_PATH` | Path to risk prediction model | `/models/risk_prediction.xgb` |
| `RATE_LIMITING_ENABLED` | Enable in‑memory rate limiting (true/false) | `true` |
| `PHI_SANITIZATION_ENABLED` | Enable PHI detection & sanitization (true/false) | `true` |

## Contributing

We love contributions! Please:

1. Fork & create a feature branch.
2. Install hooks: `pre-commit install`.
3. Adhere to linters (black, isort, flake8) and add tests.
4. Open a clear PR referencing an issue.

See `CONTRIBUTING.md` for details.

## License

This project is licensed under the Apache License 2.0.
See `LICENSE` for the full terms.
