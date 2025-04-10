# Novamind Digital Twin Implementation Strategy

## Overview

This document outlines the implementation strategy for completing the Novamind Digital Twin Backend, specifically focusing on resolving test failures and implementing missing components to achieve 80%+ test coverage. It follows the Clean Architecture and SOLID principles while ensuring HIPAA compliance.

## Identified Issues

From test failures analysis, the following issues have been identified:

### 1. Domain Entity Implementation Gaps

#### Temporal Events System
- `CorrelatedEvent` class missing `event_type` attribute
- `EventChain` constructor doesn't accept `correlation_id` parameter
- Missing proper parent-child event relationship tracking

#### Temporal Sequence System
- `TemporalSequence` class missing `create` factory method
- Constructor parameter mismatch for feature_names, timestamps, values

#### Neurotransmitter Effect System
- `NeurotransmitterEffect` constructor missing `sample_size` parameter
- Missing `create` factory method for effect calculation from raw data

#### Temporal Neurotransmitter Mapping
- Implementation of `analyze_temporal_response` method missing
- `predict_cascade_effect` not propagating to other regions
- Data structure mismatch in `simulate_treatment_response`

### 2. Service Implementation Gaps

#### XGBoost Service
- `predict_treatment_response` method doesn't accept `patient_id` parameter
- Missing `analyze_treatment_interactions` method
- Missing encoding methods: `_encode_brain_region`, `_encode_neurotransmitter`

### 3. Infrastructure Configuration Issues

- SQLAlchemy model conflicts with `metadata` reserved keyword
- Asynchronous database driver configuration issues (`psycopg2` vs `asyncpg`)
- Python module naming conflicts with built-in modules

## Implementation Strategy

### 1. Core Domain Entity Implementation

The following domain entities will be implemented first as they form the foundation of the digital twin:

#### A. Temporal Events Framework

```python
# app/domain/entities/temporal_events.py
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Set

class CorrelatedEvent:
    """
    An event that can be correlated with other events in a causal chain.
    
    Attributes:
        id: Unique identifier for this event
        event_type: Type of the event (e.g., "medication_change", "symptom_report")
        correlation_id: ID that groups related events together
        parent_event_id: ID of the event that caused this one (if any)
        timestamp: When the event occurred
        metadata: Additional data about the event
    """
    
    def __init__(
        self,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[uuid.UUID] = None,
        parent_event_id: Optional[uuid.UUID] = None,
        timestamp: Optional[datetime] = None,
        id: Optional[uuid.UUID] = None
    ):
        self.id = id or uuid.uuid4()
        self.event_type = event_type
        self.correlation_id = correlation_id or uuid.uuid4()
        self.parent_event_id = parent_event_id
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    @classmethod
    def create_child_event(
        cls,
        parent_event: 'CorrelatedEvent',
        event_type: str,
        **kwargs
    ) -> 'CorrelatedEvent':
        """Create a new event that is a child of the specified parent event."""
        # Add all kwargs to metadata
        metadata = kwargs.copy()
        
        return cls(
            event_type=event_type,
            correlation_id=parent_event.correlation_id,
            parent_event_id=parent_event.id,
            metadata=metadata
        )

class EventChain:
    """
    A chain of causally related events.
    
    Allows tracking and analyzing sequences of related events.
    """
    
    def __init__(self, correlation_id: uuid.UUID):
        self.correlation_id = correlation_id
        self.events: List[CorrelatedEvent] = []
        
    def add_event(self, event: CorrelatedEvent) -> None:
        """Add an event to the chain, ensuring it has the correct correlation ID."""
        if event.correlation_id != self.correlation_id:
            raise ValueError(
                f"Event correlation ID {event.correlation_id} does not match "
                f"chain correlation ID {self.correlation_id}"
            )
        self.events.append(event)
        
    def get_root_event(self) -> Optional[CorrelatedEvent]:
        """Get the root event (event with no parent) in the chain."""
        for event in self.events:
            if event.parent_event_id is None:
                return event
        return None
    
    def get_child_events(self, parent_id: uuid.UUID) -> List[CorrelatedEvent]:
        """Get all events that have the specified event as their parent."""
        return [e for e in self.events if e.parent_event_id == parent_id]
    
    def get_event_by_id(self, event_id: uuid.UUID) -> Optional[CorrelatedEvent]:
        """Get an event by its ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        return None
    
    def get_events_by_type(self, event_type: str) -> List[CorrelatedEvent]:
        """Get all events of the specified type."""
        return [e for e in self.events if e.event_type == event_type]
    
    def build_event_tree(self) -> Dict[uuid.UUID, List[uuid.UUID]]:
        """
        Build a tree representation of the event chain.
        
        Returns a dictionary mapping parent event IDs to lists of their child event IDs.
        """
        tree: Dict[uuid.UUID, List[uuid.UUID]] = {}
        
        for event in self.events:
            if event.parent_event_id:
                # Add this event to its parent's children
                if event.parent_event_id not in tree:
                    tree[event.parent_event_id] = []
                tree[event.parent_event_id].append(event.id)
            else:
                # Root event may not have children yet
                if event.id not in tree:
                    tree[event.id] = []
                    
        return tree
```

#### B. Temporal Sequence Framework

```python
# app/domain/entities/temporal_sequence.py
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np

class TemporalSequence:
    """
    A sequence of multidimensional values over time.
    
    Attributes:
        sequence_id: Unique identifier for this sequence
        feature_names: Names of the features/dimensions
        timestamps: Ordered list of timestamps
        values: List of feature vectors, one per timestamp
        patient_id: ID of the patient this sequence belongs to
        metadata: Additional data about the sequence
    """
    
    def __init__(
        self,
        sequence_id: uuid.UUID,
        feature_names: List[str],
        timestamps: List[datetime],
        values: List[List[float]],
        patient_id: uuid.UUID,
        metadata: Optional[Dict[str, Any]] = None
    ):
        # Validate input
        if len(timestamps) != len(values):
            raise ValueError("Number of timestamps must match number of value vectors")
            
        if any(len(value_vec) != len(feature_names) for value_vec in values):
            raise ValueError("Each value vector must have the same number of features")
            
        self.sequence_id = sequence_id
        self.feature_names = feature_names
        self.timestamps = timestamps
        self.values = values
        self.patient_id = patient_id
        self.metadata = metadata or {}
        
    @property
    def sequence_length(self) -> int:
        """Get the length of the sequence (number of timestamps)."""
        return len(self.timestamps)
        
    @property
    def feature_dimension(self) -> int:
        """Get the dimension of each value vector (number of features)."""
        return len(self.feature_names)
    
    @classmethod
    def create(
        cls,
        feature_names: List[str],
        timestamps: List[datetime],
        values: List[List[float]],
        patient_id: uuid.UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'TemporalSequence':
        """
        Factory method to create a temporal sequence.
        
        Automatically generates a sequence_id.
        """
        return cls(
            sequence_id=uuid.uuid4(),
            feature_names=feature_names,
            timestamps=timestamps,
            values=values,
            patient_id=patient_id,
            metadata=metadata
        )
    
    def to_numpy_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert to input/output numpy arrays for machine learning.
        
        Returns:
            X: Input features array (all except last timestamp)
            y: Target outputs array (all except first timestamp)
        """
        # Convert values to numpy array
        values_array = np.array(self.values)
        
        # Input features are all but the last value
        X = values_array[:-1]
        
        # Targets are all but the first value
        y = values_array[1:]
        
        return X, y
    
    def to_padded_tensor(self, max_length: int) -> Dict[str, np.ndarray]:
        """
        Convert to a padded tensor representation.
        
        Args:
            max_length: Maximum sequence length to pad to
            
        Returns:
            Dictionary with:
                - values: Padded values array
                - mask: Boolean mask indicating valid entries
                - seq_len: Actual sequence length
        """
        # Create the values array padded to max_length
        padded_values = np.zeros((max_length, self.feature_dimension))
        mask = np.zeros(max_length, dtype=bool)
        
        # Fill with actual values up to sequence_length
        actual_length = min(self.sequence_length, max_length)
        padded_values[:actual_length] = self.values[:actual_length]
        mask[:actual_length] = True
        
        return {
            "values": padded_values,
            "mask": mask,
            "seq_len": self.sequence_length
        }
    
    def extract_subsequence(self, start_idx: int, end_idx: int) -> 'TemporalSequence':
        """
        Extract a subsequence from this sequence.
        
        Args:
            start_idx: Start index (inclusive)
            end_idx: End index (exclusive)
            
        Returns:
            A new TemporalSequence containing the subsequence
        """
        return TemporalSequence(
            sequence_id=uuid.uuid4(),
            feature_names=self.feature_names,
            timestamps=self.timestamps[start_idx:end_idx],
            values=self.values[start_idx:end_idx],
            patient_id=self.patient_id,
            metadata=self.metadata.copy()
        )
    
    def get_feature_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistics for each feature in the sequence.
        
        Returns:
            Dictionary mapping feature names to their statistics
        """
        result = {}
        
        # Convert to numpy for easier computation
        values_array = np.array(self.values)
        
        for i, feature_name in enumerate(self.feature_names):
            feature_values = values_array[:, i]
            
            result[feature_name] = {
                "min": float(np.min(feature_values)),
                "max": float(np.max(feature_values)),
                "mean": float(np.mean(feature_values)),
                "std": float(np.std(feature_values)),
                "median": float(np.median(feature_values))
            }
            
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the sequence to a dictionary representation.
        
        Returns:
            Dictionary representation of the sequence
        """
        return {
            "sequence_id": str(self.sequence_id),
            "patient_id": str(self.patient_id),
            "feature_names": self.feature_names,
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "values": self.values,
            "sequence_length": self.sequence_length,
            "feature_dimension": self.feature_dimension,
            "metadata": self.metadata
        }
```

#### C. Neurotransmitter Effect Framework

```python
# app/domain/entities/neurotransmitter_effect.py
from typing import Dict, Any, Tuple, List, Optional, Union
import uuid
import numpy as np
from scipy import stats

from app.domain.entities.digital_twin_enums import (
    Neurotransmitter, 
    ClinicalSignificance
)

class NeurotransmitterEffect:
    """
    Represents the measured or predicted effect on a neurotransmitter system.
    
    Captures the statistical properties of an observed neurotransmitter effect,
    including effect size, confidence intervals, and clinical significance.
    """
    
    def __init__(
        self,
        neurotransmitter: Neurotransmitter,
        effect_size: float,
        confidence_interval: Tuple[float, float],
        p_value: float,
        sample_size: int,
        clinical_significance: ClinicalSignificance
    ):
        # Validate inputs
        if not (0 <= p_value <= 1):
            raise ValueError(f"p_value must be between 0 and 1, got {p_value}")
            
        if confidence_interval[0] > confidence_interval[1]:
            raise ValueError(
                f"Confidence interval lower bound must be less than upper bound, "
                f"got {confidence_interval}"
            )
            
        self.neurotransmitter = neurotransmitter
        self.effect_size = effect_size
        self.confidence_interval = confidence_interval
        self.p_value = p_value
        self.sample_size = sample_size
        self.clinical_significance = clinical_significance
        
    @property
    def is_statistically_significant(self) -> bool:
        """Whether the effect is statistically significant (p < 0.05)."""
        return self.p_value < 0.05
        
    @property
    def precision(self) -> float:
        """
        The precision of the effect measurement.
        
        Calculated as 1 / (confidence interval width).
        """
        ci_width = self.confidence_interval[1] - self.confidence_interval[0]
        return 1.0 / ci_width if ci_width > 0 else float('inf')
        
    @property
    def effect_magnitude(self) -> str:
        """
        The magnitude category of the effect.
        
        Returns 'large', 'medium', 'small', or 'negligible' based on Cohen's d thresholds.
        """
        abs_effect = abs(self.effect_size)
        
        if abs_effect >= 0.8:
            return "large"
        elif abs_effect >= 0.5:
            return "medium"
        elif abs_effect >= 0.2:
            return "small"
        else:
            return "negligible"
            
    @property
    def direction(self) -> str:
        """The direction of the effect ('increase', 'decrease', or 'no change')."""
        if self.effect_size > 0.1:
            return "increase"
        elif self.effect_size < -0.1:
            return "decrease"
        else:
            return "no change"
            
    @classmethod
    def create(
        cls,
        neurotransmitter: Neurotransmitter,
        raw_data: List[float],
        baseline_data: List[float],
        clinical_significance: ClinicalSignificance
    ) -> 'NeurotransmitterEffect':
        """
        Factory method to create an effect from raw measurement data.
        
        Automatically calculates effect size, p-value, and confidence interval.
        
        Args:
            neurotransmitter: The neurotransmitter being measured
            raw_data: The intervention measurements
            baseline_data: The baseline measurements
            clinical_significance: Clinician-assessed significance
            
        Returns:
            A new NeurotransmitterEffect instance
        """
        # Calculate effect size (Cohen's d)
        mean1 = np.mean(raw_data)
        mean2 = np.mean(baseline_data)
        std1 = np.std(raw_data, ddof=1)
        std2 = np.std(baseline_data, ddof=1)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((len(raw_data) - 1) * std1**2 + 
                             (len(baseline_data) - 1) * std2**2) / 
                            (len(raw_data) + len(baseline_data) - 2))
        
        # Effect size
        effect_size = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
        
        # Calculate p-value using t-test
        t_stat, p_value = stats.ttest_ind(raw_data, baseline_data, equal_var=False)
        
        # Calculate confidence interval for effect size
        # Using approximation from Hedges & Olkin
        se = np.sqrt((len(raw_data) + len(baseline_data)) / 
                     (len(raw_data) * len(baseline_data)) + 
                     effect_size**2 / (2 * (len(raw_data) + len(baseline_data))))
        
        ci_lower = effect_size - 1.96 * se
        ci_upper = effect_size + 1.96 * se
        
        return cls(
            neurotransmitter=neurotransmitter,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper),
            p_value=p_value,
            sample_size=len(raw_data) + len(baseline_data),
            clinical_significance=clinical_significance
        )
        
    def to_visualization_data(self) -> Dict[str, Any]:
        """
        Convert to a format suitable for visualization.
        
        Returns:
            Dictionary with visualization-friendly data
        """
        return {
            "neurotransmitter": self.neurotransmitter.value.lower(),
            "effect_size": self.effect_size,
            "confidence_interval": self.confidence_interval,
            "p_value": self.p_value,
            "is_significant": self.is_statistically_significant,
            "effect_magnitude": self.effect_magnitude,
            "direction": self.direction,
            "clinical_significance": self.clinical_significance.value.lower(),
            "sample_size": self.sample_size
        }
```

### 2. Service Implementations

#### XGBoost Service Implementation

```python
# app/domain/services/enhanced_xgboost_service.py
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from datetime import datetime, timedelta
import xgboost as xgb
import hashlib

from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter

class EnhancedXGBoostService:
    """
    Enhanced XGBoost service for neurotransmitter response prediction.
    
    Uses advanced machine learning techniques to model and predict:
    - Treatment responses in different brain regions
    - Interactions between multiple neurotransmitter systems
    - Personalized response patterns based on patient history
    """
    
    def __init__(self):
        """Initialize the service with pre-trained models or create new ones."""
        # In a real implementation, we would load pre-trained models
        # For test purposes, we'll create synthetic prediction models
        self._init_prediction_models()
        
        # Embedding mappings for categorical variables
        self._brain_region_embeddings = self._create_brain_region_embeddings()
        self._neurotransmitter_embeddings = self._create_neurotransmitter_embeddings()
        
        # Patient-specific calibration data
        self._patient_calibration = {}
        
    def _init_prediction_models(self):
        """Initialize prediction models for different scenarios."""
        # In a real implementation, these would be actual XGBoost models
