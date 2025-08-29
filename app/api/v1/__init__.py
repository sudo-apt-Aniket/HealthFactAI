"""
API v1 router initialization.
"""
from fastapi import APIRouter

from app.api.v1 import auth, progress, search, quiz

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth.router)
api_router.include_router(progress.router)
api_router.include_router(search.router)
api_router.include_router(quiz.router)

# Health check endpoint
@api_router.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
