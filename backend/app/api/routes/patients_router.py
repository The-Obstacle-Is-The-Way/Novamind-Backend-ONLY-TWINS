# Import necessary components (adjust paths as needed based on project structure)
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional # Added Optional
from sqlalchemy.ext.asyncio import AsyncSession # Added AsyncSession
from pydantic import BaseModel, EmailStr, Field # Import BaseModel for schema definition
from datetime import datetime # Import datetime

from ...domain.entities.patient import Patient # Use the dataclass for response
# from ...domain.use_cases.get_patient import GetPatientUseCase
# from ...domain.use_cases.create_patient import CreatePatientUseCase
# from ...domain.use_cases.update_patient import UpdatePatientUseCase
from ...infrastructure.persistence.sqlalchemy.patient_repository import PatientRepository # Actual repo
from ...infrastructure.persistence.sqlalchemy.config.database import get_db_session # Get session dependency
from ...infrastructure.security.encryption.base_encryption_service import BaseEncryptionService # For dependency
from ...presentation.api.dependencies.auth import get_current_user # Corrected import
from ...presentation.api.dependencies.repository import get_patient_repository 
from ...presentation.api.schemas.user import UserResponseSchema # Corrected schema import (assuming UserResponseSchema is needed)

# Define a Pydantic schema for patient creation aligned with test data
class PatientCreateSchema(BaseModel):
    # Align fields with test_phi_in_request_body_handled
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None # Make optional or align with actual requirement
    ssn: Optional[str] = None # Sensitive fields, potentially handled elsewhere
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    # Add other fields as necessary for creation
    # Removed: name, gender

# Define a Pydantic schema for patient updates (allowing partial updates)
class PatientUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    ssn: Optional[str] = None # Consider if this should be updatable via API
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    # Add other updatable fields as needed
    # Fields like 'id', 'created_at', 'updated_at' should generally not be in update schema

# Define the router instance
router = APIRouter()

# GET endpoint for listing patients (with pagination)
@router.get("/", response_model=List[Patient])
async def list_patients_endpoint(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Authorization: Only allow admins or doctors to list all patients
    if current_user.get("role") not in ["admin", "doctor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list patients")

    # Fetch patients using the repository
    patients = await repo.get_all(user=current_user, skip=skip, limit=limit) # Assuming repo.get_all exists
    return patients

# Placeholder GET endpoint - Use the Patient dataclass as response model
@router.get("/{patient_id}", response_model=Patient)
async def get_patient_endpoint(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    # Remove direct dependencies for db and encryption_service
    # db: AsyncSession = Depends(get_db_session),
    # encryption_service: BaseEncryptionService = Depends(), # Assuming a provider exists
    # Use the repository dependency
    repo: PatientRepository = Depends(get_patient_repository)
):
    # ADD THIS CHECK: Ensure user is authenticated before proceeding
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for 401
        )

    # Placeholder logic: Check authorization (e.g., user can access this patient)
    user_id = current_user.get("id")
    # Updated auth check logic (ensure role comparison is accurate)
    # Patients should be able to access their own data
    if current_user.get("role") == "patient" and user_id != patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient cannot access other patient data")
    # Allow Admin and Doctor roles to proceed, deny others implicitly or explicitly
    # The repository layer (_check_access) will perform fine-grained checks for doctors.
    elif current_user.get("role") not in ["admin", "doctor", "patient"]:
         # Deny any other roles not explicitly handled
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not authorized for this resource")
    # Implicit: Admin, Doctor (pending repo check), and Patient (accessing self) can proceed

    # Placeholder logic: Fetch patient using repository (already injected)
    # Pass encryption_service to the repository
    # repo = PatientRepository(db, encryption_service) # No longer needed
    patient = await repo.get_by_id(patient_id, user=current_user) # Pass user context to repo
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient # FastAPI will automatically use the response_model

# Placeholder POST endpoint - Use the Patient dataclass as response model, PatientCreateSchema for request
@router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient_endpoint(
    patient_data: PatientCreateSchema, # Use the defined schema
    current_user: Dict[str, Any] = Depends(get_current_user),
    # Remove direct dependencies for db and encryption_service
    # db: AsyncSession = Depends(get_db_session),
    # encryption_service: BaseEncryptionService = Depends(), # Assuming a provider exists
    # Use the repository dependency
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Placeholder logic: Check authorization (e.g., only admin/doctor can create)
    # Ensure role strings match exactly what the mock provides
    if current_user.get("role") not in ["admin", "doctor"]: # Example auth check
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create patients")

    # Placeholder logic: Create patient using repository (already injected)
    # Pass encryption_service to the repository
    # repo = PatientRepository(db, encryption_service) # No longer needed
    # Convert Pydantic schema to dict or domain model if needed by repo
    # Pass user context to repo create method if it requires it
    created_patient = await repo.create(patient_data.model_dump(), user=current_user) # Assuming repo.create takes user context
    return created_patient

# PUT endpoint for updating a patient
@router.put("/{patient_id}", response_model=Patient)
async def update_patient_endpoint(
    patient_id: str,
    patient_data: PatientUpdateSchema,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Authorization: Admins/Doctors can update any patient. Patients might update own (future enhancement).
    user_role = current_user.get("role")
    user_id = current_user.get("id")

    # First, check if patient exists (optional, repo.update might handle this)
    # Re-fetch using repo to ensure we have the latest state before update logic
    existing_patient = await repo.get_by_id(patient_id, user=current_user) # Use user context for fetch too
    if not existing_patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Authorization check
    can_update = False
    if user_role == "admin" or user_role == "doctor":
        can_update = True
    elif user_role == "patient" and user_id == patient_id:
        # TODO: Refine what a patient can update about themselves (e.g., contact info)
        # For now, let's restrict updates to admin/doctor for simplicity matching initial tests
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients cannot update records via this endpoint yet.")
        # can_update = True # Enable if patients can update some fields

    if not can_update:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this patient")

    # Perform the update using the repository
    # Pass only fields that are set in the request using exclude_unset=True
    update_data_dict = patient_data.model_dump(exclude_unset=True)
    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    updated_patient = await repo.update(
        patient_id=patient_id,
        update_data=update_data_dict,
        user=current_user
    ) # Assuming repo.update exists and returns the updated Patient object

    if not updated_patient: # Handle case where update fails or returns None unexpectedly
         # Consider specific error from repo if available
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found or update failed")

    return updated_patient

# DELETE endpoint for deleting a patient
@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_endpoint(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Authorization: Typically restricted to Admins
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete patients")

    # Optional: Check if patient exists before attempting delete (reduces unnecessary repo calls if already gone)
    # Re-fetch using repo for consistency
    existing_patient = await repo.get_by_id(patient_id, user=current_user) # Use user context for fetch
    if not existing_patient:
        # If not found, arguably the DELETE goal is achieved (it's gone). Return 204.
        # Alternatively, return 404 if strict confirmation of prior existence is required.
        # Returning 204 is often preferred for idempotency.
        return None # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Perform the deletion using the repository
    deleted_successfully = await repo.delete(patient_id=patient_id, user=current_user) # Assuming repo.delete returns bool or raises

    if not deleted_successfully:
         # This might indicate a permission issue within the repo or a DB error.
         # If repo.delete raises exceptions on failure, this check might not be needed.
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete patient")

    # No content is returned on successful deletion (status code 204)
    return None

# Add other endpoints (PUT, DELETE) as needed following a similar pattern