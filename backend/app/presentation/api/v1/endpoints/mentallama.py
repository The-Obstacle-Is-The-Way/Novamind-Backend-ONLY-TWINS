"""MentaLLaMA API Endpoints."""

from fastapi import APIRouter, Depends, Body, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.api.routes.ml import verify_api_key
from app.presentation.api.v1.dependencies.ml import get_mentallama_service
from app.core.services.ml.interface import MentaLLaMAInterface
from app.core.exceptions import (
    InvalidRequestError, ModelNotFoundError, ServiceUnavailableError
)

router = APIRouter()


class ProcessRequest(BaseModel):
    # Prompt must be a non-empty string; allow validation in endpoint logic
    prompt: str = Field(...)
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@router.post(
    "/process",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_200_OK
)
async def process_endpoint(
    body: ProcessRequest = Body(...),
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Process text using MentaLLaMA (stub implementation).
    """
    # Resolve service instance
    svc = service() if callable(service) else service
    # Check service health
    if hasattr(svc, 'initialized'):
        healthy = bool(getattr(svc, 'initialized'))
    elif hasattr(svc, 'is_healthy'):
        healthy = bool(svc.is_healthy())
    else:
        healthy = True
    if not healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MentaLLaMA service unavailable"
        )
    # Validate prompt
    prompt = body.prompt
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt cannot be empty"
        )
    # Validate model choice
    valid_models = ["mentallama-7b", "mentallama-33b", "mentallama-33b-lora"]
    if body.model and body.model not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {body.model} not found"
        )
    # Return stub response
    return {
        "model": body.model or "mentallama-33b",
        "text": "This is a mock response from MentaLLaMA.",
        "provider": "aws-bedrock"
    }


class AnalyzeRequest(BaseModel):
    text: str
    analysis_type: str


@router.post(
    "/analyze",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_200_OK
)
async def analyze_endpoint(
    body: AnalyzeRequest = Body(...),
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    General text analysis endpoint (stub).
    """
    # Validate text and analysis_type
    if not body.text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be empty"
        )
    if not body.analysis_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Analysis type cannot be empty"
        )
    # Stub structured data containing all expected keys
    structured_data: Dict[str, Any] = {
        "sentiment": {},
        "entities": [],
        "conditions": [],
        "therapeutic_approach": None,
        "techniques": [],
        "risk_level": None,
        "risk_factors": [],
        "protective_factors": [],
        "recommendations": [],
        "immediate_action_required": False,
        "dimensions": {}
    }
    return {"structured_data": structured_data}


class DetectRequest(BaseModel):
    text: str


@router.post(
    "/detect_conditions",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_200_OK
)
async def detect_conditions_endpoint(
    body: DetectRequest = Body(...),
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Detect mental health conditions (stub).
    """
    # Validate input text
    if not body.text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be empty"
        )
    # Stub one condition entry
    conditions: List[Dict[str, Any]] = [{"condition": "", "confidence": 0.0}]
    return {"structured_data": {"conditions": conditions}}


class TherapeuticRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None


@router.post(
    "/therapeutic_response",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_200_OK
)
async def therapeutic_response_endpoint(
    body: TherapeuticRequest = Body(...),
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Generate therapeutic response (stub).
    """
    # Validate input text
    if not body.text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be empty"
        )
    # Stub therapeutic response
    return {
        "text": "",
        "structured_data": {"therapeutic_approach": "", "techniques": []}
    }


class RiskRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None


@router.post(
    "/assess_suicide_risk",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_200_OK
)
async def assess_suicide_risk_endpoint(
    body: RiskRequest = Body(...),
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Assess suicide risk (stub).
    """
    # Validate input text
    if not body.text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be empty"
        )
    # Stub risk assessment
    structured = {
        "risk_level": None,
        "risk_factors": [],
        "protective_factors": [],
        "recommendations": [],
        "immediate_action_required": False
    }
    return {"structured_data": structured}


class WellnessRequest(BaseModel):
    text: str
    dimensions: List[str]
    include_recommendations: bool = False


@router.post(
    "/analyze_wellness_dimensions",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_200_OK
)
async def analyze_wellness_dimensions_endpoint(
    body: WellnessRequest = Body(...),
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Analyze wellness dimensions (stub).
    """
    # Validate input text and dimensions
    if not body.text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be empty"
        )
    if not isinstance(body.dimensions, list) or not body.dimensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one dimension must be specified"
        )
    # Stub wellness analysis
    dims = {
        dim: {"score": 0.0, "recommendations": []}
        for dim in body.dimensions
    }
    return {"structured_data": {"dimensions": dims}}


@router.get(
    "/health",
    status_code=status.HTTP_200_OK
)
async def health_endpoint() -> Dict[str, Any]:
    """
    Health check for MentaLLaMA service (stub).
    """
    # Stub health response
    return {"status": "healthy", "version": "mock-0.1"}