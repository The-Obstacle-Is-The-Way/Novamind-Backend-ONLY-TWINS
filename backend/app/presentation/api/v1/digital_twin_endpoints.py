"""
Digital Twin API endpoints.

This module defines the API routes for the digital twin system,
providing endpoints for creation, retrieval, and management of digital twins.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, status
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger
from app.presentation.models.biometric_data import BiometricDataInput, BiometricHistoryParams
from app.presentation.models.digital_twin import (
    DigitalTwinCreate,
    DigitalTwinOutput,
    DigitalTwinSummary
)
from app.presentation.api.dependencies import DigitalTwinServiceDep
from app.domain.entities.biometric_twin_enhanced import BiometricSource, BiometricType


logger = get_logger(__name__)
router = APIRouter(tags=["Digital Twin"])


@router.post(
    "/digital-twins",
    response_model=DigitalTwinOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Create Digital Twin",
    description="Create a new digital twin for a patient."
)
async def create_digital_twin(
    data: DigitalTwinCreate = Body(...),
    service: DigitalTwinServiceDep = Depends()
) -> Dict[str, Any]:
    """
    Create a new digital twin.
    
    Args:
        data: Digital twin creation data
        service: Digital twin service
        
    Returns:
        Newly created digital twin data
    
    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(f"Creating digital twin for patient {data.patient_id}")
        twin = await service.create_digital_twin(data.patient_id)
        if not twin:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create digital twin"
            )
        return twin
    except Exception as e:
        logger.error(f"Error creating digital twin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the digital twin"
        )


@router.get(
    "/digital-twins/patient/{patient_id}",
    response_model=DigitalTwinOutput,
    summary="Get Digital Twin",
    description="Get a patient's complete digital twin data."
)
async def get_digital_twin(
    patient_id: str = Path(..., description="ID of the patient"),
    service: DigitalTwinServiceDep = Depends()
) -> Dict[str, Any]:
    """
    Get a patient's digital twin.
    
    Args:
        patient_id: ID of the patient
        service: Digital twin service
        
    Returns:
        Digital twin data
    
    Raises:
        HTTPException: If twin is not found
    """
    try:
        logger.info(f"Retrieving digital twin for patient {patient_id}")
        twin = await service.get_digital_twin(patient_id)
        if not twin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digital twin not found"
            )
        return twin
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving digital twin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the digital twin"
        )


@router.get(
    "/digital-twins/patient/{patient_id}/summary",
    response_model=DigitalTwinSummary,
    summary="Get Digital Twin Summary",
    description="Get a summary of a patient's digital twin with latest readings."
)
async def get_digital_twin_summary(
    patient_id: str = Path(..., description="ID of the patient"),
    service: DigitalTwinServiceDep = Depends()
) -> Dict[str, Any]:
    """
    Get a summary of a patient's digital twin.
    
    Args:
        patient_id: ID of the patient
        service: Digital twin service
        
    Returns:
        Digital twin summary data
    
    Raises:
        HTTPException: If twin is not found
    """
    try:
        logger.info(f"Retrieving digital twin summary for patient {patient_id}")
        
        # Get digital twin
        twin = await service.get_digital_twin(patient_id)
        if not twin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digital twin not found"
            )
        
        # Get latest values
        latest_values = await service.get_latest_biometrics(patient_id)
        if latest_values is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve latest biometric values"
            )
        
        # Build summary response
        return {
            "id": twin["id"],
            "patient_id": twin["patient_id"],
            "latest_readings": latest_values,
            "updated_at": twin["updated_at"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving digital twin summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the digital twin summary"
        )


@router.post(
    "/digital-twins/patient/{patient_id}/biometrics",
    status_code=status.HTTP_201_CREATED,
    summary="Add Biometric Data",
    description="Add new biometric data to a patient's digital twin."
)
async def add_biometric_data(
    patient_id: str = Path(..., description="ID of the patient"),
    data: BiometricDataInput = Body(...),
    service: DigitalTwinServiceDep = Depends()
) -> Dict[str, Any]:
    """
    Add biometric data to a digital twin.
    
    Args:
        patient_id: ID of the patient
        data: Biometric data input
        service: Digital twin service
        
    Returns:
        Success message
    
    Raises:
        HTTPException: If operation fails
    """
    try:
        logger.info(f"Adding {data.biometric_type} data for patient {patient_id}")
        
        success = await service.add_biometric_data(
            patient_id=patient_id,
            biometric_type=data.biometric_type,
            value=data.value,
            source=data.source,
            timestamp=data.timestamp,
            metadata=data.metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add biometric data"
            )
        
        return {"status": "success", "message": "Biometric data added successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error adding biometric data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while adding biometric data"
        )


@router.get(
    "/digital-twins/patient/{patient_id}/biometrics/{biometric_type}",
    summary="Get Biometric History",
    description="Get history of a specific biometric measurement."
)
async def get_biometric_history(
    patient_id: str = Path(..., description="ID of the patient"),
    biometric_type: str = Path(..., description="Type of biometric data"),
    params: BiometricHistoryParams = Depends(),
    service: DigitalTwinServiceDep = Depends()
) -> Dict[str, Any]:
    """
    Get history of biometric measurements.
    
    Args:
        patient_id: ID of the patient
        biometric_type: Type of biometric data
        params: Query parameters for filtering
        service: Digital twin service
        
    Returns:
        Biometric history data
    
    Raises:
        HTTPException: If operation fails
    """
    try:
        logger.info(f"Retrieving {biometric_type} history for patient {patient_id}")
        
        # Convert datetime to strings if provided
        start_time = params.start_time.isoformat() if params.start_time else None
        end_time = params.end_time.isoformat() if params.end_time else None
        
        history = await service.get_biometric_history(
            patient_id=patient_id,
            biometric_type=biometric_type,
            start_time=start_time,
            end_time=end_time
        )
        
        if history is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve biometric history"
            )
        
        if not history:
            return {"data": [], "count": 0}
        
        return {"data": history, "count": len(history)}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving biometric history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving biometric history"
        )


@router.get(
    "/digital-twins/patient/{patient_id}/abnormal",
    summary="Get Abnormal Values",
    description="Get abnormal biometric values outside physiological ranges."
)
async def get_abnormal_values(
    patient_id: str = Path(..., description="ID of the patient"),
    service: DigitalTwinServiceDep = Depends()
) -> Dict[str, Any]:
    """
    Get abnormal biometric values.
    
    Args:
        patient_id: ID of the patient
        service: Digital twin service
        
    Returns:
        Abnormal values by biometric type
    
    Raises:
        HTTPException: If operation fails
    """
    try:
        logger.info(f"Retrieving abnormal values for patient {patient_id}")
        
        abnormal_values = await service.detect_abnormal_values(patient_id)
        
        if abnormal_values is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to detect abnormal values"
            )
        
        if not abnormal_values:
            return {"data": {}, "count": 0}
        
        # Count total abnormal values
        total_count = sum(len(values) for values in abnormal_values.values())
        
        return {
            "data": abnormal_values,
            "count": total_count
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving abnormal values: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving abnormal values"
        )


@router.get(
    "/digital-twins/patient/{patient_id}/critical",
    summary="Get Critical Values",
    description="Get critical biometric values requiring immediate attention."
)
async def get_critical_values(
    patient_id: str = Path(..., description="ID of the patient"),
    service: DigitalTwinServiceDep = Depends()
) -> Dict[str, Any]:
    """
    Get critical biometric values.
    
    Args:
        patient_id: ID of the patient
        service: Digital twin service
        
    Returns:
        Critical values by biometric type
    
    Raises:
        HTTPException: If operation fails
    """
    try:
        logger.info(f"Retrieving critical values for patient {patient_id}")
        
        critical_values = await service.detect_critical_values(patient_id)
        
        if critical_values is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to detect critical values"
            )
        
        if not critical_values:
            return {"data": {}, "count": 0}
        
        # Count total critical values
        total_count = sum(len(values) for values in critical_values.values())
        
        return {
            "data": critical_values,
            "count": total_count
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving critical values: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving critical values"
        )