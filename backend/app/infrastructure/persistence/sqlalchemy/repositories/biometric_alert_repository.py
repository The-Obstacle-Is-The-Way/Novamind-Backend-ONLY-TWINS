# -*- coding: utf-8 -*-
"""
SQLAlchemy implementation of the BiometricAlertRepository.

This module provides a concrete implementation of the BiometricAlertRepository
interface using SQLAlchemy ORM for database operations.
"""

from datetime import datetime, UTC
from app.domain.utils.datetime_utils import UTC
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.domain.services.biometric_event_processor import BiometricAlert, AlertPriority
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
            # Use alert_id which is string in the BiometricAlert class
            alert_model_id = str(alert.alert_id)
            existing_model = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.alert_id == alert_model_id
            ).first()
            
            if existing_model:
                self._update_model(existing_model, alert)
                alert_model = existing_model
            else:
                alert_model = self._map_to_model(alert)
                self.session.add(alert_model)
            
            self.session.commit()
            self.session.refresh(alert_model)
            
            # Return the updated entity
            return self._map_to_entity(alert_model)
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error saving biometric alert: {str(e)}") from e
    
    async def get_by_id(self, alert_id: UUID | str) -> Optional[BiometricAlert]:
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
        acknowledged: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BiometricAlert]:
        """
        Retrieve biometric alerts for a specific patient.
        
        Args:
            patient_id: ID of the patient
            acknowledged: Optional filter by acknowledged status
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
            query = select(BiometricAlertModel).where(
                BiometricAlertModel.patient_id == str(patient_id)
            )
            query = self._apply_filters(query, acknowledged, start_date, end_date)
            query = query.order_by(BiometricAlertModel.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await self.session.execute(query)
            alert_models = result.scalars().all()
            return [self._map_to_entity(model) for model in alert_models]
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error retrieving biometric alerts by patient: {str(e)}") from e
    
    async def get_unacknowledged_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        patient_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BiometricAlert]:
        """
        Retrieve active (non-resolved) biometric alerts.
        
        Args:
            priority: Optional filter by alert priority
            patient_id: Optional filter by patient ID
            limit: Maximum number of alerts to return
            offset: Number of alerts to skip for pagination
            
        Returns:
            List of active biometric alerts matching the criteria
            
        Raises:
            RepositoryError: If there's an error retrieving the alerts
        """
        try:
            # Build the query for unacknowledged alerts
            query = select(BiometricAlertModel).where(
                BiometricAlertModel.acknowledged == False
            )

            if patient_id:
                query = query.where(BiometricAlertModel.patient_id == str(patient_id))

            if priority:
                query = query.where(BiometricAlertModel.priority == priority.value)

            query = query.order_by(
                BiometricAlertModel.created_at.desc()
            )
            query = query.limit(limit).offset(offset)

            result = await self.session.execute(query)
            alert_models = result.scalars().all()

            return [self._map_to_entity(model) for model in alert_models]
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error retrieving active alerts: {str(e)}") from e
    
    async def delete(self, alert_id: UUID | str) -> bool:
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
            result = self.session.query(BiometricAlertModel).filter(
                BiometricAlertModel.alert_id == str(alert_id)
            ).delete()
            self.session.commit()
            return result > 0
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error deleting biometric alert: {str(e)}") from e
    
    async def count_by_patient(
        self,
        patient_id: UUID,
        acknowledged: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count biometric alerts for a specific patient.
        
        Args:
            patient_id: ID of the patient
            acknowledged: Optional filter by acknowledged status
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Number of alerts matching the criteria
            
        Raises:
            RepositoryError: If there's an error counting the alerts
        """
        try:
            query = select(func.count(BiometricAlertModel.alert_id)).where(
                BiometricAlertModel.patient_id == str(patient_id)
            )
            query = self._apply_filters_for_count(query, acknowledged, start_date, end_date)

            result = await self.session.execute(query)
            count = result.scalar_one_or_none()
            return count if count is not None else 0
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Error counting biometric alerts: {str(e)}") from e
    
    def _apply_filters(self, query, acknowledged, start_date, end_date):
        """
        Apply common filters to a query.
        
        Args:
            query: The SQLAlchemy query to filter
            acknowledged: Optional filter by acknowledged status
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            The filtered query
        """
        if acknowledged is not None:
            query = query.where(BiometricAlertModel.acknowledged == acknowledged)
        if start_date:
            query = query.where(BiometricAlertModel.created_at >= start_date)
        if end_date:
            query = query.where(BiometricAlertModel.created_at <= end_date)
        return query
    
    def _apply_filters_for_count(self, query, acknowledged, start_date, end_date):
        if acknowledged is not None:
            query = query.where(BiometricAlertModel.acknowledged == acknowledged)
        if start_date:
            query = query.where(BiometricAlertModel.created_at >= start_date)
        if end_date:
            query = query.where(BiometricAlertModel.created_at <= end_date)
        return query
    
    def _map_to_entity(self, model: BiometricAlertModel) -> BiometricAlert:
        """
        Map a BiometricAlertModel to a BiometricAlert entity.
        
        Args:
            model: The database model to map
            
        Returns:
            The corresponding domain entity
        """
        data_point_mock = MagicMock()
        return BiometricAlert(
            alert_id=str(model.alert_id),
            patient_id=UUID(model.patient_id),
            rule_id=model.rule_id,
            rule_name=model.rule_name,
            priority=AlertPriority(model.priority),
            data_point=data_point_mock,
            message=model.message,
            context=model.context,
            created_at=model.created_at,
            acknowledged=model.acknowledged,
            acknowledged_at=model.acknowledged_at,
            acknowledged_by=UUID(model.acknowledged_by) if model.acknowledged_by else None
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
            rule_id=entity.rule_id,
            rule_name=entity.rule_name,
            priority=entity.priority.value,
            message=entity.message,
            context=entity.context,
            created_at=entity.created_at,
            acknowledged=entity.acknowledged,
            acknowledged_at=entity.acknowledged_at,
            acknowledged_by=str(entity.acknowledged_by) if entity.acknowledged_by else None
        )
    
    def _update_model(self, model: BiometricAlertModel, entity: BiometricAlert) -> None:
        """
        Update a BiometricAlertModel with values from a BiometricAlert entity.
        
        Args:
            model: The database model to update
            entity: The domain entity with updated values
        """
        model.patient_id = str(entity.patient_id)
        model.rule_id = entity.rule_id
        model.rule_name = entity.rule_name
        model.priority = entity.priority.value
        model.message = entity.message
        model.context = entity.context
        if entity.acknowledged:
            model.acknowledged = entity.acknowledged
            model.acknowledged_at = entity.acknowledged_at
            model.acknowledged_by = str(entity.acknowledged_by) if entity.acknowledged_by else None