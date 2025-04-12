# -*- coding: utf-8 -*-
"""
Unit tests for the Symptom Forecasting Transformer Model.

These tests verify that the Transformer Model correctly processes
time series data and generates accurate forecasts.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.symptom_forecasting.transformer_model import SymptomTransformerModel
from app.core.interfaces.ml.base_model import BaseMLModel


class TestTransformerTimeSeriesModel:
    """Tests for the TransformerTimeSeriesModel."""

    @pytest.fixture
    def model(self):
        """Create a TransformerTimeSeriesModel with mocked internals."""
        with patch('app.infrastructure.ml.symptom_forecasting.transformer_model.torch', autospec=True), \
             patch('app.infrastructure.ml.symptom_forecasting.transformer_model.TransformerModel', autospec=True):
            model = SymptomTransformerModel(
                model_path="test_model_path",
                device="cpu",
                embedding_dim=64,
                num_heads=4,
                num_encoder_layers=3,
                num_decoder_layers=3
            )
            # Mock the internal PyTorch model
            model._model = MagicMock()
            model._model.predict = MagicMock(return_value=(
                np.array([4.2, 4.0, 3.8, 3.5]),  # predictions
                np.array([0.2, 0.2, 0.2, 0.2])   # std
            ))
            model.is_initialized = True
            return model

    @pytest.fixture
    def sample_input_data(self):
        """Create sample input data for testing."""
        # Create a DataFrame with symptom severity data
        dates = pd.date_range(start=datetime.now() - timedelta(days=10), periods=10, freq='D')
        data = {
            'date': dates,
            'symptom_type': ['anxiety'] * 10,
            'severity': [5, 6, 7, 6, 5, 4, 5, 6, 5, 4]
        }
        return pd.DataFrame(data)

    async def test_initialize_loads_model(self):
        """Test that initialize loads the model correctly."""
        # Setup
        with patch('app.infrastructure.ml.symptom_forecasting.transformer_model.torch', autospec=True) as mock_torch, \
             patch('app.infrastructure.ml.symptom_forecasting.transformer_model.TransformerModel', autospec=True) as mock_transformer_cls, \
             patch('app.infrastructure.ml.symptom_forecasting.transformer_model.os.path.exists', return_value=True):
            
            # Create model instance
            model = SymptomTransformerModel(model_path="test_model_path")
            
            # Mock torch.load to return a mock model
            mock_model = MagicMock()
            mock_torch.load.return_value = mock_model
            
            # Execute
            await model.initialize()
            
            # Verify
            mock_torch.load.assert_called_once()
            assert model.is_initialized
            assert model._model is not None

    async def test_initialize_handles_missing_model(self):
        """Test that initialize handles missing model files gracefully."""
        # Setup
        with patch('app.infrastructure.ml.symptom_forecasting.transformer_model.torch', autospec=True), \
             patch('app.infrastructure.ml.symptom_forecasting.transformer_model.TransformerModel', autospec=True) as mock_transformer_cls, \
             patch('app.infrastructure.ml.symptom_forecasting.transformer_model.os.path.exists', return_value=False):
            
            # Create model instance
            model = SymptomTransformerModel(model_path="nonexistent_path")
            
            # Execute
            await model.initialize()
            
            # Verify
            mock_transformer_cls.assert_called_once()
            assert model.is_initialized
            assert model._model is not None

    async def test_predict_returns_forecast(self, model, sample_input_data):
        """Test that predict returns a forecast with the expected structure."""
        # Execute
        result = await model.predict(sample_input_data, horizon=4)
        
        # Verify
        assert "predictions" in result
        assert "std" in result
        assert "model_metrics" in result
        
        # Check predictions shape
        assert len(result["predictions"]) == 4
        assert len(result["std"]) == 4
        
        # Check metrics
        assert "mae" in result["model_metrics"]
        assert "rmse" in result["model_metrics"]

    async def test_predict_with_quantiles(self, model, sample_input_data):
        """Test that predict handles quantile predictions correctly."""
        # Setup
        quantiles = [0.1, 0.5, 0.9]
        
        # Execute
        result = await model.predict(sample_input_data, horizon=4, quantiles=quantiles)
        
        # Verify
        assert "quantile_predictions" in result
        assert len(result["quantile_predictions"]) == len(quantiles)
        assert "0.1" in result["quantile_predictions"]
        assert "0.5" in result["quantile_predictions"]
        assert "0.9" in result["quantile_predictions"]
        
        # Check each quantile has the right shape
        for q in quantiles:
            q_str = str(q)
            assert len(result["quantile_predictions"][q_str]) == 4

    async def test_predict_handles_empty_data(self, model):
        """Test that predict handles empty input data gracefully."""
        # Setup
        empty_df = pd.DataFrame()
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
            await model.predict(empty_df, horizon=4)
        
        assert "Empty input data" in str(excinfo.value)

    async def test_predict_handles_missing_columns(self, model):
        """Test that predict handles input data with missing required columns."""
        # Setup
        incomplete_df = pd.DataFrame({
            'date': pd.date_range(start=datetime.now() - timedelta(days=5), periods=5, freq='D'),
            # Missing 'severity' column
            'symptom_type': ['anxiety'] * 5
        })
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
            await model.predict(incomplete_df, horizon=4)
        
        assert "Missing required column" in str(excinfo.value)

    async def test_preprocess_input_data(self, model, sample_input_data):
        """Test that _preprocess_input_data correctly transforms the input data."""
        # Setup
        with patch.object(model, '_preprocess_input_data', wraps=model._preprocess_input_data) as mock_preprocess:
            
            # Execute
            await model.predict(sample_input_data, horizon=4)
            
            # Verify
            mock_preprocess.assert_called_once_with(sample_input_data)
            
            # Get the processed data
            processed_data = mock_preprocess.return_value
            # Verify the processed data has the expected structure
            assert isinstance(processed_data, np.ndarray)
            assert processed_data.ndim == 2  # 2D array: [time_steps, features]
            assert processed_data.shape[0] == len(sample_input_data)  # Same number of time steps

    async def test_postprocess_predictions(self, model, sample_input_data):
        """Test that _postprocess_predictions correctly transforms the model output."""
        # Setup
        raw_predictions = np.array([4.2, 4.0, 3.8, 3.5])
        raw_std = np.array([0.2, 0.2, 0.2, 0.2])
        
        with patch.object(model, '_postprocess_predictions', wraps=model._postprocess_predictions) as mock_postprocess:
            
            # Execute
            await model.predict(sample_input_data, horizon=4)
            
            # Verify
            mock_postprocess.assert_called_once()
            
            # Call directly to test
            result = model._postprocess_predictions(raw_predictions, raw_std)
            
            # Verify the result has the expected structure
            assert "predictions" in result
            assert "std" in result
            assert "model_metrics" in result
    
    async def test_get_model_info(self, model):
        """Test that get_model_info returns information about the model."""
        # Execute
        info = await model.get_model_info()
        
        # Verify
        assert "name" in info
        assert "version" in info
        assert "description" in info
        assert "parameters" in info
        assert info["name"] == "SymptomTransformerModel"
        assert "embedding_dim" in info["parameters"]
        assert "num_heads" in info["parameters"]