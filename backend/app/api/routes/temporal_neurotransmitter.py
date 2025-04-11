"""
API endpoints for the temporal neurotransmitter system.

This module provides FastAPI routes for the temporal neurotransmitter system,
enabling access to time-series neurotransmitter data, analysis, and visualization.
"""
import importlib
import inspect
import functools
from typing import Dict, List, Optional, Union, cast, Any, Callable, TypeVar, Generic
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user_dict
from app.api.dependencies.response import ensure_serializable_response, prevent_session_exposure
from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter

# Type for avoiding FastAPI schema generation of complex types
T = TypeVar('T')

# Prevent module-level imports from causing FastAPI to analyze our dependencies
# By using a completely isolated dependency resolver that FastAPI never sees
class LazyDependency(Generic[T]):
    """
    Lazy dependency loader that completely isolates dependency chains from FastAPI.
    
    This implementation ensures FastAPI never attempts to analyze the dependency
    chain, preventing AsyncSession from appearing in response models.
    """
    
    def __init__(self, module_path: str, dependency_name: str):
        self.module_path = module_path
        self.dependency_name = dependency_name
        self._dependency = None
        self._service_instance = None
    
    async def __call__(self) -> T:
        """
        Get the service instance without FastAPI ever seeing the dependency chain.
        
        This is done by directly importing and calling the dependency function,
        completely bypassing FastAPI's dependency injection system.
        """
        if self._dependency is None:
            module = importlib.import_module(self.module_path)
            self._dependency = getattr(module, self.dependency_name)
        
        if self._service_instance is None:
            # Import DB session at runtime to avoid FastAPI analyzing it
            from app.infrastructure.persistence.sqlalchemy.config.database import get_db_session as get_session_from_config
            from sqlalchemy.ext.asyncio import AsyncSession
            
            # Get a database session directly, not through FastAPI
            session_gen = get_session_from_config()
            session = None
            async for db_session in session_gen:
                session = db_session
                break
                
            if not session:
                raise RuntimeError("Failed to obtain database session")
            
            # Import repositories at runtime
            from app.infrastructure.repositories.temporal_event_repository import SqlAlchemyEventRepository
            from app.infrastructure.repositories.temporal_sequence_repository import SqlAlchemyTemporalSequenceRepository
            
            # Create repositories directly
            seq_repo = SqlAlchemyTemporalSequenceRepository(session=session)
            event_repo = SqlAlchemyEventRepository(session=session)
            
            # Import XGBoost service
            from app.domain.services.enhanced_xgboost_service import EnhancedXGBoostService
            xgboost_service = EnhancedXGBoostService()
            
            # Import the service class directly
            from app.application.services.temporal_neurotransmitter_service import TemporalNeurotransmitterService
            
            # Create the service instance directly
            self._service_instance = TemporalNeurotransmitterService(
                sequence_repository=seq_repo,
                event_repository=event_repo,
                xgboost_service=xgboost_service
            )
            
        return self._service_instance

# Create a completely isolated service factory
_get_neurotransmitter_service = LazyDependency(
    'app.api.dependencies.services',
    'get_temporal_neurotransmitter_service'
)

# Create the router with explicit response_model=None to prevent type inspection
router = APIRouter(
    prefix="/api/v1/temporal-neurotransmitter",
    tags=["temporal-neurotransmitter"],
)


# Request/response models
class TimeSeriesGenerateRequest(BaseModel):
    """Request model for generating time series data."""
    patient_id: UUID
    brain_region: BrainRegion
    neurotransmitter: Neurotransmitter
    time_range_days: int = 14
    time_step_hours: int = 6


class TimeSeriesResponse(BaseModel):
    """Response model for time series generation."""
    sequence_id: UUID
    patient_id: UUID
    brain_region: str
    neurotransmitter: str
    time_range_days: int
    time_step_hours: int


class AnalyzeNeurotransmitterRequest(BaseModel):
    """Request model for analyzing neurotransmitter levels."""
    patient_id: UUID
    brain_region: BrainRegion
    neurotransmitter: Neurotransmitter


class NeurotransmitterEffectResponse(BaseModel):
    """Response model for neurotransmitter effect analysis."""
    neurotransmitter: str
    brain_region: str
    effect_size: float
    confidence_interval: Optional[tuple[float, float]] = None
    p_value: Optional[float] = None
    is_statistically_significant: bool
    clinical_significance: Optional[str] = None
    time_series_data: List[List[Union[str, float]]]
    comparison_periods: Dict[str, List[str]]


class TreatmentSimulationRequest(BaseModel):
    """Request model for treatment simulation."""
    patient_id: UUID
    brain_region: BrainRegion
    target_neurotransmitter: Neurotransmitter
    treatment_effect: float
    simulation_days: int = 14


class TreatmentSimulationResponse(BaseModel):
    """Response model for treatment simulation."""
    sequence_ids: Dict[str, UUID]
    patient_id: UUID
    brain_region: str
    target_neurotransmitter: str
    treatment_effect: float
    simulation_days: int


class VisualizationDataRequest(BaseModel):
    """Request model for visualization data."""
    sequence_id: UUID
    focus_features: Optional[List[str]] = None


class VisualizationDataResponse(BaseModel):
    """Response model for visualization data."""
    time_points: List[str]
    features: List[str]
    values: List[List[float]]
    metadata: Optional[Dict] = None


class CascadeVisualizationRequest(BaseModel):
    """Request model for cascade visualization."""
    patient_id: UUID
    starting_region: BrainRegion
    neurotransmitter: Neurotransmitter
    time_steps: int = 3


class CascadeVisualizationResponse(BaseModel):
    """Response model for cascade visualization."""
    nodes: List[Dict]
    connections: List[Dict]
    time_steps: List[Dict]
    metadata: Optional[Dict] = None


class TimeSeriesGenerateResponse(BaseModel):
    """Response model for generating a neurotransmitter time series."""
    sequence_id: UUID
    patient_id: UUID
    brain_region: str
    neurotransmitter: str
    time_range_days: int
    time_step_hours: int


class AnalysisResponse(BaseModel):
    """Response model for neurotransmitter analysis."""
    neurotransmitter: str
    brain_region: str
    effect_size: float
    confidence_interval: Optional[List[float]]
    p_value: Optional[float]
    is_statistically_significant: bool
    clinical_significance: Optional[str]
    time_series_data: List[List[Union[str, float]]]
    comparison_periods: Dict[str, List[str]]


@router.post(
    "/time-series",
    response_model=TimeSeriesGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate neurotransmitter time series",
    description="Generate time series data for a specific neurotransmitter in a brain region.",
)
async def generate_time_series(
    request: TimeSeriesGenerateRequest,
    current_user: Dict = Depends(get_current_user_dict),
    _: Dict = Depends(prevent_session_exposure),
):
    """
    Generate neurotransmitter time series data.
    
    This endpoint generates time series data for a specific neurotransmitter
    in a specific brain region for a given patient.
    """
    # Use the lazy dependency to get the service at runtime
    # This completely prevents FastAPI from analyzing the dependency chain
    service = await _get_neurotransmitter_service()()
    
    sequence_id = await service.generate_neurotransmitter_time_series(
        patient_id=request.patient_id,
        brain_region=request.brain_region,
        neurotransmitter=request.neurotransmitter,
        time_range_days=request.time_range_days,
        time_step_hours=request.time_step_hours
    )
    
    response_data = {
        "sequence_id": sequence_id,
        "patient_id": request.patient_id,
        "brain_region": request.brain_region.value,
        "neurotransmitter": request.neurotransmitter.value,
        "time_range_days": request.time_range_days,
        "time_step_hours": request.time_step_hours
    }
    
    return ensure_serializable_response(response_data)


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze neurotransmitter levels",
    description="Analyze neurotransmitter levels for a specific patient, brain region, and neurotransmitter.",
)
async def analyze_neurotransmitter(
    request: AnalyzeNeurotransmitterRequest,
    current_user: Dict = Depends(get_current_user_dict),
    _: Dict = Depends(prevent_session_exposure),
):
    """
    Analyze neurotransmitter levels.
    
    This endpoint analyzes the neurotransmitter levels for a specific
    brain region and neurotransmitter for a given patient.
    """
    # Use the lazy dependency to get the service at runtime
    service = await _get_neurotransmitter_service()()
    
    effect = await service.analyze_patient_neurotransmitter_levels(
        patient_id=request.patient_id,
        brain_region=request.brain_region,
        neurotransmitter=request.neurotransmitter
    )
    
    if not effect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for patient {request.patient_id} with {request.neurotransmitter.value} in {request.brain_region.value}"
        )
    
    # Format time series data for JSON response
    time_series_data = [
        [ts.strftime("%Y-%m-%dT%H:%M:%S"), value]
        for ts, value in effect.time_series_data
    ]
    
    # Format comparison periods
    comparison_periods = {}
    if effect.baseline_period:
        comparison_periods["baseline"] = [
            effect.baseline_period[0].strftime("%Y-%m-%dT%H:%M:%S"),
            effect.baseline_period[1].strftime("%Y-%m-%dT%H:%M:%S")
        ]
    if effect.comparison_period:
        comparison_periods["comparison"] = [
            effect.comparison_period[0].strftime("%Y-%m-%dT%H:%M:%S"),
            effect.comparison_period[1].strftime("%Y-%m-%dT%H:%M:%S")
        ]
    
    response_data = {
        "neurotransmitter": effect.neurotransmitter.value,
        "brain_region": effect.brain_region.value,
        "effect_size": effect.effect_size,
        "confidence_interval": effect.confidence_interval,
        "p_value": effect.p_value,
        "is_statistically_significant": effect.p_value is not None and effect.p_value < 0.05,
        "clinical_significance": effect.clinical_significance.value if effect.clinical_significance else None,
        "time_series_data": time_series_data,
        "comparison_periods": comparison_periods
    }
    return ensure_serializable_response(response_data)


@router.post(
    "/simulate-treatment",
    response_model=TreatmentSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate treatment response",
    description="Simulate treatment response for a specific patient, brain region, and neurotransmitter.",
)
async def simulate_treatment(
    request: TreatmentSimulationRequest,
    current_user: Dict = Depends(get_current_user_dict),
    _: Dict = Depends(prevent_session_exposure),
):
    """
    Simulate treatment response.
    
    This endpoint simulates the response to a treatment that targets
    a specific neurotransmitter in a specific brain region for a given patient.
    """
    # Use the lazy dependency to get the service at runtime
    service = await _get_neurotransmitter_service()()
    
    sequence_ids = await service.simulate_treatment_response(
        patient_id=request.patient_id,
        brain_region=request.brain_region,
        target_neurotransmitter=request.target_neurotransmitter,
        treatment_effect=request.treatment_effect,
        simulation_days=request.simulation_days
    )
    
    response_data = {
        "sequence_ids": {key.value: sequence_id for key, sequence_id in sequence_ids.items()},
        "patient_id": request.patient_id,
        "brain_region": request.brain_region.value,
        "target_neurotransmitter": request.target_neurotransmitter.value,
        "treatment_effect": request.treatment_effect,
        "simulation_days": request.simulation_days
    }
    return ensure_serializable_response(response_data)


@router.post(
    "/visualization-data",
    response_model=VisualizationDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get visualization data",
    description="Get visualization data for a specific sequence.",
)
async def get_visualization_data(
    request: VisualizationDataRequest,
    current_user: Dict = Depends(get_current_user_dict),
    _: Dict = Depends(prevent_session_exposure),
):
    """
    Get visualization data.
    
    This endpoint gets visualization data for a specific sequence.
    """
    # Use the lazy dependency to get the service at runtime
    service = await _get_neurotransmitter_service()()
    
    data = await service.get_visualization_data(
        sequence_id=request.sequence_id,
        focus_features=request.focus_features
    )
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for sequence {request.sequence_id}"
        )
    
    return ensure_serializable_response(data)


@router.post(
    "/cascade-visualization",
    response_model=CascadeVisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cascade visualization",
    description="Get cascade visualization for a specific patient, starting region, and neurotransmitter.",
)
async def get_cascade_visualization(
    request: CascadeVisualizationRequest,
    current_user: Dict = Depends(get_current_user_dict),
    _: Dict = Depends(prevent_session_exposure),
):
    """
    Get cascade visualization.
    
    This endpoint gets cascade visualization data showing how effects
    propagate through connected brain regions over time.
    """
    # Use the lazy dependency to get the service at runtime
    service = await _get_neurotransmitter_service()()
    
    data = await service.get_cascade_visualization(
        patient_id=request.patient_id,
        starting_region=request.starting_region,
        neurotransmitter=request.neurotransmitter,
        time_steps=request.time_steps
    )
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cascade data found for patient {request.patient_id} with {request.neurotransmitter.value} in {request.starting_region.value}"
        )
    return ensure_serializable_response(data)