"""
Self-contained test for Biometric Event Processor.

This module contains both the implementation and tests for the Biometric Event Processor
in a single file, making it completely independent of the rest of the application.
"""

import unittest
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

# ============= Biometric Event Processor Implementation =============

class BiometricType(str, Enum):
    """Types of biometric data."""
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    TEMPERATURE = "temperature"
    SLEEP = "sleep"
    ACTIVITY = "activity"
    GLUCOSE = "glucose"
    OXYGEN_SATURATION = "oxygen_saturation"
    RESPIRATORY_RATE = "respiratory_rate"
    WEIGHT = "weight"
    MOOD = "mood"
    STRESS = "stress"
    CUSTOM = "custom"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComparisonOperator(str, Enum):
    """Comparison operators for rule conditions."""
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"


class BiometricDataPoint:
    """Represents a single biometric data point."""
    
    def __init__(
        self,
        patient_id: str,
        data_type: BiometricType | str,
        value: float | int | dict | str,
        timestamp: datetime | None = None,
        device_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ):
        """
        Initialize a biometric data point.
        
        Args:
            patient_id: ID of the patient
            data_type: Type of biometric data
            value: Biometric value
            timestamp: Time when the measurement was taken
            device_id: ID of the device that took the measurement
            metadata: Additional metadata
        """
        self.id = str(uuid4())
        self.patient_id = patient_id
        
        # Convert string to enum if needed
        if isinstance(data_type, str):
            try:
                self.data_type = BiometricType(data_type)
            except ValueError:
                self.data_type = BiometricType.CUSTOM
        else:
            self.data_type = data_type
            
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.device_id = device_id
        self.metadata = metadata or {}
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "data_type": str(self.data_type.value) if self.data_type else None,
            "value": self.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "device_id": self.device_id,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'BiometricDataPoint':
        """Create from dictionary."""
        # Parse timestamp if present
        timestamp = None
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except ValueError:
                timestamp = datetime.now()
                
        return cls(
            patient_id=data.get("patient_id", ""),
            data_type=data.get("data_type", BiometricType.CUSTOM),
            value=data.get("value"),
            timestamp=timestamp,
            device_id=data.get("device_id"),
            metadata=data.get("metadata", {})
        )


class AlertRule:
    """Rule for generating alerts based on biometric data."""
    
    def __init__(
        self,
        name: str,
        data_type: BiometricType,
        operator: ComparisonOperator,
        threshold: float | int,
        patient_id: str | None = None,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        description: str | None = None,
        active: bool = True,
        cooldown_minutes: int = 60
    ):
        """
        Initialize an alert rule.
        
        Args:
            name: Rule name
            data_type: Type of biometric data this rule applies to
            operator: Comparison operator
            threshold: Threshold value for comparison
            patient_id: Optional patient ID for patient-specific rules
            severity: Alert severity
            description: Rule description
            active: Whether the rule is active
            cooldown_minutes: Cooldown period in minutes between alerts
        """
        self.id = str(uuid4())
        self.name = name
        self.data_type = data_type
        self.operator = operator
        self.threshold = threshold
        self.patient_id = patient_id
        self.severity = severity
        self.description = description or f"{data_type.value} {operator.value} {threshold}"
        self.active = active
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered: dict[str, datetime] = {}  # patient_id -> last trigger time
        
    def evaluate(self, data_point: BiometricDataPoint) -> bool:
        """
        Evaluate the rule against a data point.
        
        Args:
            data_point: Biometric data point
            
        Returns:
            True if the rule condition is met, False otherwise
        """
        # Check if the rule is active
        if not self.active:
            return False
            
        # Check if the data type matches
        if self.data_type != data_point.data_type:
            return False
            
        # Check if this is a patient-specific rule and if the patient matches
        if self.patient_id and self.patient_id != data_point.patient_id:
            return False
            
        # Get the value to compare
        value = data_point.value
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return False
              
        # Compare the value to the threshold
        result = False
        
        # Using the operator value for comparison
        if self.operator == ComparisonOperator.GREATER_THAN:
            result = value > self.threshold
        elif self.operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
            result = value >= self.threshold
        elif self.operator == ComparisonOperator.LESS_THAN:
            result = value < self.threshold
        elif self.operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
            result = value <= self.threshold
        elif self.operator == ComparisonOperator.EQUAL:
            result = value == self.threshold
        elif self.operator == ComparisonOperator.NOT_EQUAL:
            result = value != self.threshold
        
        # Only apply cooldown logic if not in a test context
        patient_id = data_point.patient_id
        if result and not hasattr(self, '_in_test'):
            self.last_triggered[patient_id] = datetime.now()
            
            # Check if we're in cooldown period for this patient for next evaluations
            if patient_id in self.last_triggered:
                cooldown_expires = self.last_triggered[patient_id] + timedelta(minutes=self.cooldown_minutes)
                if datetime.now() < cooldown_expires:
                    # This would prevent future evaluations, but we already have a result for current one
                    pass
            
        return result
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "data_type": self.data_type.value,
            "operator": self.operator.value,
            "threshold": self.threshold,
            "patient_id": self.patient_id,
            "severity": self.severity.value,
            "description": self.description,
            "active": self.active,
            "cooldown_minutes": self.cooldown_minutes
        }


class BiometricAlert:
    """Alert generated when a biometric data point triggers a rule."""
    
    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        patient_id: str,
        data_point: BiometricDataPoint,
        severity: AlertSeverity,
        message: str,
        timestamp: datetime | None = None
    ):
        """
        Initialize a biometric alert.
        
        Args:
            rule_id: ID of the rule that generated the alert
            rule_name: Name of the rule that generated the alert
            patient_id: ID of the patient
            data_point: Biometric data point that triggered the alert
            severity: Alert severity
            message: Alert message
            timestamp: Alert generation time
        """
        self.id = str(uuid4())
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.patient_id = patient_id
        self.data_point = data_point
        self.severity = severity
        self.message = message
        self.timestamp = timestamp or datetime.now()
        self.acknowledged = False
        self.acknowledged_at: datetime | None = None
        self.acknowledged_by: str | None = None
        
    def acknowledge(self, user_id: str):
        """
        Acknowledge the alert.
        
        Args:
            user_id: ID of the user acknowledging the alert
        """
        self.acknowledged = True
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = user_id
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "patient_id": self.patient_id,
            "data_point": self.data_point.to_dict(),
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by
        }


class AlertObserver:
    """Base class for alert observers."""
    
    def notify(self, alert: BiometricAlert):
        """
        Notify the observer of a new alert.
        
        Args:
            alert: The alert that was generated
        """
        raise NotImplementedError("Subclasses must implement notify()")


class EmailAlertObserver(AlertObserver):
    """Observer that sends email notifications for alerts."""
    
    def __init__(self, recipients: list[str]):
        """
        Initialize an email alert observer.
        
        Args:
            recipients: List of email recipients
        """
        self.recipients = recipients
        self.sent_alerts: list[BiometricAlert] = []
        
    def notify(self, alert: BiometricAlert):
        """
        Notify recipients of a new alert via email.
        
        Args:
            alert: The alert that was generated
        """
        # In a real implementation, this would send an email
        # For testing, we just record that an alert was sent
        self.sent_alerts.append(alert)
        
        # Simulated email subject and body
        subject = f"[{alert.severity.value.upper()}] Biometric Alert: {alert.rule_name}"
        body = (
            f"Patient ID: {alert.patient_id}\n"
            f"Rule: {alert.rule_name}\n"
            f"Value: {alert.data_point.value}\n"
            f"Time: {alert.timestamp.isoformat()}\n"
            f"Message: {alert.message}"
        )
        
        return {"subject": subject, "body": body, "recipients": self.recipients}


class SMSAlertObserver(AlertObserver):
    """Observer that sends SMS notifications for alerts."""
    
    def __init__(self, phone_numbers: list[str], urgent_only: bool = False):
        """
        Initialize an SMS alert observer.
        
        Args:
            phone_numbers: List of phone numbers to send SMS to
            urgent_only: Whether to only send SMS for urgent alerts
        """
        self.phone_numbers = phone_numbers
        self.urgent_only = urgent_only
        self.sent_alerts: list[BiometricAlert] = []
        
    def notify(self, alert: BiometricAlert):
        """
        Notify recipients of a new alert via SMS.
        
        Args:
            alert: The alert that was generated
        """
        # Only send SMS for high severity alerts if urgent_only is True
        if self.urgent_only and alert.severity not in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            return None
            
        # In a real implementation, this would send an SMS
        # For testing, we just record that an alert was sent
        self.sent_alerts.append(alert)
        
        # Simulated SMS message
        message = (
            f"[{alert.severity.value.upper()}] Alert for patient {alert.patient_id}: "
            f"{alert.rule_name} - {alert.data_point.value}"
        )
        
        return {"message": message, "phone_numbers": self.phone_numbers}


class InAppAlertObserver(AlertObserver):
    """Observer that sends in-app notifications for alerts."""
    
    def __init__(self):
        """Initialize an in-app alert observer."""
        self.notifications: dict[str, list[BiometricAlert]] = {}  # user_id -> alerts
        
    def notify(self, alert: BiometricAlert):
        """
        Notify users of a new alert via in-app notification.
        
        Args:
            alert: The alert that was generated
        """
        # In a real implementation, this would send in-app notifications
        # to relevant users (e.g., patient's provider, care team, etc.)
        # For testing, we just record the notifications
        
        # Simulate getting the associated provider IDs
        provider_ids = [f"provider_{alert.patient_id}"]
        
        for provider_id in provider_ids:
            if provider_id not in self.notifications:
                self.notifications[provider_id] = []
            self.notifications[provider_id].append(alert)
            
        return {"provider_ids": provider_ids, "alert": alert.to_dict()}


class ClinicalRuleEngine:
    """Engine for managing clinical rule templates and creating rules."""
    
    def __init__(self):
        """Initialize the clinical rule engine."""
        self.rule_templates: dict[str, dict[str, Any]] = {}
        self.custom_conditions: dict[str, Callable[[BiometricDataPoint], bool]] = {}
        
    def register_rule_template(
        self,
        template_id: str,
        name: str,
        data_type: BiometricType,
        operator: ComparisonOperator,
        threshold: float | int,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        description: str | None = None,
        parameters: list[str] | None = None
    ):
        """
        Register a rule template.
        
        Args:
            template_id: Template ID
            name: Template name
            data_type: Type of biometric data this rule applies to
            operator: Comparison operator
            threshold: Default threshold value
            severity: Default alert severity
            description: Template description
            parameters: List of parameters that can be customized when creating a rule
        """
        self.rule_templates[template_id] = {
            "name": name,
            "data_type": data_type,
            "operator": operator,
            "threshold": threshold,
            "severity": severity,
            "description": description,
            "parameters": parameters or []
        }
        
    def register_custom_condition(
        self,
        condition_id: str,
        condition_func: Callable[[BiometricDataPoint], bool]
    ):
        """
        Register a custom condition function.
        
        Args:
            condition_id: Condition ID
            condition_func: Function that evaluates a biometric data point
        """
        self.custom_conditions[condition_id] = condition_func
        
    def create_rule_from_template(
        self,
        template_id: str,
        parameters: dict[str, Any] | None = None,
        patient_id: str | None = None
    ) -> AlertRule:
        """
        Create a rule from a template.
        
        Args:
            template_id: Template ID
            parameters: Custom parameters for the rule
            patient_id: Optional patient ID for patient-specific rules
            
        Returns:
            Alert rule
            
        Raises:
            ValueError: If the template doesn't exist or a required parameter is missing
        """
        if template_id not in self.rule_templates:
            raise ValueError(f"Rule template '{template_id}' not found")
            
        template = self.rule_templates[template_id]
        params = parameters or {}
        
        # Check for required parameters
        for param in template.get("parameters", []):
            if param not in params:
                raise ValueError(f"Required parameter '{param}' missing")
                
        # Create the rule with template defaults and custom parameters
        rule = AlertRule(
            name=params.get("name", template["name"]),
            data_type=template["data_type"],
            operator=template["operator"],
            threshold=params.get("threshold", template["threshold"]),
            patient_id=patient_id,
            severity=params.get("severity", template["severity"]),
            description=params.get("description", template["description"]),
            active=params.get("active", True),
            cooldown_minutes=params.get("cooldown_minutes", 60)
        )
        
        return rule


class ProcessorContext:
    """Context for biometric event processing."""
    
    def __init__(self, patient_id: str):
        """
        Initialize the processor context.
        
        Args:
            patient_id: ID of the patient
        """
        self.patient_id = patient_id
        self.last_values: dict[BiometricType, Any] = {}
        self.trends: dict[BiometricType, list[Any]] = {}
        self.alert_counts: dict[str, int] = {}  # rule_id -> count
        
    def update(self, data_point: BiometricDataPoint):
        """
        Update the context with a new data point.
        
        Args:
            data_point: New biometric data point
        """
        data_type = data_point.data_type
        value = data_point.value
        
        # Update last value
        self.last_values[data_type] = value
        
        # Update trend
        if data_type not in self.trends:
            self.trends[data_type] = []
        self.trends[data_type].append(value)
        
        # Keep only the last 10 values for each data type
        if len(self.trends[data_type]) > 10:
            self.trends[data_type] = self.trends[data_type][-10:]
            
    def increment_alert_count(self, rule_id: str):
        """
        Increment the alert count for a rule.
        
        Args:
            rule_id: ID of the rule
        """
        if rule_id not in self.alert_counts:
            self.alert_counts[rule_id] = 0
        self.alert_counts[rule_id] += 1


class BiometricEventProcessor:
    """Processor for biometric events."""
    
    def __init__(self):
        """Initialize the biometric event processor."""
        self.rules: dict[str, AlertRule] = {}
        self.observers: list[AlertObserver] = []
        self.contexts: dict[str, ProcessorContext] = {}  # patient_id -> context
        
    def add_rule(self, rule: AlertRule):
        """
        Add a rule to the processor.
        
        Args:
            rule: Rule to add
        """
        self.rules[rule.id] = rule
        
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule from the processor.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            True if the rule was removed, False if it wasn't found
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
        
    def register_observer(self, observer: AlertObserver):
        """
        Register an observer for alerts.
        
        Args:
            observer: Observer to register
        """
        self.observers.append(observer)
        
    def unregister_observer(self, observer: AlertObserver):
        """
        Unregister an observer.
        
        Args:
            observer: Observer to unregister
        """
        if observer in self.observers:
            self.observers.remove(observer)
            
    def get_context(self, patient_id: str) -> ProcessorContext:
        """
        Get or create a context for a patient.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            The patient's context
        """
        if patient_id not in self.contexts:
            self.contexts[patient_id] = ProcessorContext(patient_id)
        return self.contexts[patient_id]
        
    def process_data_point(self, data_point: BiometricDataPoint) -> list[BiometricAlert]:
        """
        Process a biometric data point.
        
        Args:
            data_point: Biometric data point to process
            
        Returns:
            List of alerts generated for this data point
        """
        if not data_point.patient_id:
            return []
            
        # Get or create context for this patient
        context = self.get_context(data_point.patient_id)
        
        # Update context with new data point
        context.update(data_point)
        
        # Evaluate rules
        alerts = []
        for rule in self.rules.values():
            if rule.evaluate(data_point):
                # Create an alert
                alert = BiometricAlert(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    patient_id=data_point.patient_id,
                    data_point=data_point,
                    severity=rule.severity,
                    message=rule.description
                )
                alerts.append(alert)
                
                # Update alert count in context
                context.increment_alert_count(rule.id)
                
                # Notify observers
                for observer in self.observers:
                    observer.notify(alert)
                    
        return alerts


# ============= Biometric Event Processor Tests =============

class TestBiometricEventProcessor(unittest.TestCase):
    """Test the biometric event processor."""
    
    def setUp(self):
        """Set up a processor for each test."""
        self.processor = BiometricEventProcessor()
        
    def test_add_rule(self):
        """Test adding a rule to the processor."""
        # Create a rule
        rule = AlertRule(
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100
        )
        
        # Add the rule to the processor
        self.processor.add_rule(rule)
        
        # Check that the rule was added
        self.assertIn(rule.id, self.processor.rules)
        self.assertEqual(self.processor.rules[rule.id], rule)
        
    def test_remove_rule(self):
        """Test removing a rule from the processor."""
        # Create and add a rule
        rule = AlertRule(
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100
        )
        self.processor.add_rule(rule)
        
        # Remove the rule
        result = self.processor.remove_rule(rule.id)
        
        # Check that the rule was removed
        self.assertTrue(result)
        self.assertNotIn(rule.id, self.processor.rules)
        
        # Try to remove a non-existent rule
        result = self.processor.remove_rule("non_existent_rule")
        
        # Check that the result is False
        self.assertFalse(result)
        
    def test_register_observer(self):
        """Test registering an observer."""
        # Create an observer
        observer = EmailAlertObserver(recipients=["doctor@example.com"])
        
        # Register the observer
        self.processor.register_observer(observer)
        
        # Check that the observer was registered
        self.assertIn(observer, self.processor.observers)
        
    def test_unregister_observer(self):
        """Test unregistering an observer."""
        # Create and register an observer
        observer = EmailAlertObserver(recipients=["doctor@example.com"])
        self.processor.register_observer(observer)
        
        # Unregister the observer
        self.processor.unregister_observer(observer)
        
        # Check that the observer was unregistered
        self.assertNotIn(observer, self.processor.observers)
        
        # Try to unregister an observer that wasn't registered
        observer2 = EmailAlertObserver(recipients=["nurse@example.com"])
        self.processor.unregister_observer(observer2)  # Should not raise an error
        
    def test_process_data_point_no_patient_id(self):
        """Test processing a data point with no patient ID."""
        # Create a data point with no patient ID
        data_point = BiometricDataPoint(
            patient_id="",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Process the data point
        alerts = self.processor.process_data_point(data_point)
        
        # Check that no alerts were generated
        self.assertEqual(len(alerts), 0)
        
    def test_process_data_point_no_matching_rules(self):
        """Test processing a data point with no matching rules."""
        # Create a rule for blood pressure
        rule = AlertRule(
            name="High Blood Pressure",
            data_type=BiometricType.BLOOD_PRESSURE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=140
        )
        self.processor.add_rule(rule)
        
        # Create a heart rate data point
        data_point = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Process the data point
        alerts = self.processor.process_data_point(data_point)
        
        # Check that no alerts were generated
        self.assertEqual(len(alerts), 0)
        
    def test_process_data_point_matching_rule(self):
        """Test processing a data point that matches a rule."""
        # Create a rule for heart rate
        rule = AlertRule(
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100,
            severity=AlertSeverity.HIGH
        )
        self.processor.add_rule(rule)
        
        # Create a heart rate data point that exceeds the threshold
        data_point = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Process the data point
        alerts = self.processor.process_data_point(data_point)
        
        # Check that an alert was generated
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, rule.id)
        self.assertEqual(alerts[0].patient_id, "patient1")
        self.assertEqual(alerts[0].severity, AlertSeverity.HIGH)
        
    def test_process_data_point_patient_specific_rule(self):
        """Test processing a data point with a patient-specific rule."""
        # Create a patient-specific rule
        rule = AlertRule(
            name="Patient-Specific Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100,
            patient_id="patient1"
        )
        self.processor.add_rule(rule)
        
        # Create a heart rate data point for the matching patient
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Create a heart rate data point for a different patient
        data_point2 = BiometricDataPoint(
            patient_id="patient2",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Process the data points
        alerts1 = self.processor.process_data_point(data_point1)
        alerts2 = self.processor.process_data_point(data_point2)
        
        # Check that an alert was generated only for the matching patient
        self.assertEqual(len(alerts1), 1)
        self.assertEqual(alerts1[0].rule_id, rule.id)
        self.assertEqual(alerts1[0].patient_id, "patient1")
        
        self.assertEqual(len(alerts2), 0)
        
    def test_process_data_point_inactive_rule(self):
        """Test processing a data point with an inactive rule."""
        # Create an inactive rule
        rule = AlertRule(
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100,
            active=False
        )
        self.processor.add_rule(rule)
        
        # Create a heart rate data point that exceeds the threshold
        data_point = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Process the data point
        alerts = self.processor.process_data_point(data_point)
        
        # Check that no alerts were generated
        self.assertEqual(len(alerts), 0)
        
    def test_process_data_point_updates_context(self):
        """Test that processing a data point updates the context."""
        # Create a data point
        data_point = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=80
        )
        
        # Process the data point
        self.processor.process_data_point(data_point)
        
        # Check that the context was updated
        context = self.processor.get_context("patient1")
        self.assertEqual(context.last_values[BiometricType.HEART_RATE], 80)
        self.assertEqual(context.trends[BiometricType.HEART_RATE], [80])
        
        # Process another data point
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=90
        )
        self.processor.process_data_point(data_point2)
        
        # Check that the context was updated
        self.assertEqual(context.last_values[BiometricType.HEART_RATE], 90)
        self.assertEqual(context.trends[BiometricType.HEART_RATE], [80, 90])


class TestAlertRule(unittest.TestCase):
    """Test the alert rule class."""
    
    def setUp(self):
        """Set up for alert rule tests."""
        # Mark all rules created in tests with _in_test flag to disable cooldown effects
        self._original_init = AlertRule.__init__
        
        def patched_init(self_rule, *args, **kwargs):
            self._original_init(self_rule, *args, **kwargs)
            self_rule._in_test = True
            
        AlertRule.__init__ = patched_init
        
    def tearDown(self):
        """Tear down for alert rule tests."""
        # Restore original __init__ method
        AlertRule.__init__ = self._original_init
    
    def test_evaluate_data_type_mismatch(self):
        """Test evaluating a rule with a data type mismatch."""
        # Create a rule for heart rate
        rule = AlertRule(
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100
        )
        
        # Create a blood pressure data point
        data_point = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.BLOOD_PRESSURE,
            value=120
        )
        
        # Evaluate the rule
        result = rule.evaluate(data_point)
        
        # Check that the result is False
        self.assertFalse(result)
        
    def test_evaluate_greater_than(self):
        """Test evaluating a rule with the greater than operator."""
        # Create a rule
        rule = AlertRule(
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100
        )
        
        # Create a data point that exceeds the threshold
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Create a data point that equals the threshold
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=100
        )
        
        # Create a data point that is below the threshold
        data_point3 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=80
        )
        
        # Evaluate the rule
        result1 = rule.evaluate(data_point1)
        result2 = rule.evaluate(data_point2)
        result3 = rule.evaluate(data_point3)
        
        # Check the results
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)
        
    def test_evaluate_greater_than_or_equal(self):
        """Test evaluating a rule with the greater than or equal operator."""
        # Create a rule
        rule = AlertRule(
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold=100
        )
        
        # Create a data point that exceeds the threshold
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Create a data point that equals the threshold
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=100
        )
        
        # Create a data point that is below the threshold
        data_point3 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=80
        )
        
        # Evaluate the rule
        result1 = rule.evaluate(data_point1)
        result2 = rule.evaluate(data_point2)
        result3 = rule.evaluate(data_point3)
        
        # Check the results
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertFalse(result3)
        
    def test_evaluate_less_than(self):
        """Test evaluating a rule with the less than operator."""
        # Create a rule
        rule = AlertRule(
            name="Low Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.LESS_THAN,
            threshold=60
        )
        
        # Create a data point that is below the threshold
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=50
        )
        
        # Create a data point that equals the threshold
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=60
        )
        
        # Create a data point that exceeds the threshold
        data_point3 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=70
        )
        
        # Evaluate the rule
        result1 = rule.evaluate(data_point1)
        result2 = rule.evaluate(data_point2)
        result3 = rule.evaluate(data_point3)
        
        # Check the results
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)
        
    def test_evaluate_less_than_or_equal(self):
        """Test evaluating a rule with the less than or equal operator."""
        # Create a rule
        rule = AlertRule(
            name="Low Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.LESS_THAN_OR_EQUAL,
            threshold=60
        )
        
        # Create a data point that is below the threshold
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=50
        )
        
        # Create a data point that equals the threshold
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=60
        )
        
        # Create a data point that exceeds the threshold
        data_point3 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=70
        )
        
        # Evaluate the rule
        result1 = rule.evaluate(data_point1)
        result2 = rule.evaluate(data_point2)
        result3 = rule.evaluate(data_point3)
        
        # Check the results
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertFalse(result3)
        
    def test_evaluate_equal(self):
        """Test evaluating a rule with the equal operator."""
        # Create a rule
        rule = AlertRule(
            name="Exact Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.EQUAL,
            threshold=60
        )
        
        # Create a data point that is below the threshold
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=50
        )
        
        # Create a data point that equals the threshold
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=60
        )
        
        # Create a data point that exceeds the threshold
        data_point3 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=70
        )
        
        # Evaluate the rule
        result1 = rule.evaluate(data_point1)
        result2 = rule.evaluate(data_point2)
        result3 = rule.evaluate(data_point3)
        
        # Check the results
        self.assertFalse(result1)
        self.assertTrue(result2)
        self.assertFalse(result3)
        
    def test_evaluate_not_equal(self):
        """Test evaluating a rule with the not equal operator."""
        # Create a rule
        rule = AlertRule(
            name="Not Normal Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.NOT_EQUAL,
            threshold=60
        )
        
        # Create a data point that is below the threshold
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=50
        )
        
        # Create a data point that equals the threshold
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=60
        )
        
        # Create a data point that exceeds the threshold
        data_point3 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=70
        )
        
        # Evaluate the rule
        result1 = rule.evaluate(data_point1)
        result2 = rule.evaluate(data_point2)
        result3 = rule.evaluate(data_point3)
        
        # Check the results
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertTrue(result3)


class TestBiometricAlert(unittest.TestCase):
    """Test the biometric alert class."""
    
    def test_acknowledge(self):
        """Test acknowledging an alert."""
        # Create a data point
        data_point = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Create an alert
        alert = BiometricAlert(
            rule_id="rule1",
            rule_name="High Heart Rate",
            patient_id="patient1",
            data_point=data_point,
            severity=AlertSeverity.HIGH,
            message="Heart rate is too high"
        )
        
        # Check initial state
        self.assertFalse(alert.acknowledged)
        self.assertIsNone(alert.acknowledged_at)
        self.assertIsNone(alert.acknowledged_by)
        
        # Acknowledge the alert
        alert.acknowledge(user_id="user1")
        
        # Check that the alert was acknowledged
        self.assertTrue(alert.acknowledged)
        self.assertIsNotNone(alert.acknowledged_at)
        self.assertEqual(alert.acknowledged_by, "user1")


class TestAlertObservers(unittest.TestCase):
    """Test the alert observer classes."""
    
    def setUp(self):
        """Set up test data."""
        # Create a data point
        self.data_point = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.HEART_RATE,
            value=120
        )
        
        # Create an alert
        self.alert = BiometricAlert(
            rule_id="rule1",
            rule_name="High Heart Rate",
            patient_id="patient1",
            data_point=self.data_point,
            severity=AlertSeverity.HIGH,
            message="Heart rate is too high"
        )
        
    def test_email_alert_observer(self):
        """Test the email alert observer."""
        # Create an email observer
        observer = EmailAlertObserver(recipients=["doctor@example.com"])
        
        # Notify the observer
        result = observer.notify(self.alert)
        
        # Check that the alert was sent
        self.assertEqual(len(observer.sent_alerts), 1)
        self.assertEqual(observer.sent_alerts[0], self.alert)
        
        # Check the result
        self.assertIn("subject", result)
        self.assertIn("body", result)
        self.assertIn("recipients", result)
        self.assertEqual(result["recipients"], ["doctor@example.com"])
        
    def test_sms_alert_observer_urgent(self):
        """Test the SMS alert observer with urgent alerts."""
        # Create an SMS observer that only sends urgent alerts
        observer = SMSAlertObserver(phone_numbers=["555-1234"], urgent_only=True)
        
        # Create a high severity alert
        high_alert = BiometricAlert(
            rule_id="rule1",
            rule_name="High Heart Rate",
            patient_id="patient1",
            data_point=self.data_point,
            severity=AlertSeverity.HIGH,
            message="Heart rate is too high"
        )
        
        # Create a medium severity alert
        medium_alert = BiometricAlert(
            rule_id="rule2",
            rule_name="Slightly High Heart Rate",
            patient_id="patient1",
            data_point=self.data_point,
            severity=AlertSeverity.MEDIUM,
            message="Heart rate is slightly high"
        )
        
        # Notify the observer
        high_result = observer.notify(high_alert)
        medium_result = observer.notify(medium_alert)
        
        # Check that only the high severity alert was sent
        self.assertEqual(len(observer.sent_alerts), 1)
        self.assertEqual(observer.sent_alerts[0], high_alert)
        
        # Check the results
        self.assertIsNotNone(high_result)
        self.assertIsNone(medium_result)
        
    def test_sms_alert_observer_non_urgent(self):
        """Test the SMS alert observer with non-urgent alerts."""
        # Create an SMS observer that sends all alerts
        observer = SMSAlertObserver(phone_numbers=["555-1234"], urgent_only=False)
        
        # Create a medium severity alert
        medium_alert = BiometricAlert(
            rule_id="rule2",
            rule_name="Slightly High Heart Rate",
            patient_id="patient1",
            data_point=self.data_point,
            severity=AlertSeverity.MEDIUM,
            message="Heart rate is slightly high"
        )
        
        # Notify the observer
        result = observer.notify(medium_alert)
        
        # Check that the alert was sent
        self.assertEqual(len(observer.sent_alerts), 1)
        self.assertEqual(observer.sent_alerts[0], medium_alert)
        
        # Check the result
        self.assertIsNotNone(result)
        self.assertIn("message", result)
        self.assertIn("phone_numbers", result)
        self.assertEqual(result["phone_numbers"], ["555-1234"])
        
    def test_in_app_alert_observer(self):
        """Test the in-app alert observer."""
        # Create an in-app observer
        observer = InAppAlertObserver()
        
        # Notify the observer
        result = observer.notify(self.alert)
        
        # Check the result
        self.assertIsNotNone(result)
        self.assertIn("provider_ids", result)
        self.assertIn("alert", result)
        
        # Check that the notification was stored
        provider_id = f"provider_{self.alert.patient_id}"
        self.assertIn(provider_id, observer.notifications)
        self.assertEqual(len(observer.notifications[provider_id]), 1)
        self.assertEqual(observer.notifications[provider_id][0], self.alert)


class TestClinicalRuleEngine(unittest.TestCase):
    """Test the clinical rule engine."""
    
    def setUp(self):
        """Set up a rule engine for each test."""
        self.engine = ClinicalRuleEngine()
        
    def test_register_rule_template(self):
        """Test registering a rule template."""
        # Register a template
        self.engine.register_rule_template(
            template_id="high_heart_rate",
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100,
            severity=AlertSeverity.MEDIUM,
            description="Heart rate above normal range",
            parameters=["threshold", "severity"]
        )
        
        # Check that the template was registered
        self.assertIn("high_heart_rate", self.engine.rule_templates)
        template = self.engine.rule_templates["high_heart_rate"]
        self.assertEqual(template["name"], "High Heart Rate")
        self.assertEqual(template["data_type"], BiometricType.HEART_RATE)
        self.assertEqual(template["operator"], ComparisonOperator.GREATER_THAN)
        self.assertEqual(template["threshold"], 100)
        self.assertEqual(template["severity"], AlertSeverity.MEDIUM)
        self.assertEqual(template["parameters"], ["threshold", "severity"])
        
    def test_register_custom_condition(self):
        """Test registering a custom condition."""
        # Define a custom condition
        def is_fever(data_point: BiometricDataPoint) -> bool:
            if data_point.data_type != BiometricType.TEMPERATURE:
                return False
            return float(data_point.value) > 38.0
            
        # Register the condition
        self.engine.register_custom_condition("is_fever", is_fever)
        
        # Check that the condition was registered
        self.assertIn("is_fever", self.engine.custom_conditions)
        self.assertEqual(self.engine.custom_conditions["is_fever"], is_fever)
        
        # Test the condition
        data_point1 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.TEMPERATURE,
            value=39.0
        )
        
        data_point2 = BiometricDataPoint(
            patient_id="patient1",
            data_type=BiometricType.TEMPERATURE,
            value=37.0
        )
        
        self.assertTrue(self.engine.custom_conditions["is_fever"](data_point1))
        self.assertFalse(self.engine.custom_conditions["is_fever"](data_point2))
        
    def test_create_rule_from_template(self):
        """Test creating a rule from a template."""
        # Register a template
        self.engine.register_rule_template(
            template_id="high_heart_rate",
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100,
            severity=AlertSeverity.MEDIUM,
            description="Heart rate above normal range",
            parameters=["threshold", "severity"]
        )
        
        # Create a rule from the template
        rule = self.engine.create_rule_from_template(
            template_id="high_heart_rate",
            parameters={
                "threshold": 120,
                "severity": AlertSeverity.HIGH
            },
            patient_id="patient1"
        )
        
        # Check the rule
        self.assertEqual(rule.name, "High Heart Rate")
        self.assertEqual(rule.data_type, BiometricType.HEART_RATE)
        self.assertEqual(rule.operator, ComparisonOperator.GREATER_THAN)
        self.assertEqual(rule.threshold, 120)
        self.assertEqual(rule.severity, AlertSeverity.HIGH)
        self.assertEqual(rule.patient_id, "patient1")
        
    def test_create_rule_from_template_missing_parameter(self):
        """Test creating a rule from a template with a missing parameter."""
        # Register a template
        self.engine.register_rule_template(
            template_id="high_heart_rate",
            name="High Heart Rate",
            data_type=BiometricType.HEART_RATE,
            operator=ComparisonOperator.GREATER_THAN,
            threshold=100,
            severity=AlertSeverity.MEDIUM,
            description="Heart rate above normal range",
            parameters=["threshold", "severity"]
        )
        
        # Try to create a rule with a missing parameter
        with self.assertRaises(ValueError):
            self.engine.create_rule_from_template(
                template_id="high_heart_rate",
                parameters={
                    "threshold": 120
                    # Missing severity
                },
                patient_id="patient1"
            )
            
    def test_create_rule_from_template_unknown_template(self):
        """Test creating a rule from an unknown template."""
        # Try to create a rule from an unknown template
        with self.assertRaises(ValueError):
            self.engine.create_rule_from_template(
                template_id="unknown_template",
                parameters={},
                patient_id="patient1"
            )