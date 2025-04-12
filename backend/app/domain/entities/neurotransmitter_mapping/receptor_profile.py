"""
Receptor Profile entity model for the Digital Twin system.

This module contains the ReceptorProfile and ReceptorType classes,
which represent neurotransmitter receptor configurations in brain regions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from app.domain.entities.digital_twin.brain_region import BrainRegion
from app.domain.entities.digital_twin.clinical_insight import ClinicalSignificance
from app.domain.entities.digital_twin.neurotransmitter import Neurotransmitter
from app.domain.entities.digital_twin.receptor_subtype import ReceptorSubtype


class ReceptorType(str, Enum):
    """Enum representing different types of neurotransmitter receptors."""
    
    EXCITATORY = "excitatory"
    INHIBITORY = "inhibitory"
    MODULATORY = "modulatory"
    IONOTROPIC = "ionotropic"
    METABOTROPIC = "metabotropic"
    FAST_ACTING = "fast_acting"
    SLOW_ACTING = "slow_acting"


@dataclass
class ReceptorProfile:
    """
    Represents a neurotransmitter receptor profile for a specific brain region.
    
    This entity models how a particular brain region responds to different
    neurotransmitters through various receptor subtypes.
    """
    brain_region: BrainRegion
    neurotransmitter: Neurotransmitter
    receptor_type: ReceptorType
    receptor_subtype: ReceptorSubtype
    density: float = 0.5  # Receptor density in this region (0.0-1.0)
    sensitivity: float = 1.0  # Overall sensitivity factor for this neurotransmitter in this region
    clinical_relevance: Optional['ClinicalSignificance'] = None  # Clinical significance of this receptor profile
    upregulation_potential: float = 0.2  # Maximum potential for upregulation (0.0-1.0)
    downregulation_potential: float = 0.2  # Maximum potential for downregulation (0.0-1.0)
    
    def calculate_response(self, neurotransmitter_level: float) -> float:
        """
        Calculate region response to a specific neurotransmitter level.
        
        Returns:
            float: Response strength from -1.0 (strongly inhibitory) to 1.0 (strongly excitatory)
        """
        if self.density == 0:
            return 0.0
            
        # Apply different transfer functions based on receptor type
        if self.receptor_type == ReceptorType.EXCITATORY:
            response = self.density * neurotransmitter_level
        elif self.receptor_type == ReceptorType.INHIBITORY:
            response = -self.density * neurotransmitter_level
        else:  # MODULATORY or other types
            response = self.density * (neurotransmitter_level - 0.5) * 2
                
        # Scale by sensitivity and clamp to -1.0 to 1.0
        response *= self.sensitivity
        return max(-1.0, min(1.0, response))
        
    def update_regulation(self, sustained_level: float, duration_factor: float = 1.0) -> None:
        """
        Update receptor regulation based on sustained neurotransmitter levels.
        
        Args:
            sustained_level: Average neurotransmitter level over time
            duration_factor: Factor representing duration of exposure (1.0 = standard)
        """
        # Homeostatic adaptation - receptors down-regulate when neurotransmitter is high
        if sustained_level > 0.7:  # High levels
            regulation_change = -self.downregulation_potential * duration_factor
        # Receptors up-regulate when neurotransmitter is low
        elif sustained_level < 0.3:  # Low levels
            regulation_change = self.upregulation_potential * duration_factor
        else:  # Normal levels
            regulation_change = 0
            
        # Apply the regulation change to the sensitivity
        self.sensitivity = max(0.1, min(2.0, self.sensitivity + regulation_change))
