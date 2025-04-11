# -*- coding: utf-8 -*-
"""
Unit tests for the Treatment Response Model.

These tests verify that the Treatment Response Model correctly
predicts medication efficacy and side effects based on patient data.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.pharmacogenomics.treatment_model import PharmacogenomicsModel # Corrected @pytest.mark.db_required
class name:


class TestTreatmentResponseModel:
    """Tests for the TreatmentResponseModel."""

    @pytest.fixture
    def model(self):
        """Create a TreatmentResponseModel with mocked internals."""
        with patch('app.infrastructure.ml.pharmacogenomics.treatment_model.joblib', autospec=True):
            model = TreatmentResponseModel(
                model_path="test_model_path",
                medication_data_path="test_medication_path"
            )
            # Mock the internal models
            model._efficacy_model = MagicMock()
            model._efficacy_model.predict = MagicMock(return_value=np.array([0.72, 0.65, 0.58]))
            model._efficacy_model.predict_proba = MagicMock(return_value=np.array([[0.28, 0.72], [0.35, 0.65], [0.42, 0.58]]))
            
            model._side_effect_model = MagicMock()
            model._side_effect_model.predict = MagicMock(return_value=np.array([
                [0.35, 0.28, 0.15],  # Medication 1 side effects (nausea, insomnia, headache)
                [0.42, 0.20, 0.18],  # Medication 2 side effects
                [0.25, 0.22, 0.12]   # Medication 3 side effects
            ]))
            
            # Mock the medication data
            model._medication_data = {
                "fluoxetine": {
                    "class": "SSRI",
                    "common_side_effects": ["nausea", "insomnia", "headache"],
                    "typical_onset_days": {"nausea": 7, "insomnia": 14, "headache": 3},
                    "typical_severity": {"nausea": "mild", "insomnia": "mild", "headache": "mild"}
                },
                "sertraline": {
                    "class": "SSRI",
                    "common_side_effects": ["nausea", "insomnia", "headache"],
                    "typical_onset_days": {"nausea": 5, "insomnia": 10, "headache": 2},
                    "typical_severity": {"nausea": "moderate", "insomnia": "mild", "headache": "mild"}
                },
                "bupropion": {
                    "class": "NDRI",
                    "common_side_effects": ["nausea", "insomnia", "headache"],
                    "typical_onset_days": {"nausea": 3, "insomnia": 7, "headache": 1},
                    "typical_severity": {"nausea": "mild", "insomnia": "moderate", "headache": "mild"}
                }
            }
            
            model.is_initialized = True
            return model

    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data for testing."""
        return {
            "id": str(uuid4()),
            "demographics": {
                "age": 42,
                "gender": "female",
                "ethnicity": "caucasian"
            },
            "conditions": ["major_depressive_disorder", "generalized_anxiety_disorder"],
            "medication_history": [
                {
                    "name": "citalopram",
                    "dosage": "20mg",
                    "start_date": "2024-01-15",
                    "end_date": "2024-03-01",
                    "efficacy": "moderate",
                    "side_effects": ["nausea", "insomnia"],
                    "reason_for_discontinuation": "insufficient_efficacy"
                }
            ],
            "genetic_data": {
                "metabolizer_status": {
                    "CYP2D6": "normal",
                    "CYP2C19": "intermediate"
                }
            }
        }

    async def test_initialize_loads_model_and_medication_data(self):
        """Test that initialize loads the model and medication data correctly."""
        # Setup
        with patch('app.infrastructure.ml.pharmacogenomics.treatment_model.joblib', autospec=True) as mock_joblib, \
             patch('app.infrastructure.ml.pharmacogenomics.treatment_model.json', autospec=True) as mock_json, \
             patch('app.infrastructure.ml.pharmacogenomics.treatment_model.open', autospec=True) as mock_open, \
             patch('app.infrastructure.ml.pharmacogenomics.treatment_model.os.path.exists', return_value=True):
            
            # Create model instance
            model = TreatmentResponseModel(
                model_path="test_model_path",
                medication_data_path="test_medication_path"
            )
            
            # Mock joblib.load to return mock models
            mock_efficacy_model = MagicMock()
            mock_side_effect_model = MagicMock()
            mock_joblib.load.side_effect = [
                {"efficacy_model": mock_efficacy_model, "side_effect_model": mock_side_effect_model}
            ]
            
            # Mock json.load to return mock medication data
            mock_medication_data = {
                "fluoxetine": {},
                "sertraline": {}
            }
            mock_json.load.return_value = mock_medication_data
            
            # Execute
            await model.initialize()
            
            # Verify
            mock_joblib.load.assert_called_once_with("test_model_path")
            mock_json.load.assert_called_once()
            assert model.is_initialized
            assert model._efficacy_model is not None
            assert model._side_effect_model is not None
            assert model._medication_data is not None

    async def test_initialize_handles_missing_files(self):
        """Test that initialize handles missing model and medication data files gracefully."""
        # Setup
        with patch('app.infrastructure.ml.pharmacogenomics.treatment_model.joblib', autospec=True), \
             patch('app.infrastructure.ml.pharmacogenomics.treatment_model.json', autospec=True), \
             patch('app.infrastructure.ml.pharmacogenomics.treatment_model.open', autospec=True), \
             patch('app.infrastructure.ml.pharmacogenomics.treatment_model.os.path.exists', return_value=False), \
             patch('app.infrastructure.ml.pharmacogenomics.treatment_model.logging', autospec=True) as mock_logging:
            
            # Create model instance
            model = TreatmentResponseModel(
                model_path="nonexistent_path",
                medication_data_path="nonexistent_medication_path"
            )
            
            # Execute
            await model.initialize()
            
            # Verify
            mock_logging.warning.assert_called()
            assert model.is_initialized
            assert model._efficacy_model is not None
            assert model._side_effect_model is not None
            assert model._medication_data is not None

    async def test_predict_treatment_response_success(self, model, sample_patient_data):
        """Test that predict_treatment_response correctly processes patient data and returns predictions."""
        # Setup
        medications = ["fluoxetine", "sertraline", "bupropion"]
        
        # Execute
        result = await model.predict_treatment_response(sample_patient_data, medications)
        
        # Verify
        assert "medication_predictions" in result
        assert "comparative_analysis" in result
        
        # Verify medication predictions structure
        for medication in medications:
            assert medication in result["medication_predictions"]
            med_pred = result["medication_predictions"][medication]
            assert "efficacy" in med_pred
            assert "side_effects" in med_pred
            
            # Check efficacy structure
            efficacy = med_pred["efficacy"]
            assert "score" in efficacy
            assert "confidence" in efficacy
            assert "percentile" in efficacy
            
            # Check side effects structure
            side_effects = med_pred["side_effects"]
            assert len(side_effects) > 0
            for side_effect in side_effects:
                assert "name" in side_effect
                assert "risk" in side_effect
                assert "severity" in side_effect
                assert "onset_days" in side_effect
        
        # Verify comparative analysis
        comparative = result["comparative_analysis"]
        assert "highest_efficacy" in comparative
        assert "lowest_side_effects" in comparative
        assert "optimal_balance" in comparative

    async def test_predict_treatment_response_empty_medications(self, model, sample_patient_data):
        """Test that predict_treatment_response handles empty medications list gracefully."""
        # Setup
        empty_medications = []
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
            await model.predict_treatment_response(sample_patient_data, empty_medications)
        
        assert "No medications specified" in str(excinfo.value)

    async def test_extract_patient_features(self, model, sample_patient_data):
        """Test that _extract_patient_features correctly transforms patient data into features."""
        # Setup
        with patch.object(model, '_extract_patient_features', wraps=model._extract_patient_features) as mock_extract:
            
            # Execute
            await model.predict_treatment_response(sample_patient_data, ["fluoxetine"])
            
            # Verify
            mock_extract.assert_called_once_with(sample_patient_data)
            
            # Call directly to test
            features = model._extract_patient_features(sample_patient_data)
            
            # Verify the features have the expected structure
            assert isinstance(features, dict)
            assert "age" in features
            assert "gender" in features
            assert "conditions" in features
            assert "medication_history" in features
            assert "genetic_data" in features
            
            # Check specific values
            assert features["age"] == 42
            assert features["gender"] == "female"
            assert "major_depressive_disorder" in features["conditions"]
            assert "generalized_anxiety_disorder" in features["conditions"]
            assert len(features["medication_history"]) == 1
            assert features["medication_history"][0]["name"] == "citalopram"

    async def test_predict_efficacy(self, model, sample_patient_data):
        """Test that _predict_efficacy correctly predicts medication efficacy."""
        # Setup
        medications = ["fluoxetine", "sertraline", "bupropion"]
        patient_features = model._extract_patient_features(sample_patient_data)
        
        # Execute
        efficacy_predictions = model._predict_efficacy(patient_features, medications)
        
        # Verify
        assert isinstance(efficacy_predictions, dict)
        for medication in medications:
            assert medication in efficacy_predictions
            med_efficacy = efficacy_predictions[medication]
            assert "score" in med_efficacy
            assert "confidence" in med_efficacy
            assert "percentile" in med_efficacy
            assert 0 <= med_efficacy["score"] <= 1
            assert 0 <= med_efficacy["confidence"] <= 1
            assert 0 <= med_efficacy["percentile"] <= 100

    async def test_predict_side_effects(self, model, sample_patient_data):
        """Test that _predict_side_effects correctly predicts medication side effects."""
        # Setup
        medications = ["fluoxetine", "sertraline", "bupropion"]
        patient_features = model._extract_patient_features(sample_patient_data)
        
        # Execute
        side_effect_predictions = model._predict_side_effects(patient_features, medications)
        
        # Verify
        assert isinstance(side_effect_predictions, dict)
        for medication in medications:
            assert medication in side_effect_predictions
            med_side_effects = side_effect_predictions[medication]
            assert isinstance(med_side_effects, list)
            assert len(med_side_effects) > 0
            
            # Check side effect structure
            for side_effect in med_side_effects:
                assert "name" in side_effect
                assert "risk" in side_effect
                assert "severity" in side_effect
                assert "onset_days" in side_effect
                assert 0 <= side_effect["risk"] <= 1

    async def test_generate_comparative_analysis(self, model):
        """Test that _generate_comparative_analysis correctly compares medication predictions."""
        # Setup
        medication_predictions = {
            "fluoxetine": {
                "efficacy": {
                    "score": 0.72,
                    "confidence": 0.85,
                    "percentile": 75
                },
                "side_effects": [
                    {
                        "name": "nausea",
                        "risk": 0.35,
                        "severity": "mild",
                        "onset_days": 7
                    },
                    {
                        "name": "insomnia",
                        "risk": 0.28,
                        "severity": "mild",
                        "onset_days": 14
                    }
                ]
            },
            "sertraline": {
                "efficacy": {
                    "score": 0.65,
                    "confidence": 0.80,
                    "percentile": 65
                },
                "side_effects": [
                    {
                        "name": "nausea",
                        "risk": 0.42,
                        "severity": "moderate",
                        "onset_days": 5
                    }
                ]
            },
            "bupropion": {
                "efficacy": {
                    "score": 0.58,
                    "confidence": 0.75,
                    "percentile": 55
                },
                "side_effects": [
                    {
                        "name": "nausea",
                        "risk": 0.25,
                        "severity": "mild",
                        "onset_days": 3
                    }
                ]
            }
        }
        
        # Execute
        comparative = model._generate_comparative_analysis(medication_predictions)
        
        # Verify
        assert isinstance(comparative, dict)
        assert "highest_efficacy" in comparative
        assert "lowest_side_effects" in comparative
        assert "optimal_balance" in comparative
        
        # Check highest efficacy
        assert comparative["highest_efficacy"]["medication"] == "fluoxetine"
        assert comparative["highest_efficacy"]["score"] == 0.72
        
        # Check lowest side effects
        assert comparative["lowest_side_effects"]["medication"] == "bupropion"
        assert comparative["lowest_side_effects"]["highest_risk"] == 0.25
        
        # Check optimal balance (should be fluoxetine in this case)
        assert "medication" in comparative["optimal_balance"]
        assert "efficacy" in comparative["optimal_balance"]
        assert "side_effect_risk" in comparative["optimal_balance"]