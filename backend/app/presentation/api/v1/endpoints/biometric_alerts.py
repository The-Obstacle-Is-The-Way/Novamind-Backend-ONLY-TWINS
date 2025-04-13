# -*- coding: utf-8 -*-
"""
FastAPI endpoints for biometric alerts.

This module defines the API endpoints for managing biometric alerts,
including creating and managing alert rules, viewing alerts, and
acknowledging alerts.
"""

from datetime import datetime, , UTC
from app.domain.utils.datetime_utils import UTC
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordBearer

from app.domain.exceptions import ValidationError
from app.domain.services.biometric_event_processor import (
    AlertPriority,
    AlertRule,
    BiometricAlert,
    BiometricEventProcessor,
    ClinicalRuleEngine
)
from app.infrastructure.security.jwt_service import JWTService
from app.presentation.api.v1.endpoints.biometric_endpoints import get_current_user_id, get_patient_id
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

# Create router
router = APIRouter(
    prefix="/biometric-alerts",
    tags=["biometric-alerts"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
    }
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependency to get the BiometricEventProcessor
def get_biometric_event_processor() -> BiometricEventProcessor:
    """Get the BiometricEventProcessor instance."""
    processor = BiometricEventProcessor()
    return processor


# Dependency to get the ClinicalRuleEngine
def get_clinical_rule_engine() -> ClinicalRuleEngine:
    """Get the ClinicalRuleEngine instance."""
    engine = ClinicalRuleEngine()
    
    # Register common rule templates
    templates = [
        ("high_heart_rate", {
            "name": "High Heart Rate",
            "description": "Alert when heart rate exceeds a threshold",
            "required_parameters": ["threshold"],
            "condition_template": {
                "data_type": "heart_rate",
                "operator": ">",
                "threshold": "$threshold"
            }
        }),
        ("low_heart_rate", {
            "name": "Low Heart Rate",
            "description": "Alert when heart rate falls below a threshold",
            "required_parameters": ["threshold"],
            "condition_template": {
                "data_type": "heart_rate",
                "operator": "<",
                "threshold": "$threshold"
            }
        }),
        ("high_blood_pressure", {
            "name": "High Blood Pressure",
            "description": "Alert when systolic blood pressure exceeds a threshold",
            "required_parameters": ["systolic_threshold"],
            "condition_template": {
                "data_type": "blood_pressure_systolic",
                "operator": ">",
                "threshold": "$systolic_threshold"
            }
        }),
        ("low_sleep_duration", {
            "name": "Low Sleep Duration",
            "description": "Alert when sleep duration falls below a threshold",
            "required_parameters": ["threshold_hours"],
            "condition_template": {
                "data_type": "sleep_duration",
                "operator": "<",
                "threshold": "$threshold_hours"
            }
        })
    ]
    
    for template_id, template in templates:
        engine.register_rule_template(template_id, template)
    
    return engine


# Dependency to get the alert repository
def get_alert_repository():
    """Get the alert repository."""
    from app.infrastructure.persistence.sqlalchemy.repositories.biometric_alert_repository import (
        SQLAlchemyBiometricAlertRepository
    )
    from app.infrastructure.persistence.sqlalchemy.config.database import get_db
    session = next(get_db())
    return SQLAlchemyBiometricAlertRepository(session=session)


# Dependency to get the rule repository
def get_rule_repository():
    """Get the rule repository."""
    from app.infrastructure.persistence.sqlalchemy.repositories.alert_rule_repository import (
        SQLAlchemyAlertRuleRepository
    )
    from app.infrastructure.persistence.sqlalchemy.config.database import get_db
    session = next(get_db())
    return SQLAlchemyAlertRuleRepository(session=session)


@router.get(
    "/rules",
    response_model=AlertRuleListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get alert rules",
    description="Get a list of alert rules with optional filtering."
)
async def get_alert_rules(
    current_user_id: UUID = Depends(get_current_user_id),
    rule_repository = Depends(get_rule_repository),
    patient_id: Optional[UUID] = Query(None, description="Filter rules by patient ID"),
    priority: Optional[str] = Query(None, description="Filter rules by priority"),
    is_active: Optional[bool] = Query(None, description="Filter rules by active status")
):
    """Get a list of alert rules with optional filtering."""
    try:
        # Convert priority string to enum if provided
        priority_enum = None
        if priority:
            try:
                priority_enum = AlertPriority(priority.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority: {priority}"
                )
        
        # Get rules from repository
        rules = await rule_repository.get_rules(
            patient_id=patient_id,
            priority=priority_enum,
            is_active=is_active
        )
        
        # Convert to response models
        rule_responses = [
            AlertRuleResponse(
                rule_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                priority=rule.priority.value,
                condition=rule.condition,
                created_by=rule.created_by,
                patient_id=rule.patient_id,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
                is_active=rule.is_active
            )
            for rule in rules
        ]
        
        return AlertRuleListResponse(
            rules=rule_responses,
            count=len(rule_responses)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert rule",
    description="Create a new alert rule."
)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    rule_repository = Depends(get_rule_repository),
    clinical_rule_engine: ClinicalRuleEngine = Depends(get_clinical_rule_engine),
    biometric_event_processor: BiometricEventProcessor = Depends(get_biometric_event_processor)
):
    """Create a new alert rule."""
    try:
        # Convert priority string to enum
        try:
            priority = AlertPriority(rule_data.priority.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {rule_data.priority}"
            )
        
        # Create the rule
        if rule_data.template_id:
            # Create from template
            try:
                rule = clinical_rule_engine.create_rule_from_template(
                    template_id=rule_data.template_id,
                    rule_id=rule_data.rule_id,
                    name=rule_data.name,
                    description=rule_data.description,
                    priority=priority,
                    parameters=rule_data.parameters,
                    created_by=current_user_id,
                    patient_id=rule_data.patient_id
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        else:
            # Create from condition
            if not rule_data.condition:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either template_id or condition must be provided"
                )
            
            rule = AlertRule(
                rule_id=rule_data.rule_id,
                name=rule_data.name,
                description=rule_data.description,
                priority=priority,
                condition=rule_data.condition,
                created_by=current_user_id,
                patient_id=rule_data.patient_id
            )
        
        # Save the rule
        await rule_repository.create_rule(rule)
        
        # Add the rule to the processor
        biometric_event_processor.add_rule(rule)
        
        # Convert to response model
        return AlertRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            priority=rule.priority.value,
            condition=rule.condition,
            created_by=rule.created_by,
            patient_id=rule.patient_id,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            is_active=rule.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/rules/{rule_id}",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get alert rule",
    description="Get a specific alert rule by ID."
)
async def get_alert_rule(
    rule_id: str = Path(..., description="ID of the rule to get"),
    current_user_id: UUID = Depends(get_current_user_id),
    rule_repository = Depends(get_rule_repository)
):
    """Get a specific alert rule by ID."""
    try:
        # Get the rule
        rule = await rule_repository.get_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID {rule_id} not found"
            )
        
        # Convert to response model
        return AlertRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            priority=rule.priority.value,
            condition=rule.condition,
            created_by=rule.created_by,
            patient_id=rule.patient_id,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            is_active=rule.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put(
    "/rules/{rule_id}",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update alert rule",
    description="Update a specific alert rule by ID."
)
async def update_alert_rule(
    rule_data: AlertRuleUpdate,
    rule_id: str = Path(..., description="ID of the rule to update"),
    current_user_id: UUID = Depends(get_current_user_id),
    rule_repository = Depends(get_rule_repository),
    biometric_event_processor: BiometricEventProcessor = Depends(get_biometric_event_processor)
):
    """Update a specific alert rule by ID."""
    try:
        # Get the existing rule
        rule = await rule_repository.get_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID {rule_id} not found"
            )
        
        # Update the rule
        if rule_data.name is not None:
            rule.name = rule_data.name
        
        if rule_data.description is not None:
            rule.description = rule_data.description
        
        if rule_data.priority is not None:
            try:
                rule.priority = AlertPriority(rule_data.priority.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority: {rule_data.priority}"
                )
        
        if rule_data.condition is not None:
            rule.condition = rule_data.condition
        
        if rule_data.is_active is not None:
            rule.is_active = rule_data.is_active
        
        rule.updated_at = datetime.now(UTC)
        
        # Save the updated rule
        await rule_repository.update_rule(rule)
        
        # Update the rule in the processor
        biometric_event_processor.add_rule(rule)
        
        # Convert to response model
        return AlertRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            priority=rule.priority.value,
            condition=rule.condition,
            created_by=rule.created_by,
            patient_id=rule.patient_id,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            is_active=rule.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert rule",
    description="Delete a specific alert rule by ID."
)
async def delete_alert_rule(
    rule_id: str = Path(..., description="ID of the rule to delete"),
    current_user_id: UUID = Depends(get_current_user_id),
    rule_repository = Depends(get_rule_repository),
    biometric_event_processor: BiometricEventProcessor = Depends(get_biometric_event_processor)
):
    """Delete a specific alert rule by ID."""
    try:
        # Get the existing rule
        rule = await rule_repository.get_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID {rule_id} not found"
            )
        
        # Delete the rule
        await rule_repository.delete_rule(rule_id)
        
        # Remove the rule from the processor
        biometric_event_processor.remove_rule(rule_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/rule-templates",
    response_model=AlertRuleTemplateListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get rule templates",
    description="Get a list of available rule templates."
)
async def get_rule_templates(
    current_user_id: UUID = Depends(get_current_user_id),
    clinical_rule_engine: ClinicalRuleEngine = Depends(get_clinical_rule_engine)
):
    """Get a list of available rule templates."""
    try:
        # Get templates from the engine
        templates = []
        for template_id, template in clinical_rule_engine.rule_templates.items():
            templates.append(
                AlertRuleTemplateResponse(
                    template_id=template_id,
                    name=template.get("name", ""),
                    description=template.get("description", ""),
                    required_parameters=template.get("required_parameters", []),
                    condition_template=template.get("condition_template", {})
                )
            )
        
        return AlertRuleTemplateListResponse(
            templates=templates,
            count=len(templates)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/alerts",
    response_model=BiometricAlertListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get alerts",
    description="Get a list of biometric alerts with optional filtering."
)
async def get_alerts(
    current_user_id: UUID = Depends(get_current_user_id),
    alert_repository = Depends(get_alert_repository),
    patient_id: Optional[UUID] = Query(None, description="Filter alerts by patient ID"),
    priority: Optional[str] = Query(None, description="Filter alerts by priority"),
    acknowledged: Optional[bool] = Query(None, description="Filter alerts by acknowledgement status"),
    start_time: Optional[datetime] = Query(None, description="Start of time range"),
    end_time: Optional[datetime] = Query(None, description="End of time range")
):
    """Get a list of biometric alerts with optional filtering."""
    try:
        # Convert priority string to enum if provided
        priority_enum = None
        if priority:
            try:
                priority_enum = AlertPriority(priority.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority: {priority}"
                )
        
        # Get alerts from repository
        alerts = await alert_repository.get_alerts(
            patient_id=patient_id,
            priority=priority_enum,
            acknowledged=acknowledged,
            start_time=start_time,
            end_time=end_time
        )
        
        # Convert to response models
        alert_responses = [
            BiometricAlertResponse(
                alert_id=alert.alert_id,
                patient_id=alert.patient_id,
                rule_id=alert.rule_id,
                rule_name=alert.rule_name,
                priority=alert.priority.value,
                message=alert.message,
                created_at=alert.created_at,
                acknowledged=alert.acknowledged,
                acknowledged_at=alert.acknowledged_at,
                acknowledged_by=alert.acknowledged_by,
                data_point={
                    "data_id": str(alert.data_point.data_id),
                    "data_type": alert.data_point.data_type,
                    "value": alert.data_point.value,
                    "timestamp": alert.data_point.timestamp,
                    "source": alert.data_point.source
                }
            )
            for alert in alerts
        ]
        
        return BiometricAlertListResponse(
            alerts=alert_responses,
            count=len(alert_responses)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=BiometricAlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge alert",
    description="Acknowledge a specific biometric alert by ID."
)
async def acknowledge_alert(
    request: AlertAcknowledgementRequest,
    alert_id: str = Path(..., description="ID of the alert to acknowledge"),
    current_user_id: UUID = Depends(get_current_user_id),
    alert_repository = Depends(get_alert_repository)
):
    """Acknowledge a specific biometric alert by ID."""
    try:
        # Get the alert
        alert = await alert_repository.get_alert_by_id(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found"
            )
        
        # Acknowledge the alert
        alert.acknowledge(current_user_id)
        
        # Save the updated alert
        await alert_repository.update_alert(alert)
        
        # Convert to response model
        return BiometricAlertResponse(
            alert_id=alert.alert_id,
            patient_id=alert.patient_id,
            rule_id=alert.rule_id,
            rule_name=alert.rule_name,
            priority=alert.priority.value,
            message=alert.message,
            created_at=alert.created_at,
            acknowledged=alert.acknowledged,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            data_point={
                "data_id": str(alert.data_point.data_id),
                "data_type": alert.data_point.data_type,
                "value": alert.data_point.value,
                "timestamp": alert.data_point.timestamp,
                "source": alert.data_point.source
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/patients/{patient_id}/alerts",
    response_model=BiometricAlertListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient alerts",
    description="Get a list of biometric alerts for a specific patient."
)
async def get_patient_alerts(
    patient_id: UUID = Depends(get_patient_id),
    current_user_id: UUID = Depends(get_current_user_id),
    alert_repository = Depends(get_alert_repository),
    priority: Optional[str] = Query(None, description="Filter alerts by priority"),
    acknowledged: Optional[bool] = Query(None, description="Filter alerts by acknowledgement status"),
    start_time: Optional[datetime] = Query(None, description="Start of time range"),
    end_time: Optional[datetime] = Query(None, description="End of time range")
):
    """Get a list of biometric alerts for a specific patient."""
    return await get_alerts(
        current_user_id=current_user_id,
        alert_repository=alert_repository,
        patient_id=patient_id,
        priority=priority,
        acknowledged=acknowledged,
        start_time=start_time,
        end_time=end_time
    )
