"""Unit tests for Symptom Forecasting Model Service."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import pandas as pd
import numpy as np
from uuid import UUID
from datetime import datetime, timedelta

from app.infrastructure.ml.symptom_forecasting.model_service import (
    SymptomForecastingModelService,
)
from app.domain.entities.patient import Patient
from app.infrastructure.ml.symptom_forecasting.ensemble_model import EnsembleModel
from app.infrastructure.ml.interfaces.model_registry import ModelRegistry
from app.core.config.ml_settings import MLSettingsclass TestSymptomForecastingModelService:
    """Test suite for the SymptomForecastingModelService."""@pytest.fixture
def mock_model_registry(self):

                """Create a mock model registry."""
        registry = MagicMock(spec=ModelRegistry)
        registry.get_model.return_value = MagicMock(spec=EnsembleModel)
        registry.get_model.return_value.predict = AsyncMock(
            return_value=np.array([3.5, 4.2, 3.8])
        )
        return registry@pytest.fixture
def service(self, mock_model_registry):

                """Create a SymptomForecastingModelService instance for testing."""
        settings = MLSettings()
        return SymptomForecastingModelService(
            model_registry=mock_model_registry, settings=settings
        )@pytest.fixture
def sample_patient(self):

                """Create a sample patient for testing."""
        return Patient(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            first_name="John",
            last_name="Doe",
            date_of_birth="1980-01-01",
            email="john.doe@example.com",
            phone="555-123-4567",
            active=True,
        )@pytest.fixture
def sample_patient_data(self, sample_patient):

                """Create sample patient symptom data for testing."""
        return {
            "patient_id": str(sample_patient.id),
            "demographics": {
                "age": 42,
                "gender": "male",
                "has_chronic_condition": True,
            },
            "medication_history": [
                {
                    "medication": "Sertraline",
                    "start_date": (datetime.now() - timedelta(days=60)).strftime(
                        "%Y-%m-%d"
                    ),
                    "end_date": None,
                    "dosage": "50mg",
                    "frequency": "daily",
                }
            ],
            "biometrics": [
                {
                    "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                    "sleep_hours": 6.5,
                    "activity_level": "moderate",
                    "heart_rate_avg": 72,
                },
                {
                    "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "sleep_hours": 7.2,
                    "activity_level": "high",
                    "heart_rate_avg": 68,
                },
                {
                    "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "sleep_hours": 8.0,
                    "activity_level": "low",
                    "heart_rate_avg": 65,
                },
            ],
            "symptom_history": [
                {
                    "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 6,
                },
                {
                    "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 5,
                },
                {
                    "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "symptom_type": "anxiety",
                    "severity": 4,
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_preprocess_patient_data_success(
            self, service, sample_patient_data):
        """Test that preprocess_patient_data correctly processes valid patient data."""
        # Execute
        patient_id = UUID(sample_patient_data["patient_id"])
        df, metadata = await service.preprocess_patient_data(
            patient_id, sample_patient_data
        )

        # Verify
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "symptom_severity" in df.columns
        assert "sleep_hours" in df.columns
        assert "heart_rate_avg" in df.columns
        assert metadata["symptom_type"] == "anxiety"

    @pytest.mark.asyncio
    async def test_preprocess_patient_data_missing_data(self, service):
                 """Test handling of missing data during preprocessing."""
        # Setup
        incomplete_data = {
            "patient_id": "00000000-0000-0000-0000-000000000001",
            "demographics": {"age": 42, "gender": "male"},
            # Missing symptom_history
            "biometrics": [],
        }

        # Execute
        patient_id = UUID(incomplete_data["patient_id"])
        with pytest.raises(ValueError, match="Insufficient symptom data"):
            await service.preprocess_patient_data(patient_id, incomplete_data)

            @pytest.mark.asyncio
            async def test_predict_symptom_progression(
                    self, service, sample_patient_data):
        """Test prediction of symptom progression."""
        # Setup
        patient_id = UUID(sample_patient_data["patient_id"],
        forecast_days= 3

        # Mock the preprocessing
        with patch.object(
            service,
            "preprocess_patient_data",
            AsyncMock(
                return_value=(
                    pd.DataFrame(
                        {
                            "date": pd.date_range(
                                start=datetime.now() - timedelta(days=3), periods=3
                            ),
                            "symptom_severity": [6, 5, 4],
                            "sleep_hours": [6.5, 7.2, 8.0],
                            "heart_rate_avg": [72, 68, 65],
                        }
                    ),
                    {"symptom_type": "anxiety"},
                )
            ),
        ):
            # Execute
            result = await service.predict_symptom_progression(
                patient_id=patient_id,
                patient_data=sample_patient_data,
                forecast_days=forecast_days,
            )

            # Verify
            assert len(result["forecast"]) == forecast_days
            assert "dates" in result
            assert "values" in result["forecast"]
            assert len(result["forecast"]["values"]) == forecast_days
            assert result["symptom_type"] == "anxiety"
            assert "confidence_intervals" in result["forecast"]

    @pytest.mark.asyncio
    async def test_predict_symptom_progression_invalid_days(
        self, service, sample_patient_data
    ):
        """Test prediction with invalid forecast days."""
        # Setup
        patient_id = UUID(sample_patient_data["patient_id"])

        # Execute & Verify
        with pytest.raises(ValueError, match="Forecast days must be between 1 and 30"):
            await service.predict_symptom_progression(
                patient_id=patient_id,
                patient_data=sample_patient_data,
                forecast_days=0,  # Invalid value
            )

        with pytest.raises(ValueError, match="Forecast days must be between 1 and 30"):
            await service.predict_symptom_progression(
                patient_id=patient_id,
                patient_data=sample_patient_data,
                forecast_days=31,  # Invalid value
            )

    @pytest.mark.asyncio
    async def test_predict_symptom_with_interventions(
        self, service, sample_patient_data
    ):
        """Test prediction with interventions."""
        # Setup
        patient_id = UUID(sample_patient_data["patient_id"],
        forecast_days= 7
        interventions = [
            {
                "type": "medication",
                "name": "Fluoxetine",
                "start_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "expected_effect": -0.5,  # Reduce symptom severity
            },
            {
                "type": "therapy",
                "name": "CBT",
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "expected_effect": -0.3,  # Reduce symptom severity
            },
        ]

        # Mock the preprocessing and model
        with patch.object(
            service,
            "preprocess_patient_data",
            AsyncMock(
                return_value=(
                    pd.DataFrame(
                        {
                            "date": pd.date_range(
                                start=datetime.now() - timedelta(days=3), periods=3
                            ),
                            "symptom_severity": [6, 5, 4],
                            "sleep_hours": [6.5, 7.2, 8.0],
                            "heart_rate_avg": [72, 68, 65],
                        }
                    ),
                    {"symptom_type": "anxiety"},
                )
            ),
        ):
            # Execute
            result = await service.predict_symptom_progression(
                patient_id=patient_id,
                patient_data=sample_patient_data,
                forecast_days=forecast_days,
                interventions=interventions,
            )

            # Verify
            assert len(result["forecast"]) == forecast_days
            assert "intervention_effect" in result
            assert len(result["intervention_effect"]) > 0

            # The baseline forecast should be different from the intervention
            # forecast
            assert result["forecast"] != result["baseline_forecast"]
