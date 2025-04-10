# -*- coding: utf-8 -*-
"""
Unit tests for the ML Adapters.

These tests verify that the ML Adapters correctly translate between
domain entities and ML infrastructure models.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.infrastructure.ml.adapters import (
    BiometricDataAdapter,
    SymptomDataAdapter,
    GeneticDataAdapter,
    PatientDataAdapter,
    AlertAdapter
)
from app.domain.entities.digital_twin.biometric_twin import BiometricDataPoint, BiometricTwin
from app.domain.entities.digital_twin.biometric_alert import BiometricAlert, AlertPriority
from app.domain.entities.digital_twin.biometric_rule import BiometricRule, RuleCondition, RuleOperator


@pytest.mark.db_required
class TestBiometricDataAdapter:
    """Tests for the BiometricDataAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a BiometricDataAdapter."""
        return BiometricDataAdapter()

    @pytest.fixture
    def sample_biometric_twin(self):
        """Create a sample BiometricTwin."""
        patient_id = uuid4()
        twin = BiometricTwin(patient_id=patient_id)
        
        # Add heart rate data points
        for i in range(10):
            twin.add_data_point(
                BiometricDataPoint(
                    data_type="heart_rate",
                    value=70 + i,
                    timestamp=datetime.now() - timedelta(days=10-i),
                    source="test_device"
                )
            )
        
        # Add sleep data points
        for i in range(10):
            twin.add_data_point(
                BiometricDataPoint(
                    data_type="sleep_duration",
                    value=7.5 - (i * 0.2),
                    timestamp=datetime.now() - timedelta(days=10-i),
                    source="test_device"
                )
            )
            
        return twin

    @pytest.mark.db_required
def test_to_ml_format_success(self, adapter, sample_biometric_twin):
        """Test that to_ml_format correctly converts a BiometricTwin to ML format."""
        # Execute
        ml_data = adapter.to_ml_format(sample_biometric_twin)
        
        # Verify
        assert isinstance(ml_data, dict)
        assert "heart_rate" in ml_data
        assert "sleep_duration" in ml_data
        
        # Check heart rate data
        heart_rate_data = ml_data["heart_rate"]
        assert isinstance(heart_rate_data, list)
        assert len(heart_rate_data) == 10
        for data_point in heart_rate_data:
            assert "timestamp" in data_point
            assert "value" in data_point
            assert isinstance(data_point["value"], (int, float))
            
        # Check sleep data
        sleep_data = ml_data["sleep_duration"]
        assert isinstance(sleep_data, list)
        assert len(sleep_data) == 10
        for data_point in sleep_data:
            assert "timestamp" in data_point
            assert "value" in data_point
            assert isinstance(data_point["value"], (int, float))

    @pytest.mark.db_required
def test_to_ml_format_empty_twin(self, adapter):
        """Test that to_ml_format handles an empty BiometricTwin gracefully."""
        # Setup
        empty_twin = BiometricTwin(patient_id=uuid4())
        
        # Execute
        ml_data = adapter.to_ml_format(empty_twin)
        
        # Verify
        assert isinstance(ml_data, dict)
        assert len(ml_data) == 0

    @pytest.mark.db_required
def test_from_ml_format_success(self, adapter):
        """Test that from_ml_format correctly converts ML format to domain entities."""
        # Setup
        patient_id = uuid4()
        ml_data = {
            "heart_rate": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "value": 75
                },
                {
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "value": 72
                }
            ],
            "sleep_duration": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "value": 7.5
                },
                {
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "value": 8.0
                }
            ]
        }
        
        # Execute
        biometric_twin = adapter.from_ml_format(ml_data, patient_id)
        
        # Verify
        assert isinstance(biometric_twin, BiometricTwin)
        assert biometric_twin.patient_id == patient_id
        assert len(biometric_twin.data_points) == 4  # 2 heart rate + 2 sleep
        
        # Check data types
        data_types = [dp.data_type for dp in biometric_twin.data_points]
        assert "heart_rate" in data_types
        assert "sleep_duration" in data_types
        
        # Check values
        heart_rate_points = [dp for dp in biometric_twin.data_points if dp.data_type == "heart_rate"]
        sleep_points = [dp for dp in biometric_twin.data_points if dp.data_type == "sleep_duration"]
        assert len(heart_rate_points) == 2
        assert len(sleep_points) == 2
        assert any(dp.value == 75 for dp in heart_rate_points)
        assert any(dp.value == 7.5 for dp in sleep_points)


@pytest.mark.db_required
class TestSymptomDataAdapter:
    """Tests for the SymptomDataAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a SymptomDataAdapter."""
        return SymptomDataAdapter()

    @pytest.fixture
    def sample_symptom_data(self):
        """Create sample symptom data."""
        return {
            "anxiety": [
                {
                    "date": datetime.now().date().isoformat(),
                    "severity": 5
                },
                {
                    "date": (datetime.now() - timedelta(days=1)).date().isoformat(),
                    "severity": 6
                }
            ],
            "mood": [
                {
                    "date": datetime.now().date().isoformat(),
                    "severity": 4
                },
                {
                    "date": (datetime.now() - timedelta(days=1)).date().isoformat(),
                    "severity": 3
                }
            ]
        }

    @pytest.mark.db_required
def test_to_ml_format_success(self, adapter, sample_symptom_data):
        """Test that to_ml_format correctly converts symptom data to ML format."""
        # Setup
        domain_data = {
            "anxiety": [
                {"date": datetime.now().date(), "severity": 5},
                {"date": (datetime.now() - timedelta(days=1)).date(), "severity": 6}
            ],
            "mood": [
                {"date": datetime.now().date(), "severity": 4},
                {"date": (datetime.now() - timedelta(days=1)).date(), "severity": 3}
            ]
        }
        
        # Execute
        ml_data = adapter.to_ml_format(domain_data)
        
        # Verify
        assert isinstance(ml_data, dict)
        assert "anxiety" in ml_data
        assert "mood" in ml_data
        
        # Check anxiety data
        anxiety_data = ml_data["anxiety"]
        assert isinstance(anxiety_data, list)
        assert len(anxiety_data) == 2
        for data_point in anxiety_data:
            assert "date" in data_point
            assert "severity" in data_point
            assert isinstance(data_point["date"], str)
            assert isinstance(data_point["severity"], int)
            
        # Check mood data
        mood_data = ml_data["mood"]
        assert isinstance(mood_data, list)
        assert len(mood_data) == 2
        for data_point in mood_data:
            assert "date" in data_point
            assert "severity" in data_point
            assert isinstance(data_point["date"], str)
            assert isinstance(data_point["severity"], int)

    @pytest.mark.db_required
def test_from_ml_format_success(self, adapter, sample_symptom_data):
        """Test that from_ml_format correctly converts ML format to domain entities."""
        # Execute
        domain_data = adapter.from_ml_format(sample_symptom_data)
        
        # Verify
        assert isinstance(domain_data, dict)
        assert "anxiety" in domain_data
        assert "mood" in domain_data
        
        # Check anxiety data
        anxiety_data = domain_data["anxiety"]
        assert isinstance(anxiety_data, list)
        assert len(anxiety_data) == 2
        for data_point in anxiety_data:
            assert "date" in data_point
            assert "severity" in data_point
            assert isinstance(data_point["date"], datetime)
            assert isinstance(data_point["severity"], int)
            
        # Check mood data
        mood_data = domain_data["mood"]
        assert isinstance(mood_data, list)
        assert len(mood_data) == 2
        for data_point in mood_data:
            assert "date" in data_point
            assert "severity" in data_point
            assert isinstance(data_point["date"], datetime)
            assert isinstance(data_point["severity"], int)


@pytest.mark.db_required
class TestGeneticDataAdapter:
    """Tests for the GeneticDataAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a GeneticDataAdapter."""
        return GeneticDataAdapter()

    @pytest.fixture
    def sample_genetic_data(self):
        """Create sample genetic data."""
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
                }
            ]
        }

    @pytest.mark.db_required
def test_to_ml_format_success(self, adapter, sample_genetic_data):
        """Test that to_ml_format correctly converts genetic data to ML format."""
        # Setup
        domain_data = {
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
                }
            ]
        }
        
        # Execute
        ml_data = adapter.to_ml_format(domain_data)
        
        # Verify
        assert ml_data == domain_data  # Should be the same format

    @pytest.mark.db_required
def test_from_ml_format_success(self, adapter, sample_genetic_data):
        """Test that from_ml_format correctly converts ML format to domain entities."""
        # Execute
        domain_data = adapter.from_ml_format(sample_genetic_data)
        
        # Verify
        assert domain_data == sample_genetic_data  # Should be the same format


@pytest.mark.db_required
class TestPatientDataAdapter:
    """Tests for the PatientDataAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a PatientDataAdapter."""
        return PatientDataAdapter()

    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data."""
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

    @pytest.mark.db_required
def test_to_ml_format_success(self, adapter, sample_patient_data):
        """Test that to_ml_format correctly converts patient data to ML format."""
        # Setup
        domain_data = {
            "id": UUID(sample_patient_data["id"]),
            "demographics": sample_patient_data["demographics"],
            "conditions": sample_patient_data["conditions"],
            "medication_history": sample_patient_data["medication_history"]
        }
        
        # Execute
        ml_data = adapter.to_ml_format(domain_data)
        
        # Verify
        assert isinstance(ml_data, dict)
        assert "id" in ml_data
        assert "demographics" in ml_data
        assert "conditions" in ml_data
        assert "medication_history" in ml_data
        
        # Check ID is converted to string
        assert isinstance(ml_data["id"], str)
        assert ml_data["id"] == sample_patient_data["id"]
        
        # Check other fields are preserved
        assert ml_data["demographics"] == sample_patient_data["demographics"]
        assert ml_data["conditions"] == sample_patient_data["conditions"]
        assert ml_data["medication_history"] == sample_patient_data["medication_history"]

    @pytest.mark.db_required
def test_from_ml_format_success(self, adapter, sample_patient_data):
        """Test that from_ml_format correctly converts ML format to domain entities."""
        # Execute
        domain_data = adapter.from_ml_format(sample_patient_data)
        
        # Verify
        assert isinstance(domain_data, dict)
        assert "id" in domain_data
        assert "demographics" in domain_data
        assert "conditions" in domain_data
        assert "medication_history" in domain_data
        
        # Check ID is converted to UUID
        assert isinstance(domain_data["id"], UUID)
        assert str(domain_data["id"]) == sample_patient_data["id"]
        
        # Check other fields are preserved
        assert domain_data["demographics"] == sample_patient_data["demographics"]
        assert domain_data["conditions"] == sample_patient_data["conditions"]
        assert domain_data["medication_history"] == sample_patient_data["medication_history"]


@pytest.mark.db_required
class TestAlertAdapter:
    """Tests for the AlertAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create an AlertAdapter."""
        return AlertAdapter()

    @pytest.fixture
    def sample_biometric_alert(self):
        """Create a sample BiometricAlert."""
        patient_id = uuid4()
        rule_id = uuid4()
        provider_id = uuid4()
        
        return BiometricAlert(
            alert_id=uuid4(),
            patient_id=patient_id,
            rule_id=rule_id,
            provider_id=provider_id,
            data_type="heart_rate",
            value=120,
            threshold=100,
            operator=RuleOperator.GREATER_THAN,
            priority=AlertPriority.WARNING,
            timestamp=datetime.now(),
            acknowledged=False
        )

    @pytest.mark.db_required
def test_to_ml_format_success(self, adapter, sample_biometric_alert):
        """Test that to_ml_format correctly converts a BiometricAlert to ML format."""
        # Execute
        ml_data = adapter.to_ml_format(sample_biometric_alert)
        
        # Verify
        assert isinstance(ml_data, dict)
        assert "alert_id" in ml_data
        assert "patient_id" in ml_data
        assert "rule_id" in ml_data
        assert "provider_id" in ml_data
        assert "data_type" in ml_data
        assert "value" in ml_data
        assert "threshold" in ml_data
        assert "operator" in ml_data
        assert "priority" in ml_data
        assert "timestamp" in ml_data
        assert "acknowledged" in ml_data
        
        # Check ID conversions
        assert isinstance(ml_data["alert_id"], str)
        assert isinstance(ml_data["patient_id"], str)
        assert isinstance(ml_data["rule_id"], str)
        assert isinstance(ml_data["provider_id"], str)
        
        # Check enum conversions
        assert isinstance(ml_data["operator"], str)
        assert isinstance(ml_data["priority"], str)
        
        # Check timestamp conversion
        assert isinstance(ml_data["timestamp"], str)
        
        # Check values
        assert ml_data["data_type"] == "heart_rate"
        assert ml_data["value"] == 120
        assert ml_data["threshold"] == 100
        assert ml_data["operator"] == "GREATER_THAN"
        assert ml_data["priority"] == "WARNING"
        assert ml_data["acknowledged"] is False

    @pytest.mark.db_required
def test_from_ml_format_success(self, adapter, sample_biometric_alert):
        """Test that from_ml_format correctly converts ML format to a BiometricAlert."""
        # Setup
        ml_data = {
            "alert_id": str(sample_biometric_alert.alert_id),
            "patient_id": str(sample_biometric_alert.patient_id),
            "rule_id": str(sample_biometric_alert.rule_id),
            "provider_id": str(sample_biometric_alert.provider_id),
            "data_type": "heart_rate",
            "value": 120,
            "threshold": 100,
            "operator": "GREATER_THAN",
            "priority": "WARNING",
            "timestamp": sample_biometric_alert.timestamp.isoformat(),
            "acknowledged": False
        }
        
        # Execute
        alert = adapter.from_ml_format(ml_data)
        
        # Verify
        assert isinstance(alert, BiometricAlert)
        assert alert.alert_id == UUID(ml_data["alert_id"])
        assert alert.patient_id == UUID(ml_data["patient_id"])
        assert alert.rule_id == UUID(ml_data["rule_id"])
        assert alert.provider_id == UUID(ml_data["provider_id"])
        assert alert.data_type == ml_data["data_type"]
        assert alert.value == ml_data["value"]
        assert alert.threshold == ml_data["threshold"]
        assert alert.operator == RuleOperator.GREATER_THAN
        assert alert.priority == AlertPriority.WARNING
        assert isinstance(alert.timestamp, datetime)
        assert alert.acknowledged is False