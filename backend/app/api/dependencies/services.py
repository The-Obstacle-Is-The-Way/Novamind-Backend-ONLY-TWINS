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


# Re-introduce repository provider functions, using dict type annotation to prevent
# FastAPI from trying to use AsyncSession in response models
async def get_sequence_repository(db: dict = Depends(get_db)) -> dict:
    """
    Get a sequence repository instance.
    
    The return type is deliberately set to dict to prevent FastAPI
    from trying to use AsyncSession in response models.
    
    Returns:
        TemporalSequenceRepository: Repository instance (masked as dict)
    """
    # Cast db back to AsyncSession for actual use
    session = db  # Type is actually AsyncSession
    repository = SqlAlchemyTemporalSequenceRepository(session=session)
    return repository


async def get_event_repository(db: dict = Depends(get_db)) -> dict:
    """
    Get an event repository instance.
    
    The return type is deliberately set to dict to prevent FastAPI
    from trying to use AsyncSession in response models.
    
    Returns:
        EventRepository: Repository instance (masked as dict)
    """
    # Cast db back to AsyncSession for actual use
    session = db  # Type is actually AsyncSession
    repository = SqlAlchemyEventRepository(session=session)
    return repository


# Assuming EnhancedXGBoostService is the concrete type, keep it for now
# If there's an interface like XGBoostService, prefer that.
async def get_xgboost_service():
    """
    Get an XGBoost service instance.
    
    Returns:
        EnhancedXGBoostService: Service instance
    """
    # In production, model_path would be loaded from configuration
    service = EnhancedXGBoostService()
    # No yield needed if the dependency scope is handled by FastAPI/Depends
    return service


async def get_temporal_neurotransmitter_service(
    # Depend on the repository providers again, using masked types
    sequence_repository: dict = Depends(get_sequence_repository),
    event_repository: dict = Depends(get_event_repository),
    xgboost_service: EnhancedXGBoostService = Depends(get_xgboost_service)
) -> dict:
    """
    Get a temporal neurotransmitter service instance with all dependencies.

    This dependency automatically injects repositories and the XGBoost service.
    The return type is deliberately set to dict to prevent FastAPI
    from trying to use AsyncSession in response models.
    
    Returns:
        TemporalNeurotransmitterService: Service instance with injected dependencies (masked as dict)
    """
    # We know the repositories are actually TemporalSequenceRepository and EventRepository, not dict
    service = TemporalNeurotransmitterService(
        sequence_repository=sequence_repository,  # Actually TemporalSequenceRepository
        event_repository=event_repository,  # Actually EventRepository
        xgboost_service=xgboost_service
    )
    return service