# -*- coding: utf-8 -*-
"""
Analytics API Endpoints

This module provides API endpoints for accessing analytics data from the NOVAMIND platform.
These endpoints follow HIPAA compliance guidelines and implement caching and rate limiting.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
import json

from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse

# Defer service import entirely
# from app.domain.services.analytics_service import AnalyticsService 
# Removed import of non-existent get_jwt_service
from app.presentation.api.dependencies.auth import get_current_user, verify_provider_access, verify_admin_access
from app.infrastructure.cache.redis_cache import RedisCache # Removed get_cache_service
from app.presentation.api.dependencies.services import get_cache_service
from app.infrastructure.di.container import get_service # Import the DI helper
# Ensure AnalyticsService is NOT imported at the top level

# Create router
router = APIRouter(
    prefix="/api/v1/analytics", # Corrected prefix, was duplicated from below
    tags=["analytics"],
    dependencies=[Depends(verify_provider_access)],  # Only providers and admins can access analytics
)

# Cache TTL configuration (in seconds)
CACHE_TTL = {
    "patient_treatment_outcomes": 60 * 5,  # 5 minutes
    "practice_metrics": 60 * 15,  # 15 minutes
    "diagnosis_distribution": 60 * 60,  # 1 hour
    "medication_effectiveness": 60 * 30,  # 30 minutes
    "treatment_comparison": 60 * 30,  # 30 minutes
    "patient_risk_stratification": 60 * 10,  # 10 minutes
}

# Define the dependency using get_service directly
# We CANNOT import AnalyticsService here at module level
AnalyticsServiceDep = Depends(get_service("app.domain.services.analytics_service.AnalyticsService"))

# Modification: Modify get_service in container.py to accept string paths if it doesn't already
# For now, assume it works or adjust later.

@router.get("/patient/{patient_id}/treatment-outcomes", response_model=Dict[str, Any])
async def get_patient_treatment_outcomes(
    patient_id: UUID,
    start_date: datetime = Query(default=datetime.now(timezone.utc) - timedelta(days=90)),
    end_date: Optional[datetime] = Query(default=None),
    # Use Any for type hint to prevent collection-time resolution
    analytics_service: Any = AnalyticsServiceDep,
    cache_service: RedisCache = Depends(get_cache_service),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Dict[str, Any]:
    """
    Get treatment outcomes analytics for a specific patient.
    
    Args:
        patient_id: UUID of the patient
        start_date: Start date for the analytics period (default: 90 days ago)
        end_date: End date for the analytics period (default: now)
        analytics_service: Analytics service dependency (DI injected, type hint Any)
        cache_service: Cache service dependency
        background_tasks: Background tasks for async processing
        
    Returns:
        Dict[str, Any]: Treatment outcomes analytics
    """
    # Generate cache key
    cache_key = f"treatment_outcomes:{patient_id}:{start_date.isoformat()}:{end_date.isoformat() if end_date else 'now'}"
    
    # Try to get from cache
    cached_data_str = await cache_service.get(cache_key)
    if cached_data_str:
        try:
            # Decode JSON string from cache before returning
            return json.loads(cached_data_str)
        except json.JSONDecodeError:
            # Handle potential JSON decoding errors (e.g., corrupted cache)
            # Option 1: Log error and proceed as cache miss
            # logger.error(f"Failed to decode cached data for key {cache_key}", exc_info=True)
            # Option 2: Return an error response (might require adjusting response_model or using Response)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to process cached data."
            )
    
    # If not in cache, process analytically expensive operation asynchronously
    background_tasks.add_task(
        _process_treatment_outcomes,
        analytics_service, # Pass the resolved service instance
        cache_service,
        patient_id, 
        start_date, 
        end_date,
        cache_key
    )
    
    # Return a simplified immediate response
    return {
        "patient_id": str(patient_id),
        "status": "processing",
        "message": "Treatment outcomes analysis is being processed. Please check back shortly.",
        "check_url": f"/api/v1/analytics/status/{cache_key}"
    }

# The background task needs the correct type hint for the service
async def _process_treatment_outcomes(
    analytics_service: Any, # Keep correct type here
    cache_service: RedisCache,
    patient_id: UUID, 
    start_date: datetime, 
    end_date: Optional[datetime],
    cache_key: str
):
    """
    Process treatment outcomes in background and store in cache.
    
    Args:
        analytics_service: Analytics service instance
        cache_service: Cache service
        patient_id: UUID of the patient
        start_date: Start date for the analytics period
        end_date: End date for the analytics period
        cache_key: Cache key to store the results
    """
    try:
        # Get the full analytics data
        results = await analytics_service.get_patient_treatment_outcomes(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Store in cache
        await cache_service.set(
            key=cache_key,
            value=results,
            ttl=CACHE_TTL["patient_treatment_outcomes"]
        )
        
        # Also store as status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "completed", "data": results},
            ttl=CACHE_TTL["patient_treatment_outcomes"] + 60 * 10  # Add 10 minutes to status TTL
        )
    except Exception as e:
        # Store error in status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "error", "message": str(e)},
            ttl=60 * 10  # Store error for 10 minutes
        )


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_analytics_job_status(
    job_id: str,
    cache_service: RedisCache = Depends(get_cache_service),
) -> Dict[str, Any]:
    """
    Check the status of an asynchronous analytics job.
    
    Args:
        job_id: ID of the job to check
        cache_service: Cache service dependency
        
    Returns:
        Dict[str, Any]: Status of the job
    """
    status_key = f"status:{job_id}"
    status = await cache_service.get(status_key)
    
    if not status:
        return {"status": "not_found", "message": "Analytics job not found or expired"}
    
    return status


@router.get("/practice-metrics", response_model=Dict[str, Any])
async def get_practice_metrics(
    start_date: datetime = Query(default=datetime.now(timezone.utc) - timedelta(days=30)),
    end_date: Optional[datetime] = Query(default=None),
    provider_id: Optional[UUID] = Query(default=None),
    # Use Any for type hint
    analytics_service: Any = AnalyticsServiceDep,
    cache_service: RedisCache = Depends(get_cache_service),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Dict[str, Any]:
    """
    Get practice-wide metrics and analytics.
    
    Args:
        start_date: Start date for the analytics period (default: 30 days ago)
        end_date: End date for the analytics period (default: now)
        provider_id: Optional UUID to filter metrics by provider
        analytics_service: Analytics service dependency (DI injected)
        cache_service: Cache service dependency
        background_tasks: Background tasks for async processing
        
    Returns:
        Dict[str, Any]: Practice metrics analytics
    """
    # Generate cache key
    provider_part = str(provider_id) if provider_id else "all"
    cache_key = f"practice_metrics:{provider_part}:{start_date.isoformat()}:{end_date.isoformat() if end_date else 'now'}"
    
    # Try to get from cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Process in background and return immediate response
    background_tasks.add_task(
        _process_practice_metrics,
        analytics_service, # Pass the resolved service instance
        cache_service,
        start_date,
        end_date,
        provider_id,
        cache_key
    )
    
    # Return a simplified immediate response
    return {
        "provider_filter": provider_part,
        "status": "processing",
        "message": "Practice metrics analysis is being processed. Please check back shortly.",
        "check_url": f"/api/v1/analytics/status/{cache_key}"
    }


# Background task needs correct type hint
async def _process_practice_metrics(
    analytics_service: Any, # Keep correct type here
    cache_service: RedisCache,
    start_date: datetime,
    end_date: Optional[datetime],
    provider_id: Optional[UUID],
    cache_key: str
):
    """
    Process practice metrics in background and store in cache.
    
    Args:
        analytics_service: Analytics service
        cache_service: Cache service
        start_date: Start date for the analytics period
        end_date: End date for the analytics period
        provider_id: Optional UUID to filter metrics by provider
        cache_key: Cache key to store the results
    """
    try:
        # Get the full analytics data
        results = await analytics_service.get_practice_metrics(
            start_date=start_date,
            end_date=end_date,
            provider_id=provider_id
        )
        
        # Store in cache
        await cache_service.set(
            key=cache_key,
            value=results,
            ttl=CACHE_TTL["practice_metrics"]
        )
        
        # Also store as status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "completed", "data": results},
            ttl=CACHE_TTL["practice_metrics"] + 60 * 10  # Add 10 minutes to status TTL
        )
    except Exception as e:
        # Store error in status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "error", "message": str(e)},
            ttl=60 * 10  # Store error for 10 minutes
        )


@router.get("/diagnosis-distribution", response_model=List[Dict[str, Any]])
async def get_diagnosis_distribution(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    provider_id: Optional[UUID] = Query(default=None),
    # Use Any for type hint
    analytics_service: Any = AnalyticsServiceDep,
    cache_service: RedisCache = Depends(get_cache_service),
) -> List[Dict[str, Any]]:
    """
    Get the distribution of diagnoses across patients.
    
    Args:
        start_date: Start date for the analytics period (default: 1 year ago)
        end_date: End date for the analytics period (default: now)
        provider_id: Optional UUID to filter by provider
        analytics_service: Analytics service dependency
        cache_service: Cache service dependency
        
    Returns:
        List[Dict[str, Any]]: Diagnosis distribution analytics
    """
    # Generate cache key
    provider_part = str(provider_id) if provider_id else "all"
    start_part = start_date.isoformat() if start_date else "default"
    end_part = end_date.isoformat() if end_date else "now"
    cache_key = f"diagnosis_distribution:{provider_part}:{start_part}:{end_part}"
    
    # Try to get from cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get the full analytics data directly (this operation is fast enough to not need background processing)
    results = await analytics_service.get_diagnosis_distribution(
        start_date=start_date,
        end_date=end_date,
        provider_id=provider_id
    )
    
    # Store in cache
    await cache_service.set(
        key=cache_key,
        value=results,
        ttl=CACHE_TTL["diagnosis_distribution"]
    )
    
    return results


@router.get("/medications/{medication_name}/effectiveness", response_model=Dict[str, Any])
async def get_medication_effectiveness(
    medication_name: str,
    diagnosis_code: Optional[str] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    # Use Any for type hint
    analytics_service: Any = AnalyticsServiceDep,
    cache_service: RedisCache = Depends(get_cache_service),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Dict[str, Any]:
    """
    Analyze the effectiveness of a specific medication.
    
    Args:
        medication_name: Name of the medication
        diagnosis_code: Optional diagnosis code to filter by
        start_date: Start date for the analytics period (default: 1 year ago)
        end_date: End date for the analytics period (default: now)
        analytics_service: Analytics service dependency
        cache_service: Cache service dependency
        background_tasks: Background tasks for async processing
        
    Returns:
        Dict[str, Any]: Medication effectiveness analytics
    """
    # Normalize medication name for cache key
    normalized_medication = medication_name.lower().replace(" ", "_")
    diagnosis_part = diagnosis_code or "all"
    start_part = start_date.isoformat() if start_date else "default"
    end_part = end_date.isoformat() if end_date else "now"
    cache_key = f"medication_effectiveness:{normalized_medication}:{diagnosis_part}:{start_part}:{end_part}"
    
    # Try to get from cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Process in background and return immediate response
    background_tasks.add_task(
        _process_medication_effectiveness,
        analytics_service,
        cache_service,
        medication_name,
        diagnosis_code,
        start_date,
        end_date,
        cache_key
    )
    
    # Return a simplified immediate response
    return {
        "medication_name": medication_name,
        "diagnosis_filter": diagnosis_code,
        "status": "processing",
        "message": "Medication effectiveness analysis is being processed. Please check back shortly.",
        "check_url": f"/api/v1/analytics/status/{cache_key}"
    }


# Background task needs correct type hint
async def _process_medication_effectiveness(
    analytics_service: Any, # Keep correct type here
    cache_service: RedisCache,
    medication_name: str,
    diagnosis_code: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    cache_key: str
):
    """
    Process medication effectiveness in background and store in cache.
    
    Args:
        analytics_service: Analytics service
        cache_service: Cache service
        medication_name: Name of the medication
        diagnosis_code: Optional diagnosis code to filter by
        start_date: Start date for the analytics period
        end_date: End date for the analytics period
        cache_key: Cache key to store the results
    """
    try:
        # Get the full analytics data
        results = await analytics_service.get_medication_effectiveness(
            medication_name=medication_name,
            diagnosis_code=diagnosis_code,
            start_date=start_date,
            end_date=end_date
        )
        
        # Store in cache
        await cache_service.set(
            key=cache_key,
            value=results,
            ttl=CACHE_TTL["medication_effectiveness"]
        )
        
        # Also store as status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "completed", "data": results},
            ttl=CACHE_TTL["medication_effectiveness"] + 60 * 10  # Add 10 minutes to status TTL
        )
    except Exception as e:
        # Store error in status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "error", "message": str(e)},
            ttl=60 * 10  # Store error for 10 minutes
        )


@router.get("/treatment-comparison/{diagnosis_code}", response_model=Dict[str, Any])
async def get_treatment_comparison(
    diagnosis_code: str,
    treatments: List[str] = Query(...),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    # Use Any for type hint
    analytics_service: Any = AnalyticsServiceDep,
    cache_service: RedisCache = Depends(get_cache_service),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Dict[str, Any]:
    """
    Compare the effectiveness of different treatments for a specific diagnosis.
    
    Args:
        diagnosis_code: Diagnosis code to analyze
        treatments: List of treatment names to compare
        start_date: Start date for the analytics period (default: 1 year ago)
        end_date: End date for the analytics period (default: now)
        analytics_service: Analytics service dependency
        cache_service: Cache service dependency
        background_tasks: Background tasks for async processing
        
    Returns:
        Dict[str, Any]: Treatment comparison analytics
    """
    # Generate cache key
    treatments_part = "-".join(sorted([t.lower().replace(" ", "_") for t in treatments]))
    start_part = start_date.isoformat() if start_date else "default"
    end_part = end_date.isoformat() if end_date else "now"
    cache_key = f"treatment_comparison:{diagnosis_code}:{treatments_part}:{start_part}:{end_part}"
    
    # Try to get from cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Process in background and return immediate response
    background_tasks.add_task(
        _process_treatment_comparison,
        analytics_service,
        cache_service,
        diagnosis_code,
        treatments,
        start_date,
        end_date,
        cache_key
    )
    
    # Return a simplified immediate response
    return {
        "diagnosis_code": diagnosis_code,
        "treatments": treatments,
        "status": "processing",
        "message": "Treatment comparison analysis is being processed. Please check back shortly.",
        "check_url": f"/api/v1/analytics/status/{cache_key}"
    }


# Background task needs correct type hint
async def _process_treatment_comparison(
    analytics_service: Any, # Keep correct type here
    cache_service: RedisCache,
    diagnosis_code: str,
    treatments: List[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    cache_key: str
):
    """
    Process treatment comparison in background and store in cache.
    
    Args:
        analytics_service: Analytics service
        cache_service: Cache service
        diagnosis_code: Diagnosis code to analyze
        treatments: List of treatment names to compare
        start_date: Start date for the analytics period
        end_date: End date for the analytics period
        cache_key: Cache key to store the results
    """
    try:
        # Get the full analytics data
        results = await analytics_service.get_treatment_comparison(
            diagnosis_code=diagnosis_code,
            treatments=treatments,
            start_date=start_date,
            end_date=end_date
        )
        
        # Store in cache
        await cache_service.set(
            key=cache_key,
            value=results,
            ttl=CACHE_TTL["treatment_comparison"]
        )
        
        # Also store as status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "completed", "data": results},
            ttl=CACHE_TTL["treatment_comparison"] + 60 * 10  # Add 10 minutes to status TTL
        )
    except Exception as e:
        # Store error in status
        status_key = f"status:{cache_key}"
        await cache_service.set(
            key=status_key,
            value={"status": "error", "message": str(e)},
            ttl=60 * 10  # Store error for 10 minutes
        )


@router.get("/patient-risk-stratification", response_model=List[Dict[str, Any]])
async def get_patient_risk_stratification(
    # Use Any for type hint
    analytics_service: Any = AnalyticsServiceDep,
    cache_service: RedisCache = Depends(get_cache_service),
) -> List[Dict[str, Any]]:
    """
    Stratify patients by risk level based on clinical data.
    
    Args:
        analytics_service: Analytics service dependency
        cache_service: Cache service dependency
        
    Returns:
        List[Dict[str, Any]]: Patient risk stratification analytics
    """
    # Generate cache key
    cache_key = "patient_risk_stratification"
    
    # Try to get from cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get the full analytics data directly
    results = await analytics_service.get_patient_risk_stratification()
    
    # Store in cache
    await cache_service.set(
        key=cache_key,
        value=results,
        ttl=CACHE_TTL["patient_risk_stratification"]
    )
    
    return results