# -*- coding: utf-8 -*-
"""
Digital Twin API endpoints.

This module provides FastAPI endpoints for interacting with Digital Twin services.
These endpoints allow clinicians and systems to query patient digital twin models,
get insights, and simulate treatment outcomes.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import UUID4
from uuid import UUID
from app.core.exceptions.ml_exceptions import (
    ModelInferenceError as CoreModelInferenceError,
    ModelNotFoundError,
    ServiceUnavailableError,
    DigitalTwinError,
    DigitalTwinInferenceError,
    DigitalTwinSessionError,
    SimulationError
)
from app.domain.exceptions import ValidationError, ModelInferenceError as DomainModelInferenceError
from app.domain.exceptions import ValidationError
from app.presentation.api.dependencies import get_digital_twin_service
from app.infrastructure.ml.digital_twin_integration_service import DigitalTwinIntegrationService
from app.presentation.api.v1.schemas.digital_twin_schemas import (
    DigitalTwinStatusResponse,
    PatientInsightsResponse,
    SymptomForecastResponse,
    BiometricCorrelationResponse,
    MedicationResponsePredictionResponse,
    TreatmentPlanResponse
)


async def get_current_user_id(request: Request) -> UUID:
    """
    Get the ID of the currently authenticated user.
    
    In a real implementation, this would extract the user ID from
    the authentication token or session. For this mock implementation,
    we return a fixed UUID.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        User UUID
    """
    # In a real implementation, this would come from the auth token
    # For now, we'll return a fixed ID for testing
    return UUID("00000000-0000-0000-0000-000000000001")


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


@router.get(
    "/patients/{patient_id}/status",
    response_model=DigitalTwinStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Digital Twin status for a patient",
    description="Retrieves the current status and completeness of a patient's Digital Twin model."
)
async def get_digital_twin_status(
    patient_id: UUID4 = Path(..., description="Patient ID"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get the current status of a patient's Digital Twin.
    
    Args:
        patient_id: Unique identifier for the patient
        digital_twin_service: Digital Twin integration service
        current_user_id: ID of the authenticated user
    
    Returns:
        Digital Twin status response
    
    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        status_response = await digital_twin_service.get_digital_twin_status(patient_id)
        return status_response
    except (ModelNotFoundError, ServiceUnavailableError, ValidationError) as e:
        # Handle errors without leaking PHI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CoreModelInferenceError, DomainModelInferenceError) as e:
        # Explicitly handle ModelInferenceError to ensure it returns a 400
        logging.error(f"Error in get_digital_twin_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the full error but return a generic message to avoid leaking PHI
        logging.error(f"Error in get_digital_twin_status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred processing the digital twin status"
        )


@router.get(
    "/patients/{patient_id}/insights",
    response_model=PatientInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get comprehensive patient insights",
    description="Retrieves comprehensive insights about a patient from their Digital Twin model."
)
async def get_patient_insights(
    patient_id: UUID4 = Path(..., description="Patient ID"),
    include_symptom_forecast: bool = Query(True, description="Include symptom forecasting insights"),
    include_biometric_correlations: bool = Query(True, description="Include biometric correlations"),
    include_medication_predictions: bool = Query(True, description="Include medication response predictions"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get comprehensive insights for a patient from their Digital Twin model.
    
    Args:
        patient_id: Unique identifier for the patient
        include_symptom_forecast: Whether to include symptom forecasting insights
        include_biometric_correlations: Whether to include biometric correlations
        include_medication_predictions: Whether to include medication response predictions
        digital_twin_service: Digital Twin integration service
        current_user_id: ID of the authenticated user
    
    Returns:
        Comprehensive patient insights
    
    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        options = {
            "include_symptom_forecast": include_symptom_forecast,
            "include_biometric_correlations": include_biometric_correlations,
            "include_medication_predictions": include_medication_predictions
        }
        
        insights = await digital_twin_service.generate_comprehensive_patient_insights(
            patient_id=patient_id,
            options=options
        )
        
        return insights
    except (ModelNotFoundError, ServiceUnavailableError, ValidationError) as e:
        # Handle errors without leaking PHI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CoreModelInferenceError, DomainModelInferenceError) as e:
        # Explicitly handle ModelInferenceError to ensure it returns a 400
        logging.error(f"Error in get_patient_insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the full error but return a generic message to avoid leaking PHI
        logging.error(f"Error in get_patient_insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred processing patient insights"
        )


@router.post(
    "/patients/{patient_id}/update",
    response_model=DigitalTwinStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Update patient Digital Twin",
    description="Updates a patient's Digital Twin model with new data."
)
async def update_digital_twin(
    update_data: Dict,
    patient_id: UUID4 = Path(..., description="Patient ID"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Update a patient's Digital Twin model with new data.
    
    Args:
        update_data: Data to update the Digital Twin with
        patient_id: Unique identifier for the patient
        digital_twin_service: Digital Twin integration service
        current_user_id: ID of the authenticated user
    
    Returns:
        Updated Digital Twin status
    
    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        # Update the digital twin
        await digital_twin_service.update_digital_twin(
            patient_id=patient_id,
            update_data=update_data
        )
        
        # Get the updated status
        status_response = await digital_twin_service.get_digital_twin_status(patient_id)
        return status_response
    except (ModelNotFoundError, ServiceUnavailableError, ValidationError) as e:
        # Handle errors without leaking PHI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CoreModelInferenceError, DomainModelInferenceError) as e:
        # Explicitly handle ModelInferenceError to ensure it returns a 400
        logging.error(f"Error in update_digital_twin: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the full error but return a generic message to avoid leaking PHI
        logging.error(f"Error in update_digital_twin: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred updating the digital twin"
        )


@router.get(
    "/patients/{patient_id}/symptom-forecast",
    response_model=SymptomForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get symptom forecast for patient",
    description="Retrieves a forecast of symptom progression for a patient."
)
async def get_symptom_forecast(
    patient_id: UUID4 = Path(..., description="Patient ID"),
    days: int = Query(30, description="Number of days to forecast"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a forecast of symptom progression for a patient.
    
    Args:
        patient_id: Unique identifier for the patient
        days: Number of days to forecast
        digital_twin_service: Digital Twin integration service
        current_user_id: ID of the authenticated user
    
    Returns:
        Symptom forecast
    
    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        forecast = await digital_twin_service.symptom_forecasting_service.forecast_symptoms(
            patient_id=patient_id,
            days=days
        )
        
        return forecast
    except (ModelNotFoundError, ServiceUnavailableError, ValidationError) as e:
        # Handle errors without leaking PHI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CoreModelInferenceError, DomainModelInferenceError) as e:
        # Explicitly handle ModelInferenceError to ensure it returns a 400
        logging.error(f"Error in get_symptom_forecast: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the full error but return a generic message to avoid leaking PHI
        logging.error(f"Error in get_symptom_forecast: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred generating symptom forecast"
        )


@router.get(
    "/patients/{patient_id}/biometric-correlations",
    response_model=BiometricCorrelationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get biometric correlations for patient",
    description="Retrieves correlations between biometric data and mental health indicators."
)
async def get_biometric_correlations(
    patient_id: UUID4 = Path(..., description="Patient ID"),
    days: int = Query(30, description="Number of days of data to analyze"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get correlations between biometric data and mental health indicators.
    
    Args:
        patient_id: Unique identifier for the patient
        days: Number of days of data to analyze
        digital_twin_service: Digital Twin integration service
        current_user_id: ID of the authenticated user
    
    Returns:
        Biometric correlations
    
    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        correlations = await digital_twin_service.biometric_correlation_service.analyze_correlations(
            patient_id=patient_id,
            window_days=days
        )
        
        return correlations
    except (ModelNotFoundError, ServiceUnavailableError, ValidationError) as e:
        # Handle errors without leaking PHI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CoreModelInferenceError, DomainModelInferenceError) as e:
        # Explicitly handle ModelInferenceError to ensure it returns a 400
        logging.error(f"Error in get_biometric_correlations: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the full error but return a generic message to avoid leaking PHI
        logging.error(f"Error in get_biometric_correlations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred analyzing biometric correlations"
        )


@router.post(
    "/patients/{patient_id}/medication-response",
    response_model=MedicationResponsePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict medication response",
    description="Predicts a patient's response to specified medications."
)
async def predict_medication_response(
    request_data: Dict,
    patient_id: UUID4 = Path(..., description="Patient ID"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Predict a patient's response to specified medications.
    
    Args:
        request_data: Request data containing medications to predict response for
        patient_id: Unique identifier for the patient
        digital_twin_service: Digital Twin integration service
        current_user_id: ID of the authenticated user
    
    Returns:
        Medication response predictions
    
    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        medications = request_data.get("medications", [])
        
        predictions = await digital_twin_service.pharmacogenomics_service.predict_medication_responses(
            patient_id=patient_id,
            medications=medications
        )
        
        return predictions
    except (ModelNotFoundError, ServiceUnavailableError, ValidationError) as e:
        # Handle errors without leaking PHI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CoreModelInferenceError, DomainModelInferenceError) as e:
        # Explicitly handle ModelInferenceError to ensure it returns a 400
        logging.error(f"Error in predict_medication_response: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the full error but return a generic message to avoid leaking PHI
        logging.error(f"Error in predict_medication_response: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred predicting medication response"
        )


@router.post(
    "/patients/{patient_id}/treatment-plan",
    response_model=TreatmentPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate treatment plan",
    description="Generates a personalized treatment plan for a patient."
)
async def generate_treatment_plan(
    request_data: Dict,
    patient_id: UUID4 = Path(..., description="Patient ID"),
    digital_twin_service: DigitalTwinIntegrationService = Depends(get_digital_twin_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Generate a personalized treatment plan for a patient.
    
    Args:
        request_data: Request data containing treatment plan parameters
        patient_id: Unique identifier for the patient
        digital_twin_service: Digital Twin integration service
        current_user_id: ID of the authenticated user
    
    Returns:
        Personalized treatment plan
    
    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        treatment_plan = await digital_twin_service.pharmacogenomics_service.recommend_treatment_plan(
            patient_id=patient_id,
            diagnosis=request_data.get("diagnosis"),
            treatment_goals=request_data.get("treatment_goals", []),
            treatment_constraints=request_data.get("treatment_constraints", [])
        )
        
        return treatment_plan
    except (ModelNotFoundError, ServiceUnavailableError, ValidationError) as e:
        # Handle errors without leaking PHI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CoreModelInferenceError, DomainModelInferenceError) as e:
        # Explicitly handle ModelInferenceError to ensure it returns a 400
        logging.error(f"Error in generate_treatment_plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the full error but return a generic message to avoid leaking PHI
        logging.error(f"Error in generate_treatment_plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred generating treatment plan"
        )
