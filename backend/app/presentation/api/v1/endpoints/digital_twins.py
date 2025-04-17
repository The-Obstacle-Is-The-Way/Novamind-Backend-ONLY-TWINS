"""
API Endpoints for Digital Twin Management.

Provides endpoints for creating, retrieving, updating, and managing
patient digital twins.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body

# Dependencies
from app.presentation.api.dependencies.services import get_digital_twin_service
from app.presentation.api.dependencies.auth import get_current_user

# Domain interface
from app.domain.services.digital_twin_core_service import DigitalTwinCoreService
# User entity
from app.domain.entities.user import User

router = APIRouter()


@router.get(
    "/{patient_id}",
    summary="Get Latest Digital Twin State",
    description="Retrieve the latest state of the digital twin for a specific patient, "
                "optionally initializing with genetic data or biomarkers.",
)
async def get_latest_state(
    patient_id: UUID,
    include_genetic_data: Optional[bool] = False,
    include_biomarkers: Optional[bool] = False,
    current_user: User = Depends(get_current_user),
    service: DigitalTwinCoreService = Depends(get_digital_twin_service),
) -> Dict[str, Any]:
    try:
        state = await service.initialize_digital_twin(
            patient_id, include_genetic_data, include_biomarkers
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    return {
        "id": str(state.id),
        "patient_id": str(state.patient_id),
        "version": state.version,
        "data": state.data,
    }


@router.post(
    "/{patient_id}/events",
    summary="Process Treatment Event",
    description="Append a treatment event to the digital twin's history.",
    status_code=status.HTTP_200_OK,
)
async def process_treatment_event(
    patient_id: UUID,
    event_data: Dict[str, Any] = Body(...),
    service: DigitalTwinCoreService = Depends(get_digital_twin_service),
) -> Dict[str, Any]:
    try:
        state = await service.process_treatment_event(patient_id, event_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    return {
        "id": str(state.id),
        "patient_id": str(state.patient_id),
        "version": state.version,
        "data": state.data,
    }


@router.get(
    "/{patient_id}/recommendations",
    summary="Generate Treatment Recommendations",
    description="Generate medication and therapy treatment recommendations.",
)
async def generate_treatment_recommendations(
    patient_id: UUID,
    consider_current_medications: Optional[bool] = False,
    include_therapy_options: Optional[bool] = False,
    service: DigitalTwinCoreService = Depends(get_digital_twin_service),
) -> List[Dict[str, Any]]:
    return await service.generate_treatment_recommendations(
        patient_id, consider_current_medications, include_therapy_options
    )


@router.get(
    "/{patient_id}/visualization",
    summary="Get Visualization Data",
    description="Retrieve visualization data for the digital twin (e.g., 3D brain model).",
)
async def get_visualization_data(
    patient_id: UUID,
    visualization_type: Optional[str] = "brain_model_3d",
    service: DigitalTwinCoreService = Depends(get_digital_twin_service),
) -> Dict[str, Any]:
    return await service.get_visualization_data(patient_id, visualization_type)


@router.post(
    "/{patient_id}/compare",
    summary="Compare Two Digital Twin States",
    description="Compare changes between two digital twin state versions.",
)
async def compare_states(
    patient_id: UUID,
    state_id_1: UUID = Body(..., embed=True),
    state_id_2: UUID = Body(..., embed=True),
    service: DigitalTwinCoreService = Depends(get_digital_twin_service),
) -> Dict[str, Any]:
    return await service.compare_states(patient_id, state_id_1, state_id_2)


@router.get(
    "/{patient_id}/summary",
    summary="Generate Clinical Summary",
    description="Generate a summary report for a patient, including history and predictions.",
)
async def generate_clinical_summary(
    patient_id: UUID,
    include_treatment_history: Optional[bool] = False,
    include_predictions: Optional[bool] = False,
    service: DigitalTwinCoreService = Depends(get_digital_twin_service),
) -> Dict[str, Any]:
    return await service.generate_clinical_summary(
        patient_id, include_treatment_history, include_predictions
    )

