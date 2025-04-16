# Import necessary components (adjust paths as needed based on project structure)
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional # Added Optional
from sqlalchemy.ext.asyncio import AsyncSession # Added AsyncSession
from pydantic import BaseModel, EmailStr, Field # Import BaseModel for schema definition
from datetime import datetime # Import datetime

# Use absolute paths for domain/infra/presentation imports for clarity in routing layer
from app.domain.entities.patient import Patient # Use the dataclass for response
# from ...domain.use_cases.get_patient import GetPatientUseCase
# from ...domain.use_cases.create_patient import CreatePatientUseCase
# from ...domain.use_cases.update_patient import UpdatePatientUseCase
from app.infrastructure.persistence.sqlalchemy.patient_repository import PatientRepository # Actual repo
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_session # Get session dependency
# Correct relative import for BaseEncryptionService if needed, or use absolute
# from ...infrastructure.security.encryption.base_encryption_service import BaseEncryptionService # For dependency
from app.presentation.api.dependencies.auth import get_current_user # Corrected import
from app.presentation.api.dependencies.repository import get_patient_repository 
# from ...presentation.api.schemas.user import UserResponseSchema # Not directly used here

# Define a Pydantic schema for patient creation aligned with Patient entity
class PatientCreateSchema(BaseModel):
    name: str = Field(..., example="Jane Doe")
    date_of_birth: str = Field(..., example="1990-01-30") # Accept string, entity handles conversion
    gender: str = Field(..., example="Female")
    email: Optional[EmailStr] = Field(None, example="jane.doe@example.com")
    phone: Optional[str] = Field(None, example="555-123-4567")
    address: Optional[str] = Field(None, example="123 Main St, Anytown, USA")
    insurance_number: Optional[str] = Field(None, example="INS987654321")
    # Sensitive fields like ssn are omitted from direct API creation/update
    # medical_history, medications, allergies, notes are managed via specific methods/endpoints ideally

# Define a Pydantic schema for patient updates (aligned with Patient entity)
class PatientUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, example="Jane Smith")
    date_of_birth: Optional[str] = Field(None, example="1990-01-30")
    gender: Optional[str] = Field(None, example="Female")
    email: Optional[EmailStr] = Field(None, example="jane.smith@example.com")
    phone: Optional[str] = Field(None, example="555-987-6543")
    address: Optional[str] = Field(None, example="456 Oak Ave, Anytown, USA")
    insurance_number: Optional[str] = Field(None, example="INS112233445")
    # Only include fields that should be updatable via this generic PUT

# Define the router instance
router = APIRouter()

# GET endpoint for listing patients (with pagination)
@router.get("/", response_model=List[Patient])
async def list_patients_endpoint(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user), # Use the corrected dependency
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Authorization: Only allow admins or doctors to list all patients
    # Assuming role info is available in the current_user dict/object
    user_roles = current_user.get("roles", []) # Use .get with default
    if "admin" not in user_roles and "doctor" not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list patients")

    # Fetch patients using the repository
    patients = await repo.get_all(user=current_user, skip=skip, limit=limit)
    return patients

# GET endpoint - Use the Patient dataclass as response model
@router.get("/{patient_id}", response_model=Patient)
async def get_patient_endpoint(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: PatientRepository = Depends(get_patient_repository)
):
    # ADD THIS CHECK: Ensure user is authenticated before proceeding
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for 401
        )

    # Authorization logic: Check if the user can access this specific patient
    user_sub = current_user.get("sub") # Use 'sub' from JWT payload
    user_roles = current_user.get("roles", [])

    can_access = False
    if "admin" in user_roles: # Admins can access any
        can_access = True
    # TODO: Refine doctor access check based on assigned patients if needed by repo/service layer
    elif "doctor" in user_roles:
         can_access = True # Currently allowing doctors access to any patient endpoint hit
    elif "patient" in user_roles and user_sub == patient_id: # Patients can access own (compare sub to patient_id)
        can_access = True
        
    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this patient data")

    # Fetch patient using repository
    patient = await repo.get_by_id(patient_id, user=current_user) # Pass user context to repo
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient

# POST endpoint - Use the Patient dataclass as response model, PatientCreateSchema for request
@router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient_endpoint(
    patient_data: PatientCreateSchema, # Use the corrected schema
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Authorization: Check if the user has permission to create patients
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and "doctor" not in user_roles: # Only Admin/Doctor can create
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create patients")

    # Create patient using repository
    patient_dict = patient_data.model_dump()
    try:
        created_patient = await repo.create(patient_dict, user=current_user)
        return created_patient
    except Exception as e:
        # Log the exception
        # logger.error(f"Failed to create patient: {e}") 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create patient record")

# PUT endpoint for updating a patient
@router.put("/{patient_id}", response_model=Patient)
async def update_patient_endpoint(
    patient_id: str,
    patient_data: PatientUpdateSchema, # Use the corrected schema
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Authorization: Admins/Doctors can update any patient.
    user_roles = current_user.get("roles", [])
    user_id = current_user.get("id")

    # Check if patient exists first
    existing_patient = await repo.get_by_id(patient_id, user=current_user) 
    if not existing_patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Authorization check (Allow admin/doctor, deny patient update for now)
    if "admin" not in user_roles and "doctor" not in user_roles:
        # If the user is a patient trying to update their own record, different logic might apply
        if "patient" in user_roles and user_id == patient_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient self-update not yet implemented via this endpoint.")
        else:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this patient")

    # Perform the update using the repository
    update_data_dict = patient_data.model_dump(exclude_unset=True)
    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    try:
        updated_patient = await repo.update(
            patient_id=patient_id,
            update_data=update_data_dict,
            user=current_user
        )
        if not updated_patient: # Should ideally not happen if existence check passed
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Update failed, patient may no longer exist")
        return updated_patient
    except Exception as e:
        # Log the exception
        # logger.error(f"Failed to update patient {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update patient record")

# DELETE endpoint for deleting a patient
@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_endpoint(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: PatientRepository = Depends(get_patient_repository)
):
    # Authorization: Typically restricted to Admins
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete patients")

    # Check existence before delete attempt
    existing_patient = await repo.get_by_id(patient_id, user=current_user)
    if not existing_patient:
        # Return 204 even if not found, as the state matches the desired outcome (it's gone)
        return None 

    # Perform the deletion using the repository
    try:
        deleted_successfully = await repo.delete(patient_id=patient_id, user=current_user)
        if not deleted_successfully:
            # This might indicate a permission issue resolved within the repo or other logic failure
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deletion condition not met or failed")
    except Exception as e:
        # Log the exception
        # logger.error(f"Failed to delete patient {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete patient record")

    # No content is returned on successful deletion
    return None
