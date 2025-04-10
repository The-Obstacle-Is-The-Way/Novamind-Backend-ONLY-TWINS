"""
API routes package for the Novamind Digital Twin Backend.

This package contains all FastAPI routes organized by feature areas,
ensuring clean separation of concerns and maintaining the API structure.
"""
from fastapi import APIRouter

from app.api.routes import temporal_neurotransmitter

# Create main API router
api_router = APIRouter()

# Include routers from individual modules
api_router.include_router(
    temporal_neurotransmitter.router,
    prefix="/temporal",
    tags=["Temporal Neurotransmitter System"]
)

# Additional routers would be included here
# Example:
# api_router.include_router(
#     patient.router,
#     prefix="/patients",
#     tags=["Patient Management"]
# )