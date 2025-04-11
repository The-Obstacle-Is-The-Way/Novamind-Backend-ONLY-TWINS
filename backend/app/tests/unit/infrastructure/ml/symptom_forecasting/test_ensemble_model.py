# -*- coding: utf-8 -*-
"""
Unit tests for the Symptom Forecasting Ensemble Model.

These tests verify that the Ensemble Model correctly combines predictions
from multiple models to generate more accurate forecasts.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.symptom_forecasting.ensemble_model import SymptomForecastingEnsemble # Corrected @pytest.mark.db_required
class name:
from app.infrastructure.ml.base.base_model import BaseModel # Corrected class name


class TestSymptomForecastEnsembleModel:
    """Tests for the SymptomForecastEnsembleModel."""

    @pytest.fixture
    def mock_model_1(self):
        """Create a mock model for the ensemble."""
        model = AsyncMock(spec=BaseMLModel)
        model.name = "Model1"
        model.predict = AsyncMock(return_value={
            "predictions": np.array([4.2, 4.0, 3.8, 3.5]),
            "std": np.array([0.2, 0.2, 0.2, 0.2]),
            "model_metrics": {
                "mae": 0.42,
                "rmse": 0.68
            }
        })
        return model

    @pytest.fixture
    def mock_model_2(self):
        """Create another mock model for the ensemble."""
        model = AsyncMock(spec=BaseMLModel)
        model.name = "Model2"
        model.predict = AsyncMock(return_value={
            "predictions": np.array([4.3, 4.1, 3.9, 3.6]),
            "std": np.array([0.3, 0.3, 0.3, 0.3]),
            "model_metrics": {
                "mae": 0.47,
                "rmse": 0.72
            }
        })
        return model

    @pytest.fixture
    def ensemble_model(self, mock_model_1, mock_model_2):
        """Create an ensemble model with mock component models."""
        return SymptomForecastEnsembleModel(
            models=[mock_model_1, mock_model_2],
            weights={"Model1": 0.7, "Model2": 0.3}
        )

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

    async def test_predict_combines_model_predictions(self, ensemble_model, sample_input_data, mock_model_1, mock_model_2):
        """Test that predict correctly combines predictions from component models."""
        # Execute
        result = await ensemble_model.predict(sample_input_data, horizon=4)

        # Verify component models were called
        mock_model_1.predict.assert_called_once()
        mock_model_2.predict.assert_called_once()

        # Verify result structure
        assert "predictions" in result
        assert "std" in result
        assert "model_metrics" in result
        assert "contributing_models" in result

        # Verify ensemble calculation (weighted average)
        expected_predictions = (
            mock_model_1.predict.return_value["predictions"] * 0.7 +
            mock_model_2.predict.return_value["predictions"] * 0.3
        )
        np.testing.assert_array_almost_equal(result["predictions"], expected_predictions)

        # Verify contributing models are included
        assert "Model1" in result["contributing_models"]
        assert "Model2" in result["contributing_models"]
        assert result["contributing_models"]["Model1"]["weight"] == 0.7
        assert result["contributing_models"]["Model2"]["weight"] == 0.3

    async def test_predict_with_custom_weights(self, mock_model_1, mock_model_2, sample_input_data):
        """Test that predict respects custom weights provided at prediction time."""
        # Setup
        ensemble = SymptomForecastEnsembleModel(
            models=[mock_model_1, mock_model_2],
            weights={"Model1": 0.7, "Model2": 0.3}
        )

        # Execute with custom weights
        custom_weights = {"Model1": 0.4, "Model2": 0.6}
        result = await ensemble.predict(sample_input_data, horizon=4, weights=custom_weights)

        # Verify ensemble calculation with custom weights
        expected_predictions = (
            mock_model_1.predict.return_value["predictions"] * 0.4 +
            mock_model_2.predict.return_value["predictions"] * 0.6
        )
        np.testing.assert_array_almost_equal(result["predictions"], expected_predictions)

        # Verify contributing models reflect custom weights
        assert result["contributing_models"]["Model1"]["weight"] == 0.4
        assert result["contributing_models"]["Model2"]["weight"] == 0.6

    async def test_predict_handles_model_error(self, mock_model_1, mock_model_2, sample_input_data):
        """Test that predict handles errors in component models gracefully."""
        # Setup
        mock_model_1.predict.side_effect = Exception("Model error")
        ensemble = SymptomForecastEnsembleModel(
            models=[mock_model_1, mock_model_2],
            weights={"Model1": 0.5, "Model2": 0.5}
        )

        # Execute
        result = await ensemble.predict(sample_input_data, horizon=4)

        # Verify only working model is used
        assert "Model1" not in result["contributing_models"]
        assert "Model2" in result["contributing_models"]
        assert result["contributing_models"]["Model2"]["weight"] == 1.0

        # Verify predictions match the working model
        np.testing.assert_array_almost_equal(
            result["predictions"],
            mock_model_2.predict.return_value["predictions"]
        )

    async def test_predict_with_all_models_failing(self, mock_model_1, mock_model_2, sample_input_data):
        """Test that predict handles the case where all component models fail."""
        # Setup
        mock_model_1.predict.side_effect = Exception("Model 1 error")
        mock_model_2.predict.side_effect = Exception("Model 2 error")
        ensemble = SymptomForecastEnsembleModel(
            models=[mock_model_1, mock_model_2],
            weights={"Model1": 0.5, "Model2": 0.5}
        )

        # Execute and verify exception is raised
        with pytest.raises(Exception) as excinfo:
            await ensemble.predict(sample_input_data, horizon=4)
        
        assert "All models failed" in str(excinfo.value)

    async def test_calculate_confidence_intervals(self, ensemble_model, sample_input_data):
        """Test that confidence intervals are correctly calculated."""
        # Execute
        result = await ensemble_model.predict(sample_input_data, horizon=4)

        # Verify confidence intervals
        assert "confidence_intervals" in result
        assert "80%" in result["confidence_intervals"]
        assert "95%" in result["confidence_intervals"]
        
        # Verify structure of confidence intervals
        assert "lower" in result["confidence_intervals"]["80%"]
        assert "upper" in result["confidence_intervals"]["80%"]
        assert "lower" in result["confidence_intervals"]["95%"]
        assert "upper" in result["confidence_intervals"]["95%"]
        
        # Verify values (80% interval should be narrower than 95%)
        ci_80_width = (
            result["confidence_intervals"]["80%"]["upper"] - 
            result["confidence_intervals"]["80%"]["lower"]
        )
        ci_95_width = (
            result["confidence_intervals"]["95%"]["upper"] - 
            result["confidence_intervals"]["95%"]["lower"]
        )
        
        # 95% interval should be wider than 80% interval
        assert np.all(ci_95_width > ci_80_width)