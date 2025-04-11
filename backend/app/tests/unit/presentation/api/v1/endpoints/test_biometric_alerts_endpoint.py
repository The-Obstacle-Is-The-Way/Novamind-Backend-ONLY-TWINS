# -*- coding: utf-8 -*-
"""
Unit tests for Biometric Alerts API endpoints.

These tests verify that the Biometric Alerts API endpoints correctly handle
requests and responses, maintain HIPAA compliance, and integrate properly
with the biometric event processor.
"""

import json
from datetime import datetime, UTC, UTC, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import parse_obj_as

from app.domain.exceptions import ValidationError
from app.domain.services.biometric_event_processor import (
    AlertPriority,
    AlertRule,
    BiometricAlert,
    BiometricEventProcessor,
    ClinicalRuleEngine
)
from app.domain.entities.biometric_twin import BiometricDataPoint
from app.presentation.api.v1.endpoints.biometric_alerts import (
    router,
    get_biometric_event_processor,
    get_clinical_rule_engine,
    get_alert_repository,
    get_rule_repository,
    get_current_user_id
)
from app.presentation.api.v1.schemas.biometric_alert_schemas import (
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertRuleListResponse,
    BiometricAlertResponse,
    BiometricAlertListResponse,
    AlertRuleTemplateResponse,
    AlertRuleTemplateListResponse,
    AlertAcknowledgementRequest
)


@pytest.fixture
def mock_biometric_event_processor():
    """Create a mock BiometricEventProcessor."""
    processor = AsyncMock(spec=BiometricEventProcessor)
    
    # Mock methods
    processor.add_rule = MagicMock()
    processor.remove_rule = MagicMock()
    processor.register_observer = MagicMock()
    processor.unregister_observer = MagicMock()
    processor.process_data_point = MagicMock()
    
    return processor


@pytest.fixture
def mock_clinical_rule_engine():
    """Create a mock ClinicalRuleEngine."""
    engine = AsyncMock(spec=ClinicalRuleEngine)
    
    # Mock methods
    engine.register_rule_template = MagicMock()
    engine.register_custom_condition = MagicMock()
    engine.create_rule_from_template = MagicMock()
    
    # Mock rule templates
    engine.rule_templates = {
        "high_heart_rate": {
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds a threshold",
            "required_parameters": ["threshold"],
            "condition_template": {
                "data_type": "heart_rate",
                "operator": ">",
                "threshold": "$threshold"
            }
        },
        "low_heart_rate": {
            "name": "Low Heart Rate",
            "description": "Alert when heart rate falls below a threshold",
            "required_parameters": ["threshold"],
            "condition_template": {
                "data_type": "heart_rate",
                "operator": "<",
                "threshold": "$threshold"
            }
        }
    }
    
    return engine


@pytest.fixture
def mock_alert_repository():
    """Create a mock alert repository."""
    repository = AsyncMock()
    
    # Mock methods
    repository.get_alerts = AsyncMock()
    repository.get_alert_by_id = AsyncMock()
    repository.create_alert = AsyncMock()
    repository.update_alert = AsyncMock()
    repository.delete_alert = AsyncMock()
    
    return repository


@pytest.fixture
def mock_rule_repository():
    """Create a mock rule repository."""
    repository = AsyncMock()
    
    # Mock methods
    repository.get_rules = AsyncMock()
    repository.get_rule_by_id = AsyncMock()
    repository.create_rule = AsyncMock()
    repository.update_rule = AsyncMock()
    repository.delete_rule = AsyncMock()
    
    return repository


@pytest.fixture
def app(
    mock_biometric_event_processor,
    mock_clinical_rule_engine,
    mock_alert_repository,
    mock_rule_repository
):
    """Create a FastAPI test app with the biometric alerts router."""
    app = FastAPI()
    
    # Override dependencies
    app.dependency_overrides[get_biometric_event_processor] = lambda: mock_biometric_event_processor
    app.dependency_overrides[get_clinical_rule_engine] = lambda: mock_clinical_rule_engine
    app.dependency_overrides[get_alert_repository] = lambda: mock_alert_repository
    app.dependency_overrides[get_rule_repository] = lambda: mock_rule_repository
    app.dependency_overrides[get_current_user_id] = lambda: UUID("00000000-0000-0000-0000-000000000001")
    
    # Include router
    app.include_router(router)
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_patient_id():
    """Create a sample patient ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_rule(sample_patient_id):
    """Create a sample alert rule."""
    return AlertRule(
        rule_id="test-rule-1",
        name="High Heart Rate",
        description="Alert when heart rate exceeds 100 bpm",
        priority=AlertPriority.WARNING,
        condition={
            "data_type": "heart_rate",
            "operator": ">",
            "threshold": 100.0
        },
        created_by=UUID("00000000-0000-0000-0000-000000000001"),
        patient_id=sample_patient_id
    )


@pytest.fixture
def sample_data_point(sample_patient_id):
    """Create a sample biometric data point."""
    return BiometricDataPoint(
        data_id=UUID("00000000-0000-0000-0000-000000000002"),
        patient_id=sample_patient_id,
        data_type="heart_rate",
        value=120.0,
        timestamp=datetime.now(UTC),
        source="apple_watch",
        metadata={"activity": "resting"},
        confidence=0.95
    )


@pytest.fixture
def sample_alert(sample_rule, sample_data_point):
    """Create a sample biometric alert."""
    return BiometricAlert(
        alert_id="test-alert-1",
        patient_id=sample_data_point.patient_id,
        rule_id=sample_rule.rule_id,
        rule_name=sample_rule.name,
        priority=sample_rule.priority,
        data_point=sample_data_point,
        message="Heart rate 120.0 exceeds threshold of 100.0",
        context={}
    )


@pytest.mark.db_required
class TestBiometricAlertsEndpoints:
    """Tests for the Biometric Alerts API endpoints."""
    
    def test_get_alert_rules(self, client, mock_rule_repository, sample_rule):
        """Test that get_alert_rules returns the correct response."""
        # Setup
        mock_rule_repository.get_rules.return_value = [sample_rule]
        
        # Execute
        response = client.get("/biometric-alerts/rules")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["rules"]) == 1
        assert data["rules"][0]["rule_id"] == sample_rule.rule_id
        assert data["rules"][0]["name"] == sample_rule.name
        assert data["rules"][0]["priority"] == sample_rule.priority.value
        mock_rule_repository.get_rules.assert_called_once()
    
    def test_create_alert_rule_from_template(
        self,
        client,
        mock_rule_repository,
        mock_clinical_rule_engine,
        mock_biometric_event_processor,
        sample_rule
    ):
        """Test that create_alert_rule creates a rule from a template."""
        # Setup
        mock_clinical_rule_engine.create_rule_from_template.return_value = sample_rule
        
        rule_data = {
            "rule_id": "test-rule-1",
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds 100 bpm",
            "priority": "warning",
            "template_id": "high_heart_rate",
            "parameters": {"threshold": 100.0},
            "patient_id": str(sample_rule.patient_id)
        }
        
        # Execute
        response = client.post("/biometric-alerts/rules", json=rule_data)
        
        # Verify
        assert response.status_code == 201
        data = response.json()
        assert data["rule_id"] == sample_rule.rule_id
        assert data["name"] == sample_rule.name
        assert data["priority"] == sample_rule.priority.value
        mock_clinical_rule_engine.create_rule_from_template.assert_called_once()
        mock_rule_repository.create_rule.assert_called_once()
        mock_biometric_event_processor.add_rule.assert_called_once()
    
    def test_create_alert_rule_from_condition(
        self,
        client,
        mock_rule_repository,
        mock_biometric_event_processor,
        sample_rule
    ):
        """Test that create_alert_rule creates a rule from a condition."""
        # Setup
        mock_rule_repository.create_rule.return_value = None
        
        rule_data = {
            "rule_id": "test-rule-1",
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds 100 bpm",
            "priority": "warning",
            "condition": {
                "data_type": "heart_rate",
                "operator": ">",
                "threshold": 100.0
            },
            "patient_id": str(sample_rule.patient_id)
        }
        
        # Execute
        response = client.post("/biometric-alerts/rules", json=rule_data)
        
        # Verify
        assert response.status_code == 201
        data = response.json()
        assert data["rule_id"] == rule_data["rule_id"]
        assert data["name"] == rule_data["name"]
        assert data["priority"] == rule_data["priority"]
        mock_rule_repository.create_rule.assert_called_once()
        mock_biometric_event_processor.add_rule.assert_called_once()
    
    def test_create_alert_rule_validation_error(
        self,
        client,
        mock_clinical_rule_engine
    ):
        """Test that create_alert_rule handles validation errors."""
        # Setup
        mock_clinical_rule_engine.create_rule_from_template.side_effect = ValidationError("Missing required parameter")
        
        rule_data = {
            "rule_id": "test-rule-1",
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds 100 bpm",
            "priority": "warning",
            "template_id": "high_heart_rate",
            "parameters": {},  # Missing required parameter
            "patient_id": "12345678-1234-5678-1234-567812345678"
        }
        
        # Execute
        response = client.post("/biometric-alerts/rules", json=rule_data)
        
        # Verify
        assert response.status_code == 400
        assert "Missing required parameter" in response.json()["detail"]
        mock_clinical_rule_engine.create_rule_from_template.assert_called_once()
    
    def test_get_alert_rule(self, client, mock_rule_repository, sample_rule):
        """Test that get_alert_rule returns the correct response."""
        # Setup
        mock_rule_repository.get_rule_by_id.return_value = sample_rule
        
        # Execute
        response = client.get(f"/biometric-alerts/rules/{sample_rule.rule_id}")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["rule_id"] == sample_rule.rule_id
        assert data["name"] == sample_rule.name
        assert data["priority"] == sample_rule.priority.value
        mock_rule_repository.get_rule_by_id.assert_called_once_with(sample_rule.rule_id)
    
    def test_get_alert_rule_not_found(self, client, mock_rule_repository):
        """Test that get_alert_rule handles not found errors."""
        # Setup
        mock_rule_repository.get_rule_by_id.return_value = None
        
        # Execute
        response = client.get("/biometric-alerts/rules/nonexistent-rule")
        
        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        mock_rule_repository.get_rule_by_id.assert_called_once_with("nonexistent-rule")
    
    def test_update_alert_rule(
        self,
        client,
        mock_rule_repository,
        mock_biometric_event_processor,
        sample_rule
    ):
        """Test that update_alert_rule updates a rule."""
        # Setup
        mock_rule_repository.get_rule_by_id.return_value = sample_rule
        mock_rule_repository.update_rule.return_value = None
        
        update_data = {
            "name": "Updated High Heart Rate",
            "description": "Updated description",
            "priority": "urgent",
            "is_active": False
        }
        
        # Execute
        response = client.put(f"/biometric-alerts/rules/{sample_rule.rule_id}", json=update_data)
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["rule_id"] == sample_rule.rule_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]
        assert data["is_active"] == update_data["is_active"]
        mock_rule_repository.get_rule_by_id.assert_called_once_with(sample_rule.rule_id)
        mock_rule_repository.update_rule.assert_called_once()
        mock_biometric_event_processor.add_rule.assert_called_once()
    
    def test_delete_alert_rule(
        self,
        client,
        mock_rule_repository,
        mock_biometric_event_processor,
        sample_rule
    ):
        """Test that delete_alert_rule deletes a rule."""
        # Setup
        mock_rule_repository.get_rule_by_id.return_value = sample_rule
        mock_rule_repository.delete_rule.return_value = None
        
        # Execute
        response = client.delete(f"/biometric-alerts/rules/{sample_rule.rule_id}")
        
        # Verify
        assert response.status_code == 204
        mock_rule_repository.get_rule_by_id.assert_called_once_with(sample_rule.rule_id)
        mock_rule_repository.delete_rule.assert_called_once_with(sample_rule.rule_id)
        mock_biometric_event_processor.remove_rule.assert_called_once_with(sample_rule.rule_id)
    
    def test_get_rule_templates(self, client, mock_clinical_rule_engine):
        """Test that get_rule_templates returns the correct response."""
        # Setup
        # The mock_clinical_rule_engine fixture already has rule templates
        
        # Execute
        response = client.get("/biometric-alerts/rule-templates")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["templates"]) == 2
        assert data["templates"][0]["template_id"] in ["high_heart_rate", "low_heart_rate"]
        assert data["templates"][1]["template_id"] in ["high_heart_rate", "low_heart_rate"]
    
    def test_get_alerts(self, client, mock_alert_repository, sample_alert):
        """Test that get_alerts returns the correct response."""
        # Setup
        mock_alert_repository.get_alerts.return_value = [sample_alert]
        
        # Execute
        response = client.get("/biometric-alerts/alerts")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["alert_id"] == sample_alert.alert_id
        assert data["alerts"][0]["patient_id"] == str(sample_alert.patient_id)
        assert data["alerts"][0]["rule_id"] == sample_alert.rule_id
        assert data["alerts"][0]["priority"] == sample_alert.priority.value
        mock_alert_repository.get_alerts.assert_called_once()
    
    def test_get_alerts_with_filters(self, client, mock_alert_repository, sample_alert, sample_patient_id):
        """Test that get_alerts handles filters correctly."""
        # Setup
        mock_alert_repository.get_alerts.return_value = [sample_alert]
        
        # Execute
        response = client.get(
            "/biometric-alerts/alerts",
            params={
                "patient_id": str(sample_patient_id),
                "priority": "warning",
                "acknowledged": "false",
                "start_time": "2025-01-01T00:00:00",
                "end_time": "2025-12-31T23:59:59"
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        mock_alert_repository.get_alerts.assert_called_once()
        call_kwargs = mock_alert_repository.get_alerts.call_args[1]
        assert call_kwargs["patient_id"] == sample_patient_id
        assert call_kwargs["priority"].value == "warning"
        assert call_kwargs["acknowledged"] is False
        assert isinstance(call_kwargs["start_time"], datetime)
        assert isinstance(call_kwargs["end_time"], datetime)
    
    def test_acknowledge_alert(self, client, mock_alert_repository, sample_alert):
        """Test that acknowledge_alert acknowledges an alert."""
        # Setup
        mock_alert_repository.get_alert_by_id.return_value = sample_alert
        mock_alert_repository.update_alert.return_value = None
        
        # Execute
        response = client.post(
            f"/biometric-alerts/alerts/{sample_alert.alert_id}/acknowledge",
            json={"notes": "Acknowledged by test"}
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == sample_alert.alert_id
        assert data["acknowledged"] is True
        assert data["acknowledged_by"] == "00000000-0000-0000-0000-000000000001"
        mock_alert_repository.get_alert_by_id.assert_called_once_with(sample_alert.alert_id)
        mock_alert_repository.update_alert.assert_called_once()
    
    def test_get_patient_alerts(self, client, mock_alert_repository, sample_alert, sample_patient_id):
        """Test that get_patient_alerts returns the correct response."""
        # Setup
        mock_alert_repository.get_alerts.return_value = [sample_alert]
        
        # Execute
        response = client.get(f"/biometric-alerts/patients/{sample_patient_id}/alerts")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["alert_id"] == sample_alert.alert_id
        assert data["alerts"][0]["patient_id"] == str(sample_alert.patient_id)
        mock_alert_repository.get_alerts.assert_called_once()
        call_kwargs = mock_alert_repository.get_alerts.call_args[1]
        assert call_kwargs["patient_id"] == sample_patient_id
    
    def test_hipaa_compliance_in_responses(self, client, mock_alert_repository, sample_alert):
        """Test that responses maintain HIPAA compliance by not including unnecessary PHI."""
        # Setup
        mock_alert_repository.get_alerts.return_value = [sample_alert]
        
        # Execute
        response = client.get("/biometric-alerts/alerts")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        
        # Check that only necessary PHI is included
        assert "patient_id" in data["alerts"][0]  # This is necessary for identification
        
        # Check that detailed PHI is not included
        assert "medical_record_number" not in data["alerts"][0]
        assert "social_security_number" not in data["alerts"][0]
        assert "date_of_birth" not in data["alerts"][0]
        assert "address" not in data["alerts"][0]
        
        # Check that data point includes only necessary information
        data_point = data["alerts"][0]["data_point"]
        assert "data_id" in data_point
        assert "data_type" in data_point
        assert "value" in data_point
        assert "timestamp" in data_point
        assert "source" in data_point
        
        # Check that sensitive metadata is not included
        assert "metadata" not in data_point