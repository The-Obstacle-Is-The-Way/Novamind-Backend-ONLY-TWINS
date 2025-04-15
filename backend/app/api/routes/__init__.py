"""
API routes package for the Novamind Digital Twin Backend.

This package contains all FastAPI routes organized by feature areas,
ensuring clean separation of concerns and maintaining the API structure.
"""
import importlib
from typing import Dict, Callable, Any
from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Lazy router loading to prevent FastAPI from analyzing dependencies during import
def get_router(module_name: str) -> APIRouter:
    """
    Lazily load a router module to prevent AsyncSession dependency analysis at import time.
    
    Args:
        module_name: The name of the module containing the router
        
    Returns:
        The router from the module
    """
    # Only import the module when this function is called
    module = importlib.import_module(f"app.api.routes.{module_name}")
    return module.router

# Include routers at runtime instead of import time
def setup_routers() -> None:
    """Set up all API routers with proper prefixes and tags."""
    # Temporal neurotransmitter router
    api_router.include_router(
        get_router("temporal_neurotransmitter"),
        prefix="/temporal",
        tags=["Temporal Neurotransmitter System"]
    )
    
    # Actigraphy router
    api_router.include_router(
        get_router("actigraphy"),
        prefix="/actigraphy",
        tags=["Actigraphy Analysis"]
    )
    
    # XGBoost router (uncomment when ready to use)
    # api_router.include_router(
    #     get_router("xgboost"),
    #     prefix="/ml/xgboost",
    #     tags=["XGBoost ML Services"]
    # )
    
    # Include Patient router
    api_router.include_router(
        get_router("patients_router"), # Corrected: Use simple module name
        prefix="/patients",
        tags=["Patients"]
    )
    
    # Additional routers would be included here
    # Example:
    # api_router.include_router(
    #     get_router("patient"),
    #     prefix="/patients",
    #     tags=["Patient Management"]
    # )

# This function must be called by the main application after FastAPI app is created
# to lazily load all routers and avoid AsyncSession analysis at import time