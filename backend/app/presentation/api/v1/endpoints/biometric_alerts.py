# -*- coding: utf-8 -*-
"""
FastAPI router for biometric alert endpoints.

This module provides API endpoints for managing biometric alerts,
including creating, retrieving, and updating alerts.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.domain.services.biometric_event_processor import BiometricAlert, AlertStatus, AlertPriority
from app.domain.exceptions import EntityNotFoundError, RepositoryError
from app.domain.repositories.biometric_alert_repository import BiometricAlertRepository
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_session # Corrected import
from app.infrastructure.persistence.sqlalchemy.repositories.biometric_alert_repository import SQLAlchemyBiometricAlertRepository
from app.presentation.api.dependencies.auth import get_current_user, verify_provider_access
from app.presentation.api.schemas.biometric_alert import (
    AlertListResponseSchema,
    AlertStatusUpdateSchema,
    BiometricAlertCreateSchema,
    BiometricAlertResponseSchema,
    AlertPriorityEnum,
    AlertStatusEnum
)
from app.presentation.api.schemas.user import UserResponseSchema
from app.infrastructure.cache.redis_cache import RedisCache # Import directly
from app.presentation.api.dependencies import get_cache_service, get_alert_repository
from app.infrastructure.di.container import get_service


router = APIRouter(
    prefix="/biometric-alerts",
    tags=["biometric-alerts"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"}
    }
)


def get_alert_repository(db: Session = Depends(get_db_session)) -> BiometricAlertRepository: # Corrected dependency function name
    """
    Dependency for getting the biometric alert repository.
    
    Args:
        db: Database session
        
    Returns:
        BiometricAlertRepository instance
    """
    return SQLAlchemyBiometricAlertRepository(db)


@router.post(
    "/",
    response_model=BiometricAlertResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new biometric alert",
    description="Create a new biometric alert for a patient based on biometric data analysis."
)
async def create_alert(
    alert_data: BiometricAlertCreateSchema,
    repository: BiometricAlertRepository = Depends(get_alert_repository),
    current_user: UserResponseSchema = Depends(get_current_user) # Changed to get_current_user
) -> BiometricAlertResponseSchema:
    """
    Create a new biometric alert.
    
    Args:
        alert_data: Data for creating the alert
        repository: Repository for storing the alert
        current_user: Current authenticated provider
        
    Returns:
        The created biometric alert
        
    Raises:
        HTTPException: If there's an error creating the alert
    """
    try:
        # Create the alert entity
        alert = BiometricAlert(
            patient_id=alert_data.patient_id,
            alert_type=alert_data.alert_type,
            description=alert_data.description,
            priority=AlertPriority(alert_data.priority.value),
            data_points=alert_data.data_points,
            rule_id=alert_data.rule_id,
            metadata=alert_data.metadata
        )
        
        # Save the alert
        created_alert = await repository.save(alert)
        
        return created_alert
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating biometric alert: {str(e)}"
        )


@router.get(
    "/patient/{patient_id}",
    response_model=AlertListResponseSchema,
    summary="Get alerts for a patient",
    description="Retrieve biometric alerts for a specific patient with optional filtering."
)
async def get_patient_alerts(
    patient_id: UUID = Path(..., description="ID of the patient"),
    status: Optional[AlertStatusEnum] = Query(None, description="Filter by alert status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    repository: BiometricAlertRepository = Depends(get_alert_repository),
    current_user: UserResponseSchema = Depends(get_current_user)
) -> AlertListResponseSchema:
    """
    Get biometric alerts for a specific patient.
    
    Args:
        patient_id: ID of the patient
        status: Optional filter by alert status
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        page: Page number for pagination
        page_size: Number of items per page
        repository: Repository for retrieving alerts
        current_user: Current authenticated user
        
    Returns:
        Paginated list of biometric alerts
        
    Raises:
        HTTPException: If there's an error retrieving the alerts
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Convert status enum to domain enum if provided
        alert_status = AlertStatus(status.value) if status else None
        
        # Get alerts for the patient
        alerts = await repository.get_by_patient_id(
            patient_id=patient_id,
            status=alert_status,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset
        )
        
        # Get total count for pagination
        total = await repository.count_by_patient(
            patient_id=patient_id,
            status=alert_status,
            start_date=start_date,
            end_date=end_date
        )
        
        return AlertListResponseSchema(
            items=alerts,
            total=total,
            page=page,
            page_size=page_size
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving biometric alerts: {str(e)}"
        )


@router.get(
    "/active",
    response_model=AlertListResponseSchema,
    summary="Get active alerts",
    description="Retrieve active (non-resolved) biometric alerts with optional filtering by priority."
)
async def get_active_alerts(
    priority: Optional[AlertPriorityEnum] = Query(None, description="Filter by alert priority"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    repository: BiometricAlertRepository = Depends(get_alert_repository),
    current_user: UserResponseSchema = Depends(get_current_user) # Changed to get_current_user
) -> AlertListResponseSchema:
    """
    Get active (non-resolved) biometric alerts.
    
    Args:
        priority: Optional filter by alert priority
        page: Page number for pagination
        page_size: Number of items per page
        repository: Repository for retrieving alerts
        current_user: Current authenticated provider
        
    Returns:
        Paginated list of active biometric alerts
        
    Raises:
        HTTPException: If there's an error retrieving the alerts
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Convert priority enum to domain enum if provided
        alert_priority = AlertPriority(priority.value) if priority else None
        
        # Get active alerts
        alerts = await repository.get_active_alerts(
            priority=alert_priority,
            limit=page_size,
            offset=offset
        )
        
        # For simplicity, we'll use the length of the returned alerts as the total count
        # In a real implementation, you might want to add a count_active_alerts method to the repository
        total = len(alerts)
        
        return AlertListResponseSchema(
            items=alerts,
            total=total,
            page=page,
            page_size=page_size
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving active alerts: {str(e)}"
        )


@router.get(
    "/{alert_id}",
    response_model=BiometricAlertResponseSchema,
    summary="Get alert by ID",
    description="Retrieve a specific biometric alert by its ID."
)
async def get_alert(
    alert_id: UUID = Path(..., description="ID of the alert"),
    repository: BiometricAlertRepository = Depends(get_alert_repository),
    current_user: UserResponseSchema = Depends(get_current_user)
) -> BiometricAlertResponseSchema:
    """
    Get a specific biometric alert by its ID.
    
    Args:
        alert_id: ID of the alert
        repository: Repository for retrieving the alert
        current_user: Current authenticated user
        
    Returns:
        The biometric alert
        
    Raises:
        HTTPException: If the alert doesn't exist or there's an error retrieving it
    """
    try:
        alert = await repository.get_by_id(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Biometric alert with ID {alert_id} not found"
            )
        
        return alert
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving biometric alert: {str(e)}"
        )


@router.patch(
    "/{alert_id}/status",
    response_model=BiometricAlertResponseSchema,
    summary="Update alert status",
    description="Update the status of a biometric alert (acknowledge, mark in progress, resolve, or dismiss)."
)
async def update_alert_status(
    alert_id: UUID = Path(..., description="ID of the alert"),
    status_update: AlertStatusUpdateSchema = None,
    repository: BiometricAlertRepository = Depends(get_alert_repository),
    current_user: UserResponseSchema = Depends(get_current_user) # Changed to get_current_user
) -> BiometricAlertResponseSchema:
    """
    Update the status of a biometric alert.
    
    Args:
        alert_id: ID of the alert
        status_update: New status and optional notes
        repository: Repository for updating the alert
        current_user: Current authenticated provider
        
    Returns:
        The updated biometric alert
        
    Raises:
        HTTPException: If the alert doesn't exist or there's an error updating it
    """
    try:
        # Convert status enum to domain enum
        alert_status = AlertStatus(status_update.status.value)
        
        # Update the alert status
        updated_alert = await repository.update_status(
            alert_id=alert_id,
            status=alert_status,
            provider_id=current_user.id,
            notes=status_update.notes
        )
        
        return updated_alert
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Biometric alert with ID {alert_id} not found"
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating biometric alert status: {str(e)}"
        )


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert",
    description="Delete a biometric alert (admin only)."
)
async def delete_alert(
    alert_id: UUID = Path(..., description="ID of the alert"),
    repository: BiometricAlertRepository = Depends(get_alert_repository),
    current_user: UserResponseSchema = Depends(get_current_user) # Changed to get_current_user
) -> None:
    """
    Delete a biometric alert.
    
    Args:
        alert_id: ID of the alert
        repository: Repository for deleting the alert
        current_user: Current authenticated provider
        
    Raises:
        HTTPException: If the alert doesn't exist or there's an error deleting it
    """
    try:
        # Check if the alert exists
        alert = await repository.get_by_id(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Biometric alert with ID {alert_id} not found"
            )
        
        # Delete the alert
        deleted = await repository.delete(alert_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete biometric alert with ID {alert_id}"
            )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting biometric alert: {str(e)}"
        )