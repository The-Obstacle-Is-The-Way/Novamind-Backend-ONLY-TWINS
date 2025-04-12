# -*- coding: utf-8 -*-
"""
Unit tests for the Biometric Correlation Model Service.

These tests verify that the Biometric Correlation Model Service correctly
analyzes correlations between biometric data and mental health indicators.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.biometric_correlation.model_service import BiometricCorrelationService
from app.infrastructure.ml.biometric_correlation.lstm_model import BiometricCorrelationModel


class TestBiometricCorrelationService:
    """Tests for the BiometricCorrelationService."""

    @pytest.fixture
    def mock_lstm_model(self):
        """Create a mock BiometricLSTMModel."""
        model = AsyncMock(spec=BiometricCorrelationModel)
        model.is_initialized = True
        model.analyze_correlations = AsyncMock(return_value={)
            "correlations": [
                {
                    "biometric_type": "heart_rate_variability",
                    "symptom_type": "anxiety",
                    "coefficient": -0.72,
                    "lag_hours": 8,
                    "confidence": 0.85,
                    "p_value": 0.002
                },
                {
                    "biometric_type": "sleep_duration",
                    "symptom_type": "mood",
                    "coefficient": 0.65,
                    "lag_hours": 24,
                    "confidence": 0.82,
                    "p_value": 0.005
                }
            ],
            "model_metrics": {
                "accuracy": 0.87,
                "false_positive_rate": 0.08,
                "lag_prediction_mae": 2.3
            }
(        })
        return model

    @pytest.fixture
    def service(self, mock_lstm_model, tmp_path):
        """Create a BiometricCorrelationService with mock dependencies."""
        # Create a temporary model directory
        model_dir = str(tmp_path / "models")
        
        # Create service with the correct parameters
    service = BiometricCorrelationService()
    model_dir=model_dir,
    model_path=None,
    biometric_features=["heart_rate_variability", "sleep_duration", "physical_activity"],
    mental_health_indicators=["anxiety", "mood"]
(    )
        
        # Replace the model with our mock
    service.model = mock_lstm_model
        
#     return service # FIXME: return outside function

    @pytest.fixture
    def sample_biometric_data(self):
        """Create sample biometric data for testing."""
        # Heart rate variability data
        hrv_dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
        hrv_data = {
            "heart_rate_variability": [
                {
                    "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "value": 45 + np.random.normal(0, 5)
                } for dt in hrv_dates
            ]
        }
        
        # Sleep duration data
    sleep_dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
    sleep_data = {
    "sleep_duration": [
    {
    "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "value": 7 + np.random.normal(0, 1)
    } for dt in sleep_dates
    ]
    }
        
        # Physical activity data
    activity_dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
    activity_data = {
    "physical_activity": [
    {
    "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "value": 30 + np.random.normal(0, 10)
    } for dt in activity_dates
    ]
    }
        
        # Combine all data
    biometric_data = {
    **hrv_data,
    **sleep_data,
    **activity_data
    }
        
#     return biometric_data # FIXME: return outside function

    @pytest.fixture
    def sample_patient_id(self):
        """Create a sample patient ID."""
        
    return str(uuid4())

    async def test_analyze_correlations_success(self, service, mock_lstm_model, sample_biometric_data, sample_patient_id):
    """Test that analyze_correlations correctly processes biometric data and returns correlations."""
        # Setup
    lookback_days = 30
    correlation_threshold = 0.3
        
        # Execute
    result = await service.analyze_correlations()
    patient_id=sample_patient_id,
    biometric_data=sample_biometric_data,
    lookback_days=lookback_days,
    correlation_threshold=correlation_threshold
(    )
        
        # Verify
    assert "patient_id" in result
    assert result["patient_id"] == sample_patient_id
    assert "reliability" in result
    assert "correlations" in result
    assert "insights" in result
    assert "biometric_coverage" in result
    assert "model_metrics" in result
        
        # Verify model was called
    mock_lstm_model.analyze_correlations.assert_called_once()
        
        # Verify correlations structure
    for correlation in result["correlations"]:
    assert "biometric_type" in correlation
    assert "symptom_type" in correlation
    assert "coefficient" in correlation
    assert "lag_hours" in correlation
    assert "confidence" in correlation
    assert "p_value" in correlation
            
        # Verify insights structure
    for insight in result["insights"]:
    assert "type" in insight
    assert "message" in insight
    assert "action" in insight

    async def test_analyze_correlations_empty_data(self, service, sample_patient_id):
    """Test that analyze_correlations handles empty biometric data gracefully."""
        # Setup
    empty_data = {}
        
        # Execute and verify exception is raised
    with pytest.raises(ValueError) as excinfo:
    await service.analyze_correlations()
    patient_id=sample_patient_id,
    biometric_data=empty_data,
    lookback_days=30
(    )
        
    assert "Empty biometric data" in str(excinfo.value)

    async def test_analyze_correlations_insufficient_data(self, service, sample_patient_id):
    """Test that analyze_correlations handles insufficient biometric data gracefully."""
        # Setup
    insufficient_data = {
    "heart_rate_variability": [
    {
    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "value": 45
    }
    ]
    }
        
        # Execute
    result = await service.analyze_correlations()
    patient_id=sample_patient_id,
    biometric_data=insufficient_data,
    lookback_days=30
(    )
        
        # Verify
    assert "patient_id" in result
    assert result["patient_id"] == sample_patient_id
    assert "reliability" in result
    assert result["reliability"] == "low"
    assert "correlations" in result
    assert len(result["correlations"]) == 0
    assert "insights" in result
    assert len(result["insights"]) == 0
    assert "warning" in result
    assert "insufficient_data" in result["warning"]

    async def test_analyze_correlations_model_error(self, service, mock_lstm_model, sample_biometric_data, sample_patient_id):
    """Test that analyze_correlations handles model errors gracefully."""
        # Setup
    mock_lstm_model.analyze_correlations.side_effect = Exception("Model error")
        
        # Execute
    result = await service.analyze_correlations()
    patient_id=sample_patient_id,
    biometric_data=sample_biometric_data,
    lookback_days=30
(    )
        
        # Verify
    assert "patient_id" in result
    assert result["patient_id"] == sample_patient_id
    assert "error" in result
    assert "Model error" in result["error"]
    assert "correlations" in result
    assert len(result["correlations"]) == 0
    assert "insights" in result
    assert len(result["insights"]) == 0

    async def test_preprocess_biometric_data(self, service, sample_biometric_data):
    """Test that _preprocess_biometric_data correctly transforms the input data."""
        # Setup
    with patch.object(service, '_preprocess_biometric_data', wraps=service._preprocess_biometric_data) as mock_preprocess:
            
            # Execute
            
            # Execute
    await service.analyze_correlations()
    patient_id=str(uuid4()),
    biometric_data=sample_biometric_data,
    lookback_days=30
(    )
            
            # Verify
    mock_preprocess.assert_called_once_with(sample_biometric_data, 30)
            
            # Call directly to test
    processed_data = service._preprocess_biometric_data(sample_biometric_data, 30)
            
            # Verify structure
    assert isinstance(processed_data, dict)
    assert "heart_rate_variability" in processed_data
    assert "sleep_duration" in processed_data
    assert "physical_activity" in processed_data
            
            # Verify data conversion
    for key, data in processed_data.items():
    assert isinstance(data, pd.DataFrame)
    assert "timestamp" in data.columns
    assert "value" in data.columns
                
    async def test_validate_biometric_data(self, service):
    """Test that _validate_biometric_data correctly validates input data."""
        # Valid data
    valid_data = {
    "heart_rate": [
    {
    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "value": 72
    }
    ]
    }
        
        # Invalid data - missing timestamp
    invalid_data_1 = {
    "heart_rate": [
    {
    "value": 72
    }
    ]
    }
        
        # Invalid data - missing value
    invalid_data_2 = {
    "heart_rate": [
    {
    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    ]
    }
        
        # Verify validation works
    assert service._validate_biometric_data(valid_data) == True
        
        # Verify validation fails on invalid data
    with pytest.raises(ValueError):
    service._validate_biometric_data(invalid_data_1)
            
    with pytest.raises(ValueError):
    service._validate_biometric_data(invalid_data_2)