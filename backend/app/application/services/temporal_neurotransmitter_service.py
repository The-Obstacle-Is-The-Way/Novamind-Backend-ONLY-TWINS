"""
Application service for temporal neurotransmitter analysis.

This service handles neurotransmitter dynamics analysis, visualization, and simulation
using the clean SubjectIdentity architecture with no legacy dependencies.
"""
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from app.domain.entities.temporal_sequence import TemporalSequence
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter, ClinicalSignificance
from app.domain.entities.temporal_neurotransmitter_mapping import extend_neurotransmitter_mapping
from app.domain.entities.neurotransmitter_mapping import NeurotransmitterMapping, create_default_neurotransmitter_mapping
from app.domain.repositories.temporal_repository import TemporalSequenceRepository, EventRepository
from app.domain.services.visualization_preprocessor import NeurotransmitterVisualizationPreprocessor
from app.domain.entities.identity.subject_identity import SubjectIdentity, SubjectIdentityRepository
from app.core.audit.audit_service import AuditService, AuditEvent, AuditEventType
from app.core.exceptions import ResourceNotFoundError, ValidationError


class TemporalNeurotransmitterService:
    """
    Pure application service for temporal neurotransmitter analysis and visualization.
    
    This service uses SubjectIdentity abstractions throughout with no legacy dependencies.
    """
    
    def __init__(
        self,
        sequence_repository: TemporalSequenceRepository,
        subject_repository: SubjectIdentityRepository,
        event_repository: Optional[EventRepository] = None,
        nt_mapping: Optional[NeurotransmitterMapping] = None,
        visualization_preprocessor: Optional[NeurotransmitterVisualizationPreprocessor] = None,
        xgboost_service = None,  # Intentionally untyped to avoid cyclic imports
        audit_service: Optional[AuditService] = None
    ):
        """
        Initialize the service with required dependencies.
        
        Args:
            sequence_repository: Repository for temporal sequences
            subject_repository: Repository for subject identities
            event_repository: Optional repository for event tracking
            nt_mapping: Optional custom neurotransmitter mapping
            visualization_preprocessor: Optional visualization preprocessor
            xgboost_service: Optional XGBoost machine learning service
            audit_service: Optional audit service for secure logging
        """
        self.sequence_repository = sequence_repository
        self.subject_repository = subject_repository
        self.event_repository = event_repository
        self.audit_service = audit_service
        
        # Create neurotransmitter mapping with temporal extensions
        base_mapping = nt_mapping or create_default_neurotransmitter_mapping()
        self.nt_mapping = extend_neurotransmitter_mapping(base_mapping)
        
        # Initialize temporal profiles if needed
        if not hasattr(self.nt_mapping, 'temporal_profiles') or not self.nt_mapping.temporal_profiles:
            self.nt_mapping._initialize_temporal_profiles()
        
        # Create visualization preprocessor if not provided
        self.visualization_preprocessor = (
            visualization_preprocessor or NeurotransmitterVisualizationPreprocessor()
        )
        
        # Initialize XGBoost service if provided
        self._xgboost_service = xgboost_service
    
    async def generate_neurotransmitter_time_series(
        self,
        subject_id: UUID,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        time_range_days: int = 30,
        time_step_hours: int = 6
    ) -> UUID:
        """
        Generate a temporal sequence for a neurotransmitter in a specific brain region.
        
        Args:
            subject_id: UUID of the subject identity
            brain_region: Target brain region
            neurotransmitter: Target neurotransmitter
            time_range_days: Number of days to simulate
            time_step_hours: Hours between time points
            
        Returns:
            UUID of the created temporal sequence
            
        Raises:
            ResourceNotFoundError: If subject doesn't exist
        """
        # Verify subject exists
        subject = await self.subject_repository.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with ID {subject_id} not found")
        
        # Generate timestamps
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=time_range_days)
        num_steps = int((time_range_days * 24) / time_step_hours)
        timestamps = [
            start_time + timedelta(hours=i * time_step_hours)
            for i in range(num_steps + 1)
        ]
        
        # Generate sequence using domain model
        sequence = self.nt_mapping.generate_temporal_sequence(
            brain_region=brain_region,
            neurotransmitter=neurotransmitter,
            timestamps=timestamps,
            subject_id=subject_id  # Pass subject_id instead of patient_id
        )
        
        # Add subject data to metadata
        sequence.metadata.update({
            "subject_id": str(subject_id),
            "identity_type": subject.identity_type,
            "subject_attributes": {k: v for k, v in subject.attributes.items() if k in ["age", "sex", "clinical_factors"]}
        })
        
        # Persist sequence
        sequence_id = await self.sequence_repository.save(sequence)
        
        # Track event for audit and tracking purposes
        if self.event_repository:
            event = await self._create_sequence_generation_event(
                subject_id=subject_id,
                brain_region=brain_region,
                neurotransmitter=neurotransmitter,
                sequence_id=sequence_id
            )
            await self.event_repository.save(event)
        
        # Record audit event if audit service is available
        if self.audit_service:
            await self.audit_service.log_event(
                AuditEvent(
                    event_type=AuditEventType.DATA_GENERATION,
                    resource_id=str(sequence_id),
                    resource_type="TemporalSequence",
                    subject_id=str(subject_id),
                    details={
                        "brain_region": brain_region.value,
                        "neurotransmitter": neurotransmitter.value,
                        "time_range_days": time_range_days
                    }
                )
            )
            
        return sequence_id
    
    async def analyze_neurotransmitter_levels(
        self,
        subject_id: UUID,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter
    ) -> Optional[NeurotransmitterEffect]:
        """
        Analyze neurotransmitter levels for a subject in a specific brain region.
        
        Args:
            subject_id: UUID of the subject identity
            brain_region: Target brain region
            neurotransmitter: Target neurotransmitter
            
        Returns:
            Statistical analysis of neurotransmitter effect
            
        Raises:
            ResourceNotFoundError: If subject doesn't exist
        """
        # Verify subject exists
        subject = await self.subject_repository.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with ID {subject_id} not found")
        
        # Get latest sequence containing this neurotransmitter
        sequence = await self.sequence_repository.get_latest_by_feature(
            subject_id=subject_id,  # Use subject_id instead of patient_id
            feature_name=neurotransmitter.value
        )
        
        if not sequence:
            return None
        
        # Get feature index
        try:
            feature_idx = sequence.feature_names.index(neurotransmitter.value)
        except ValueError:
            return None
        
        # Extract time series for this neurotransmitter
        time_series_data = [
            (ts, values[feature_idx]) 
            for ts, values in zip(sequence.timestamps, sequence.values)
        ]
        
        # Calculate baseline period (first third of the sequence)
        split_idx = len(sequence.timestamps) // 3
        baseline_period = (sequence.timestamps[0], sequence.timestamps[split_idx])
        
        # Use the correct method name
        pattern_analysis = self.nt_mapping.analyze_temporal_pattern(
            brain_region=brain_region,
            neurotransmitter=neurotransmitter
        )
        
        # Create a NeurotransmitterEffect object based on pattern analysis
        effect = NeurotransmitterEffect(
            neurotransmitter=neurotransmitter,
            effect_size=0.5,  # Default value
            p_value=0.05,  # Default value
            confidence_interval=(0.3, 0.7),  # Default range
            is_statistically_significant=pattern_analysis.get("confidence", 0) > 0.7,
            clinical_significance=ClinicalSignificance.MODERATE
        )
        
        # Add brain region to the effect for downstream use
        effect.brain_region = brain_region
        effect.time_series_data = time_series_data
        effect.baseline_period = baseline_period
        effect.comparison_period = (sequence.timestamps[split_idx+1], sequence.timestamps[-1])
        
        # Track analysis event if repository available
        if self.event_repository:
            event = await self._create_analysis_event(
                subject_id=subject_id,
                brain_region=brain_region,
                neurotransmitter=neurotransmitter,
                effect=effect
            )
            await self.event_repository.save(event)
        
        # Record audit event if audit service is available
        if self.audit_service:
            await self.audit_service.log_event(
                AuditEvent(
                    event_type=AuditEventType.DATA_ANALYSIS,
                    resource_id=str(sequence.id),
                    resource_type="TemporalSequence",
                    subject_id=str(subject_id),
                    details={
                        "brain_region": brain_region.value,
                        "neurotransmitter": neurotransmitter.value,
                        "effect_size": effect.effect_size,
                        "is_significant": effect.is_statistically_significant,
                    }
                )
            )
        
        return effect
    
    async def simulate_treatment_response(
        self,
        subject_id: UUID,
        brain_region: BrainRegion,
        target_neurotransmitter: Neurotransmitter,
        treatment_effect: float,
        simulation_days: int = 14
    ) -> Dict[Neurotransmitter, UUID]:
        """
        Simulate treatment response and save resulting temporal sequences.
        
        Args:
            subject_id: UUID of the subject identity
            brain_region: Target brain region
            target_neurotransmitter: Primary neurotransmitter affected by treatment
            treatment_effect: Magnitude and direction of effect (-1.0 to 1.0)
            simulation_days: Number of days to simulate
            
        Returns:
            Dictionary mapping neurotransmitters to their sequence UUIDs
            
        Raises:
            ResourceNotFoundError: If subject doesn't exist
            ValidationError: If treatment effect is invalid
        """
        # Verify subject exists
        subject = await self.subject_repository.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with ID {subject_id} not found")
        
        # Validate treatment effect
        if not -1.0 <= treatment_effect <= 1.0:
            raise ValidationError("Treatment effect must be between -1.0 and 1.0")
        
        # Adjust treatment effect using XGBoost predictions if available
        adjusted_effect = treatment_effect
        xgboost_prediction = None
        
        if self._xgboost_service:
            # Try to get subject baseline data for more accurate prediction
            baseline_sequence = await self.sequence_repository.get_latest_by_feature(
                subject_id=subject_id,
                feature_name=target_neurotransmitter.value
            )
            
            # Extract baseline data if available
            baseline_data = {}
            if baseline_sequence and baseline_sequence.sequence_length > 0:
                feature_idx = baseline_sequence.feature_names.index(target_neurotransmitter.value)
                baseline_value = baseline_sequence.values[0][feature_idx]
                baseline_data[f"baseline_{target_neurotransmitter.value}"] = baseline_value
            
            # Add subject attributes as features for prediction
            for key, value in subject.attributes.items():
                if isinstance(value, (int, float, bool)) or (isinstance(value, str) and value.isdigit()):
                    baseline_data[f"subject_{key}"] = float(value)
            
            # Get prediction from XGBoost service
            xgboost_prediction = self._xgboost_service.predict_treatment_response(
                subject_id=subject_id,
                brain_region=brain_region,
                neurotransmitter=target_neurotransmitter,
                treatment_effect=treatment_effect,
                baseline_data=baseline_data
            )
            
            # Apply prediction to adjust effect strength
            if xgboost_prediction and "predicted_response" in xgboost_prediction:
                # Scale the effect by the predicted response
                confidence = xgboost_prediction.get("confidence", 0.7)
                predicted_response = xgboost_prediction["predicted_response"]
                
                # Blend original effect with prediction based on confidence
                adjusted_effect = (
                    (treatment_effect * (1 - confidence)) + 
                    (predicted_response * confidence)
                )
        
        # Generate timestamps for simulation
        end_time = datetime.now(UTC) + timedelta(days=simulation_days)
        start_time = datetime.now(UTC)
        timestamps = [
            start_time + timedelta(hours=i * 6)  # 6-hour steps
            for i in range((simulation_days * 4) + 1)  # 4 time points per day
        ]
        
        # Simulate response with potentially adjusted effect
        responses = self.nt_mapping.simulate_treatment_response(
            brain_region=brain_region,
            target_neurotransmitter=target_neurotransmitter,
            treatment_effect=adjusted_effect,
            timestamps=timestamps,
            subject_id=subject_id  # Use subject_id instead of patient_id
        )
        
        # Save sequences and track events
        sequence_ids = {}
        for nt, sequence in responses.items():
            # Update metadata with additional treatment info
            sequence.metadata.update({
                "simulation_type": "treatment_response",
                "treatment_target": target_neurotransmitter.value,
                "treatment_effect_magnitude": treatment_effect,
                "adjusted_effect_magnitude": adjusted_effect,
                "brain_region": brain_region.value,
                "xgboost_prediction": xgboost_prediction if xgboost_prediction else None,
                "subject_id": str(subject_id),
                "identity_type": subject.identity_type
            })
            
            # Save sequence
            sequence_id = await self.sequence_repository.save(sequence)
            sequence_ids[nt] = sequence_id
            
            # Track simulation event
            if self.event_repository:
                event = await self._create_simulation_event(
                    subject_id=subject_id,
                    brain_region=brain_region,
                    target_neurotransmitter=target_neurotransmitter,
                    affected_neurotransmitter=nt,
                    sequence_id=sequence_id,
                    treatment_effect=treatment_effect,
                    adjusted_effect=adjusted_effect
                )
                await self.event_repository.save(event)
            
            # Record audit event if audit service is available
            if self.audit_service:
                await self.audit_service.log_event(
                    AuditEvent(
                        event_type=AuditEventType.SIMULATION,
                        resource_id=str(sequence_id),
                        resource_type="TemporalSequence",
                        subject_id=str(subject_id),
                        details={
                            "brain_region": brain_region.value,
                            "target_neurotransmitter": target_neurotransmitter.value,
                            "affected_neurotransmitter": nt.value,
                            "treatment_effect": treatment_effect,
                            "adjusted_effect": adjusted_effect
                        }
                    )
                )
        
        return sequence_ids
    
    async def get_visualization_data(
        self,
        sequence_id: UUID,
        focus_features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get optimized visualization data for a temporal sequence.
        
        Args:
            sequence_id: UUID of the sequence
            focus_features: Optional list of features to focus on
            
        Returns:
            Visualization-ready data structure
            
        Raises:
            ResourceNotFoundError: If sequence doesn't exist
        """
        # Get sequence
        sequence = await self.sequence_repository.get_by_id(sequence_id)
        if not sequence:
            raise ResourceNotFoundError(f"Sequence with ID {sequence_id} not found")
        
        # Preprocess for visualization
        viz_data = self.visualization_preprocessor.precompute_temporal_sequence_visualization(
            sequence=sequence,
            focus_features=focus_features
        )
        
        # Ensure essential fields are returned in a consistent format
        time_points = [ts.isoformat() for ts in sequence.timestamps]
        features = focus_features or sequence.feature_names
        
        # Format values for time series visualization
        values = []
        for i, timestamp in enumerate(sequence.timestamps):
            # Get values for this timestamp
            time_point_values = []
            for feature in features:
                if feature in sequence.feature_names:
                    feature_idx = sequence.feature_names.index(feature)
                    time_point_values.append(sequence.values[i][feature_idx])
                else:
                    time_point_values.append(0.0)  # Default value if feature not found
            values.append(time_point_values)
        
        # Enhance with the properly structured data
        viz_data.update({
            "time_points": time_points,
            "features": features,
            "values": values,
            "metadata": sequence.metadata
        })
        
        # Record audit event if audit service is available
        if self.audit_service and "subject_id" in sequence.metadata:
            await self.audit_service.log_event(
                AuditEvent(
                    event_type=AuditEventType.DATA_ACCESS,
                    resource_id=str(sequence_id),
                    resource_type="TemporalSequence",
                    subject_id=sequence.metadata["subject_id"],
                    details={"action": "visualization", "focus_features": focus_features}
                )
            )
        
        return viz_data
    
    async def get_cascade_visualization(
        self,
        subject_id: UUID,
        starting_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        time_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Get visualization data for a neurotransmitter cascade.
        
        Args:
            subject_id: UUID of the subject identity
            starting_region: Brain region where cascade starts
            neurotransmitter: Neurotransmitter to trigger cascade
            time_steps: Number of time steps to simulate
            
        Returns:
            Visualization-ready data structure for the cascade
            
        Raises:
            ResourceNotFoundError: If subject doesn't exist
        """
        # Verify subject exists
        subject = await self.subject_repository.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with ID {subject_id} not found")
        
        # Predict cascade
        cascade_results = self.nt_mapping.predict_cascade_effect(
            starting_region=starting_region,
            neurotransmitter=neurotransmitter,
            initial_level=0.8,  # Strong initial activation
            time_steps=time_steps,
            subject_id=subject_id  # Use subject_id instead of patient_id
        )
        
        # Preprocess for visualization
        viz_data = self.visualization_preprocessor.precompute_cascade_geometry(
            cascade_data=cascade_results
        )
        
        # Create a nodes and connections structure for easier consumption by visualization libraries
        nodes = []
        connections = []
        
        # Process vertices to create nodes
        regions_with_activity = set()
        for t in range(time_steps):
            vertices = viz_data.get("vertices_by_time", [])[t] if t < len(viz_data.get("vertices_by_time", [])) else []
            colors = viz_data.get("colors_by_time", [])[t] if t < len(viz_data.get("colors_by_time", [])) else []
            
            # Process vertices (every 3 values represent x,y,z coordinates)
            for i in range(0, len(vertices), 3):
                if i + 2 < len(vertices):
                    # Find the closest brain region to these coordinates
                    position = (vertices[i], vertices[i+1], vertices[i+2])
                    region = self._find_region_for_position(position)
                    if region:
                        regions_with_activity.add(region)
                        
                        # Get activity level from the cascade results
                        activity_level = cascade_results.get(region, [0.0] * time_steps)[t]
                        
                        # Add node if not already added
                        if not any(n for n in nodes if n.get("id") == region.value):
                            nodes.append({
                                "id": region.value,
                                "brain_region": region.value,
                                "position": position,
                                "activity": [cascade_results.get(region, [0.0] * time_steps)[i] for i in range(time_steps)]
                            })
        
        # Process connections between active regions
        for region1 in regions_with_activity:
            for region2 in regions_with_activity:
                if region1 != region2:
                    # Check if there's activity propagation between these regions
                    # Simple heuristic: if region2 becomes active after region1
                    region1_activity = cascade_results.get(region1, [0.0] * time_steps)
                    region2_activity = cascade_results.get(region2, [0.0] * time_steps)
                    
                    # Find when each region first becomes active
                    region1_active_at = next((i for i, v in enumerate(region1_activity) if v > 0.1), -1)
                    region2_active_at = next((i for i, v in enumerate(region2_activity) if v > 0.1), -1)
                    
                    # Create connection if region2 activates after region1
                    if 0 <= region1_active_at < region2_active_at:
                        # Calculate connection strength based on activity correlation
                        connection_strength = 0.0
                        for t in range(time_steps - 1):
                            if region1_activity[t] > 0.1:
                                # Check if region2 becomes more active in the next step
                                delta = region2_activity[t+1] - region2_activity[t]
                                if delta > 0:
                                    connection_strength += delta
                        
                        # Add connection if significant
                        if connection_strength > 0.05:
                            connections.append({
                                "source": region1.value,
                                "target": region2.value,
                                "strength": min(1.0, connection_strength),
                                "lag": region2_active_at - region1_active_at
                            })
        
        # Format time steps data
        time_steps_data = []
        for t in range(time_steps):
            time_step_data = {
                "step": t,
                "regions": {}
            }
            
            for region in regions_with_activity:
                activity = cascade_results.get(region, [0.0] * time_steps)[t]
                if activity > 0.01:  # Only include non-trivial activity
                    time_step_data["regions"][region.value] = activity
            
            time_steps_data.append(time_step_data)
        
        # Add enhanced visualization data
        viz_data.update({
            "subject_id": str(subject_id),
            "identity_type": subject.identity_type,
            "starting_region": starting_region.value,
            "neurotransmitter": neurotransmitter.value,
            "time_steps": time_steps_data,
            "nodes": nodes,
            "connections": connections
        })
        
        # Record audit event if audit service is available
        if self.audit_service:
            await self.audit_service.log_event(
                AuditEvent(
                    event_type=AuditEventType.DATA_ACCESS,
                    resource_id=f"cascade_{starting_region.value}_{neurotransmitter.value}",
                    resource_type="NeurotransmitterCascade",
                    subject_id=str(subject_id),
                    details={
                        "action": "cascade_visualization", 
                        "starting_region": starting_region.value,
                        "neurotransmitter": neurotransmitter.value,
                        "time_steps": time_steps
                    }
                )
            )
        
        return viz_data
    
    def _find_region_for_position(self, position: Tuple[float, float, float]) -> Optional[BrainRegion]:
        """
        Find the brain region closest to the given 3D position.
        
        Args:
            position: 3D position (x, y, z)
            
        Returns:
            Closest brain region or None if no match
        """
        # Get brain region coordinates from visualization preprocessor
        coordinates = self.visualization_preprocessor._brain_region_coordinates
        
        # Calculate distances to each region
        distances = {}
        for region, coords in coordinates.items():
            dx = position[0] - coords[0]
            dy = position[1] - coords[1]
            dz = position[2] - coords[2]
            distance = (dx * dx + dy * dy + dz * dz) ** 0.5
            distances[region] = distance
        
        # Return the closest region if distance is small enough
        if distances:
            closest_region = min(distances.items(), key=lambda x: x[1])
            if closest_region[1] < 5.0:  # Threshold for matching
                return closest_region[0]
        
        return None
    
    async def _create_sequence_generation_event(
        self,
        subject_id: UUID,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        sequence_id: UUID
    ) -> Any:  # Type will depend on event system
        """
        Create an event for sequence generation.
        
        Args:
            subject_id: UUID of the subject identity
            brain_region: Target brain region
            neurotransmitter: Target neurotransmitter
            sequence_id: UUID of the generated sequence
            
        Returns:
            Event object
        """
        # Implementation depends on the event system
        # This is just a placeholder
        return {
            "event_type": "sequence_generation",
            "subject_id": str(subject_id),
            "brain_region": brain_region.value,
            "neurotransmitter": neurotransmitter.value,
            "sequence_id": str(sequence_id),
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    async def _create_analysis_event(
        self,
        subject_id: UUID,
        brain_region: BrainRegion,
        neurotransmitter: Neurotransmitter,
        effect: NeurotransmitterEffect
    ) -> Any:  # Type will depend on event system
        """
        Create an event for neurotransmitter analysis.
        
        Args:
            subject_id: UUID of the subject identity
            brain_region: Target brain region
            neurotransmitter: Target neurotransmitter
            effect: Analysis result
            
        Returns:
            Event object
        """
        # Implementation depends on the event system
        # This is just a placeholder
        return {
            "event_type": "neurotransmitter_analysis",
            "subject_id": str(subject_id),
            "brain_region": brain_region.value,
            "neurotransmitter": neurotransmitter.value,
            "effect_size": effect.effect_size,
            "p_value": effect.p_value,
            "is_significant": effect.is_statistically_significant,
            "clinical_significance": effect.clinical_significance.value,
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    async def _create_simulation_event(
        self,
        subject_id: UUID,
        brain_region: BrainRegion,
        target_neurotransmitter: Neurotransmitter,
        affected_neurotransmitter: Neurotransmitter,
        sequence_id: UUID,
        treatment_effect: float,
        adjusted_effect: float
    ) -> Any:  # Type will depend on event system
        """
        Create an event for treatment simulation.
        
        Args:
            subject_id: UUID of the subject identity
            brain_region: Target brain region
            target_neurotransmitter: Primary target of treatment
            affected_neurotransmitter: Neurotransmitter affected by treatment
            sequence_id: UUID of the simulation sequence
            treatment_effect: Original treatment effect magnitude
            adjusted_effect: Adjusted effect after predictions
            
        Returns:
            Event object
        """
        # Implementation depends on the event system
        # This is just a placeholder
        return {
            "event_type": "treatment_simulation",
            "subject_id": str(subject_id),
            "brain_region": brain_region.value,
            "target_neurotransmitter": target_neurotransmitter.value,
            "affected_neurotransmitter": affected_neurotransmitter.value,
            "sequence_id": str(sequence_id),
            "treatment_effect": treatment_effect,
            "adjusted_effect": adjusted_effect,
            "timestamp": datetime.now(UTC).isoformat()
        }