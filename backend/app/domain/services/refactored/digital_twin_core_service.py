"""
Digital Twin Core Service Interface.
This is the central orchestrating service that coordinates the Trinity Stack components.
Pure domain interface with no infrastructure dependencies.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.app.domain.entities.refactored.digital_twin_core import (
    DigitalTwinState,
)
from backend.app.domain.entities.refactored.knowledge_graph import (
    BayesianBeliefNetwork,
    TemporalKnowledgeGraph,
)


class DigitalTwinCoreService(ABC):
    """
    Abstract interface for Digital Twin Core operations.
    Responsible for orchestrating interactions between all AI components
    and managing the state of the Digital Twin.
    
    Concrete implementations will be provided in the infrastructure layer.
    """
    
    @abstractmethod
    async def initialize_digital_twin(
        self,
        reference_id: UUID,
        initial_data: dict | None = None,
        enable_knowledge_graph: bool = True,
        enable_belief_network: bool = True
    ) -> tuple[DigitalTwinState, TemporalKnowledgeGraph | None, BayesianBeliefNetwork | None]:
        """
        Initialize a new Digital Twin with knowledge graph and belief network.
        
        Args:
            reference_id: UUID reference identifier
            initial_data: Optional initial data for the Digital Twin
            enable_knowledge_graph: Whether to enable the knowledge graph
            enable_belief_network: Whether to enable the Bayesian belief network
            
        Returns:
            Tuple of (DigitalTwinState, TemporalKnowledgeGraph, BayesianBeliefNetwork)
            Knowledge graph and belief network may be None if disabled
        """
        pass
    
    @abstractmethod
    async def process_multimodal_data(
        self,
        reference_id: UUID,
        text_data: dict | None = None,
        physiological_data: dict | None = None,
        imaging_data: dict | None = None,
        behavioral_data: dict | None = None,
        genetic_data: dict | None = None,
        context: dict | None = None
    ) -> tuple[DigitalTwinState, list[dict]]:
        """
        Process multimodal data using all three AI components (Trinity Stack).
        
        Args:
            reference_id: UUID reference identifier
            text_data: Optional textual data (clinical notes, etc.)
            physiological_data: Optional physiological data (heart rate, etc.)
            imaging_data: Optional imaging data (brain scans, etc.)
            behavioral_data: Optional behavioral data (activity, sleep, etc.)
            genetic_data: Optional genetic data (variants, etc.)
            context: Optional additional context
            
        Returns:
            Tuple of (updated DigitalTwinState, processing results)
        """
        pass
    
    @abstractmethod
    async def update_knowledge_graph(
        self,
        reference_id: UUID,
        new_data: dict,
        data_source: str,
        digital_twin_state_id: UUID | None = None
    ) -> TemporalKnowledgeGraph:
        """
        Update the temporal knowledge graph with new data.
        
        Args:
            reference_id: UUID reference identifier
            new_data: New data to incorporate into the graph
            data_source: Source of the new data
            digital_twin_state_id: Optional specific Digital Twin state ID
            
        Returns:
            Updated TemporalKnowledgeGraph
        """
        pass
    
    @abstractmethod
    async def update_belief_network(
        self,
        reference_id: UUID,
        evidence: dict[str, Any],
        data_source: str
    ) -> BayesianBeliefNetwork:
        """
        Update the Bayesian belief network with new evidence.
        
        Args:
            reference_id: UUID reference identifier
            evidence: New evidence as node-value pairs
            data_source: Source of the evidence
            
        Returns:
            Updated BayesianBeliefNetwork
        """
        pass
    
    @abstractmethod
    async def perform_counterfactual_simulation(
        self,
        reference_id: UUID,
        intervention: dict[str, Any],
        target_states: list[str],
        context: dict | None = None
    ) -> dict[str, Any]:
        """
        Perform counterfactual simulation to predict outcomes of interventions.
        
        Args:
            reference_id: UUID reference identifier
            intervention: Intervention to simulate (e.g., medication change)
            target_states: States to predict after intervention
            context: Optional additional context
            
        Returns:
            Simulation results including predictions and confidence intervals
        """
        pass
    
    @abstractmethod
    async def detect_temporal_cascade(
        self,
        reference_id: UUID,
        event_types: list[str],
        time_window: tuple[datetime, datetime] | None = None
    ) -> dict[str, Any]:
        """
        Detect temporal cascades (cause-effect chains) in data.
        
        Args:
            reference_id: UUID reference identifier
            event_types: Types of events to analyze
            time_window: Optional time window for analysis
            
        Returns:
            Detected temporal cascades with confidence scores
        """
        pass
    
    @abstractmethod
    async def generate_clinical_summary(
        self,
        reference_id: UUID,
        include_insights: bool = True,
        include_predictions: bool = True,
        include_recommendations: bool = True
    ) -> dict[str, Any]:
        """
        Generate a comprehensive clinical summary from the Digital Twin.
        
        Args:
            reference_id: UUID reference identifier
            include_insights: Whether to include clinical insights
            include_predictions: Whether to include predictions
            include_recommendations: Whether to include recommendations
            
        Returns:
            Clinical summary with requested components
        """
        pass
    
    @abstractmethod
    async def generate_visualization_data(
        self,
        reference_id: UUID,
        visualization_type: str,
        parameters: dict[str, Any],
        digital_twin_state_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Generate data for visualizing the Digital Twin.
        
        Args:
            reference_id: UUID reference identifier
            visualization_type: Type of visualization to generate
            parameters: Parameters for the visualization
            digital_twin_state_id: Optional specific Digital Twin state ID
            
        Returns:
            Visualization data in the requested format
        """
        pass
    
    @abstractmethod
    async def get_latest_digital_twin_state(
        self,
        reference_id: UUID
    ) -> DigitalTwinState | None:
        """
        Get the latest Digital Twin state.
        
        Args:
            reference_id: UUID reference identifier
            
        Returns:
            Latest DigitalTwinState if available, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_digital_twin_state(
        self,
        state_id: UUID
    ) -> DigitalTwinState | None:
        """
        Get a specific Digital Twin state by ID.
        
        Args:
            state_id: UUID of the state to retrieve
            
        Returns:
            DigitalTwinState if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def compare_digital_twin_states(
        self,
        state_id_1: UUID,
        state_id_2: UUID
    ) -> dict[str, Any]:
        """
        Compare two Digital Twin states and return differences.
        
        Args:
            state_id_1: UUID of first state to compare
            state_id_2: UUID of second state to compare
            
        Returns:
            Dictionary containing the differences between the states
        """
        pass
    
    @abstractmethod
    async def subscribe_to_events(
        self,
        reference_id: UUID,
        event_types: list[str],
        callback: Any
    ) -> str:
        """
        Subscribe to Digital Twin events.
        
        Args:
            reference_id: UUID reference identifier
            event_types: Types of events to subscribe to
            callback: Callback to invoke when events occur
            
        Returns:
            Subscription ID
        """
        pass
    
    @abstractmethod
    async def publish_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        source: str,
        reference_id: UUID
    ) -> None:
        """
        Publish an event related to the Digital Twin.
        
        Args:
            event_type: Type of event
            event_data: Event data
            source: Source of the event
            reference_id: UUID reference identifier
        """
        pass