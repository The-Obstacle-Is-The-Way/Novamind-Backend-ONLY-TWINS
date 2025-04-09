"""
Patient domain entities for the Novamind Digital Twin platform.
Pure domain models with no external dependencies.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID


class Gender(Enum):
    """Patient gender for clinical relevance."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class DiagnosisStatus(Enum):
    """Status of a clinical diagnosis."""
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    DIFFERENTIAL = "differential"
    RULED_OUT = "ruled_out"
    IN_REMISSION = "in_remission"


class MedicationStatus(Enum):
    """Status of a medication."""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    PLANNED = "planned"
    ON_HOLD = "on_hold"


@dataclass
class Diagnosis:
    """Clinical diagnosis for a patient."""
    id: UUID
    code: str  # ICD-10 or DSM-5 code
    name: str
    status: DiagnosisStatus
    onset_date: Optional[date] = None
    diagnosed_date: date = field(default_factory=date.today)
    notes: Optional[str] = None
    severity: Optional[float] = None  # 0.0 to 1.0 if applicable
    diagnosed_by: Optional[UUID] = None  # Reference to clinician
    
    @property
    def is_active(self) -> bool:
        """Return True if diagnosis is currently active."""
        return self.status in [DiagnosisStatus.CONFIRMED, DiagnosisStatus.PROVISIONAL]


@dataclass
class Medication:
    """Medication prescribed to a patient."""
    id: UUID
    name: str
    dosage: str
    frequency: str
    status: MedicationStatus
    start_date: date
    end_date: Optional[date] = None
    prescriber_id: Optional[UUID] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Return True if medication is currently active."""
        return (
            self.status == MedicationStatus.ACTIVE and
            (self.end_date is None or self.end_date >= date.today())
        )


@dataclass
class PatientPreference:
    """Patient preferences for care and communication."""
    communication_method: str  # e.g., "email", "phone", "text"
    appointment_reminder_time: int  # hours before appointment
    data_sharing_approved: bool = False
    research_participation: bool = False
    theme_preference: str = "default"
    visualization_detail_level: str = "standard"  # "minimal", "standard", "detailed"


@dataclass
class Patient:
    """
    Patient entity representing an individual receiving care.
    Core domain entity that contains PHI and must be handled with HIPAA compliance.
    """
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    diagnoses: List[Diagnosis] = field(default_factory=list)
    medications: List[Medication] = field(default_factory=list)
    preferences: Optional[PatientPreference] = None
    primary_provider_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def full_name(self) -> str:
        """Return patient's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        """Calculate patient's age from date of birth."""
        today = date.today()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    
    @property
    def active_diagnoses(self) -> List[Diagnosis]:
        """Return list of active diagnoses."""
        return [d for d in self.diagnoses if d.is_active]
    
    @property
    def active_medications(self) -> List[Medication]:
        """Return list of active medications."""
        return [m for m in self.medications if m.is_active]
