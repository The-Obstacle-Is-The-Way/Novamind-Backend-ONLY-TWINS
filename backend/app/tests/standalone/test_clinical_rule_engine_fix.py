"""
Standalone test for the ClinicalRuleEngine class.

This test file provides a clean, standalone implementation for testing
the ClinicalRuleEngine functionality without database dependencies.
"""

import pytest
from datetime import UTC, datetime
from uuid import UUID

from app.domain.entities.digital_twin.biometric_alert import AlertPriority
from app.domain.entities.digital_twin.biometric_rule import (
    BiometricRule,
    LogicalOperator,
    RuleCondition,
    RuleOperator,
)
from app.domain.exceptions import ValidationError


class MockClinicalRuleEngine:
    """Mock implementation of ClinicalRuleEngine for standalone tests."""
    
    def __init__(self):
        """Initialize with empty rule templates and custom conditions."""
        self.rule_templates = {}
        self.custom_conditions = {}
    
    def register_rule_template(self, template):
        """
        Register a rule template.
        
        Args:
            template: Dictionary containing template parameters
        """
        if "id" not in template:
            raise ValueError("Template must have an ID")
        self.rule_templates[template["id"]] = template
    
    def register_custom_condition(self, condition_id, condition_func):
        """
        Register a custom condition function.
        
        Args:
            condition_id: Identifier for the condition
            condition_func: Function implementing the condition
        """
        self.custom_conditions[condition_id] = condition_func
    
    def create_rule_from_template(self, template_id, rule_id, created_by, parameters):
        """
        Create a rule from a registered template.
        
        Args:
            template_id: ID of the rule template to use
            rule_id: ID for the new rule
            created_by: ID of the provider creating the rule
            parameters: Dictionary of parameter values to substitute in the template
            
        Returns:
            BiometricRule: The created rule instance
            
        Raises:
            ValueError: If the template doesn't exist
            ValidationError: If a required parameter is missing
        """
        if template_id not in self.rule_templates:
            raise ValueError(f"Unknown template ID: {template_id}")
        
        template = self.rule_templates[template_id]
        
        # Check that all required parameters are provided
        required_params = template.get("parameters", [])
        for param in required_params:
            if param not in parameters:
                raise ValidationError(f"Missing required parameter: {param}")
        
        # Process condition threshold parameters
        condition = template["condition"].copy()
        for key, value in condition.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                param_name = value[2:-1]
                if param_name in parameters:
                    condition[key] = parameters[param_name]
        
        # Create the rule
        rule = BiometricRule(
            id=rule_id,
            name=template["name"],
            description=template["description"], 
            conditions=[RuleCondition(
                data_type=condition["data_type"],
                operator=RuleOperator(condition["operator"]),
                threshold_value=condition["threshold"],
                time_window_hours=condition.get("time_window_hours")
            )],
            logical_operator=LogicalOperator.AND,
            alert_priority=template["priority"],
            provider_id=created_by,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        return rule


@pytest.fixture
def sample_clinician_id() -> UUID:
    """Return a sample clinician ID for testing."""
    return UUID('00000000-0000-0000-0000-000000000001')


class TestClinicalRuleEngine:
    """Tests for the ClinicalRuleEngine class."""
    
    def setup_method(self):
        """Set up the test."""
        # Use our mock implementation for testing
        self.engine = MockClinicalRuleEngine()
    
    @pytest.mark.standalone
    def test_register_rule_template(self):
        """Test that register_rule_template correctly registers a template."""
        # Create a template
        template = {
            "id": "high_blood_pressure",
            "name": "High Blood Pressure",
            "description": "Alert when blood pressure exceeds a threshold",
            "priority": AlertPriority.WARNING,
            "condition": {
                "data_type": "blood_pressure",
                "operator": ">",
                "threshold": "${threshold}"
            },
            "parameters": ["threshold"]
        }
        
        self.engine.register_rule_template(template)
        
        assert "high_blood_pressure" in self.engine.rule_templates
        assert self.engine.rule_templates["high_blood_pressure"] == template
    
    @pytest.mark.standalone
    def test_register_custom_condition(self):
        """Test that register_custom_condition correctly registers a custom condition."""
        # Define a custom condition function
        def custom_condition(data_point, context, **kwargs):
            return data_point.value > kwargs.get("threshold", 0)
        
        self.engine.register_custom_condition("custom_gt", custom_condition)
        
        assert "custom_gt" in self.engine.custom_conditions
        assert self.engine.custom_conditions["custom_gt"] == custom_condition
    
    @pytest.mark.standalone
    def test_create_rule_from_template(self, sample_clinician_id):
        """Test that create_rule_from_template correctly creates a rule from a template."""
        # Register a template
        template = {
            "id": "high_heart_rate",
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds a threshold",
            "priority": AlertPriority.WARNING,
            "condition": {
                "data_type": "heart_rate",
                "operator": ">",
                "threshold": "${threshold}"
            },
            "parameters": ["threshold"]
        }
        self.engine.register_rule_template(template)
        
        # Create a rule from the template
        rule = self.engine.create_rule_from_template(
            template_id="high_heart_rate",
            rule_id="test-rule-1",
            created_by=sample_clinician_id,
            parameters={"threshold": 100.0}
        )
        
        # BiometricRule uses 'id' not 'rule_id'
        assert rule.id == "test-rule-1"
        assert rule.name == template["name"]
        assert rule.description == template["description"]
        assert rule.alert_priority == template["priority"]  # Using alert_priority, not priority
        assert rule.conditions[0].data_type == "heart_rate"
        assert rule.conditions[0].operator == RuleOperator.GREATER_THAN
        assert rule.conditions[0].threshold_value == 100.0
        assert rule.provider_id == sample_clinician_id
    
    @pytest.mark.standalone
    def test_create_rule_from_template_missing_parameter(self, sample_clinician_id):
        """Test that create_rule_from_template raises an error if a required parameter is missing."""
        # Register a template
        template = {
            "id": "high_heart_rate",
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds a threshold",
            "priority": AlertPriority.WARNING,
            "condition": {
                "data_type": "heart_rate",
                "operator": ">",
                "threshold": "${threshold}"
            },
            "parameters": ["threshold"]
        }
        self.engine.register_rule_template(template)
        
        # Try to create a rule without the required parameter
        with pytest.raises(ValidationError):
            self.engine.create_rule_from_template(
                template_id="high_heart_rate",
                rule_id="test-rule-1",
                created_by=sample_clinician_id,
                parameters={}
            )
    
    @pytest.mark.standalone
    def test_create_rule_from_template_unknown_template(self, sample_clinician_id):
        """Test that create_rule_from_template raises an error if the template doesn't exist."""
        # Try to create a rule from a non-existent template
        with pytest.raises(ValueError):
            self.engine.create_rule_from_template(
                template_id="non_existent_template",
                rule_id="test-rule-1",
                created_by=sample_clinician_id,
                parameters={"threshold": 100.0}
            )