"""
Model adapter for Digital Twin entities.

This module provides adapter classes and functions to ensure compatibility
between different model implementations (dataclasses, Pydantic models, etc.)
used in the Digital Twin system.
"""

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from uuid import UUID

from app.domain.entities.digital_twin.brain_region import BrainRegion
from app.domain.entities.digital_twin.clinical_insight import ClinicalInsight, ClinicalSignificance
from app.domain.entities.digital_twin.neurotransmitter import Neurotransmitter


def ensure_enum_value(value, enum_class):
    """Convert string to enum value if necessary, or keep as enum value."""
    if isinstance(value, str):
        try:
            return enum_class(value)
        except ValueError:
            # If the string doesn't match any enum value, try matching by name
            try:
                return enum_class[value]
            except KeyError:
                # Return the original string if all conversions fail
                return value
    return value


@dataclass
class BrainRegionStateAdapter:
    """
    Adapter implementation of BrainRegionState that accepts positional arguments.
    This allows compatibility with code that expects the dataclass implementation.
    """
    region: BrainRegion
    activation_level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    related_symptoms: List[str] = field(default_factory=list)
    clinical_significance: ClinicalSignificance = ClinicalSignificance.NONE


@dataclass
class NeurotransmitterStateAdapter:
    """
    Adapter implementation of NeurotransmitterState that accepts positional arguments.
    This allows compatibility with code that expects the dataclass implementation.
    """
    neurotransmitter: Neurotransmitter
    level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    clinical_significance: ClinicalSignificance = ClinicalSignificance.NONE
    
    def __add__(self, other):
        """Support addition with a float value."""
        if isinstance(other, (int, float)):
            return self.level + other
        raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __radd__(self, other):
        """Support right addition with a float value."""
        return self.__add__(other)
    
    def __sub__(self, other):
        """Support subtraction with a float value."""
        if isinstance(other, (int, float)):
            return self.level - other
        raise TypeError(f"unsupported operand type(s) for -: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __rsub__(self, other):
        """Support right subtraction with a float value."""
        if isinstance(other, (int, float)):
            return other - self.level
        raise TypeError(f"unsupported operand type(s) for -: '{type(other).__name__}' and '{type(self).__name__}'")
    
    def __mul__(self, other):
        """Support multiplication with a float value."""
        if isinstance(other, (int, float)):
            return self.level * other
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __rmul__(self, other):
        """Support right multiplication with a float value."""
        return self.__mul__(other)
    
    def __truediv__(self, other):
        """Support division with a float value."""
        if isinstance(other, (int, float)):
            return self.level / other
        raise TypeError(f"unsupported operand type(s) for /: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __rtruediv__(self, other):
        """Support right division with a float value."""
        if isinstance(other, (int, float)):
            return other / self.level
        raise TypeError(f"unsupported operand type(s) for /: '{type(other).__name__}' and '{type(self).__name__}'")
    
    def __float__(self):
        """Allow conversion to float."""
        return float(self.level)


@dataclass
class NeuralConnectionAdapter:
    """
    Adapter implementation of NeuralConnection that accepts positional arguments.
    This allows compatibility with code that expects the dataclass implementation.
    """
    source_region: BrainRegion
    target_region: BrainRegion
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0


@dataclass
class TemporalPatternAdapter:
    """
    Adapter implementation of TemporalPattern that accepts positional arguments.
    This allows compatibility with code that expects the dataclass implementation.
    """
    pattern_type: str  # e.g., "circadian", "weekly", "seasonal" 
    description: str
    confidence: float
    strength: float
    clinical_significance: ClinicalSignificance


@dataclass
class DigitalTwinStateAdapter:
    """
    Adapter implementation of DigitalTwinState that accepts positional arguments.
    This allows compatibility with code that expects the dataclass implementation.
    """
    patient_id: UUID
    timestamp: datetime
    brain_regions: Dict[BrainRegion, BrainRegionStateAdapter] = field(default_factory=dict)
    neurotransmitters: Dict[Neurotransmitter, NeurotransmitterStateAdapter] = field(default_factory=dict)
    neural_connections: List[NeuralConnectionAdapter] = field(default_factory=list)
    clinical_insights: List[ClinicalInsight] = field(default_factory=list)
    temporal_patterns: List[TemporalPatternAdapter] = field(default_factory=list)
    update_source: Optional[str] = None
    version: int = 1
    
    # Additional fields required by the mock service implementation
    id: UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    biomarkers: Dict[str, Any] = field(default_factory=dict)
    predicted_states: Dict[str, Any] = field(default_factory=dict)
    treatment_responses: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    active_treatments: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def significant_regions(self) -> List[BrainRegionStateAdapter]:
        """Return brain regions with clinical significance above NONE."""
        return [
            region for region in self.brain_regions.values()
            if region.clinical_significance != ClinicalSignificance.NONE
        ]
        
    def create_copy(self) -> 'DigitalTwinStateAdapter':
        """Create a deep copy of the current state."""
        # Create a new instance with the same essential properties
        new_state = DigitalTwinStateAdapter(
            patient_id=self.patient_id,
            timestamp=self.timestamp,
            version=self.version,
            id=uuid.uuid4(),  # Generate a new ID for the copy
            created_at=self.created_at,
            updated_at=datetime.now()  # Update the updated_at timestamp
        )
        
        # Deep copy all collections
        new_state.brain_regions = {k: v for k, v in self.brain_regions.items()}
        new_state.neurotransmitters = {k: v for k, v in self.neurotransmitters.items()}
        new_state.neural_connections = [conn for conn in self.neural_connections]
        # Process clinical insights to ensure proper enum handling
        new_state.clinical_insights = self.process_clinical_insights([insight for insight in self.clinical_insights])
        new_state.temporal_patterns = [pattern for pattern in self.temporal_patterns]
        new_state.biomarkers = self.biomarkers.copy()
        new_state.predicted_states = self.predicted_states.copy()
        new_state.treatment_responses = self.treatment_responses.copy()
        new_state.confidence_scores = self.confidence_scores.copy()
        new_state.active_treatments = self.active_treatments.copy()
        new_state.metadata = self.metadata.copy()
        new_state.update_source = self.update_source
        
        return new_state
    
    def process_clinical_insights(self, insights: List[ClinicalInsight]) -> List[ClinicalInsight]:
        """Process clinical insights to ensure proper enum conversion for brain regions and neurotransmitters."""
        processed_insights = []
        
        for insight in insights:
            # Create a deep copy to avoid modifying the original
            processed_insight = copy.deepcopy(insight)
            
            # Process brain regions
            if hasattr(processed_insight, 'brain_regions') and processed_insight.brain_regions:
                processed_brain_regions = []
                for region in processed_insight.brain_regions:
                    processed_brain_regions.append(ensure_enum_value(region, BrainRegion))
                processed_insight.brain_regions = processed_brain_regions
                
            # Process neurotransmitters
            if hasattr(processed_insight, 'neurotransmitters') and processed_insight.neurotransmitters:
                processed_neurotransmitters = []
                for nt in processed_insight.neurotransmitters:
                    processed_neurotransmitters.append(ensure_enum_value(nt, Neurotransmitter))
                processed_insight.neurotransmitters = processed_neurotransmitters
                
            processed_insights.append(processed_insight)
            
        return processed_insights
    
    @property
    def critical_insights(self) -> List[ClinicalInsight]:
        """Return insights with HIGH or CRITICAL significance."""
        return [
            insight for insight in self.clinical_insights
            if insight.clinical_significance in [
                ClinicalSignificance.HIGH, ClinicalSignificance.CRITICAL
            ]
        ]
    
    def create_copy(self, **kwargs) -> 'DigitalTwinStateAdapter':
        """Create a copy of this state with some fields updated."""
        # Create a new dict of all current attributes
        data = {
            'patient_id': self.patient_id,
            'timestamp': kwargs.get('timestamp', datetime.now()),
            'brain_regions': self.brain_regions.copy(),
            'neurotransmitters': self.neurotransmitters.copy(),
            'neural_connections': self.neural_connections.copy(),
            'clinical_insights': self.clinical_insights.copy(),
            'temporal_patterns': self.temporal_patterns.copy(),
            'update_source': kwargs.get('update_source', self.update_source),
            'version': kwargs.get('version', self.version + 1)
        }
        
        # Update with provided kwargs
        for key, value in kwargs.items():
            if key in data:
                data[key] = value
        
        # Create a new instance
        return DigitalTwinStateAdapter(**data)
    
    def generate_fingerprint(self) -> str:
        """Generate a unique fingerprint for this state for verification."""
        return f"{self.patient_id}:{self.timestamp}:{self.version}"
    
    def add_clinical_insight(self, insight: ClinicalInsight) -> None:
        """Add a clinical insight to this state."""
        # Process the insight before adding to ensure proper enum handling
        processed_insights = self.process_clinical_insights([insight])
        self.clinical_insights.append(processed_insights[0])
    
    def add_temporal_pattern(self, pattern: TemporalPatternAdapter) -> None:
        """Add a temporal pattern to this state."""
        self.temporal_patterns.append(pattern)
