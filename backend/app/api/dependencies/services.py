"""
Dependency injection for application services.

This module provides FastAPI dependency functions to inject services
into route handlers, ensuring proper initialization and cleanup.
"""
from typing import AsyncGenerator

from fastapi import Depends

# Import AsyncSession for type hinting
from sqlalchemy.ext.asyncio import AsyncSession
from app.presentation.api.dependencies.database import get_db # Corrected import path
# Re-import necessary infrastructure and domain types
from app.infrastructure.repositories.temporal_event_repository import SqlAlchemyEventRepository
from app.infrastructure.repositories.temporal_sequence_repository import SqlAlchemyTemporalSequenceRepository
from app.domain.repositories.temporal_repository import TemporalSequenceRepository, EventRepository
from app.application.services.temporal_neurotransmitter_service import TemporalNeurotransmitterService
from app.domain.services.enhanced_xgboost_service import EnhancedXGBoostService


# Re-introduce repository provider functions
async def get_sequence_repository(db: AsyncSession = Depends(get_db)) -> TemporalSequenceRepository:
    """Get a sequence repository instance."""
    repository = SqlAlchemyTemporalSequenceRepository(session=db)
    return repository


async def get_event_repository(db: AsyncSession = Depends(get_db)) -> EventRepository:
    """Get an event repository instance."""
    repository = SqlAlchemyEventRepository(session=db)
    return repository


# Assuming EnhancedXGBoostService is the concrete type, keep it for now
# If there's an interface like XGBoostService, prefer that.
async def get_xgboost_service() -> EnhancedXGBoostService:
    """Get an XGBoost service instance."""
    # In production, model_path would be loaded from configuration
    service = EnhancedXGBoostService()
    # No yield needed if the dependency scope is handled by FastAPI/Depends
    return service


async def get_temporal_neurotransmitter_service(
    # Depend on the repository providers again
    sequence_repository: TemporalSequenceRepository = Depends(get_sequence_repository),
    event_repository: EventRepository = Depends(get_event_repository),
    xgboost_service: EnhancedXGBoostService = Depends(get_xgboost_service)
) -> TemporalNeurotransmitterService:
    """
    Get a temporal neurotransmitter service instance with all dependencies.

    This dependency automatically injects repositories and the XGBoost service.
    """
    service = TemporalNeurotransmitterService(
        sequence_repository=sequence_repository,
        event_repository=event_repository,
        xgboost_service=xgboost_service
    )
    return service