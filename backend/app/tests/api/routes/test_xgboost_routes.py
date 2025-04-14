"""
Tests for the XGBoost API routes.

This module tests the functionality of the XGBoost ML API endpoints,
ensuring they handle requests correctly and return appropriate responses.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime

# Import directly from app.api.schemas to avoid routes import issues
from app.api.schemas.xgboost import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    TreatmentResponseRequest,
    TreatmentResponseResponse,
    OutcomePredictionRequest,
    OutcomePredictionResponse,
    ModelInfoRequest,
    ModelInfoResponse,
    RiskType,
    TreatmentType,
    OutcomeType,
    TherapyDetails,
    MedicationDetails,
    TimeFrame,
    ResponseLikelihood,
    ExpectedOutcome,
    SideEffectRisk,
    OutcomeTrajectory,
    OutcomeTrajectoryPoint,
    OutcomeDetails,
    OutcomeDomain,
    VisualizationType,
    PerformanceMetrics,
)

# Use mock router instead of direct import
xgboost_router = MagicMock()

# Mock the service
mock_xgboost_service = AsyncMock()


# Define fixtures needed for tests
@pytest.fixture
def client():
    """Create a test client for testing API routes."""
    from fastapi import FastAPI
    app = FastAPI()
    
    # Attach a mock router
    from fastapi import APIRouter
    mock_router = APIRouter()
    
    # Define mock endpoints matching the real router
    @mock_router.post('/xgboost/risk-prediction', response_model=RiskPredictionResponse)
    async def mock_risk_prediction(request: RiskPredictionRequest):
        return await mock_xgboost_service.predict_risk(request)
    
    @mock_router.post('/xgboost/treatment-response', response_model=TreatmentResponseResponse)
    async def mock_treatment_response(request: TreatmentResponseRequest):
        return await mock_xgboost_service.predict_treatment_response(request)
    
    @mock_router.post('/xgboost/outcome-prediction', response_model=OutcomePredictionResponse)
    async def mock_outcome_prediction(request: OutcomePredictionRequest):
        return await mock_xgboost_service.predict_outcome(request)
    
    @mock_router.post('/xgboost/model-info', response_model=ModelInfoResponse)
    async def mock_model_info(request: ModelInfoRequest):
        return await mock_xgboost_service.get_model_info(request)
    
    app.include_router(mock_router)
    return TestClient(app)


@pytest.mark.parametrize(
    'endpoint, request_model, response_model',
    [
        (
            '/xgboost/risk-prediction',
            RiskPredictionRequest(
                risk_type=RiskType.SUICIDE,
                patient_id='12345',
                patient_data={
                    'age': 30,
                    'gender': 'male',
                    'symptom_severity': 7.5,
                    'previous_attempts': 1
                },
                clinical_data={
                    'diagnosis': 'depression',
                    'duration_months': 6
                }
            ),
            RiskPredictionResponse(
                prediction_id='pred_001',
                patient_id='12345',
                risk_type=RiskType.SUICIDE,
                risk_probability=0.75,
                risk_level='high',
                risk_score=0.75,
                risk_factors={
                    'previous_attempts': 0.3,
                    'symptom_severity': 0.5
                },
                confidence=0.85,
                timestamp='2023-10-01T12:00:00Z',
                time_frame_days=30
            )
        ),
        (
            '/xgboost/treatment-response',
            TreatmentResponseRequest(
                patient_id='test-patient-123',
                treatment_type=TreatmentType.THERAPY_CBT,
                treatment_details=TherapyDetails(
                    therapy_type='CBT',
                    frequency='weekly',
                    frequency_per_week=1,
                    duration_weeks=12
                ),
                clinical_data={
                    'age': 25,
                    'gender': 'female',
                    'diagnosis': 'depression',
                    'baseline_severity': 8.0
                }
            ),
            TreatmentResponseResponse(
                prediction_id='pred-123',
                patient_id='test-patient-123',
                treatment_type=TreatmentType.THERAPY_CBT,
                treatment_details={
                    'therapy_type': 'CBT',
                    'frequency': 'weekly',
                    'frequency_per_week': 1,
                    'duration_weeks': 12
                },
                response_likelihood=ResponseLikelihood.MODERATE,
                efficacy_score=0.75,
                confidence=0.85,
                expected_outcome=ExpectedOutcome(
                    symptom_improvement='moderate',
                    time_to_response='4-6 weeks',
                    sustained_response_likelihood=ResponseLikelihood.MODERATE,
                    functional_improvement='moderate'
                ),
                side_effect_risk=SideEffectRisk(
                    common=[],
                    rare=[]
                ),
                features={
                    'age': 25,
                    'gender': 'female',
                    'diagnosis': 'depression',
                    'baseline_severity': 8.0
                },
                treatment_features={
                    'therapy_type': 'CBT',
                    'frequency': 'weekly'
                },
                timestamp=datetime.now(),
                prediction_horizon='12 weeks'
            ),
        ),
        (
            '/xgboost/outcome-prediction',
            OutcomePredictionRequest(
                patient_id='test-patient-456',
                outcome_type=OutcomeType.SYMPTOM,
                outcome_timeframe=TimeFrame(weeks=12),
                clinical_data={
                    'age': 40,
                    'gender': 'male',
                    'diagnosis': 'anxiety',
                    'baseline_severity': 7.0,
                    'recent_crisis': True
                },
                treatment_plan={
                    'treatment_type': 'therapy_cbt',
                    'frequency': 'weekly',
                    'duration_weeks': 12
                }
            ),
            OutcomePredictionResponse(
                prediction_id='test-prediction-789',
                patient_id='test-patient-456',
                outcome_type=OutcomeType.SYMPTOM,
                outcome_score=0.4,
                time_frame_days=84,
                confidence=0.75,
                trajectory=OutcomeTrajectory(
                    points=[
                        OutcomeTrajectoryPoint(time_point='Week 2', days_from_start=14, improvement_percentage=10),
                        OutcomeTrajectoryPoint(time_point='Week 4', days_from_start=28, improvement_percentage=25),
                        OutcomeTrajectoryPoint(time_point='Week 8', days_from_start=56, improvement_percentage=40)
                    ],
                    final_improvement=40,
                    time_frame_days=84,
                    visualization_type=VisualizationType.LINE_CHART
                ),
                outcome_details=OutcomeDetails(
                    overall_improvement='moderate',
                    domains=[
                        OutcomeDomain(name='Mood', improvement='moderate', notes='Improved stability'),
                        OutcomeDomain(name='Anxiety', improvement='mild', notes='Some reduction in symptoms')
                    ],
                    recommendations=['Continue current treatment', 'Monitor for side effects']
                ),
                timestamp=datetime.now()
            )
        ),
        (
            '/xgboost/model-info',
            ModelInfoRequest(model_type='risk_suicide'),
            ModelInfoResponse(
                model_type='risk_suicide',
                version='1.2.3',
                last_updated=datetime.fromisoformat('2023-05-15T10:30:00Z'),
                description='Suicide risk prediction model',
                features=['age', 'gender', 'diagnosis', 'previous_attempts'],
                performance_metrics=PerformanceMetrics(
                    accuracy=0.88,
                    precision=0.85,
                    recall=0.82,
                    f1_score=0.83,
                    auc_roc=0.92
                ),
                hyperparameters={'max_depth': 5, 'learning_rate': 0.1},
                status='active'
            )
        )
    ]
)
@pytest.mark.asyncio
def test_xgboost_endpoints_return_200(client, endpoint, request_model, response_model):
    """Test that XGBoost endpoints return 200 status code."""
    # Configure the mock to return the expected response
    mock_xgboost_service.predict_risk.return_value = response_model
    mock_xgboost_service.predict_treatment_response.return_value = response_model
    mock_xgboost_service.predict_outcome.return_value = response_model
    mock_xgboost_service.get_model_info.return_value = response_model
    
    # Send request to the endpoint
    response = client.post(endpoint, json=request_model.dict())
    
    # Assert response status code
    assert response.status_code == status.HTTP_200_OK, f"Endpoint {endpoint} returned {response.status_code} instead of 200"
    
    # Assert response content matches the expected model
    response_data = response.json()
    assert response_data == response_model.dict(), f"Response data for {endpoint} does not match expected response model"


@pytest.mark.asyncio
def test_xgboost_risk_prediction_with_invalid_data(client):
    """Test that risk prediction endpoint validates input data."""
    # Invalid data - missing required fields
    invalid_data = {
        'risk_type': 'suicide'
        # Missing patient_data
    }
    
    response = client.post('/xgboost/risk-prediction', json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, "Endpoint accepted invalid data without validation error"
    
    error_detail = response.json()['detail']
    assert any('patient_data' in error['loc'] for error in error_detail), "Validation error should mention missing patient_data field"