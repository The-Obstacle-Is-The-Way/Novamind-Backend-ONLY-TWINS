"""
API routes for temporal neurotransmitter analysis.

This module defines FastAPI routes for the temporal neurotransmitter service
using the clean SubjectIdentity architecture with no legacy dependencies.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security, status, Path, Query

from app.api.auth.jwt import get_current_user, verify_token
from app.api.deps import (
    get_subject_repository,
    get_sequence_repository,
    get_event_repository,
    get_audit_service,
    get_xgboost_service,
)
from app.api.schemas.temporal_schemas import (
    GenerateTimeSeriesRequest,
    TimeSeriesResponse,
    NeurotransmitterAnalysisRequest,
    NeurotransmitterEffectResponse,
    TreatmentSimulationRequest,
    SimulationResultResponse,
    CascadeVisualizationRequest,
    VisualizationDataResponse,
    APIResponse,
)
from app.application.services.temporal_neurotransmitter_service import TemporalNeurotransmitterService
from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter
from app.domain.entities.identity.subject_identity import SubjectIdentityRepository
from app.domain.repositories.temporal_repository import TemporalSequenceRepository, EventRepository
from app.domain.services.visualization_preprocessor import NeurotransmitterVisualizationPreprocessor
from app.core.audit.audit_service import AuditService
from app.core.exceptions import ResourceNotFoundError, ValidationError, AuthorizationError


router = APIRouter(
    prefix="/api/v1/neurotransmitters",
    tags=["Neurotransmitter Analysis"],
    dependencies=[Security(verify_token, scopes=["digital_twin:read", "digital_twin:write"])],
)


async def get_service(
    subject_repository: SubjectIdentityRepository = Depends(get_subject_repository),
    sequence_repository: TemporalSequenceRepository = Depends(get_sequence_repository),
    event_repository: EventRepository = Depends(get_event_repository),
    audit_service: AuditService = Depends(get_audit_service),
    xgboost_service: Any = Depends(get_xgboost_service),
) -> TemporalNeurotransmitterService:
    """
    Get the temporal neurotransmitter service with all dependencies properly injected.
    
    Args:
        subject_repository: Repository for subject identities
        sequence_repository: Repository for temporal sequences
        event_repository: Repository for event tracking
        audit_service: Service for audit logging
        xgboost_service: Service for ML predictions
        
    Returns:
        Configured TemporalNeurotransmitterService
    """
    visualizer = NeurotransmitterVisualizationPreprocessor()
    
    return TemporalNeurotransmitterService(
        sequence_repository=sequence_repository,
        subject_repository=subject_repository,
        event_repository=event_repository,
        visualization_preprocessor=visualizer,
        xgboost_service=xgboost_service,
        audit_service=audit_service,
    )


@router.post("/time-series", response_model=APIResponse)
async def generate_time_series(
    request: GenerateTimeSeriesRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TemporalNeurotransmitterService = Depends(get_service),
) -> APIResponse:
    """
    Generate a temporal sequence for a neurotransmitter in a specific brain region.
    
    Args:
        request: Request parameters for time series generation
        current_user: Current authenticated user
        service: Temporal neurotransmitter service
        
    Returns:
        API response with sequence ID
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Generate time series
        sequence_id = await service.generate_neurotransmitter_time_series(
            subject_id=request.subject_id,
            brain_region=request.brain_region,
            neurotransmitter=request.neurotransmitter,
            time_range_days=request.time_range_days,
            time_step_hours=request.time_step_hours,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Neurotransmitter time series generated successfully",
            data=TimeSeriesResponse(
                sequence_id=sequence_id,
                subject_id=request.subject_id,
                brain_region=request.brain_region,
                neurotransmitter=request.neurotransmitter,
            ),
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating time series: {str(e)}",
        )


@router.post("/analysis", response_model=APIResponse)
async def analyze_neurotransmitter(
    request: NeurotransmitterAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TemporalNeurotransmitterService = Depends(get_service),
) -> APIResponse:
    """
    Analyze neurotransmitter levels for a subject in a specific brain region.
    
    Args:
        request: Request parameters for neurotransmitter analysis
        current_user: Current authenticated user
        service: Temporal neurotransmitter service
        
    Returns:
        API response with analysis results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Perform analysis
        effect = await service.analyze_neurotransmitter_levels(
            subject_id=request.subject_id,
            brain_region=request.brain_region,
            neurotransmitter=request.neurotransmitter,
        )
        
        if not effect:
            return APIResponse(
                success=True,
                message="No data available for analysis",
                data=None,
            )
        
        # Return response
        return APIResponse(
            success=True,
            message="Neurotransmitter analysis completed successfully",
            data=NeurotransmitterEffectResponse(
                subject_id=request.subject_id,
                brain_region=request.brain_region,
                neurotransmitter=request.neurotransmitter,
                effect_size=effect.effect_size,
                p_value=effect.p_value,
                confidence_interval=effect.confidence_interval,
                is_statistically_significant=effect.is_statistically_significant,
                clinical_significance=effect.clinical_significance,
                time_series_data=effect.time_series_data,
            ),
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing neurotransmitter analysis: {str(e)}",
        )


@router.post("/treatment-simulation", response_model=APIResponse)
async def simulate_treatment(
    request: TreatmentSimulationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TemporalNeurotransmitterService = Depends(get_service),
) -> APIResponse:
    """
    Simulate treatment response for a specific neurotransmitter and brain region.
    
    Args:
        request: Request parameters for treatment simulation
        current_user: Current authenticated user
        service: Temporal neurotransmitter service
        
    Returns:
        API response with simulation results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Perform simulation
        sequence_ids = await service.simulate_treatment_response(
            subject_id=request.subject_id,
            brain_region=request.brain_region,
            target_neurotransmitter=request.target_neurotransmitter,
            treatment_effect=request.treatment_effect,
            simulation_days=request.simulation_days,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Treatment simulation completed successfully",
            data=SimulationResultResponse(
                subject_id=request.subject_id,
                brain_region=request.brain_region,
                target_neurotransmitter=request.target_neurotransmitter,
                treatment_effect=request.treatment_effect,
                sequence_ids={nt.value: str(seq_id) for nt, seq_id in sequence_ids.items()},
            ),
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error simulating treatment response: {str(e)}",
        )


@router.get("/sequences/{sequence_id}/visualization", response_model=APIResponse)
async def get_sequence_visualization(
    sequence_id: UUID = Path(..., description="UUID of the sequence"),
    focus_features: Optional[List[str]] = Query(None, description="Features to focus on"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TemporalNeurotransmitterService = Depends(get_service),
) -> APIResponse:
    """
    Get visualization data for a temporal sequence.
    
    Args:
        sequence_id: UUID of the sequence
        focus_features: Optional list of features to focus on
        current_user: Current authenticated user
        service: Temporal neurotransmitter service
        
    Returns:
        API response with visualization data
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get visualization data
        viz_data = await service.get_visualization_data(
            sequence_id=sequence_id,
            focus_features=focus_features,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Visualization data retrieved successfully",
            data=viz_data,
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving visualization data: {str(e)}",
        )


@router.post("/cascade-visualization", response_model=APIResponse)
async def get_cascade_visualization(
    request: CascadeVisualizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TemporalNeurotransmitterService = Depends(get_service),
) -> APIResponse:
    """
    Get visualization data for a neurotransmitter cascade.
    
    Args:
        request: Request parameters for cascade visualization
        current_user: Current authenticated user
        service: Temporal neurotransmitter service
        
    Returns:
        API response with cascade visualization data
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get cascade visualization
        viz_data = await service.get_cascade_visualization(
            subject_id=request.subject_id,
            starting_region=request.starting_region,
            neurotransmitter=request.neurotransmitter,
            time_steps=request.time_steps,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Cascade visualization data retrieved successfully",
            data=VisualizationDataResponse(
                subject_id=request.subject_id,
                visualization_data=viz_data,
            ),
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cascade visualization: {str(e)}",
        )