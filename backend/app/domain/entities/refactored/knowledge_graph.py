"""
Knowledge representation entities for the Digital Twin.
Pure domain models for graph-based knowledge representation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""
    SYMPTOM = "symptom"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    BIOMARKER = "biomarker"
    BRAIN_REGION = "brain_region"
    NEUROTRANSMITTER = "neurotransmitter"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    LIFE_EVENT = "life_event"
    THOUGHT_PATTERN = "thought_pattern"
    SLEEP_PATTERN = "sleep_pattern"
    ACTIVITY = "activity"


class EdgeType(Enum):
    """Types of edges in the knowledge graph."""
    CAUSES = "causes"
    CORRELATES_WITH = "correlates_with"
    TREATS = "treats"
    WORSENS = "worsens"
    IMPROVES = "improves"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    PART_OF = "part_of"
    REGULATES = "regulates"
    INTERACTS_WITH = "interacts_with"
    INFLUENCES = "influences"


@dataclass
class KnowledgeGraphNode:
    """Node in the knowledge graph representing a clinical entity."""
    id: UUID
    type: NodeType
    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # Default to high confidence
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, type: NodeType, name: str, properties: dict[str, Any] | None = None, 
               confidence: float = 1.0) -> "KnowledgeGraphNode":
        """Factory method to create a new node with a generated UUID."""
        return cls(
            id=uuid4(),
            type=type,
            name=name,
            properties=properties or {},
            confidence=confidence
        )


@dataclass
class KnowledgeGraphEdge:
    """Edge in the knowledge graph representing a relationship between entities."""
    id: UUID
    source_id: UUID
    target_id: UUID
    type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    temporal_context: dict[str, Any] | None = None
    
    @classmethod
    def create(cls, source_id: UUID, target_id: UUID, type: EdgeType, 
               properties: dict[str, Any] | None = None, confidence: float = 1.0,
               temporal_context: dict[str, Any] | None = None) -> "KnowledgeGraphEdge":
        """Factory method to create a new edge with a generated UUID."""
        return cls(
            id=uuid4(),
            source_id=source_id,
            target_id=target_id,
            type=type,
            properties=properties or {},
            confidence=confidence,
            temporal_context=temporal_context
        )


@dataclass
class TemporalKnowledgeGraph:
    """
    Knowledge graph with temporal capabilities.
    Represents clinical knowledge as nodes and edges with time dimensions.
    """
    reference_id: UUID  # Reference ID (e.g., for a specific digital twin)
    nodes: dict[UUID, KnowledgeGraphNode] = field(default_factory=dict)
    edges: dict[UUID, KnowledgeGraphEdge] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def add_node(self, node: KnowledgeGraphNode) -> UUID:
        """
        Add a node to the graph.
        
        Args:
            node: The node to add
            
        Returns:
            UUID of the added node
        """
        self.nodes[node.id] = node
        self.updated_at = datetime.now()
        return node.id
    
    def add_edge(self, edge: KnowledgeGraphEdge) -> UUID:
        """
        Add an edge to the graph.
        
        Args:
            edge: The edge to add
            
        Returns:
            UUID of the added edge
        """
        # Ensure source and target nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Source or target node not found in graph")
        
        self.edges[edge.id] = edge
        self.updated_at = datetime.now()
        return edge.id
    
    def get_node(self, node_id: UUID) -> KnowledgeGraphNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: UUID) -> KnowledgeGraphEdge | None:
        """Get an edge by ID."""
        return self.edges.get(edge_id)
    
    def get_nodes_by_type(self, node_type: NodeType) -> list[KnowledgeGraphNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.type == node_type]
    
    def get_edges_by_type(self, edge_type: EdgeType) -> list[KnowledgeGraphEdge]:
        """Get all edges of a specific type."""
        return [edge for edge in self.edges.values() if edge.type == edge_type]
    
    def get_node_neighbors(self, node_id: UUID) -> dict[EdgeType, list[KnowledgeGraphNode]]:
        """
        Get all neighboring nodes connected by outgoing edges.
        
        Args:
            node_id: ID of the node to get neighbors for
            
        Returns:
            Dictionary mapping edge types to lists of neighboring nodes
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in graph")
            
        result = {}
        for edge in self.edges.values():
            if edge.source_id == node_id:
                edge_type = edge.type
                target_node = self.nodes.get(edge.target_id)
                if target_node:
                    if edge_type not in result:
                        result[edge_type] = []
                    result[edge_type].append(target_node)
        return result
    
    @classmethod
    def create(cls, reference_id: UUID) -> "TemporalKnowledgeGraph":
        """Create a new empty temporal knowledge graph."""
        return cls(reference_id=reference_id)


class BeliefNodeType(Enum):
    """Types of nodes in the Bayesian belief network."""
    SYMPTOM = "symptom"
    DIAGNOSIS = "diagnosis"
    TREATMENT_RESPONSE = "treatment_response"
    MEDICATION_EFFECT = "medication_effect"
    BIOMARKER = "biomarker"
    BRAIN_STATE = "brain_state"
    NEUROTRANSMITTER_LEVEL = "neurotransmitter_level"
    BEHAVIOR = "behavior"
    ENVIRONMENTAL_FACTOR = "environmental_factor"
    COGNITIVE_STATE = "cognitive_state"


@dataclass
class BayesianNode:
    """Node in the Bayesian belief network."""
    id: UUID
    type: BeliefNodeType
    name: str
    states: list[str]  # Possible states of this node
    probabilities: dict[str, float]  # Current probability distribution
    conditional_dependencies: list[UUID] = field(default_factory=list)  # Node IDs this node depends on
    conditional_probability_table: dict[str, float] | None = None  # Full CPT if available
    
    @classmethod
    def create(cls, type: BeliefNodeType, name: str, states: list[str], 
               probabilities: dict[str, float], 
               conditional_dependencies: list[UUID] | None = None) -> "BayesianNode":
        """Factory method to create a new Bayesian node."""
        return cls(
            id=uuid4(),
            type=type,
            name=name,
            states=states,
            probabilities=probabilities,
            conditional_dependencies=conditional_dependencies or []
        )


@dataclass
class BayesianBeliefNetwork:
    """
    Bayesian belief network for probabilistic reasoning.
    Models causal relationships and probabilities for clinical reasoning.
    """
    reference_id: UUID
    nodes: dict[UUID, BayesianNode] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def add_node(self, node: BayesianNode) -> UUID:
        """Add a node to the network."""
        # Validate probabilities sum to approximately 1.0
        prob_sum = sum(node.probabilities.values())
        if not (0.99 <= prob_sum <= 1.01):  # Allow for small floating point errors
            raise ValueError(f"Probabilities must sum to 1.0, got {prob_sum}")
            
        # Ensure all conditional dependencies exist in the network
        for dep_id in node.conditional_dependencies:
            if dep_id not in self.nodes:
                raise ValueError(f"Dependency node {dep_id} not found in network")
                
        self.nodes[node.id] = node
        self.updated_at = datetime.now()
        return node.id
    
    def update_node_probabilities(self, node_id: UUID, new_probabilities: dict[str, float]) -> None:
        """Update the probabilities of a node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in network")
            
        # Validate probabilities sum to approximately 1.0
        prob_sum = sum(new_probabilities.values())
        if not (0.99 <= prob_sum <= 1.01):
            raise ValueError(f"Probabilities must sum to 1.0, got {prob_sum}")
            
        # Ensure all states have probabilities
        node = self.nodes[node_id]
        for state in node.states:
            if state not in new_probabilities:
                raise ValueError(f"Missing probability for state '{state}'")
                
        node.probabilities = new_probabilities
        self.updated_at = datetime.now()
    
    def get_node(self, node_id: UUID) -> BayesianNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_nodes_by_type(self, node_type: BeliefNodeType) -> list[BayesianNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.type == node_type]
        
    @classmethod
    def create(cls, reference_id: UUID) -> "BayesianBeliefNetwork":
        """Create a new empty Bayesian belief network."""
        return cls(reference_id=reference_id)