"""
Brain Region State entity model for the Digital Twin system.

This module contains the BrainRegionState class, which represents the state of a brain region
at a specific point in time, including activity levels, connections, and neurotransmitter effects.
"""

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from .brain_region import BrainRegion


class ConnectionType(str, Enum):
    """Types of neural connections between brain regions."""
    
    EXCITATORY = "excitatory"
    INHIBITORY = "inhibitory"
    MODULATORY = "modulatory"
    BIDIRECTIONAL = "bidirectional"


class BrainRegionState(BaseModel):
    """
    Model representing the complete state of a brain region, including activity,
    connections to other regions, and neurotransmitter interactions.
    """
    
    region: BrainRegion
    activity_level: float = Field(
        ...,
        ge=-1.0, 
        le=1.0, 
        description="Normalized activity level from -1.0 (inhibited) to 1.0 (excited)"
    )
    connections: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Dictionary mapping target region IDs to connection properties"
    )
    neurotransmitter_sensitivity: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary mapping neurotransmitter names to sensitivity levels"
    )
    receptor_density: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary mapping receptor types to density levels"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence level in this state assessment (0.0-1.0)"
    )
    timestamp: Optional[float] = Field(
        default=None,
        description="Timestamp when this state was recorded (if temporal)"
    )
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )
    
    def add_connection(
        self, 
        target_region: BrainRegion, 
        connection_type: ConnectionType,
        strength: float = 0.5
    ) -> None:
        """
        Add a connection from this region to another brain region.
        
        Args:
            target_region: The target brain region to connect to
            connection_type: The type of connection (excitatory, inhibitory, etc.)
            strength: The strength of the connection (0.0-1.0)
        """
        if target_region.value not in self.connections:
            self.connections[target_region.value] = {}
        
        self.connections[target_region.value].update({
            "type": connection_type,
            "strength": strength
        })
    
    def get_connections(self) -> Dict[str, Dict[str, float]]:
        """
        Get all connections from this region to other regions.
        
        Returns:
            Dictionary mapping target region IDs to connection properties
        """
        return self.connections
    
    def set_neurotransmitter_sensitivity(self, neurotransmitter: str, sensitivity: float) -> None:
        """
        Set the sensitivity of this region to a specific neurotransmitter.
        
        Args:
            neurotransmitter: The neurotransmitter name
            sensitivity: The sensitivity level (-1.0 to 1.0, where negative means inhibitory)
        """
        self.neurotransmitter_sensitivity[neurotransmitter] = max(-1.0, min(1.0, sensitivity))
    
    def is_connected_to(self, target_region: BrainRegion) -> bool:
        """
        Check if this region is connected to the specified target region.
        
        Args:
            target_region: The target brain region
            
        Returns:
            True if connected, False otherwise
        """
        return target_region.value in self.connections
