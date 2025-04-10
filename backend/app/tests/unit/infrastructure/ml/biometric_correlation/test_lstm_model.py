# -*- coding: utf-8 -*-
"""
Unit tests for the Biometric Correlation LSTM Model.

These tests verify that the LSTM Model correctly processes
biometric data and identifies correlations with mental health indicators.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.biometric_correlation.lstm_model import BiometricCorrelationModel # Corrected class name


class TestBiometricLSTMModel:
    """Tests for the BiometricLSTMModel."""

    @pytest.fixture
    def model(self):
        """Create a BiometricLSTMModel with mocked internals."""
        with patch('app.infrastructure.ml.biometric_correlation.lstm_model.torch', autospec=True), \
             patch('app.infrastructure.ml.biometric_correlation.lstm_model.LSTMCorrelationModel', autospec=True):
            model = BiometricLSTMModel(
                model_path="test_model_path",
                device="cpu",
                hidden_size=64,
                num_layers=2,
                dropout=0.2
            )
            # Mock the internal PyTorch model
            model._model = MagicMock()
            model._model.analyze = MagicMock(return_value={
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
                "metrics": {
                    "accuracy": 0.87,
                    "false_positive_rate": 0.08,
                    "lag_prediction_mae": 2.3
                }
            })
            model.is_initialized = True
            return model

    @pytest.fixture
    def sample_biometric_data(self):
        """Create sample biometric data for testing."""
        # Create DataFrames for different biometric types
        hrv_data = pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D'),
            'value': [45 + np.random.normal(0, 5) for _ in range(30)]
        })
        
        sleep_data = pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D'),
            'value': [7 + np.random.normal(0, 1) for _ in range(30)]
        })
        
        activity_data = pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D'),
            'value': [30 + np.random.normal(0, 10) for _ in range(30)]
        })
        
        # Combine into a dictionary
        return {
            "heart_rate_variability": hrv_data,
            "sleep_duration": sleep_data,
            "physical_activity": activity_data
        }

    @pytest.fixture
    def sample_symptom_data(self):
        """Create sample symptom data for testing."""
        # Create DataFrames for different symptom types
        anxiety_data = pd.DataFrame({
            'date': pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D'),
            'severity': [5 + np.random.normal(0, 1) for _ in range(30)]
        })
        
        mood_data = pd.DataFrame({
            'date': pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D'),
            'severity': [6 + np.random.normal(0, 1.5) for _ in range(30)]
        })
        
        # Combine into a dictionary
        return {
            "anxiety": anxiety_data,
            "mood": mood_data
        }

    async def test_initialize_loads_model(self):
        """Test that initialize loads the model correctly."""
        # Setup
        with patch('app.infrastructure.ml.biometric_correlation.lstm_model.torch', autospec=True) as mock_torch, \
             patch('app.infrastructure.ml.biometric_correlation.lstm_model.LSTMCorrelationModel', autospec=True) as mock_lstm_cls, \
             patch('app.infrastructure.ml.biometric_correlation.lstm_model.os.path.exists', return_value=True):
            
            # Create model instance
            model = BiometricLSTMModel(model_path="test_model_path")
            
            # Mock torch.load to return a mock model
            mock_model = MagicMock()
            mock_torch.load.return_value = {
                'model': mock_model,
                'config': {'hidden_size': 64, 'num_layers': 2},
                'metadata': {'version': '1.0'}
            }
            
            # Execute
            await model.initialize()
            
            # Verify
            mock_torch.load.assert_called_once()
            assert model.is_initialized
            assert model._model is not None
            assert model._metadata == {'version': '1.0'}

    async def test_initialize_handles_missing_model(self):
        """Test that initialize handles missing model files gracefully."""
        # Setup
        with patch('app.infrastructure.ml.biometric_correlation.lstm_model.torch', autospec=True), \
             patch('app.infrastructure.ml.biometric_correlation.lstm_model.LSTMCorrelationModel', autospec=True) as mock_lstm_cls, \
             patch('app.infrastructure.ml.biometric_correlation.lstm_model.os.path.exists', return_value=False):
            
            # Create model instance
            model = BiometricLSTMModel(model_path="nonexistent_path")
            
            # Execute
            await model.initialize()
            
            # Verify
            mock_lstm_cls.assert_called_once()
            assert model.is_initialized
            assert model._model is not None

    async def test_analyze_correlations_returns_correlations(self, model, sample_biometric_data, sample_symptom_data):
        """Test that analyze_correlations returns correlations with the expected structure."""
        # Execute
        result = await model.analyze_correlations(sample_biometric_data, sample_symptom_data)
        
        # Verify
        assert "correlations" in result
        assert "model_metrics" in result
        
        # Check correlations structure
        assert len(result["correlations"]) == 2
        for correlation in result["correlations"]:
            assert "biometric_type" in correlation
            assert "symptom_type" in correlation
            assert "coefficient" in correlation
            assert "lag_hours" in correlation
            assert "confidence" in correlation
            assert "p_value" in correlation
        
        # Check metrics structure
        assert "accuracy" in result["model_metrics"]
        assert "false_positive_rate" in result["model_metrics"]
        assert "lag_prediction_mae" in result["model_metrics"]

    async def test_analyze_correlations_handles_empty_data(self, model):
        """Test that analyze_correlations handles empty input data gracefully."""
        # Setup
        empty_biometric_data = {}
        empty_symptom_data = {}
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
            await model.analyze_correlations(empty_biometric_data, empty_symptom_data)
        
        assert "Empty input data" in str(excinfo.value)

    async def test_analyze_correlations_handles_missing_columns(self, model, sample_biometric_data):
        """Test that analyze_correlations handles input data with missing required columns."""
        # Setup
        incomplete_symptom_data = {
            "anxiety": pd.DataFrame({
                # Missing 'severity' column
                'date': pd.date_range(start=datetime.now() - timedelta(days=5), periods=5, freq='D')
            })
        }
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
            await model.analyze_correlations(sample_biometric_data, incomplete_symptom_data)
        
        assert "Missing required column" in str(excinfo.value)

    async def test_preprocess_data(self, model, sample_biometric_data, sample_symptom_data):
        """Test that _preprocess_data correctly transforms the input data."""
        # Setup
        with patch.object(model, '_preprocess_data', wraps=model._preprocess_data) as mock_preprocess:
            
            # Execute
            await model.analyze_correlations(sample_biometric_data, sample_symptom_data)
            
            # Verify
            mock_preprocess.assert_called_once_with(sample_biometric_data, sample_symptom_data)
            
            # Call directly to test
            processed_biometric, processed_symptom = model._preprocess_data(sample_biometric_data, sample_symptom_data)
            
            # Verify the processed data has the expected structure
            assert isinstance(processed_biometric, dict)
            assert isinstance(processed_symptom, dict)
            
            # Check biometric data
            for biometric_type, data in processed_biometric.items():
                assert isinstance(data, np.ndarray)
                assert data.ndim == 2  # 2D array: [time_steps, features]
                
            # Check symptom data
            for symptom_type, data in processed_symptom.items():
                assert isinstance(data, np.ndarray)
                assert data.ndim == 1  # 1D array: [time_steps]

    async def test_align_time_series(self, model):
        """Test that _align_time_series correctly aligns time series data."""
        # Setup
        biometric_df = pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now() - timedelta(days=10), periods=10, freq='D'),
            'value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        
        symptom_df = pd.DataFrame({
            'date': pd.date_range(start=datetime.now() - timedelta(days=8), periods=8, freq='D'),
            'severity': [5, 6, 7, 8, 9, 10, 11, 12]
        })
        
        # Execute
        aligned_biometric, aligned_symptom = model._align_time_series(biometric_df, symptom_df)
        
        # Verify
        assert len(aligned_biometric) == len(aligned_symptom)
        assert len(aligned_biometric) == 8  # Should match the overlap period
        
        # Check values are correctly aligned
        np.testing.assert_array_equal(aligned_biometric, [3, 4, 5, 6, 7, 8, 9, 10])
        np.testing.assert_array_equal(aligned_symptom, [5, 6, 7, 8, 9, 10, 11, 12])

    async def test_calculate_lag_correlations(self, model):
        """Test that _calculate_lag_correlations correctly calculates lagged correlations."""
        # Setup
        biometric_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        symptom_data = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])  # Offset by 1
        max_lag = 3
        
        # Execute
        correlations = model._calculate_lag_correlations(biometric_data, symptom_data, max_lag)
        
        # Verify
        assert len(correlations) == max_lag + 1  # 0 to max_lag
        
        # Lag 1 should have the highest correlation (perfect correlation)
        assert correlations[1] > correlations[0]
        assert correlations[1] > correlations[2]
        assert correlations[1] > correlations[3]
        assert abs(correlations[1]) > 0.95  # Should be close to 1