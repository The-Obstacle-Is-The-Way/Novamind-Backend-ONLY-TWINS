"""
Temporal neurotransmitter mapping module for the Temporal Neurotransmitter System.

This module defines the core classes that map neurotransmitter activity across brain regions
over time, including mechanisms for modeling cascading effects and treatment responses.
"""
import math
import random
import uuid
import numpy as np
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

from app.domain.entities.digital_twin_enums import (
    BrainRegion,
    ClinicalSignificance,
    Neurotransmitter,
    TemporalResolution,
)
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.neurotransmitter_mapping import (
    NeurotransmitterMapping,
    ReceptorProfile,
    ReceptorType,
)
from app.domain.entities.temporal_events import (
    TemporalEvent,
)
from app.domain.entities.temporal_sequence import TemporalSequence


class EventType(Enum):
    """Types of neurotransmitter events that can be tracked."""
    LEVEL_INCREASE = auto()
    LEVEL_DECREASE = auto()
    THRESHOLD_CROSSED_UP = auto()
    THRESHOLD_CROSSED_DOWN = auto()
    OSCILLATION = auto()
    TREATMENT_RESPONSE = auto()
    ACTIVITY_CHANGE = auto()
    CONNECTIVITY_CHANGE = auto()


class TransmissionPattern(Enum):
    """Patterns of neurotransmitter transmission across regions."""
    SEQUENTIAL = auto()
    PARALLEL = auto()
    FEEDBACK = auto()
    FEEDFORWARD = auto()
    OSCILLATORY = auto()
    CYCLICAL = auto()
    CHAOTIC = auto()
    INHIBITORY = auto()  # Added this pattern for inhibitory neurotransmitters like GABA


class TemporalNeurotransmitterMapping(NeurotransmitterMapping):
    """
    Extended neurotransmitter mapping with temporal dynamics.
    
    This class adds temporal aspects to the neurotransmitter mapping, allowing for:
    - Tracking how neurotransmitter levels change over time
    - Modeling cascading effects across brain regions
    - Simulating treatment responses
    - Analyzing temporal patterns and correlations
    """
    
    def __init__(self, patient_id: UUID | None = None):
        """
        Initialize a temporal neurotransmitter mapping.
        
        Args:
            patient_id: Optional UUID of the associated patient
        """
        super().__init__(patient_id=patient_id)
        
        # Track temporal sequences
        
        # Track temporal sequences
        self.temporal_sequences: dict[tuple[BrainRegion, Neurotransmitter], list[TemporalSequence]] = {}
        
        # Track events
        self.events: dict[UUID, TemporalEvent] = {}
        
        # Track correlations between events
        self.correlations: dict[UUID, dict[UUID, float]] = {}
        
        # Track cascading patterns
        self.cascade_patterns: dict[BrainRegion, dict[Neurotransmitter, TransmissionPattern]] = {}
        
        # Baseline activity levels for each region and neurotransmitter
        self.baseline_levels: dict[BrainRegion, dict[Neurotransmitter, float]] = {}
        
        # Initialize baselines with default values
        self._initialize_baselines()
        
    def _initialize_baselines(self):
        """Initialize baseline neurotransmitter levels for all brain regions."""
        for region in BrainRegion:
            self.baseline_levels[region] = {}
            for nt in Neurotransmitter:
                # Default baseline is 0.5 (normalized range 0-1)
                # Adjust based on whether the region produces this neurotransmitter
                produces = False
                if nt in self.production_sites:
                    produces = region in self.production_sites[nt]
                    
                # Regions that produce a neurotransmitter have slightly higher baseline
                self.baseline_levels[region][nt] = 0.6 if produces else 0.4
                
    def analyze_receptor_affinity(self, neurotransmitter: Neurotransmitter, brain_region: BrainRegion) -> float:
        """
        Analyze the affinity of receptors in a brain region for a specific neurotransmitter.
        
        Args:
            neurotransmitter: The neurotransmitter to analyze
            brain_region: The brain region to analyze
            
        Returns:
            A float value representing the receptor affinity (0.0 to 1.0)
        """
        # Get all receptor profiles for this combination
        profiles = self.get_receptor_profiles(
            brain_region=brain_region,
            neurotransmitter=neurotransmitter
        )
        
        if not profiles:
            return 0.0  # No receptors for this neurotransmitter in this region
            
        # Calculate the average affinity based on receptor density and sensitivity
        total_affinity = 0.0
        count = 0
        
        for profile in profiles:
            # Calculate affinity based on density and sensitivity
            affinity = profile.density * profile.sensitivity
            total_affinity += affinity
            count += 1
            
        return total_affinity / max(count, 1)  # Avoid division by zero
        
    def generate_temporal_sequence(
        self,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        timestamps: List[datetime],
        noise_level: float = 0.1
    ) -> TemporalSequence:
        """
        Generate a temporal sequence for a neurotransmitter in a brain region.
        
        Args:
            brain_region: The brain region to model
            neurotransmitter: The primary neurotransmitter to model
            timestamps: The timestamps for the sequence
            noise_level: Amount of random noise to add (0.0-1.0)
            
        Returns:
            A TemporalSequence object with the generated data
        """
        # Get baseline level for this neurotransmitter in this region
        baseline = self.baseline_levels.get(brain_region, {}).get(neurotransmitter, 0.5)
        
        # Create feature names for all neurotransmitters
        feature_names = [nt.value for nt in Neurotransmitter]
        
        # Initialize data matrix with zeros
        num_timestamps = len(timestamps)
        num_features = len(feature_names)
        data = np.zeros((num_timestamps, num_features))
        
        # Get index of the primary neurotransmitter
        primary_nt_idx = [i for i, name in enumerate(feature_names) if name == neurotransmitter.value][0]
        
        # Generate values for primary neurotransmitter
        for t in range(num_timestamps):
            # Add some temporal dependency (autoregressive component)
            if t > 0:
                prev_value = data[t-1, primary_nt_idx]
                # Random walk with mean reversion to baseline
                data[t, primary_nt_idx] = prev_value + (baseline - prev_value) * 0.3 + (random.random() - 0.5) * noise_level
            else:
                data[t, primary_nt_idx] = baseline + (random.random() - 0.5) * noise_level
                
            # Ensure values stay in valid range
            data[t, primary_nt_idx] = max(0.0, min(1.0, data[t, primary_nt_idx]))
        
        # Generate correlated values for other neurotransmitters
        for nt_idx, nt_name in enumerate(feature_names):
            if nt_idx != primary_nt_idx:
                # Create correlation based on receptor affinities
                other_nt = next(nt for nt in Neurotransmitter if nt.value == nt_name)
                correlation = self.analyze_receptor_affinity(other_nt, brain_region) * 0.8
                
                # Generate correlated data
                other_baseline = self.baseline_levels.get(brain_region, {}).get(other_nt, 0.5)
                
                for t in range(num_timestamps):
                    # Correlation effect + independent component + baseline
                    data[t, nt_idx] = (
                        other_baseline * 0.7 +
                        correlation * (data[t, primary_nt_idx] - baseline) +
                        (random.random() - 0.5) * noise_level
                    )
                    # Ensure values stay in valid range
                    data[t, nt_idx] = max(0.0, min(1.0, data[t, nt_idx]))
        
        # Create metadata
        metadata = {
            "brain_region": brain_region.value,
            "primary_neurotransmitter": neurotransmitter.value,
            "generation_time": datetime.now().isoformat(),
            "baseline_level": baseline,
            "is_simulation": True
        }
        
        # Convert data to list format for TemporalSequence
        values_list = data.tolist()
        
        # Create the temporal sequence with the correct parameters
        sequence = TemporalSequence(
            sequence_id=uuid.uuid4(),
            feature_names=feature_names,
            timestamps=timestamps,
            values=values_list,
            patient_id=self.patient_id if self.patient_id else uuid.uuid4(),
            metadata=metadata,
            name=f"{brain_region.value}_{neurotransmitter.value}_sequence",
            brain_region=brain_region,
            neurotransmitter=neurotransmitter,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            temporal_resolution=TemporalResolution.HOURLY
        )
        
        # Store in our mapping
        key = (brain_region, neurotransmitter)
        if key not in self.temporal_sequences:
            self.temporal_sequences[key] = []
        self.temporal_sequences[key].append(sequence)
        
        return sequence
        
    def predict_cascade_effect(
        self,
        starting_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        effect_magnitude: float = 1.0,
        max_depth: int = 3,
        effect_duration: Optional[float] = None,
        initial_level: float = None,
        time_steps: int = None
    ) -> Union[Dict[BrainRegion, Dict[Neurotransmitter, float]], Dict[BrainRegion, List[float]]]:
        """
        Predict how a change in one brain region cascades to others.
        
        Args:
            starting_region: The brain region where the effect starts
            neurotransmitter: The neurotransmitter whose level changes
            effect_magnitude: Magnitude of the initial effect (positive or negative)
            max_depth: Maximum depth of cascading effects to model
            effect_duration: Optional duration of effect in hours
            
        Returns:
            Nested dictionary mapping brain regions to affected neurotransmitters and effect sizes
        """
        # Initialize result structure
        cascade_effects = {}
        
        # Initialize queue for breadth-first traversal
        # Each entry is (region, neurotransmitter, effect_size, depth)
        queue = [(starting_region, neurotransmitter, effect_magnitude, 0)]
        
        # Track visited combinations to avoid cycles
        visited = set()
        
        # Process the queue
        while queue:
            region, nt, effect, depth = queue.pop(0)
            
            # Skip if we've exceeded max depth
            if depth > max_depth:
                continue
                
            # Create a unique key for this combination
            visit_key = (region, nt)
            if visit_key in visited:
                continue
            visited.add(visit_key)
            
            # Record this effect
            if region not in cascade_effects:
                cascade_effects[region] = {}
            
            # If this neurotransmitter is already affected, accumulate the effect
            if nt in cascade_effects[region]:
                cascade_effects[region][nt] += effect
            else:
                cascade_effects[region][nt] = effect
                
            # If we've reached max depth, don't add any more to the queue
            if depth == max_depth:
                continue
                
            # Find connected regions
            connected_regions = []
            if hasattr(self, 'brain_region_connectivity') and region in self.brain_region_connectivity:
                connected_regions = list(self.brain_region_connectivity[region].items())
            
            # Sort by connection strength (descending)
            connected_regions.sort(key=lambda x: x[1], reverse=True)
            
            # For each connected region, propagate effect
            for connected_region, connection_strength in connected_regions:
                # Calculate propagated effect size
                propagated_effect = effect * connection_strength * 0.8  # Dampen with distance
                
                # Determine which neurotransmitters are affected
                affected_neurotransmitters = [nt]  # The primary neurotransmitter
                
                # Add secondary neurotransmitters based on receptor profiles
                for other_nt in Neurotransmitter:
                    if other_nt != nt:
                        # Check if there are receptors for both neurotransmitters
                        has_source_receptors = any(
                            p.neurotransmitter == nt for p in self.get_receptor_profiles_for_region(connected_region)
                        )
                        has_target_receptors = any(
                            p.neurotransmitter == other_nt for p in self.get_receptor_profiles_for_region(connected_region)
                        )
                        
                        if has_source_receptors and has_target_receptors:
                            affected_neurotransmitters.append(other_nt)
                
                # Queue up effects for the next iteration
                for affected_nt in affected_neurotransmitters:
                    # Calculate modulation factor based on receptor types
                    modulation = 1.0
                    profiles = self.get_receptor_profiles(
                        brain_region=connected_region,
                        neurotransmitter=affected_nt
                    )
                    
                    for profile in profiles:
                        if profile.receptor_type == ReceptorType.INHIBITORY:
                            modulation = -0.7  # Inhibitory receptors reverse effect direction
                            break
                    
                    # Add to queue with modulated effect
                    secondary_effect = propagated_effect * modulation * (0.5 if affected_nt != nt else 1.0)
                    queue.append((connected_region, affected_nt, secondary_effect, depth + 1))
        
        return cascade_effects
    
    def analyze_temporal_response(self, sequence: TemporalSequence) -> Dict[str, Any]:
        """
        Analyze a temporal sequence to extract patterns and insights.
        
        Args:
            sequence: The temporal sequence to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Initialize results
        results = {
            "trends": {},
            "patterns": {},
            "correlations": {},
            "statistics": {}
        }
        
        # Extract data as numpy array for analysis
        data = np.array(sequence.values)
        timestamps = sequence.timestamps
        feature_names = sequence.feature_names
        
        # Calculate basic statistics for each neurotransmitter
        for i, feature in enumerate(feature_names):
            # Get all values for this feature
            values = [row[i] for row in sequence.values]
            
            # Calculate statistics
            mean_value = sum(values) / len(values)
            std_dev = math.sqrt(sum((x - mean_value) ** 2 for x in values) / len(values))
            min_value = min(values)
            max_value = max(values)
            
            # Detect trend direction
            if len(values) > 1:
                # Simple linear regression to detect trend
                x = np.arange(len(values))
                A = np.vstack([x, np.ones(len(x))]).T
                m, c = np.linalg.lstsq(A, values, rcond=None)[0]
                
                # Determine trend direction
                if abs(m) < 0.01:
                    trend = "stable"
                elif m > 0:
                    trend = "increasing"
                else:
                    trend = "decreasing"
                    
                # Calculate rate of change
                rate_of_change = m
            else:
                trend = "unknown"
                rate_of_change = 0.0
                
            # Store statistics
            results["statistics"][feature] = {
                "mean": mean_value,
                "std_dev": std_dev,
                "min": min_value,
                "max": max_value,
                "range": max_value - min_value
            }
            
            # Store trend
            results["trends"][feature] = {
                "direction": trend,
                "rate_of_change": rate_of_change
            }
            
        # Calculate correlations between neurotransmitters
        if len(feature_names) > 1:
            # Create correlation matrix
            corr_matrix = np.zeros((len(feature_names), len(feature_names)))
            for i in range(len(feature_names)):
                for j in range(len(feature_names)):
                    if i == j:
                        corr_matrix[i, j] = 1.0
                    else:
                        values_i = [row[i] for row in sequence.values]
                        values_j = [row[j] for row in sequence.values]
                        
                        # Calculate correlation coefficient
                        mean_i = sum(values_i) / len(values_i)
                        mean_j = sum(values_j) / len(values_j)
                        
                        num = sum((values_i[k] - mean_i) * (values_j[k] - mean_j) for k in range(len(values_i)))
                        denom_i = sum((values_i[k] - mean_i) ** 2 for k in range(len(values_i)))
                        denom_j = sum((values_j[k] - mean_j) ** 2 for k in range(len(values_j)))
                        
                        if denom_i > 0 and denom_j > 0:
                            corr = num / (math.sqrt(denom_i) * math.sqrt(denom_j))
                            corr_matrix[i, j] = corr
                        else:
                            corr_matrix[i, j] = 0.0
            
            for i, feature1 in enumerate(feature_names):
                for j, feature2 in enumerate(feature_names):
                    if i != j:
                        correlation = float(corr_matrix[i, j])
                        
                        # Skip weak correlations
                        if abs(correlation) > 0.3:
                            if feature1 not in results["correlations"]:
                                results["correlations"][feature1] = {}
                                
                            results["correlations"][feature1][feature2] = correlation
        
        # Detect oscillations and patterns
        for i, feature in enumerate(feature_names):
            values = [row[i] for row in sequence.values]
            
            # Detect oscillations (simplified)
            # Count sign changes in first derivative
            if len(values) > 3:
                diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
                sign_changes = sum(1 for i in range(len(diffs)-1) if diffs[i] * diffs[i+1] < 0)
                
                # Check if there are many sign changes (potential oscillation)
                oscillation_threshold = len(values) * 0.4
                has_oscillation = sign_changes > oscillation_threshold
                
                # Store pattern information
                results["patterns"][feature] = {
                    "has_oscillation": bool(has_oscillation),
                    "oscillation_count": int(sign_changes),
                    "pattern_type": "oscillatory" if has_oscillation else "directional"
                }
                
        return results
     
    def simulate_treatment_response(
        self,
        brain_region: BrainRegion,
        target_neurotransmitter: Neurotransmitter = None,
        treatment_effect: float = 0.5,
        timestamps: List[datetime] = None,
        affected_neurotransmitters: Dict[Neurotransmitter, float] = None,
        medication_name: str = "Generic Medication"
    ) -> Dict[Neurotransmitter, TemporalSequence]:
        """
        Simulate how a medication affects neurotransmitter levels over time.
        
        Args:
            brain_region: The primary brain region targeted
            target_neurotransmitter: The primary neurotransmitter affected (for backwards compatibility)
            treatment_effect: Overall strength of the treatment effect
            timestamps: List of timestamps for the temporal sequences
            affected_neurotransmitters: Dictionary mapping neurotransmitters to relative effect sizes
            medication_name: Name of the medication being simulated
            
        Returns:
            Dictionary mapping neurotransmitters to temporal sequences
        """
        # For backwards compatibility
        if affected_neurotransmitters is None:
            affected_neurotransmitters = {}
            if target_neurotransmitter:
                affected_neurotransmitters[target_neurotransmitter] = 1.0
        
        # Use current timestamps if none provided
        if timestamps is None:
            now = datetime.now()
            timestamps = [now + timedelta(hours=i) for i in range(10)]
            
        # Calculate direct effects on primary region
        response_effects = {brain_region: {}}
        
        for nt, effect_modifier in affected_neurotransmitters.items():
            # Calculate modified treatment effect for this neurotransmitter
            modified_effect = treatment_effect * effect_modifier
            
            # Get baseline level from receptor affinity
            baseline = 0.5 + (0.2 * self.analyze_receptor_affinity(nt, brain_region))
            
            # Calculate final effect considering baseline levels
            final_effect = modified_effect * baseline
            
            # Record the effect
            response_effects[brain_region][nt] = final_effect
            
        # Model the cascade effects from the primary region
        for primary_nt, effect in response_effects[brain_region].items():
            # Only cascade significant effects
            if abs(effect) > 0.1:
                # Calculate cascade effects starting from the primary region
                cascade = self.predict_cascade_effect(
                    starting_region=brain_region,
                    neurotransmitter=primary_nt,
                    effect_magnitude=effect,
                    max_depth=2  # Limit cascade depth for treatment simulation
                )
                
                # Merge cascade effects into our response
                for cascade_region, cascade_effects in cascade.items():
                    if cascade_region != brain_region:  # Skip the primary region as we've already recorded its direct effects
                        if cascade_region not in response_effects:
                            response_effects[cascade_region] = {}
                            
                        # Merge effects for this region
                        for cascade_nt, cascade_effect in cascade_effects.items():
                            if cascade_nt in response_effects[cascade_region]:
                                response_effects[cascade_region][cascade_nt] += cascade_effect
                            else:
                                response_effects[cascade_region][cascade_nt] = cascade_effect
        
        # Generate temporal sequences for each affected neurotransmitter
        # Start with an empty result
        sequences = {}
        
        # Process the highest-effect neurotransmitter first
        primary_nt = target_neurotransmitter
        if not primary_nt and affected_neurotransmitters:
            # Find the neurotransmitter with highest effect
            primary_nt = max(affected_neurotransmitters.items(), key=lambda x: abs(x[1]))[0]

        if primary_nt:
            # Generate sequence for the primary neurotransmitter
            primary_sequence = self.generate_temporal_sequence(
                brain_region=brain_region,
                neurotransmitter=primary_nt,
                timestamps=timestamps
            )
            sequences[primary_nt] = primary_sequence
            
            # Add metadata to indicate this is a treatment response
            primary_sequence.metadata["medication_name"] = medication_name
            primary_sequence.metadata["treatment_effect"] = treatment_effect
            primary_sequence.metadata["is_treatment_response"] = True
            
        # Add metadata to the response
        medication_metadata = {
            "medication_name": medication_name,
            "primary_region": brain_region.value,
            "treatment_strength": treatment_effect,
            "timestamp": datetime.now().isoformat()
        }
        
        # Create an event to track this treatment
        event_id = uuid.uuid4()
        self.events[event_id] = TemporalEvent(
            event_type="medication_effect",
            timestamp=datetime.now(),
            value=treatment_effect,
            metadata=medication_metadata
        )
        
        return sequences


def extend_neurotransmitter_mapping(base_mapping: NeurotransmitterMapping, patient_id: UUID | None = None) -> TemporalNeurotransmitterMapping:
    """
    Extends a base NeurotransmitterMapping with temporal capabilities.
    
    This function takes a base mapping and creates a new TemporalNeurotransmitterMapping
    that inherits all the receptor profiles and mappings from the base, but adds
    temporal analysis capabilities.
    
    Args:
        base_mapping: The base NeurotransmitterMapping to extend
        patient_id: Optional UUID of the associated patient
        
    Returns:
        A TemporalNeurotransmitterMapping with data copied from the base mapping
    """
    # Use base_mapping's patient_id if not specified
    if patient_id is None and hasattr(base_mapping, 'patient_id'):
        patient_id = base_mapping.patient_id
    
    # Create a new temporal mapping
    temporal_mapping = TemporalNeurotransmitterMapping(patient_id=patient_id)
    
    # Copy receptor profiles
    for profile in base_mapping.receptor_profiles:
        temporal_mapping.add_receptor_profile(profile)
    
    # Copy receptor maps (if not updated by add_receptor_profile)
    if hasattr(base_mapping, 'receptor_map') and hasattr(temporal_mapping, 'receptor_map'):
        for region, nt_map in base_mapping.receptor_map.items():
            if region not in temporal_mapping.receptor_map:
                temporal_mapping.receptor_map[region] = {}
            
            for nt, value in nt_map.items():
                temporal_mapping.receptor_map[region][nt] = value
    
    # Copy production sites
    if hasattr(base_mapping, 'production_sites'):
        for key, value in base_mapping.production_sites.items():
            temporal_mapping.production_sites[key] = value
    
    # Copy brain region connectivity if available
    if hasattr(base_mapping, 'brain_region_connectivity'):
        temporal_mapping.brain_region_connectivity = base_mapping.brain_region_connectivity
    
    return temporal_mapping