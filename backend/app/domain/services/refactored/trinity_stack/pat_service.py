"""
PAT (Pretrained Actigraphy Transformer) Service Interface.
Domain interface for the physiological and behavioral data analysis component of the Trinity Stack.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.app.domain.entities.refactored.digital_twin_core import (
    ClinicalInsight,
    TemporalPattern,
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
        actigraphy_data: dict[str, Any],
        reference_id: UUID | None = None,
        analysis_parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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
        sleep_data: dict[str, Any],
        time_window: tuple[datetime, datetime] | None = None,
        reference_id: UUID | None = None
    ) -> dict[str, Any]:
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
        physiological_data: dict[str, Any],
        data_types: list[str] | None = None,
        minimum_days: int = 7,
        reference_id: UUID | None = None
    ) -> list[TemporalPattern]:
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
        behavioral_data: dict[str, Any],
        symptom_data: dict[str, Any],
        lag_window: int | None = None,  # hours
        reference_id: UUID | None = None
    ) -> dict[str, Any]:
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
        behavioral_data: dict[str, Any],
        physiological_data: dict[str, Any] | None = None,
        digital_twin_state_id: UUID | None = None,
        reference_id: UUID | None = None
    ) -> list[ClinicalInsight]:
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
        activity_data: dict[str, Any],
        baseline_period: tuple[datetime, datetime] | None = None,
        sensitivity: float = 0.8,
        reference_id: UUID | None = None
    ) -> list[dict[str, Any]]:
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
        social_data: dict[str, Any],
        reference_id: UUID | None = None
    ) -> dict[str, Any]:
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
        behavioral_history: dict[str, Any],
        symptom_history: dict[str, Any],
        prediction_window: int = 48,  # hours
        reference_id: UUID | None = None
    ) -> dict[str, Any]:
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
        analysis_results: dict[str, Any],
        reference_id: UUID,
        digital_twin_state_id: UUID | None = None
    ) -> dict[str, Any]:
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