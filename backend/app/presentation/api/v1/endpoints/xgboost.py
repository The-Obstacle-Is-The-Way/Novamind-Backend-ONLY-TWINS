# -*- coding: utf-8 -*-
"""
XGBoost Service API Endpoints.

Provides API endpoints for interacting with the XGBoost prediction service.
"""

import logging
from uuid import UUID
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
import inspect
from datetime import datetime

# Dependency Injection for Service
# from app.presentation.api.dependencies.services import get_xgboost_service # Likely removed/refactored
# TODO: Update dependency injection for XGBoostInterface if needed.
from app.infrastructure.di.container import get_service # Use generic service provider
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

# Authentication Dependency
from app.presentation.api.dependencies.auth import get_current_user, verify_provider_access
from app.domain.models.user import User # Or appropriate user model

logger = logging.getLogger(__name__)

router = APIRouter(
    # prefix="/xgboost", # Prefix is likely already handled by main app include_router
    tags=["XGBoost ML"],
    dependencies=[Depends(verify_provider_access)] # Protect endpoints
)

@router.post(
    "/predict/risk",
    response_model=RiskPredictionResponse,
    summary="Predict Patient Risk",
    description="Predicts various risk types (e.g., relapse, suicide) using XGBoost models.",
    status_code=status.HTTP_200_OK
)
async def predict_risk(
    request: RiskPredictionRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_service(XGBoostInterface)), # Use get_service
    # current_user: User = Depends(get_current_user) # Optional: If user info needed
) -> RiskPredictionResponse:
    """Endpoint to predict patient risk using XGBoost."""
    try:
        raw = xgboost_service.predict_risk(
            patient_id=str(request.patient_id),
            risk_type=request.risk_type.value,
            clinical_data=request.clinical_data,
            time_frame_days=request.time_frame_days
        )
        result = await raw if inspect.isawaitable(raw) else raw
        # Augment result with required fields for RiskPredictionResponse
        result.setdefault("patient_id", str(request.patient_id))
        result.setdefault("risk_type", request.risk_type.value)
        result.setdefault("risk_factors", {})
        result.setdefault("timestamp", datetime.utcnow())
        result.setdefault("time_frame_days", request.time_frame_days)
        return RiskPredictionResponse(**result)
    except ValidationError as e:
        logger.warning(f"Validation error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found for risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PredictionError as e:
        logger.error(f"Prediction failed during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction failed: {e}")
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during risk prediction for patient {request.patient_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during risk prediction.")

@router.post(
    "/predict/treatment-response",
    # Removed response_model to allow raw dict return for integration tests
    summary="Predict Treatment Response",
    description="Predicts patient response to specific treatments using XGBoost models.",
    status_code=status.HTTP_200_OK
)
async def predict_treatment_response(
    request: TreatmentResponseRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_service(XGBoostInterface)), # Use get_service
) -> dict:
    """Endpoint to predict treatment response using XGBoost."""
    try:
        raw = xgboost_service.predict_treatment_response(
            patient_id=str(request.patient_id),
            treatment_type=request.treatment_type.value,
            treatment_details=(request.treatment_details.dict()
                if hasattr(request.treatment_details, "dict")
                else request.treatment_details),
            clinical_data=request.clinical_data
        )
        result = await raw if inspect.isawaitable(raw) else raw
        # Assuming service returns a dict compatible with TreatmentResponseResponse
        # Return raw service output for integration tests
        return result
    except ValidationError as e:
        logger.warning(f"Validation error during treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found for treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PredictionError as e:
        logger.error(f"Prediction failed during treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction failed: {e}")
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during treatment response prediction for patient {request.patient_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during treatment response prediction.")

@router.post(
    "/predict/outcome",
    response_model=OutcomePredictionResponse,
    summary="Predict Clinical Outcome",
    description="Predicts clinical outcomes based on patient data and treatment plan using XGBoost.",
    status_code=status.HTTP_200_OK
)
async def predict_outcome(
    request: OutcomePredictionRequest = Body(...),
    xgboost_service: XGBoostInterface = Depends(get_service(XGBoostInterface)), # Use get_service
) -> OutcomePredictionResponse:
    """Endpoint to predict clinical outcome using XGBoost."""
    try:
        raw = xgboost_service.predict_outcome(
            patient_id=str(request.patient_id),
            outcome_timeframe=request.outcome_timeframe.dict() if request.outcome_timeframe else {},
            clinical_data=request.clinical_data,
            treatment_plan=request.treatment_plan.dict() if request.treatment_plan else {}
        )
        result = await raw if inspect.isawaitable(raw) else raw
        # Assuming service returns a dict compatible with OutcomePredictionResponse
        return OutcomePredictionResponse(**result)
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
    "/models/{model_type}/info",
    response_model=ModelInfoResponse, # Assuming this schema exists
    summary="Get Model Information",
    description="Retrieves metadata and information about a specific XGBoost model.",
    status_code=status.HTTP_200_OK
)
async def get_model_info(
    model_type: str, # Or use ModelType enum if defined appropriately
    xgboost_service: XGBoostInterface = Depends(get_service(XGBoostInterface)), # Use get_service
) -> ModelInfoResponse:
    """Endpoint to get information about an XGBoost model."""
    try:
        info = await xgboost_service.get_model_info(model_type=model_type)
        # Assuming service returns a dict compatible with ModelInfoResponse
        return ModelInfoResponse(**info)
    except ModelNotFoundError as e:
        logger.warning(f"Model info not found for type '{model_type}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error retrieving model info for '{model_type}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error retrieving model info for '{model_type}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving model information.")

@router.get(
    "/predictions/{prediction_id}/feature-importance",
    response_model=FeatureImportanceResponse, # Assuming this schema exists
    summary="Get Feature Importance",
    description="Retrieves feature importance scores for a specific prediction.",
    status_code=status.HTTP_200_OK
)
async def get_feature_importance(
    prediction_id: str,
    # request: FeatureImportanceRequest = Body(...), # Or get params from query/path
    patient_id: UUID = Query(..., description="Patient ID associated with the prediction"), # Need patient ID
    model_type: str = Query(..., description="Model type used for the prediction"), # Need model type
    xgboost_service: XGBoostInterface = Depends(get_service(XGBoostInterface)), # Use get_service
) -> FeatureImportanceResponse:
    """Endpoint to get feature importance for a prediction."""
    try:
        # Note: Service interface might need patient_id and model_type here
        importance_data = await xgboost_service.get_feature_importance(
            patient_id=str(patient_id),
            model_type=model_type,
            prediction_id=prediction_id
        )
        # Assuming service returns dict compatible with FeatureImportanceResponse
        return FeatureImportanceResponse(**importance_data)
    except ValidationError as e:
        logger.warning(f"Validation error during feature importance request: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ResourceNotFoundError as e: # Service uses ResourceNotFoundError for missing prediction
        logger.warning(f"Prediction or importance data not found for ID '{prediction_id}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error retrieving feature importance for prediction '{prediction_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"XGBoost service error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error retrieving feature importance for prediction '{prediction_id}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving feature importance.")

# Add other endpoints as needed based on tests and service interface
# e.g., /integrate-digital-twin 
