# -*- coding: utf-8 -*-
"""
ML Service API Routes.

This module defines the FastAPI routes for the ML services.
"""

from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Security

from app.api.auth.jwt import verify_token, get_current_user
from app.api.deps import get_ml_service_factory
from app.api.schemas.ml_schemas import (
    APIResponse,
    ProcessTextRequest,
    DepressionDetectionRequest,
    RiskAssessmentRequest,
    SentimentAnalysisRequest,
    WellnessDimensionsRequest,
    DigitalTwinConversationRequest,
    PHIDetectionRequest,
    PHIRedactionRequest,
    DigitalTwinSessionCreateRequest,
    DigitalTwinMessageRequest,
    DigitalTwinInsightsRequest,
)
from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)
from app.core.services.ml.factory import MLServiceFactory
from app.core.utils.logging import get_logger


# Create logger (no PHI logging)
logger = get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/ml",
    tags=["Machine Learning"],
    dependencies=[Security(verify_token, scopes=["ml:read", "ml:write"])],
)


@router.post("/process", response_model=APIResponse)
async def process_text(
    request: ProcessTextRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Process text with MentaLLaMA.
    
    Args:
        request: Process text request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with processing results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get MentaLLaMA service
        service = ml_factory.get_mentalllama_service()
        
        # Process text
        result = service.process(
            prompt=request.prompt,
            model=request.model,
            task=request.task,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Text processed successfully",
            data=result,
        )
        
    except ModelNotFoundError as e:
        logger.error(f"Model not found error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(e)}",
        )
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text: {str(e)}",
        )


@router.post("/depression-detection", response_model=APIResponse)
async def depression_detection(
    request: DepressionDetectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Perform depression detection analysis on text.
    
    Args:
        request: Depression detection request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with depression detection results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get MentaLLaMA service
        service = ml_factory.get_mentalllama_service()
        
        # Perform depression detection
        result = service.depression_detection(
            text=request.text,
            model=request.model,
            include_rationale=request.include_rationale,
            severity_assessment=request.severity_assessment,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Depression detection completed successfully",
            data=result,
        )
        
    except ModelNotFoundError as e:
        logger.error(f"Model not found error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(e)}",
        )
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error performing depression detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing depression detection: {str(e)}",
        )


@router.post("/risk-assessment", response_model=APIResponse)
async def risk_assessment(
    request: RiskAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Perform risk assessment analysis on text.
    
    Args:
        request: Risk assessment request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with risk assessment results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get MentaLLaMA service
        service = ml_factory.get_mentalllama_service()
        
        # Perform risk assessment
        result = service.risk_assessment(
            text=request.text,
            model=request.model,
            include_key_phrases=request.include_key_phrases,
            include_suggested_actions=request.include_suggested_actions,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Risk assessment completed successfully",
            data=result,
        )
        
    except ModelNotFoundError as e:
        logger.error(f"Model not found error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(e)}",
        )
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error performing risk assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing risk assessment: {str(e)}",
        )


@router.post("/sentiment-analysis", response_model=APIResponse)
async def sentiment_analysis(
    request: SentimentAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Perform sentiment analysis on text.
    
    Args:
        request: Sentiment analysis request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with sentiment analysis results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get MentaLLaMA service
        service = ml_factory.get_mentalllama_service()
        
        # Perform sentiment analysis
        result = service.sentiment_analysis(
            text=request.text,
            model=request.model,
            include_emotion_distribution=request.include_emotion_distribution,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Sentiment analysis completed successfully",
            data=result,
        )
        
    except ModelNotFoundError as e:
        logger.error(f"Model not found error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(e)}",
        )
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error performing sentiment analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing sentiment analysis: {str(e)}",
        )


@router.post("/wellness-dimensions", response_model=APIResponse)
async def wellness_dimensions(
    request: WellnessDimensionsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Perform wellness dimensions analysis on text.
    
    Args:
        request: Wellness dimensions request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with wellness dimensions analysis results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get MentaLLaMA service
        service = ml_factory.get_mentalllama_service()
        
        # Perform wellness dimensions analysis
        result = service.wellness_dimensions(
            text=request.text,
            model=request.model,
            dimensions=request.dimensions,
            include_recommendations=request.include_recommendations,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Wellness dimensions analysis completed successfully",
            data=result,
        )
        
    except ModelNotFoundError as e:
        logger.error(f"Model not found error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(e)}",
        )
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error performing wellness dimensions analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing wellness dimensions analysis: {str(e)}",
        )


@router.post("/digital-twin/conversation", response_model=APIResponse)
async def digital_twin_conversation(
    request: DigitalTwinConversationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Conduct a conversation with a patient's digital twin.
    
    Args:
        request: Digital twin conversation request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with digital twin conversation results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get MentaLLaMA service
        service = ml_factory.get_mentalllama_service()
        
        # Conduct digital twin conversation
        result = service.digital_twin_conversation(
            prompt=request.prompt,
            patient_id=request.patient_id,
            session_id=request.session_id,
            model=request.model,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Digital twin conversation processed successfully",
            data=result,
        )
        
    except ModelNotFoundError as e:
        logger.error(f"Model not found error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(e)}",
        )
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error conducting digital twin conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error conducting digital twin conversation: {str(e)}",
        )


@router.post("/phi/detect", response_model=APIResponse)
async def detect_phi(
    request: PHIDetectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Detect PHI in text.
    
    Args:
        request: PHI detection request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with PHI detection results
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get PHI detection service
        service = ml_factory.get_phi_detection_service()
        
        # Detect PHI
        result = service.detect_phi(
            text=request.text,
            detection_level=request.detection_level,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="PHI detection completed successfully",
            data=result,
        )
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error detecting PHI: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting PHI: {str(e)}",
        )


@router.post("/phi/redact", response_model=APIResponse)
async def redact_phi(
    request: PHIRedactionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Redact PHI from text.
    
    Args:
        request: PHI redaction request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with redacted text and metadata
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get PHI detection service
        service = ml_factory.get_phi_detection_service()
        
        # Redact PHI
        result = service.redact_phi(
            text=request.text,
            replacement=request.replacement,
            detection_level=request.detection_level,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="PHI redaction completed successfully",
            data=result,
        )
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error redacting PHI: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error redacting PHI: {str(e)}",
        )


@router.post("/digital-twin/sessions", response_model=APIResponse)
async def create_digital_twin_session(
    request: DigitalTwinSessionCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Create a new Digital Twin session.
    
    Args:
        request: Digital twin session create request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with session information
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get Digital Twin service
        service = ml_factory.get_digital_twin_service()
        
        # Create session
        result = service.create_session(
            patient_id=request.patient_id,
            context=request.context,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Digital Twin session created successfully",
            data=result,
        )
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error creating Digital Twin session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating Digital Twin session: {str(e)}",
        )


@router.get("/digital-twin/sessions/{session_id}", response_model=APIResponse)
async def get_digital_twin_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Get Digital Twin session information.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with session information
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get Digital Twin service
        service = ml_factory.get_digital_twin_service()
        
        # Get session
        result = service.get_session(
            session_id=session_id,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Digital Twin session retrieved successfully",
            data=result,
        )
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error retrieving Digital Twin session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Digital Twin session: {str(e)}",
        )


@router.post("/digital-twin/sessions/{session_id}/messages", response_model=APIResponse)
async def send_digital_twin_message(
    session_id: str,
    request: DigitalTwinMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Send a message to the Digital Twin.
    
    Args:
        session_id: Session ID
        request: Digital twin message request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with Digital Twin response
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get Digital Twin service
        service = ml_factory.get_digital_twin_service()
        
        # Send message
        result = service.send_message(
            session_id=session_id,
            message=request.message,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Message sent to Digital Twin successfully",
            data=result,
        )
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error sending message to Digital Twin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message to Digital Twin: {str(e)}",
        )


@router.delete("/digital-twin/sessions/{session_id}", response_model=APIResponse)
async def end_digital_twin_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    End a Digital Twin session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with session end confirmation
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get Digital Twin service
        service = ml_factory.get_digital_twin_service()
        
        # End session
        result = service.end_session(
            session_id=session_id,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Digital Twin session ended successfully",
            data=result,
        )
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error ending Digital Twin session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ending Digital Twin session: {str(e)}",
        )


@router.post("/digital-twin/insights", response_model=APIResponse)
async def get_digital_twin_insights(
    request: DigitalTwinInsightsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_factory: MLServiceFactory = Depends(get_ml_service_factory),
) -> APIResponse:
    """
    Get Digital Twin insights for a patient.
    
    Args:
        request: Digital twin insights request
        current_user: Current authenticated user
        ml_factory: ML service factory
        
    Returns:
        API response with Digital Twin insights
        
    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Get Digital Twin service
        service = ml_factory.get_digital_twin_service()
        
        # Get insights
        result = service.get_insights(
            patient_id=request.patient_id,
            insight_type=request.insight_type,
            time_period=request.time_period,
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="Digital Twin insights retrieved successfully",
            data=result,
        )
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )
    except InvalidRequestError as e:
        logger.error(f"Invalid request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error retrieving Digital Twin insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Digital Twin insights: {str(e)}",
        )