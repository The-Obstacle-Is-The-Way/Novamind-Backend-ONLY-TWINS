"""
Neurotransmitter effect models for the Temporal Neurotransmitter System.

This module defines the data structures for representing neurotransmitter effects
and their clinical significance.
"""
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
import uuid
from uuid import UUID

from app.domain.entities.digital_twin_enums import Neurotransmitter, BrainRegion, ClinicalSignificance


class NeurotransmitterEffect:
    """
    Model for representing the effects of a neurotransmitter on a brain region.
    
    This class captures statistical and clinical measures of neurotransmitter effects,
    including effect size, confidence intervals, statistical significance, and
    potential clinical implications.
    """

    def __init__(
        self,
        neurotransmitter: Neurotransmitter,
        effect_size: float,
        p_value: float,
        confidence_interval: Tuple[float, float],
        clinical_significance: Optional[ClinicalSignificance] = None,
        is_statistically_significant: bool = False,
        brain_region: Optional[BrainRegion] = None,
        time_series_data: Optional[List[Tuple[datetime, float]]] = None,
        baseline_period: Optional[Tuple[datetime, datetime]] = None,
        comparison_period: Optional[Tuple[datetime, datetime]] = None,
    ):
        """
        Initialize a new neurotransmitter effect.
        
        Args:
            neurotransmitter: The neurotransmitter being analyzed
            effect_size: Magnitude of effect (0.0 to 1.0)
            p_value: Statistical p-value of the effect
            confidence_interval: Lower and upper bounds of the effect size
            clinical_significance: Clinical significance classification
            is_statistically_significant: Whether the effect is statistically significant
            brain_region: Brain region where the effect occurs
            time_series_data: Time series data for the neurotransmitter levels
            baseline_period: Period defining the baseline for comparison
            comparison_period: Period to compare against the baseline
        """
        self.neurotransmitter = neurotransmitter
        self.effect_size = effect_size
        self.p_value = p_value
        self.confidence_interval = confidence_interval
        self.clinical_significance = clinical_significance or self._determine_clinical_significance()
        self.is_statistically_significant = is_statistically_significant
        self.brain_region = brain_region
        self.time_series_data = time_series_data or []
        self.baseline_period = baseline_period
        self.comparison_period = comparison_period
    
    def _determine_clinical_significance(self) -> ClinicalSignificance:
        """
        Determine clinical significance based on effect size and statistical significance.
        
        Returns:
            ClinicalSignificance enum value
        """
        if self.is_statistically_significant and self.effect_size >= 0.8:
            return ClinicalSignificance.SIGNIFICANT
        elif self.is_statistically_significant and self.effect_size >= 0.5:
            return ClinicalSignificance.MODERATE
        elif self.is_statistically_significant and self.effect_size >= 0.2:
            return ClinicalSignificance.MILD
        elif self.is_statistically_significant:
            return ClinicalSignificance.MINIMAL
        else:
            return ClinicalSignificance.NONE
    
    def get_relative_change(self) -> float:
        """
        Calculate relative change in neurotransmitter levels.
        
        Returns:
            Relative change as a percentage
        """
        if not self.time_series_data or len(self.time_series_data) < 2:
            return 0.0
            
        # Get first and last values
        first_value = self.time_series_data[0][1]
        last_value = self.time_series_data[-1][1]
        
        # Avoid division by zero
        if first_value == 0:
            return 0.0 if last_value == 0 else 1.0
            
        return (last_value - first_value) / first_value
    
    def get_trend_direction(self) -> str:
        """
        Get trend direction (increasing, decreasing, stable).
        
        Returns:
            String describing the trend direction
        """
        relative_change = self.get_relative_change()
        
        if relative_change > 0.1:
            return "increasing"
        elif relative_change < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert effect to dictionary for serialization.
        
        Returns:
            Dictionary representation of the effect
        """
        result = {
            "neurotransmitter": self.neurotransmitter.value,
            "effect_size": self.effect_size,
            "p_value": self.p_value,
            "confidence_interval": self.confidence_interval,
            "is_statistically_significant": self.is_statistically_significant,
            "clinical_significance": self.clinical_significance.value if self.clinical_significance else None,
            "trend_direction": self.get_trend_direction(),
        }
        
        if self.brain_region:
            result["brain_region"] = self.brain_region.value
            
        # Add time series data if available
        if self.time_series_data:
            result["time_series_data"] = [
                {"timestamp": ts.isoformat(), "value": value}
                for ts, value in self.time_series_data
            ]
            
        # Add comparison periods if available
        if self.baseline_period and self.comparison_period:
            result["comparison_periods"] = {
                "baseline": {
                    "start": self.baseline_period[0].isoformat(),
                    "end": self.baseline_period[1].isoformat()
                },
                "comparison": {
                    "start": self.comparison_period[0].isoformat(),
                    "end": self.comparison_period[1].isoformat()
                }
            }
            
        return result