# -*- coding: utf-8 -*-
"""
Unit tests for the Symptom Forecasting XGBoost Model.

These tests verify that the XGBoost Model correctly processes
time series data and generates accurate forecasts with feature importance.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.symptom_forecasting.xgboost_model import XGBoostSymptomModel


@pytest.mark.db_required()
class TestXGBoostSymptomModel:
    """Tests for the XGBoostSymptomModel."""

    @pytest.fixture
    def model(self):
        """Create an XGBoostSymptomModel with mocked internals."""
        with patch('app.infrastructure.ml.symptom_forecasting.xgboost_model.xgb', autospec=True):
            model = XGBoostSymptomModel()
            model_path = "test_model_path",
            feature_names = [
                "symptom_history_1",
                "symptom_history_2",
                "medication_adherence",
                "sleep_quality"],
            target_names = ["depression_score"]
            ()
            # Mock the internal models
            model.models = {"depression_score": MagicMock()}
            return model

            def test_load_model(self, tmp_path):
        """Test that the model loads correctly from a file."""
        with patch('app.infrastructure.ml.symptom_forecasting.xgboost_model.joblib', autospec=True) as mock_joblib, \
                patch('app.infrastructure.ml.symptom_forecasting.xgboost_model.os.path.exists', return_value=True):
            # Setup
            mock_joblib.load.return_value = {
                "models": {"depression_score": MagicMock()},
                "feature_names": ["f1", "f2", "f3"],
                "target_names": ["t1"],
                "params": {"n_estimators": 100}
            }

            # Execute
    model = XGBoostSymptomModel(model_path="test/model/path.json")

    # Verify
    mock_joblib.load.assert_called_once_with("test/model/path.json")
    assert "depression_score" in model.models
    assert model.feature_names == ["f1", "f2", "f3"]
    assert model.target_names == ["t1"]
    assert model.params["n_estimators"] == 100

    def test_save_model(self, model, tmp_path):
        """Test that the model is saved correctly."""
        with patch('app.infrastructure.ml.symptom_forecasting.xgboost_model.joblib', autospec=True) as mock_joblib:
            # Execute
            model.save_model(f"{tmp_path}/model.json")

            # Verify
            mock_joblib.dump.assert_called_once()
            # Check that the model data was passed to dump
            args, _ = mock_joblib.dump.call_args
            assert "models" in args[0]
            assert "feature_names" in args[0]
            assert "target_names" in args[0]
            assert "params" in args[0]
            assert "timestamp" in args[0]

            @pytest.mark.asyncio()
            async def test_predict(self, model):
        """Test that the model predicts correctly."""
        # Setup
        X = np.array([)
                     [3.0, 4.0, 0.8, 0.6],
                     [2.0, 3.0, 0.9, 0.5],
                     [4.0, 5.0, 0.7, 0.8]
                     (])
        horizon = 3

        # Mock the internal dmatrix and predict function
        with patch('app.infrastructure.ml.symptom_forecasting.xgboost_model.xgb.DMatrix', autospec=True) as mock_dmatrix:
            # Setup the mock prediction
        model.models["depression_score"].predict.return_value = np.array([
                                                                         4.2, 3.8, 4.5])

        # Execute
        result = await model.predict(X, horizon)

        # Verify
        assert "values" in result
        assert "feature_importance" in result
        assert "model_type" in result
        assert result["model_type"] == "xgboost"
        # The result shape should be (n_samples, horizon, n_targets)
        assert result["values"].shape == (3, 3, 1)

        def test_get_feature_importance(self, model):
        """Test that feature importance is correctly calculated."""
        # Setup
        mock_model = model.models["depression_score"]
        mock_model.get_score.return_value = {
            "symptom_history_1": 15.5,
            "symptom_history_2": 12.3,
            "medication_adherence": 25.7,
            "sleep_quality": 18.2
        }

        # Execute
    result = model.get_feature_importance()

    # Verify
    assert "depression_score" in result
    assert result["depression_score"]["medication_adherence"] == 25.7
    mock_model.get_score.assert_called_once_with(importance_type="gain")

    def test_get_model_info(self, model):
        """Test that model info is correctly reported."""
        # Execute
        info = model.get_model_info()

        # Verify
        assert "model_type" in info
        assert "feature_names" in info
        assert "target_names" in info
        assert "params" in info
        assert "num_models" in info
        assert "timestamp" in info
        assert info["feature_names"] == [
            "symptom_history_1",
            "symptom_history_2",
            "medication_adherence",
            "sleep_quality"]
        assert info["target_names"] == ["depression_score"]

        def test_train(self, model):
        """Test that the model trains correctly."""
        # Setup
        X_train = np.array([)
                           [3.0, 4.0, 0.8, 0.6],
                           [2.0, 3.0, 0.9, 0.5],
                           [4.0, 5.0, 0.7, 0.8]
                           (])
        y_train = np.array([4.2, 3.8, 4.5])

        # Mock the internal training
        with patch('app.infrastructure.ml.symptom_forecasting.xgboost_model.xgb', autospec=True) as mock_xgb:
        mock_xgb.DMatrix.return_value = MagicMock()
        mock_xgb.train.return_value = MagicMock()

        # Set up the model to return feature importance
        mock_model = mock_xgb.train.return_value = mock_model.get_score.return_value = {
            "symptom_history_1": 15.5,
            "symptom_history_2": 12.3,
            "medication_adherence": 25.7,
            "sleep_quality": 18.2}

        # Execute
    result = model.train(X_train, y_train, optimize=False)

    # Verify
    assert "training_results" in result
    assert "feature_names" in result
    assert "target_names" in result
    assert "params" in result
    assert "depression_score" in result["training_results"]
    assert "feature_importance" in result["training_results"]["depression_score"]
    assert "params" in result["training_results"]["depression_score"]
