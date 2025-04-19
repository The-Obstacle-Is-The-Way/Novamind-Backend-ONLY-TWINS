# -*- coding: utf-8 -*-
"""
XGBoost Service API Endpoints.

Provides API endpoints for interacting with the XGBoost prediction service.
"""

import logging
from uuid import UUID
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Body
import inspect
from datetime import datetime

# Dependency Injection for Service
 # from app.presentation.api.dependencies.services import get_xgboost_service # Likely removed/refactored
 # TODO: Update dependency injection for XGBoostInterface if needed.
# Remove container-based DI, use alias module for tests
from app.api.routes.xgboost import get_xgboost_service, verify_provider_access
from app.core.services.ml.xgboost.interface import XGBoostInterface # Import the interface

# Schemas for Request/Response Validation
from app.presentation.api.schemas.xgboost import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    TreatmentResponseRequest,
    TreatmentResponseResponse,
    OutcomePredictionRequest,
    OutcomePredictionResponse,
    ModelInfoRequest, # Assuming this schema exists or will be created
    ModelInfoResponse, # Assuming this schema exists or will be created
    FeatureImportanceRequest, # Assuming this schema exists or will be created
    FeatureImportanceResponse, # Assuming this schema exists or will be created
    RiskFactors,  # Add risk factors schema for default
)
from app.core.services.ml.xgboost.exceptions import (
    XGBoostServiceError,
    ValidationError,
    ModelNotFoundError,
    PredictionError,
    ConfigurationError,
    ServiceConnectionError,
    ResourceNotFoundError
)

# Authentication and DI dependencies now via alias module
# current_user and verify_provider_access imported above
from app.domain.models.user import User # Or appropriate user model

logger = logging.getLogger(__name__)

router = APIRouter(
    # prefix="/xgboost", # Prefix is likely already handled by main app include_router
    tags=["XGBoost ML"]
)

@router.post(
    "/risk",
    summary="Predict Patient Risk",
    description="Predicts various risk types (e.g., relapse, suicide) using XGBoost models.",
    status_code=status.HTTP_200_OK
)
@router.post(
    "/risk-prediction",
    summary="Predict Patient Risk",
    description="Predicts various risk types (e.g., relapse, suicide) using XGBoost models.",
    status_code=status.HTTP_200_OK
)
@router.post(
    "/predict/risk",
    summary="Predict Patient Risk",
    description="Predicts various risk types (e.g., relapse, suicide) using XGBoost models.",
    status_code=status.HTTP_200_OK
)
async def predict_risk(
    request: RiskPredictionRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service),
    user: dict = Depends(verify_provider_access)
) -> dict:
    """Endpoint to predict patient risk using XGBoost."""
    try:
        # Determine risk_type value for service, supporting enum or string
        rt = request.risk_type.value if hasattr(request.risk_type, 'value') else request.risk_type
        raw = xgboost_service.predict_risk(
            patient_id=str(request.patient_id),
            risk_type=rt,
            clinical_data=request.clinical_data,
            time_frame_days=request.time_frame_days
        )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ValidationError as e:
        logger.warning(f"Validation error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found for risk prediction: {e}", exc_info=True)
        # Return error detail as list to indicate missing model
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=[str(e)])
    except PredictionError as e:
        logger.error(f"Prediction failed during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction failed: {e}")
    except ConfigurationError as e:
        logger.error(f"Configuration error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during risk prediction for patient {request.patient_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during risk prediction.")

@router.post(
    "/treatment-response",
    summary="Predict Treatment Response",
    description="Predicts patient response to specific treatments using XGBoost models.",
    status_code=status.HTTP_200_OK
)
@router.post(
    "/predict/treatment-response",
    summary="Predict Treatment Response",
    description="Predicts patient response to specific treatments using XGBoost models.",
    status_code=status.HTTP_200_OK
)
async def predict_treatment_response(
    request: TreatmentResponseRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service),
    user: dict = Depends(verify_provider_access)
) -> dict:
    """Endpoint to predict treatment response using XGBoost."""
    try:
        raw = xgboost_service.predict_treatment_response(
            patient_id=str(request.patient_id),
            treatment_type=request.treatment_type.value,
            treatment_details=(
                request.treatment_details.dict()
                if hasattr(request.treatment_details, "dict")
                else request.treatment_details
            ),
            clinical_data=request.clinical_data
        )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ValidationError as e:
        logger.warning(f"Validation error during treatment response prediction: {e}", exc_info=True)
        # Return validation error details
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found for treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PredictionError as e:
        logger.error(f"Prediction failed during treatment response prediction: {e}", exc_info=True)
        # Return prediction errors as client errors
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=[str(e)])
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during treatment response prediction for patient {request.patient_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during treatment response prediction.")

@router.post(
    "/outcome",
    summary="Predict Clinical Outcome",
    description="Predicts clinical outcomes based on patient data and treatment plan using XGBoost.",
    status_code=status.HTTP_200_OK
)
@router.post(
    "/outcome-prediction",
    summary="Predict Clinical Outcome",
    description="Predicts clinical outcomes based on patient data and treatment plan using XGBoost.",
    status_code=status.HTTP_200_OK
)
@router.post(
    "/predict/outcome",
    summary="Predict Clinical Outcome",
    description="Predicts clinical outcomes based on patient data and treatment plan using XGBoost.",
    status_code=status.HTTP_200_OK
)
async def predict_outcome(
    request: OutcomePredictionRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service),
    user: dict = Depends(verify_provider_access)
) -> dict:
    """Endpoint to predict clinical outcome using XGBoost."""
    try:
        # Prepare timeframe and treatment plan, handling dict or Pydantic model
        timeframe = (
            request.outcome_timeframe.dict()
            if hasattr(request.outcome_timeframe, 'dict')
            else request.outcome_timeframe or {}
        )
        plan = (
            request.treatment_plan.dict()
            if hasattr(request.treatment_plan, 'dict')
            else request.treatment_plan or {}
        )
        raw = xgboost_service.predict_outcome(
            patient_id=str(request.patient_id),
            outcome_timeframe=timeframe,
            clinical_data=request.clinical_data,
            treatment_plan=plan,
            social_determinants=request.social_determinants,
            comorbidities=request.comorbidities
        )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ValidationError as e:
        logger.warning(f"Validation error during outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found for outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PredictionError as e:
        logger.error(f"Prediction failed during outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction failed: {e}")
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during outcome prediction for patient {request.patient_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during outcome prediction.")

@router.get(
    "/model-info/{model_type}",
    summary="Get Model Information",
    description="Retrieves metadata and information about a specific XGBoost model.",
    status_code=status.HTTP_200_OK
)
async def get_model_info(
    model_type: str, # Or use ModelType enum if defined appropriately
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service), # Use alias DI for XGBoost service
) -> dict:
    """Endpoint to get information about an XGBoost model."""
    try:
        # Handle sync or async service methods
        raw = xgboost_service.get_model_info(model_type=model_type)
        info = await raw if inspect.isawaitable(raw) else raw
        return info
    except ModelNotFoundError as e:
        logger.warning(f"Model info not found for type '{model_type}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error retrieving model info for '{model_type}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error retrieving model info for '{model_type}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving model information.")
    # POST endpoint for model information requests (integration tests)
@router.post(
    "/model-info",
    summary="Get Model Information",
    description="Retrieves metadata and information about a specific XGBoost model.",
    status_code=status.HTTP_200_OK
)
async def post_model_info(
    request: ModelInfoRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        raw = xgboost_service.get_model_info(model_type=request.model_type)
        info = await raw if inspect.isawaitable(raw) else raw
        return info
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except XGBoostServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving model information.")

@router.get(
    "/feature-importance/{model_type}",
    summary="Get Feature Importance",
    description="Retrieves feature importance scores for a specific prediction.",
    status_code=status.HTTP_200_OK
)
async def get_feature_importance(
    model_type: str,
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service),
) -> dict:
    """Endpoint to get feature importance for a prediction."""
    try:
        # Handle sync or async service methods
        raw = xgboost_service.get_feature_importance(model_type=model_type)
        importance_data = await raw if inspect.isawaitable(raw) else raw
        return importance_data
    except ValidationError as e:
        logger.warning(f"Validation error during feature importance request: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ResourceNotFoundError as e: # Service uses ResourceNotFoundError for missing prediction
        logger.warning(f"Prediction or importance data not found for ID '{model_type}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error retrieving feature importance for prediction '{model_type}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error retrieving feature importance for prediction '{model_type}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving feature importance.")

# POST endpoint for feature importance requests (integration tests)
@router.post(
    "/feature-importance",
    summary="Get Feature Importance",
    description="Retrieves feature importance for a specific prediction.",
    status_code=status.HTTP_200_OK
)
async def post_feature_importance(
    request: FeatureImportanceRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        raw = xgboost_service.get_feature_importance(
            patient_id=request.patient_id,
            model_type=request.model_type,
            prediction_id=request.prediction_id
        )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except XGBoostServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving feature importance.")

@router.post(
    "/digital-twin-simulation",
    summary="Simulate Digital Twin",
    description="Simulates patient progression using digital twin concept.",
    status_code=status.HTTP_200_OK
)
async def digital_twin_simulation(
    request_data: Dict[str, Any] = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service)
) -> dict:
    """Endpoint to simulate a digital twin using XGBoost."""
    raw = xgboost_service.simulate_digital_twin(
        patient_id=request_data["patient_id"],
        simulation_timeframe=request_data["simulation_timeframe"],
        treatment_plan=request_data["treatment_plan"],
        baseline_metrics=request_data["baseline_metrics"]
    )
    result = await raw if inspect.isawaitable(raw) else raw
    return result
   
# POST endpoint for digital-twin integration (integration tests)
@router.post(
    "/digital-twin-integration",
    summary="Integrate with Digital Twin",
    description="Integrates prediction results with the Digital Twin service.",
    status_code=status.HTTP_200_OK
)
async def integrate_with_digital_twin(
    request_data: Dict[str, Any] = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_xgboost_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        raw = xgboost_service.integrate_with_digital_twin(
            patient_id=request_data["patient_id"],
            profile_id=request_data["profile_id"],
            prediction_id=request_data["prediction_id"]
        )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
