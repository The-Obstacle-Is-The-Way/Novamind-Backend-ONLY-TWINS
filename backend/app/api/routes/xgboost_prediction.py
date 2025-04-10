"""
XGBoost Prediction API Routes.

This module defines the FastAPI endpoints for the XGBoost prediction service,
providing HIPAA-compliant access to psychiatric risk assessment, treatment
response prediction, and outcome forecasting.
"""

import logging
from typing import Annotated, Any, Optional, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Security, Path, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.dependencies.auth import get_current_user, validate_clinician_access
from app.api.dependencies.services import get_xgboost_service
from app.api.dependencies.phi_detection import validate_no_phi

from app.api.schemas.xgboost_prediction import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    TreatmentResponseRequest,
    TreatmentResponsePrediction,
    OutcomePredictionRequest,
    OutcomePredictionResponse,
    FeatureImportanceRequest,
    FeatureImportance,
    DigitalTwinIntegrationRequest,
    DigitalTwinIntegration,
    ModelInfoRequest,
    ModelInfo,
    ErrorResponse
)

from app.core.services.ml.xgboost import (
    XGBoostInterface,
    XGBoostBaseException,
    ConfigurationError,
    ValidationError,
    DataPrivacyError,
    AuthorizationError,
    ResourceNotFoundError,
    ModelNotFoundError,
    PredictionError,
    FeatureEngineeringError,
    IntegrationError,
    ServiceUnavailableError,
    ThrottlingError,
    SecurityError
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/xgboost",
    tags=["xgboost", "predictions", "ml"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}
    }
)

# Security scheme for Swagger UI
security = HTTPBearer()


def handle_xgboost_exception(exc: XGBoostBaseException) -> HTTPException:
    """
    Convert domain exceptions to appropriate HTTP exceptions.
    
    Args:
        exc: The domain exception to convert
        
    Returns:
        HTTPException with appropriate status code and details
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = {"error_type": type(exc).__name__, "message": str(exc)}
    
    # Include additional context if available
    if hasattr(exc, "context") and exc.context:
        # Filter out any potential PHI from error details
        safe_context = {
            k: v for k, v in exc.context.items()
            if k not in ["source"]
        }
        detail["details"] = safe_context
    
    # Map domain exceptions to HTTP status codes
    if isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, DataPrivacyError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AuthorizationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, (ResourceNotFoundError, ModelNotFoundError)):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ServiceUnavailableError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, ThrottlingError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        if hasattr(exc, "retry_after") and exc.retry_after:
            # Include Retry-After header
            headers = {"Retry-After": str(exc.retry_after)}
            return HTTPException(
                status_code=status_code,
                detail=detail,
                headers=headers
            )
    
    return HTTPException(
        status_code=status_code,
        detail=detail
    )


@router.post(
    "/risk-prediction",
    response_model=RiskPredictionResponse,
    summary="Predict psychiatric risk",
    description="Predicts risk of psychiatric symptoms or relapse based on clinical data"
)
async def predict_risk(
    request: RiskPredictionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: XGBoostInterface = Depends(get_xgboost_service),
    _: None = Depends(validate_clinician_access),
    __: None = Depends(validate_no_phi)
):
    """
    Predict psychiatric risk for a patient.
    
    This endpoint uses XGBoost models to predict the risk of psychiatric
    symptoms or relapse based on clinical data, demographics, and 
    temporal measurements.
    """
    try:
        # Validate patient access
        if current_user.get("id") != request.patient_id and not current_user.get("is_clinician"):
            raise AuthorizationError("Not authorized to access this patient's data")
        
        # Make prediction
        result = service.predict_risk(
            patient_id=request.patient_id,
            risk_type=request.risk_type,
            clinical_data=request.clinical_data.model_dump(),
            demographic_data=(
                request.demographic_data.model_dump() 
                if request.demographic_data else None
            ),
            temporal_data=(
                request.temporal_data.model_dump() 
                if request.temporal_data else None
            ),
            confidence_threshold=request.confidence_threshold
        )
        
        logger.info(
            f"Risk prediction completed for patient (sanitized): "
            f"{request.patient_id[:4]}**** - "
            f"Type: {request.risk_type}, "
            f"Result: {result.get('risk_level')}"
        )
        
        return result
        
    except XGBoostBaseException as e:
        logger.error(f"Risk prediction error: {str(e)}")
        raise handle_xgboost_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error in risk prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UnexpectedError", "message": "An unexpected error occurred"}
        )


@router.post(
    "/treatment-response",
    response_model=TreatmentResponsePrediction,
    summary="Predict treatment response",
    description="Predicts patient response to a specific medication or therapy"
)
async def predict_treatment_response(
    request: TreatmentResponseRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: XGBoostInterface = Depends(get_xgboost_service),
    _: None = Depends(validate_clinician_access),
    __: None = Depends(validate_no_phi)
):
    """
    Predict patient response to a specific treatment.
    
    This endpoint uses XGBoost models to predict how a patient will
    respond to a particular medication or therapy, based on clinical
    data, genetic information, and treatment history.
    """
    try:
        # Validate patient access
        if current_user.get("id") != request.patient_id and not current_user.get("is_clinician"):
            raise AuthorizationError("Not authorized to access this patient's data")
        
        # Make prediction
        result = service.predict_treatment_response(
            patient_id=request.patient_id,
            treatment_type=request.treatment_type,
            treatment_details=request.treatment_details,
            clinical_data=request.clinical_data.model_dump(),
            genetic_data=(
                request.genetic_data.model_dump() 
                if request.genetic_data else None
            ),
            treatment_history=(
                request.treatment_history.model_dump() 
                if request.treatment_history else None
            )
        )
        
        logger.info(
            f"Treatment response prediction completed for patient (sanitized): "
            f"{request.patient_id[:4]}**** - "
            f"Type: {request.treatment_type}, "
            f"Result: {result.get('response_label')}"
        )
        
        return result
        
    except XGBoostBaseException as e:
        logger.error(f"Treatment response prediction error: {str(e)}")
        raise handle_xgboost_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error in treatment response prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UnexpectedError", "message": "An unexpected error occurred"}
        )


@router.post(
    "/outcome-prediction",
    response_model=OutcomePredictionResponse,
    summary="Predict psychiatric outcomes",
    description="Predicts outcomes based on treatment plan and patient factors"
)
async def predict_outcome(
    request: OutcomePredictionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: XGBoostInterface = Depends(get_xgboost_service),
    _: None = Depends(validate_clinician_access),
    __: None = Depends(validate_no_phi)
):
    """
    Predict psychiatric outcomes based on treatment plan.
    
    This endpoint uses XGBoost models to predict clinical outcomes over
    a specified timeframe, considering the treatment plan, clinical data,
    social determinants, and comorbidities.
    """
    try:
        # Validate patient access
        if current_user.get("id") != request.patient_id and not current_user.get("is_clinician"):
            raise AuthorizationError("Not authorized to access this patient's data")
        
        # Make prediction
        result = service.predict_outcome(
            patient_id=request.patient_id,
            outcome_timeframe=request.outcome_timeframe,
            clinical_data=request.clinical_data.model_dump(),
            treatment_plan=request.treatment_plan.model_dump(),
            social_determinants=(
                request.social_determinants.model_dump() 
                if request.social_determinants else None
            ),
            comorbidities=(
                request.comorbidities.model_dump() 
                if request.comorbidities else None
            )
        )
        
        logger.info(
            f"Outcome prediction completed for patient (sanitized): "
            f"{request.patient_id[:4]}**** - "
            f"Timeframe: {request.outcome_timeframe}"
        )
        
        return result
        
    except XGBoostBaseException as e:
        logger.error(f"Outcome prediction error: {str(e)}")
        raise handle_xgboost_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error in outcome prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UnexpectedError", "message": "An unexpected error occurred"}
        )


@router.post(
    "/feature-importance",
    response_model=FeatureImportance,
    summary="Get feature importance for a prediction",
    description="Returns feature importance scores for a specific prediction"
)
async def get_feature_importance(
    request: FeatureImportanceRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: XGBoostInterface = Depends(get_xgboost_service),
    _: None = Depends(validate_clinician_access)
):
    """
    Get feature importance for a specific prediction.
    
    This endpoint provides detailed explanation of which factors
    contributed most significantly to a prediction result, using
    techniques like SHAP values for model interpretability.
    """
    try:
        # Validate patient access
        if current_user.get("id") != request.patient_id and not current_user.get("is_clinician"):
            raise AuthorizationError("Not authorized to access this patient's data")
        
        # Get feature importance
        result = service.get_feature_importance(
            patient_id=request.patient_id,
            model_type=request.model_type,
            prediction_id=request.prediction_id
        )
        
        logger.info(
            f"Feature importance retrieved for patient (sanitized): "
            f"{request.patient_id[:4]}**** - "
            f"Prediction: {request.prediction_id}"
        )
        
        return result
        
    except XGBoostBaseException as e:
        logger.error(f"Feature importance error: {str(e)}")
        raise handle_xgboost_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error in feature importance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UnexpectedError", "message": "An unexpected error occurred"}
        )


@router.post(
    "/digital-twin-integration",
    response_model=DigitalTwinIntegration,
    summary="Integrate prediction with digital twin",
    description="Integrates a prediction with a patient's digital twin profile"
)
async def integrate_with_digital_twin(
    request: DigitalTwinIntegrationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: XGBoostInterface = Depends(get_xgboost_service),
    _: None = Depends(validate_clinician_access)
):
    """
    Integrate a prediction with a patient's digital twin profile.
    
    This endpoint connects XGBoost predictions with digital twin models,
    enabling comprehensive, multi-modal representation of patient status
    and treatment trajectories.
    """
    try:
        # Validate patient access
        if current_user.get("id") != request.patient_id and not current_user.get("is_clinician"):
            raise AuthorizationError("Not authorized to access this patient's data")
        
        # Perform integration
        result = service.integrate_with_digital_twin(
            patient_id=request.patient_id,
            profile_id=request.profile_id,
            prediction_id=request.prediction_id
        )
        
        logger.info(
            f"Digital twin integration completed for patient (sanitized): "
            f"{request.patient_id[:4]}**** - "
            f"Profile: {request.profile_id}"
        )
        
        return result
        
    except XGBoostBaseException as e:
        logger.error(f"Digital twin integration error: {str(e)}")
        raise handle_xgboost_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error in digital twin integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UnexpectedError", "message": "An unexpected error occurred"}
        )


@router.get(
    "/model-info/{model_type}",
    response_model=ModelInfo,
    summary="Get model information",
    description="Returns information about a specific prediction model"
)
async def get_model_info(
    model_type: str = Path(..., description="Type of model to get information about"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: XGBoostInterface = Depends(get_xgboost_service),
    _: None = Depends(validate_clinician_access)
):
    """
    Get information about a specific model type.
    
    This endpoint provides metadata about prediction models, including
    version, features used, performance metrics, and capabilities.
    """
    try:
        # Get model info
        result = service.get_model_info(model_type=model_type)
        
        logger.info(
            f"Model info retrieved for type: {model_type}"
        )
        
        return result
        
    except XGBoostBaseException as e:
        logger.error(f"Model info error: {str(e)}")
        raise handle_xgboost_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error in model info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UnexpectedError", "message": "An unexpected error occurred"}
        )


# Healthcheck endpoint
@router.get(
    "/health",
    summary="Healthcheck endpoint",
    description="Checks if the XGBoost service is operational"
)
async def health_check(
    service: XGBoostInterface = Depends(get_xgboost_service)
):
    """
    Health check endpoint for the XGBoost service.
    
    This endpoint verifies that the XGBoost service is operational
    and properly configured. It's useful for monitoring and
    automated health checks.
    """
    try:
        # Check if service can be initialized
        if not hasattr(service, "_initialized") or not service._initialized:
            return {
                "status": "error",
                "message": "XGBoost service not initialized"
            }
        
        return {
            "status": "ok",
            "service": "xgboost",
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }