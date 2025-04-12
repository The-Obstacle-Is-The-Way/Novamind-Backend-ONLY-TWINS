"""
Neurotransmitter State entity model for the Digital Twin system.

This module contains the NeurotransmitterState class, which represents 
the dynamic state of a neurotransmitter at a specific point in time.
"""

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .neurotransmitter import Neurotransmitter


class NeurotransmitterState(BaseModel):
    """
    Model representing the comprehensive state of a neurotransmitter within the digital twin,
    including its current level, receptor interactions, and clinical significance.
    """
    
    neurotransmitter: Neurotransmitter
    level: float = Field(
        ...,
        ge=-1.0, 
        le=1.0, 
        description="Normalized level from -1.0 (severe deficiency) to 1.0 (severe excess)"
    )
    receptor_interactions: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary mapping receptor types to interaction strengths"
    )
    region_effects: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary mapping brain regions to effect strengths"
    )
    temporal_dynamics: Dict[str, float] = Field(
        default_factory=dict,
        description="Temporal characteristics like half-life, accumulation rate, etc."
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence level in this state assessment (0.0-1.0)"
    )
    clinical_significance: str = Field(
        default="none",
        description="Clinical significance of the current state (none, low, moderate, high, critical)"
    )
    timestamp: Optional[float] = Field(
        default=None,
        description="Timestamp when this state was recorded (if temporal)"
    )
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )
    
    def add_receptor_interaction(self, receptor_type: str, interaction_strength: float) -> None:
        """
        Add or update a receptor interaction for this neurotransmitter.
        
        Args:
            receptor_type: The type of receptor (e.g., "5-HT1A", "D2", etc.)
            interaction_strength: The strength of interaction (-1.0 to 1.0)
        """
        self.receptor_interactions[receptor_type] = max(-1.0, min(1.0, interaction_strength))
    
    def add_region_effect(self, brain_region: str, effect_strength: float) -> None:
        """
        Add or update an effect on a brain region for this neurotransmitter.
        
        Args:
            brain_region: The brain region name
            effect_strength: The strength of effect (-1.0 to 1.0)
        """
        self.region_effects[brain_region] = max(-1.0, min(1.0, effect_strength))
    
    def get_dominant_receptors(self, threshold: float = 0.5) -> List[str]:
        """
        Get the most strongly affected receptors for this neurotransmitter.
        
        Args:
            threshold: Minimum absolute interaction strength to include
            
        Returns:
            List of receptor types with strong interactions
        """
        return [r for r, strength in self.receptor_interactions.items() 
                if abs(strength) >= threshold]
    
    def get_dominant_regions(self, threshold: float = 0.5) -> List[str]:
        """
        Get the most strongly affected brain regions for this neurotransmitter.
        
        Args:
            threshold: Minimum absolute effect strength to include
            
        Returns:
            List of brain regions with strong effects
        """
        return [r for r, strength in self.region_effects.items() 
                if abs(strength) >= threshold]
