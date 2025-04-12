"""
End-to-end integration tests for the temporal neurotransmitter system.

These tests validate the complete vertical stack from API to infrastructure,
ensuring that all components work together seamlessly with proper horizontal
coverage across all neurotransmitters and brain regions.
"""
import asyncio
import pytest
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.temporal_neurotransmitter import router as temporal_router
from app.application.services.temporal_neurotransmitter_service import TemporalNeurotransmitterService
from app.core.config import settings
from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter, ClinicalSignificance
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.temporal_events import CorrelatedEvent, EventChain
from app.domain.entities.temporal_sequence import TemporalSequence
from app.domain.repositories.temporal_repository import TemporalSequenceRepository, EventRepository
from app.domain.services.enhanced_xgboost_service import EnhancedXGBoostService
from app.domain.services.visualization_preprocessor import NeurotransmitterVisualizationPreprocessor
from app.infrastructure.models.temporal_sequence_model import Base
from app.infrastructure.repositories.temporal_event_repository import SqlAlchemyEventRepository
from app.infrastructure.repositories.temporal_sequence_repository import SqlAlchemyTemporalSequenceRepository


# Create a test database engine
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_SQLALCHEMY_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker()
    autocommit = False, autoflush = False, bind = engine, class_ = AsyncSession
()

# Mock user for authentication
test_user = {
    "id": str(uuid4()),
    "email": "test.neurologist@novamind.io",
    "first_name": "Test",
    "last_name": "Neurologist",
    "roles": ["CLINICIAN"],
    "is_active": True
}


@pytest.fixture
async def db_session():
        """Create an async SQLAlchemy session for testing with in-memory database."""
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        
        async with TestingSessionLocal() as session:
        yield session
        
        # Clean up
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        @pytest.fixture
        async def sequence_repository(db_session):
            """Create sequence repository with test session."""    
    #     return SqlAlchemyTemporalSequenceRepository(session=db_session) # FIXME: return outside function
    @pytest.fixture
    async def event_repository(db_session):
        """Create event repository with test session."""    
    #     return SqlAlchemyEventRepository(session=db_session) # FIXME: return outside function
    @pytest.fixture
    def xgboost_service():
                """Create XGBoost service for testing."""    
    return EnhancedXGBoostService()
    @pytest.fixture
    async def temporal_service(sequence_repository, event_repository, xgboost_service):
        """Create temporal neurotransmitter service with repositories and XGBoost."""    
    #     return TemporalNeurotransmitterService( # FIXME: return outside function)
        sequence_repository=sequence_repository,
        event_repository=event_repository,
        xgboost_service=xgboost_service
    (    )


    # Local test_app and test_client fixtures removed; tests will use the client fixture from conftest.py
    @pytest.fixture
    def mock_current_user():
                """Mock current user dependency."""    
    return patch()
        "app.api.dependencies.auth.get_current_user_dict",
    (        return_value=AsyncMock(return_value=test_user))
    ()
    @pytest.fixture
    def patient_id():
                """Generate a patient ID for testing."""    
    return uuid4()


    @pytest.mark.asyncio()
    @pytest.mark.db_required()
    async def test_temporal_service_with_xgboost_integration()
    temporal_service: TemporalNeurotransmitterService,
    xgboost_service: EnhancedXGBoostService,
    patient_id: UUID
    ():
        """
    Test the integration between TemporalNeurotransmitterService and EnhancedXGBoostService.
    
    This test verifies that the temporal service correctly leverages XGBoost predictions
    to enhance treatment simulations.
    """
    # Set up - create a baseline sequence
    baseline_sequence_id = await temporal_service.generate_neurotransmitter_time_series()
        patient_id=patient_id,
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        time_range_days=30,
        time_step_hours=6
    (    )
    
    # Verify baseline sequence was created
    assert baseline_sequence_id is not None
    
    # Set up spy on XGBoost service
    original_predict = xgboost_service.predict_treatment_response
    prediction_calls = []
    def prediction_spy(*args, **kwargs):
        prediction_calls.append(kwargs)
    return original_predict(*args, **kwargs)
    
    xgboost_service.predict_treatment_response = prediction_spy
    
    # Test - simulate treatment response with XGBoost prediction
    treatment_effect = 0.6
    response_sequences = await temporal_service.simulate_treatment_response()
        patient_id=patient_id,
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        target_neurotransmitter=Neurotransmitter.SEROTONIN,
        treatment_effect=treatment_effect,
        simulation_days=14
    (    )
    
    # Verify XGBoost service was called
    assert len(prediction_calls) > 0
    assert "patient_id" in prediction_calls[0]
    assert prediction_calls[0]["patient_id"] == patient_id
    assert "treatment_effect" in prediction_calls[0]
    assert prediction_calls[0]["treatment_effect"] == treatment_effect
    
    # Verify sequences were created for multiple neurotransmitters
    assert len(response_sequences) > 1
    
    # Verify neurotransmitter mapping in sequences
    sequences_contain_serotonin = False
    sequences_contain_dopamine = False
    
    for nt, sequence_id in response_sequences.items():
        if nt == Neurotransmitter.SEROTONIN:
            sequences_contain_serotonin = True
            elif nt == Neurotransmitter.DOPAMINE:
                sequences_contain_dopamine = True
    
                assert sequences_contain_serotonin, "Sequences should include serotonin"
            assert sequences_contain_dopamine, "Sequences should include dopamine (indirect effect)"
    
            # Cleanup - restore original method
            xgboost_service.predict_treatment_response = original_predict
    
            # Additional verification - get a sequence and verify metadata includes XGBoost info
            sequence = await temporal_service.sequence_repository.get_by_id()
            response_sequences[Neurotransmitter.SEROTONIN]
            (    )
            assert sequence is not None
            assert "xgboost_prediction" in sequence.metadata


            @pytest.mark.asyncio()
            async def test_full_brain_region_coverage_with_visualization()
            temporal_service: TemporalNeurotransmitterService,
            patient_id: UUID
            ():
        """
    Test complete horizontal coverage across brain regions with visualization.
    
    This test ensures that the service can generate visualizations for all brain regions.
    """
    # Test key brain regions with significant neurotransmitter involvement
    test_regions = [
        BrainRegion.PREFRONTAL_CORTEX,  # Executive function
        BrainRegion.AMYGDALA,           # Emotional processing
        BrainRegion.HIPPOCAMPUS,        # Memory
        BrainRegion.RAPHE_NUCLEI,       # Serotonin production
        BrainRegion.VENTRAL_TEGMENTAL_AREA  # Dopamine production
    ]
    
    visualization_data = {}
    
    # Generate visualization for each region
    for region in test_regions:
        # Create cascade visualization
        viz_data = await temporal_service.get_cascade_visualization()
            patient_id=patient_id,
            starting_region=region,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            time_steps=5
        (        )
        
        visualization_data[region] = viz_data
        
        # Verify visualization data structure
        assert "nodes" in viz_data
        assert "connections" in viz_data
        assert "time_steps" in viz_data
        
        # Verify that the starting region is included in the nodes
        starting_region_in_nodes = False
        for node in viz_data["nodes"]:
            if node["brain_region"] == region.value:
                starting_region_in_nodes = True
                break
        
                assert starting_region_in_nodes, f"Starting region {region.value} should be in visualization nodes"
    
                # Verify that different regions produce different visualizations
                # Compare nodes and connections counts
                node_counts = [len(data["nodes"]) for data in visualization_data.values()]
                connection_counts = [len(data["connections"]) for data in visualization_data.values()]
    
                # Not all visualizations should have the same node/connection count
                assert len(set(node_counts)) > 1 or len(set(connection_counts)) > 1, \
                "Different regions should produce different visualization structures"


                @pytest.mark.asyncio()
                async def test_full_neurotransmitter_coverage_with_treatment()
                temporal_service: TemporalNeurotransmitterService,
                patient_id: UUID
                ():
        """
    Test complete horizontal coverage across neurotransmitters with treatment simulation.
    
    This test ensures that the service can simulate treatment effects for all neurotransmitters.
    """
    # Test major neurotransmitters involved in psychiatric conditions
    test_neurotransmitters = [
        Neurotransmitter.SEROTONIN,     # Depression, anxiety
        Neurotransmitter.DOPAMINE,      # Reward, addiction, psychosis
        Neurotransmitter.GABA,          # Anxiety, sleep
        Neurotransmitter.GLUTAMATE      # Learning, excitotoxicity
    ]
    
    treatment_results = {}
    
    # Simulate treatment for each neurotransmitter
    for nt in test_neurotransmitters:
        # Simulate treatment targeting this neurotransmitter
        response = await temporal_service.simulate_treatment_response()
            patient_id=patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            target_neurotransmitter=nt,
            treatment_effect=0.5,
            simulation_days=7
        (        )
        
        treatment_results[nt] = response
        
        # Verify response contains sequences for multiple neurotransmitters
        assert len(response) > 1
        assert nt in response, f"Response should include target neurotransmitter {nt.value}"
        
        # Verify that the target neurotransmitter sequence ID is valid
        sequence = await temporal_service.sequence_repository.get_by_id(response[nt])
        assert sequence is not None
        
        # Verify metadata contains treatment information
        assert "treatment_target" in sequence.metadata
        assert sequence.metadata["treatment_target"] == nt.value
    
        # Verify that different neurotransmitters produce different patterns of effects
        # Count how many secondary neurotransmitters are affected
        secondary_counts = [len(result) for result in treatment_results.values()]
    
        # Not all treatments should affect the same number of neurotransmitters
        assert len(set(secondary_counts)) > 1, \
        "Different neurotransmitter treatments should affect different numbers of secondary neurotransmitters"


        @pytest.mark.asyncio()
        async def test_api_integration_with_service()
        client: TestClient, # Use client fixture from conftest.py
        mock_current_user,
        # test_app fixture removed
        temporal_service,
        patient_id
        ():
        """
    Test API integration with the neurotransmitter service.
    
    This test verifies that the API layer correctly integrates with the service layer.
    """
    # Setup - patch dependencies to use our service instance
    with mock_current_user, patch(:)
        "app.api.dependencies.services.get_temporal_neurotransmitter_service",
    (        return_value=AsyncMock(return_value=temporal_service))
    ()
        # Test 1: Generate time series
        time_series_response = client.post( # Use client fixture)
            "/api/v1/temporal-neurotransmitter/time-series",
            json={
                "patient_id": str(patient_id),
                "brain_region": BrainRegion.PREFRONTAL_CORTEX.value,
                "neurotransmitter": Neurotransmitter.SEROTONIN.value,
                "time_range_days": 14,
                "time_step_hours": 6
            }
()
        
        # Verify response
        assert time_series_response.status_code  ==  201
        assert "sequence_id" in time_series_response.json()
        
        # Test 2: Simulate treatment
        treatment_response = client.post( # Use client fixture)
            "/api/v1/temporal-neurotransmitter/simulate-treatment",
            json={
                "patient_id": str(patient_id),
                "brain_region": BrainRegion.PREFRONTAL_CORTEX.value,
                "target_neurotransmitter": Neurotransmitter.SEROTONIN.value,
                "treatment_effect": 0.5,
                "simulation_days": 14
            }
()
        
        # Verify response
        assert treatment_response.status_code  ==  200
        assert "sequence_ids" in treatment_response.json()
        
        # Extract a sequence ID for visualization test
        first_sequence_id = list(treatment_response.json()["sequence_ids"].values())[0]
        
        # Test 3: Get visualization data
        viz_response = client.post( # Use client fixture)
            "/api/v1/temporal-neurotransmitter/visualization-data",
            json={
                "sequence_id": first_sequence_id
            }
()
        
        # Verify response
        assert viz_response.status_code  ==  200
        assert "time_points" in viz_response.json()
assert "features" in viz_response.json()
assert "values" in viz_response.json()