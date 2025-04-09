#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Temporal Neurotransmitter Service
=====================================

This script provides a convenient way to run the Temporal Neurotransmitter
Service in isolation for development and testing purposes.

Usage:
    python scripts/run_temporal_neurotransmitter_service.py

The script will:
1. Set up necessary test data
2. Initialize the service with mock repositories
3. Run a sample temporal mapping calculation
4. Display the results
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domain.entities.temporal_events import TemporalEvent
from app.domain.entities.temporal_sequence import TemporalSequence
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter
from app.application.services.temporal_neurotransmitter_service import TemporalNeurotransmitterService
from app.domain.repositories.temporal_repository import TemporalSequenceRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("temporal_neurotransmitter_demo")


class MockTemporalRepository(TemporalSequenceRepository):
    """Mock implementation of TemporalSequenceRepository for testing."""
    
    def __init__(self):
        self.sequences = {}
        
    async def save(self, sequence: TemporalSequence) -> UUID:
        """Persist a temporal sequence."""
        sequence_id = UUID(f"00000000-0000-0000-0000-{len(self.sequences) + 1:012d}")
        self.sequences[sequence_id] = sequence
        return sequence_id
        
    async def get_by_id(self, sequence_id: UUID) -> Optional[TemporalSequence]:
        """Retrieve a temporal sequence by ID."""
        return self.sequences.get(sequence_id)
        
    async def get_by_patient_id(self, patient_id: UUID) -> List[TemporalSequence]:
        """Get all temporal sequences for a patient."""
        return [seq for seq in self.sequences.values() if seq.user_id == str(patient_id)]
        
    async def delete(self, sequence_id: UUID) -> bool:
        """Delete a temporal sequence."""
        if sequence_id in self.sequences:
            del self.sequences[sequence_id]
            return True
        return False
        
    async def get_latest_by_feature(
        self,
        patient_id: UUID,
        feature_name: str,
        limit: int = 10
    ) -> Optional[TemporalSequence]:
        """Get the most recent temporal sequence containing a specific feature."""
        patient_sequences = [seq for seq in self.sequences.values() if seq.user_id == str(patient_id)]
        # Sort by creation time (most recent first)
        patient_sequences.sort(key=lambda x: x.start_time, reverse=True)
        # In a real implementation, we would check if the sequence contains the feature
        return patient_sequences[0] if patient_sequences else None


def create_test_data() -> Dict[str, Any]:
    """Create test data for the temporal neurotransmitter service."""
    # Create some test events representing medication administrations
    now = datetime.now()
    
    # SSRI (selective serotonin reuptake inhibitor) administration
    ssri_event = TemporalEvent(
        event_id=UUID("00000000-0000-0000-0000-000000000001"),
        timestamp=now - timedelta(days=7),
        value="medication",
        metadata={
            "medication": "fluoxetine",
            "dosage": "20mg",
            "class": "SSRI",
            "event_type": "medication"
        }
    )
    
    # Benzodiazepine administration
    benzo_event = TemporalEvent(
        event_id=UUID("00000000-0000-0000-0000-000000000002"),
        timestamp=now - timedelta(days=3),
        value="medication",
        metadata={
            "medication": "lorazepam",
            "dosage": "1mg",
            "class": "benzodiazepine",
            "event_type": "medication"
        }
    )
    
    # Therapy session with noted improvement
    therapy_event = TemporalEvent(
        event_id=UUID("00000000-0000-0000-0000-000000000003"),
        timestamp=now - timedelta(days=1),
        value="therapy_session",
        metadata={
            "type": "CBT",
            "notes": "Patient reported decreased anxiety and improved sleep",
            "duration": "50 minutes",
            "event_type": "therapy_session"
        }
    )
    
    # Create medication effects
    ssri_effects = [
        NeurotransmitterEffect(
            neurotransmitter=Neurotransmitter.SEROTONIN,
            effect_size=0.7,
            p_value=0.01,
            confidence_interval=(0.5, 0.9),
            is_statistically_significant=True,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            time_series_data=[(now - timedelta(days=14), 0.3), (now, 0.7)]
        ),
        NeurotransmitterEffect(
            neurotransmitter=Neurotransmitter.SEROTONIN,
            effect_size=0.5,
            p_value=0.02,
            confidence_interval=(0.3, 0.7),
            is_statistically_significant=True,
            brain_region=BrainRegion.HIPPOCAMPUS,
            time_series_data=[(now - timedelta(days=14), 0.2), (now, 0.5)]
        )
    ]
    
    benzo_effects = [
        NeurotransmitterEffect(
            neurotransmitter=Neurotransmitter.GABA,
            effect_size=0.8,
            p_value=0.005,
            confidence_interval=(0.6, 0.95),
            is_statistically_significant=True,
            brain_region=BrainRegion.AMYGDALA,
            time_series_data=[(now - timedelta(days=3), 0.1), (now, 0.8)]
        ),
        NeurotransmitterEffect(
            neurotransmitter=Neurotransmitter.GABA,
            effect_size=0.4,
            p_value=0.03,
            confidence_interval=(0.2, 0.6),
            is_statistically_significant=True,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            time_series_data=[(now - timedelta(days=3), 0.1), (now, 0.4)]
        )
    ]
    
    # Create a temporal sequence
    sequence = TemporalSequence(
        name="Treatment Response Simulation",
        sequence_id=UUID("00000000-0000-0000-0000-000000000010"),
        patient_id=UUID("00000000-0000-0000-0000-000000123456"),
        events=[ssri_event, benzo_event, therapy_event],
        metadata={
            "description": "Simulation of neurotransmitter changes in response to SSRI and benzodiazepine",
            "start_time": now - timedelta(days=10),
            "end_time": now + timedelta(days=30)
        }
    )
    
    return {
        "sequence": sequence,
        "ssri_effects": ssri_effects,
        "benzo_effects": benzo_effects
    }


async def run_demo():
    """Run the temporal neurotransmitter service demonstration."""
    logger.info("Initializing Temporal Neurotransmitter Service Demo")
    
    # Create test data
    test_data = create_test_data()
    sequence = test_data["sequence"]
    ssri_effects = test_data["ssri_effects"]
    benzo_effects = test_data["benzo_effects"]
    
    # Create repository and service
    repo = MockTemporalRepository()
    service = TemporalNeurotransmitterService(temporal_repository=repo)
    
    # Save the sequence
    sequence_id = await repo.save(sequence)
    logger.info(f"Created temporal sequence with ID: {sequence_id}")
    
    # Register neurotransmitter effects for medications
    for event in sequence.events:
        if event.event_type == "medication":
            if event.event_data.get("class") == "SSRI":
                logger.info(f"Registering SSRI effects for event {event.id}")
                await service.register_neurotransmitter_effects(event.id, ssri_effects)
            elif event.event_data.get("class") == "benzodiazepine":
                logger.info(f"Registering benzodiazepine effects for event {event.id}")
                await service.register_neurotransmitter_effects(event.id, benzo_effects)
    
    # Generate neurotransmitter mapping
    logger.info("Generating temporal neurotransmitter mapping")
    mapping = await service.generate_temporal_mapping(
        sequence_id=sequence_id,
        neurotransmitters=[Neurotransmitter.SEROTONIN, Neurotransmitter.GABA],
        brain_regions=[
            BrainRegion.PREFRONTAL_CORTEX, 
            BrainRegion.HIPPOCAMPUS,
            BrainRegion.AMYGDALA
        ],
        resolution=timedelta(days=1)
    )
    
    # Display results
    logger.info("Temporal Neurotransmitter Mapping Results:")
    for timestamp, levels in mapping.items():
        logger.info(f"\nTimestamp: {timestamp.strftime('%Y-%m-%d')}")
        for region, nt_levels in levels.items():
            nt_str = ", ".join([f"{nt.name}: {round(level, 2)}" for nt, level in nt_levels.items()])
            logger.info(f"  {region.name}: {nt_str}")
    
    logger.info("\nDemo completed successfully")


if __name__ == "__main__":
    asyncio.run(run_demo())