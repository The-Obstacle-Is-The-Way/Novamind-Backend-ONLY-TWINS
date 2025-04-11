# -*- coding: utf-8 -*-
"""
Unit tests for the Pharmacogenomics Model Service.

These tests verify that the Pharmacogenomics Model Service correctly
analyzes genetic data and predicts medication responses.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.pharmacogenomics.model_service import PharmacogenomicsService
from app.infrastructure.ml.pharmacogenomics.gene_medication_model import GeneMedicationModel
from app.infrastructure.ml.pharmacogenomics.treatment_model import PharmacogenomicsModel

class TestPharmacogenomicsService:
    """Tests for the PharmacogenomicsService."""

    @pytest.fixture
    def mock_gene_medication_model(self):
        """Create a mock GeneMedicationModel."""
        model = AsyncMock(spec=GeneMedicationModel)
        model.is_initialized = True
        model.predict_medication_interactions = AsyncMock(return_value={
            "gene_medication_interactions": [
                {
                    "gene": "CYP2D6",
                    "variant": "*1/*1",
                    "medication": "fluoxetine",
                    "interaction_type": "metabolism",
                    "effect": "normal",
                    "evidence_level": "high",
                    "recommendation": "standard_dosing"
                },
                {
                    "gene": "CYP2C19",
                    "variant": "*1/*2",
                    "medication": "escitalopram",
                    "interaction_type": "metabolism",
                    "effect": "reduced",
                    "evidence_level": "high",
                    "recommendation": "dose_reduction"
                }
            ],
            "metabolizer_status": {
                "CYP2D6": "normal",
                "CYP2C19": "intermediate",
                "CYP1A2": "rapid"
            }
        })
        return model

    @pytest.fixture
    def mock_treatment_model(self):
        """Create a mock TreatmentResponseModel."""
        model = AsyncMock(spec=PharmacogenomicsModel)
        model.is_initialized = True
        model.predict_treatment_response = AsyncMock(return_value={
            "medication_predictions": {
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
                }
            },
            "comparative_analysis": {
                "highest_efficacy": {
                    "medication": "fluoxetine",
                    "score": 0.72
                },
                "lowest_side_effects": {
                    "medication": "bupropion",
                    "highest_risk": 0.25
                }
            }
        })
        return model

    @pytest.fixture
    def service(self, mock_gene_medication_model, mock_treatment_model):
        """Create a PharmacogenomicsService with mock dependencies."""
        return PharmacogenomicsService(
            gene_medication_model=mock_gene_medication_model,
            treatment_model=mock_treatment_model
        )

    @pytest.fixture
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
            ]
        }

    @pytest.fixture
    def sample_patient_id(self):
        """Create a sample patient ID."""
        return str(uuid4())

    async def test_predict_medication_response_success(self, service, mock_gene_medication_model, 
                                                      mock_treatment_model, sample_genetic_data, 
                                                      sample_patient_data, sample_patient_id):
        """Test that predict_medication_response correctly processes data and returns predictions."""
        # Setup
        medications = ["fluoxetine", "sertraline", "bupropion"]
        
        # Execute
        result = await service.predict_medication_response(
            patient_id=sample_patient_id,
            genetic_data=sample_genetic_data,
            patient_data=sample_patient_data,
            medications=medications
        )
        
        # Verify
        assert "patient_id" in result
        assert result["patient_id"] == sample_patient_id
        assert "medication_predictions" in result
        assert "gene_medication_interactions" in result
        assert "metabolizer_status" in result
        assert "comparative_analysis" in result
        
        # Verify models were called
        mock_gene_medication_model.predict_medication_interactions.assert_called_once()
        mock_treatment_model.predict_treatment_response.assert_called_once()
        
        # Verify medication predictions structure
        for medication in medications:
            assert medication in result["medication_predictions"]
            med_pred = result["medication_predictions"][medication]
            assert "efficacy" in med_pred
            assert "side_effects" in med_pred
            assert "recommendation" in med_pred
            
        # Verify gene interactions structure
        for interaction in result["gene_medication_interactions"]:
            assert "gene" in interaction
            assert "variant" in interaction
            assert "medication" in interaction
            assert "effect" in interaction
            assert "recommendation" in interaction

    async def test_predict_medication_response_empty_genetic_data(self, service, sample_patient_data, sample_patient_id):
        """Test that predict_medication_response handles empty genetic data gracefully."""
        # Setup
        empty_genetic_data = {"genes": []}
        medications = ["fluoxetine", "sertraline"]
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
            await service.predict_medication_response(
                patient_id=sample_patient_id,
                genetic_data=empty_genetic_data,
                patient_data=sample_patient_data,
                medications=medications
            )
        
        assert "Empty genetic data" in str(excinfo.value)

    async def test_predict_medication_response_empty_medications(self, service, sample_genetic_data, 
                                                                sample_patient_data, sample_patient_id):
        """Test that predict_medication_response handles empty medications list gracefully."""
        # Setup
        empty_medications = []
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError) as excinfo:
            await service.predict_medication_response(
                patient_id=sample_patient_id,
                genetic_data=sample_genetic_data,
                patient_data=sample_patient_data,
                medications=empty_medications
            )
        
        assert "No medications specified" in str(excinfo.value)

    async def test_predict_medication_response_model_error(self, service, mock_gene_medication_model,
                                                          sample_genetic_data, sample_patient_data, 
                                                          sample_patient_id):
        """Test that predict_medication_response handles model errors gracefully."""
        # Setup
        mock_gene_medication_model.predict_medication_interactions.side_effect = Exception("Model error")
        medications = ["fluoxetine", "sertraline"]
        
        # Execute
        result = await service.predict_medication_response(
            patient_id=sample_patient_id,
            genetic_data=sample_genetic_data,
            patient_data=sample_patient_data,
            medications=medications
        )
        
        # Verify
        assert "patient_id" in result
        assert result["patient_id"] == sample_patient_id
        assert "error" in result
        assert "Model error" in result["error"]
        assert "medication_predictions" not in result
        assert "gene_medication_interactions" not in result

    async def test_generate_medication_recommendations(self, service, sample_genetic_data, sample_patient_data):
        """Test that _generate_medication_recommendations creates meaningful recommendations."""
        # Setup
        gene_interactions = [
            {
                "gene": "CYP2D6",
                "variant": "*1/*1",
                "medication": "fluoxetine",
                "interaction_type": "metabolism",
                "effect": "normal",
                "evidence_level": "high",
                "recommendation": "standard_dosing"
            },
            {
                "gene": "CYP2C19",
                "variant": "*1/*2",
                "medication": "escitalopram",
                "interaction_type": "metabolism",
                "effect": "reduced",
                "evidence_level": "high",
                "recommendation": "dose_reduction"
            }
        ]
        
        treatment_predictions = {
            "fluoxetine": {
                "efficacy": {
                    "score": 0.72,
                    "confidence": 0.85
                },
                "side_effects": [
                    {
                        "name": "nausea",
                        "risk": 0.35,
                        "severity": "mild"
                    }
                ]
            },
            "escitalopram": {
                "efficacy": {
                    "score": 0.65,
                    "confidence": 0.80
                },
                "side_effects": [
                    {
                        "name": "nausea",
                        "risk": 0.42,
                        "severity": "moderate"
                    }
                ]
            }
        }
        
        # Execute
        recommendations = service._generate_medication_recommendations(
            gene_interactions, 
            treatment_predictions,
            sample_patient_data
        )
        
        # Verify
        assert isinstance(recommendations, dict)
        assert "fluoxetine" in recommendations
        assert "escitalopram" in recommendations
        
        # Check recommendation structure
        for medication, rec in recommendations.items():
            assert "action" in rec
            assert "rationale" in rec
            assert "caution_level" in rec
            assert "dosing_guidance" in rec
            
        # Verify specific recommendations
        assert recommendations["fluoxetine"]["action"] == "standard_dosing"
        assert recommendations["escitalopram"]["action"] == "dose_reduction"
        assert "reduced metabolism" in recommendations["escitalopram"]["rationale"].lower()

    async def test_combine_predictions(self, service):
        """Test that _combine_predictions correctly combines predictions from different models."""
        # Setup
        gene_predictions = {
            "gene_medication_interactions": [
                {
                    "gene": "CYP2D6",
                    "variant": "*1/*1",
                    "medication": "fluoxetine",
                    "interaction_type": "metabolism",
                    "effect": "normal",
                    "recommendation": "standard_dosing"
                }
            ],
            "metabolizer_status": {
                "CYP2D6": "normal"
            }
        }
        
        treatment_predictions = {
            "medication_predictions": {
                "fluoxetine": {
                    "efficacy": {
                        "score": 0.72
                    },
                    "side_effects": [
                        {
                            "name": "nausea",
                            "risk": 0.35
                        }
                    ]
                }
            },
            "comparative_analysis": {
                "highest_efficacy": {
                    "medication": "fluoxetine",
                    "score": 0.72
                }
            }
        }
        
        patient_data = {
            "conditions": ["major_depressive_disorder"]
        }
        
        # Execute
        combined = service._combine_predictions(
            gene_predictions, 
            treatment_predictions,
            patient_data
        )
        
        # Verify
        assert "medication_predictions" in combined
        assert "gene_medication_interactions" in combined
        assert "metabolizer_status" in combined
        assert "comparative_analysis" in combined
        
        # Check that medication predictions include both efficacy and gene data
        fluoxetine_pred = combined["medication_predictions"]["fluoxetine"]
        assert "efficacy" in fluoxetine_pred
        assert "side_effects" in fluoxetine_pred
        assert "recommendation" in fluoxetine_pred
        assert fluoxetine_pred["recommendation"]["action"] == "standard_dosing"