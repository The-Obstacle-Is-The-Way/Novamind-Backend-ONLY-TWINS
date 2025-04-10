# -*- coding: utf-8 -*-
"""
Digital Twins API Endpoints.

This module provides FastAPI routes for managing patient digital twins
using the MentaLLaMA framework with HIPAA compliance.
"""

import logging
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from pydantic import UUID4

# Import EntityNotFoundError from domain exceptions
from app.domain.exceptions import EntityNotFoundError
from app.core.exceptions.ml_exceptions import (
    DigitalTwinError,
    # SimulationError, # Not defined in ml_exceptions.py
    # TwinNotFoundError, # Removed - Does not exist
    # TwinStorageError # Removed - Does not exist
)
from app.infrastructure.ml.digital_twin_integration_service import DigitalTwinIntegrationService
from app.presentation.api.dependencies import get_digital_twin_service
from app.presentation.api.schemas.ml_schemas import (
    DigitalTwinCreateRequest,
    DigitalTwinResponse,
    DigitalTwinUpdateRequest,
    SimulationRequest,
    SimulationResponse
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/digital-twins",
    tags=["digital-twins"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Insufficient permissions"},
        status.HTTP_404_NOT_FOUND: {"description": "Digital twin not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@router.post(
    "/",
    response_model=DigitalTwinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new digital twin",
    description="""
    Create a new digital twin for a patient.
    
    This endpoint creates a new digital twin model for a patient based on
    their clinical data. The twin can be used for treatment simulation,
    outcome prediction, and personalized care planning.
    """,
)
async def create_digital_twin(
    request: DigitalTwinCreateRequest,
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
) -> DigitalTwinResponse:
    """
    Create a new digital twin for a patient.
    
    Args:
        request: Creation request with patient data
        digital_twin_service: Digital twin service instance
        
    Returns:
        Created digital twin information
        
    Raises:
        HTTPException: If twin creation fails
    """
    try:
        # Log operation (no PHI)
        twin_id = str(uuid.uuid4())
        logger.info(f"Digital twin creation requested, ID: {twin_id}")
        
        # Create digital twin
        result = await digital_twin_service.create_twin(
            twin_id=twin_id,
            patient_id=request.patient_id,
            clinical_data=request.clinical_data,
            demographic_data=request.demographic_data,
            parameters=request.parameters
        )
        
        # Log completion (no PHI)
        logger.info(f"Digital twin created successfully, ID: {twin_id}")
        
        return result
        
    except DigitalTwinError as e: # Changed exception type
        logger.error(f"Twin storage error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store digital twin. Please try again.",
        )
        
    except DigitalTwinError as e:
        logger.error(f"Digital twin creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create digital twin. Please try again.",
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in digital twin creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )


@router.get(
    "/{twin_id}",
    response_model=DigitalTwinResponse,
    status_code=status.HTTP_200_OK,
    summary="Get digital twin",
    description="""
    Retrieve a digital twin by ID.
    
    This endpoint retrieves information about an existing digital twin,
    including its current state, parameters, and metadata.
    """,
)
async def get_digital_twin(
    twin_id: UUID4 = Path(..., description="ID of the digital twin to retrieve"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
) -> DigitalTwinResponse:
    """
    Retrieve a digital twin by ID.
    
    Args:
        twin_id: Digital twin ID
        digital_twin_service: Digital twin service instance
        
    Returns:
        Digital twin information
        
    Raises:
        HTTPException: If twin is not found or retrieval fails
    """
    try:
        # Log operation (no PHI)
        logger.info(f"Digital twin retrieval requested, ID: {twin_id}")
        
        # Get digital twin
        result = await digital_twin_service.get_twin(twin_id=str(twin_id))
        
        # Log completion (no PHI)
        logger.info(f"Digital twin retrieved successfully, ID: {twin_id}")
        
        return result
        
    except EntityNotFoundError: # Changed exception type
        logger.warning(f"Digital twin not found, ID: {twin_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digital twin with ID {twin_id} not found",
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in digital twin retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve digital twin. Please try again.",
        )


@router.put(
    "/{twin_id}",
    response_model=DigitalTwinResponse,
    status_code=status.HTTP_200_OK,
    summary="Update digital twin",
    description="""
    Update an existing digital twin.
    
    This endpoint updates an existing digital twin with new clinical data,
    parameters, or other information. It can be used to keep the twin
    synchronized with real patient data.
    """,
)
async def update_digital_twin(
    request: DigitalTwinUpdateRequest,
    twin_id: UUID4 = Path(..., description="ID of the digital twin to update"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
) -> DigitalTwinResponse:
    """
    Update an existing digital twin.
    
    Args:
        request: Update request with new data
        twin_id: Digital twin ID
        digital_twin_service: Digital twin service instance
        
    Returns:
        Updated digital twin information
        
    Raises:
        HTTPException: If twin is not found or update fails
    """
    try:
        # Log operation (no PHI)
        logger.info(f"Digital twin update requested, ID: {twin_id}")
        
        # Update digital twin
        result = await digital_twin_service.update_twin(
            twin_id=str(twin_id),
            clinical_data=request.clinical_data,
            parameters=request.parameters
        )
        
        # Log completion (no PHI)
        logger.info(f"Digital twin updated successfully, ID: {twin_id}")
        
        return result
        
    except EntityNotFoundError: # Changed exception type
        logger.warning(f"Digital twin not found for update, ID: {twin_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digital twin with ID {twin_id} not found",
        )
        
    except TwinStorageError as e:
        logger.error(f"Twin storage error during update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update digital twin. Please try again.",
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in digital twin update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )


@router.post(
    "/{twin_id}/simulate",
    response_model=SimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run simulation on digital twin",
    description="""
    Run a simulation on a digital twin.
    
    This endpoint runs a simulation on an existing digital twin to predict
    treatment outcomes, responses, or other clinical scenarios. It can be
    used for personalized treatment planning.
    """,
)
async def run_simulation(
    request: SimulationRequest,
    twin_id: UUID4 = Path(..., description="ID of the digital twin to simulate"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
) -> SimulationResponse:
    """
    Run a simulation on a digital twin.
    
    Args:
        request: Simulation parameters
        twin_id: Digital twin ID
        digital_twin_service: Digital twin service instance
        
    Returns:
        Simulation results
        
    Raises:
        HTTPException: If twin is not found or simulation fails
    """
    try:
        # Log operation (no PHI)
        logger.info(
            f"Digital twin simulation requested, ID: {twin_id}, "
            f"scenario: {request.scenario}"
        )
        
        # Run simulation
        result = await digital_twin_service.run_simulation(
            twin_id=str(twin_id),
            scenario=request.scenario,
            parameters=request.parameters,
            duration=request.duration
        )
        
        # Log completion (no PHI)
        logger.info(
            f"Digital twin simulation completed, ID: {twin_id}, "
            f"scenario: {request.scenario}"
        )
        
        return result
        
    except EntityNotFoundError: # Changed exception type
        logger.warning(f"Digital twin not found for simulation, ID: {twin_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digital twin with ID {twin_id} not found",
        )
        
    except SimulationError as e:
        logger.error(f"Simulation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}",
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in digital twin simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )


@router.delete(
    "/{twin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete digital twin",
    description="""
    Delete a digital twin.
    
    This endpoint deletes an existing digital twin. This operation cannot
    be undone, but an audit trail of the deletion is maintained.
    """,
)
async def delete_digital_twin(
    twin_id: UUID4 = Path(..., description="ID of the digital twin to delete"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
) -> None:
    """
    Delete a digital twin.
    
    Args:
        twin_id: Digital twin ID
        digital_twin_service: Digital twin service instance
        
    Raises:
        HTTPException: If twin is not found or deletion fails
    """
    try:
        # Log operation (no PHI)
        logger.info(f"Digital twin deletion requested, ID: {twin_id}")
        
        # Delete digital twin
        await digital_twin_service.delete_twin(twin_id=str(twin_id))
        
        # Log completion (no PHI)
        logger.info(f"Digital twin deleted successfully, ID: {twin_id}")
        
        return None
        
    except EntityNotFoundError: # Changed exception type
        logger.warning(f"Digital twin not found for deletion, ID: {twin_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digital twin with ID {twin_id} not found",
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in digital twin deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete digital twin. Please try again.",
        )


@router.get(
    "/",
    response_model=List[DigitalTwinResponse],
    status_code=status.HTTP_200_OK,
    summary="List digital twins",
    description="""
    List digital twins for a patient.
    
    This endpoint retrieves a list of all digital twins for a specific patient,
    optionally filtered by parameters.
    """,
)
async def list_patient_twins(
    patient_id: str = Query(..., description="Patient ID to list twins for"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
) -> List[DigitalTwinResponse]:
    """
    List digital twins for a patient.
    
    Args:
        patient_id: Patient ID to list twins for
        digital_twin_service: Digital twin service instance
        
    Returns:
        List of digital twins for the patient
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        # Log operation (no PHI)
        logger.info(f"Digital twin listing requested for patient")
        
        # List digital twins
        results = await digital_twin_service.list_twins(patient_id=patient_id)
        
        # Log completion (no PHI)
        logger.info(f"Retrieved {len(results)} digital twins")
        
        return results
        
    except Exception as e:
        logger.error(f"Unexpected error in digital twin listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list digital twins. Please try again.",
        )
