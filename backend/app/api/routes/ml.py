# -*- coding: utf-8 -*-
"""
ML API Routes.

This module defines FastAPI routes for ML services.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.deps import get_current_user, require_clinician_role
from app.api.schemas.ml import (
    CreateSessionRequest,
    CreateSessionResponse,
    DepressionDetectionRequest,
    DepressionDetectionResponse,
    DigitalTwinMessage,
    DigitalTwinSessionType,
    EndSessionRequest,
    EndSessionResponse,
    GenerateDigitalTwinRequest,
    GenerateDigitalTwinResponse,
    GetInsightsRequest,
    GetInsightsResponse,
    GetSessionResponse,
    InsightType,
    MentaLLaMAModelType,
    MentaLLaMAProcessRequest,
    MentaLLaMAProcessResponse,
    PHIDetectionRequest,
    PHIDetectionResponse,
    PHIRedactionRequest,
    PHIRedactionResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    SenderType,
    SendMessageRequest,
    SendMessageResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    ServiceHealthResponse,
    WellnessAnalysisRequest,
    WellnessAnalysisResponse,
)
from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)
from app.core.services.ml.factory import MLServiceCache # Import the correct cache
from app.core.services.ml.interface import MentaLLaMAInterface, PHIDetectionInterface
from app.core.utils.logging import get_logger


# Create logger (no PHI logging)
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/ml", tags=["ML"])


# ---- Service Dependencies ----

def get_mentalllama_service() -> MentaLLaMAInterface:
    """
    Get MentaLLaMA service instance as a FastAPI dependency.
    
    Returns:
        MentaLLaMA service
        
    Raises:
        HTTPException: If service is unavailable
    """
    try:
        # Use the MLServiceCache singleton to get the service
        return MLServiceCache.get_instance().get_mentalllama_service()
    except ServiceUnavailableError as e:
        logger.error(f"Failed to get MentaLLaMA service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )


def get_phi_detection_service() -> PHIDetectionInterface:
    """
    Get PHI detection service instance as a FastAPI dependency.
    
    Returns:
        PHI detection service
        
    Raises:
        HTTPException: If service is unavailable
    """
    try:
        # Use the MLServiceCache singleton to get the service
        return MLServiceCache.get_instance().get_phi_detection_service()
    except ServiceUnavailableError as e:
        logger.error(f"Failed to get PHI detection service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PHI detection service is unavailable"
        )


# ---- Health Check Routes ----

@router.get("/mentalllama/health", response_model=ServiceHealthResponse)
async def mentalllama_health_check(
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> ServiceHealthResponse:
    """
    Check the health of the MentaLLaMA service.
    
    Args:
        service: MentaLLaMA service
        
    Returns:
        Health status
    """
    from datetime import datetime, UTC, UTC
    
    is_healthy = service.is_healthy()
    timestamp = datetime.now(UTC).isoformat() + "Z"
    
    return ServiceHealthResponse(
        is_healthy=is_healthy,
        timestamp=timestamp
    )


@router.get("/phi/health", response_model=ServiceHealthResponse)
async def phi_health_check(
    service: PHIDetectionInterface = Depends(get_phi_detection_service)
) -> ServiceHealthResponse:
    """
    Check the health of the PHI detection service.
    
    Args:
        service: PHI detection service
        
    Returns:
        Health status
    """
    from datetime import datetime, UTC, UTC
    
    is_healthy = service.is_healthy()
    timestamp = datetime.now(UTC).isoformat() + "Z"
    
    return ServiceHealthResponse(
        is_healthy=is_healthy,
        timestamp=timestamp
    )


# ---- MentaLLaMA Processing Routes ----

@router.post("/mentalllama/process", response_model=MentaLLaMAProcessResponse)
async def process_text(
    request: MentaLLaMAProcessRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> MentaLLaMAProcessResponse:
    """
    Process text using the MentaLLaMA model.
    
    Args:
        request: Processing request
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Processing results
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Process text
        result = service.process(
            text=request.text,
            model_type=request.model_type.value if request.model_type else None,
            options=request.options
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid MentaLLaMA processing request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelNotFoundError as e:
        logger.warning(f"MentaLLaMA model not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in MentaLLaMA processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/depression", response_model=DepressionDetectionResponse)
async def detect_depression(
    request: DepressionDetectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> DepressionDetectionResponse:
    """
    Detect depression signals in text.
    
    Args:
        request: Depression detection request
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Depression detection results
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Detect depression
        result = service.detect_depression(
            text=request.text,
            options=request.options
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid depression detection request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for depression detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in depression detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/risk", response_model=RiskAssessmentResponse)
async def assess_risk(
    request: RiskAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> RiskAssessmentResponse:
    """
    Assess risk in text.
    
    Args:
        request: Risk assessment request
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Risk assessment results
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Assess risk
        result = service.assess_risk(
            text=request.text,
            risk_type=request.risk_type.value if request.risk_type else None,
            options=request.options
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid risk assessment request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for risk assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in risk assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/sentiment", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> SentimentAnalysisResponse:
    """
    Analyze sentiment in text.
    
    Args:
        request: Sentiment analysis request
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Sentiment analysis results
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Analyze sentiment
        result = service.analyze_sentiment(
            text=request.text,
            options=request.options
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid sentiment analysis request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for sentiment analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in sentiment analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/wellness", response_model=WellnessAnalysisResponse)
async def analyze_wellness_dimensions(
    request: WellnessAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> WellnessAnalysisResponse:
    """
    Analyze wellness dimensions in text.
    
    Args:
        request: Wellness dimensions analysis request
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Wellness dimensions analysis results
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Analyze wellness dimensions
        result = service.analyze_wellness_dimensions(
            text=request.text,
            dimensions=[d.value for d in request.dimensions] if request.dimensions else None,
            options=request.options
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid wellness dimensions analysis request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for wellness dimensions analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in wellness dimensions analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# ---- PHI Detection Routes ----

@router.post("/phi/detect", response_model=PHIDetectionResponse)
async def detect_phi(
    request: PHIDetectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: PHIDetectionInterface = Depends(get_phi_detection_service)
) -> PHIDetectionResponse:
    """
    Detect PHI in text.
    
    Args:
        request: PHI detection request
        current_user: Current authenticated user
        service: PHI detection service
        
    Returns:
        PHI detection results
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Detect PHI
        result = service.detect_phi(
            text=request.text,
            detection_level=request.detection_level.value if request.detection_level else None
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid PHI detection request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"PHI detection service unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PHI detection service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in PHI detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/phi/redact", response_model=PHIRedactionResponse)
async def redact_phi(
    request: PHIRedactionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: PHIDetectionInterface = Depends(get_phi_detection_service)
) -> PHIRedactionResponse:
    """
    Redact PHI from text.
    
    Args:
        request: PHI redaction request
        current_user: Current authenticated user
        service: PHI detection service
        
    Returns:
        PHI redaction results
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Redact PHI
        result = service.redact_phi(
            text=request.text,
            replacement=request.replacement,
            detection_level=request.detection_level.value if request.detection_level else None
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid PHI redaction request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"PHI detection service unavailable for redaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PHI detection service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in PHI redaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# ---- Digital Twin Routes ----

@router.post("/mentalllama/digital-twin", response_model=GenerateDigitalTwinResponse)
async def generate_digital_twin(
    request: GenerateDigitalTwinRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> GenerateDigitalTwinResponse:
    """
    Generate or update a digital twin model for a patient.
    
    This endpoint creates or updates a personalized digital twin model for a patient
    based on their clinical history, assessments, and other relevant data.
    
    Args:
        request: Digital twin request containing patient data
        current_user: Current authenticated user (must be a clinician)
        service: MentaLLaMA service
        
    Returns:
        Digital twin model data and metrics
        
    Raises:
        HTTPException: If request is invalid, permissions are insufficient, or service is unavailable
    """
    # Only clinicians can create digital twins
    require_clinician_role(current_user)
    
    try:
        # Generate or update digital twin
        result = service.generate_digital_twin(
            patient_id=request.patient_id,
            patient_data=request.patient_data,
            options=request.options
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid digital twin request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for digital twin generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in digital twin generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> CreateSessionResponse:
    """
    Create a new Digital Twin session.
    
    Args:
        request: Session creation request
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Created session details
        
    Raises:
        HTTPException: If request is invalid or service is unavailable
    """
    try:
        # Create session
        result = service.create_digital_twin_session(
            therapist_id=request.therapist_id,
            patient_id=request.patient_id,
            session_type=request.session_type.value if request.session_type else None,
            session_params=request.session_params
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid session creation request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for session creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in session creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/mentalllama/sessions/{session_id}", response_model=GetSessionResponse)
async def get_session(
    session_id: str = Path(..., description="ID of the session"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> GetSessionResponse:
    """
    Get details of an existing Digital Twin session.
    
    Args:
        session_id: ID of the session to retrieve
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Session details
        
    Raises:
        HTTPException: If session not found or service is unavailable
    """
    try:
        # Get session
        result = service.get_digital_twin_session(session_id=session_id)
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid session request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelNotFoundError as e:
        logger.warning(f"Session not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for session retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in session retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    session_id: str = Path(..., description="ID of the session"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> SendMessageResponse:
    """
    Send a message to a Digital Twin session.
    
    Args:
        request: Message request
        session_id: ID of the session
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Message response
        
    Raises:
        HTTPException: If request is invalid, session not found, or service is unavailable
    """
    try:
        # Ensure session_id consistency
        if request.session_id != session_id:
            raise InvalidRequestError("session_id in URL must match session_id in request body")
        
        # Send message
        result = service.send_message_to_session(
            session_id=session_id,
            message=request.message,
            sender_type=request.sender_type.value if request.sender_type else None,
            sender_id=request.sender_id,
            message_params=request.message_params
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid message request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelNotFoundError as e:
        logger.warning(f"Session not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for message sending: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in message sending: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/sessions/{session_id}/end", response_model=EndSessionResponse)
async def end_session(
    request: EndSessionRequest,
    session_id: str = Path(..., description="ID of the session"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> EndSessionResponse:
    """
    End a Digital Twin session.
    
    Args:
        request: End session request
        session_id: ID of the session
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        End session response
        
    Raises:
        HTTPException: If request is invalid, session not found, or service is unavailable
    """
    try:
        # Ensure session_id consistency
        if request.session_id != session_id:
            raise InvalidRequestError("session_id in URL must match session_id in request body")
        
        # End session
        result = service.end_digital_twin_session(
            session_id=session_id,
            end_reason=request.end_reason
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid end session request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelNotFoundError as e:
        logger.warning(f"Session not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for ending session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in ending session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/mentalllama/sessions/{session_id}/insights", response_model=GetInsightsResponse)
async def get_insights(
    request: GetInsightsRequest,
    session_id: str = Path(..., description="ID of the session"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MentaLLaMAInterface = Depends(get_mentalllama_service)
) -> GetInsightsResponse:
    """
    Get insights from a Digital Twin session.
    
    Args:
        request: Get insights request
        session_id: ID of the session
        current_user: Current authenticated user
        service: MentaLLaMA service
        
    Returns:
        Session insights
        
    Raises:
        HTTPException: If request is invalid, session not found, or service is unavailable
    """
    try:
        # Ensure session_id consistency
        if request.session_id != session_id:
            raise InvalidRequestError("session_id in URL must match session_id in request body")
        
        # Get insights
        result = service.get_session_insights(
            session_id=session_id,
            insight_type=request.insight_type.value if request.insight_type else None
        )
        
        return result
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid get insights request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelNotFoundError as e:
        logger.warning(f"Session not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceUnavailableError as e:
        logger.error(f"MentaLLaMA service unavailable for retrieving insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in retrieving insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )