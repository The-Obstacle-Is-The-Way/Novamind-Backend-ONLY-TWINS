"""
FastAPI routes for actigraphy data analysis.

This module defines the API endpoints for actigraphy data analysis, embedding
generation, and integration with digital twins.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.schemas.actigraphy import (
    AnalysesList,
    AnalysisResult,
    AnalyzeActigraphyRequest,
    EmbeddingResult,
    GetActigraphyEmbeddingsRequest,
    IntegrateWithDigitalTwinRequest,
    IntegrationResult,
)
# Removed incorrect import: from app.core.auth.jwt import get_current_user_id, validate_jwt
# Assuming standard dependency injection setup
from app.presentation.api.dependencies.auth import get_current_user # Corrected import
# Removed incorrect User schema import: from app.presentation.api.schemas.user import User
from typing import Dict, Any # Import Dict and Any for type hinting

from app.core.services.ml.pat import (
    AnalysisError,
    AuthorizationError,
    EmbeddingError,
    InitializationError,
    IntegrationError,
    PATInterface,
    PATServiceFactory,
    ResourceNotFoundError,
    ValidationError,
)

# Set up logging with no PHI
logger = logging.getLogger(__name__)

# Set up router
router = APIRouter(prefix="/actigraphy", tags=["actigraphy"])

# Set up security
security = HTTPBearer()


async def get_pat_service() -> PATInterface:
    """Get an initialized PAT service instance.
    
    This dependency provides a configured PAT service using the service factory.
    The service type is determined by configuration.
    
    Returns:
        An initialized PAT service
        
    Raises:
        HTTPException: If service initialization fails
    """
    try:
        # Create a PAT service using the factory
        # In production, the service type would be determined by configuration
        factory = PATServiceFactory()
        service = factory.create_service("mock")
        
        # Initialize the service
        # In production, configuration would be loaded from env vars or settings
        service.initialize({
            "mock_delay_ms": 100,  # Small delay for realistic behavior
        })
        
        return service
    
    except InitializationError as e:
        logger.error(f"Failed to initialize PAT service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PAT service is currently unavailable"
        )


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze actigraphy data",
    description="Analyze raw actigraphy data to derive physical activity insights."
)
async def analyze_actigraphy(
    request: AnalyzeActigraphyRequest,
    # Replace token dependency with user dependency
    current_user: Dict[str, Any] = Depends(get_current_user), # Corrected type hint
    pat_service: PATInterface = Depends(get_pat_service)
) -> AnalysisResult:
    """Analyze actigraphy data endpoint.
    
    This endpoint processes raw accelerometer data to extract physical activity
    patterns and insights, such as activity levels, sleep patterns, gait
    characteristics, and tremor analysis.
    
    Args:
        request: The analysis request containing the data to analyze
        token: JWT token for authentication
        pat_service: PAT service for analysis
        
    Returns:
        Analysis results
        
    Raises:
        HTTPException: If analysis fails or validation errors occur
    """
    try:
        # Token validation and user retrieval are handled by get_current_active_user dependency
        # Assuming the payload from get_current_user is a dict as per its type hint
        user_id = current_user.get("id") # Get user ID from the injected user dict
        
        # Ensure the user is authorized to access this patient's data
        # This would typically check if the user is the patient, their provider,
        # or has appropriate access rights
        # Here we simply check if the patient_id matches the authenticated user_id
        if user_id != request.patient_id:
            logger.warning(
                f"Unauthorized attempt to access patient data: "
                f"user_id={user_id}, patient_id={request.patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this patient's data"
            )
        
        # Log analysis request (without PHI)
        logger.info(
            f"Analyzing actigraphy data: "
            f"readings_count={len(request.readings)}, "
            f"analysis_types={[at.value for at in request.analysis_types]}"
        )
        
        # Prepare readings for the service
        readings = [reading.model_dump() for reading in request.readings]
        
        # Analyze actigraphy data
        result = pat_service.analyze_actigraphy(
            patient_id=request.patient_id,
            readings=readings,
            start_time=request.start_time,
            end_time=request.end_time,
            sampling_rate_hz=request.sampling_rate_hz,
            device_info=request.device_info.model_dump(),
            analysis_types=[at.value for at in request.analysis_types]
        )
        
        # Log success (without PHI)
        logger.info(
            f"Successfully analyzed actigraphy data: "
            f"analysis_id={result['analysis_id']}"
        )
        
        return result
    
    except ValidationError as e:
        logger.warning(f"Validation error in analyze_actigraphy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except AnalysisError as e:
        logger.error(f"Analysis error in analyze_actigraphy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in analyze_actigraphy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during analysis"
        )


@router.post(
    "/embeddings",
    response_model=EmbeddingResult,
    status_code=status.HTTP_201_CREATED,
    summary="Generate embeddings from actigraphy data",
    description="Generate embeddings from actigraphy data for machine learning models."
)
async def get_actigraphy_embeddings(
    request: GetActigraphyEmbeddingsRequest,
    # Replace token dependency with user dependency
    current_user: Dict[str, Any] = Depends(get_current_user), # Corrected type hint
    pat_service: PATInterface = Depends(get_pat_service)
) -> EmbeddingResult:
    """Generate embeddings from actigraphy data endpoint.
    
    This endpoint processes raw accelerometer data to generate vector embeddings
    that can be used for similarity search, clustering, or as input to other
    machine learning models.
    
    Args:
        request: The embedding request containing the data
        token: JWT token for authentication
        pat_service: PAT service for embedding generation
        
    Returns:
        Embedding results
        
    Raises:
        HTTPException: If embedding generation fails or validation errors occur
    """
    try:
        # Token validation and user retrieval are handled by get_current_active_user dependency
        user_id = current_user.get("id") # Get user ID from the injected user dict
        
        # Ensure the user is authorized to access this patient's data
        if user_id != request.patient_id:
            logger.warning(
                f"Unauthorized attempt to access patient data: "
                f"user_id={user_id}, patient_id={request.patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this patient's data"
            )
        
        # Log embedding request (without PHI)
        logger.info(
            f"Generating actigraphy embeddings: "
            f"readings_count={len(request.readings)}"
        )
        
        # Prepare readings for the service
        readings = [reading.model_dump() for reading in request.readings]
        
        # Generate embeddings
        result = pat_service.get_actigraphy_embeddings(
            patient_id=request.patient_id,
            readings=readings,
            start_time=request.start_time,
            end_time=request.end_time,
            sampling_rate_hz=request.sampling_rate_hz
        )
        
        # Log success (without PHI)
        logger.info(
            f"Successfully generated actigraphy embeddings: "
            f"embedding_id={result['embedding_id']}"
        )
        
        return result
    
    except ValidationError as e:
        logger.warning(f"Validation error in get_actigraphy_embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except EmbeddingError as e:
        logger.error(f"Embedding error in get_actigraphy_embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in get_actigraphy_embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during embedding generation"
        )


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResult,
    summary="Get an analysis by ID",
    description="Retrieve a specific actigraphy analysis by its ID."
)
async def get_analysis_by_id(
    analysis_id: str,
    # Replace token dependency with user dependency
    current_user: Dict[str, Any] = Depends(get_current_user), # Corrected type hint
    pat_service: PATInterface = Depends(get_pat_service)
) -> AnalysisResult:
    """Get an analysis by ID endpoint.
    
    This endpoint retrieves a specific analysis by its unique identifier,
    including all analysis results and metadata.
    
    Args:
        analysis_id: The unique identifier of the analysis
        token: JWT token for authentication
        pat_service: PAT service
        
    Returns:
        The requested analysis
        
    Raises:
        HTTPException: If the analysis is not found or access is denied
    """
    try:
        # Token validation handled by dependency
        # Log request
        logger.info(f"Retrieving analysis: analysis_id={analysis_id}")
        
        # Get the analysis
        result = pat_service.get_analysis_by_id(analysis_id)
        
        user_id = current_user.get("id") # Get user ID from the injected user dict
        
        # Ensure the user is authorized to access this analysis
        if user_id != result["patient_id"]:
            logger.warning(
                f"Unauthorized attempt to access analysis: "
                f"user_id={user_id}, patient_id={result['patient_id']}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this analysis"
            )
        
        # Log success (without PHI)
        logger.info(f"Successfully retrieved analysis: analysis_id={analysis_id}")
        
        return result
    
    except ResourceNotFoundError as e:
        logger.warning(f"Analysis not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found: {analysis_id}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in get_analysis_by_id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the analysis"
        )


@router.get(
    "/patient/{patient_id}/analyses",
    response_model=AnalysesList,
    summary="Get analyses for a patient",
    description="Retrieve a list of actigraphy analyses for a specific patient."
)
async def get_patient_analyses(
    patient_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    # Replace token dependency with user dependency
    current_user: Dict[str, Any] = Depends(get_current_user), # Corrected type hint
    pat_service: PATInterface = Depends(get_pat_service)
) -> AnalysesList:
    """Get analyses for a patient endpoint.
    
    This endpoint retrieves a paginated list of analyses for a specific patient,
    including summary information for each analysis.
    
    Args:
        patient_id: The patient's unique identifier
        limit: Maximum number of analyses to return
        offset: Offset for pagination
        token: JWT token for authentication
        pat_service: PAT service
        
    Returns:
        Paginated list of analyses
        
    Raises:
        HTTPException: If access is denied or an error occurs
    """
    try:
        # Token validation and user retrieval are handled by get_current_active_user dependency
        user_id = current_user.get("id") # Get user ID from the injected user dict
        
        # Ensure the user is authorized to access this patient's data
        if user_id != patient_id:
            logger.warning(
                f"Unauthorized attempt to access patient analyses: "
                f"user_id={user_id}, patient_id={patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this patient's analyses"
            )
        
        # Log request (without PHI)
        logger.info(
            f"Retrieving patient analyses: "
            f"limit={limit}, offset={offset}"
        )
        
        # Get the analyses
        result = pat_service.get_patient_analyses(
            patient_id=patient_id,
            limit=limit,
            offset=offset
        )
        
        # Log success (without PHI)
        logger.info(
            f"Successfully retrieved patient analyses: "
            f"count={len(result['analyses'])}"
        )
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in get_patient_analyses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving analyses"
        )


@router.get(
    "/model-info",
    response_model=dict,
    summary="Get PAT model information",
    description="Retrieve information about the PAT model being used."
)
async def get_model_info(
    # Replace token dependency with user dependency
    current_user: Dict[str, Any] = Depends(get_current_user), # Corrected type hint
    pat_service: PATInterface = Depends(get_pat_service)
) -> dict:
    """Get PAT model information endpoint.
    
    This endpoint retrieves information about the PAT model being used,
    including its capabilities, version, and other metadata.
    
    Args:
        token: JWT token for authentication
        pat_service: PAT service
        
    Returns:
        Model information
        
    Raises:
        HTTPException: If an error occurs
    """
    try:
        # Token validation handled by dependency
        # Log request
        logger.info("Retrieving PAT model information")
        
        # Get model info
        result = pat_service.get_model_info()
        
        # Log success
        logger.info("Successfully retrieved PAT model information")
        
        return result
    
    except Exception as e:
        logger.error(f"Unexpected error in get_model_info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving model information"
        )


@router.post(
    "/integrate-with-digital-twin",
    response_model=IntegrationResult,
    status_code=status.HTTP_201_CREATED,
    summary="Integrate with Digital Twin",
    description="Integrate actigraphy analysis with a digital twin profile."
)
async def integrate_with_digital_twin(
    request: IntegrateWithDigitalTwinRequest,
    # Replace token dependency with user dependency
    current_user: Dict[str, Any] = Depends(get_current_user), # Corrected type hint
    pat_service: PATInterface = Depends(get_pat_service)
) -> IntegrationResult:
    """Integrate with digital twin endpoint.
    
    This endpoint integrates actigraphy analysis results with a digital twin
    profile, providing insights and updating the digital twin model based on
    physical activity data.
    
    Args:
        request: The integration request
        token: JWT token for authentication
        pat_service: PAT service
        
    Returns:
        Integration results
        
    Raises:
        HTTPException: If integration fails or validation errors occur
    """
    try:
        # Token validation and user retrieval are handled by get_current_active_user dependency
        user_id = current_user.get("id") # Get user ID from the injected user dict
        
        # Ensure the user is authorized to access this patient's data
        if user_id != request.patient_id:
            logger.warning(
                f"Unauthorized attempt to integrate with digital twin: "
                f"user_id={user_id}, patient_id={request.patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to integrate with this patient's digital twin"
            )
        
        # Log integration request (without PHI)
        logger.info(
            f"Integrating with Digital Twin: "
            f"profile_id={request.profile_id}, "
            f"analysis_id={request.analysis_id}"
        )
        
        # Integrate with digital twin
        result = pat_service.integrate_with_digital_twin(
            patient_id=request.patient_id,
            profile_id=request.profile_id,
            analysis_id=request.analysis_id
        )
        
        # Log success (without PHI)
        logger.info(
            f"Successfully integrated with Digital Twin: "
            f"integration_id={result['integration_id']}"
        )
        
        return result
    
    except ValidationError as e:
        logger.warning(f"Validation error in integrate_with_digital_twin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in integrate_with_digital_twin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except AuthorizationError as e:
        logger.warning(f"Authorization error in integrate_with_digital_twin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    except IntegrationError as e:
        logger.error(f"Integration error in integrate_with_digital_twin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integration failed: {str(e)}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in integrate_with_digital_twin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during integration"
        )