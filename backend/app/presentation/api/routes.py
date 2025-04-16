"""
Centralized API router setup for the Novamind Digital Twin Backend Presentation Layer.

This module aggregates all API routers from the v1 endpoints and provides a
mechanism to include them in the main FastAPI application.
"""

import importlib
from typing import Dict, Callable, Any
from fastapi import APIRouter

# Create main API router for the presentation layer
api_router = APIRouter()

# Lazy router loading to prevent FastAPI from analyzing dependencies during import
def get_router(module_name: str) -> APIRouter:
    """
    Lazily load a router module from the v1 endpoints directory.
    
    Args:
        module_name: The name of the endpoint module (e.g., 'patients')
        
    Returns:
        The router instance from the specified module.
    """
    # Update the import path to the new location
    module_path = f"app.presentation.api.v1.endpoints.{module_name}"
    try:
        module = importlib.import_module(module_path)
        return module.router
    except ModuleNotFoundError:
        # Optionally log this or raise a more specific configuration error
        print(f"Error: Could not find router module at {module_path}")
        raise
    except AttributeError:
        # Optionally log this or raise a more specific configuration error
        print(f"Error: Module {module_path} does not have a 'router' attribute.")
        raise

# Include routers at runtime instead of import time
def setup_routers() -> None:
    """Set up all API routers with appropriate prefixes and tags."""
    
    # Patient router
    api_router.include_router(
        get_router("patients"), # Use the endpoint module name
        prefix="/v1/patients", # Add v1 prefix
        tags=["Patients"]
    )
    
    # Digital Twin router
    api_router.include_router(
        get_router("digital_twins"), # Use the endpoint module name
        prefix="/v1/digital-twins", # Add v1 prefix
        tags=["Digital Twins"]
    )
    
    # Temporal Neurotransmitter router
    api_router.include_router(
        get_router("temporal_neurotransmitter"),
        prefix="/v1/temporal", # Add v1 prefix
        tags=["Temporal Neurotransmitter System"]
    )
    
    # Actigraphy router
    api_router.include_router(
        get_router("actigraphy"),
        prefix="/v1/actigraphy", # Add v1 prefix
        tags=["Actigraphy Analysis"]
    )

    # --- Add New Routers ---
    # Appointments router
    # try:
    #     api_router.include_router(
    #         get_router("appointments"),
    #         prefix="/v1/appointments",
    #         tags=["Appointments"]
    #     )
    # except (ModuleNotFoundError, AttributeError):
    #     print("Appointments router not found or setup incorrectly, skipping.")

    # Clinical Sessions router
    # try:
    #     api_router.include_router(
    #         get_router("clinical_sessions"),
    #         prefix="/v1/sessions", # Using /sessions for brevity
    #         tags=["Clinical Sessions"]
    #     )
    # except (ModuleNotFoundError, AttributeError):
    #     print("Clinical Sessions router not found or setup incorrectly, skipping.")

    # Symptom Assessments router
    # try:
    #     api_router.include_router(
    #         get_router("symptom_assessments"),
    #         prefix="/v1/assessments", # Using /assessments
    #         tags=["Symptom Assessments"]
    #     )
    # except (ModuleNotFoundError, AttributeError):
    #     print("Symptom Assessments router not found or setup incorrectly, skipping.")
    # --- End New Routers ---

    # --- Add Moved Routers ---
    # Analytics router
    try:
        api_router.include_router(
            get_router("analytics_endpoints"), # Use the filename
            prefix="/v1/analytics", # Example prefix
            tags=["Analytics"]
        )
    except (ModuleNotFoundError, AttributeError):
        print("Analytics router not found or setup incorrectly, skipping.")
        
    # Biometric Alerts router
    try:
        api_router.include_router(
            get_router("biometric_alerts"), # Use the filename
            prefix="/v1/biometric-alerts", # Example prefix
            tags=["Biometric Alerts"]
        )
    except (ModuleNotFoundError, AttributeError):
        print("Biometric Alerts router not found or setup incorrectly, skipping.")
    # --- End Moved Routers ---

    # Placeholder for Auth router (if implemented in endpoints/auth.py)
    # try:
    #     api_router.include_router(
    #         get_router("auth"),
    #         prefix="/v1/auth",
    #         tags=["Authentication"]
    #     )
    # except (ModuleNotFoundError, AttributeError):
    #     print("Auth router not found or setup incorrectly, skipping.")

    # XGBoost router
    try:
        api_router.include_router(
            get_router("xgboost"),
            prefix="/ml/xgboost",
            tags=["XGBoost ML Services"]
        )
    except (ModuleNotFoundError, AttributeError):
        print("XGBoost router not found or setup incorrectly, skipping.")

# This function should be called by the main application (e.g., main.py)
# after the FastAPI app instance is created.
