# Novamind Digital Twin Platform: Implementation Examples

## Overview

This document provides concrete implementation examples for key components in the refactored architecture. These examples demonstrate the coding patterns, architectural principles, and best practices that should be followed throughout the implementation.

## Core Domain Entities

### DigitalTwinSubject Implementation

```python
"""
Digital Twin Subject domain entity.

This entity represents the core identity abstraction for the Digital Twin platform,
completely replacing patient/EHR dependencies with a clean domain model.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


@dataclass
class DigitalTwinSubject:
    """
    Digital Twin Subject representation.
    
    Core domain entity that abstracts identity concerns from direct PHI,
    while maintaining the necessary context for Digital Twin functionality.
    """
    subject_id: UUID
    identity_type: str  # "research", "clinical", "anonymous"
    demographic_factors: Dict[str, Any]  # Age, sex, etc. without direct PHI
    clinical_factors: Dict[str, Any]  # Diagnostic codes, medication classes, etc.
    creation_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    external_references: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def create_research_subject(
        cls,
        age: Optional[int] = None,
        sex: Optional[str] = None,
        diagnostic_codes: Optional[List[str]] = None,
        medication_classes: Optional[List[str]] = None,
        **kwargs
    ) -> "DigitalTwinSubject":
        """
        Create a new research subject with standardized factors.
        
        Args:
            age: Subject age
            sex: Subject biological sex
            diagnostic_codes: List of diagnostic codes (e.g., ICD-10, DSM-5)
            medication_classes: List of medication classes
            **kwargs: Additional attributes to store in metadata
            
        Returns:
            New DigitalTwinSubject instance
        """
        # Construct normalized demographic factors
        demographic_factors = {}
        if age is not None:
            demographic_factors["age"] = age
        if sex is not None:
            demographic_factors["sex"] = sex
            
        # Construct normalized clinical factors
        clinical_factors = {}
        if diagnostic_codes:
            clinical_factors["diagnostic_codes"] = diagnostic_codes
        if medication_classes:
            clinical_factors["medication_classes"] = medication_classes
            
        # Extract any additional metadata
        metadata = {k: v for k, v in kwargs.items() if k not in [
            "age", "sex", "diagnostic_codes", "medication_classes"
        ]}
        
        return cls(
            subject_id=uuid4(),
            identity_type="research",
            demographic_factors=demographic_factors,
            clinical_factors=clinical_factors,
            metadata=metadata
        )
    
    @classmethod
    def create_anonymous_subject(
        cls,
        **kwargs
    ) -> "DigitalTwinSubject":
        """
        Create a new anonymous subject with minimal information.
        
        Args:
            **kwargs: Attributes to store in metadata
            
        Returns:
            New DigitalTwinSubject instance
        """
        return cls(
            subject_id=uuid4(),
            identity_type="anonymous",
            demographic_factors={},
            clinical_factors={},
            metadata=kwargs
        )
    
    @property
    def age(self) -> Optional[int]:
        """Get subject age if available."""
        return self.demographic_factors.get("age")
    
    @property
    def sex(self) -> Optional[str]:
        """Get subject biological sex if available."""
        return self.demographic_factors.get("sex")
    
    @property
    def diagnostic_codes(self) -> List[str]:
        """Get diagnostic codes if available."""
        return self.clinical_factors.get("diagnostic_codes", [])
    
    @property
    def medication_classes(self) -> List[str]:
        """Get medication classes if available."""
        return self.clinical_factors.get("medication_classes", [])
    
    def add_clinical_factor(self, key: str, value: Any) -> None:
        """
        Add a clinical factor to the subject.
        
        Args:
            key: Factor name
            value: Factor value
        """
        self.clinical_factors[key] = value
        self.last_updated = datetime.now(timezone.utc)
    
    def update_demographic_factor(self, key: str, value: Any) -> None:
        """
        Update a demographic factor for the subject.
        
        Args:
            key: Factor name
            value: Factor value
        """
        self.demographic_factors[key] = value
        self.last_updated = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the subject
        """
        return {
            "subject_id": str(self.subject_id),
            "identity_type": self.identity_type,
            "demographic_factors": self.demographic_factors,
            "clinical_factors": self.clinical_factors,
            "creation_date": self.creation_date.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
            "external_references": self.external_references
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DigitalTwinSubject":
        """
        Create from dictionary representation.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Reconstructed DigitalTwinSubject instance
        """
        # Convert string ID to UUID
        subject_id = UUID(data["subject_id"])
        
        # Parse datetime strings
        creation_date = datetime.fromisoformat(data["creation_date"])
        last_updated = datetime.fromisoformat(data["last_updated"])
        
        return cls(
            subject_id=subject_id,
            identity_type=data["identity_type"],
            demographic_factors=data["demographic_factors"],
            clinical_factors=data["clinical_factors"],
            creation_date=creation_date,
            last_updated=last_updated,
            metadata=data.get("metadata", {}),
            external_references=data.get("external_references", {})
        )
```

### DigitalTwin with Subject Identity Reference

```python
"""
Digital Twin domain entity.

Core model representing the complete psychiatric digital twin state,
using the clean DigitalTwinSubject abstraction.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union
from uuid import UUID


class BrainRegion(Enum):
    """Brain regions of interest for the Digital Twin."""
    PREFRONTAL_CORTEX = "prefrontal_cortex"
    ANTERIOR_CINGULATE = "anterior_cingulate"
    AMYGDALA = "amygdala"
    HIPPOCAMPUS = "hippocampus"
    NUCLEUS_ACCUMBENS = "nucleus_accumbens"
    VENTRAL_TEGMENTAL = "ventral_tegmental"
    HYPOTHALAMUS = "hypothalamus"
    INSULA = "insula"
    ORBITOFRONTAL_CORTEX = "orbitofrontal_cortex"
    DORSOLATERAL_PREFRONTAL = "dorsolateral_prefrontal"


class Neurotransmitter(Enum):
    """Key neurotransmitters tracked in the Digital Twin."""
    SEROTONIN = "serotonin"
    DOPAMINE = "dopamine"
    NOREPINEPHRINE = "norepinephrine"
    GABA = "gaba"
    GLUTAMATE = "glutamate"


class ClinicalSignificance(Enum):
    """Clinical significance levels for insights and changes."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BrainRegionState:
    """State of a specific brain region in the Digital Twin."""
    region: BrainRegion
    activation_level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    related_symptoms: List[str] = field(default_factory=list)
    clinical_significance: ClinicalSignificance = ClinicalSignificance.NONE


@dataclass
class NeurotransmitterState:
    """State of a specific neurotransmitter in the Digital Twin."""
    neurotransmitter: Neurotransmitter
    level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    clinical_significance: ClinicalSignificance = ClinicalSignificance.NONE


@dataclass
class NeuralConnection:
    """Connection between brain regions in the Digital Twin."""
    source_region: BrainRegion
    target_region: BrainRegion
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0


@dataclass
class ClinicalInsight:
    """Clinical insight derived from Digital Twin analysis."""
    id: UUID
    title: str
    description: str
    source: str  # e.g., "PAT", "MentalLLaMA", "XGBoost"
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    clinical_significance: ClinicalSignificance
    brain_regions: List[BrainRegion] = field(default_factory=list)
    neurotransmitters: List[Neurotransmitter] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class TemporalPattern:
    """Temporal pattern detected in subject data."""
    pattern_type: str  # e.g., "circadian", "weekly", "seasonal" 
    description: str
    confidence: float
    strength: float
    clinical_significance: ClinicalSignificance


@dataclass
class DigitalTwin:
    """
    Comprehensive state of the Digital Twin for a subject.
    Core domain entity that represents the complete mental health model.
    """
    subject_id: UUID  # Reference to DigitalTwinSubject, not patient_id
    timestamp: datetime
    brain_regions: Dict[BrainRegion, BrainRegionState] = field(default_factory=dict)
    neurotransmitters: Dict[Neurotransmitter, NeurotransmitterState] = field(default_factory=dict)
    neural_connections: List[NeuralConnection] = field(default_factory=list)
    clinical_insights: List[ClinicalInsight] = field(default_factory=list)
    temporal_patterns: List[TemporalPattern] = field(default_factory=list)
    update_source: Optional[str] = None
    version: int = 1
    
    @property
    def significant_regions(self) -> List[BrainRegionState]:
        """Return brain regions with clinical significance above NONE."""
        return [
            region for region in self.brain_regions.values()
            if region.clinical_significance != ClinicalSignificance.NONE
        ]
    
    @property
    def critical_insights(self) -> List[ClinicalInsight]:
        """Return insights with HIGH or CRITICAL significance."""
        return [
            insight for insight in self.clinical_insights
            if insight.clinical_significance in [
                ClinicalSignificance.HIGH, ClinicalSignificance.CRITICAL
            ]
        ]
    
    def generate_fingerprint(self) -> str:
        """Generate a unique fingerprint for this state for verification."""
        # Implementation creates a hash based on key properties
        return f"{self.subject_id}:{self.timestamp}:{self.version}"
```

## Repository Interfaces and Implementations

### DigitalTwinSubjectRepository

```python
"""
Repository interfaces for Digital Twin Subject domain entity.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.domain.entities.digital_twin.digital_twin_subject import DigitalTwinSubject


class DigitalTwinSubjectRepository(ABC):
    """
    Repository interface for Digital Twin Subject persistence.
    
    This abstract class defines the contract for storing and retrieving
    subject identities independent of the underlying storage mechanism.
    """
    
    @abstractmethod
    async def save(self, subject: DigitalTwinSubject) -> UUID:
        """
        Save a subject identity.
        
        Args:
            subject: The subject to save
            
        Returns:
            The subject's UUID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, subject_id: UUID) -> Optional[DigitalTwinSubject]:
        """
        Retrieve a subject by its ID.
        
        Args:
            subject_id: UUID of the subject
            
        Returns:
            Subject if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_by_type(self, identity_type: str) -> List[DigitalTwinSubject]:
        """
        List all subjects of a specific type.
        
        Args:
            identity_type: Type of subjects to list
            
        Returns:
            List of subjects
        """
        pass
    
    @abstractmethod
    async def get_by_external_reference(self, system: str, identifier: str) -> Optional[DigitalTwinSubject]:
        """
        Retrieve a subject by external reference.
        
        Args:
            system: External system name
            identifier: External identifier
            
        Returns:
            Subject if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, subject_id: UUID) -> bool:
        """
        Delete a subject.
        
        Args:
            subject_id: UUID of the subject to delete
            
        Returns:
            True if deletion was successful
        """
        pass
```

### PostgreSQL Implementation

```python
"""
PostgreSQL implementation of the Digital Twin Subject repository.
"""
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID
import json

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.digital_twin.digital_twin_subject import DigitalTwinSubject
from app.domain.repositories.digital_twin_subject_repository import DigitalTwinSubjectRepository
from app.infrastructure.database.models import DigitalTwinSubjectModel


class PostgreSQLDigitalTwinSubjectRepository(DigitalTwinSubjectRepository):
    """PostgreSQL implementation of the DigitalTwinSubject repository."""
    
    def __init__(self, session_factory: Callable[..., AsyncSession]):
        """
        Initialize the repository.
        
        Args:
            session_factory: Factory function for creating database sessions
        """
        self.session_factory = session_factory
    
    async def save(self, subject: DigitalTwinSubject) -> UUID:
        """
        Save a subject to PostgreSQL.
        
        Args:
            subject: The subject to save
            
        Returns:
            The subject's UUID
        """
        async with self.session_factory() as session:
            # Check if subject already exists
            stmt = select(DigitalTwinSubjectModel).where(
                DigitalTwinSubjectModel.subject_id == str(subject.subject_id)
            )
            result = await session.execute(stmt)
            db_subject = result.scalar_one_or_none()
            
            if db_subject:
                # Update existing subject
                db_subject.identity_type = subject.identity_type
                db_subject.demographic_factors = json.dumps(subject.demographic_factors)
                db_subject.clinical_factors = json.dumps(subject.clinical_factors)
                db_subject.last_updated = subject.last_updated
                db_subject.metadata = json.dumps(subject.metadata)
                db_subject.external_references = json.dumps(subject.external_references)
            else:
                # Create new subject
                db_subject = DigitalTwinSubjectModel(
                    subject_id=str(subject.subject_id),
                    identity_type=subject.identity_type,
                    demographic_factors=json.dumps(subject.demographic_factors),
                    clinical_factors=json.dumps(subject.clinical_factors),
                    creation_date=subject.creation_date,
                    last_updated=subject.last_updated,
                    metadata=json.dumps(subject.metadata),
                    external_references=json.dumps(subject.external_references)
                )
                session.add(db_subject)
            
            await session.commit()
            return subject.subject_id
    
    async def get_by_id(self, subject_id: UUID) -> Optional[DigitalTwinSubject]:
        """
        Retrieve a subject by ID from PostgreSQL.
        
        Args:
            subject_id: UUID of the subject
            
        Returns:
            Subject if found, None otherwise
        """
        async with self.session_factory() as session:
            stmt = select(DigitalTwinSubjectModel).where(
                DigitalTwinSubjectModel.subject_id == str(subject_id)
            )
            result = await session.execute(stmt)
            db_subject = result.scalar_one_or_none()
            
            if not db_subject:
                return None
            
            return DigitalTwinSubject(
                subject_id=UUID(db_subject.subject_id),
                identity_type=db_subject.identity_type,
                demographic_factors=json.loads(db_subject.demographic_factors),
                clinical_factors=json.loads(db_subject.clinical_factors),
                creation_date=db_subject.creation_date,
                last_updated=db_subject.last_updated,
                metadata=json.loads(db_subject.metadata),
                external_references=json.loads(db_subject.external_references)
            )
    
    # Other method implementations...
```

## Application Service Implementation

### DigitalTwinService

```python
"""
Application service for Digital Twin operations.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

from app.domain.entities.digital_twin.digital_twin import (
    DigitalTwin, BrainRegion, Neurotransmitter, ClinicalSignificance,
    BrainRegionState, NeurotransmitterState, ClinicalInsight
)
from app.domain.entities.digital_twin.digital_twin_subject import DigitalTwinSubject
from app.domain.repositories.digital_twin_repository import DigitalTwinRepository
from app.domain.repositories.digital_twin_subject_repository import DigitalTwinSubjectRepository
from app.core.audit.audit_service import AuditService, AuditEvent, AuditEventType
from app.core.exceptions import ResourceNotFoundError, ValidationError


class DigitalTwinService:
    """
    Application service for Digital Twin operations.
    
    This service coordinates domain logic for creating, updating, and analyzing
    digital twins, using the DigitalTwinSubject abstraction throughout.
    """
    
    def __init__(
        self,
        subject_repository: DigitalTwinSubjectRepository,
        twin_repository: DigitalTwinRepository,
        audit_service: Optional[AuditService] = None
    ):
        """
        Initialize the service with required dependencies.
        
        Args:
            subject_repository: Repository for subject access
            twin_repository: Repository for digital twin access
            audit_service: Optional audit service for secure logging
        """
        self.subject_repository = subject_repository
        self.twin_repository = twin_repository
        self.audit_service = audit_service
    
    async def create_digital_twin(
        self,
        subject_id: UUID,
        initial_brain_regions: Optional[Dict[BrainRegion, Dict[str, Any]]] = None,
        initial_neurotransmitters: Optional[Dict[Neurotransmitter, Dict[str, Any]]] = None
    ) -> UUID:
        """
        Create a new digital twin for a subject.
        
        Args:
            subject_id: UUID of the subject identity
            initial_brain_regions: Optional initial brain region states
            initial_neurotransmitters: Optional initial neurotransmitter states
            
        Returns:
            UUID of the created digital twin
            
        Raises:
            ResourceNotFoundError: If subject doesn't exist
        """
        # Verify subject exists
        subject = await self.subject_repository.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with ID {subject_id} not found")
        
        # Create brain region states if provided
        brain_regions = {}
        if initial_brain_regions:
            for region, state_data in initial_brain_regions.items():
                brain_regions[region] = BrainRegionState(
                    region=region,
                    activation_level=state_data.get("activation_level", 0.5),
                    confidence=state_data.get("confidence", 0.5),
                    related_symptoms=state_data.get("related_symptoms", []),
                    clinical_significance=state_data.get(
                        "clinical_significance", ClinicalSignificance.NONE
                    )
                )
        
        # Create neurotransmitter states if provided
        neurotransmitters = {}
        if initial_neurotransmitters:
            for nt, state_data in initial_neurotransmitters.items():
                neurotransmitters[nt] = NeurotransmitterState(
                    neurotransmitter=nt,
                    level=state_data.get("level", 0.5),
                    confidence=state_data.get("confidence", 0.5),
                    clinical_significance=state_data.get(
                        "clinical_significance", ClinicalSignificance.NONE
                    )
                )
        
        # Create the digital twin
        digital_twin = DigitalTwin(
            subject_id=subject_id,
            timestamp=datetime.now(timezone.utc),
            brain_regions=brain_regions,
            neurotransmitters=neurotransmitters,
            update_source="initialization"
        )
        
        # Save the digital twin
        twin_id = await self.twin_repository.save(digital_twin)
        
        # Record audit event if audit service is available
        if self.audit_service:
            await self.audit_service.log_event(
                AuditEvent(
                    event_type=AuditEventType.CREATION,
                    resource_id=str(twin_id),
                    resource_type="DigitalTwin",
                    subject_id=str(subject_id),
                    details={
                        "initial_brain_regions": len(brain_regions),
                        "initial_neurotransmitters": len(neurotransmitters)
                    }
                )
            )
        
        return twin_id
    
    # Other method implementations...
```

## API Implementation

### Request and Response Models

```python
"""
API models for Digital Twin Subject endpoints.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SubjectCreate(BaseModel):
    """Request model for creating a new Digital Twin Subject."""
    identity_type: str = Field(..., description="Type of subject (research, clinical, anonymous)")
    demographic_factors: Dict[str, Any] = Field(default_factory=dict, description="Demographic factors")
    clinical_factors: Dict[str, Any] = Field(default_factory=dict, description="Clinical factors")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator("identity_type")
    def validate_identity_type(cls, v):
        """Validate identity type."""
        allowed_types = ["research", "clinical", "anonymous"]
        if v not in allowed_types:
            raise ValueError(f"Identity type must be one of: {', '.join(allowed_types)}")
        return v


class SubjectResponse(BaseModel):
    """Response model for Digital Twin Subject operations."""
    subject_id: UUID
    identity_type: str
    demographic_factors: Dict[str, Any]
    clinical_factors: Dict[str, Any]
    creation_date: datetime
    last_updated: datetime
    metadata: Dict[str, Any]
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "subject_id": "123e4567-e89b-12d3-a456-426614174000",
                "identity_type": "research",
                "demographic_factors": {
                    "age": 35,
                    "sex": "female"
                },
                "clinical_factors": {
                    "diagnostic_codes": ["F32.1", "F41.1"],
                    "medication_classes": ["SSRI"]
                },
                "creation_date": "2025-03-15T12:00:00Z",
                "last_updated": "2025-03-15T12:00:00Z",
                "metadata": {
                    "research_study_id": "STUDY-2025-001",
                    "enrollment_date": "2025-03-01"
                }
            }
        }
```

### API Routes

```python
"""
API routes for Digital Twin Subject operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.api.dependencies import get_subject_service, get_current_user
from app.api.models.digital_twin_subject import SubjectCreate, SubjectResponse
from app.application.services.digital_twin_subject_service import DigitalTwinSubjectService
from app.core.exceptions import ResourceNotFoundError
from app.domain.entities.user import User


router = APIRouter(prefix="/api/v1/digital-twin-subjects", tags=["Digital Twin Subjects"])


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    subject_service: DigitalTwinSubjectService = Depends(get_subject_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new digital twin subject.
    
    This endpoint creates a new subject entity that can be used as the
    foundation for digital twin models.
    """
    # Create the subject
    subject_id = await subject_service.create_subject(
        identity_type=subject_data.identity_type,
        demographic_factors=subject_data.demographic_factors,
        clinical_factors=subject_data.clinical_factors,
        metadata=subject_data.metadata
    )
    
    # Retrieve the created subject
    subject = await subject_service.get_subject(subject_id)
    
    return SubjectResponse(
        subject_id=subject.subject_id,
        identity_type=subject.identity_type,
        demographic_factors=subject.demographic_factors,
        clinical_factors=subject.clinical_factors,
        creation_date=subject.creation_date,
        last_updated=subject.last_updated,
        metadata=subject.metadata
    )


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: UUID,
    subject_service: DigitalTwinSubjectService = Depends(get_subject_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get a digital twin subject by ID.
    
    This endpoint retrieves a specific subject entity by its UUID.
    """
    try:
        subject = await subject_service.get_subject(subject_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
        
    return SubjectResponse(
        subject_id=subject.subject_id,
        identity_type=subject.identity_type,
        demographic_factors=subject.demographic_factors,
        clinical_factors=subject.clinical_factors,
        creation_date=subject.creation_date,
        last_updated=subject.last_updated,
        metadata=subject.metadata
    )


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: UUID,
    subject_data: SubjectCreate,
    subject_service: DigitalTwinSubjectService = Depends(get_subject_service),
    current_user: User = Depends(get_current_user)
):
    """
    Update a digital twin subject.
    
    This endpoint updates an existing subject entity with new data.
    """
    try:
        updated_subject = await subject_service.update_subject(
            subject_id=subject_id,
            identity_type=subject_data.identity_type,
            demographic_factors=subject_data.demographic_factors,
            clinical_factors=subject_data.clinical_factors,
            metadata=subject_data.metadata
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
        
    return SubjectResponse(
        subject_id=updated_subject.subject_id,
        identity_type=updated_subject.identity_type,
        demographic_factors=updated_subject.demographic_factors,
        clinical_factors=updated_subject.clinical_factors,
        creation_date=updated_subject.creation_date,
        last_updated=updated_subject.last_updated,
        metadata=updated_subject.metadata
    )


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: UUID,
    subject_service: DigitalTwinSubjectService = Depends(get_subject_service),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a digital twin subject.
    
    This endpoint deletes a subject entity by its UUID.
    """
    try:
        success = await subject_service.delete_subject(subject_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete subject"
            )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
```

## Unit Test Examples

### DigitalTwinSubject Tests

```python
"""
Unit tests for the Digital Twin Subject entity.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.entities.digital_twin.digital_twin_subject import DigitalTwinSubject


class TestDigitalTwinSubject:
    """Test suite for the DigitalTwinSubject entity."""
    
    def test_create_research_subject(self):
        """Test creating a research subject with factory method."""
        # Act
        subject = DigitalTwinSubject.create_research_subject(
            age=35,
            sex="female",
            diagnostic_codes=["F32.1", "F41.1"],
            medication_classes=["SSRI"]
        )
        
        # Assert
        assert subject.identity_type == "research"
        assert subject.age == 35
        assert subject.sex == "female"
        assert "F32.1" in subject.diagnostic_codes
        assert "SSRI" in subject.medication_classes
    
    def test_create_anonymous_subject(self):
        """Test creating an anonymous subject with factory method."""
        # Act
        subject = DigitalTwinSubject.create_anonymous_subject(
            study_group="control"
        )
        
        # Assert
        assert subject.identity_type == "anonymous"
        assert not subject.demographic_factors
        assert not subject.clinical_factors
        assert subject.metadata.get("study_group") == "control"
    
    def test_serialization_roundtrip(self):
        """Test serialization and deserialization."""
        # Arrange
        original = DigitalTwinSubject.create_research_subject(
            age=42,
            sex="male",
            diagnostic_codes=["F32.1"],
            medication_classes=["SSRI", "Anxiolytic"]
        )
        
        # Act
        data = original.to_dict()
        reconstructed = DigitalTwinSubject.from_dict(data)
        
        # Assert
        assert reconstructed.subject_id == original.subject_id
        assert reconstructed.identity_type == original.identity_type
        assert reconstructed.age == original.age
        assert reconstructed.sex == original.sex
        assert reconstructed.diagnostic_codes == original.diagnostic_codes
        assert reconstructed.medication_classes == original.medication_classes
    
    def test_demographic_factor_update(self):
        """Test updating demographic factors."""
        # Arrange
        subject = DigitalTwinSubject.create_research_subject(age=35)
        original_updated = subject.last_updated
        
        # Act
        subject.update_demographic_factor("sex", "male")
        
        # Assert
        assert subject.sex == "male"
        assert subject.last_updated > original_updated
    
    def test_clinical_factor_addition(self):
        """Test adding clinical factors."""
        # Arrange
        subject = DigitalTwinSubject.create_research_subject()
        original_updated = subject.last_updated
        
        # Act
        subject.add_clinical_factor("symptom_severity", 0.7)
        
        # Assert
        assert subject.clinical_factors.get("symptom_severity") == 0.7
        assert subject.last_updated > original_updated
```

### Repository Tests

```python
"""
Integration tests for the PostgreSQL Digital Twin Subject repository.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.entities.digital_twin.digital_twin_subject import DigitalTwinSubject
from app.infrastructure.repositories.postgresql_digital_twin_subject_repository import (
    PostgreSQLDigitalTwinSubjectRepository
)


@pytest.mark.asyncio
class TestPostgreSQLDigitalTwinSubjectRepository:
    """Test suite for the PostgreSQL repository implementation."""
    
    async def test_save_and_retrieve_subject(self, db_session_factory):
        """Test saving and retrieving a subject."""
        # Arrange
        repository = PostgreSQLDigitalTwinSubjectRepository(db_session_factory)
        subject = DigitalTwinSubject.create_research_subject(
            age=35,
            sex="female",
            diagnostic_codes=["F32.1"]
        )
        
        # Act
        await repository.save(subject)
        retrieved = await repository.get_by_id(subject.subject_id)
        
        # Assert
        assert retrieved is not None
        assert retrieved.subject_id == subject.subject_id
        assert retrieved.age == subject.age
        assert retrieved.sex == subject.sex
        assert retrieved.diagnostic_codes == subject.diagnostic_codes
    
    async def test_update_subject(self, db_session_factory):
        """Test updating an existing subject."""
        # Arrange
        repository = PostgreSQLDigitalTwinSubjectRepository(db_session_factory)
        subject = DigitalTwinSubject.create_research_subject(
            age=35,
            sex="female"
        )
        await repository.save(subject)
        
        # Act
        subject.update_demographic_factor("age", 36)
        subject.add_clinical_factor("new_diagnosis", "F41.1")
        await repository.save(subject)
        updated = await repository.get_by_id(subject.subject_id)
        
        # Assert
        assert updated.age == 36
        assert updated.clinical_factors.get("new_diagnosis") == "F41.1"
    
    async def test_list_by_type(self, db_session_factory):
        """Test listing subjects by type."""
        # Arrange
        repository = PostgreSQLDigitalTwinSubjectRepository(db_session_factory)
        
        # Create research subjects
        research1 = DigitalTwinSubject.create_research_subject(age=35)
        research2 = DigitalTwinSubject.create_research_subject(age=42)
        await repository.save(research1)
        await repository.save(research2)
        
        # Create anonymous subject
        anonymous = DigitalTwinSubject.create_anonymous_subject()
        await repository.save(anonymous)
        
        # Act
        research_subjects = await repository.list_by_type("research")
        anonymous_subjects = await repository.list_by_type("anonymous")
        
        # Assert
        assert len(research_subjects) == 2
        assert len(anonymous_subjects) == 1
        assert research_subjects[0].identity_type == "research"
        assert anonymous_subjects[0].identity_type == "anonymous"
```

## Implementation Sequence

When implementing these components, follow this sequence:

1. Start with the core domain entities (DigitalTwinSubject)
2. Implement the repository interfaces and concrete implementations
3. Create the application services that utilize these components
4. Build the API layer on top of the application services
5. Develop comprehensive tests at each layer

This approach ensures that the core domain model is solid before adding layers that depend on it.