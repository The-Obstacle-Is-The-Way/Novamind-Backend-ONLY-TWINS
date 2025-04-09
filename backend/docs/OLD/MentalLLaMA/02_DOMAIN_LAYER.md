# DOMAIN_LAYER

## Overview

The Domain Layer contains the core business logic and entities for the NOVAMIND psychiatric platform. This layer is completely independent of frameworks, databases, or external services.

## Key Principles

- **Zero External Dependencies**: No imports from FastAPI, SQLAlchemy, or any other framework
- **Pure Business Logic**: Contains only domain rules and psychiatric practice operations
- **Rich Domain Model**: Entities contain behavior, not just data
- **Value Objects**: Immutable objects representing concepts without identity

## Core Domain Entities

### Patient Entity

```python
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID, uuid4

class Patient:
    """Patient entity representing a person receiving psychiatric care."""
    
    def __init__(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        email: str,
        phone: str,
        id: Optional[UUID] = None,
        address: Optional[dict] = None,
        insurance: Optional[dict] = None,
        active: bool = True,
        emergency_contact: Optional[dict] = None
    ):
        self.id = id or uuid4()
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.email = email
        self.phone = phone
        self.address = address
        self.insurance = insurance
        self.active = active
        self.emergency_contact = emergency_contact
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def deactivate(self) -> None:
        self.active = False
        self.updated_at = datetime.utcnow()
    
    def reactivate(self) -> None:
        self.active = True
        self.updated_at = datetime.utcnow()
```

### Appointment Entity

```python
from datetime import datetime
from enum import Enum, auto
from typing import Optional
from uuid import UUID, uuid4

class AppointmentType(Enum):
    INITIAL_CONSULTATION = "initial_consultation"
    FOLLOW_UP = "follow_up"
    MEDICATION_REVIEW = "medication_review"
    THERAPY = "therapy"
    EMERGENCY = "emergency"

class AppointmentStatus(Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Appointment:
    """Appointment entity representing a scheduled meeting between patient and provider."""
    
    def __init__(
        self,
        patient_id: UUID,
        start_time: datetime,
        end_time: datetime,
        appointment_type: AppointmentType,
        id: Optional[UUID] = None,
        status: AppointmentStatus = AppointmentStatus.SCHEDULED,
        notes: Optional[str] = None,
        virtual: bool = False,
        location: Optional[str] = None
    ):
        self.id = id or uuid4()
        self.patient_id = patient_id
        self.start_time = start_time
        self.end_time = end_time
        self.appointment_type = appointment_type
        self.status = status
        self.notes = notes
        self.virtual = virtual
        self.location = location
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
    
    @property
    def duration_minutes(self) -> int:
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def confirm(self) -> None:
        self.status = AppointmentStatus.CONFIRMED
        self.updated_at = datetime.utcnow()
    
    def complete(self) -> None:
        self.status = AppointmentStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        self.status = AppointmentStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def mark_no_show(self) -> None:
        self.status = AppointmentStatus.NO_SHOW
        self.updated_at = datetime.utcnow()
        
    def overlaps_with(self, other: 'Appointment') -> bool:
        """Check if this appointment overlaps with another."""
        return (
            (self.start_time < other.end_time and self.end_time > other.start_time) or
            (other.start_time < self.end_time and other.end_time > self.start_time)
        )
```

### Clinical Note Entity

```python
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

class NoteType(Enum):
    """Types of clinical notes"""
    PROGRESS_NOTE = "progress_note"
    INTAKE_ASSESSMENT = "intake_assessment"
    MEDICATION_NOTE = "medication_note"
    TREATMENT_PLAN = "treatment_plan"
    DISCHARGE_SUMMARY = "discharge_summary"

class ClinicalNote:
    """
    Entity representing a clinical note for a patient.
    Implements versioning for audit compliance.
    """
    def __init__(
        self,
        patient_id: UUID,
        content: str,
        note_type: NoteType,
        author_id: UUID,
        id: UUID = None,
        appointment_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        version: int = 1,
        previous_versions: Optional[List[dict]] = None,
    ):
        self.id = id or uuid4()
        self.patient_id = patient_id
        self.content = content
        self.note_type = note_type
        self.author_id = author_id
        self.appointment_id = appointment_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = self.created_at
        self.version = version
        self.previous_versions = previous_versions or []

    def update_content(self, new_content: str, editor_id: UUID) -> None:
        """
        Update note content, preserving previous version.
        Maintains audit trail required for HIPAA compliance.
        """
        # Store the current version before updating
        previous_version = {
            "content": self.content,
            "version": self.version,
            "updated_at": self.updated_at,
            "editor_id": self.author_id
        }
        self.previous_versions.append(previous_version)

        # Update with new content
        self.content = new_content
        self.version += 1
        self.updated_at = datetime.utcnow()
        self.author_id = editor_id

    def get_version_history(self) -> List[dict]:
        """Get complete version history of this note."""
        history = self.previous_versions.copy()
        # Add current version
        history.append({
            "content": self.content,
            "version": self.version,
            "updated_at": self.updated_at,
            "editor_id": self.author_id
        })
        return sorted(history, key=lambda x: x["version"])
```

### Digital Twin Entity

```python
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4
from dataclasses import dataclass

class ModelType(str, Enum):
    """Types of models in the digital twin system"""
    TIME_SERIES = "time_series"
    BIOMETRIC_CORRELATION = "biometric_correlation"
    PRECISION_MEDICATION = "precision_medication"

class SymptomType(str, Enum):
    """Types of psychiatric symptoms tracked in the system"""
    DEPRESSION = "depression"
    ANXIETY = "anxiety"
    SLEEP_DISTURBANCE = "sleep_disturbance"
    IRRITABILITY = "irritability"
    ANHEDONIA = "anhedonia"
    FATIGUE = "fatigue"
    CONCENTRATION = "concentration"
    SUICIDAL_IDEATION = "suicidal_ideation"
    MOOD_INSTABILITY = "mood_instability"
    PSYCHOSIS = "psychosis"

class BiometricType(str, Enum):
    """Types of biometric data tracked in the system"""
    HEART_RATE = "heart_rate"
    HEART_RATE_VARIABILITY = "heart_rate_variability"
    SLEEP_DURATION = "sleep_duration"
    SLEEP_LATENCY = "sleep_latency"
    SLEEP_EFFICIENCY = "sleep_efficiency"
    DEEP_SLEEP = "deep_sleep"
    REM_SLEEP = "rem_sleep"
    ACTIVITY_LEVEL = "activity_level"
    STEP_COUNT = "step_count"
    BODY_TEMPERATURE = "body_temperature"

class InsightType(str, Enum):
    """Types of clinical insights generated by the system"""
    EARLY_WARNING = "early_warning"
    TREATMENT_RESPONSE = "treatment_response"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    MEDICATION_EFFECT = "medication_effect"
    BIOMETRIC_CORRELATION = "biometric_correlation"
    SLEEP_IMPACT = "sleep_impact"
    ACTIVITY_IMPACT = "activity_impact"
    RISK_ASSESSMENT = "risk_assessment"

@dataclass(frozen=True)
class BiometricCorrelation:
    """
    Value object representing a correlation between a biometric measure and a symptom.
    """
    biometric_type: BiometricType
    symptom_type: SymptomType
    correlation_strength: float  # -1.0 to 1.0
    lag_days: int  # How many days the biometric change precedes the symptom change

@dataclass(frozen=True)
class ClinicalInsight:
    """
    Value object representing a clinical insight derived from the digital twin.
    """
    id: str
    insight_type: InsightType
    description: str
    confidence: float
    generated_at: datetime
    supporting_evidence: List['EvidencePoint']
    relevant_model_ids: List[str]

@dataclass(frozen=True)
class EvidencePoint:
    """
    Value object representing a piece of evidence supporting a clinical insight.
    """
    data_type: str
    timestamp: datetime
    value: Any
    reference_range: Optional[Tuple[float, float]] = None
    deviation_severity: Optional[float] = None

@dataclass(frozen=True)
class PredictionPoint:
    """
    Value object representing a single point in a prediction trajectory.
    """
    date: datetime
    value: float
    confidence_lower: float
    confidence_upper: float

class DigitalTwin:
    """
    Digital Twin entity representing a computational model of a patient's psychiatric state.
    """
    
    def __init__(
        self,
        patient_id: UUID,
        id: Optional[UUID] = None,
        symptom_forecast: Optional[Dict] = None,
        biometric_correlations: Optional[Dict] = None,
        medication_responses: Optional[Dict] = None,
        last_updated: Optional[datetime] = None,
        version: int = 1,
        confidence_score: float = 0.0,
        clinical_insights: Optional[List[ClinicalInsight]] = None,
        last_calibration: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.patient_id = patient_id
        self.symptom_forecast = symptom_forecast or {}
        self.biometric_correlations = biometric_correlations or {}
        self.medication_responses = medication_responses or {}
        self.last_updated = last_updated or datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.version = version
        self.confidence_score = confidence_score
        self.clinical_insights = clinical_insights or []
        self.last_calibration = last_calibration or datetime.utcnow()
    
    def update_symptom_forecast(self, forecast_data: Dict) -> None:
        """Update symptom forecast data and timestamp."""
        self.symptom_forecast = forecast_data
        self.last_updated = datetime.utcnow()
        self.version += 1
    
    def update_biometric_correlations(self, correlation_data: Dict) -> None:
        """Update biometric correlation data and timestamp."""
        self.biometric_correlations = correlation_data
        self.last_updated = datetime.utcnow()
        self.version += 1
    
    def update_medication_responses(self, medication_data: Dict) -> None:
        """Update medication response data and timestamp."""
        self.medication_responses = medication_data
        self.last_updated = datetime.utcnow()
        self.version += 1
    
    def add_clinical_insight(self, insight: ClinicalInsight) -> None:
        """Add a new clinical insight to the digital twin."""
        self.clinical_insights.append(insight)
        self.last_updated = datetime.utcnow()
        self.version += 1
    
    def recalibrate(self, confidence_score: float) -> None:
        """Recalibrate the digital twin with a new confidence score."""
        self.confidence_score = confidence_score
        self.last_calibration = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.version += 1
    
    @property
    def is_stale(self) -> bool:
        """Return True if the digital twin data is older than 7 days."""
        if not self.last_updated:
            return True
        delta = datetime.utcnow() - self.last_updated
        return delta.days > 7
```

### Digital Twin Repository Interface

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.digital_twin import DigitalTwin

class DigitalTwinRepository(ABC):
    """Repository interface for digital twin persistence."""
    
    @abstractmethod
    async def save(self, digital_twin: DigitalTwin) -> None:
        """Save a digital twin."""
        pass
    
    @abstractmethod
    async def get_by_id(self, digital_twin_id: UUID) -> Optional[DigitalTwin]:
        """Get a digital twin by ID."""
        pass
    
    @abstractmethod
    async def get_by_patient_id(self, patient_id: UUID) -> Optional[DigitalTwin]:
        """Get a digital twin by patient ID."""
        pass
    
    @abstractmethod
    async def get_version_history(
        self,
        digital_twin_id: UUID,
        limit: int = 10
    ) -> List[DigitalTwin]:
        """Get version history of a digital twin."""
        pass
```

### Medication Entity

```python
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

class MedicationStatus(Enum):
    """Status of a medication prescription"""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"

class MedicationFrequency(Enum):
    """Frequency of medication administration"""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    AS_NEEDED = "as_needed"
    ONCE_WEEKLY = "once_weekly"
    BEDTIME = "bedtime"
    MORNING = "morning"
    OTHER = "other"

class Medication:
    """
    Entity representing a medication prescribed to a patient.
    """
    def __init__(
        self,
        patient_id: UUID,
        name: str,
        dosage: str,
        frequency: MedicationFrequency,
        prescriber_id: UUID,
        id: UUID = None,
        instructions: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: MedicationStatus = MedicationStatus.ACTIVE,
        reason: Optional[str] = None,
    ):
        self.id = id or uuid4()
        self.patient_id = patient_id
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.prescriber_id = prescriber_id
        self.instructions = instructions
        self.start_date = start_date or datetime.utcnow()
        self.end_date = end_date
        self.status = status
        self.reason = reason

    def discontinue(self, reason: str) -> None:
        """
        Discontinue medication with reason.
        """
        if self.status != MedicationStatus.ACTIVE:
            raise ValueError("Can only discontinue active medications")

        self.status = MedicationStatus.DISCONTINUED
        self.end_date = datetime.utcnow()
        self.reason = reason

    def complete(self) -> None:
        """
        Mark medication as completed (course finished).
        """
        if self.status != MedicationStatus.ACTIVE:
            raise ValueError("Can only complete active medications")

        self.status = MedicationStatus.COMPLETED
        self.end_date = datetime.utcnow()

    def update_dosage(self, new_dosage: str, new_instructions: Optional[str] = None) -> None:
        """
        Update medication dosage and instructions.
        """
        if self.status != MedicationStatus.ACTIVE:
            raise ValueError("Can only update active medications")

        self.dosage = new_dosage
        if new_instructions:
            self.instructions = new_instructions

    def is_active(self) -> bool:
        """
        Check if medication is currently active.
        """
        return self.status == MedicationStatus.ACTIVE
```

## Repository Interfaces

### Base Repository Interface

```python
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

T = TypeVar('T')

class Repository(Generic[T], ABC):
    """Base repository interface for all domain entities."""
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """List entities with pagination."""
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> Optional[T]:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete an entity by ID."""
        pass
```

### Patient Repository Interface

```python
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from app.domain.entities.patient import Patient
from app.domain.repositories.base_repository import Repository

class PatientRepository(Repository[Patient], ABC):
    """Repository interface for Patient entities."""
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Patient]:
        """Find a patient by email address."""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> List[Patient]:
        """Find patients by name (partial match)."""
        pass
    
    @abstractmethod
    async def find_by_date_of_birth(self, dob: date) -> List[Patient]:
        """Find patients by date of birth."""
        pass
    
    @abstractmethod
    async def get_active_patients(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get only active patients."""
        pass
```

### Appointment Repository Interface

```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.repositories.base_repository import Repository

class AppointmentRepository(Repository[Appointment], ABC):
    """Interface for appointment data access"""

    @abstractmethod
    async def get_for_patient(self, patient_id: UUID) -> List[Appointment]:
        """Get all appointments for a patient"""
        pass

    @abstractmethod
    async def get_in_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        status: Optional[List[AppointmentStatus]] = None
    ) -> List[Appointment]:
        """Get appointments in a time range with optional status filter"""
        pass
```

## Domain Services

### Appointment Scheduling Service

```python
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from app.domain.entities.appointment import Appointment, AppointmentStatus, AppointmentType
from app.domain.entities.patient import Patient
from app.domain.exceptions.domain_exceptions import AppointmentConflictException

class AppointmentSchedulingService:
    """Domain service for appointment scheduling logic."""
    
    def validate_appointment_time(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Validate appointment time constraints:
        - Must be in the future
        - Must be during business hours (9 AM - 5 PM)
        - Must be on a weekday
        - Must have valid duration (30, 45, or 60 minutes)
        """
        now = datetime.utcnow()
        
        # Must be in the future
        if start_time <= now:
            return False
        
        # Must be during business hours (9 AM - 5 PM)
        if start_time.hour < 9 or end_time.hour > 17:
            return False
        
        # Must be on a weekday
        if start_time.weekday() > 4:  # 5 = Saturday, 6 = Sunday
            return False
        
        # Calculate duration in minutes
        duration = (end_time - start_time).total_seconds() / 60
        
        # Must have valid duration (30, 45, or 60 minutes)
        if duration not in (30, 45, 60):
            return False
        
        return True
    
    def check_appointment_conflict(
        self,
        proposed_start: datetime,
        proposed_end: datetime,
        existing_appointments: List[Appointment]
    ) -> bool:
        """
        Check if a proposed appointment conflicts with existing appointments.
        Returns True if there is a conflict, False otherwise.
        """
        for appointment in existing_appointments:
            # Skip cancelled appointments
            if appointment.status == AppointmentStatus.CANCELLED:
                continue
                
            # Check for overlap
            if (proposed_start < appointment.end_time and
                proposed_end > appointment.start_time):
                return True
                
        return False
    
    def suggest_available_slots(
        self,
        preferred_date: datetime,
        duration_minutes: int,
        existing_appointments: List[Appointment]
    ) -> List[dict]:
        """
        Suggest available appointment slots on the preferred date.
        """
        available_slots = []
        
        # Start at 9 AM on the preferred date
        current_date = preferred_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # End at 5 PM
        end_of_day = current_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        # Create a timedelta for the appointment duration
        duration = timedelta(minutes=duration_minutes)
        
        # Iterate through the day in 15-minute increments
        while current_date + duration <= end_of_day:
            slot_end = current_date + duration
            
            # Check if this slot conflicts with existing appointments
            if not self.check_appointment_conflict(current_date, slot_end, existing_appointments):
                available_slots.append({
                    "start_time": current_date,
                    "end_time": slot_end
                })
            
            # Move to the next 15-minute increment
            current_date += timedelta(minutes=15)
        
        return available_slots
        
    def schedule_appointment(
        self,
        appointment: Appointment,
        existing_appointments: List[Appointment]
    ) -> Appointment:
        """
        Schedule a new appointment, checking for conflicts.
        
        Args:
            appointment: The appointment to schedule
            existing_appointments: List of existing appointments to check for conflicts
            
        Returns:
            The scheduled appointment
            
        Raises:
            AppointmentConflictException: If appointment conflicts with existing one
        """
        # Validate appointment time
        if not self.validate_appointment_time(appointment.start_time, appointment.end_time):
            raise ValueError("Invalid appointment time")
            
        # Check for conflicts
        for existing in existing_appointments:
            if appointment.overlaps_with(existing):
                raise AppointmentConflictException(
                    appointment.start_time,
                    appointment.end_time
                )
                
        return appointment
```

## Value Objects

### ContactInfo Value Object

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ContactInfo:
    """Immutable value object representing contact information."""
    email: str
    phone: str
```

### Address Value Object

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Address:
    """Immutable value object representing a physical address."""
    street1: str
    street2: Optional[str]
    city: str
    state: str
    zip_code: str
    country: str = "USA"
```

### Insurance Value Object

```python
from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass(frozen=True)
class Insurance:
    """
    Immutable value object representing insurance information.
    """
    provider: str
    policy_number: str
    group_number: Optional[str] = None
    policy_holder: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

    def is_valid(self, check_date: Optional[date] = None) -> bool:
        """
        Check if insurance is valid on the given date.
        Defaults to current date if none provided.
        """
        check_date = check_date or date.today()

        # If no dates are set, assume it's valid
        if not self.valid_from and not self.valid_to:
            return True

        # Check start date if set
        if self.valid_from and check_date < self.valid_from:
            return False

        # Check end date if set
        if self.valid_to and check_date > self.valid_to:
            return False

        return True
```

## Implementation Guidelines

1. **Entity Creation**: Always use factories or constructors to create entities
2. **Value Objects**: Use immutable dataclasses for value objects
3. **Domain Logic**: Keep business rules in domain entities or services
4. **Repository Interfaces**: Define in domain layer, implement in infrastructure
5. **Validation**: Implement domain-specific validation in entities or value objects
6. **Error Handling**: Use domain-specific exceptions for business rule violations

## Domain Exceptions

```python
class DomainException(Exception):
    """Base exception for all domain-specific errors."""
    pass

class EntityNotFoundException(DomainException):
    """Raised when an entity cannot be found by ID."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(self.message)

class ValidationException(DomainException):
    """Raised when entity validation fails."""
    pass

class AppointmentConflictException(DomainException):
    """Raised when there is a scheduling conflict with existing appointments."""
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.message = f"Appointment conflict detected for time slot {start_time} to {end_time}"
        super().__init__(self.message)

class BusinessRuleViolationException(DomainException):
    """Raised when a business rule is violated."""
    pass

class UnauthorizedAccessException(DomainException):
    """Raised when an operation is attempted without proper authorization."""
    def __init__(self, resource_type: str, operation: str):
        self.resource_type = resource_type
        self.operation = operation
        self.message = f"Unauthorized access to {resource_type} for operation {operation}"
        super().__init__(self.message)

class PatientDataAccessException(DomainException):
    """
    Raised when there's an attempt to access patient data without proper authorization.
    This is a critical HIPAA compliance exception.
    """
    def __init__(self, patient_id: str, accessor_id: str):
        self.patient_id = patient_id
        self.accessor_id = accessor_id
        # Note: We don't include actual patient identifiers in the error message
        self.message = f"Unauthorized patient data access attempt by {accessor_id}"
        super().__init__(self.message)
```

## Testing Strategy

Domain layer tests should be pure unit tests, focusing on business rules without dependencies:

```python
# tests/unit/domain/test_patient.py
import pytest
from datetime import date
from uuid import uuid4

from app.domain.entities.patient import Patient
from app.domain.value_objects.contact_info import ContactInfo
from app.domain.value_objects.address import Address


class TestPatient:
    """Tests for Patient entity"""

    def test_patient_creation(self):
        """Test that a patient can be created with valid data"""
        contact = ContactInfo(email="patient@example.com", phone="555-123-4567")
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 15),
            contact_info=contact
        )

        assert patient.first_name == "John"
        assert patient.last_name == "Doe"
        assert patient.date_of_birth == date(1990, 1, 15)
        assert patient.contact_info == contact
        assert patient.active is True
        assert patient.id is not None

    def test_patient_full_name(self):
        """Test full_name property"""
        contact = ContactInfo(email="patient@example.com", phone="555-123-4567")
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 15),
            contact_info=contact
        )

        assert patient.full_name == "John Doe"

    def test_patient_age_calculation(self):
        """Test age calculation logic"""
        contact = ContactInfo(email="patient@example.com", phone="555-123-4567")
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 15),
            contact_info=contact
        )

        # This test needs to account for the current date
        today = date.today()
        expected_age = today.year - 1990 - ((today.month, today.day) < (1, 15))

        assert patient.age == expected_age

    def test_patient_deactivation(self):
        """Test patient deactivation"""
        contact = ContactInfo(email="patient@example.com", phone="555-123-4567")
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 15),
            contact_info=contact
        )

        assert patient.active is True
        patient.deactivate()
        assert patient.active is False
        patient.reactivate()
        assert patient.active is True
```

These tests ensure that the domain entities work correctly and enforce business rules as expected.