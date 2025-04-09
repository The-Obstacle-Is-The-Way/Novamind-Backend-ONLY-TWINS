"""
PAT (Pretrained Actigraphy Transformer) Service Interface.
Domain interface for the physiological and behavioral data analysis component of the Trinity Stack.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any
from uuid import UUID

from backend.app.domain.entities.refactored.digital_twin_core import (
    ClinicalInsight, TemporalPattern, ClinicalSignificance
)


class PATService(ABC):
    """
    Abstract interface for PAT (Pretrained Actigraphy Transformer) operations.
    PAT is the behavioral and physiological data analysis component of the Trinity Stack,
    specializing in actigraphy, sleep patterns, and behavioral rhythms analysis.
    """
    
    @abstractmethod
    async def analyze_actigraphy_data(
        self,
        actigraphy_data: Dict[str, Any],
        reference_id: Optional[UUID] = None,
        analysis_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze raw actigraphy data to extract features and patterns.
        
        Args:
            actigraphy_data: Raw actigraphy data
            reference_id: Optional reference ID for tracing
            analysis_parameters: Optional parameters for the analysis
            
        Returns:
            Analysis results including activity metrics and features
        """
        pass
    
    @abstractmethod
    async def analyze_sleep_patterns(
        self,
        sleep_data: Dict[str, Any],
        time_window: Optional[Tuple[datetime, datetime]] = None,
        reference_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Analyze sleep data to identify patterns and disturbances.
        
        Args:
            sleep_data: Sleep monitoring data
            time_window: Optional time window for analysis
            reference_id: Optional reference ID for tracing
            
        Returns:
            Sleep analysis results including patterns and quality metrics
        """
        pass
    
    @abstractmethod
    async def detect_circadian_rhythms(
        self,
        physiological_data: Dict[str, Any],
        data_types: Optional[List[str]] = None,
        minimum_days: int = 7,
        reference_id: Optional[UUID] = None
    ) -> List[TemporalPattern]:
        """
        Detect circadian rhythms from physiological data.
        
        Args:
            physiological_data: Physiological time series data
            data_types: Optional types of data to include in analysis
            minimum_days: Minimum days of data required
            reference_id: Optional reference ID for tracing
            
        Returns:
            List of detected temporal patterns
        """
        pass
    
    @abstractmethod
    async def correlate_behavior_with_symptoms(
        self,
        behavioral_data: Dict[str, Any],
        symptom_data: Dict[str, Any],
        lag_window: Optional[int] = None,  # hours
        reference_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Correlate behavioral patterns with symptom intensity.
        
        Args:
            behavioral_data: Behavioral time series data
            symptom_data: Symptom intensity data
            lag_window: Optional maximum lag to consider in hours
            reference_id: Optional reference ID for tracing
            
        Returns:
            Correlation results including lag analysis
        """
        pass
    
    @abstractmethod
    async def generate_behavioral_insights(
        self,
        behavioral_data: Dict[str, Any],
        physiological_data: Optional[Dict[str, Any]] = None,
        digital_twin_state_id: Optional[UUID] = None,
        reference_id: Optional[UUID] = None
    ) -> List[ClinicalInsight]:
        """
        Generate clinical insights from behavioral and physiological data.
        
        Args:
            behavioral_data: Behavioral data
            physiological_data: Optional physiological data
            digital_twin_state_id: Optional Digital Twin state ID
            reference_id: Optional reference ID for tracing
            
        Returns:
            List of clinical insights
        """
        pass
    
    @abstractmethod
    async def detect_activity_anomalies(
        self,
        activity_data: Dict[str, Any],
        baseline_period: Optional[Tuple[datetime, datetime]] = None,
        sensitivity: float = 0.8,
        reference_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in activity patterns compared to baseline.
        
        Args:
            activity_data: Activity time series data
            baseline_period: Optional period to use as baseline
            sensitivity: Detection sensitivity (0.0 to 1.0)
            reference_id: Optional reference ID for tracing
            
        Returns:
            List of detected anomalies with timestamps and scores
        """
        pass
    
    @abstractmethod
    async def analyze_social_rhythms(
        self,
        social_data: Dict[str, Any],
        reference_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Analyze social interaction patterns and rhythms.
        
        Args:
            social_data: Social interaction data
            reference_id: Optional reference ID for tracing
            
        Returns:
            Analysis of social rhythms and interaction patterns
        """
        pass
    
    @abstractmethod
    async def predict_behavioral_triggers(
        self,
        behavioral_history: Dict[str, Any],
        symptom_history: Dict[str, Any],
        prediction_window: int = 48,  # hours
        reference_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Predict behavioral triggers for symptom exacerbation.
        
        Args:
            behavioral_history: Historical behavioral data
            symptom_history: Historical symptom data
            prediction_window: Window for prediction in hours
            reference_id: Optional reference ID for tracing
            
        Returns:
            Predicted triggers with confidence scores
        """
        pass
    
    @abstractmethod
    async def integrate_with_digital_twin(
        self,
        analysis_results: Dict[str, Any],
        reference_id: UUID,
        digital_twin_state_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Integrate analysis results with the Digital Twin.
        
        Args:
            analysis_results: Results from PAT analysis
            reference_id: UUID reference identifier
            digital_twin_state_id: Optional specific Digital Twin state ID
            
        Returns:
            Integration results including updates to Digital Twin
        """
        pass