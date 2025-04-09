# APPLICATION_LAYER

## Overview

The Application Layer implements use cases and orchestrates the flow of data between the presentation and domain layers. It contains services that implement business logic, DTOs (Data Transfer Objects) for data transformation, and validators for input validation.

## Use Case Services

### Patient Service

```python
# app/application/services/patient_service.py
from datetime import date
from typing import List, Optional
from uuid import UUID

from app.application.dtos.patient_dto import (
    PatientCreateDTO,
    PatientResponseDTO,
    PatientUpdateDTO
)
from app.domain.entities.patient import Patient
from app.domain.repositories.patient_repository import PatientRepository
from app.infrastructure.persistence.database import get_db_session
from app.core.utils.logging import log_operation
from app.core.exceptions import EntityNotFoundError, ValidationError

class PatientService:
    """Service for patient-related use cases."""
    
    def __init__(self, patient_repository: PatientRepository):
        self.patient_repository = patient_repository
    
    @log_operation("Get patient by ID")
    async def get_patient_by_id(self, patient_id: UUID) -> PatientResponseDTO:
        """Get a patient by ID."""
        patient = await self.patient_repository.get_by_id(patient_id)
        
        if patient is None:
            raise EntityNotFoundError(f"Patient with ID {patient_id} not found")
            
        return PatientResponseDTO.from_entity(patient)
    
    @log_operation("Get patients by name")
    async def get_patients_by_name(self, name: str) -> List[PatientResponseDTO]:
        """Get patients by name (partial match)."""
        if not name or len(name) < 2:
            raise ValidationError("Name search requires at least 2 characters")
            
        patients = await self.patient_repository.find_by_name(name)
        return [PatientResponseDTO.from_entity(patient) for patient in patients]
    
    @log_operation("Create patient")
    async def create_patient(self, patient_data: PatientCreateDTO) -> PatientResponseDTO:
        """Create a new patient."""
        # Check if patient with same email already exists
        existing_patient = await self.patient_repository.find_by_email(patient_data.email)
        
        if existing_patient:
            raise ValidationError(f"Patient with email {patient_data.email} already exists")
        
        # Convert DTO to domain entity
        patient = Patient(
            id=None,  # Will be generated on save
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            date_of_birth=patient_data.date_of_birth,
            email=patient_data.email,
            phone=patient_data.phone,
            address=patient_data.address,
            insurance=patient_data.insurance,
            emergency_contact=patient_data.emergency_contact,
            active=True
        )
        
        # Save patient
        created_patient = await self.patient_repository.add(patient)
        
        return PatientResponseDTO.from_entity(created_patient)
    
    @log_operation("Update patient")
    async def update_patient(
        self, 
        patient_id: UUID, 
        patient_data: PatientUpdateDTO
    ) -> PatientResponseDTO:
        """Update an existing patient."""
        # Get existing patient
        existing_patient = await self.patient_repository.get_by_id(patient_id)
        
        if existing_patient is None:
            raise EntityNotFoundError(f"Patient with ID {patient_id} not found")
        
        # Update fields
        for field, value in patient_data.dict(exclude_unset=True).items():
            setattr(existing_patient, field, value)
        
        # Save updated patient
        updated_patient = await self.patient_repository.update(existing_patient)
        
        return PatientResponseDTO.from_entity(updated_patient)
    
    @log_operation("Deactivate patient")
    async def deactivate_patient(self, patient_id: UUID) -> bool:
        """Deactivate a patient (soft delete)."""
        existing_patient = await self.patient_repository.get_by_id(patient_id)
        
        if existing_patient is None:
            raise EntityNotFoundError(f"Patient with ID {patient_id} not found")
        
        existing_patient.active = False
        await self.patient_repository.update(existing_patient)
        
        return True
    
    @log_operation("Get active patients")
    async def get_active_patients(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[PatientResponseDTO]:
        """Get active patients with pagination."""
        patients = await self.patient_repository.get_active_patients(skip, limit)
        return [PatientResponseDTO.from_entity(patient) for patient in patients]
```

### Appointment Service

```python
# app/application/services/appointment_service.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.application.dtos.appointment_dto import (
    AppointmentCreateDTO,
    AppointmentResponseDTO,
    AppointmentUpdateDTO
)
from app.domain.entities.appointment import Appointment
from app.domain.repositories.appointment_repository import AppointmentRepository
from app.domain.repositories.patient_repository import PatientRepository
from app.core.utils.logging import log_operation
from app.core.exceptions import EntityNotFoundError, ValidationError

class AppointmentService:
    """Service for appointment-related use cases."""
    
    def __init__(
        self, 
        appointment_repository: AppointmentRepository,
        patient_repository: PatientRepository
    ):
        self.appointment_repository = appointment_repository
        self.patient_repository = patient_repository
    
    @log_operation("Get appointment by ID")
    async def get_appointment_by_id(self, appointment_id: UUID) -> AppointmentResponseDTO:
        """Get an appointment by ID."""
        appointment = await self.appointment_repository.get_by_id(appointment_id)
        
        if appointment is None:
            raise EntityNotFoundError(f"Appointment with ID {appointment_id} not found")
            
        return AppointmentResponseDTO.from_entity(appointment)
    
    @log_operation("Get patient appointments")
    async def get_patient_appointments(
        self, 
        patient_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AppointmentResponseDTO]:
        """Get appointments for a specific patient."""
        # Verify patient exists
        patient = await self.patient_repository.get_by_id(patient_id)
        
        if patient is None:
            raise EntityNotFoundError(f"Patient with ID {patient_id} not found")
        
        # Get appointments
        appointments = await self.appointment_repository.find_by_patient_id(
            patient_id, 
            start_date, 
            end_date
        )
        
        return [AppointmentResponseDTO.from_entity(appt) for appt in appointments]
    
    @log_operation("Create appointment")
    async def create_appointment(
        self, 
        appointment_data: AppointmentCreateDTO
    ) -> AppointmentResponseDTO:
        """Create a new appointment."""
        # Verify patient exists
        patient = await self.patient_repository.get_by_id(appointment_data.patient_id)
        
        if patient is None:
            raise EntityNotFoundError(
                f"Patient with ID {appointment_data.patient_id} not found"
            )
        
        # Validate appointment times
        if appointment_data.end_time <= appointment_data.start_time:
            raise ValidationError("End time must be after start time")
        
        # Check for overlapping appointments
        overlapping = await self.appointment_repository.find_overlapping(
            None,  # No appointment ID for new appointments
            appointment_data.start_time,
            appointment_data.end_time
        )
        
        if overlapping:
            raise ValidationError("Appointment overlaps with existing appointments")
        
        # Create appointment entity
        appointment = Appointment(
            id=None,  # Will be generated on save
            patient_id=appointment_data.patient_id,
            start_time=appointment_data.start_time,
            end_time=appointment_data.end_time,
            appointment_type=appointment_data.appointment_type,
            status="scheduled",
            notes=appointment_data.notes,
            virtual=appointment_data.virtual,
            location=appointment_data.location
        )
        
        # Save appointment
        created_appointment = await self.appointment_repository.add(appointment)
        
        return AppointmentResponseDTO.from_entity(created_appointment)
    
    @log_operation("Update appointment")
    async def update_appointment(
        self, 
        appointment_id: UUID, 
        appointment_data: AppointmentUpdateDTO
    ) -> AppointmentResponseDTO:
        """Update an existing appointment."""
        # Get existing appointment
        existing_appointment = await self.appointment_repository.get_by_id(appointment_id)
        
        if existing_appointment is None:
            raise EntityNotFoundError(f"Appointment with ID {appointment_id} not found")
        
        # Check for time changes
        start_time = appointment_data.start_time or existing_appointment.start_time
        end_time = appointment_data.end_time or existing_appointment.end_time
        
        # Validate appointment times
        if end_time <= start_time:
            raise ValidationError("End time must be after start time")
        
        # Check for overlapping appointments if times changed
        if (start_time != existing_appointment.start_time or 
            end_time != existing_appointment.end_time):
            
            overlapping = await self.appointment_repository.find_overlapping(
                appointment_id,  # Exclude current appointment
                start_time,
                end_time
            )
            
            if overlapping:
                raise ValidationError("Appointment overlaps with existing appointments")
        
        # Update fields
        for field, value in appointment_data.dict(exclude_unset=True).items():
            setattr(existing_appointment, field, value)
        
        # Save updated appointment
        updated_appointment = await self.appointment_repository.update(existing_appointment)
        
        return AppointmentResponseDTO.from_entity(updated_appointment)
    
    @log_operation("Cancel appointment")
    async def cancel_appointment(self, appointment_id: UUID) -> bool:
        """Cancel an appointment."""
        existing_appointment = await self.appointment_repository.get_by_id(appointment_id)
        
        if existing_appointment is None:
            raise EntityNotFoundError(f"Appointment with ID {appointment_id} not found")
        
        existing_appointment.status = "cancelled"
        await self.appointment_repository.update(existing_appointment)
        
        return True
```

### Digital Twin Service

```python
# app/application/services/digital_twin_service.py
from typing import Dict, Optional
from uuid import UUID

from app.application.dtos.digital_twin_dto import (
    DigitalTwinResponseDTO,
    DigitalTwinUpdateDTO
)
from app.domain.entities.digital_twin import DigitalTwin
from app.domain.repositories.digital_twin_repository import DigitalTwinRepository
from app.domain.repositories.patient_repository import PatientRepository
from app.domain.services.digital_twin_integration_service import DigitalTwinIntegrationService
from app.core.utils.logging import log_operation
from app.core.exceptions import EntityNotFoundError

class DigitalTwinService:
    """Service for digital twin-related use cases."""
    
    def __init__(
        self, 
        digital_twin_repository: DigitalTwinRepository,
        patient_repository: PatientRepository,
        digital_twin_integration_service: DigitalTwinIntegrationService
    ):
        self.digital_twin_repository = digital_twin_repository
        self.patient_repository = patient_repository
        self.digital_twin_integration_service = digital_twin_integration_service
    
    @log_operation("Get digital twin by patient ID")
    async def get_digital_twin(self, patient_id: UUID) -> DigitalTwinResponseDTO:
        """Get a digital twin by patient ID."""
        # Verify patient exists
        patient = await self.patient_repository.get_by_id(patient_id)
        
        if patient is None:
            raise EntityNotFoundError(f"Patient with ID {patient_id} not found")
        
        # Get digital twin
        digital_twin = await self.digital_twin_repository.find_by_patient_id(patient_id)
        
        if digital_twin is None:
            # Create a new digital twin if it doesn't exist
            digital_twin = await self.create_digital_twin(patient_id)
        
        return DigitalTwinResponseDTO.from_entity(digital_twin)
    
    @log_operation("Create digital twin")
    async def create_digital_twin(self, patient_id: UUID) -> DigitalTwin:
        """Create a new digital twin for a patient."""
        # Verify patient exists
        patient = await self.patient_repository.get_by_id(patient_id)
        
        if patient is None:
            raise EntityNotFoundError(f"Patient with ID {patient_id} not found")
        
        # Check if digital twin already exists
        existing_twin = await self.digital_twin_repository.find_by_patient_id(patient_id)
        
        if existing_twin:
            return existing_twin
        
        # Initialize digital twin with empty data
        digital_twin = DigitalTwin(
            id=None,  # Will be generated on save
            patient_id=patient_id,
            symptom_forecast={},
            biometric_correlations={},
            medication_responses={}
        )
        
        # Save digital twin
        created_twin = await self.digital_twin_repository.add(digital_twin)
        
        return created_twin
    
    @log_operation("Update digital twin")
    async def update_digital_twin(
        self, 
        patient_id: UUID, 
        update_data: DigitalTwinUpdateDTO
    ) -> DigitalTwinResponseDTO:
        """Update a digital twin with new data."""
        # Get existing digital twin
        digital_twin = await self.digital_twin_repository.find_by_patient_id(patient_id)
        
        if digital_twin is None:
            # Create a new digital twin if it doesn't exist
            digital_twin = await self.create_digital_twin(patient_id)
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            current_value = getattr(digital_twin, field, {})
            if isinstance(current_value, dict) and isinstance(value, dict):
                # Merge dictionaries for JSON fields
                current_value.update(value)
                setattr(digital_twin, field, current_value)
            else:
                setattr(digital_twin, field, value)
        
        # Save updated digital twin
        updated_twin = await self.digital_twin_repository.update(digital_twin)
        
        return DigitalTwinResponseDTO.from_entity(updated_twin)
    
    @log_operation("Generate symptom forecast")
    async def generate_symptom_forecast(self, patient_id: UUID) -> Dict:
        """Generate a symptom forecast for a patient."""
        # Verify patient exists
        patient = await self.patient_repository.get_by_id(patient_id)
        
        if patient is None:
            raise EntityNotFoundError(f"Patient with ID {patient_id} not found")
        
        # Get digital twin
        digital_twin = await self.digital_twin_repository.find_by_patient_id(patient_id)
        
        if digital_twin is None:
            # Create a new digital twin if it doesn't exist
            digital_twin = await self.create_digital_twin(patient_id)
        
        # Generate forecast using integration service
        forecast = await self.digital_twin_integration_service.generate_symptom_forecast(patient_id)
        
        # Update digital twin with new forecast
        digital_twin.symptom_forecast = forecast
        await self.digital_twin_repository.update(digital_twin)
        
        return forecast
```

## Data Transfer Objects (DTOs)

### Patient DTOs

```python
# app/application/dtos/patient_dto.py
from datetime import date
from typing import Dict, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator

from app.domain.entities.patient import Patient

class PatientBaseDTO(BaseModel):
    """Base DTO for patient data."""
    
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    address: Optional[Dict] = None
    insurance: Optional[Dict] = None
    emergency_contact: Optional[Dict] = None
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in the future."""
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

class PatientCreateDTO(PatientBaseDTO):
    """DTO for creating a new patient."""
    pass

class PatientUpdateDTO(BaseModel):
    """DTO for updating an existing patient."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[Dict] = None
    insurance: Optional[Dict] = None
    emergency_contact: Optional[Dict] = None
    active: Optional[bool] = None

class PatientResponseDTO(PatientBaseDTO):
    """DTO for patient responses."""
    
    id: UUID
    active: bool
    
    class Config:
        orm_mode = True
    
    @classmethod
    def from_entity(cls, entity: Patient) -> 'PatientResponseDTO':
        """Create DTO from domain entity."""
        return cls(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            date_of_birth=entity.date_of_birth,
            email=entity.email,
            phone=entity.phone,
            address=entity.address,
            insurance=entity.insurance,
            emergency_contact=entity.emergency_contact,
            active=entity.active
        )
```

### Appointment DTOs

```python
# app/application/dtos/appointment_dto.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.domain.entities.appointment import Appointment

class AppointmentBaseDTO(BaseModel):
    """Base DTO for appointment data."""
    
    patient_id: UUID
    start_time: datetime
    end_time: datetime
    appointment_type: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None
    virtual: bool = False
    location: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end time is after start time."""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("End time must be after start time")
        return v

class AppointmentCreateDTO(AppointmentBaseDTO):
    """DTO for creating a new appointment."""
    pass

class AppointmentUpdateDTO(BaseModel):
    """DTO for updating an existing appointment."""
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    appointment_type: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = Field(None, min_length=1, max_length=20)
    notes: Optional[str] = None
    virtual: Optional[bool] = None
    location: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end time is after start time if both are provided."""
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError("End time must be after start time")
        return v

class AppointmentResponseDTO(AppointmentBaseDTO):
    """DTO for appointment responses."""
    
    id: UUID
    status: str
    
    class Config:
        orm_mode = True
    
    @classmethod
    def from_entity(cls, entity: Appointment) -> 'AppointmentResponseDTO':
        """Create DTO from domain entity."""
        return cls(
            id=entity.id,
            patient_id=entity.patient_id,
            start_time=entity.start_time,
            end_time=entity.end_time,
            appointment_type=entity.appointment_type,
            status=entity.status,
            notes=entity.notes,
            virtual=entity.virtual,
            location=entity.location
        )
```

## Dependency Injection

```python
# app/application/dependencies.py
from functools import lru_cache
from typing import Callable, Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.persistence.database import get_db_session
from app.domain.repositories.patient_repository import PatientRepository
from app.domain.repositories.appointment_repository import AppointmentRepository
from app.domain.repositories.digital_twin_repository import DigitalTwinRepository
from app.infrastructure.persistence.repositories.patient_repository import SQLAlchemyPatientRepository
from app.infrastructure.persistence.repositories.appointment_repository import SQLAlchemyAppointmentRepository
from app.infrastructure.persistence.repositories.digital_twin_repository import SQLAlchemyDigitalTwinRepository
from app.domain.services.digital_twin_integration_service import DigitalTwinIntegrationService
from app.infrastructure.services.digital_twin_integration_service import MLDigitalTwinIntegrationService
from app.application.services.patient_service import PatientService
from app.application.services.appointment_service import AppointmentService
from app.application.services.digital_twin_service import DigitalTwinService

# Repositories
def get_patient_repository(db: Session = Depends(get_db_session)) -> PatientRepository:
    """Dependency for PatientRepository."""
    return SQLAlchemyPatientRepository(db)

def get_appointment_repository(db: Session = Depends(get_db_session)) -> AppointmentRepository:
    """Dependency for AppointmentRepository."""
    return SQLAlchemyAppointmentRepository(db)

def get_digital_twin_repository(db: Session = Depends(get_db_session)) -> DigitalTwinRepository:
    """Dependency for DigitalTwinRepository."""
    return SQLAlchemyDigitalTwinRepository(db)

# Domain Services
@lru_cache()
def get_digital_twin_integration_service() -> DigitalTwinIntegrationService:
    """Dependency for DigitalTwinIntegrationService."""
    return MLDigitalTwinIntegrationService()

# Application Services
def get_patient_service(
    patient_repository: PatientRepository = Depends(get_patient_repository)
) -> PatientService:
    """Dependency for PatientService."""
    return PatientService(patient_repository)

def get_appointment_service(
    appointment_repository: AppointmentRepository = Depends(get_appointment_repository),
    patient_repository: PatientRepository = Depends(get_patient_repository)
) -> AppointmentService:
    """Dependency for AppointmentService."""
    return AppointmentService(appointment_repository, patient_repository)

def get_digital_twin_service(
    digital_twin_repository: DigitalTwinRepository = Depends(get_digital_twin_repository),
    patient_repository: PatientRepository = Depends(get_patient_repository),
    digital_twin_integration_service: DigitalTwinIntegrationService = Depends(get_digital_twin_integration_service)
) -> DigitalTwinService:
    """Dependency for DigitalTwinService."""
    return DigitalTwinService(
        digital_twin_repository,
        patient_repository,
        digital_twin_integration_service
    )
```

## Exception Handling

```python
# app/core/exceptions.py
from typing import Any, Dict, List, Optional

class NovamindException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self, 
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(NovamindException):
    """Exception for validation errors."""
    
    def __init__(
        self, 
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=400, details=details)

class EntityNotFoundError(NovamindException):
    """Exception for entity not found errors."""
    
    def __init__(
        self, 
        message: str = "Entity not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=404, details=details)

class AuthenticationError(NovamindException):
    """Exception for authentication errors."""
    
    def __init__(
        self, 
        message: str = "Authentication error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=401, details=details)

class AuthorizationError(NovamindException):
    """Exception for authorization errors."""
    
    def __init__(
        self, 
        message: str = "Authorization error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=403, details=details)
```

## Implementation Guidelines

1. **Use Case Isolation**: Each service should implement a single use case or a group of closely related use cases
2. **Input Validation**: Always validate input data using Pydantic models before processing
3. **Error Handling**: Use custom exceptions for domain-specific errors and handle them appropriately
4. **Dependency Injection**: Use FastAPI's dependency injection system for service dependencies
5. **Logging**: Log all operations with appropriate context and PHI redaction
6. **Transaction Management**: Ensure all database operations are wrapped in transactions
7. **Security**: Implement proper authentication and authorization checks in services
8. **Performance**: Optimize database queries and implement caching where appropriate