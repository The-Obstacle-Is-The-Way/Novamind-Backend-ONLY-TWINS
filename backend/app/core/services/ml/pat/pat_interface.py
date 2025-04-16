# -*- coding: utf-8 -*-
"""
PAT (Pretrained Actigraphy Transformer) Service Interface.

This module provides the interface for PAT services.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from app.core.services.ml.interface import MLService


class PATInterface(MLService):
    """
    Interface for Pretrained Actigraphy Transformer (PAT) services.
    
    This interface defines the contract that PAT implementations must follow.
    """
    
    @abstractmethod
    def analyze_actigraphy(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
        device_info: Dict[str, str],
        analysis_types: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze actigraphy data using the PAT model.
        
        Args:
            patient_id: Patient identifier
            readings: Accelerometer readings with timestamp and x,y,z values
            start_time: Start time of recording (ISO 8601 format)
            end_time: End time of recording (ISO 8601 format)
            sampling_rate_hz: Sampling rate in Hz
            device_info: Information about the device used
            analysis_types: Types of analysis to perform (e.g., "sleep", "activity", "mood")
            **kwargs: Additional parameters
            
        Returns:
            Dict containing analysis results and metadata
        """
        pass
    
    @abstractmethod
    def get_sleep_metrics(
        self,
        patient_id: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get sleep metrics for a patient over a specified time period.
        
        Args:
            patient_id: Patient identifier
            start_date: Start date (ISO 8601 format)
            end_date: End date (ISO 8601 format)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing sleep metrics
        """
        pass
    
    @abstractmethod
    def get_activity_metrics(
        self,
        patient_id: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get activity metrics for a patient over a specified time period.
        
        Args:
            patient_id: Patient identifier
            start_date: Start date (ISO 8601 format)
            end_date: End date (ISO 8601 format)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing activity metrics
        """
        pass
    
    @abstractmethod
    def detect_anomalies(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        baseline_period: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Detect anomalies in actigraphy data compared to baseline or population norms.
        
        Args:
            patient_id: Patient identifier
            readings: Accelerometer readings with timestamp and x,y,z values
            baseline_period: Optional period to use as baseline (start_date, end_date)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing detected anomalies
        """
        pass
    
    @abstractmethod
    def predict_mood_state(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        historical_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Predict mood state based on actigraphy patterns.
        
        Args:
            patient_id: Patient identifier
            readings: Accelerometer readings with timestamp and x,y,z values
            historical_context: Optional historical context for the patient
            **kwargs: Additional parameters
            
        Returns:
            Dict containing mood state predictions
        """
        pass
    
    @abstractmethod
    def integrate_with_digital_twin(
        self,
        patient_id: str,
        profile_id: str,
        actigraphy_analysis: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Integrate actigraphy analysis with digital twin profile.
        
        Args:
            patient_id: Patient identifier
            profile_id: Digital twin profile identifier
            actigraphy_analysis: Results from actigraphy analysis
            **kwargs: Additional parameters
            
        Returns:
            Dict containing integrated digital twin profile
        """
        pass
