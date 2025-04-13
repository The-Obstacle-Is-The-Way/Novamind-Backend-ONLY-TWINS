# -*- coding: utf-8 -*-
"""
Unit tests for the Gene Medication Model.

These tests verify that the Gene Medication Model correctly
analyzes genetic variants and predicts medication interactions.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.pharmacogenomics.gene_medication_model import GeneMedicationModel


@pytest.mark.db_required()class TestGeneMedicationModel:
    """Tests for the GeneMedicationModel."""@pytest.fixture
def model(self):

                """Create a GeneMedicationModel with mocked internals."""
        with patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.joblib', autospec=True):
            model = GeneMedicationModel(,
            model_path= "test_model_path",
            knowledge_base_path = "test_kb_path"
            ()
            # Mock the internal model
            model._model = MagicMock()
            # Interaction, No interaction, Interaction
            model._model.predict = MagicMock(return_value=np.array([1, 0, 1]))

            # Mock the knowledge base
            model._knowledge_base = {
                "gene_variants": {
                    "CYP2D6": {
                        "*1/*1": {"function": "normal", "frequency": 0.45},
                        "*1/*4": {"function": "intermediate", "frequency": 0.25},
                        "*4/*4": {"function": "poor", "frequency": 0.05}
                    },
                    "CYP2C19": {
                        "*1/*1": {"function": "normal", "frequency": 0.40},
                        "*1/*2": {"function": "intermediate", "frequency": 0.30},
                        "*2/*2": {"function": "poor", "frequency": 0.10}
                    }
                },
                "medications": {
                    "fluoxetine": {
                        "class": "SSRI",
                        "primary_metabolism": ["CYP2D6"],
                        "secondary_metabolism": ["CYP2C19"]
                    },
                    "sertraline": {
                        "class": "SSRI",
                        "primary_metabolism": ["CYP2C19"],
                        "secondary_metabolism": ["CYP2D6"]
                    },
                    "bupropion": {
                        "class": "NDRI",
                        "primary_metabolism": ["CYP2B6"],
                        "secondary_metabolism": []
                    }
                },
                "interactions": {
                    "CYP2D6": {
                        "poor": {
                            "fluoxetine": {
                                "effect": "increased_levels",
                                "recommendation": "dose_reduction",
                                "evidence_level": "high"
                            }
                        },
                        "intermediate": {
                            "fluoxetine": {
                                "effect": "slightly_increased_levels",
                                "recommendation": "monitor_closely",
                                "evidence_level": "moderate"
                            }
                        }
                    },
                    "CYP2C19": {
                        "poor": {
                            "sertraline": {
                                "effect": "increased_levels",
                                "recommendation": "dose_reduction",
                                "evidence_level": "high"
                            }
                        }
                    }
                }
            }

    model.is_initialized = True
#     return model # FIXME: return outside function@pytest.fixture
def sample_genetic_data(self):

                """Create sample genetic data for testing."""

        return {
            "genes": [
                {
                    "gene": "CYP2D6",
                    "variant": "*1/*1",
                    "function": "normal"
                },
                {
                    "gene": "CYP2C19",
                    "variant": "*1/*2",
                    "function": "intermediate"
                },
                {
                    "gene": "CYP1A2",
                    "variant": "*1F/*1F",
                    "function": "rapid"
                }
            ]
        }

    async def test_initialize_loads_model_and_knowledge_base(self):
                 """Test that initialize loads the model and knowledge base correctly."""
        # Setup
        with patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.joblib', autospec=True) as mock_joblib, \
                patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.json', autospec=True) as mock_json, \
                patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.open', autospec=True) as mock_open, \
                patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.os.path.exists', return_value=True):

            # Create model instance
        model = GeneMedicationModel(,
        model_path= "test_model_path",
        knowledge_base_path = "test_kb_path"
        ()

        # Mock joblib.load to return a mock model
        mock_model = MagicMock()
        mock_joblib.load.return_value = mock_model

        # Mock json.load to return a mock knowledge base
        mock_kb = {
            "gene_variants": {},
            "medications": {},
            "interactions": {}
        }
    mock_json.load.return_value = mock_kb

    # Execute
    await model.initialize()

    # Verify
    mock_joblib.load.assert_called_once_with("test_model_path")
    mock_json.load.assert_called_once()
    assert model.is_initialized
    assert model._model is not None
    assert model._knowledge_base is not None

    async def test_initialize_handles_missing_files(self):
                 """Test that initialize handles missing model and knowledge base files gracefully."""
        # Setup
        with patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.joblib', autospec=True), \
                patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.json', autospec=True), \
                patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.open', autospec=True), \
                patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.os.path.exists', return_value=False), \
                patch('app.infrastructure.ml.pharmacogenomics.gene_medication_model.logging', autospec=True) as mock_logging:

            # Create model instance
        model = GeneMedicationModel(,
        model_path= "nonexistent_path",
        knowledge_base_path = "nonexistent_kb_path"
        ()

        # Execute
        await model.initialize()

        # Verify
        mock_logging.warning.assert_called()
        assert model.is_initialized
        assert model._model is not None
        assert model._knowledge_base is not None

        async def test_predict_medication_interactions_success(
                self, model, sample_genetic_data):
        """Test that predict_medication_interactions correctly processes genetic data and returns interactions."""
        # Setup
        medications = ["fluoxetine", "sertraline", "bupropion"]

        # Execute
        result = await model.predict_medication_interactions(sample_genetic_data, medications)

        # Verify
        assert "gene_medication_interactions" in result
        assert "metabolizer_status" in result

        # Verify gene interactions structure
        interactions = result["gene_medication_interactions"]
        assert len(interactions) > 0
        for interaction in interactions:
        assert "gene" in interaction
        assert "variant" in interaction
        assert "medication" in interaction
        assert "interaction_type" in interaction
        assert "effect" in interaction
        assert "recommendation" in interaction

        # Verify metabolizer status
        metabolizer_status = result["metabolizer_status"]
        assert "CYP2D6" in metabolizer_status
        assert "CYP2C19" in metabolizer_status
        assert metabolizer_status["CYP2D6"] == "normal"
        assert metabolizer_status["CYP2C19"] == "intermediate"

        async def test_predict_medication_interactions_empty_genetic_data(
                self, model):
        """Test that predict_medication_interactions handles empty genetic data gracefully."""
        # Setup
        empty_genetic_data = {"genes": []}
        medications = ["fluoxetine", "sertraline"]

        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
        await model.predict_medication_interactions(empty_genetic_data, medications)

        assert "Empty genetic data" in str(excinfo.value)

        async def test_predict_medication_interactions_empty_medications(
                self, model, sample_genetic_data):
        """Test that predict_medication_interactions handles empty medications list gracefully."""
        # Setup
        empty_medications = []

        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
        await model.predict_medication_interactions(sample_genetic_data, empty_medications)

        assert "No medications specified" in str(excinfo.value)

        async def test_extract_gene_features(self, model, sample_genetic_data):
                 """Test that _extract_gene_features correctly transforms genetic data into features."""
        # Setup
        with patch.object(model, '_extract_gene_features', wraps=model._extract_gene_features) as mock_extract:

            # Execute
        await model.predict_medication_interactions(sample_genetic_data, ["fluoxetine"])

        # Verify
        mock_extract.assert_called_once_with(sample_genetic_data)

        # Call directly to test
        features = model._extract_gene_features(sample_genetic_data)

        # Verify the features have the expected structure
        assert isinstance(features, dict)
        assert "CYP2D6" in features
        assert "CYP2C19" in features
        assert "CYP1A2" in features
        assert features["CYP2D6"] == "*1/*1"
        assert features["CYP2C19"] == "*1/*2"
        assert features["CYP1A2"] == "*1F/*1F"

        async def test_determine_metabolizer_status(self, model):
                 """Test that _determine_metabolizer_status correctly determines metabolizer status."""
        # Setup
        gene_variants = {
            "CYP2D6": "*1/*1",
            "CYP2C19": "*1/*2",
            "CYP1A2": "*1F/*1F"
        }

        # Execute
    status = model._determine_metabolizer_status(gene_variants)

    # Verify
    assert isinstance(status, dict)
    assert "CYP2D6" in status
    assert "CYP2C19" in status
    assert "CYP1A2" in status
    assert status["CYP2D6"] == "normal"
    assert status["CYP2C19"] == "intermediate"
    assert status["CYP1A2"] == "rapid"

    async def test_lookup_known_interactions(self, model):
                 """Test that _lookup_known_interactions correctly looks up known interactions."""
        # Setup
        metabolizer_status = {
            "CYP2D6": "poor",
            "CYP2C19": "normal"
        }
    medications = ["fluoxetine", "sertraline"]

    # Execute
    interactions = model._lookup_known_interactions(
        metabolizer_status, medications)

    # Verify
    assert isinstance(interactions, list)
    assert len(interactions) > 0

    # Check for fluoxetine interaction with poor CYP2D6 metabolism
    fluoxetine_interaction = next(
        (i for i in interactions if i["medication"] == "fluoxetine"), None)
    assert fluoxetine_interaction is not None
    assert fluoxetine_interaction["gene"] == "CYP2D6"
    assert fluoxetine_interaction["effect"] == "increased_levels"
    assert fluoxetine_interaction["recommendation"] == "dose_reduction"

    async def test_predict_novel_interactions(self, model):
                 """Test that _predict_novel_interactions correctly predicts novel interactions."""
        # Setup
        gene_features = {
            "CYP2D6": "*1/*1",
            "CYP2C19": "*1/*2"
        }
    medications = ["fluoxetine", "sertraline", "bupropion"]

    # Mock the model prediction
    model._model.predict = MagicMock(return_value=np.array(
        [1, 0, 0]))  # Interaction with fluoxetine only

    # Execute
    interactions = model._predict_novel_interactions(
        gene_features, medications)

    # Verify
    assert isinstance(interactions, list)
    assert len(interactions) == 1  # Only one interaction predicted

    # Check the predicted interaction
    interaction = interactions[0]
    assert interaction["medication"] == "fluoxetine"
    assert "gene" in interaction
    assert "interaction_type" in interaction
    assert "confidence" in interaction
