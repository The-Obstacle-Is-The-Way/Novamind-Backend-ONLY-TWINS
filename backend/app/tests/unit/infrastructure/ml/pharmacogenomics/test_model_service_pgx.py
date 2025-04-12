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

    async def test_predict_medication_response_success(
        self, service, mock_gene_medication_model, 
        mock_treatment_model, sample_genetic_data,
        sample_patient_data, sample_patient_id
    ):
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
        
        # Verify model arguments
        gene_model_args = mock_gene_medication_model.predict_medication_interactions.call_args[1]
        assert gene_model_args["genetic_data"] == sample_genetic_data
        assert gene_model_args["medications"] == medications
        
        treatment_model_args = mock_treatment_model.predict_treatment_response.call_args[1]
        assert treatment_model_args["patient_data"] == sample_patient_data
        assert treatment_model_args["medications"] == medications
        assert "metabolizer_status" in treatment_model_args

    async def test_predict_medication_response_no_genetic_data(self, service, sample_patient_data, sample_patient_id):
        """Test that predict_medication_response handles missing genetic data."""
        # Setup
        medications = ["fluoxetine", "sertraline"]
        
        # Execute/Assert
        with pytest.raises(ValueError) as excinfo:
            await service.predict_medication_response(
                patient_id=sample_patient_id,
                genetic_data=None,
                patient_data=sample_patient_data,
                medications=medications
            )
        
        assert "genetic data is required" in str(excinfo.value).lower()

    async def test_predict_medication_response_no_patient_data(self, service, sample_genetic_data, sample_patient_id):
        """Test that predict_medication_response handles missing patient data."""
        # Setup
        medications = ["fluoxetine", "sertraline"]
        
        # Execute/Assert
        with pytest.raises(ValueError) as excinfo:
            await service.predict_medication_response(
                patient_id=sample_patient_id,
                genetic_data=sample_genetic_data,
                patient_data=None,
                medications=medications
            )
        
        assert "patient data is required" in str(excinfo.value).lower()

    async def test_predict_medication_response_no_medications(
        self, service, sample_genetic_data, 
        sample_patient_data, sample_patient_id
    ):
        """Test that predict_medication_response handles empty medications list."""
        # Execute/Assert
        with pytest.raises(ValueError) as excinfo:
            await service.predict_medication_response(
                patient_id=sample_patient_id,
                genetic_data=sample_genetic_data,
                patient_data=sample_patient_data,
                medications=[]
            )
        
        assert "medications list cannot be empty" in str(excinfo.value).lower()

    async def test_predict_medication_response_model_error(
        self, service, mock_gene_medication_model,
        sample_genetic_data, sample_patient_data,
        sample_patient_id
    ):
        """Test that predict_medication_response handles model errors correctly."""
        # Setup
        medications = ["fluoxetine", "sertraline"]
        mock_gene_medication_model.predict_medication_interactions.side_effect = Exception("Model error")
        
        # Execute/Assert
        with pytest.raises(RuntimeError) as excinfo:
            await service.predict_medication_response(
                patient_id=sample_patient_id,
                genetic_data=sample_genetic_data,
                patient_data=sample_patient_data,
                medications=medications
            )
        
        assert "prediction failed" in str(excinfo.value).lower()

    @patch('app.infrastructure.ml.pharmacogenomics.model_service.log_phi_access')
    async def test_phi_access_logging(
        self, mock_log_phi_access, service, sample_genetic_data,
        sample_patient_data, sample_patient_id
    ):
        """Test that PHI access is properly logged."""
        # Setup
        medications = ["fluoxetine", "sertraline"]
        
        # Execute
        await service.predict_medication_response(
            patient_id=sample_patient_id,
            genetic_data=sample_genetic_data,
            patient_data=sample_patient_data,
            medications=medications
        )
        
        # Verify PHI access logging
        mock_log_phi_access.assert_called_once()
        log_args = mock_log_phi_access.call_args[0]
        assert log_args[0] == "PharmacogenomicsService.predict_medication_response"
        assert log_args[1] == sample_patient_id

    async def test_analyze_medication_interactions(
        self, service, mock_gene_medication_model,
        sample_genetic_data
    ):
        """Test the analyze_medication_interactions method."""
        # Setup
        medications = ["fluoxetine", "sertraline"]
        
        # Execute
        result = await service.analyze_medication_interactions(
            genetic_data=sample_genetic_data,
            medications=medications
        )
        
        # Verify
        assert "gene_medication_interactions" in result
        assert "metabolizer_status" in result
        mock_gene_medication_model.predict_medication_interactions.assert_called_once()

    async def test_analyze_medication_interactions_no_genetic_data(self, service):
        """Test analyze_medication_interactions with no genetic data."""
        # Setup
        medications = ["fluoxetine", "sertraline"]
        
        # Execute/Assert
        with pytest.raises(ValueError) as excinfo:
            await service.analyze_medication_interactions(
                genetic_data=None,
                medications=medications
            )
        
        assert "genetic data is required" in str(excinfo.value).lower()

    async def test_is_model_healthy(self, service, mock_gene_medication_model, mock_treatment_model):
        """Test the is_model_healthy method."""
        # Both models are healthy
        assert await service.is_model_healthy() is True
        
        # Gene medication model is not initialized
        mock_gene_medication_model.is_initialized = False
        assert await service.is_model_healthy() is False
        
        # Gene medication model is initialized, but treatment model is not
        mock_gene_medication_model.is_initialized = True
        mock_treatment_model.is_initialized = False
        assert await service.is_model_healthy() is False
        
        # Both models are initialized again
        mock_treatment_model.is_initialized = True
        assert await service.is_model_healthy() is True

    async def test_get_model_info(self, service, mock_gene_medication_model, mock_treatment_model):
        """Test the get_model_info method."""
        # Setup mock responses
        mock_gene_medication_model.get_model_info = AsyncMock(return_value={
            "name": "GeneMedicationModel",
            "version": "1.0.0",
            "description": "Predicts medication interactions based on genetic variants"
        })
        
        mock_treatment_model.get_model_info = AsyncMock(return_value={
            "name": "PharmacogenomicsModel",
            "version": "1.0.0",
            "description": "Predicts treatment response based on genetic and patient data"
        })
        
        # Execute
        result = await service.get_model_info()
        
        # Verify
        assert "service_info" in result
        assert result["service_info"]["name"] == "PharmacogenomicsService"
        assert "gene_medication_model" in result
        assert "treatment_model" in result
        assert result["gene_medication_model"]["name"] == "GeneMedicationModel"
        assert result["treatment_model"]["name"] == "PharmacogenomicsModel"