# DATA_LAYER

## Overview

The Data Layer implements the persistence mechanisms for the NOVAMIND platform, following Clean Architecture principles to ensure separation of concerns. This layer contains the database configuration, ORM models, and repository implementations.

## Database Configuration

```python
# app/infrastructure/persistence/database.py
import os
from contextlib import contextmanager
from typing import Callable, Iterator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Base class for all ORM models
Base = declarative_base()

# Get database URL from environment variables
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/novamind"
)

# Create engine with connection pooling
engine = create_engine(
    DB_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,
    connect_args={"sslmode": "require"} if "localhost" not in DB_URL else {}
)

# Create session factory
SessionFactory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

@contextmanager
def get_db_session() -> Iterator[Session]:
    """
    Context manager for database sessions.
    Ensures session is properly closed after use.
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

## Base Model

```python
# app/infrastructure/persistence/models/base_model.py
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.persistence.database import Base

class BaseModel(Base):
    """Base model for all database models with common fields."""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

## Entity Models

### Patient Model

```python
# app/infrastructure/persistence/models/patient_model.py
from datetime import date
from sqlalchemy import Boolean, Column, Date, String, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.persistence.models.base_model import BaseModel

class PatientModel(BaseModel):
    """SQLAlchemy model for patient data."""
    
    __tablename__ = "patients"
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String, nullable=False)
    address_dict = Column(JSON, nullable=True)
    insurance_dict = Column(JSON, nullable=True)
    emergency_contact_dict = Column(JSON, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self) -> str:
        return f"<Patient {self.first_name} {self.last_name}>"
```

### Appointment Model

```python
# app/infrastructure/persistence/models/appointment_model.py
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base_model import BaseModel

class AppointmentModel(BaseModel):
    """SQLAlchemy model for appointment data."""
    
    __tablename__ = "appointments"
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    appointment_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="scheduled")
    notes = Column(String, nullable=True)
    virtual = Column(Boolean, nullable=False, default=False)
    location = Column(String, nullable=True)
    
    # Relationships
    patient = relationship("PatientModel", backref="appointments")
    
    def __repr__(self) -> str:
        return f"<Appointment {self.id} - {self.start_time}>"
```

### Digital Twin Model

```python
# app/infrastructure/persistence/models/digital_twin_model.py
from sqlalchemy import Column, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base_model import BaseModel

class DigitalTwinModel(BaseModel):
    """SQLAlchemy model for digital twin data."""
    
    __tablename__ = "digital_twins"
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    symptom_forecast = Column(JSON, nullable=True)
    biometric_correlations = Column(JSON, nullable=True)
    medication_responses = Column(JSON, nullable=True)
    last_updated = Column(DateTime, nullable=False)
    
    # Relationships
    patient = relationship("PatientModel", backref="digital_twin", uselist=False)
    
    def __repr__(self) -> str:
        return f"<DigitalTwin {self.id} - Patient {self.patient_id}>"
```

## Repository Implementations

### Base Repository Implementation

```python
# app/infrastructure/persistence/repositories/base_repository.py
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.persistence.database import Base

T = TypeVar('T', bound=Base)
E = TypeVar('E')  # Domain entity type

class BaseRepository(Generic[T, E]):
    """Base repository implementation for SQLAlchemy models."""
    
    def __init__(self, db_session: Session, model_class: Type[T]):
        self.db_session = db_session
        self.model_class = model_class
    
    async def get_by_id(self, id: UUID) -> Optional[E]:
        """Get entity by ID."""
        model = self.db_session.query(self.model_class).get(id)
        if model is None:
            return None
        return self._to_entity(model)
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[E]:
        """List entities with pagination."""
        models = self.db_session.query(self.model_class).offset(skip).limit(limit).all()
        return [self._to_entity(model) for model in models]
    
    async def add(self, entity: E) -> E:
        """Add a new entity."""
        model = self._to_model(entity)
        self.db_session.add(model)
        self.db_session.commit()
        self.db_session.refresh(model)
        return self._to_entity(model)
    
    async def update(self, entity: E) -> Optional[E]:
        """Update an existing entity."""
        model = self.db_session.query(self.model_class).get(entity.id)
        if model is None:
            return None
            
        # Update model with entity data
        updated_model = self._to_model(entity)
        for key, value in updated_model.__dict__.items():
            if not key.startswith('_'):
                setattr(model, key, value)
        
        self.db_session.commit()
        self.db_session.refresh(model)
        return self._to_entity(model)
    
    async def delete(self, id: UUID) -> bool:
        """Delete an entity by ID."""
        model = self.db_session.query(self.model_class).get(id)
        if model is None:
            return False
            
        self.db_session.delete(model)
        self.db_session.commit()
        return True
    
    def _to_entity(self, model: T) -> E:
        """Convert from ORM model to domain entity."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def _to_model(self, entity: E) -> T:
        """Convert from domain entity to ORM model."""
        raise NotImplementedError("Subclasses must implement this method")
```

### Patient Repository Implementation

```python
# app/infrastructure/persistence/repositories/patient_repository.py
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.entities.patient import Patient
from app.domain.repositories.patient_repository import PatientRepository
from app.infrastructure.persistence.models.patient_model import PatientModel
from app.infrastructure.persistence.repositories.base_repository import BaseRepository

class SQLAlchemyPatientRepository(BaseRepository[PatientModel, Patient], PatientRepository):
    """SQLAlchemy implementation of the PatientRepository interface."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, PatientModel)
    
    async def find_by_email(self, email: str) -> Optional[Patient]:
        """Find a patient by email address."""
        model = self.db_session.query(PatientModel).filter(
            PatientModel.email == email
        ).first()
        
        if model is None:
            return None
            
        return self._to_entity(model)
    
    async def find_by_name(self, name: str) -> List[Patient]:
        """Find patients by name (partial match)."""
        models = self.db_session.query(PatientModel).filter(
            or_(
                PatientModel.first_name.ilike(f"%{name}%"),
                PatientModel.last_name.ilike(f"%{name}%")
            )
        ).all()
        
        return [self._to_entity(model) for model in models]
    
    async def find_by_date_of_birth(self, dob: date) -> List[Patient]:
        """Find patients by date of birth."""
        models = self.db_session.query(PatientModel).filter(
            PatientModel.date_of_birth == dob
        ).all()
        
        return [self._to_entity(model) for model in models]
    
    async def get_active_patients(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get only active patients."""
        models = self.db_session.query(PatientModel).filter(
            PatientModel.active == True
        ).offset(skip).limit(limit).all()
        
        return [self._to_entity(model) for model in models]
    
    def _to_entity(self, model: PatientModel) -> Patient:
        """Convert from ORM model to domain entity."""
        return Patient(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            date_of_birth=model.date_of_birth,
            email=model.email,
            phone=model.phone,
            address=model.address_dict,
            insurance=model.insurance_dict,
            active=model.active,
            emergency_contact=model.emergency_contact_dict
        )
    
    def _to_model(self, entity: Patient) -> PatientModel:
        """Convert from domain entity to ORM model."""
        return PatientModel(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            date_of_birth=entity.date_of_birth,
            email=entity.email,
            phone=entity.phone,
            address_dict=entity.address,
            insurance_dict=entity.insurance,
            emergency_contact_dict=entity.emergency_contact,
            active=entity.active
        )
```

## Data Encryption

```python
# app/infrastructure/persistence/encryption.py
import base64
import os
from typing import Any, Dict, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        # Get encryption key from environment or generate one
        encryption_key = os.getenv("NOVAMIND_ENCRYPTION_KEY")
        
        if encryption_key:
            self.key = base64.urlsafe_b64decode(encryption_key)
        else:
            # Generate a key from password and salt
            password = os.getenv("NOVAMIND_ENCRYPTION_PASSWORD", "").encode()
            salt = os.getenv("NOVAMIND_ENCRYPTION_SALT", "").encode()
            
            if not password or not salt:
                # Generate random values if not provided
                password = os.urandom(32)
                salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Initialize Fernet cipher
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return a base64-encoded string."""
        if isinstance(data, str):
            data = data.encode()
        
        encrypted_data = self.cipher.encrypt(data)
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        """Decrypt base64-encoded encrypted data."""
        if isinstance(encrypted_data, str):
            encrypted_data = base64.urlsafe_b64decode(encrypted_data)
        
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return decrypted_data.decode()
    
    def encrypt_dict(self, data: Dict[str, Any], keys_to_encrypt: list) -> Dict[str, Any]:
        """Encrypt specific keys in a dictionary."""
        result = {}
        
        for key, value in data.items():
            if key in keys_to_encrypt and isinstance(value, (str, bytes)):
                result[key] = self.encrypt(value)
            elif isinstance(value, dict):
                result[key] = self.encrypt_dict(value, keys_to_encrypt)
            else:
                result[key] = value
        
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], keys_to_decrypt: list) -> Dict[str, Any]:
        """Decrypt specific keys in a dictionary."""
        result = {}
        
        for key, value in data.items():
            if key in keys_to_decrypt and isinstance(value, str):
                try:
                    result[key] = self.decrypt(value)
                except Exception:
                    # If decryption fails, assume it wasn't encrypted
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self.decrypt_dict(value, keys_to_decrypt)
            else:
                result[key] = value
        
        return result
```

## Migrations

```python
# alembic/env.py
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.models import *  # Import all models
from app.core.config import settings

# this is the Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Add model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Clinical Note Model

```python
# app/infrastructure/persistence/models/clinical_note_model.py
from sqlalchemy import Column, Text, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base_model import BaseModel

class ClinicalNoteModel(BaseModel):
    """SQLAlchemy model for clinical notes."""
    
    __tablename__ = "clinical_notes"
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True
    )
    
    author_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    note_type = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    previous_versions = Column(JSONB, nullable=True)
    
    # Relationships
    patient = relationship("PatientModel", backref="clinical_notes")
    appointment = relationship("AppointmentModel", backref="clinical_notes")
    
    def __repr__(self) -> str:
        return f"<ClinicalNote {self.id} - {self.note_type}>"
```

## Medication Model

```python
# app/infrastructure/persistence/models/medication_model.py
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base_model import BaseModel

class MedicationModel(BaseModel):
    """SQLAlchemy model for medications."""
    
    __tablename__ = "medications"
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    prescriber_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    instructions = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="active")
    reason = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("PatientModel", backref="medications")
    
    def __repr__(self) -> str:
        return f"<Medication {self.id} - {self.name}>"
```

## Appointment Repository Implementation

```python
# app/infrastructure/persistence/repositories/appointment_repository.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.repositories.appointment_repository import AppointmentRepository
from app.infrastructure.persistence.models.appointment_model import AppointmentModel
from app.infrastructure.persistence.repositories.base_repository import BaseRepository

class SQLAlchemyAppointmentRepository(BaseRepository[AppointmentModel, Appointment], AppointmentRepository):
    """SQLAlchemy implementation of the AppointmentRepository interface."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, AppointmentModel)
    
    async def get_for_patient(self, patient_id: UUID) -> List[Appointment]:
        """Get all appointments for a patient."""
        models = self.db_session.query(AppointmentModel) \
            .filter(AppointmentModel.patient_id == patient_id) \
            .order_by(AppointmentModel.start_time.desc()) \
            .all()
        
        return [self._to_entity(model) for model in models]
    
    async def get_in_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        status: Optional[List[AppointmentStatus]] = None
    ) -> List[Appointment]:
        """Get appointments in a time range with optional status filter."""
        query = self.db_session.query(AppointmentModel).filter(
            or_(
                # Appointment starts during the range
                and_(
                    AppointmentModel.start_time >= start_time,
                    AppointmentModel.start_time < end_time
                ),
                # Appointment ends during the range
                and_(
                    AppointmentModel.end_time > start_time,
                    AppointmentModel.end_time <= end_time
                ),
                # Appointment spans the entire range
                and_(
                    AppointmentModel.start_time <= start_time,
                    AppointmentModel.end_time >= end_time
                )
            )
        )
        
        # Apply status filter if provided
        if status:
            query = query.filter(AppointmentModel.status.in_([s.value for s in status]))
        
        # Order by start time
        query = query.order_by(AppointmentModel.start_time)
        
        # Execute query and convert to domain entities
        models = query.all()
        return [self._to_entity(model) for model in models]
    
    def _to_entity(self, model: AppointmentModel) -> Appointment:
        """Convert from ORM model to domain entity."""
        return Appointment(
            id=model.id,
            patient_id=model.patient_id,
            start_time=model.start_time,
            end_time=model.end_time,
            appointment_type=model.appointment_type,
            status=model.status,
            notes=model.notes,
            virtual=model.virtual,
            location=model.location
        )
    
    def _to_model(self, entity: Appointment) -> AppointmentModel:
        """Convert from domain entity to ORM model."""
        return AppointmentModel(
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

## Clinical Note Repository Implementation

```python
# app/infrastructure/persistence/repositories/clinical_note_repository.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.clinical_note import ClinicalNote, NoteType
from app.domain.repositories.clinical_note_repository import ClinicalNoteRepository
from app.infrastructure.persistence.models.clinical_note_model import ClinicalNoteModel
from app.infrastructure.persistence.repositories.base_repository import BaseRepository

class SQLAlchemyClinicalNoteRepository(BaseRepository[ClinicalNoteModel, ClinicalNote], ClinicalNoteRepository):
    """SQLAlchemy implementation of the ClinicalNoteRepository interface."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, ClinicalNoteModel)
    
    async def get_for_patient(self, patient_id: UUID) -> List[ClinicalNote]:
        """Get all clinical notes for a patient."""
        models = self.db_session.query(ClinicalNoteModel) \
            .filter(ClinicalNoteModel.patient_id == patient_id) \
            .order_by(ClinicalNoteModel.created_at.desc()) \
            .all()
        
        return [self._to_entity(model) for model in models]
    
    async def get_for_appointment(self, appointment_id: UUID) -> List[ClinicalNote]:
        """Get all clinical notes for an appointment."""
        models = self.db_session.query(ClinicalNoteModel) \
            .filter(ClinicalNoteModel.appointment_id == appointment_id) \
            .order_by(ClinicalNoteModel.created_at.desc()) \
            .all()
        
        return [self._to_entity(model) for model in models]
    
    async def get_latest_by_type(self, patient_id: UUID, note_type: NoteType) -> Optional[ClinicalNote]:
        """Get the most recent clinical note of a specific type."""
        model = self.db_session.query(ClinicalNoteModel) \
            .filter(
                ClinicalNoteModel.patient_id == patient_id,
                ClinicalNoteModel.note_type == note_type
            ) \
            .order_by(ClinicalNoteModel.created_at.desc()) \
            .first()
        
        return self._to_entity(model) if model else None
    
    def _to_entity(self, model: ClinicalNoteModel) -> ClinicalNote:
        """Convert from ORM model to domain entity."""
        return ClinicalNote(
            id=model.id,
            patient_id=model.patient_id,
            content=model.content,
            note_type=model.note_type,
            author_id=model.author_id,
            appointment_id=model.appointment_id,
            created_at=model.created_at,
            version=model.version,
            previous_versions=model.previous_versions
        )
    
    def _to_model(self, entity: ClinicalNote) -> ClinicalNoteModel:
        """Convert from domain entity to ORM model."""
        return ClinicalNoteModel(
            id=entity.id,
            patient_id=entity.patient_id,
            appointment_id=entity.appointment_id,
            author_id=entity.author_id,
            content=entity.content,
            note_type=entity.note_type,
            version=entity.version,
            previous_versions=entity.previous_versions
        )
```

## Medication Repository Implementation

```python
# app/infrastructure/persistence/repositories/medication_repository.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.medication import Medication, MedicationStatus
from app.domain.repositories.medication_repository import MedicationRepository
from app.infrastructure.persistence.models.medication_model import MedicationModel
from app.infrastructure.persistence.repositories.base_repository import BaseRepository

class SQLAlchemyMedicationRepository(BaseRepository[MedicationModel, Medication], MedicationRepository):
    """SQLAlchemy implementation of the MedicationRepository interface."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, MedicationModel)
    
    async def get_active_medications(self, patient_id: UUID) -> List[Medication]:
        """Get all active medications for a patient."""
        models = self.db_session.query(MedicationModel) \
            .filter(
                MedicationModel.patient_id == patient_id,
                MedicationModel.status == "active"
            ) \
            .order_by(MedicationModel.name) \
            .all()
        
        return [self._to_entity(model) for model in models]
    
    async def get_medication_history(self, patient_id: UUID) -> List[Medication]:
        """Get full medication history for a patient."""
        models = self.db_session.query(MedicationModel) \
            .filter(MedicationModel.patient_id == patient_id) \
            .order_by(MedicationModel.start_date.desc()) \
            .all()
        
        return [self._to_entity(model) for model in models]
    
    def _to_entity(self, model: MedicationModel) -> Medication:
        """Convert from ORM model to domain entity."""
        return Medication(
            id=model.id,
            patient_id=model.patient_id,
            name=model.name,
            dosage=model.dosage,
            frequency=model.frequency,
            prescriber_id=model.prescriber_id,
            instructions=model.instructions,
            start_date=model.start_date,
            end_date=model.end_date,
            status=model.status,
            reason=model.reason
        )
    
    def _to_model(self, entity: Medication) -> MedicationModel:
        """Convert from domain entity to ORM model."""
        return MedicationModel(
            id=entity.id,
            patient_id=entity.patient_id,
            name=entity.name,
            dosage=entity.dosage,
            frequency=entity.frequency,
            prescriber_id=entity.prescriber_id,
            instructions=entity.instructions,
            start_date=entity.start_date,
            end_date=entity.end_date,
            status=entity.status,
            reason=entity.reason
        )
```

## Transaction Management

```python
# app/infrastructure/persistence/unit_of_work.py
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.patient_repository import SQLAlchemyPatientRepository
from app.infrastructure.persistence.repositories.appointment_repository import SQLAlchemyAppointmentRepository
from app.infrastructure.persistence.repositories.clinical_note_repository import SQLAlchemyClinicalNoteRepository
from app.infrastructure.persistence.repositories.medication_repository import SQLAlchemyMedicationRepository

class UnitOfWork:
    """
    Implements the Unit of Work pattern to manage database transactions.
    Provides a consistent interface to all repositories.
    """
    def __init__(self, session: Session = None):
        self.session = session or SessionFactory()
        
        # Create repositories
        self.patients = SQLAlchemyPatientRepository(self.session)
        self.appointments = SQLAlchemyAppointmentRepository(self.session)
        self.clinical_notes = SQLAlchemyClinicalNoteRepository(self.session)
        self.medications = SQLAlchemyMedicationRepository(self.session)
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()

@contextmanager
def get_unit_of_work() -> Generator[UnitOfWork, None, None]:
    """
    Context manager for UnitOfWork.
    Ensures proper transaction handling with automatic rollback on errors.
    """
    uow = UnitOfWork()
    try:
        yield uow
        uow.commit()
    except Exception:
        uow.rollback()
        raise
    finally:
        uow.close()
```

## Data Access Auditing

```python
# app/infrastructure/persistence/audit.py
import json
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.persistence.models.audit_model import DataAccessAuditModel

class DataAccessAudit:
    """
    Audits all data access operations for HIPAA compliance.
    Records who accessed what data and when.
    """
    @staticmethod
    def record_access(
        db: Session,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a data access event.
        
        Args:
            db: Database session
            user_id: ID of user performing the action
            entity_type: Type of entity being accessed (Patient, Appointment, etc.)
            entity_id: ID of the entity being accessed
            action: Type of access (view, create, update, delete)
            details: Additional details about the access
        """
        audit_record = DataAccessAuditModel(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            timestamp=datetime.utcnow(),
            details=json.dumps(details) if details else None,
            created_by=str(user_id),
            updated_by=str(user_id)
        )
        
        db.add(audit_record)
        db.flush()
```

## Dependency Injection

```python
# app/infrastructure/persistence/container.py
from typing import Callable
from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.persistence.database import get_db_session
from app.infrastructure.persistence.repositories.patient_repository import SQLAlchemyPatientRepository
from app.infrastructure.persistence.repositories.appointment_repository import SQLAlchemyAppointmentRepository
from app.infrastructure.persistence.repositories.clinical_note_repository import SQLAlchemyClinicalNoteRepository
from app.infrastructure.persistence.repositories.medication_repository import SQLAlchemyMedicationRepository
from app.domain.repositories.patient_repository import PatientRepository
from app.domain.repositories.appointment_repository import AppointmentRepository
from app.domain.repositories.clinical_note_repository import ClinicalNoteRepository
from app.domain.repositories.medication_repository import MedicationRepository

def get_patient_repository(session: Session = Depends(get_db_session)) -> PatientRepository:
    """Dependency provider for PatientRepository."""
    return SQLAlchemyPatientRepository(session)

def get_appointment_repository(session: Session = Depends(get_db_session)) -> AppointmentRepository:
    """Dependency provider for AppointmentRepository."""
    return SQLAlchemyAppointmentRepository(session)

def get_clinical_note_repository(session: Session = Depends(get_db_session)) -> ClinicalNoteRepository:
    """Dependency provider for ClinicalNoteRepository."""
    return SQLAlchemyClinicalNoteRepository(session)

def get_medication_repository(session: Session = Depends(get_db_session)) -> MedicationRepository:
    """Dependency provider for MedicationRepository."""
    return SQLAlchemyMedicationRepository(session)
```

## Testing the Data Layer

### Unit Testing Repositories

```python
# tests/unit/infrastructure/persistence/repositories/test_patient_repository.py
import pytest
from datetime import date
from unittest.mock import Mock
from uuid import uuid4

from app.domain.entities.patient import Patient
from app.infrastructure.persistence.repositories.patient_repository import SQLAlchemyPatientRepository

class TestPatientRepository:
    """Unit tests for the SQLAlchemyPatientRepository."""
    
    def test_add_patient(self):
        """Test adding a patient to the repository."""
        # Setup
        mock_session = Mock()
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        
        repository = SQLAlchemyPatientRepository(mock_session)
        
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 15),
            email="john.doe@example.com",
            phone="555-123-4567"
        )
        
        # Exercise
        result = repository.add(patient)
        
        # Verify
        assert mock_session.add.called
        assert mock_session.flush.called
        assert result.first_name == "John"
        assert result.last_name == "Doe"
```

### Integration Testing

```python
# tests/integration/infrastructure/persistence/repositories/test_patient_repository.py
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.repositories.patient_repository import SQLAlchemyPatientRepository
from app.domain.entities.patient import Patient

@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after the test
        Base.metadata.drop_all(bind=engine)

class TestPatientRepositoryIntegration:
    """Integration tests for the SQLAlchemyPatientRepository."""
    
    def test_patient_lifecycle(self, db_session):
        """Test full patient lifecycle: create, read, update, delete."""
        # Setup
        repository = SQLAlchemyPatientRepository(db_session)
        
        # Create
        patient = Patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 15),
            email="john.doe@example.com",
            phone="555-123-4567"
        )
        
        created_patient = repository.add(patient)
        db_session.commit()
        
        # Read
        retrieved_patient = repository.get_by_id(created_patient.id)
        assert retrieved_patient is not None
        assert retrieved_patient.first_name == "John"
        assert retrieved_patient.last_name == "Doe"
        
        # Update
        retrieved_patient.email = "john.updated@example.com"
        updated_patient = repository.update(retrieved_patient)
        db_session.commit()
        
        # Verify update
        fresh_patient = repository.get_by_id(created_patient.id)
        assert fresh_patient.email == "john.updated@example.com"
        
        # Delete
        repository.delete(created_patient.id)
        db_session.commit()
        
        # Verify deletion
        deleted_patient = repository.get_by_id(created_patient.id)
        assert deleted_patient is None
```

## Implementation Guidelines

1. **Repository Pattern**: Always use repositories to access data, never direct ORM queries in application code
2. **Session Management**: Use context managers for database sessions to ensure proper cleanup
3. **Data Encryption**: Encrypt sensitive PHI fields before storing in the database
4. **Audit Trail**: Maintain created_by, updated_by, created_at, and updated_at fields for all records
5. **Migrations**: Use Alembic for database migrations, never modify schema directly
6. **Transactions**: Ensure all related database operations are wrapped in transactions
7. **Error Handling**: Implement proper error handling and rollback for database operations
8. **Type Safety**: Use type hints and generics for repository implementations
9. **Security**: Encrypt sensitive PHI at all times, both in transit and at rest
10. **Audit Logs**: Maintain comprehensive audit logs for all data access operations
11. **Connection Pooling**: Configure appropriate connection pooling for production use
12. **Use Caching Wisely**: When appropriate, implement caching for frequently accessed, non-sensitive data
13. **Repository Isolation**: Repositories should be self-contained and not depend on each other

## Data Integration Architecture

The Data Integration Architecture component provides a secure, flexible framework for connecting diverse mental health data sources while maintaining strict HIPAA compliance and supporting the luxury experience expected by our concierge patients.

### Core Integration Principles

1. **Privacy by Design**: Privacy protections embedded in integration architecture, not added afterward
2. **Minimal Necessary Data**: Only integrating data elements with clear clinical or analytical value
3. **Standardized Interfaces**: Consistent integration patterns across all data sources
4. **Consent-Driven Architecture**: Patient consent management integrated at every connection point
5. **Data Lineage Tracking**: Complete visibility into data provenance and transformation
6. **Security by Default**: End-to-end encryption and strict access controls for all integrations
7. **Clean Separation**: Following Clean Architecture patterns for domain isolation
8. **Luxury Experience**: Integration designed to be invisible to patients while enhancing their care

### Data Source Integration Components

#### Electronic Medical Record (EMR) Integration

Our EMR integration component securely connects with various electronic medical record systems while maintaining strict HIPAA compliance and patient privacy.

**Key Components:**

- Standards-based connectivity (HL7, FHIR)
- Role-based data access restrictions
- Patient consent verification before data exchange
- Configurable field-level privacy controls
- Complete audit logging for all data access events

**Implementation Notes:**

- Utilizes a gateway pattern to abstract EMR-specific details
- Incorporates health data standards for semantic interoperability
- Features connection adapters for major EMR systems
- Supports both pull and push integration models
- Maintains HIPAA-compliant business associate agreements

#### Patient-Generated Health Data Integration

Our patient-generated health data (PGHD) integration framework securely incorporates patient-reported data from various sources, including questionnaires, journaling, and mobile applications.

**Key Components:**

- Standardized questionnaire data models
- Secure journaling content storage
- Mobile application data synchronization
- Passive data collection mechanisms
- Patient-controlled data sharing preferences

**Implementation Notes:**

- Features data validation for patient-generated inputs
- Incorporates secure file storage for media uploads
- Supports both structured and unstructured data
- Implements data quality assessment mechanisms
- Maintains comprehensive privacy controls

#### Wearable Device Integration

Our wearable device integration component enables secure connectivity with personal health devices while maintaining patient privacy and providing contextualized health metrics.

**Key Components:**

- Multi-device connectivity framework
- Real-time and batch data synchronization
- Privacy-preserving data aggregation
- Consent-driven data sharing controls
- Contextual health metric analysis

**Implementation Notes:**

- Supports major fitness and health tracking platforms
- Implements OAuth 2.0 for secure authentication
- Features device-specific data transformation
- Includes data normalization across different sources
- Maintains clear data provenance tracking

### Integration Architecture Patterns

#### Domain-Driven Data Gateway Design

Our integration architecture employs a domain-driven gateway pattern that maintains clean domain boundaries while enabling efficient data flow.

**Key Components:**

- Domain-specific data gateways with clear boundaries
- Repository interfaces abstracting data access
- Rich domain models for integrated data
- Anti-corruption layers preventing domain pollution
- Infrastructure adapters for external systems

#### Event-Driven Integration Approach

Our event-driven integration architecture enables loose coupling between systems while maintaining data consistency and synchronization.

**Key Components:**

- Domain event publication for integration triggers
- Event consumers for data synchronization
- Message-based integration patterns
- Idempotent processing for reliability
- Eventual consistency management

**Implementation Notes:**

- Utilizes asynchronous processing for performance
- Maintains event ordering guarantees when needed
- Implements dead-letter queues for error handling
- Features event sourcing for data lineage
- Includes compensating transactions for rollbacks

#### Secure Adapter Pattern Implementation

Our secure adapter pattern implementation enables standardized connectivity with diverse data sources while maintaining consistent security controls.

**Key Components:**

- Standardized adapter interfaces by data source type
- Security-focused adapter implementation
- Adapter factories for dynamic instantiation
- Monitoring and metrics collection
- Request/response validation middleware

### HIPAA-Compliant Integration Mechanisms

#### De-identification and Tokenization Pipelines

Our de-identification and tokenization pipelines protect sensitive patient data during integration while maintaining analytical utility and clinical relevance.

**Key Components:**

- Field-level tokenization for identifiers
- Contextual de-identification based on data sensitivity
- Re-identification capabilities for authorized access
- Cryptographic token generation and management
- Separation of identifiable and clinical data

**Implementation Notes:**

- Implements HIPAA Safe Harbor and Expert Determination methods
- Features k-anonymity and differential privacy techniques
- Includes privacy impact assessment for integration flows
- Supports tokenization with varying security levels
- Maintains token-to-identifier mapping in secure storage

#### End-to-End Encryption Protocols

Our end-to-end encryption protocols ensure that sensitive patient data remains protected throughout the integration process, from source to destination.

**Key Components:**

- Transport layer security for data in transit
- Field-level encryption for sensitive data elements
- Key management and rotation services
- Encryption protocol version management
- Secure key exchange mechanisms

**Implementation Notes:**

- Utilizes AES-256 encryption for field-level protection
- Implements TLS 1.3 for all network communications
- Features envelope encryption for key management
- Includes perfect forward secrecy for transport security
- Supports hardware security modules for key protection

#### Access Control Integration Points

Our access control integration points ensure that data access during integration processes adheres to the principle of least privilege and is appropriately authorized.

**Key Components:**

- Integration-specific access control policies
- Role-based access control for integration operations
- Purpose-based access limitations
- Attribute-based access control for sensitive data
- Access logging and auditability

**Implementation Notes:**

- Enforces separation of duties for integration tasks
- Features purpose limitation for data access
- Includes context-aware access policies
- Supports temporary access elevation with approval
- Maintains comprehensive access logs for compliance

#### Audit Logging Integration Framework

Our audit logging integration framework ensures comprehensive visibility into all data access and manipulation operations, supporting compliance requirements and security monitoring.

**Key Components:**

- Detailed event logging for all data operations
- Actor-action-resource model for audit events
- Time-synchronized logging infrastructure
- Immutable audit trails with tamper detection
- Contextual metadata capture for each event

**Implementation Notes:**

- Utilizes structured logging with consistent schema
- Features centralized log aggregation and indexing
- Includes query interfaces for compliance reporting
- Supports real-time alerting on suspicious patterns
- Maintains log retention based on compliance requirements

#### Breach Prevention and Detection Mechanisms

Our breach prevention and detection mechanisms provide proactive security controls and real-time monitoring to protect sensitive patient data during integration processes.

**Key Components:**

- Anomaly detection for integration operations
- Behavioral analytics for access patterns
- Rate limiting and throttling mechanisms
- Automated intrusion detection and prevention
- Integration-specific security monitoring

**Implementation Notes:**

- Utilizes machine learning for anomaly detection
- Features baseline profiling for normal behavior
- Includes correlation of security events across systems
- Supports automated incident response workflows
- Maintains comprehensive security metrics