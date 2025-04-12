# -*- coding: utf-8 -*-
"""
Unit tests for Biometric Alerts API endpoints.

These tests verify that the Biometric Alerts API endpoints correctly handle
requests and responses, maintain HIPAA compliance, and integrate properly
with the biometric event processor.
"""

import json
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional # Added Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Depends, status # Added Depends, status
from fastapi.testclient import TestClient
from pydantic import parse_obj_as

from app.domain.exceptions import ValidationError, EntityNotFoundError, RepositoryError # Added imports
from app.domain.services.biometric_event_processor import (
    AlertPriority,
    AlertRule, # Assuming AlertRule exists or is defined elsewhere
    BiometricAlert,
    BiometricEventProcessor,
    AlertObserver,
    EmailAlertObserver,
    SMSAlertObserver,
    InAppAlertObserver,
    ClinicalRuleEngine # Assuming ClinicalRuleEngine exists or is defined elsewhere
)
from app.domain.entities.biometric_twin import BiometricDataPoint
from app.domain.entities.digital_twin.biometric_alert import AlertStatus # Added import
from app.presentation.api.v1.endpoints.biometric_alerts import (
    router,
    get_biometric_event_processor,
    get_clinical_rule_engine,
    get_alert_repository,
    get_rule_repository,
    # Assuming get_current_user_id is imported/defined correctly for dependency injection
    # If not, it needs to be imported or mocked appropriately
    # get_current_user_id
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
    AlertAcknowledgementRequest,
    AlertStatusEnum, # Added import
    AlertPriorityEnum # Added import
)
# Assuming BaseRepository exists for type hinting
from app.domain.repositories.base_repository import BaseRepository


@pytest.fixture
def mock_biometric_event_processor():
    """Create a mock BiometricEventProcessor."""
    processor = AsyncMock(spec=BiometricEventProcessor)
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
    engine.register_rule_template = MagicMock()
    engine.register_custom_condition = MagicMock()
    engine.create_rule_from_template = MagicMock()
    engine.rule_templates = {
        "high_heart_rate": {
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds {threshold}",
            "required_parameters": ["threshold"],
            "condition_template": {
                "data_type": "heart_rate",
                "operator": ">",
                "threshold_value": "{threshold}" # Placeholder notation
            }
        },
        "low_heart_rate": {
            "name": "Low Heart Rate",
            "description": "Alert when heart rate falls below {threshold}",
            "required_parameters": ["threshold"],
            "condition_template": {
                "data_type": "heart_rate",
                "operator": "<",
                "threshold_value": "{threshold}"
            }
        }
    }
    return engine


@pytest.fixture
def mock_alert_repository():
    """Create a mock alert repository."""
    repository = AsyncMock(spec=BaseRepository) # Use a base spec if available
    repository.get_alerts = AsyncMock()
    repository.get_alert_by_id = AsyncMock()
    repository.create_alert = AsyncMock()
    repository.update_alert = AsyncMock()
    repository.delete_alert = AsyncMock()
    return repository


@pytest.fixture
def mock_rule_repository():
    """Create a mock rule repository."""
    repository = AsyncMock(spec=BaseRepository) # Use a base spec if available
    repository.get_rules = AsyncMock()
    repository.get_rule_by_id = AsyncMock()
    repository.create_rule = AsyncMock()
    repository.update_rule = AsyncMock()
    repository.delete_rule = AsyncMock()
    return repository

@pytest.fixture
def mock_current_user_id():
    """Fixture for a mock user ID."""
    
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def app(
    mock_biometric_event_processor,
    mock_clinical_rule_engine,
    mock_alert_repository,
    mock_rule_repository,
    mock_current_user_id
):
    """Create a FastAPI test app with the biometric alerts router."""
    app_instance = FastAPI()

    # Override dependencies
    app_instance.dependency_overrides[get_biometric_event_processor] = lambda: mock_biometric_event_processor
    app_instance.dependency_overrides[get_clinical_rule_engine] = lambda: mock_clinical_rule_engine
    app_instance.dependency_overrides[get_alert_repository] = lambda: mock_alert_repository
    app_instance.dependency_overrides[get_rule_repository] = lambda: mock_rule_repository
    # Assuming get_current_user_id is the correct dependency name
    try:
        # Attempt to import the actual dependency function if it exists
        from app.presentation.api.dependencies.auth import get_current_user_id as auth_get_user_id
        app_instance.dependency_overrides[auth_get_user_id] = lambda: mock_current_user_id
    except ImportError:
        # Fallback if the exact path is different or doesn't exist
        print("Warning: Auth dependency get_current_user_id not found at expected path.")
        # Override the one imported locally if needed
        app_instance.dependency_overrides[get_current_user_id] = lambda: mock_current_user_id


    # Include router
    app_instance.include_router(router)

#     return app_instance # FIXME: return outside function


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
    # Assuming AlertRule takes condition as a dict for simplicity in test setup
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
        patient_id=sample_patient_id,
        is_active=True # Assuming is_active attribute exists
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
        alert_id=uuid4(), # Generate a UUID for the alert
        patient_id=sample_data_point.patient_id,
        rule_id=sample_rule.rule_id,
        rule_name=sample_rule.name,
        priority=sample_rule.priority,
        data_point=sample_data_point,
        message="Heart rate 120.0 exceeds threshold of 100.0",
        context={},
        created_at=datetime.now(UTC), # Add created_at
        updated_at=datetime.now(UTC), # Add updated_at
        status=AlertStatus.NEW # Add status
    )


@pytest.mark.db_required() # Assuming db_required is a valid marker
class TestBiometricAlertsEndpoints:
    """Tests for the Biometric Alerts API endpoints."""

    def test_get_alert_rules(self, client, mock_rule_repository, sample_rule):
        """Test that get_alert_rules returns the correct response."""
        # Setup
        mock_rule_repository.get_rules.return_value = ([sample_rule], 1) # Return tuple (items, total)

        # Execute
    response = client.get("/biometric-alerts/rules")

        # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
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
        # Assume create_rule returns the created rule or its ID
        mock_rule_repository.create_rule = AsyncMock(return_value=sample_rule)

    rule_data = {
            # "rule_id": "test-rule-1", # ID should be generated by backend
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
    assert data["rule_id"] == sample_rule.rule_id # Check against generated ID
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
        # Assume create_rule returns the created rule or its ID
        mock_rule_repository.create_rule = AsyncMock(return_value=sample_rule)

    rule_data = {
            # "rule_id": "test-rule-1", # ID should be generated
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
    assert data["rule_id"] == sample_rule.rule_id # Check against generated ID
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
        rule_id = "nonexistent-rule"
        mock_rule_repository.get_rule_by_id.return_value = None

        # Execute
    response = client.get(f"/biometric-alerts/rules/{rule_id}")

        # Verify
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    mock_rule_repository.get_rule_by_id.assert_called_once_with(rule_id)

    def test_update_alert_rule(
        self,
        client,
        mock_rule_repository,
        mock_biometric_event_processor,
        sample_rule
    ):
        """Test that update_alert_rule updates a rule."""
        # Setup
        # Simulate the updated rule being returned or used
        updated_rule = sample_rule.copy(update={
            "name": "Updated High Heart Rate",
            "description": "Updated description",
            "priority": AlertPriority.URGENT,
            "is_active": False
        })
        mock_rule_repository.get_rule_by_id.return_value = sample_rule
        mock_rule_repository.update_rule = AsyncMock(return_value=updated_rule) # Assume update returns the updated rule

    update_data = {
    "name": "Updated High Heart Rate",
    "description": "Updated description",
    "priority": "urgent", # Use string value
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
    mock_biometric_event_processor.add_rule.assert_called_once() # Rule is re-added/updated in processor

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
        mock_rule_repository.delete_rule = AsyncMock(return_value=True) # Assume delete returns success bool

        # Execute
    response = client.delete(f"/biometric-alerts/rules/{sample_rule.rule_id}")

        # Verify
    assert response.status_code == 204
    mock_rule_repository.get_rule_by_id.assert_called_once_with(sample_rule.rule_id)
    mock_rule_repository.delete_rule.assert_called_once_with(sample_rule.rule_id)
    mock_biometric_event_processor.remove_rule.assert_called_once_with(sample_rule.rule_id)

    def test_get_rule_templates(self, client, mock_clinical_rule_engine):
        """Test that get_rule_templates returns the correct response."""
        # Setup - mock_clinical_rule_engine fixture already has templates

        # Execute
    response = client.get("/biometric-alerts/rule-templates")

        # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["templates"]) == 2
    template_ids = {t["template_id"] for t in data["templates"]}
    assert template_ids == {"high_heart_rate", "low_heart_rate"}

    def test_get_alerts(self, client, mock_alert_repository, sample_alert):
        """Test that get_alerts returns the correct response."""
        # Setup
        mock_alert_repository.get_alerts.return_value = ([sample_alert], 1) # Return tuple (items, total)

        # Execute
    response = client.get("/biometric-alerts/alerts")

        # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["alert_id"] == str(sample_alert.alert_id)
    assert data["alerts"][0]["patient_id"] == str(sample_alert.patient_id)
    assert data["alerts"][0]["rule_id"] == sample_alert.rule_id
    assert data["alerts"][0]["priority"] == sample_alert.priority.value
    mock_alert_repository.get_alerts.assert_called_once()

    def test_get_alerts_with_filters(self, client, mock_alert_repository, sample_alert, sample_patient_id):
        """Test that get_alerts handles filters correctly."""
        # Setup
        sample_alert.acknowledged = False # Ensure acknowledged status matches filter
        mock_alert_repository.get_alerts.return_value = ([sample_alert], 1)

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
    assert data["total"] == 1
    mock_alert_repository.get_alerts.assert_called_once()
    call_args, call_kwargs = mock_alert_repository.get_alerts.call_args
    assert call_kwargs["patient_id"] == sample_patient_id
    assert call_kwargs["priority"] == AlertPriority.WARNING # Use Enum
    assert call_kwargs["acknowledged"] is False
    assert isinstance(call_kwargs["start_time"], datetime)
    assert isinstance(call_kwargs["end_time"], datetime)

    def test_acknowledge_alert(self, client, mock_alert_repository, sample_alert, mock_current_user_id):
        """Test that acknowledge_alert acknowledges an alert."""
        # Setup
        alert_id = sample_alert.alert_id
        # Simulate the updated alert being returned
        acknowledged_alert = sample_alert.copy(update={
            "acknowledged": True,
            "acknowledged_by": mock_current_user_id,
            "acknowledged_at": datetime.now(UTC),
            "status": AlertStatus.ACKNOWLEDGED,
            "notes": "Acknowledged by test"
        })
        mock_alert_repository.get_alert_by_id.return_value = sample_alert
        mock_alert_repository.update_alert = AsyncMock(return_value=acknowledged_alert)

        # Execute
    response = client.post(
    f"/biometric-alerts/alerts/{alert_id}/acknowledge",
    json={"notes": "Acknowledged by test"}
    )

        # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["alert_id"] == str(alert_id)
    assert data["acknowledged"] is True
    assert data["status"] == AlertStatusEnum.ACKNOWLEDGED.value # Check against schema enum

    mock_alert_repository.get_alert_by_id.assert_called_once_with(alert_id)
    mock_alert_repository.update_alert.assert_called_once()
        # Check the updated alert object passed to update_alert
    call_args, _ = mock_alert_repository.update_alert.call_args
    updated_alert_arg = call_args[0]
    assert updated_alert_arg.acknowledged is True
    assert updated_alert_arg.acknowledged_by == mock_current_user_id
    assert updated_alert_arg.notes == "Acknowledged by test"

    def test_get_patient_alert_summary(self, client, mock_alert_repository, sample_patient_id):
        """Test retrieving the alert summary for a patient."""
        # Setup
        summary_data = {
            "total_alerts": 15,
            "new_alerts": 3,
            "acknowledged_alerts": 10,
            "resolved_alerts": 2,
            "urgent_alerts": 1,
            "warning_alerts": 5,
            "informational_alerts": 9
        }
        mock_alert_repository.get_patient_alert_summary = AsyncMock(return_value=summary_data)

        # Execute
    response = client.get(f"/biometric-alerts/patients/{sample_patient_id}/summary")

        # Verify
    assert response.status_code == 200
    assert response.json() == summary_data
    mock_alert_repository.get_patient_alert_summary.assert_called_once_with(patient_id=sample_patient_id)