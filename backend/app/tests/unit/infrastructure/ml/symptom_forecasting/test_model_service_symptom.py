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
from app.infrastructure.ml.symptom_forecasting.transformer_model import SymptomTransformerModel
from app.infrastructure.ml.symptom_forecasting.xgboost_model import XGBoostSymptomModel


class TestSymptomForecastingService:
    """Tests for the SymptomForecastingService."""

    @pytest.fixture
    def mock_transformer_model(self):
        """Create a mock TransformerTimeSeriesModel."""
        model = AsyncMock(spec=SymptomTransformerModel)
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
        model = AsyncMock(spec=XGBoostSymptomModel)
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
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    # Missing symptom_type
                    "severity": 5
                }
            ]
        }

        # Execute/Verify
        with pytest.raises(ValueError) as excinfo:
            await service.preprocess_patient_data(patient_data)
        
        assert "required fields" in str(excinfo.value).lower()

    async def test_forecast_symptom_severity_success(self, service, sample_patient_data, 
                                                   mock_transformer_model, mock_xgboost_model):
        """Test successful symptom severity forecasting."""
        # Execute
        result = await service.forecast_symptom_severity(
            patient_data=sample_patient_data,
            symptom_type="anxiety",
            models=["transformer", "xgboost", "ensemble"]
        )
        
        # Verify
        assert "patient_id" in result
        assert result["patient_id"] == sample_patient_data["patient_id"]
        assert "forecast_days" in result
        assert result["forecast_days"] == 4
        assert "symptom_type" in result
        assert result["symptom_type"] == "anxiety"
        
        # Check forecasts
        assert "transformer_forecast" in result
        assert "xgboost_forecast" in result
        assert "ensemble_forecast" in result
        
        # Check confidence intervals
        assert "confidence_intervals" in result
        assert "80%" in result["confidence_intervals"]
        assert "95%" in result["confidence_intervals"]
        
        # Verify model calls
        mock_transformer_model.predict.assert_called_once()
        mock_xgboost_model.predict.assert_called_once()

    async def test_forecast_symptom_severity_single_model(self, service, sample_patient_data, 
                                                        mock_transformer_model, mock_xgboost_model):
        """Test forecasting using only a single model."""
        # Execute with only transformer model
        result = await service.forecast_symptom_severity(
            patient_data=sample_patient_data,
            symptom_type="anxiety",
            models=["transformer"]
        )
        
        # Verify
        assert "transformer_forecast" in result
        assert "xgboost_forecast" not in result
        assert "ensemble_forecast" not in result
        
        mock_transformer_model.predict.assert_called_once()
        mock_xgboost_model.predict.assert_not_called()
        
        # Reset mocks
        mock_transformer_model.reset_mock()
        mock_xgboost_model.reset_mock()
        
        # Execute with only xgboost model
        result = await service.forecast_symptom_severity(
            patient_data=sample_patient_data,
            symptom_type="anxiety",
            models=["xgboost"]
        )
        
        # Verify
        assert "transformer_forecast" not in result
        assert "xgboost_forecast" in result
        assert "ensemble_forecast" not in result
        
        mock_transformer_model.predict.assert_not_called()
        mock_xgboost_model.predict.assert_called_once()

    async def test_forecast_symptom_severity_invalid_model(self, service, sample_patient_data):
        """Test forecasting with an invalid model name."""
        # Execute and verify
        with pytest.raises(ValueError) as excinfo:
            await service.forecast_symptom_severity(
                patient_data=sample_patient_data,
                symptom_type="anxiety",
                models=["invalid_model_name"]
            )
        
        assert "unknown model" in str(excinfo.value).lower()

    async def test_forecast_symptom_severity_insufficient_data(self, service):
        """Test forecasting with insufficient data."""
        # Setup patient with very little history
        patient_data = {
            "patient_id": str(uuid4()),
            "symptom_history": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 5
                }
            ]
        }
        
        # Execute
        result = await service.forecast_symptom_severity(
            patient_data=patient_data,
            symptom_type="anxiety",
            models=["ensemble"]
        )
        
        # Verify
        assert "error" in result
        assert result["error"] == "insufficient_data"

    async def test_model_initialization(self, mock_transformer_model, mock_xgboost_model):
        """Test that the service initializes models correctly."""
        # Setup
        service = SymptomForecastingService(
            transformer_model=mock_transformer_model,
            xgboost_model=mock_xgboost_model,
            forecast_days=4
        )
        
        # Execute
        await service.initialize()
        
        # Verify
        mock_transformer_model.initialize.assert_called_once()
        mock_xgboost_model.initialize.assert_called_once()
        
    async def test_handle_model_failure(self, service, sample_patient_data, mock_transformer_model):
        """Test service handles model failures gracefully."""
        # Setup - make transformer model fail
        mock_transformer_model.predict.side_effect = Exception("Model inference failed")
        
        # Execute
        result = await service.forecast_symptom_severity(
            patient_data=sample_patient_data,
            symptom_type="anxiety",
            models=["transformer"]
        )
        
        # Verify error handling
        assert "error" in result
        assert "model_failure" in result["error"]
        assert "transformer" in result["error"]