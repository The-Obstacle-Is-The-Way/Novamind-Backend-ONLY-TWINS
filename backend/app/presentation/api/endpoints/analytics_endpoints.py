# -*- coding: utf-8 -*-
"""
Analytics API Endpoints.

This module contains API endpoints for analytics data collection
and retrieval, with proper HIPAA compliance and validation.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from pydantic import BaseModel, Field, validator

from app.core.utils.logging import get_logger
from app.core.constants import CacheNamespace, EventType
from app.application.interfaces.services.cache_service import CacheService
from app.presentation.api.dependencies.services import get_cache_service # Corrected import path
from app.presentation.api.dependencies.auth import get_current_user
from app.presentation.api.dependencies.rate_limiter import RateLimitDependency
from app.infrastructure.ml.phi_detection import PHIDetectionService


# Create router
router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
    },
)

# Logger
logger = get_logger(__name__)

# PHI detection service
phi_detector = PHIDetectionService()


class ClientInfo(BaseModel):
    """Client information for analytics events."""
    
    browser: Optional[str] = None
    os: Optional[str] = None
    device: Optional[str] = None
    screen_size: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


class AnalyticsEvent(BaseModel):
    """Analytics event data model."""
    
    event_id: Optional[str] = Field(
        None, description="Unique identifier for the event (auto-generated if not provided)"
    )
    event_type: str = Field(..., description="Type of analytics event")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO-8601 timestamp of the event"
    )
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    client_info: ClientInfo = Field(
        default_factory=ClientInfo,
        description="Client context information"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data"
    )
    
    @validator("event_id", pre=True, always=True)
    def set_event_id(cls, v):
        """Auto-generate event ID if not provided."""
        return v or str(uuid.uuid4())
        
    @validator("event_type")
    def validate_event_type(cls, v):
        """Validate the event type."""
        # Allow custom event types with namespace
        if "." in v:
            return v
            
        # Check built-in event types
        valid_event_types = [
            EventType.USER_LOGIN,
            EventType.USER_LOGOUT,
            EventType.USER_REGISTER,
            EventType.USER_UPDATE,
            EventType.CONTENT_VIEW,
            EventType.CONTENT_SEARCH,
            EventType.FEATURE_USE,
            EventType.API_REQUEST,
            EventType.API_ERROR,
        ]
        
        if v not in valid_event_types:
            logger.warning(f"Unknown event type: {v}")
            
        return v


class AnalyticsBatch(BaseModel):
    """Batch of analytics events."""
    
    events: List[AnalyticsEvent] = Field(..., min_items=1, max_items=100)


class ApiResponse(BaseModel):
    """API response model."""
    
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None


async def _process_analytics_event(
    event: AnalyticsEvent, 
    user_id: Optional[str]
) -> None:
    """
    Process an analytics event in the background.
    
    This function processes events asynchronously to avoid blocking
    the request handler, handles PHI detection, and stores the event.
    
    Args:
        event: Analytics event to process
        user_id: User ID from authentication
    """
    # Set user ID from authentication if not already set
    if not event.user_id and user_id:
        event.user_id = user_id
        
    # Convert event to dict for PHI scanning
    event_dict = event.dict()
    event_json = json.dumps(event_dict)
    
    # Ensure PHI detector is initialized
    phi_detector.ensure_initialized()
    
    # Check for PHI in the event data
    if phi_detector.contains_phi(event_json):
        logger.warning(
            f"PHI detected in analytics event {event.event_id}, "
            f"event type: {event.event_type}"
        )
        
        # Redact PHI from data field
        data_json = json.dumps(event_dict["data"])
        if phi_detector.contains_phi(data_json):
            redacted_data = phi_detector.redact_phi(data_json)
            event_dict["data"] = json.loads(redacted_data)
            logger.info(f"Redacted PHI from event {event.event_id}")
            
    # Save event to data store or send to analytics service
    # For now, just log it
    logger.info(
        f"Processing analytics event {event.event_id} "
        f"of type {event.event_type} for user {event.user_id}"
    )


async def _process_analytics_batch(
    events: List[AnalyticsEvent], 
    user_id: Optional[str]
) -> None:
    """
    Process a batch of analytics events.
    
    Args:
        events: List of analytics events to process
        user_id: User ID from authentication
    """
    for event in events:
        await _process_analytics_event(event, user_id)


async def _get_dashboard_data(
    timeframe: str, 
    cache: CacheService
) -> Dict[str, Any]:
    """
    Get analytics dashboard data.
    
    Args:
        timeframe: Time period for dashboard data
        cache: Cache service instance
        
    Returns:
        Dashboard data dictionary
    """
    # Try to get from cache first
    cache_key = f"{CacheNamespace.ANALYTICS}:dashboard:{timeframe}"
    cached_data = await cache.get(cache_key)
    
    if cached_data:
        logger.debug(f"Returning cached dashboard data for {timeframe}")
        return cached_data
        
    # Generate dashboard data (this would use data from database or analytics service)
    # For now, return dummy data
    dashboard_data = {
        "event_count": 1250,
        "unique_users": 120,
        "top_events": [
            {"event_type": EventType.CONTENT_VIEW, "count": 800},
            {"event_type": EventType.USER_LOGIN, "count": 350},
            {"event_type": EventType.FEATURE_USE, "count": 100}
        ],
        "hourly_breakdown": [
            {"hour": i, "count": 10 + i * 5} for i in range(24)
        ]
    }
    
    # Cache dashboard data
    await cache.set(cache_key, dashboard_data, expiration=300)  # 5 minutes
    
    return dashboard_data


@router.post(
    "/events",
    response_model=ApiResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RateLimitDependency(api_tier="analytics", max_requests=50, window_seconds=60))]
)
async def record_analytics_event(
    event: AnalyticsEvent,
    background_tasks: BackgroundTasks,
    cache: CacheService = Depends(get_cache_service),
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> ApiResponse:
    """
    Record an analytics event.
    
    This endpoint accepts and processes individual analytics events,
    handling them asynchronously for better performance.
    
    Args:
        event: Analytics event data
        background_tasks: FastAPI background tasks
        cache: Cache service
        user: Authenticated user information
        
    Returns:
        API response with event ID
    """
    user_id = user.get("sub") if user else None
    
    # Increment rate limiting counter for analytics events
    rate_key = f"{CacheNamespace.ANALYTICS}:rate:{user_id or 'anonymous'}"
    await cache.increment(rate_key)
    await cache.expire(rate_key, 3600)  # 1 hour
    
    # Process event in background
    background_tasks.add_task(_process_analytics_event, event, user_id)
    
    return ApiResponse(
        status="success",
        message="Event accepted for processing",
        data={"event_id": event.event_id}
    )


@router.post(
    "/events/batch",
    response_model=ApiResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RateLimitDependency(api_tier="analytics_batch", max_requests=10, window_seconds=60))]
)
async def record_analytics_batch(
    batch: AnalyticsBatch,
    background_tasks: BackgroundTasks,
    cache: CacheService = Depends(get_cache_service),
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> ApiResponse:
    """
    Record a batch of analytics events.
    
    This endpoint accepts multiple events at once for more efficient processing.
    
    Args:
        batch: Batch of analytics events
        background_tasks: FastAPI background tasks
        cache: Cache service
        user: Authenticated user information
        
    Returns:
        API response with batch information
    """
    user_id = user.get("sub") if user else None
    
    # Increment rate limiting counter for analytics batches
    rate_key = f"{CacheNamespace.ANALYTICS}:batch_rate:{user_id or 'anonymous'}"
    await cache.increment(rate_key)
    await cache.expire(rate_key, 3600)  # 1 hour
    
    # Process all events in background
    background_tasks.add_task(_process_analytics_batch, batch.events, user_id)
    
    return ApiResponse(
        status="success",
        message=f"Batch of {len(batch.events)} events accepted for processing",
        data={"batch_size": len(batch.events), "batch_id": str(uuid.uuid4())}
    )


@router.get(
    "/dashboard",
    response_model=ApiResponse,
    dependencies=[Depends(RateLimitDependency(api_tier="analytics_dashboard", max_requests=20, window_seconds=60))]
)
async def get_analytics_dashboard(
    timeframe: str = "daily",
    cache: CacheService = Depends(get_cache_service),
    user: Dict[str, Any] = Depends(get_current_user)
) -> ApiResponse:
    """
    Get analytics dashboard data.
    
    This endpoint provides aggregated analytics data for dashboards.
    
    Args:
        timeframe: Time period for dashboard data (daily, weekly, monthly)
        cache: Cache service
        user: Authenticated user information
        
    Returns:
        API response with dashboard data
    """
    # Check user permissions (admin or analytics access required)
    if "role" not in user or user["role"] not in ["admin", "provider"]:
        return ApiResponse(
            status="error",
            message="Insufficient permissions to access analytics dashboard"
        )
        
    # Get dashboard data
    dashboard_data = await _get_dashboard_data(timeframe, cache)
    
    return ApiResponse(
        status="success",
        message=f"Analytics dashboard data for {timeframe} timeframe",
        data=dashboard_data
    )


@router.get(
    "/events/{event_id}",
    response_model=ApiResponse,
    dependencies=[Depends(RateLimitDependency(api_tier="analytics", max_requests=100, window_seconds=60))]
)
async def get_analytics_event(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> ApiResponse:
    """
    Get a specific analytics event by ID.
    
    This endpoint retrieves details of a specific event.
    
    Args:
        event_id: ID of the event to retrieve
        user: Authenticated user information
        
    Returns:
        API response with event data
    """
    # Check user permissions (admin or analytics access required)
    if "role" not in user or user["role"] not in ["admin", "provider"]:
        return ApiResponse(
            status="error",
            message="Insufficient permissions to access analytics events"
        )
        
    # In a real implementation, fetch the event from a database
    # For now, return a dummy event
    event = AnalyticsEvent(
        event_id=event_id,
        event_type=EventType.CONTENT_VIEW,
        timestamp=datetime.now().isoformat(),
        session_id="demo-session",
        user_id="demo-user",
        client_info=ClientInfo(browser="Chrome", os="Windows"),
        data={"page": "/dashboard", "time_spent": 120}
    )
    
    return ApiResponse(
        status="success",
        message=f"Analytics event {event_id}",
        data=event.dict()
    )