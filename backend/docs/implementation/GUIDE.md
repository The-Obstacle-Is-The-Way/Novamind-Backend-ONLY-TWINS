# Novamind Digital Twin Implementation Guide

This guide provides instructions for using and extending the Novamind Digital Twin framework.

## System Overview

The Novamind Digital Twin platform integrates three specialized AI components:

1. **PAT (Pretrained Actigraphy Transformer)** - Processes wearable device data
2. **XGBoost Prediction Engine** - Delivers clinical predictions and brain modeling
3. **MentalLLaMA-33B** - Specialized LLM for psychiatric text analysis

These components are orchestrated by the Digital Twin Core, which manages state transitions and provides a unified interface for applications.

## Project Structure

```
app/
├── domain/                   # Pure domain models and interfaces
│   ├── entities/             # Business entities
│   ├── repositories/         # Data access interfaces
│   └── services/             # Service interfaces
├── infrastructure/           # Implementation of interfaces
│   ├── factories/            # Component creation and wiring
│   ├── repositories/         # Repository implementations
│   └── services/             # Service implementations
├── application/              # Application use cases
│   └── digital_twin/         # Digital Twin specific use cases
├── presentation/             # API and UI components
│   ├── api/                  # FastAPI endpoints
│   └── schemas/              # API request/response schemas
├── demo/                     # Demonstration scripts
└── tests/                    # Tests
    ├── unit/                 # Unit tests
    └── integration/          # Integration tests
```

## Getting Started

### Running the Demo

The easiest way to see the Digital Twin in action is to run the demo script:

```bash
# From the project root
python -m app.demo.run_digital_twin_demo
```

This will:
1. Create a sample patient with realistic clinical data
2. Initialize a Digital Twin state
3. Process actigraphy data from a wearable device
4. Analyze clinical notes using MentalLLaMA
5. Generate treatment recommendations
6. Create visualizations of the brain model
7. Generate a comprehensive clinical summary

The demo outputs JSON files to `app/demo/output/` for inspection.

### Running Tests

To verify that all components are working correctly, run the integration test:

```bash
# From the project root
pytest app/tests/integration/test_digital_twin_integration.py -v
```

## Using the Digital Twin Core

### Initializing the System

The factory pattern makes it easy to create and wire all components:

```python
from app.infrastructure.factories.mock_digital_twin_factory import MockDigitalTwinFactory

# Create the core service with all dependencies
digital_twin_core = MockDigitalTwinFactory.create_digital_twin_core()

# Or get all components individually
system = MockDigitalTwinFactory.create_complete_system()
digital_twin_repository = system["repositories"]["digital_twin_repository"]
patient_repository = system["repositories"]["patient_repository"]
```

### Working with Patients

Create and save a patient:

```python
from datetime import datetime, timedelta
from uuid import uuid4
from app.domain.entities.patient import Patient, Gender, Diagnosis, Medication

# Create a patient
patient = Patient(
    id=uuid4(),
    first_name="John",
    last_name="Smith",
    date_of_birth=datetime.now() - timedelta(days=365 * 40),
    gender=Gender.MALE,
    diagnoses=[
        Diagnosis(
            code="F32.1",
            name="Major depressive disorder, single episode, moderate",
            date_diagnosed=datetime.now() - timedelta(days=90),
            is_active=True
        )
    ],
    medications=[
        Medication(
            name="Sertraline",
            dosage="50mg",
            frequency="daily",
            start_date=datetime.now() - timedelta(days=30),
            is_active=True
        )
    ]
)

# Save the patient
saved_patient = await patient_repository.save(patient)
```

### Managing the Digital Twin

Initialize a Digital Twin for a patient:

```python
# Initialize the Digital Twin
initial_state = await digital_twin_core.initialize_digital_twin(
    patient_id=patient.id,
    initial_data={
        "clinical_metrics": {
            "phq9_score": 14,  # Moderate depression
            "gad7_score": 12   # Moderate anxiety
        }
    }
)
```

Update the Digital Twin with actigraphy data:

```python
# Prepare actigraphy data
actigraphy_data = {
    "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
    "end_time": datetime.now().isoformat(),
    "daily_activity": [
        {"date": (datetime.now() - timedelta(days=i)).date().isoformat(), 
         "steps": 5000, "active_minutes": 30}
        for i in range(7)
    ],
    "sleep_data": [
        {"date": (datetime.now() - timedelta(days=i)).date().isoformat(), 
         "duration_hours": 6.5, "efficiency": 0.8}
        for i in range(7)
    ]
}

# Update the Digital Twin
updated_state = await digital_twin_core.update_from_actigraphy(
    patient_id=patient.id,
    actigraphy_data=actigraphy_data,
    data_source="fitbit"
)
```

Process clinical notes:

```python
# Clinical notes from a session
clinical_note = """
Patient reports continued depressive symptoms with moderate severity.
Sleep has improved somewhat with current medication, but still experiencing
early morning awakening. Will continue Sertraline at current dose.
"""

# Update the Digital Twin with the notes
updated_state = await digital_twin_core.update_from_clinical_notes(
    patient_id=patient.id,
    note_text=clinical_note,
    note_type="progress_note",
    clinician_id=uuid4()  # ID of the clinician who wrote the note
)
```

Generate treatment recommendations:

```python
# Generate recommendations
recommendations = await digital_twin_core.generate_treatment_recommendations(
    patient_id=patient.id,
    include_rationale=True
)

# Review top recommendations
for rec in recommendations[:3]:
    print(f"{rec['type'].title()}: {rec['name']}")
    print(f"Efficacy: {rec.get('predicted_efficacy', 0) * 100:.1f}%")
    if "rationale" in rec:
        print(f"Rationale: {rec['rationale']}")
```

Generate brain visualization data:

```python
# Get visualization data
visualization_data = await digital_twin_core.get_visualization_data(
    patient_id=patient.id,
    visualization_type="brain_model"
)

# This data can be passed to a 3D visualization component
```

Generate a comprehensive clinical summary:

```python
# Generate summary
summary = await digital_twin_core.generate_clinical_summary(
    patient_id=patient.id,
    include_treatment_history=True,
    include_predictions=True
)

# The summary contains patient details, insights, recommendations, and risk assessments
```

## Extending the System

### Implementing Real Services

To replace the mock implementations with real ones:

1. **Create concrete implementations** of the service interfaces that connect to your actual AI models
2. **Update the factory** to use your real implementations
3. **Create a database-backed repository** implementation

Example implementation for a real XGBoost service:

```python
class RealXGBoostService(XGBoostService):
    def __init__(self, model_path: str, config: Dict):
        import xgboost as xgb
        self.model = xgb.Booster()
        self.model.load_model(model_path)
        self.config = config
    
    async def predict_treatment_response(
        self,
        patient_id: UUID,
        digital_twin_state_id: UUID,
        treatment_options: List[Dict],
        time_horizon: str = "short_term"
    ) -> Dict:
        # Real implementation using actual XGBoost model
        # ...
```

### Adding New AI Components

To add a new AI component:

1. **Define a domain service interface** in the domain layer
2. **Create mock and real implementations** in the infrastructure layer
3. **Update the DigitalTwinCoreService** to use the new component
4. **Update the factory** to wire up the new component

### Database Integration

To implement database-backed repositories:

1. **Create ORM models** corresponding to your domain entities
2. **Implement the repository interfaces** using your chosen database technology
3. **Update the factory** to use your database repositories

## AWS HIPAA-Compliant Deployment

For a production HIPAA-compliant deployment:

1. **Use AWS HIPAA-eligible services**:
   - Amazon RDS with encryption for databases
   - Amazon S3 with encryption for file storage
   - AWS Lambda for serverless compute
   - Amazon Cognito for authentication
   - AWS KMS for key management

2. **Implement proper encryption**:
   - Encryption at rest using KMS
   - Encryption in transit using TLS
   - Client-side encryption for sensitive data

3. **Set up access controls**:
   - IAM roles with least privilege
   - Multi-factor authentication
   - Role-based access control

4. **Configure audit logging**:
   - AWS CloudTrail for API activity
   - AWS CloudWatch for application logs
   - Custom PHI access logging

5. **Implement backup and recovery**:
   - Automated backups
   - Cross-region replication
   - Disaster recovery plan

## Conclusion

The Novamind Digital Twin framework provides a robust foundation for building a state-of-the-art psychiatric care platform. By following clean architecture principles and implementing the proper interfaces, you can extend and customize the system to meet your specific requirements while maintaining HIPAA compliance and excellent performance.