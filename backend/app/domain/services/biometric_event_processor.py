"""
Biometric Event Processor for real-time biometric alerts.

This module implements the Observer pattern to process biometric data streams
and trigger clinical interventions when concerning patterns emerge.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID  # Corrected import

from app.domain.entities.biometric_twin import BiometricDataPoint
from app.domain.exceptions import ValidationError


class AlertPriority(Enum):
    """Priority levels for biometric alerts."""
    
    URGENT = "urgent"
    WARNING = "warning"
    INFORMATIONAL = "informational"


class AlertRule:
    """Rule for triggering biometric alerts."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        priority: AlertPriority,
        condition: dict[str, Any],
        created_by: UUID,
        patient_id: UUID | None = None
    ):
        """
        Initialize a new alert rule.
        
        Args:
            rule_id: Unique identifier for the rule
            name: Name of the rule
            description: Description of the rule
            priority: Priority level of alerts triggered by this rule
            condition: Condition that triggers the alert
            created_by: ID of the user who created the rule
            patient_id: Optional ID of the patient this rule applies to
        """
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.priority = priority
        self.condition = condition
        self.created_by = created_by
        self.patient_id = patient_id
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at
        self.is_active = True
    
    def evaluate(self, data_point: BiometricDataPoint, context: dict[str, Any]) -> bool:
        """
        Evaluate the rule against a biometric data point.
        
        Args:
            data_point: Biometric data point to evaluate
            context: Additional context for evaluation
            
        Returns:
            True if the rule condition is met, False otherwise
        """
        # Simple condition evaluation for demonstration
        # In a real implementation, this would use a rule engine
        
        # Check data type match
        if self.condition.get("data_type") != data_point.data_type:
            return False
        
        # Check threshold condition
        operator = self.condition.get("operator", "")
        threshold = self.condition.get("threshold", 0)
        
        if operator == ">":
            return data_point.value > threshold
        elif operator == ">=":
            return data_point.value >= threshold
        elif operator == "<":
            return data_point.value < threshold
        elif operator == "<=":
            return data_point.value <= threshold
        elif operator == "==":
            return data_point.value == threshold
        elif operator == "!=":
            return data_point.value != threshold
        
        # Complex conditions would be evaluated here
        return False


class BiometricAlert:
    """Alert generated from biometric data."""
    
    def __init__(
        self,
        alert_id: str,
        patient_id: UUID,
        rule_id: str,
        rule_name: str,
        priority: AlertPriority,
        data_point: BiometricDataPoint,
        message: str,
        context: dict[str, Any]
    ):
        """
        Initialize a new biometric alert.
        
        Args:
            alert_id: Unique identifier for the alert
            patient_id: ID of the patient
            rule_id: ID of the rule that triggered the alert
            rule_name: Name of the rule that triggered the alert
            priority: Priority level of the alert
            data_point: Biometric data point that triggered the alert
            message: Alert message
            context: Additional context for the alert
        """
        self.alert_id = alert_id
        self.patient_id = patient_id
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.priority = priority
        self.data_point = data_point
        self.message = message
        self.context = context
        self.created_at = datetime.now(UTC)
        self.acknowledged = False
        self.acknowledged_at = None
        self.acknowledged_by = None
    
    def acknowledge(self, user_id: UUID) -> None:
        """
        Acknowledge the alert.
        
        Args:
            user_id: ID of the user acknowledging the alert
        """
        self.acknowledged = True
        self.acknowledged_at = datetime.now(UTC)
        self.acknowledged_by = user_id


class AlertObserver:
    """Observer interface for biometric alerts."""
    
    def notify(self, alert: BiometricAlert) -> None:
        """
        Notify the observer of a new alert.
        
        Args:
            alert: The alert to notify about
        """
        raise NotImplementedError("Subclasses must implement notify()")


class EmailAlertObserver(AlertObserver):
    """Observer that sends email notifications for alerts."""
    
    def __init__(self, email_service: object):
        """
        Initialize a new email alert observer.
        
        Args:
            email_service: Service for sending emails
        """
        self.email_service = email_service
    
    def notify(self, alert: BiometricAlert) -> None:
        """
        Send an email notification for an alert.
        
        Args:
            alert: The alert to notify about
        """
        # In a real implementation, this would use the email service
        # to send a HIPAA-compliant email notification
        recipient = self._get_recipient_for_patient(alert.patient_id)
        subject = f"Biometric Alert: {alert.priority.value.capitalize()} - {alert.rule_name}"
        
        # Sanitize PHI from the message
        sanitized_message = self._sanitize_phi(alert.message)
        
        # Send the email
        # self.email_service.send_email(recipient, subject, sanitized_message)
        
        # Log notification with sanitized message
        print(f"Email notification sent to {recipient}: {subject} - {sanitized_message}")
    
    def _get_recipient_for_patient(self, patient_id: UUID) -> str:
        """
        Get the email recipient for a patient.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Email address of the recipient
        """
        # In a real implementation, this would look up the appropriate
        # clinical staff for the patient
        return "clinician@example.com"
    
    def _sanitize_phi(self, message: str) -> str:
        """
        Sanitize PHI from a message.
        
        Args:
            message: Message to sanitize
            
        Returns:
            Sanitized message
        """
        # In a real implementation, this would use a PHI sanitizer
        # to remove or redact PHI from the message
        return message


class SMSAlertObserver(AlertObserver):
    """Observer that sends SMS notifications for alerts."""
    
    def __init__(self, sms_service: object):
        """
        Initialize a new SMS alert observer.
        
        Args:
            sms_service: Service for sending SMS messages
        """
        self.sms_service = sms_service
    
    def notify(self, alert: BiometricAlert) -> None:
        """
        Send an SMS notification for an alert.
        
        Args:
            alert: The alert to notify about
        """
        # Only send SMS for urgent alerts
        if alert.priority != AlertPriority.URGENT:
            return
        
        # In a real implementation, this would use the SMS service
        # to send a HIPAA-compliant SMS notification
        recipient = self._get_recipient_for_patient(alert.patient_id)
        
        # Sanitize PHI from the message
        sanitized_message = self._sanitize_phi(alert.message)
        
        # Send the SMS
        # self.sms_service.send_sms(recipient, sanitized_message)
        
        print(f"SMS notification sent to {recipient}: {sanitized_message}")
    
    def _get_recipient_for_patient(self, patient_id: UUID) -> str:
        """
        Get the SMS recipient for a patient.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Phone number of the recipient
        """
        # In a real implementation, this would look up the appropriate
        # clinical staff for the patient
        return "+1234567890"
    
    def _sanitize_phi(self, message: str) -> str:
        """
        Sanitize PHI from a message.
        
        Args:
            message: Message to sanitize
            
        Returns:
            Sanitized message
        """
        # In a real implementation, this would use a PHI sanitizer
        # to remove or redact PHI from the message
        return message


class InAppAlertObserver(AlertObserver):
    """Observer that sends in-app notifications for alerts."""
    
    def __init__(self, notification_service: object):
        """
        Initialize a new in-app alert observer.
        
        Args:
            notification_service: Service for sending in-app notifications
        """
        self.notification_service = notification_service
    
    def notify(self, alert: BiometricAlert) -> None:
        """
        Send an in-app notification for an alert.
        
        Args:
            alert: The alert to notify about
        """
        # In a real implementation, this would use the notification service
        # to send an in-app notification
        recipients = self._get_recipients_for_patient(alert.patient_id)
        
        # Send the notification
        # for recipient in recipients:
        #     self.notification_service.send_notification(
        #         recipient,
        #         alert.priority.value,
        #         alert.message,
        #         {"alert_id": alert.alert_id}
        #     )
        
        print(f"In-app notification sent to {len(recipients)} recipients")
    
    def _get_recipients_for_patient(self, patient_id: UUID) -> list[UUID]:
        """
        Get the in-app notification recipients for a patient.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            List of user IDs to notify
        """
        # In a real implementation, this would look up the appropriate
        # clinical staff for the patient
        return [UUID("00000000-0000-0000-0000-000000000001")]


class BiometricEventProcessor:
    """
    Processor for biometric events that implements the Observer pattern.
    
    This class processes biometric data streams and triggers alerts
    when concerning patterns emerge.
    """
    
    def __init__(self):
        """Initialize a new biometric event processor."""
        self.rules: dict[str, AlertRule] = {}
        self.observers: dict[AlertPriority, list[AlertObserver]] = {
            AlertPriority.URGENT: [],
            AlertPriority.WARNING: [],
            AlertPriority.INFORMATIONAL: []
        }
        self.patient_context: dict[UUID, dict[str, Any]] = {}
    
    def add_rule(self, rule: AlertRule) -> None:
        """
        Add a new alert rule.
        
        Args:
            rule: Rule to add
        """
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str) -> None:
        """
        Remove an alert rule.
        
        Args:
            rule_id: ID of the rule to remove
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def register_observer(self, observer: AlertObserver, priorities: list[AlertPriority]) -> None:
        """
        Register an observer for alerts with specific priorities.
        
        Args:
            observer: Observer to register
            priorities: List of priorities to register for
        """
        for priority in priorities:
            if priority in self.observers:
                self.observers[priority].append(observer)
    
    def unregister_observer(self, observer: AlertObserver) -> None:
        """
        Unregister an observer from all priorities.
        
        Args:
            observer: Observer to unregister
        """
        for priority in self.observers:
            if observer in self.observers[priority]:
                self.observers[priority].remove(observer)
    
    def process_data_point(self, data_point: BiometricDataPoint) -> list[BiometricAlert]:
        """
        Process a biometric data point and generate alerts if needed.
        
        Args:
            data_point: Biometric data point to process
            
        Returns:
            List of alerts generated
        """
        if not data_point.patient_id:
            raise ValidationError("Data point must have a patient ID")
        
        # Get or create patient context
        context = self.patient_context.get(data_point.patient_id, {})
        
        # Update context with the new data point
        data_type = data_point.data_type
        if "latest_values" not in context:
            context["latest_values"] = {}
        context["latest_values"][data_type] = data_point.value
        
        # Store the updated context
        self.patient_context[data_point.patient_id] = context
        
        # Evaluate rules
        alerts = []
        for rule_id, rule in self.rules.items():
            # Skip rules that don't apply to this patient
            if rule.patient_id and rule.patient_id != data_point.patient_id:
                continue
            
            # Skip inactive rules
            if not rule.is_active:
                continue
            
            # Evaluate the rule
            if rule.evaluate(data_point, context):
                # Create an alert
                alert = BiometricAlert(
                    alert_id=f"{rule_id}-{datetime.now(UTC).isoformat()}",
                    patient_id=data_point.patient_id,
                    rule_id=rule_id,
                    rule_name=rule.name,
                    priority=rule.priority,
                    data_point=data_point,
                    message=self._generate_alert_message(rule, data_point),
                    context=context.copy()
                )
                
                # Add to the list of alerts
                alerts.append(alert)
                
                # Notify observers
                self._notify_observers(alert)
        
        return alerts
    
    def _generate_alert_message(self, rule: AlertRule, data_point: BiometricDataPoint) -> str:
        """
        Generate an alert message for a rule and data point.
        
        Args:
            rule: Rule that triggered the alert
            data_point: Data point that triggered the alert
            
        Returns:
            Alert message
        """
        # In a real implementation, this would generate a more detailed message
        timestamp = data_point.timestamp.isoformat()
        return f"{rule.name}: {data_point.data_type} value {data_point.value} at {timestamp}"
    
    def _notify_observers(self, alert: BiometricAlert) -> None:
        """
        Notify observers of an alert.
        
        Args:
            alert: Alert to notify about
        """
        # Notify observers for this priority
        for observer in self.observers[alert.priority]:
            observer.notify(alert)


class ClinicalRuleEngine:
    """
    Engine for evaluating clinical rules against biometric data.
    
    This class provides a flexible rule system for defining alert thresholds
    and evaluating complex conditions.
    """
    
    def __init__(self):
        """Initialize a new clinical rule engine."""
        self.rule_templates: dict[str, dict[str, Any]] = {}
        self.custom_conditions: dict[str, Callable] = {}
    
    def register_rule_template(self, template_id: str, template: dict[str, Any]) -> None:
        """
        Register a rule template.
        
        Args:
            template_id: ID of the template
            template: Template definition
        """
        self.rule_templates[template_id] = template
    
    def register_custom_condition(self, condition_id: str, condition_func: Callable) -> None:
        """
        Register a custom condition function.
        
        Args:
            condition_id: ID of the condition
            condition_func: Function that evaluates the condition
        """
        self.custom_conditions[condition_id] = condition_func
    
    def create_rule_from_template(
        self,
        template_id: str,
        rule_id: str,
        name: str,
        description: str,
        priority: AlertPriority,
        parameters: dict[str, Any],
        created_by: UUID,
        patient_id: UUID | None = None
    ) -> AlertRule:
        """
        Create a rule from a template.
        
        Args:
            template_id: ID of the template to use
            rule_id: ID for the new rule
            name: Name for the new rule
            description: Description for the new rule
            priority: Priority for the new rule
            parameters: Parameters to apply to the template
            created_by: ID of the user creating the rule
            patient_id: Optional ID of the patient this rule applies to
            
        Returns:
            The created rule
            
        Raises:
            ValidationError: If the template doesn't exist or parameters are invalid
        """
        if template_id not in self.rule_templates:
            raise ValidationError(f"Rule template '{template_id}' not found")
        
        template = self.rule_templates[template_id]
        
        # Validate parameters
        required_params = template.get("required_parameters", [])
        for param in required_params:
            if param not in parameters:
                raise ValidationError(f"Missing required parameter '{param}'")
        
        # Create the condition
        condition = self._create_condition_from_template(template, parameters)
        
        # Create the rule
        return AlertRule(
            rule_id=rule_id,
            name=name,
            description=description,
            priority=priority,
            condition=condition,
            created_by=created_by,
            patient_id=patient_id
        )
    
    def _create_condition_from_template(
        self,
        template: dict[str, Any],
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a condition from a template and parameters.
        
        Args:
            template: Template to use
            parameters: Parameters to apply
            
        Returns:
            The created condition
        """
        condition_template = template.get("condition_template", {})
        condition = {}
        
        # Apply parameters to the template
        for key, value in condition_template.items():
            if isinstance(value, str) and value.startswith("$"):
                param_name = value[1:]
                if param_name in parameters:
                    condition[key] = parameters[param_name]
                else:
                    condition[key] = value
            else:
                condition[key] = value
        
        return condition