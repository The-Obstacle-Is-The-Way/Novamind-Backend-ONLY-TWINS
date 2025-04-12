"""
Unit tests for the TemporalNeurotransmitterService.

These tests ensure the service correctly orchestrates interactions between
domain entities, repositories, and external services.
"""
import asyncio
from datetime import datetime, UTC, timedelta
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.services.temporal_neurotransmitter_service import TemporalNeurotransmitterService
from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter, ClinicalSignificance
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.temporal_events import CorrelatedEvent, EventChain, TemporalEvent
from app.domain.entities.temporal_sequence import TemporalSequence
from app.domain.services.visualization_preprocessor import NeurotransmitterVisualizationPreprocessor

# Fixtures for testing

@pytest.fixture
@pytest.mark.db_required()
def test_patient_id():
    """Generate a test patient ID."""
    return uuid.uuid4()

@pytest.fixture
def mock_sequence_repository():
    """Create a mock sequence repository."""
    repository = AsyncMock()
    repository.save = AsyncMock(return_value=uuid.uuid4())
    repository.get_by_id = AsyncMock()
    repository.get_latest_by_feature = AsyncMock()
    
    return repository

@pytest.fixture
def mock_event_repository():
    """Create a mock event repository."""
    repository = AsyncMock()
    repository.save = AsyncMock(return_value=uuid.uuid4())
    
    return repository

@pytest.fixture
def mock_xgboost_service():
    """Create a mock XGBoost service."""
    service = MagicMock()
    service.predict_treatment_response = MagicMock(return_value={
        "predicted_response": 0.75,
        "confidence": 0.85,
        "timeframe_days": 14,
        "feature_importance": {
            "baseline_serotonin": 0.45,
            "age": 0.25,
            "previous_treatment_response": 0.3
        }
    })
    
    return service

@pytest.fixture
def mock_sequence():
    """Create a mock temporal sequence."""
    # Create timestamps
    now = datetime.now()
    timestamps = [now + timedelta(hours=i * 6) for i in range(5)]
    
    # Create feature names for multiple neurotransmitters
    feature_names = [nt.value for nt in Neurotransmitter]
    
    # Create sample values
    values = []
    for _ in range(5):
        values.append([0.5] * len(feature_names))
    
    # Make values for serotonin increase over time
    serotonin_idx = feature_names.index(Neurotransmitter.SEROTONIN.value)
    for i in range(5):
        values[i][serotonin_idx] = 0.3 + (i * 0.1)
    
    # Create sequence with compatible parameters
    sequence = TemporalSequence(
        name="test_sequence",
        sequence_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        feature_names=feature_names,
        timestamps=timestamps,
        values=values,
        metadata={"test": "data"}
    )
    
    # No need to add events, they're already in the values list
    
    # The sequence already has these properties from initialization
    # No need to set them again
    
    return sequence

@pytest.fixture
def temporal_service(mock_sequence_repository, mock_event_repository, mock_xgboost_service):
    """Create a temporal neurotransmitter service with mock dependencies."""
    return TemporalNeurotransmitterService(
        sequence_repository=mock_sequence_repository,
        event_repository=mock_event_repository,
        xgboost_service=mock_xgboost_service
    )


class TestTemporalNeurotransmitterService:
    """Test suite for the TemporalNeurotransmitterService."""
    
    @pytest.mark.asyncio()
    async def test_generate_neurotransmitter_time_series(self, temporal_service, test_patient_id):
        """Test generation of neurotransmitter time series."""
        # Execute
        sequence_id = await temporal_service.generate_neurotransmitter_time_series(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            time_range_days=14,
            time_step_hours=6
        )
        
        # Verify
        assert sequence_id is not None
        assert temporal_service.sequence_repository.save.called
        
        # Verify event tracking
        if temporal_service.event_repository:
            assert temporal_service.event_repository.save.called
    
    @pytest.mark.asyncio()
    async def test_analyze_patient_neurotransmitter_levels(
        self, temporal_service, mock_sequence_repository, mock_sequence, test_patient_id
    ):
        """Test analysis of neurotransmitter levels."""
        # Setup - configure mock to return a sequence
        mock_sequence_repository.get_latest_by_feature.return_value = mock_sequence
        
        # Execute
        effect = await temporal_service.analyze_patient_neurotransmitter_levels(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN
        )
        
        # Verify
        assert effect is not None
        assert effect.neurotransmitter  ==  Neurotransmitter.SEROTONIN
        assert effect.brain_region  ==  BrainRegion.PREFRONTAL_CORTEX
        assert effect.effect_size is not None
        assert len(effect.time_series_data) > 0
        assert effect.baseline_period is not None
        assert effect.comparison_period is not None
    
    @pytest.mark.asyncio()
    async def test_analyze_patient_neurotransmitter_levels_no_data(
        self, temporal_service, mock_sequence_repository, test_patient_id
    ):
        """Test analysis when no data is available."""
        # Setup - configure mock to return None (no sequence found)
        mock_sequence_repository.get_latest_by_feature.return_value = None
        
        # Execute
        effect = await temporal_service.analyze_patient_neurotransmitter_levels(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN
        )
        
        # Verify
        assert effect is None
    
    @pytest.mark.asyncio()
    async def test_simulate_treatment_response(
        self, temporal_service, mock_sequence_repository, test_patient_id
    ):
        """Test simulation of treatment response."""
        # Setup for empty sequence check
        mock_sequence_repository.get_latest_by_feature.return_value = MagicMock(sequence_length=0)
        
        # Execute
        response_sequences = await temporal_service.simulate_treatment_response(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            target_neurotransmitter=Neurotransmitter.SEROTONIN,
            treatment_effect=0.5,
            simulation_days=7
        )
        
        # Verify
        assert isinstance(response_sequences, dict)
        assert len(response_sequences) > 0
        assert temporal_service.sequence_repository.save.called
        
        # Verify XGBoost was called
        assert temporal_service._xgboost_service.predict_treatment_response.called
    
    @pytest.mark.asyncio()
    async def test_simulate_treatment_response_without_xgboost(
        self, mock_sequence_repository, mock_event_repository
    ):
        """Test simulation of treatment response without XGBoost service."""
        # Create service without XGBoost
        service = TemporalNeurotransmitterService(
            sequence_repository=mock_sequence_repository,
            event_repository=mock_event_repository,
            xgboost_service=None
        )
        
        # Configure mock to return no sequence
        mock_sequence_repository.get_latest_by_feature.return_value = None
        
        # Execute
        response_sequences = await service.simulate_treatment_response(
            patient_id=uuid.uuid4(),
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            target_neurotransmitter=Neurotransmitter.SEROTONIN,
            treatment_effect=0.5,
            simulation_days=7
        )
        
        # Verify
        assert isinstance(response_sequences, dict)
        assert len(response_sequences) > 0
        assert mock_sequence_repository.save.called
    
    @pytest.mark.asyncio()
    async def test_get_visualization_data(
        self, temporal_service, mock_sequence_repository, mock_sequence
    ):
        """Test retrieval of visualization data."""
        # Setup
        sequence_id = uuid.uuid4()
        mock_sequence_repository.get_by_id.return_value = mock_sequence
        
        # Execute
        viz_data = await temporal_service.get_visualization_data(sequence_id)
        
        # Verify
        assert viz_data is not None
        assert "time_points" in viz_data
        assert "features" in viz_data
        assert "values" in viz_data
        assert "metadata" in viz_data
        assert mock_sequence_repository.get_by_id.called
    
    @pytest.mark.asyncio()
    async def test_get_visualization_data_invalid_id(
        self, temporal_service, mock_sequence_repository
    ):
        """Test visualization data retrieval with invalid ID."""
        # Setup
        sequence_id = uuid.uuid4()
        mock_sequence_repository.get_by_id.return_value = None
        
        # Execute and verify
        with pytest.raises(ValueError):
            await temporal_service.get_visualization_data(sequence_id)
    
    @pytest.mark.asyncio()
    async def test_get_cascade_visualization(
        self, temporal_service, test_patient_id
    ):
        """Test cascade visualization."""
        # Execute
        cascade_data = await temporal_service.get_cascade_visualization(
            patient_id=test_patient_id,
            starting_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            time_steps=5
        )
        
        # Verify
        assert cascade_data is not None
        assert "nodes" in cascade_data
        assert "connections" in cascade_data
        assert "time_steps" in cascade_data
        assert "patient_id" in cascade_data
        assert cascade_data["patient_id"] == str(test_patient_id)
        assert cascade_data["starting_region"] == BrainRegion.PREFRONTAL_CORTEX.value
        assert cascade_data["neurotransmitter"] == Neurotransmitter.SEROTONIN.value
    
    @pytest.mark.asyncio()
    async def test_xgboost_integration_treatment_adjustment(
        self, temporal_service, mock_sequence_repository, mock_sequence, test_patient_id
    ):
        """Test XGBoost integration for treatment effect adjustment."""
        # Setup - ensure baseline data is available
        mock_sequence_repository.get_latest_by_feature.return_value = mock_sequence
        
        # Configure XGBoost to predict a stronger response
        temporal_service._xgboost_service.predict_treatment_response.return_value = {
            "predicted_response": 0.9,  # Higher than input effect
            "confidence": 0.8,
            "timeframe_days": 14
        }
        
        # Execute
        input_effect = 0.5
        response_sequences = await temporal_service.simulate_treatment_response(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            target_neurotransmitter=Neurotransmitter.SEROTONIN,
            treatment_effect=input_effect,
            simulation_days=14
        )
        
        # Verify sequences were created
        assert isinstance(response_sequences, dict)
        assert len(response_sequences) > 0
        
        # Verify XGBoost service was called with correct parameters
        xgboost_call = temporal_service._xgboost_service.predict_treatment_response
        assert xgboost_call.called
        
        # Get the call arguments
        call_args = xgboost_call.call_args[1]
        assert "patient_id" in call_args
        assert "brain_region" in call_args
        assert "neurotransmitter" in call_args
        assert "treatment_effect" in call_args
        assert call_args["treatment_effect"] == input_effect