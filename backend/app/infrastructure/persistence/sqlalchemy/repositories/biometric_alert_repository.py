# -*- coding: utf-8 -*-
"""
SQLAlchemy implementation of the BiometricAlertRepository.

This module provides a concrete implementation of the BiometricAlertRepository
interface using SQLAlchemy ORM for database operations.
"""

from datetime import datetime, UTC, UTC
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.domain.entities.digital_twin.biometric_alert import BiometricAlert, AlertStatus, AlertPriority
from app.domain.repositories.biometric_alert_repository import BiometricAlertRepository
from app.domain.exceptions import EntityNotFoundError, RepositoryError
from app.infrastructure.persistence.sqlalchemy.models.biometric_alert_model import BiometricAlertModel


class SQLAlchemyBiometricAlertRepository(BiometricAlertRepository):
    """
    SQLAlchemy implementation of the BiometricAlertRepository interface.
    
    This class provides concrete implementations of the repository methods
    using SQLAlchemy ORM for database operations.
    """
    
    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a SQLAlchemy session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    async def save(self, alert: BiometricAlert) -> BiometricAlert:
        """
        Save a biometric alert to the repository.
        
        Args:
            alert: The biometric alert to save
            
        Returns:
            The saved biometric alert with any updates (e.g., ID assignment)
            
        Raises:
            RepositoryError: If there's an error saving the alert
        """
        try:
            # Check if the alert already exists
            existing_model = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.alert_id == str(alert.alert_id)
            ).first()
            
            if existing_model:
                # Update existing alert
                self._update_model(existing_model, alert)
                alert_model = existing_model
            else:
                # Create new alert
                alert_model = self._map_to_model(alert)
                self.session.add(alert_model)
            
            # Commit changes
            self.session.commit()
            
            # Refresh the model to get any database-generated values
            self.session.refresh(alert_model)
            
            # Return the updated entity
            return self._map_to_entity(alert_model)
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error saving biometric alert: {str(e)}") from e
    
    async def get_by_id(self, alert_id: UUID) -> Optional[BiometricAlert]:
        """
        Retrieve a biometric alert by its ID.
        
        Args:
            alert_id: ID of the alert to retrieve
            
        Returns:
            The biometric alert if found, None otherwise
            
        Raises:
            RepositoryError: If there's an error retrieving the alert
        """
        try:
            alert_model = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.alert_id == str(alert_id)
            ).first()
            
            if not alert_model:
                return None
            
            return self._map_to_entity(alert_model)
        except Exception as e:
            raise RepositoryError(f"Error retrieving biometric alert: {str(e)}") from e
    
    async def get_by_patient_id(
        self,
        patient_id: UUID,
        status: Optional[AlertStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BiometricAlert]:
        """
        Retrieve biometric alerts for a specific patient.
        
        Args:
            patient_id: ID of the patient
            status: Optional filter by alert status
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of alerts to return
            offset: Number of alerts to skip for pagination
            
        Returns:
            List of biometric alerts matching the criteria
            
        Raises:
            RepositoryError: If there's an error retrieving the alerts
        """
        try:
            # Build the query
            query = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.patient_id == str(patient_id)
            )
            
            # Apply filters
            query = self._apply_filters(query, status, start_date, end_date)
            
            # Apply pagination and ordering
            query = query.order_by(BiometricAlertModel.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            # Execute the query
            alert_models = query.all()
            
            # Map to entities
            return [self._map_to_entity(model) for model in alert_models]
        except Exception as e:
            raise RepositoryError(f"Error retrieving biometric alerts: {str(e)}") from e
    
    async def get_active_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BiometricAlert]:
        """
        Retrieve active (non-resolved) biometric alerts.
        
        Args:
            priority: Optional filter by alert priority
            limit: Maximum number of alerts to return
            offset: Number of alerts to skip for pagination
            
        Returns:
            List of active biometric alerts matching the criteria
            
        Raises:
            RepositoryError: If there's an error retrieving the alerts
        """
        try:
            # Build the query for active alerts
            query = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.status.in_([
                    AlertStatus.NEW.value,
                    AlertStatus.ACKNOWLEDGED.value,
                    AlertStatus.IN_PROGRESS.value
                ])
            )
            
            # Apply priority filter if provided
            if priority:
                query = query.filter(BiometricAlertModel.priority == priority)
            
            # Apply pagination and ordering
            query = query.order_by(
                BiometricAlertModel.priority.desc(),  # Higher priority first
                BiometricAlertModel.created_at.desc()  # Newer alerts first
            )
            query = query.limit(limit).offset(offset)
            
            # Execute the query
            alert_models = query.all()
            
            # Map to entities
            return [self._map_to_entity(model) for model in alert_models]
        except Exception as e:
            raise RepositoryError(f"Error retrieving active alerts: {str(e)}") from e
    
    async def update_status(
        self,
        alert_id: UUID,
        status: AlertStatus,
        provider_id: UUID,
        notes: Optional[str] = None
    ) -> BiometricAlert:
        """
        Update the status of a biometric alert.
        
        Args:
            alert_id: ID of the alert to update
            status: New status for the alert
            provider_id: ID of the provider making the update
            notes: Optional notes about the status update
            
        Returns:
            The updated biometric alert
            
        Raises:
            EntityNotFoundError: If the alert doesn't exist
            RepositoryError: If there's an error updating the alert
        """
        try:
            # Get the alert
            alert_model = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.alert_id == str(alert_id)
            ).first()
            
            if not alert_model:
                raise EntityNotFoundError(f"Biometric alert with ID {alert_id} not found")
            
            # Map to entity
            alert = self._map_to_entity(alert_model)
            
            # Update the status based on the requested status
            if status == AlertStatus.ACKNOWLEDGED:
                alert.acknowledge(provider_id)
            elif status == AlertStatus.IN_PROGRESS:
                alert.mark_in_progress(provider_id)
            elif status == AlertStatus.RESOLVED:
                alert.resolve(provider_id, notes)
            elif status == AlertStatus.DISMISSED:
                alert.dismiss(provider_id, notes)
            else:
                # Just update the status
                alert.status = status
                alert.updated_at = datetime.now(UTC)
            
            # Save the updated alert
            return await self.save(alert)
        except EntityNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error updating alert status: {str(e)}") from e
    
    async def delete(self, alert_id: UUID) -> bool:
        """
        Delete a biometric alert from the repository.
        
        Args:
            alert_id: ID of the alert to delete
            
        Returns:
            True if the alert was deleted, False otherwise
            
        Raises:
            RepositoryError: If there's an error deleting the alert
        """
        try:
            # Delete the alert
            deleted = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.alert_id == str(alert_id)
            ).delete()
            
            self.session.commit()
            
            return deleted > 0
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error deleting biometric alert: {str(e)}") from e
    
    async def count_by_patient(
        self,
        patient_id: UUID,
        status: Optional[AlertStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count biometric alerts for a specific patient.
        
        Args:
            patient_id: ID of the patient
            status: Optional filter by alert status
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Number of alerts matching the criteria
            
        Raises:
            RepositoryError: If there's an error counting the alerts
        """
        try:
            # Build the query
            query = self.session.query(func.count(BiometricAlertModel.alert_id)).filter(
                BiometricAlertModel.patient_id == str(patient_id)
            )
            
            # Apply filters
            query = self._apply_filters(query, status, start_date, end_date)
            
            # Execute the query
            return query.scalar()
        except Exception as e:
            raise RepositoryError(f"Error counting biometric alerts: {str(e)}") from e
    
    def _apply_filters(self, query, status, start_date, end_date):
        """
        Apply common filters to a query.
        
        Args:
            query: The SQLAlchemy query to filter
            status: Optional filter by alert status
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            The filtered query
        """
        # Apply status filter if provided
        if status:
            query = query.filter(BiometricAlertModel.status == status)
        
        # Apply date range filters if provided
        if start_date:
            query = query.filter(BiometricAlertModel.created_at >= start_date)
        
        if end_date:
            query = query.filter(BiometricAlertModel.created_at <= end_date)
        
        return query
    
    def _map_to_entity(self, model: BiometricAlertModel) -> BiometricAlert:
        """
        Map a BiometricAlertModel to a BiometricAlert entity.
        
        Args:
            model: The database model to map
            
        Returns:
            The corresponding domain entity
        """
        return BiometricAlert(
            patient_id=UUID(model.patient_id),
            alert_type=model.alert_type,
            description=model.description,
            priority=model.priority,
            data_points=model.data_points,
            rule_id=UUID(model.rule_id),
            created_at=model.created_at,
            updated_at=model.updated_at,
            alert_id=UUID(model.alert_id),
            status=model.status,
            acknowledged_by=UUID(model.acknowledged_by) if model.acknowledged_by else None,
            acknowledged_at=model.acknowledged_at,
            resolved_by=UUID(model.resolved_by) if model.resolved_by else None,
            resolved_at=model.resolved_at,
            resolution_notes=model.resolution_notes,
            metadata=model.alert_metadata or {} # Renamed
        )
    
    def _map_to_model(self, entity: BiometricAlert) -> BiometricAlertModel:
        """
        Map a BiometricAlert entity to a BiometricAlertModel.
        
        Args:
            entity: The domain entity to map
            
        Returns:
            The corresponding database model
        """
        return BiometricAlertModel(
            alert_id=str(entity.alert_id),
            patient_id=str(entity.patient_id),
            alert_type=entity.alert_type,
            description=entity.description,
            priority=entity.priority,
            data_points=entity.data_points,
            rule_id=str(entity.rule_id),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            status=entity.status,
            acknowledged_by=str(entity.acknowledged_by) if entity.acknowledged_by else None,
            acknowledged_at=entity.acknowledged_at,
            resolved_by=str(entity.resolved_by) if entity.resolved_by else None,
            resolved_at=entity.resolved_at,
            resolution_notes=entity.resolution_notes,
            alert_metadata=entity.metadata # Renamed model attribute
        )
    
    def _update_model(self, model: BiometricAlertModel, entity: BiometricAlert) -> None:
        """
        Update a BiometricAlertModel with values from a BiometricAlert entity.
        
        Args:
            model: The database model to update
            entity: The domain entity with updated values
        """
        model.alert_type = entity.alert_type
        model.description = entity.description
        model.priority = entity.priority
        model.data_points = entity.data_points
        model.updated_at = entity.updated_at
        model.status = entity.status
        model.acknowledged_by = str(entity.acknowledged_by) if entity.acknowledged_by else None
        model.acknowledged_at = entity.acknowledged_at
        model.resolved_by = str(entity.resolved_by) if entity.resolved_by else None
        model.resolved_at = entity.resolved_at
        model.resolution_notes = entity.resolution_notes
        model.alert_metadata = entity.metadata # Renamed model attribute