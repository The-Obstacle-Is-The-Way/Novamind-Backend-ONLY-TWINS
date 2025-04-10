# -*- coding: utf-8 -*-
"""
BiometricAlertRepository interface.

This module defines the repository interface for BiometricAlert entities,
following the Repository pattern to abstract data access operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.entities.digital_twin.biometric_alert import BiometricAlert, AlertStatus, AlertPriority


class BiometricAlertRepository(ABC):
    """
    Repository interface for BiometricAlert entities.
    
    This abstract class defines the contract that any concrete repository
    implementation must follow for BiometricAlert data access operations.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass