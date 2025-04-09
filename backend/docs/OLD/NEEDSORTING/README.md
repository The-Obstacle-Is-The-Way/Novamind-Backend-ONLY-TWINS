# NOVAMIND Digital Twin Platform

NOVAMIND is a premium, HIPAA-compliant concierge psychiatry platform designed for a solo provider practice with potential for future growth. This platform integrates cutting-edge Digital Twin technology to deliver personalized psychiatric care.

## Features

- **Digital Twin Technology**: Computational representation of a patient's psychiatric state
- **Symptom Trajectory Forecasting**: Predict symptom progression and detect early warning signs
- **Biometric-Mental Correlation**: Link physiological markers to mental states
- **Precision Medication Modeling**: Personalize medication selection based on genetics and history
- **HIPAA Compliance**: End-to-end security and privacy controls

## Architecture

This project follows Clean Architecture principles with a strict separation of:
- Domain Layer: Pure business logic
- Application Layer: Use cases and application services
- Infrastructure Layer: External frameworks and tools
- Presentation Layer: API endpoints

## Getting Started

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
5. Set up environment variables: Copy `.env.example` to `.env` and update values
6. Run migrations: `alembic upgrade head`
7. Start the server: `uvicorn app.presentation.api.main:app --reload`

## License

Proprietary software.
