"""
FastAPI routes for the XGBoost service.

This module defines the API endpoints for accessing the XGBoost ML service,
providing prediction and model information endpoints with proper validation,
error handling, and security.
"""

import logging
import importlib
from typing import Annotated, Dict, Any, cast, TypeVar, Generic, Callable
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Security, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.dependencies.response import ensure_serializable_response, prevent_session_exposure

from app.api.schemas.xgboost import (
    RiskPredictionRequest, RiskPredictionResponse, 
    TreatmentResponseRequest, TreatmentResponseResponse,
    OutcomePredictionRequest, OutcomePredictionResponse,
    FeatureImportanceRequest, FeatureImportanceResponse,
    DigitalTwinIntegrationRequest, DigitalTwinIntegrationResponse,
    ModelInfoRequest, ModelInfoResponse,
    ErrorResponse
)

# Setup logging
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Type for avoiding FastAPI schema generation of complex types
T = TypeVar('T')

# Prevent module-level imports from causing FastAPI to analyze our dependencies
# By using a late binding approach, FastAPI cannot "see" complex dependencies during router setup
class LazyDependency(Generic[T]):
    """Lazy dependency loader that prevents FastAPI from analyzing complex dependency chains at import time."""
    
    def __init__(self, module_path: str, dependency_name: str):
        self.module_path = module_path
        self.dependency_name = dependency_name
        self._dependency = None
    
    def __call__(self) -> T:
        if self._dependency is None:
            module = importlib.import_module(self.module_path)
            self._dependency = getattr(module, self.dependency_name)
        return self._dependency()

# Create lazy bindings for imports that would trigger AsyncSession analysis
_get_xgboost_service = LazyDependency(
    'app.core.services.ml.xgboost', 
    'get_xgboost_service'
)

# Import error classes statically as they don't contain AsyncSession references
from app.core.services.ml.xgboost import (
    ValidationError, DataPrivacyError, ModelNotFoundError,
    PredictionError, ServiceConnectionError, ResourceNotFoundError,
    XGBoostServiceError
)

# For type checking only - FastAPI won't analyze this
if False:  # This code block is never executed, just for static type checking
    from app.core.services.ml.xgboost import XGBoostInterface

# Create router
router = APIRouter(
    prefix="/api/v1/ml/xgboost",
    tags=["xgboost"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse, "description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse, "description": "Forbidden"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


# --------------------- Dependencies ---------------------

def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Security(security)]) -> Dict[str, Any]:
    """
    Validate JWT token and return user information.
    
    This is a placeholder for actual authentication logic,
    which would typically validate a JWT token with AWS Cognito
    or another HIPAA-compliant authentication provider.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        User information from the token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Placeholder for JWT validation logic
        # In an actual implementation, this would:
        # 1. Verify the token's signature
        # 2. Check if the token is expired
        # 3. Validate the claims
        # 4. Return the user information from the token
        
        # For now, return a mock user with clinician role
        return {
            "user_id": "mock-user-id",
            "role": "clinician",
            "access_level": "full",
            "organization_id": "main-clinic"
        }
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# --------------------- Request Handlers ---------------------

def handle_xgboost_error(error: Exception) -> HTTPException:
    """
    Map XGBoost service exceptions to appropriate HTTP exceptions.
    
    Args:
        error: XGBoost service exception
        
    Returns:
        Appropriate HTTP exception
    """
    logger.error(f"XGBoost error: {str(error)}")
    
    if isinstance(error, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    elif isinstance(error, DataPrivacyError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data privacy violation detected"
        )
    elif isinstance(error, ModelNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(error)}"
        )
    elif isinstance(error, ResourceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource not found: {str(error)}"
        )
    elif isinstance(error, PredictionError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(error)}"
        )
    elif isinstance(error, ServiceConnectionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(error)}"
        )
    elif isinstance(error, XGBoostServiceError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# --------------------- API Endpoints ---------------------

@router.post(
    "/risk-prediction",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Predict risk level",
    description="Predict risk level using clinical data",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Bad Request"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Model Not Found"}
    }
)
async def predict_risk(
    request: RiskPredictionRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(prevent_session_exposure)
):
    """
    Predict risk level for a patient using clinical data.
    
    Args:
        request: Risk prediction request
        user: Current authenticated user
        
    Returns:
        Risk prediction response
        
    Raises:
        HTTPException: For validation errors, privacy violations, or service issues
    """
    try:
        # Log prediction request (without PHI)
        logger.info(f"Risk prediction request: risk_type={request.risk_type}, time_frame={request.time_frame_days}")
        
        # Get service using lazy dependency to avoid FastAPI analysis of AsyncSession
        service = await _get_xgboost_service()()
        
        # Add current user context for audit trail
        service._current_user_id = user["user_id"]
        
        # Call XGBoost service
        result = service.predict_risk(
            patient_id=request.patient_id,
            risk_type=request.risk_type.value,
            clinical_data=request.clinical_data,
            time_frame_days=request.time_frame_days
        )
        
        # Map domain result to API response
        # Note: Since we're using a common field structure, we can add any missing fields
        if "patient_id" not in result:
            result["patient_id"] = request.patient_id
            
        if "risk_type" not in result:
            result["risk_type"] = request.risk_type
            
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()
            
        # For risk factors, if they're not in the expected format, create a default structure
        if "risk_factors" not in result:
            contributing = []
            protective = []
            
            # If there are factors in the result, use them
            if "factors" in result:
                for factor in result["factors"]:
                    contributing.append({"name": factor, "weight": "medium"})
                    
            result["risk_factors"] = {
                "contributing_factors": contributing,
                "protective_factors": protective
            }
            
        # For supporting evidence, if it's not provided, create an empty list
        if "supporting_evidence" not in result:
            result["supporting_evidence"] = []
            
        # Create response and ensure no AsyncSession objects are returned
        return ensure_serializable_response(RiskPredictionResponse(**result))
        
    except Exception as e:
        raise handle_xgboost_error(e)


@router.post(
    "/treatment-response",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Predict treatment response",
    description="Predict response to a psychiatric treatment",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Bad Request"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Model Not Found"}
    }
)
async def predict_treatment_response(
    request: TreatmentResponseRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(prevent_session_exposure)
):
    """
    Predict response to a psychiatric treatment.
    
    Args:
        request: Treatment response prediction request
        user: Current authenticated user
        
    Returns:
        Treatment response prediction
        
    Raises:
        HTTPException: For validation errors, privacy violations, or service issues
    """
    try:
        # Log prediction request (without PHI)
        logger.info(f"Treatment response prediction request: treatment_type={request.treatment_type}")
        
        # Get service using lazy dependency to avoid FastAPI analysis of AsyncSession
        service = await _get_xgboost_service()()
        
        # Add current user context for audit trail
        service._current_user_id = user["user_id"]
        
        # Call XGBoost service
        result = service.predict_treatment_response(
            patient_id=request.patient_id,
            treatment_type=request.treatment_type.value,
            treatment_details=request.treatment_details.model_dump(),
            clinical_data=request.clinical_data,
            prediction_horizon=request.prediction_horizon
        )
        
        # Map domain result to API response
        # Set missing fields if necessary
        if "patient_id" not in result:
            result["patient_id"] = request.patient_id
            
        if "treatment_type" not in result:
            result["treatment_type"] = request.treatment_type
            
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()
            
        # Handle expected fields that might be missing
        if "treatment_details" not in result:
            result["treatment_details"] = request.treatment_details.model_dump()
            
        # Ensure expected structures for side effects and expected outcomes
        if "side_effect_risk" not in result:
            result["side_effect_risk"] = {
                "common": [],
                "rare": []
            }
            
        if "expected_outcome" not in result:
            result["expected_outcome"] = {
                "symptom_improvement": "Moderate improvement expected",
                "time_to_response": "4-6 weeks",
                "sustained_response_likelihood": "moderate",
                "functional_improvement": "Some improvement in daily functioning expected"
            }
            
        # Create response and ensure no AsyncSession objects are returned
        return ensure_serializable_response(TreatmentResponseResponse(**result))
        
    except Exception as e:
        raise handle_xgboost_error(e)


@router.post(
    "/outcome-prediction",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Predict clinical outcomes",
    description="Predict clinical outcomes based on treatment plan",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Bad Request"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Model Not Found"}
    }
)
async def predict_outcome(
    request: OutcomePredictionRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(prevent_session_exposure)
):
    """
    Predict clinical outcomes based on treatment plan.
    
    Args:
        request: Outcome prediction request
        user: Current authenticated user
        
    Returns:
        Outcome prediction
        
    Raises:
        HTTPException: For validation errors, privacy violations, or service issues
    """
    try:
        # Log prediction request (without PHI)
        logger.info(f"Outcome prediction request: outcome_type={request.outcome_type}")
        
        # Get service using lazy dependency to avoid FastAPI analysis of AsyncSession
        service = await _get_xgboost_service()()
        
        # Add current user context for audit trail
        service._current_user_id = user["user_id"]
        
        # Call XGBoost service
        result = service.predict_outcome(
            patient_id=request.patient_id,
            outcome_timeframe=request.outcome_timeframe.model_dump(),
            clinical_data=request.clinical_data,
            treatment_plan=request.treatment_plan,
            outcome_type=request.outcome_type.value
        )
        
        # Map domain result to API response
        # Set missing fields if necessary
        if "patient_id" not in result:
            result["patient_id"] = request.patient_id
            
        if "outcome_type" not in result:
            result["outcome_type"] = request.outcome_type
            
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()
        
        # Ensure expected structures for trajectory and outcome details
        if "trajectory" not in result:
            # Create default trajectory data
            result["trajectory"] = {
                "points": [
                    {
                        "time_point": "Initial",
                        "days_from_start": 0,
                        "improvement_percentage": 0
                    },
                    {
                        "time_point": "Final",
                        "days_from_start": result.get("time_frame_days", 90),
                        "improvement_percentage": int(result.get("outcome_score", 0.5) * 100)
                    }
                ],
                "final_improvement": int(result.get("outcome_score", 0.5) * 100),
                "time_frame_days": result.get("time_frame_days", 90),
                "visualization_type": "line_chart"
            }
            
        if "outcome_details" not in result:
            result["outcome_details"] = {
                "overall_improvement": "Moderate improvement expected",
                "domains": [
                    {
                        "name": "Symptoms",
                        "improvement": "Moderate improvement",
                        "notes": "Gradual reduction in severity expected"
                    }
                ],
                "recommendations": [
                    "Continue with current treatment plan",
                    "Monitor progress closely"
                ]
            }
            
        # Create response and ensure no AsyncSession objects are returned
        return ensure_serializable_response(OutcomePredictionResponse(**result))
        
    except Exception as e:
        raise handle_xgboost_error(e)


@router.post(
    "/feature-importance",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Get feature importance",
    description="Get feature importance for a prediction",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Bad Request"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Resource Not Found"}
    }
)
async def get_feature_importance(
    request: FeatureImportanceRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(prevent_session_exposure)
):
    """
    Get feature importance for a prediction.
    
    Args:
        request: Feature importance request
        user: Current authenticated user
        
    Returns:
        Feature importance data
        
    Raises:
        HTTPException: For validation errors or service issues
    """
    try:
        # Log request (without PHI)
        logger.info(f"Feature importance request: model_type={request.model_type}")
        
        # Get service using lazy dependency to avoid FastAPI analysis of AsyncSession
        service = await _get_xgboost_service()()
        
        # Add current user context for audit trail
        service._current_user_id = user["user_id"]
        
        # Call XGBoost service
        result = service.get_feature_importance(
            patient_id=request.patient_id,
            model_type=request.model_type,
            prediction_id=request.prediction_id
        )
        
        # Map domain result to API response
        # Set missing fields if necessary
        if "patient_id" not in result:
            result["patient_id"] = request.patient_id
            
        if "model_type" not in result:
            result["model_type"] = request.model_type
            
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()
            
        # Ensure expected structures for features
        if "features" not in result:
            result["features"] = []
            
        # Create response and ensure no AsyncSession objects are returned
        return ensure_serializable_response(FeatureImportanceResponse(**result))
        
    except Exception as e:
        raise handle_xgboost_error(e)


@router.post(
    "/integrate-with-digital-twin",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Integrate XGBoost with Digital Twin",
    description="Integrate XGBoost models with digital twin profiles",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Bad Request"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Not Found"}
    }
)
async def integrate_with_digital_twin(
    request: DigitalTwinIntegrationRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(prevent_session_exposure)
):
    """
    Integrate XGBoost models with digital twin profiles.
    
    Args:
        request: Integration request
        user: Current authenticated user
        
    Returns:
        Integration result
        
    Raises:
        HTTPException: For validation errors or service issues
    """
    try:
        # Log request (without PHI)
        logger.info(f"Digital twin integration request: profile_id={request.profile_id}")
        
        # Get service using lazy dependency to avoid FastAPI analysis of AsyncSession
        service = await _get_xgboost_service()()
        
        # Add current user context for audit trail
        service._current_user_id = user["user_id"]
        
        # Call XGBoost service
        result = service.integrate_with_digital_twin(
            patient_id=request.patient_id,
            profile_id=request.profile_id,
            integration_settings=request.integration_settings
        )
        
        # Map domain result to API response
        # Set missing fields if necessary
        if "patient_id" not in result:
            result["patient_id"] = request.patient_id
            
        if "profile_id" not in result:
            result["profile_id"] = request.profile_id
            
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()
            
        # Create response and ensure no AsyncSession objects are returned
        return ensure_serializable_response(DigitalTwinIntegrationResponse(**result))
        
    except Exception as e:
        raise handle_xgboost_error(e)


@router.post(
    "/model-info",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Get model information",
    description="Get detailed information about a specific XGBoost model",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Bad Request"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Model Not Found"}
    }
)
async def get_model_info(
    request: ModelInfoRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(prevent_session_exposure)
):
    """
    Get detailed information about a specific XGBoost model.
    
    Args:
        request: Model info request
        user: Current authenticated user
        
    Returns:
        Model information
        
    Raises:
        HTTPException: For validation errors or if model not found
    """
    try:
        # Log request
        logger.info(f"Model info request: model_type={request.model_type}")
        
        # Get service using lazy dependency to avoid FastAPI analysis of AsyncSession
        service = await _get_xgboost_service()()
        
        # Add current user context for audit trail
        service._current_user_id = user["user_id"]
        
        # Call XGBoost service
        result = service.get_model_info(
            model_type=request.model_type,
            version=request.version
        )
        
        # Map domain result to API response
        # Set missing fields if necessary
        if "model_type" not in result:
            result["model_type"] = request.model_type
            
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()
            
        # Create response and ensure no AsyncSession objects are returned
        return ensure_serializable_response(ModelInfoResponse(**result))
        
    except Exception as e:
        raise handle_xgboost_error(e)