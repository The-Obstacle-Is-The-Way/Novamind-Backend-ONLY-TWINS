"""
Clinical Rule Engine Service for the Digital Twin Psychiatry Platform.

This service provides a flexible system for defining, managing, and evaluating
clinical rules for biometric data. It enables psychiatrists to create custom
alert thresholds for their patients.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from app.domain.utils.datetime_utils import UTC
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.entities.digital_twin.biometric_alert import AlertPriority
from app.domain.entities.digital_twin.biometric_rule import (
    BiometricRule,
    LogicalOperator,
    RuleCondition,
    RuleOperator,
)
from app.domain.exceptions import ValidationError
from app.domain.repositories.biometric_rule_repository import BiometricRuleRepository


class ClinicalRuleEngine:
    """
    Service for managing and creating clinical rules for biometric data.
    
    This service provides methods for creating, updating, and managing
    clinical rules that define when alerts should be generated based on
    biometric data patterns.
    """
    
    def __init__(self, rule_repository: BiometricRuleRepository) -> None:
        """
        Initialize the ClinicalRuleEngine.
        
        Args:
            rule_repository: Repository for storing and retrieving clinical rules
        """
        self.rule_repository = rule_repository
    
    async def create_rule(
        self,
        name: str,
        description: str,
        conditions: list[dict[str, Any]],
        logical_operator: str = "AND",
        alert_priority: str = "WARNING",
        patient_id: UUID | None = None,
        provider_id: UUID = None,
        metadata: dict[str, Any] | None = None
    ) -> BiometricRule:
        """
        Create a new clinical rule.
        
        Args:
            name: Name of the rule
            description: Detailed description of the rule's purpose
            conditions: List of condition dictionaries
            logical_operator: How to combine conditions ("AND" or "OR")
            alert_priority: Priority level for alerts ("URGENT", "WARNING", "INFORMATIONAL")
            patient_id: Optional patient ID if this rule is patient-specific
            provider_id: ID of the provider creating the rule
            metadata: Additional contextual information
            
        Returns:
            The created biometric rule
            
        Raises:
            ValidationError: If the rule parameters are invalid
        """
        # Validate and parse conditions
        rule_conditions = []
        for condition_data in conditions:
            condition = self._parse_condition(condition_data)
            rule_conditions.append(condition)
        
        # Parse logical operator
        try:
            logical_op = LogicalOperator(logical_operator)
        except ValueError:
            raise ValidationError(f"Invalid logical operator: {logical_operator}")
        
        # Parse alert priority
        try:
            priority = AlertPriority(alert_priority.lower())
        except ValueError:
            raise ValidationError(f"Invalid alert priority: {alert_priority}")
        
        # Create the rule
        rule = BiometricRule(
            name=name,
            description=description,
            conditions=rule_conditions,
            logical_operator=logical_op,
            alert_priority=priority,
            patient_id=patient_id,
            provider_id=provider_id,
            metadata=metadata or {}
        )
        
        # Save and return the rule
        return await self.rule_repository.save(rule)
    
    def _parse_condition(self, condition_data: dict[str, Any]) -> RuleCondition:
        """
        Parse a condition dictionary into a RuleCondition object.
        
        Args:
            condition_data: Dictionary containing condition parameters
            
        Returns:
            A RuleCondition object
            
        Raises:
            ValidationError: If the condition parameters are invalid
        """
        required_fields = ["data_type", "operator", "threshold_value"]
        for field in required_fields:
            if field not in condition_data:
                raise ValidationError(f"Missing required field in condition: {field}")
        
        # Parse operator
        operator_str = condition_data["operator"]
        try:
            operator = RuleOperator(operator_str)
        except ValueError:
            raise ValidationError(f"Invalid operator: {operator_str}")
        
        # Create the condition
        return RuleCondition(
            data_type=condition_data["data_type"],
            operator=operator,
            threshold_value=condition_data["threshold_value"],
            time_window_hours=condition_data.get("time_window_hours")
        )
    
    async def update_rule(
        self,
        rule_id: UUID,
        name: str | None = None,
        description: str | None = None,
        conditions: list[dict[str, Any]] | None = None,
        logical_operator: str | None = None,
        alert_priority: str | None = None,
        is_active: bool | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BiometricRule:
        """
        Update an existing clinical rule.
        
        Args:
            rule_id: ID of the rule to update
            name: Optional new name for the rule
            description: Optional new description
            conditions: Optional new list of condition dictionaries
            logical_operator: Optional new logical operator
            alert_priority: Optional new alert priority
            is_active: Optional new active status
            metadata: Optional new metadata
            
        Returns:
            The updated biometric rule
            
        Raises:
            EntityNotFoundError: If the rule doesn't exist
            ValidationError: If the update parameters are invalid
        """
        # Get the existing rule
        rule = await self.rule_repository.get_by_id(rule_id)
        if not rule:
            raise ValidationError(f"Rule with ID {rule_id} not found")
        
        # Update fields if provided
        if name is not None:
            rule.name = name
        
        if description is not None:
            rule.description = description
        
        if conditions is not None:
            rule_conditions = []
            for condition_data in conditions:
                condition = self._parse_condition(condition_data)
                rule_conditions.append(condition)
            rule.update_conditions(rule_conditions)
        
        if logical_operator is not None:
            try:
                logical_op = LogicalOperator(logical_operator)
                rule.logical_operator = logical_op
            except ValueError:
                raise ValidationError(f"Invalid logical operator: {logical_operator}")
        
        if alert_priority is not None:
            try:
                priority = AlertPriority(alert_priority.lower())
                rule.alert_priority = priority
            except ValueError:
                raise ValidationError(f"Invalid alert priority: {alert_priority}")
        
        if is_active is not None:
            if is_active:
                rule.activate()
            else:
                rule.deactivate()
        
        if metadata is not None:
            rule.metadata.update(metadata)
        
        rule.updated_at = datetime.now(UTC)
        
        # Save and return the updated rule
        return await self.rule_repository.save(rule)
    
    async def create_standard_rules(
        self,
        provider_id: UUID,
        patient_id: UUID | None = None
    ) -> list[BiometricRule]:
        """
        Create a set of standard clinical rules.
        
        This method creates a set of common clinical rules that are useful
        for most patients, such as heart rate thresholds, sleep disruption
        detection, and activity level monitoring.
        
        Args:
            provider_id: ID of the provider creating the rules
            patient_id: Optional patient ID if these rules are patient-specific
            
        Returns:
            List of created biometric rules
        """
        standard_rules = [
            # Heart rate elevated rule
            {
                "name": "Elevated Heart Rate",
                "description": "Alert when heart rate is consistently elevated",
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
            },
            # Sleep disruption rule
            {
                "name": "Sleep Disruption",
                "description": "Alert when sleep quality is poor and duration is low",
                "conditions": [
                    {
                        "data_type": "sleep_quality",
                        "operator": "<",
                        "threshold_value": 50,
                        "time_window_hours": 24
                    },
                    {
                        "data_type": "sleep_duration",
                        "operator": "<",
                        "threshold_value": 6,
                        "time_window_hours": 24
                    }
                ],
                "logical_operator": "AND",
                "alert_priority": "WARNING"
            },
            # Anxiety spike rule
            {
                "name": "Anxiety Spike",
                "description": "Alert when anxiety levels spike significantly",
                "conditions": [
                    {
                        "data_type": "anxiety_level",
                        "operator": ">",
                        "threshold_value": 7,
                        "time_window_hours": 6
                    }
                ],
                "logical_operator": "AND",
                "alert_priority": "URGENT"
            },
            # Physical inactivity rule
            {
                "name": "Physical Inactivity",
                "description": "Alert when physical activity is consistently low",
                "conditions": [
                    {
                        "data_type": "step_count",
                        "operator": "<",
                        "threshold_value": 1000,
                        "time_window_hours": 24
                    }
                ],
                "logical_operator": "AND",
                "alert_priority": "INFORMATIONAL"
            }
        ]
        
        created_rules = []
        for rule_data in standard_rules:
            rule = await self.create_rule(
                name=rule_data["name"],
                description=rule_data["description"],
                conditions=rule_data["conditions"],
                logical_operator=rule_data["logical_operator"],
                alert_priority=rule_data["alert_priority"],
                patient_id=patient_id,
                provider_id=provider_id
            )
            created_rules.append(rule)
        
        return created_rules
    
    async def get_active_rules_for_patient(
        self,
        patient_id: UUID
    ) -> list[BiometricRule]:
        """
        Get all active rules that apply to a specific patient.
        
        This includes both patient-specific rules and global rules.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            List of active biometric rules for the patient
        """
        # Get patient-specific rules
        patient_rules = await self.rule_repository.get_by_patient_id(patient_id)
        active_patient_rules = [rule for rule in patient_rules if rule.is_active]
        
        # Get global rules
        global_rules = await self.rule_repository.get_all_active()
        active_global_rules = [rule for rule in global_rules if rule.patient_id is None]
        
        # Combine and return
        return active_patient_rules + active_global_rules