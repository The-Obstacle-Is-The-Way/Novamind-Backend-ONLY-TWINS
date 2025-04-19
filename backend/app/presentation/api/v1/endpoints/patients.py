"""
CRUD HTTP endpoints for Patient resource.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict
from datetime import datetime

# Database session dependency
# Prefer the original get_db dependency which is overridden in tests.
from app.infrastructure.database.session import get_db as get_db_session  # type: ignore
# Repository for patient persistence
from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import PatientRepository
# Domain entity
from app.domain.entities.patient import Patient as PatientEntity

router = APIRouter()

def patient_to_dict(patient: PatientEntity) -> Dict[str, Any]:
    """Convert PatientEntity to JSON-serializable dict."""
    dob = patient.date_of_birth
    if isinstance(dob, datetime):
        dob_str = dob.date().isoformat()
    else:
        dob_str = str(dob) if dob is not None else None
    return {
        "id": patient.id,
        "medical_record_number": patient.medical_record_number,
        "name": patient.name,
        "date_of_birth": dob_str,
        "gender": patient.gender,
        "email": patient.email,
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_patient_endpoint(
    patient_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Create a new patient."""
    repo = PatientRepository(db)
    try:
        entity = PatientEntity(**patient_data)
    except TypeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid patient data")
    created = await repo.create(entity)
    return patient_to_dict(created)

@router.get("/{patient_id}", status_code=status.HTTP_200_OK)
async def get_patient_endpoint(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get a patient by ID."""
    repo = PatientRepository(db)
    patient = await repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient_to_dict(patient)

@router.patch("/{patient_id}", status_code=status.HTTP_200_OK)
async def update_patient_endpoint(
    patient_id: str,
    update_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Update an existing patient."""
    repo = PatientRepository(db)
    existing = await repo.get_by_id(patient_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    # Apply updates to entity
    for key, value in update_data.items():
        setattr(existing, key, value)
    updated = await repo.update(existing)
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Update failed")
    return patient_to_dict(updated)

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_endpoint(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> None:
    """Delete a patient by ID."""
    repo = PatientRepository(db)
    existing = await repo.get_by_id(patient_id)
    if not existing:
        # Idempotent delete: return no content
        return
    success = await repo.delete(patient_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deletion failed")
    return None
