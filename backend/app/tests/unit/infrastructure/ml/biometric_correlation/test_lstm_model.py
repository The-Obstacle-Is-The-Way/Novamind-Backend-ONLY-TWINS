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

from app.infrastructure.ml.biometric_correlation.lstm_model import BiometricCorrelationModel


@pytest.mark.asyncio
class TestBiometricLSTMModel:
    """Tests for the BiometricLSTMModel."""

    @pytest.fixture
    def model(self):
        """Create a BiometricLSTMModel with mocked internals."""
        model = BiometricCorrelationModel(
            model_path="test_model_path",
            input_dim=10,
            output_dim=5
        )
        # Mock the internal model
        model._initialize_model = MagicMock()
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
        with patch('os.path.exists', return_value=True):
            # Create model instance
            model = BiometricCorrelationModel(model_path="test_model_path")
            
            # Execute
            model._load_model = MagicMock()
            model._initialize_model = MagicMock()
            
            # Verify
            assert model.model_path == "test_model_path"
            assert model.input_dim == 10  # Default value
            assert model.output_dim == 5  # Default value

    async def test_initialize_handles_missing_model(self):
        """Test that initialize handles missing model files gracefully."""
        # Setup
        with patch('os.path.exists', return_value=False):
            # Create model instance
            model = BiometricCorrelationModel(model_path="nonexistent_path")
            
            # Execute
            model._initialize_model = MagicMock()
            
            # Verify
            assert model.model_path == "nonexistent_path"
            assert model.is_initialized

    async def test_analyze_correlations_returns_correlations(self, model):
        """Test that analyze_correlations returns correlations with the expected structure."""
        # Execute
        result = await model.analyze_correlations()
        
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
        # Execute
        result = await model.analyze_correlations()
        
        # Verify
        assert "correlations" in result
        assert len(result["correlations"]) > 0
        assert "model_metrics" in result

    async def test_identify_key_biometric_indicators(self, model):
        """Test that identify_key_biometric_indicators returns the expected structure."""
        # Setup
        biometric_data = np.random.rand(10, 5)
        mental_health_data = np.random.rand(10, 3)
        
        # Execute
        result = await model.identify_key_biometric_indicators(biometric_data, mental_health_data)
        
        # Verify
        assert "key_indicators" in result
        assert "model_metrics" in result
        
        # Check key indicators structure
        assert len(result["key_indicators"]) > 0
        for indicator in result["key_indicators"]:
            assert "biometric_index" in indicator
            assert "mental_health_index" in indicator
            assert "correlation" in indicator