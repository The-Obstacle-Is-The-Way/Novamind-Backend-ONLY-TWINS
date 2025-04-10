# -*- coding: utf-8 -*-
"""
Appointment Repository Interface

This module defines the interface for appointment repositories.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from app.domain.entities.appointment import Appointment, AppointmentStatus


class AppointmentRepository(ABC):
    """
    Interface for appointment repositories.
    
    This abstract class defines the contract that all appointment repositories
    must implement, ensuring consistent access to appointment data regardless
    of the underlying storage mechanism.
    """
    
    @abstractmethod
    def get_by_id(self, appointment_id: Union[UUID, str]) -> Optional[Appointment]:
        """
        Get an appointment by ID.
        
        Args:
            appointment_id: ID of the appointment
            
        Returns:
            Appointment if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_patient_id(
        self,
        patient_id: Union[UUID, str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """
        Get appointments for a patient.
        
        Args:
            patient_id: ID of the patient
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            status: Optional status for filtering
            
        Returns:
            List of appointments
        """
        pass
    
    @abstractmethod
    def get_by_provider_id(
        self,
        provider_id: Union[UUID, str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """
        Get appointments for a provider.
        
        Args:
            provider_id: ID of the provider
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            status: Optional status for filtering
            
        Returns:
            List of appointments
        """
        pass
    
    @abstractmethod
    def save(self, appointment: Appointment) -> Appointment:
        """
        Save an appointment.
        
        Args:
            appointment: Appointment to save
            
        Returns:
            Saved appointment
        """
        pass
    
    @abstractmethod
    def delete(self, appointment_id: Union[UUID, str]) -> bool:
        """
        Delete an appointment.
        
        Args:
            appointment_id: ID of the appointment to delete
            
        Returns:
            True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def get_upcoming_appointments(
        self,
        days: int = 7,
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """
        Get upcoming appointments.
        
        Args:
            days: Number of days to look ahead
            status: Optional status for filtering
            
        Returns:
            List of upcoming appointments
        """
        pass
    
    @abstractmethod
    def get_appointments_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_id: Optional[Union[UUID, str]] = None,
        patient_id: Optional[Union[UUID, str]] = None,
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """
        Get appointments within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            provider_id: Optional provider ID for filtering
            patient_id: Optional patient ID for filtering
            status: Optional status for filtering
            
        Returns:
            List of appointments
        """
        pass
    
    @abstractmethod
    def get_appointments_needing_reminder(self) -> List[Appointment]:
        """
        Get appointments that need reminders.
        
        Returns:
            List of appointments needing reminders
        """
        pass
