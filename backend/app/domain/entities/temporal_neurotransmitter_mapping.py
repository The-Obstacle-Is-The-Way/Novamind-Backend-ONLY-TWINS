"""
Temporal neurotransmitter mapping module for the Temporal Neurotransmitter System.

This module defines the core classes that map neurotransmitter activity across brain regions
over time, including mechanisms for modeling cascading effects and treatment responses.
"""
import math
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any
from uuid import UUID

from app.domain.entities.digital_twin_enums import (
    BrainRegion,
    ClinicalSignificance,
    Neurotransmitter,
)
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.neurotransmitter_mapping import (
    NeurotransmitterMapping,
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
        self.cascade_patterns: dict[Neurotransmitter, dict[BrainRegion, TransmissionPattern]] = {}
        
        # Initialize temporal profiles
        self.temporal_profiles: dict[tuple[BrainRegion, Neurotransmitter], dict[str, Any]] = {}
        
        # Initialize with default patterns
        self._initialize_default_patterns()
    
    def _initialize_default_patterns(self) -> None:
        """Initialize default transmission patterns for common neurotransmitters."""
        # Serotonin - generally inhibitory, acts sequentially
        serotonin_patterns = {
            BrainRegion.RAPHE_NUCLEI: TransmissionPattern.SEQUENTIAL,
            BrainRegion.PREFRONTAL_CORTEX: TransmissionPattern.FEEDBACK,
            BrainRegion.AMYGDALA: TransmissionPattern.FEEDFORWARD,
            BrainRegion.HIPPOCAMPUS: TransmissionPattern.OSCILLATORY
        }
        
        # Dopamine - reward system, parallel activation
        dopamine_patterns = {
            BrainRegion.VENTRAL_TEGMENTAL_AREA: TransmissionPattern.PARALLEL,
            BrainRegion.NUCLEUS_ACCUMBENS: TransmissionPattern.FEEDFORWARD,
            BrainRegion.PREFRONTAL_CORTEX: TransmissionPattern.FEEDBACK,
            BrainRegion.STRIATUM: TransmissionPattern.SEQUENTIAL
        }
        
        # GABA - inhibitory, often feedback
        gaba_patterns = {
            BrainRegion.PREFRONTAL_CORTEX: TransmissionPattern.FEEDBACK,
            BrainRegion.AMYGDALA: TransmissionPattern.INHIBITORY,
            BrainRegion.STRIATUM: TransmissionPattern.OSCILLATORY
        }
        
        # Glutamate - excitatory, often feedforward
        glutamate_patterns = {
            BrainRegion.PREFRONTAL_CORTEX: TransmissionPattern.FEEDFORWARD,
            BrainRegion.AMYGDALA: TransmissionPattern.PARALLEL,
            BrainRegion.HIPPOCAMPUS: TransmissionPattern.SEQUENTIAL
        }
        
        # Store patterns
        self.cascade_patterns[Neurotransmitter.SEROTONIN] = serotonin_patterns
        self.cascade_patterns[Neurotransmitter.DOPAMINE] = dopamine_patterns
        self.cascade_patterns[Neurotransmitter.GABA] = gaba_patterns
        self.cascade_patterns[Neurotransmitter.GLUTAMATE] = glutamate_patterns
    
    def _initialize_temporal_profiles(self) -> None:
        """
        Initialize temporal profiles for common neurotransmitter-region combinations.
        
        This creates default temporal profiles that describe how neurotransmitter levels
        typically change over time in different brain regions.
        """
        # Create default profiles for all region-neurotransmitter pairs
        for region in BrainRegion:
            for nt in Neurotransmitter:
                # Skip combinations that don't make sense biologically
                if not self._is_valid_region_nt_combination(region, nt):
                    continue
                
                # Calculate baseline metrics
                baseline_receptor_affinity = self.analyze_receptor_affinity(nt, region)
                is_producing_region = region in self.get_producing_regions(nt)
                
                # Determine temporal characteristics based on neurotransmitter type
                if nt == Neurotransmitter.SEROTONIN:
                    # Serotonin tends to have slower, more stable dynamics
                    temporal_profile = {
                        "baseline_level": 0.5 + (0.2 * baseline_receptor_affinity),
                        "variance": 0.05 + (0.05 * (1.0 - baseline_receptor_affinity)),
                        "response_delay": 3.0,  # Days for significant level changes
                        "oscillation_frequency": 0.2,  # Low frequency oscillations
                        "treatment_sensitivity": 0.8 if region == BrainRegion.RAPHE_NUCLEI else 0.5,
                        "is_producing_region": is_producing_region,
                        "pattern": TransmissionPattern.SEQUENTIAL
                    }
                
                elif nt == Neurotransmitter.DOPAMINE:
                    # Dopamine can change more quickly with higher variance
                    temporal_profile = {
                        "baseline_level": 0.4 + (0.3 * baseline_receptor_affinity),
                        "variance": 0.1 + (0.1 * (1.0 - baseline_receptor_affinity)),
                        "response_delay": 1.0,  # Quicker response to stimuli
                        "oscillation_frequency": 0.5,  # Higher frequency
                        "treatment_sensitivity": 0.9 if region in [BrainRegion.VENTRAL_TEGMENTAL_AREA, BrainRegion.NUCLEUS_ACCUMBENS] else 0.6,
                        "is_producing_region": is_producing_region,
                        "pattern": TransmissionPattern.PARALLEL if is_producing_region else TransmissionPattern.FEEDFORWARD
                    }
                
                elif nt == Neurotransmitter.GABA:
                    # GABA as an inhibitory neurotransmitter
                    temporal_profile = {
                        "baseline_level": 0.6,  # Higher baseline for inhibitory balance
                        "variance": 0.05,  # Low variance - more stable regulation
                        "response_delay": 0.5,  # Fast response for inhibition
                        "oscillation_frequency": 0.8,  # High frequency for quick regulation
                        "treatment_sensitivity": 0.7,
                        "is_producing_region": is_producing_region,
                        "pattern": TransmissionPattern.INHIBITORY
                    }
                
                elif nt == Neurotransmitter.GLUTAMATE:
                    # Glutamate as the main excitatory neurotransmitter
                    temporal_profile = {
                        "baseline_level": 0.5,
                        "variance": 0.1,  # Moderate variance
                        "response_delay": 0.3,  # Very fast response
                        "oscillation_frequency": 0.9,  # High frequency
                        "treatment_sensitivity": 0.6,
                        "is_producing_region": is_producing_region,
                        "pattern": TransmissionPattern.FEEDFORWARD
                    }
                
                else:
                    # Default profile for other neurotransmitters
                    temporal_profile = {
                        "baseline_level": 0.5,
                        "variance": 0.1,
                        "response_delay": 1.0,
                        "oscillation_frequency": 0.5,
                        "treatment_sensitivity": 0.5,
                        "is_producing_region": is_producing_region,
                        "pattern": TransmissionPattern.SEQUENTIAL
                    }
                
                # Store the profile
                self.temporal_profiles[(region, nt)] = temporal_profile
    
    def _is_valid_region_nt_combination(self, region: BrainRegion, nt: Neurotransmitter) -> bool:
        """
        Determine if a brain region and neurotransmitter combination is biologically valid.
        
        Args:
            region: Brain region to check
            nt: Neurotransmitter to check
            
        Returns:
            True if the combination is valid, False otherwise
        """
        # Primary producing regions should always be valid
        if region in self.get_producing_regions(nt):
            return True
        
        # For simplicity, most combinations are valid with some exceptions:
        invalid_combinations = [
            # These are just examples - a real implementation would have 
            # more comprehensive biological constraints
            (BrainRegion.RAPHE_NUCLEI, Neurotransmitter.GLUTAMATE),
            (BrainRegion.VENTRAL_TEGMENTAL_AREA, Neurotransmitter.SEROTONIN)
        ]
        
        return (region, nt) not in invalid_combinations
    
    def analyze_temporal_pattern(
        self,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        time_range: timedelta = timedelta(days=30)
    ) -> dict[str, Any]:
        """
        Analyze the temporal pattern of a neurotransmitter in a region.
        
        Args:
            brain_region: Target brain region
            neurotransmitter: Target neurotransmitter
            time_range: Time period to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Get sequences for this region and neurotransmitter
        key = (brain_region, neurotransmitter)
        sequences = self.temporal_sequences.get(key, [])
        
        if not sequences:
            return {
                "pattern": "unknown",
                "confidence": 0.0,
                "rhythmicity": 0.0,
                "trend": "unknown",
                "variance": 0.0,
                "peak_count": 0,
                "event_count": 0
            }
        
        # Get most recent sequence
        sequence = sequences[-1]
        
        # Get events within time range
        cutoff = datetime.now() - time_range
        events = [e for e in sequence.events if e.timestamp >= cutoff]
        
        if not events:
            return {
                "pattern": "insufficient_data",
                "confidence": 0.0,
                "rhythmicity": 0.0,
                "trend": "unknown",
                "variance": 0.0,
                "peak_count": 0,
                "event_count": 0
            }
        
        # Get values
        values = [e.value for e in events if isinstance(e.value, (int, float))]
        
        if not values:
            return {
                "pattern": "non_numeric_data",
                "confidence": 0.0,
                "rhythmicity": 0.0,
                "trend": "unknown",
                "variance": 0.0,
                "peak_count": 0,
                "event_count": len(events)
            }
        
        # Calculate statistics
        mean_value = sum(values) / len(values)
        variance = sum((v - mean_value) ** 2 for v in values) / len(values)
        
        # Count peaks (local maxima)
        peaks = 0
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks += 1
        
        # Determine trend
        start_value = values[0]
        end_value = values[-1]
        
        if abs(end_value - start_value) / max(abs(start_value), 0.1) < 0.1:
            trend = "stable"
        elif end_value > start_value:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        # Calculate rhythmicity (regularity of peaks)
        rhythmicity = 0.0
        if peaks >= 2:
            peak_indices = []
            for i in range(1, len(values) - 1):
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    peak_indices.append(i)
            
            intervals = [peak_indices[i] - peak_indices[i-1] for i in range(1, len(peak_indices))]
            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                interval_variance = sum((i - mean_interval) ** 2 for i in intervals) / len(intervals)
                
                # Lower variance = higher rhythmicity
                max_possible_variance = mean_interval ** 2
                rhythmicity = 1.0 - min(1.0, interval_variance / max(max_possible_variance, 1.0))
        
        # Determine pattern
        pattern = "random"
        confidence = 0.5
        
        if rhythmicity > 0.7:
            pattern = "oscillatory"
            confidence = rhythmicity
        elif peaks == 0 and trend == "stable":
            pattern = "flat"
            confidence = 0.8
        elif trend == "increasing" and variance < 0.05:
            pattern = "linear_increase"
            confidence = 0.7
        elif trend == "decreasing" and variance < 0.05:
            pattern = "linear_decrease"
            confidence = 0.7
        elif variance > 0.2:
            pattern = "chaotic"
            confidence = min(1.0, variance / 0.5)
        
        return {
            "pattern": pattern,
            "confidence": confidence,
            "rhythmicity": rhythmicity,
            "trend": trend,
            "variance": variance,
            "peak_count": peaks,
            "event_count": len(events)
        }
    
    def analyze_region_interactions(
        self,
        neurotransmitter: Neurotransmitter,
        time_range: timedelta = timedelta(days=30),
        correlation_threshold: float = 0.6
    ) -> dict[tuple[BrainRegion, BrainRegion], float]:
        """
        Analyze interactions between brain regions for a neurotransmitter.
        
        Args:
            neurotransmitter: Target neurotransmitter
            time_range: Time period to analyze
            correlation_threshold: Minimum correlation coefficient to include
            
        Returns:
            Dictionary mapping region pairs to correlation strength
        """
        # Get all regions with sequences for this neurotransmitter
        regions_with_data = []
        for key in self.temporal_sequences:
            region, nt = key
            if nt == neurotransmitter and self.temporal_sequences[key]:
                regions_with_data.append(region)
        
        if len(regions_with_data) < 2:
            return {}
        
        # Analyze correlations between all pairs of regions
        correlations = {}
        for i, region1 in enumerate(regions_with_data):
            for j in range(i + 1, len(regions_with_data)):
                region2 = regions_with_data[j]
                
                # Get sequences
                seq1 = self.temporal_sequences.get((region1, neurotransmitter), [])
                seq2 = self.temporal_sequences.get((region2, neurotransmitter), [])
                
                if not seq1 or not seq2:
                    continue
                
                # Get most recent sequences
                seq1 = seq1[-1]
                seq2 = seq2[-1]
                
                # Get events within time range
                cutoff = datetime.now() - time_range
                events1 = [e for e in seq1.events if e.timestamp >= cutoff]
                events2 = [e for e in seq2.events if e.timestamp >= cutoff]
                
                if not events1 or not events2:
                    continue
                
                # Get values
                values1 = [e.value for e in events1 if isinstance(e.value, (int, float))]
                values2 = [e.value for e in events2 if isinstance(e.value, (int, float))]
                
                if not values1 or not values2:
                    continue
                
                # For simplicity, compare the latest 10 values from each
                values1 = values1[-10:]
                values2 = values2[-10:]
                
                # Truncate to same length if needed
                min_length = min(len(values1), len(values2))
                values1 = values1[-min_length:]
                values2 = values2[-min_length:]
                
                # Calculate correlation
                if min_length < 3:
                    continue
                
                # Simple correlation calculation
                mean1 = sum(values1) / len(values1)
                mean2 = sum(values2) / len(values2)
                
                # Calculate covariance and standard deviations
                covariance = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(min_length))
                std_dev1 = math.sqrt(sum((v - mean1) ** 2 for v in values1))
                std_dev2 = math.sqrt(sum((v - mean2) ** 2 for v in values2))
                
                # Calculate correlation coefficient
                if std_dev1 == 0 or std_dev2 == 0:
                    correlation = 0
                else:
                    correlation = covariance / (std_dev1 * std_dev2)
                
                # Only include strong correlations
                if abs(correlation) >= correlation_threshold:
                    correlations[(region1, region2)] = correlation
        
        return correlations
    
    def get_recent_sequences(
        self,
        days: int = 30
    ) -> dict[tuple[BrainRegion, Neurotransmitter], TemporalSequence]:
        """
        Get the most recent temporal sequences across all brain regions.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary mapping (region, neurotransmitter) to most recent sequence
        """
        cutoff = datetime.now() - timedelta(days=days)
        result = {}
        
        # Get most recent sequence for each region/neurotransmitter pair
        for key, sequences in self.temporal_sequences.items():
            if sequences:
                # Find most recent sequence updated after cutoff
                recent_sequences = [s for s in sequences if s.updated_at >= cutoff]
                if recent_sequences:
                    result[key] = max(recent_sequences, key=lambda s: s.updated_at)
        
        return result
    
    def generate_temporal_sequence(
        self,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        timestamps: list[datetime],
        baseline_level: float = 0.5,
        random_seed: int | None = None,
        patient_id: UUID | None = None
    ) -> TemporalSequence:
        """
        Generate a temporal sequence for a neurotransmitter in a specific brain region.
        
        Args:
            brain_region: Target brain region
            neurotransmitter: Target neurotransmitter
            timestamps: List of timestamps for the sequence
            baseline_level: Starting baseline level (0.0-1.0)
            random_seed: Optional random seed for reproducibility
            patient_id: Optional patient ID to override the default
            
        Returns:
            TemporalSequence with generated values
        """
        # Set random seed if provided
        if random_seed is not None:
            random.seed(random_seed)
        
        # Use provided patient_id or fall back to self.patient_id
        used_patient_id = patient_id if patient_id is not None else self.patient_id
        
        # Create a sequence
        sequence_name = f"{neurotransmitter.value}_{brain_region.value}_temporal"
        
        # Get receptor affinity to determine stability
        affinity = self.analyze_receptor_affinity(neurotransmitter, brain_region)
        
        # Higher affinity means more stable levels (less variance)
        variance = 0.15 * (1.0 - affinity)
        
        # Generate values for all neurotransmitters
        nt_count = len(list(Neurotransmitter))
        all_values = []
        
        # Set initial level
        current_level = baseline_level
        
        # Generate sequence for each timestamp
        for timestamp in timestamps:
            # Create array of values for all neurotransmitters
            values = [0.0] * nt_count
            
            # Add random variation to current level
            variation = random.uniform(-variance, variance)
            new_level = current_level + variation
            
            # Ensure level stays within valid range
            new_level = max(0.0, min(1.0, new_level))
            
            # Get index of current neurotransmitter
            nt_idx = list(Neurotransmitter).index(neurotransmitter)
            
            # Set value for current neurotransmitter
            values[nt_idx] = new_level
            
            # Set values for other neurotransmitters
            for idx, nt in enumerate(Neurotransmitter):
                if idx != nt_idx:
                    # Generate random correlation with main neurotransmitter
                    # Some neurotransmitters will have inverse correlation
                    if random.random() < 0.3:  # 30% chance of correlation
                        # Strong inverse correlation for opposing neurotransmitters
                        if (nt in [Neurotransmitter.GABA] and
                            neurotransmitter in [Neurotransmitter.GLUTAMATE]):
                            values[idx] = 1.0 - new_level + random.uniform(-0.1, 0.1)
                        # Strong positive correlation for related neurotransmitters
                        elif (nt in [Neurotransmitter.DOPAMINE] and
                              neurotransmitter in [Neurotransmitter.SEROTONIN]):
                            values[idx] = new_level + random.uniform(-0.1, 0.1)
                        else:
                            # Random level for unrelated neurotransmitters
                            values[idx] = random.uniform(0.2, 0.8)
                    else:
                        # Default level around 0.5 with some randomness
                        values[idx] = random.uniform(0.4, 0.6)
                    
                    # Ensure value stays within valid range
                    values[idx] = max(0.0, min(1.0, values[idx]))
            
            # Update current level for next iteration
            current_level = new_level
            
            # Add to values
            all_values.append(values)
        
        # Create the sequence with all the generated data
        feature_names = [nt.value for nt in Neurotransmitter]
        
        sequence = TemporalSequence[float](
            sequence_id=uuid.uuid4(),
            name=sequence_name,
            patient_id=used_patient_id,
            brain_region=brain_region,
            neurotransmitter=neurotransmitter,
            feature_names=feature_names,
            timestamps=timestamps,
            values=all_values,
            metadata={
                "generated": True,
                "baseline_level": baseline_level,
                "receptor_density": self.analyze_receptor_affinity(neurotransmitter, brain_region),
                "is_producing_region": brain_region in self.get_producing_regions(neurotransmitter),
                "brain_region": brain_region.value,
                "primary_neurotransmitter": neurotransmitter.value
            }
        )
        
        return sequence
    
    def predict_cascade_effect(
        self,
        starting_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        initial_level: float,
        time_steps: int = 5,
        step_duration: timedelta = timedelta(minutes=15),
        patient_id: UUID | None = None
    ) -> dict[BrainRegion, list[float]]:
        """
        Predict how a neurotransmitter change cascades across brain regions.
        
        Args:
            starting_region: Region where the change begins
            neurotransmitter: Target neurotransmitter
            initial_level: Initial level in the starting region
            time_steps: Number of time steps to simulate
            step_duration: Duration of each time step
            patient_id: Optional patient ID to override the default
            
        Returns:
            Dictionary mapping brain regions to lists of levels over time
        """
        # Initialize results dictionary
        cascade_results: dict[BrainRegion, list[float]] = {}
        
        # Set initial level for starting region
        cascade_results[starting_region] = [initial_level]
        
        # Get brain region connectivity for cascade
        # This simplifies the complex connectivity in the brain
        # In a real implementation, this would be based on actual neural pathways
        connectivity = {
            BrainRegion.PREFRONTAL_CORTEX: [
                (BrainRegion.ANTERIOR_CINGULATE_CORTEX, 0.8),
                (BrainRegion.STRIATUM, 0.7),
                (BrainRegion.AMYGDALA, 0.5),
                (BrainRegion.HIPPOCAMPUS, 0.4)
            ],
            BrainRegion.AMYGDALA: [
                (BrainRegion.HIPPOCAMPUS, 0.7),
                (BrainRegion.HYPOTHALAMUS, 0.6),
                (BrainRegion.PREFRONTAL_CORTEX, 0.5)
            ],
            BrainRegion.HIPPOCAMPUS: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.6),
                (BrainRegion.AMYGDALA, 0.5)
            ],
            BrainRegion.NUCLEUS_ACCUMBENS: [
                (BrainRegion.VENTRAL_TEGMENTAL_AREA, 0.8),
                (BrainRegion.PREFRONTAL_CORTEX, 0.6)
            ],
            BrainRegion.VENTRAL_TEGMENTAL_AREA: [
                (BrainRegion.NUCLEUS_ACCUMBENS, 0.9),
                (BrainRegion.PREFRONTAL_CORTEX, 0.5)
            ],
            BrainRegion.RAPHE_NUCLEI: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.7),
                (BrainRegion.HIPPOCAMPUS, 0.6),
                (BrainRegion.AMYGDALA, 0.5)
            ],
            BrainRegion.LOCUS_COERULEUS: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.8),
                (BrainRegion.AMYGDALA, 0.7),
                (BrainRegion.HIPPOCAMPUS, 0.5)
            ],
            BrainRegion.STRIATUM: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.7),
                (BrainRegion.NUCLEUS_ACCUMBENS, 0.6)
            ]
        }
        
        # Set all other regions to a small initial level (not zero)
        # This ensures there's always some baseline activity to start with
        for region in BrainRegion:
            if region != starting_region:
                # Small initial level that varies by proximity to starting region
                if region in [r for r, _ in connectivity.get(starting_region, [])]:
                    # Direct connection gets higher initial value
                    cascade_results[region] = [0.1]
                else:
                    # Indirect connections get smaller initial value
                    cascade_results[region] = [0.05]
        
        # Get brain region connectivity for cascade
        # This simplifies the complex connectivity in the brain
        # In a real implementation, this would be based on actual neural pathways
        connectivity = {
            BrainRegion.PREFRONTAL_CORTEX: [
                (BrainRegion.ANTERIOR_CINGULATE_CORTEX, 0.8),
                (BrainRegion.STRIATUM, 0.7),
                (BrainRegion.AMYGDALA, 0.5),
                (BrainRegion.HIPPOCAMPUS, 0.4)
            ],
            BrainRegion.AMYGDALA: [
                (BrainRegion.HIPPOCAMPUS, 0.7),
                (BrainRegion.HYPOTHALAMUS, 0.6),
                (BrainRegion.PREFRONTAL_CORTEX, 0.5)
            ],
            BrainRegion.HIPPOCAMPUS: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.6),
                (BrainRegion.AMYGDALA, 0.5)
            ],
            BrainRegion.NUCLEUS_ACCUMBENS: [
                (BrainRegion.VENTRAL_TEGMENTAL_AREA, 0.8),
                (BrainRegion.PREFRONTAL_CORTEX, 0.6)
            ],
            BrainRegion.VENTRAL_TEGMENTAL_AREA: [
                (BrainRegion.NUCLEUS_ACCUMBENS, 0.9),
                (BrainRegion.PREFRONTAL_CORTEX, 0.5)
            ],
            BrainRegion.RAPHE_NUCLEI: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.7),
                (BrainRegion.HIPPOCAMPUS, 0.6),
                (BrainRegion.AMYGDALA, 0.5)
            ],
            BrainRegion.LOCUS_COERULEUS: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.8),
                (BrainRegion.AMYGDALA, 0.7),
                (BrainRegion.HIPPOCAMPUS, 0.5)
            ],
            BrainRegion.STRIATUM: [
                (BrainRegion.PREFRONTAL_CORTEX, 0.7),
                (BrainRegion.NUCLEUS_ACCUMBENS, 0.6)
            ]
        }
        
        # Simulate cascade over time steps
        for step in range(1, time_steps):
            # For each region, calculate new level based on connected regions
            new_levels = {}
            
            for region in BrainRegion:
                # Skip regions not in connectivity map
                if region not in connectivity:
                    # Maintain previous level
                    new_levels[region] = cascade_results[region][-1]
                    continue
                
                # Get connections for this region
                connections = connectivity.get(region, [])
                
                # Get current level
                current_level = cascade_results[region][-1]
                
                # Calculate influence from connected regions
                total_influence = 0.0
                total_weight = 0.0
                
                for connected_region, strength in connections:
                    # Get level in connected region from previous time step
                    if step - 1 < len(cascade_results[connected_region]):
                        connected_level = cascade_results[connected_region][step - 1]
                        
                        # Apply receptor affinity as a modifier
                        receptor_factor = self.analyze_receptor_affinity(neurotransmitter, connected_region)
                        
                        # Calculate influence
                        influence = connected_level * strength * receptor_factor
                        total_influence += influence
                        total_weight += strength * receptor_factor
                
                # Calculate new level
                if total_weight > 0:
                    # Average influence from connected regions
                    influence_level = total_influence / total_weight
                    
                    # Blend with current level
                    decay_factor = 0.7  # How much previous level persists
                    propagation_factor = 0.3  # How much new influence affects level
                    
                    # For the starting region, apply a slower decay
                    if region == starting_region:
                        decay_factor = 0.9
                        propagation_factor = 0.1
                    
                    new_level = (current_level * decay_factor) + (influence_level * propagation_factor)
                else:
                    # If no connections, apply decay
                    new_level = current_level * 0.9
                
                # Ensure level stays within valid range
                new_level = max(0.0, min(1.0, new_level))
                
                # Store new level
                new_levels[region] = new_level
            
            # Update cascade results with new levels
            for region, level in new_levels.items():
                cascade_results[region].append(level)
        
        return cascade_results
    
    def simulate_treatment_response(
        self,
        brain_region: BrainRegion,
        target_neurotransmitter: Neurotransmitter,
        treatment_effect: float,
        timestamps: list[datetime],
        patient_id: UUID | None = None
    ) -> dict[Neurotransmitter, TemporalSequence]:
        """
        Simulate the response to a treatment affecting a specific neurotransmitter.
        
        Args:
            brain_region: Target brain region
            target_neurotransmitter: Primary neurotransmitter affected by treatment
            treatment_effect: Magnitude and direction of effect (-1.0 to 1.0)
            timestamps: List of timestamps for the simulation
            patient_id: Optional patient ID to override the default
            
        Returns:
            Dictionary mapping neurotransmitters to their temporal sequences
        """
        # Use provided patient_id or fall back to self.patient_id
        used_patient_id = patient_id if patient_id is not None else self.patient_id
        
        # Create result dictionary
        result = {}
        
        # Get affected neurotransmitters (primary + secondary effects)
        affected_neurotransmitters = self._get_treatment_affected_neurotransmitters(
            target_neurotransmitter, treatment_effect
        )
        
        # Simulate effect on each neurotransmitter
        for nt, effect_modifier in affected_neurotransmitters.items():
            # Calculate modified treatment effect for this neurotransmitter
            modified_effect = treatment_effect * effect_modifier
            
            # Get baseline level from receptor affinity
            baseline = 0.5 + (0.2 * self.analyze_receptor_affinity(nt, brain_region))
            
            # Ensure baseline is valid
            baseline = max(0.1, min(0.9, baseline))
            
            # Create sequence for this neurotransmitter
            sequence = self.generate_temporal_sequence(
                brain_region=brain_region,
                neurotransmitter=nt,
                timestamps=timestamps,
                baseline_level=baseline,
                patient_id=used_patient_id
            )
            
            # Apply treatment effect to sequence
            _apply_treatment_effect(sequence, modified_effect, timestamps)
            
            # Add to result
            result[nt] = sequence
        
        return result
    
    def analyze_temporal_response(
        self,
        patient_id: UUID,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        time_series_data: list[tuple[datetime, float]],
        baseline_period: tuple[datetime, datetime]
    ) -> NeurotransmitterEffect:
        """
        Analyze a temporal response to detect effects on neurotransmitter levels.
        
        Args:
            patient_id: The patient's unique identifier
            brain_region: The brain region being analyzed
            neurotransmitter: The neurotransmitter being analyzed
            time_series_data: List of (timestamp, value) tuples representing measurements
            baseline_period: (start, end) timestamps defining the baseline period
            
        Returns:
            A NeurotransmitterEffect capturing the statistical properties of the effect
        """
        # Split data into baseline and intervention periods
        baseline_data = []
        intervention_data = []
        
        # Sort data by timestamp to ensure chronological order
        sorted_data = sorted(time_series_data, key=lambda x: x[0])
        
        # Extract baseline period (timestamps within baseline_period)
        for timestamp, value in sorted_data:
            if baseline_period[0] <= timestamp <= baseline_period[1]:
                baseline_data.append(value)
            elif timestamp > baseline_period[1]:
                intervention_data.append(value)
        
        # Ensure we have enough data for statistical analysis
        if len(baseline_data) < 2 or len(intervention_data) < 2:
            raise ValueError(
                "Insufficient data for analysis. Need at least 2 points in baseline and intervention periods."
            )
            
        # Estimate clinical significance based on effect magnitude
        effect_magnitude = self._estimate_effect_magnitude(baseline_data, intervention_data)
        
        # Create NeurotransmitterEffect using factory method
        effect = NeurotransmitterEffect.create(
            neurotransmitter=neurotransmitter,
            raw_data=intervention_data,
            baseline_data=baseline_data,
            clinical_significance=effect_magnitude
        )
        
        return effect
    
    def _estimate_effect_magnitude(
        self,
        baseline_data: list[float],
        intervention_data: list[float]
    ) -> ClinicalSignificance:
        """Estimate clinical significance based on data differences."""
        baseline_mean = sum(baseline_data) / len(baseline_data)
        intervention_mean = sum(intervention_data) / len(intervention_data)
        
        # Calculate percent change
        if baseline_mean > 0:
            percent_change = abs((intervention_mean - baseline_mean) / baseline_mean)
        else:
            percent_change = abs(intervention_mean - baseline_mean)
            
        # Assign clinical significance based on percent change
        if percent_change > 0.5:
            return ClinicalSignificance.SIGNIFICANT
        elif percent_change > 0.3:
            return ClinicalSignificance.MODERATE
        elif percent_change > 0.1:
            return ClinicalSignificance.MILD
        else:
            return ClinicalSignificance.MINIMAL
            
    def _get_treatment_affected_neurotransmitters(
        self, primary_nt: Neurotransmitter, effect_strength: float
    ) -> dict[Neurotransmitter, float]:
        """
        Determine which neurotransmitters are affected by a treatment.
        
        Args:
            primary_nt: Primary neurotransmitter targeted by treatment
            effect_strength: Strength of treatment effect (-1.0 to 1.0)
            
        Returns:
            Dictionary mapping affected neurotransmitters to effect modifiers
        """
        result = {primary_nt: 1.0}  # Primary effect at full strength
        
        # Add secondary effects based on primary neurotransmitter
        if primary_nt == Neurotransmitter.SEROTONIN:
            # SSRI-like effects: Secondary effects on other monoamines
            result[Neurotransmitter.DOPAMINE] = 0.3
            result[Neurotransmitter.NOREPINEPHRINE] = 0.2
            
            # Indirect effect on inhibitory/excitatory balance
            if effect_strength > 0:  # Increasing serotonin
                result[Neurotransmitter.GABA] = 0.1
                result[Neurotransmitter.GLUTAMATE] = -0.1
            else:  # Decreasing serotonin
                result[Neurotransmitter.GABA] = -0.1
                result[Neurotransmitter.GLUTAMATE] = 0.2
        
        elif primary_nt == Neurotransmitter.DOPAMINE:
            # Dopaminergic effects: Secondary effects on related systems
            result[Neurotransmitter.NOREPINEPHRINE] = 0.4
            
            # Indirect effects on serotonin depend on direction
            if effect_strength > 0:  # Increasing dopamine
                result[Neurotransmitter.SEROTONIN] = 0.1
                result[Neurotransmitter.GLUTAMATE] = 0.2
            else:  # Decreasing dopamine
                result[Neurotransmitter.SEROTONIN] = -0.1
                result[Neurotransmitter.GLUTAMATE] = -0.1
        
        elif primary_nt == Neurotransmitter.GABA:
            # GABAergic effects: Inhibitory system changes
            result[Neurotransmitter.GLUTAMATE] = -0.5  # Strong reciprocal relationship
            
            # Secondary effects on monoamines
            if effect_strength > 0:  # Increasing GABA (more inhibition)
                result[Neurotransmitter.DOPAMINE] = -0.2
                result[Neurotransmitter.SEROTONIN] = 0.1
            else:  # Decreasing GABA (less inhibition)
                result[Neurotransmitter.DOPAMINE] = 0.3
                result[Neurotransmitter.GLUTAMATE] = 0.4
        
        elif primary_nt == Neurotransmitter.GLUTAMATE:
            # Glutamatergic effects: Excitatory system changes
            result[Neurotransmitter.GABA] = -0.4  # Reciprocal relationship
            
            # Secondary effects on other systems
            if effect_strength > 0:  # Increasing glutamate
                result[Neurotransmitter.DOPAMINE] = 0.2
                result[Neurotransmitter.SEROTONIN] = -0.1
            else:  # Decreasing glutamate
                result[Neurotransmitter.DOPAMINE] = -0.1
                result[Neurotransmitter.SEROTONIN] = 0.1
        
        return result
    
    def __str__(self) -> str:
        """String representation of the mapping."""
        return f"TemporalNeurotransmitterMapping(patient_id={self.patient_id}, sequences={len(self.temporal_sequences)})"


def _apply_treatment_effect(
    sequence: TemporalSequence,
    effect: float,
    timestamps: list[datetime]
) -> None:
    """
    Apply treatment effect to a temporal sequence.
    
    Args:
        sequence: Sequence to modify
        effect: Treatment effect (-1.0 to 1.0)
        timestamps: Timestamps when treatment is applied
    """
    if not sequence or not timestamps:
        return
    
    # Skip if effect is negligible
    if abs(effect) < 0.05:
        return
    
    # Get maximum effect (change in neurotransmitter level)
    max_effect = effect * 0.4  # Scale to reasonable range
    
    # Apply gradual effect over time
    treatment_start = timestamps[0]
    treatment_duration = timestamps[-1] - treatment_start
    total_days = treatment_duration.total_seconds() / (24 * 3600)
    
    # No effect if duration is too short
    if total_days < 0.5:
        return
    
    # Calculate onset delay based on effect size
    # Larger effects may take longer to manifest
    onset_days = 1.0 + (abs(effect) * 2.0)
    onset_days = min(onset_days, total_days / 2)  # Can't be more than half the duration
    # Get the index of the target neurotransmitter
    if sequence.neurotransmitter:
        nt_idx = list(Neurotransmitter).index(sequence.neurotransmitter)
    else:
        # If no specific neurotransmitter is set, assume we're modifying all values
        nt_idx = None
    
    # Iterate through timestamps and values
    for i, (timestamp, values) in enumerate(zip(sequence.timestamps, sequence.values)):
        # Skip timestamps outside treatment timeframe
        if timestamp < treatment_start or timestamp > timestamps[-1]:
            continue
        
        # Calculate days since treatment start
        days_since_start = (timestamp - treatment_start).total_seconds() / (24 * 3600)
        
        # Calculate effect factor based on time (sigmoid curve)
        if days_since_start < onset_days:
            # Gradual onset phase
            factor = days_since_start / onset_days
            effect_factor = factor ** 2  # Quadratic ramp-up
        else:
            # Full effect phase with slight random variation
            effect_factor = 1.0 + (random.uniform(-0.1, 0.1) * (1.0 - (days_since_start / total_days)))
        
        # Apply effect to values
        effect_amount = max_effect * effect_factor
        
        if nt_idx is not None:
            # Modify only the target neurotransmitter
            sequence.values[i][nt_idx] += effect_amount
        else:
            # Modify all values
            for j in range(len(values)):
                sequence.values[i][j] += effect_amount
            new_value = current_value + effect_amount
            
            # Ensure value stays within valid range
            new_value = max(0.0, min(1.0, new_value))
            
            # Update metadata to track treatment effect
            event_metadata = event.metadata or {}
            event_metadata["treatment_effect"] = effect_amount
            event_metadata["original_value"] = current_value
            
            # Update event value and metadata
            event.value = new_value
            event.metadata = event_metadata


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
    
    return temporal_mapping