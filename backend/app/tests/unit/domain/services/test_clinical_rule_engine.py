# -*- coding: utf-8 -*-
"""
Unit tests for the ClinicalRuleEngine service.

These tests verify that the ClinicalRuleEngine correctly creates, updates,
and manages clinical rules for biometric data.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.domain.entities.digital_twin.biometric_alert import AlertPriority
from app.domain.entities.digital_twin.biometric_rule import
    BiometricRule, RuleCondition, RuleOperator, LogicalOperator
()
from app.domain.exceptions import ValidationError
from app.domain.services.clinical_rule_engine import ClinicalRuleEngine


@pytest.mark.db_required() # Assuming db_required is a valid marker
class TestClinicalRuleEngine:
    """Tests for the ClinicalRuleEngine service."""

    @pytest.fixture
    def mock_rule_repository(self):
        """Create a mock BiometricRuleRepository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_patient_id = AsyncMock()
        repo.get_all_active = AsyncMock()
        return repo

        @pytest.fixture
        def rule_engine(self, mock_rule_repository):
        """Create a ClinicalRuleEngine with mock dependencies."""
        
        return ClinicalRuleEngine(mock_rule_repository)

        @pytest.fixture
        def sample_patient_id(self):
        """Create a sample patient ID."""
        
        return UUID('12345678-1234-5678-1234-567812345678')

        @pytest.fixture
        def sample_provider_id(self):
        """Create a sample provider ID."""
        
        return UUID('87654321-8765-4321-8765-432187654321')

        @pytest.fixture
        def sample_rule_data(self):
        """Create sample rule data for testing."""
        
        return {
        "name": "Elevated Heart Rate",
        "description": "Alert when heart rate is above 100",
        "conditions": [
        {
        "data_type": "heart_rate",
        "operator": ">",
        "threshold_value": 100,
        "time_window_hours": 1
    }
    ],
    "logical_operator": "AND",
    "alert_priority": "WARNING"
    }

    @pytest.fixture
    def sample_rule(self, sample_patient_id, sample_provider_id):
        """Create a sample BiometricRule."""
        condition = RuleCondition()
            data_type="heart_rate",
            operator=RuleOperator.GREATER_THAN,
            threshold_value=100,
            time_window_hours=1
        (        )
        return BiometricRule()
            name="Elevated Heart Rate",
            description="Alert when heart rate is above 100",
            conditions=[condition],
            logical_operator=LogicalOperator.AND,
            alert_priority=AlertPriority.WARNING,
            patient_id=sample_patient_id,
            provider_id=sample_provider_id,
            is_active=True
        (        )

        @pytest.mark.asyncio
        async def test_create_rule(self, rule_engine, mock_rule_repository,)
        (    sample_rule_data, sample_patient_id, sample_provider_id):
    """Test that create_rule correctly creates a rule from the provided data."""
        # Setup
    mock_rule_repository.save.return_value = MagicMock() # Return a mock object

        # Execute
    result = await rule_engine.create_rule()
    name=sample_rule_data["name"],
    description=sample_rule_data["description"],
    conditions=sample_rule_data["conditions"],
    logical_operator=sample_rule_data["logical_operator"],
    alert_priority=sample_rule_data["alert_priority"],
    patient_id=sample_patient_id,
    provider_id=sample_provider_id
    (    )

        # Verify
    mock_rule_repository.save.assert_called_once()
    saved_rule = mock_rule_repository.save.call_args[0][0]
    assert isinstance(saved_rule, BiometricRule)
    assert saved_rule.name == sample_rule_data["name"]
    assert saved_rule.description == sample_rule_data["description"]
    assert len(saved_rule.conditions) == 1
    assert saved_rule.conditions[0].data_type == "heart_rate"
    assert saved_rule.conditions[0].operator == RuleOperator.GREATER_THAN
    assert saved_rule.conditions[0].threshold_value == 100
    assert saved_rule.conditions[0].time_window_hours == 1
    assert saved_rule.logical_operator == LogicalOperator.AND
    assert saved_rule.alert_priority == AlertPriority.WARNING
    assert saved_rule.patient_id == sample_patient_id
    assert saved_rule.provider_id == sample_provider_id
    assert saved_rule.is_active is True

    @pytest.mark.asyncio
    async def test_create_rule_with_invalid_operator(self, rule_engine, sample_rule_data,)
    (    sample_patient_id, sample_provider_id):
    """Test that create_rule raises ValidationError for invalid operators."""
        # Modify the sample data to have an invalid operator
    sample_rule_data["conditions"][0]["operator"] = "INVALID_OPERATOR"

        # Execute and verify
    with pytest.raises(ValidationError):
        await rule_engine.create_rule()
        name=sample_rule_data["name"],
        description=sample_rule_data["description"],
        conditions=sample_rule_data["conditions"],
        logical_operator=sample_rule_data["logical_operator"],
        alert_priority=sample_rule_data["alert_priority"],
        patient_id=sample_patient_id,
        provider_id=sample_provider_id
        (    )

        @pytest.mark.asyncio
        async def test_create_rule_with_invalid_logical_operator(self, rule_engine, sample_rule_data,)
        (    sample_patient_id, sample_provider_id):
    """Test that create_rule raises ValidationError for invalid logical operators."""
        # Execute and verify
    with pytest.raises(ValidationError):
        await rule_engine.create_rule()
        name=sample_rule_data["name"],
        description=sample_rule_data["description"],
        conditions=sample_rule_data["conditions"],
        logical_operator="INVALID_OPERATOR",
        alert_priority=sample_rule_data["alert_priority"],
        patient_id=sample_patient_id,
        provider_id=sample_provider_id
        (    )

        @pytest.mark.asyncio
        async def test_create_rule_with_invalid_priority(self, rule_engine, sample_rule_data,)
        (    sample_patient_id, sample_provider_id):
    """Test that create_rule raises ValidationError for invalid priorities."""
        # Execute and verify
    with pytest.raises(ValidationError):
        await rule_engine.create_rule()
        name=sample_rule_data["name"],
        description=sample_rule_data["description"],
        conditions=sample_rule_data["conditions"],
        logical_operator=sample_rule_data["logical_operator"],
        alert_priority="INVALID_PRIORITY",
        patient_id=sample_patient_id,
        provider_id=sample_provider_id
        (    )

        @pytest.mark.asyncio
        async def test_update_rule(self, rule_engine, mock_rule_repository, sample_rule):
        """Test that update_rule correctly updates an existing rule."""
        # Setup
        rule_id = sample_rule.rule_id
        mock_rule_repository.get_by_id.return_value = sample_rule
        mock_rule_repository.save.return_value = sample_rule # Return the rule itself

        # Execute
        result = await rule_engine.update_rule()
        rule_id=rule_id,
        name="Updated Rule Name",
        description="Updated description",
        is_active=False
        (    )

        # Verify
        mock_rule_repository.get_by_id.assert_called_once_with(rule_id)
        mock_rule_repository.save.assert_called_once()
        updated_rule = mock_rule_repository.save.call_args[0][0]
        assert updated_rule.name == "Updated Rule Name"
        assert updated_rule.description == "Updated description"
        assert updated_rule.is_active is False
        # Ensure other properties weren't changed
        assert updated_rule.conditions == sample_rule.conditions
        assert updated_rule.logical_operator == sample_rule.logical_operator
        assert updated_rule.alert_priority == sample_rule.alert_priority

        @pytest.mark.asyncio
        async def test_update_rule_conditions(self, rule_engine, mock_rule_repository, sample_rule):
        """Test that update_rule correctly updates rule conditions."""
        # Setup
        rule_id = sample_rule.rule_id
        mock_rule_repository.get_by_id.return_value = sample_rule
        mock_rule_repository.save.return_value = sample_rule # Return the rule itself

        new_conditions = [
        {
        "data_type": "heart_rate",
        "operator": ">",
        "threshold_value": 120,
        "time_window_hours": 2
    },
        {
        "data_type": "blood_pressure_systolic",
        "operator": ">",
        "threshold_value": 140,
        "time_window_hours": 2
    }
    ]

        # Execute
    result = await rule_engine.update_rule()
    rule_id=rule_id,
    conditions=new_conditions,
    logical_operator="OR"
(    )

        # Verify
    mock_rule_repository.save.assert_called_once()
    updated_rule = mock_rule_repository.save.call_args[0][0]
    assert len(updated_rule.conditions) == 2
    assert updated_rule.conditions[0].data_type == "heart_rate"
    assert updated_rule.conditions[0].threshold_value == 120
    assert updated_rule.conditions[1].data_type == "blood_pressure_systolic"
    assert updated_rule.logical_operator == LogicalOperator.OR

    @pytest.mark.asyncio
    async def test_update_nonexistent_rule(self, rule_engine, mock_rule_repository):
        """Test that update_rule raises ValidationError for nonexistent rules."""
        # Setup
        rule_id = uuid4()
        mock_rule_repository.get_by_id.return_value = None

        # Execute and verify
        with pytest.raises(ValidationError):
        await rule_engine.update_rule()
        rule_id=rule_id,
        name="Updated Rule Name"
        (    )

        @pytest.mark.asyncio
        async def test_create_standard_rules(self, rule_engine, mock_rule_repository,)
        (    sample_provider_id, sample_patient_id):
    """Test that create_standard_rules creates a set of predefined rules."""
        # Setup
        # Make save return the rule passed to it
    async def save_side_effect(rule):
        #     return rule # FIXME: return outside function
        mock_rule_repository.save.side_effect = save_side_effect

        # Execute
        result = await rule_engine.create_standard_rules()
        provider_id=sample_provider_id,
        patient_id=sample_patient_id
        (    )

        # Verify
        assert len(result) == 4  # Should create 4 standard rules
        assert mock_rule_repository.save.call_count == 4

        # Check that each rule has the correct properties
        rule_names = [rule.name for rule in result]
        assert "Elevated Heart Rate" in rule_names
        assert "Sleep Disruption" in rule_names
        assert "Anxiety Spike" in rule_names
        assert "Physical Inactivity" in rule_names

        # Check that all rules have the correct patient and provider IDs
        for rule in result:
        assert rule.patient_id == sample_patient_id
        assert rule.provider_id == sample_provider_id
        assert rule.is_active is True

        @pytest.mark.asyncio
        async def test_get_active_rules_for_patient(self, rule_engine, mock_rule_repository,)
        (    sample_patient_id, sample_rule):
    """Test that get_active_rules_for_patient returns all active rules for a patient."""
        # Setup
    patient_specific_rule = sample_rule
    global_rule = BiometricRule()
    name="Global Rule",
    description="A rule that applies to all patients",
    conditions=[
    RuleCondition()
    data_type="anxiety_level",
    operator=RuleOperator.GREATER_THAN,
    threshold_value=8
    (    )
    ],
    logical_operator=LogicalOperator.AND,
    alert_priority=AlertPriority.URGENT,
    patient_id=None,  # Global rule
    provider_id=uuid4(),
    is_active=True
    (    )

    mock_rule_repository.get_by_patient_id.return_value = [patient_specific_rule]
    mock_rule_repository.get_all_active.return_value = [global_rule]

        # Execute
    result = await rule_engine.get_active_rules_for_patient(sample_patient_id)

        # Verify
    assert len(result) == 2
    assert patient_specific_rule in result
    assert global_rule in result
    mock_rule_repository.get_by_patient_id.assert_called_once_with(sample_patient_id)
    mock_rule_repository.get_all_active.assert_called_once()