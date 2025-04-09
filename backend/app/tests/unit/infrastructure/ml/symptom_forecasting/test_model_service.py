# -*- coding: utf-8 -*-
"""
Unit tests for the Symptom Forecasting Model Service.

These tests verify that the Symptom Forecasting Model Service correctly
processes patient symptom data and generates accurate forecasts.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.symptom_forecasting.model_service import SymptomForecastingService
from app.infrastructure.ml.symptom_forecasting.transformer_model import TransformerTimeSeriesModel
from app.infrastructure.ml.symptom_forecasting.xgboost_model import XGBoostTimeSeriesModel


class TestSymptomForecastingService:
    """Tests for the SymptomForecastingService."""

    @pytest.fixture
    def mock_transformer_model(self):
        """Create a mock TransformerTimeSeriesModel."""
        model = AsyncMock(spec=TransformerTimeSeriesModel)
        model.is_initialized = True
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
    def mock_xgboost_model(self):
        """Create a mock XGBoostTimeSeriesModel."""
        model = AsyncMock(spec=XGBoostTimeSeriesModel)
        model.is_initialized = True
        model.predict = AsyncMock(return_value={
            "predictions": np.array([4.3, 4.1, 3.9, 3.6]),
            "feature_importance": {"feature1": 0.5, "feature2": 0.3, "feature3": 0.2},
            "model_metrics": {
                "mae": 0.47,
                "rmse": 0.72
            }
        })
        return model

    @pytest.fixture
    def service(self, mock_transformer_model, mock_xgboost_model):
        """Create a SymptomForecastingService with mock dependencies."""
        return SymptomForecastingService(
            transformer_model=mock_transformer_model,
            xgboost_model=mock_xgboost_model,
            forecast_days=4,
            confidence_levels=[0.80, 0.95]
        )

    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data for testing."""
        return {
            "patient_id": str(uuid4()),
            "symptom_history": [
                {
                    "date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 5
                },
                {
                    "date": (datetime.now() - timedelta(days=9)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 6
                },
                {
                    "date": (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 7
                },
                {
                    "date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 6
                },
                {
                    "date": (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 5
                },
                {
                    "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 4
                },
                {
                    "date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 5
                },
                {
                    "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 6
                },
                {
                    "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 5
                },
                {
                    "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 4
                }
            ]
        }

    async def test_preprocess_patient_data_success(self, service, sample_patient_data):
        """Test that preprocess_patient_data correctly processes valid patient data."""
        # Execute
        df, metadata = await service.preprocess_patient_data(sample_patient_data)

        # Verify
        assert not df.empty
        assert "date" in df.columns
        assert "symptom_type" in df.columns
        assert "severity" in df.columns
        assert "normalization_params" in metadata
        assert "symptom_types" in metadata
        assert "date_range" in metadata
        assert "patient_id" in metadata
        assert metadata["patient_id"] == sample_patient_data["patient_id"]
        assert "anxiety" in metadata["symptom_types"]

    async def test_preprocess_patient_data_empty_history(self, service):
        """Test that preprocess_patient_data handles empty symptom history."""
        # Setup
        patient_data = {
            "patient_id": str(uuid4()),
            "symptom_history": []
        }

        # Execute
        df, metadata = await service.preprocess_patient_data(patient_data)

        # Verify
        assert df.empty
        assert "error" in metadata
        assert metadata["error"] == "insufficient_data"

    async def test_preprocess_patient_data_missing_columns(self, service):
        """Test that preprocess_patient_data handles missing required columns."""
        # Setup
        patient_data = {
            "patient_id": str(uuid4()),
            "symptom_history": [
                {
                    "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    # Missing symptom_type
                    "severity": 5
                }
            ]
        }

        # Execute
        df, metadata = await service.preprocess_patient_data(patient_data)

        # Verify
        assert df.empty
        assert "error" in metadata
        assert metadata["error"] == "missing_columns"

    async def test_generate_forecast_success(self, service, sample_patient_data, mock_transformer_model, mock_xgboost_model):
        """Test that generate_forecast correctly generates a forecast for valid patient data."""
        # Execute
        forecast = await service.generate_forecast(sample_patient_data)

        # Verify
        assert "forecast" in forecast
        assert "confidence_intervals" in forecast
        assert "reliability" in forecast
        assert "forecast_dates" in forecast
        assert "patient_id" in forecast
        assert forecast["patient_id"] == sample_patient_data["patient_id"]
        assert len(forecast["forecast"]) == 4  # 4 days forecast
        assert "80%" in forecast["confidence_intervals"]
        assert "95%" in forecast["confidence_intervals"]
        assert "lower" in forecast["confidence_intervals"]["80%"]
        assert "upper" in forecast["confidence_intervals"]["80%"]
        assert "contributing_models" in forecast
        assert "transformer" in forecast["contributing_models"]
        assert "xgboost" in forecast["contributing_models"]

        # Verify models were called
        mock_transformer_model.predict.assert_called_once()
        mock_xgboost_model.predict.assert_called_once()

    async def test_generate_forecast_insufficient_data(self, service, mock_transformer_model, mock_xgboost_model):
        """Test that generate_forecast handles insufficient data."""
        # Setup
        patient_data = {
            "patient_id": str(uuid4()),
            "symptom_history": []
        }

        # Execute
        forecast = await service.generate_forecast(patient_data)

        # Verify
        assert "error" in forecast
        assert forecast["error"] == "insufficient_data"
        assert forecast["forecast"] is None
        assert forecast["confidence_intervals"] is None
        assert forecast["reliability"] == "none"

        # Verify models were not called
        mock_transformer_model.predict.assert_not_called()
        mock_xgboost_model.predict.assert_not_called()

    async def test_generate_forecast_model_error(self, service, sample_patient_data, mock_transformer_model):
        """Test that generate_forecast handles model errors gracefully."""
        # Setup
        mock_transformer_model.predict.side_effect = Exception("Model error")

        # Execute
        forecast = await service.generate_forecast(sample_patient_data)

        # Verify
        assert "error" in forecast
        assert "Model error" in forecast["error"]
        assert forecast["forecast"] is None
        assert forecast["confidence_intervals"] is None
        assert forecast["reliability"] == "none"

    async def test_model_initialization(self):
        """Test that models are initialized if not already initialized."""
        # Setup
        mock_transformer = AsyncMock(spec=TransformerTimeSeriesModel)
        mock_transformer.is_initialized = False
        mock_transformer.initialize = AsyncMock()

        mock_xgboost = AsyncMock(spec=XGBoostTimeSeriesModel)
        mock_xgboost.is_initialized = False
        mock_xgboost.initialize = AsyncMock()

        # Execute
        service = SymptomForecastingService(
            transformer_model=mock_transformer,
            xgboost_model=mock_xgboost
        )

        # Verify
        mock_transformer.initialize.assert_called_once()
        mock_xgboost.initialize.assert_called_once()