# -*- coding: utf-8 -*-
"""
XGBoost Service API Endpoints.

Provides API endpoints for interacting with the XGBoost prediction service.
"""

import logging
import inspect
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body

# Import the xgboost DI and auth alias module (for tests and service)
import app.api.routes.xgboost as xgboost_routes
from app.core.services.ml.xgboost.interface import XGBoostInterface
from app.core.services.ml.xgboost.exceptions import (
    XGBoostServiceError,
    ValidationError,
    DataPrivacyError,
    ResourceNotFoundError,
    ModelNotFoundError,
    ServiceUnavailableError
)

# Authentication and DI dependencies now via alias module
# current_user and verify_provider_access imported above
from app.domain.models.user import User # Or appropriate user model

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["XGBoost ML"]
)

@router.post(
    "/predict/risk",
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
    "/risk",
    summary="Predict Patient Risk",
    description="Predicts various risk types (e.g., relapse, suicide) using XGBoost models.",
    status_code=status.HTTP_200_OK
)
async def predict_risk(
    patient_id: str = Body(...),
    risk_type: str = Body(...),
    clinical_data: Dict[str, Any] = Body(...),
    demographic_data: Optional[Dict[str, Any]] = Body(None),
    temporal_data: Optional[Dict[str, Any]] = Body(None),
    confidence_threshold: Optional[float] = Body(None),
    time_frame_days: Optional[int] = Body(None),
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
) -> Dict[str, Any]:
    """Endpoint to predict patient risk using XGBoost."""
    try:
        xgboost_routes.validate_permissions()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    try:
        # Determine which parameters to pass based on request
        if time_frame_days is not None:
            # Alias route with time_frame_days
            raw = xgboost_service.predict_risk(
                patient_id=patient_id,
                risk_type=risk_type,
                clinical_data=clinical_data,
                time_frame_days=time_frame_days
            )
        else:
            # ML route with demographic and confidence parameters
            raw = xgboost_service.predict_risk(
                patient_id=patient_id,
                risk_type=risk_type,
                clinical_data=clinical_data,
                demographic_data=demographic_data,
                temporal_data=temporal_data,
                confidence_threshold=confidence_threshold
            )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ValidationError as e:
        logger.warning(f"Validation error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DataPrivacyError as e:
        logger.warning(f"Data privacy error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sensitive information detected")
    except ModelNotFoundError as e:
        logger.error(f"Model not found for risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during risk prediction for patient {patient_id}")
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
@router.post(
    "/treatment-response",
    summary="Predict Treatment Response",
    description="Predicts patient response to specific treatments using XGBoost models.",
    status_code=status.HTTP_200_OK
)
async def predict_treatment_response(
    patient_id: str = Body(...),
    treatment_type: str = Body(...),
    treatment_details: Dict[str, Any] = Body(...),
    clinical_data: Dict[str, Any] = Body(...),
    genetic_data: Optional[Any] = Body(None),
    treatment_history: Optional[Any] = Body(None),
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
) -> Dict[str, Any]:
    """Endpoint to predict treatment response using XGBoost."""
    try:
        xgboost_routes.validate_permissions()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    try:
        # Determine which parameters to pass based on request
        if genetic_data is None and treatment_history is None:
            # Alias route without genetic context
            raw = xgboost_service.predict_treatment_response(
                patient_id=patient_id,
                treatment_type=treatment_type,
                treatment_details=treatment_details,
                clinical_data=clinical_data
            )
        else:
            # ML route with genetic and history data
            raw = xgboost_service.predict_treatment_response(
                patient_id=patient_id,
                treatment_type=treatment_type,
                treatment_details=treatment_details,
                clinical_data=clinical_data,
                genetic_data=genetic_data,
                treatment_history=treatment_history
            )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ValidationError as e:
        logger.warning(f"Validation error during treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found for treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable during treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during treatment response prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during treatment response prediction for patient {patient_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during treatment response prediction.")

@router.post(
    "/outcome-prediction",
    summary="Predict Clinical Outcome",
    description="Predicts clinical outcomes based on patient data and treatment plan using XGBoost models.",
    status_code=status.HTTP_200_OK
)
@router.post(
    "/predict/outcome",
    summary="Predict Clinical Outcome",
    description="Predicts clinical outcomes based on patient data and treatment plan using XGBoost models.",
    status_code=status.HTTP_200_OK
)
@router.post(
    "/outcome",
    summary="Predict Clinical Outcome",
    description="Predicts clinical outcomes based on patient data and treatment plan using XGBoost models.",
    status_code=status.HTTP_200_OK
)
async def predict_outcome(
    patient_id: str = Body(...),
    outcome_timeframe: Dict[str, Any] = Body(...),
    clinical_data: Dict[str, Any] = Body(...),
    treatment_plan: Dict[str, Any] = Body(...),
    social_determinants: Optional[Dict[str, Any]] = Body(None),
    comorbidities: Optional[Any] = Body(None),
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
) -> Dict[str, Any]:
    """Endpoint to predict clinical outcome using XGBoost."""
    try:
        xgboost_routes.validate_permissions()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    try:
        # Determine which parameters to pass based on request
        if social_determinants is None and comorbidities is None:
            # Alias route without extended parameters
            raw = xgboost_service.predict_outcome(
                patient_id=patient_id,
                outcome_timeframe=outcome_timeframe,
                clinical_data=clinical_data,
                treatment_plan=treatment_plan
            )
        else:
            # ML route with full context
            raw = xgboost_service.predict_outcome(
                patient_id=patient_id,
                outcome_timeframe=outcome_timeframe,
                clinical_data=clinical_data,
                treatment_plan=treatment_plan,
                social_determinants=social_determinants,
                comorbidities=comorbidities
            )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ValidationError as e:
        logger.warning(f"Validation error during outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found for outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable during outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except XGBoostServiceError as e:
        logger.error(f"XGBoost service error during outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during outcome prediction for patient {patient_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during outcome prediction.")

@router.get(
    "/model-info/{model_type}",
    summary="Get Model Information",
    description="Retrieves metadata and information about a specific XGBoost model.",
    status_code=status.HTTP_200_OK
)
async def get_model_info(
    model_type: str, # Or use ModelType enum if defined appropriately
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
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
    model_type: str = Body(...),
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
) -> Dict[str, Any]:
    """Endpoint to get information about an XGBoost model."""
    try:
        xgboost_routes.validate_permissions()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    try:
        raw = xgboost_service.get_model_info(model_type=model_type)
        info = await raw if inspect.isawaitable(raw) else raw
        return info
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except XGBoostServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving model information.")

@router.get(
    "/feature-importance/{model_type}",
    summary="Get Feature Importance",
    description="Retrieves feature importance scores for a specific prediction.",
    status_code=status.HTTP_200_OK
)
async def get_feature_importance(
    model_type: str,
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
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

@router.post(
    "/feature-importance",
    summary="Get Feature Importance",
    description="Retrieves feature importance for a specific prediction.",
    status_code=status.HTTP_200_OK
)
async def post_feature_importance(
    patient_id: str = Body(...),
    model_type: str = Body(...),
    prediction_id: str = Body(...),
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
) -> Dict[str, Any]:
    """Endpoint to get feature importance for a prediction."""
    try:
        xgboost_routes.validate_permissions()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    try:
        raw = xgboost_service.get_feature_importance(
            patient_id=patient_id,
            model_type=model_type,
            prediction_id=prediction_id
        )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except XGBoostServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving feature importance.")

@router.post(
    "/digital-twin-simulation",
    summary="Simulate Digital Twin",
    description="Simulates patient progression using digital twin concept.",
    status_code=status.HTTP_200_OK
)
async def digital_twin_simulation(
    request_data: Dict[str, Any] = Body(...),
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
) -> Dict[str, Any]:
    """Endpoint to simulate a digital twin using XGBoost."""
    raw = xgboost_service.simulate_digital_twin(
        patient_id=request_data["patient_id"],
        simulation_timeframe=request_data["simulation_timeframe"],
        treatment_plan=request_data["treatment_plan"],
        baseline_metrics=request_data["baseline_metrics"]
    )
    result = await raw if inspect.isawaitable(raw) else raw
    return result
   
@router.post(
    "/digital-twin-integration",
    summary="Integrate with Digital Twin",
    description="Integrates prediction results with the Digital Twin service.",
    status_code=status.HTTP_200_OK
)
async def integrate_with_digital_twin(
    patient_id: str = Body(...),
    profile_id: str = Body(...),
    prediction_id: str = Body(...),
    xgboost_service: XGBoostInterface = Depends(xgboost_routes.get_xgboost_service)
) -> Dict[str, Any]:
    """Endpoint to integrate prediction with Digital Twin."""
    try:
        xgboost_routes.validate_permissions()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    try:
        raw = xgboost_service.integrate_with_digital_twin(
            patient_id=patient_id,
            profile_id=profile_id,
            prediction_id=prediction_id
        )
        result = await raw if inspect.isawaitable(raw) else raw
        return result
    except XGBoostServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
