"""
Dependency injection for application services.

This module provides FastAPI dependency functions to inject services
into route handlers, ensuring proper initialization and cleanup.
"""
from typing import AsyncGenerator

from fastapi import Depends

from app.api.dependencies.database import get_db
from app.application.services.temporal_neurotransmitter_service import TemporalNeurotransmitterService
from app.domain.services.enhanced_xgboost_service import EnhancedXGBoostService
from app.infrastructure.repositories.temporal_event_repository import SqlAlchemyEventRepository
from app.infrastructure.repositories.temporal_sequence_repository import SqlAlchemyTemporalSequenceRepository


async def get_sequence_repository(db=Depends(get_db)) -> AsyncGenerator:
    """Get a sequence repository instance."""
    repository = SqlAlchemyTemporalSequenceRepository(session=db)
    yield repository


async def get_event_repository(db=Depends(get_db)) -> AsyncGenerator:
    """Get an event repository instance."""
    repository = SqlAlchemyEventRepository(session=db)
    yield repository


async def get_xgboost_service() -> AsyncGenerator:
    """Get an XGBoost service instance."""
    # In production, model_path would be loaded from configuration
    service = EnhancedXGBoostService()
    yield service


async def get_temporal_neurotransmitter_service(
    sequence_repository=Depends(get_sequence_repository),
    event_repository=Depends(get_event_repository),
    xgboost_service=Depends(get_xgboost_service)
) -> AsyncGenerator:
    """
    Get a temporal neurotransmitter service instance with all dependencies.
    
    This dependency automatically injects repositories and the XGBoost service.
    """
    service = TemporalNeurotransmitterService(
        sequence_repository=sequence_repository,
        event_repository=event_repository,
        xgboost_service=xgboost_service
    )
    yield service