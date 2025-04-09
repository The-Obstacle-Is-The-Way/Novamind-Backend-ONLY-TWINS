"""
Base interface for the Patient Activity Tracking (PAT) service.

This module defines the abstract base class that all PAT implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PATBase(ABC):
    """Abstract base class for all PAT service implementations."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the service with configuration parameters.
        
        Args:
            config: Configuration parameters
        """
        pass
    
    @abstractmethod
    def analyze_actigraphy(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
        device_info: Dict[str, Any],
        analysis_types: List[str],
    ) -> Dict[str, Any]:
        """Analyze actigraphy data to extract insights.
        
        Args:
            patient_id: Unique patient identifier
            readings: List of actigraphy readings, each with timestamp and x,y,z values
            start_time: ISO-8601 timestamp for start of data collection
            end_time: ISO-8601 timestamp for end of data collection
            sampling_rate_hz: Data sampling rate in Hz
            device_info: Information about the recording device
            analysis_types: List of analysis types to perform
            
        Returns:
            A dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    def get_actigraphy_embeddings(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
    ) -> Dict[str, Any]:
        """Generate embeddings from actigraphy data for similarity comparison.
        
        Args:
            patient_id: Unique patient identifier
            readings: List of actigraphy readings, each with timestamp and x,y,z values
            start_time: ISO-8601 timestamp for start of data collection
            end_time: ISO-8601 timestamp for end of data collection
            sampling_rate_hz: Data sampling rate in Hz
            
        Returns:
            A dictionary containing embedding vector and metadata
        """
        pass
    
    @abstractmethod
    def get_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
        """Retrieve an analysis by its ID.
        
        Args:
            analysis_id: The ID of the analysis to retrieve
            
        Returns:
            The analysis record
        """
        pass
    
    @abstractmethod
    def get_patient_analyses(
        self, patient_id: str, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """Retrieve analyses for a patient.
        
        Args:
            patient_id: The patient's ID
            limit: Maximum number of analyses to return
            offset: Starting index for pagination
            
        Returns:
            Dictionary with analyses and pagination metadata
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the underlying model.
        
        Returns:
            Dictionary with model information
        """
        pass
    
    @abstractmethod
    def integrate_with_digital_twin(
        self, patient_id: str, profile_id: str, analysis_id: str
    ) -> Dict[str, Any]:
        """Integrate actigraphy analysis with a digital twin profile.
        
        Args:
            patient_id: Patient ID
            profile_id: Digital twin profile ID
            analysis_id: Analysis ID to integrate
            
        Returns:
            Dictionary with integration results
        """
        pass