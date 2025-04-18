"""MentaLLaMA API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
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
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@router.post(
    "/process",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_200_OK
)
async def process_endpoint(
    request: ProcessRequest
) -> Dict[str, Any]:
    """
    Process text using MentaLLaMA.
    """
    prompt = request.prompt
    valid_models = ["mentallama-7b", "mentallama-33b", "mentallama-33b-lora"]
    if not prompt:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Prompt cannot be empty")
    model = request.model
    if model and model not in valid_models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model {model} not found")
    # Stub response
    return {
        "model": model or "mentallama-33b",
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
    request: AnalyzeRequest,
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    General text analysis endpoint.
    """
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
    request: DetectRequest,
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Detect mental health conditions.
    """
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
    request: TherapeuticRequest,
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Generate therapeutic response.
    """
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
    request: RiskRequest,
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Assess suicide risk.
    """
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
    request: WellnessRequest,
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Analyze wellness dimensions.
    """
    dims = {
        dim: {"score": 0.0, "recommendations": []}
        for dim in request.dimensions
    }
    return {"structured_data": {"dimensions": dims}}


@router.get(
    "/health",
    status_code=status.HTTP_200_OK
)
async def health_endpoint(
    service: MentaLLaMAInterface = Depends(get_mentallama_service)
) -> Dict[str, Any]:
    """
    Health check for MentaLLaMA service.
    """
    try:
        return service.get_health_status()  # type: ignore
    except Exception:
        status_str = "healthy" if service.is_healthy() else "unhealthy"
        version = getattr(service, "version", None)
        return {"status": status_str, "version": version}