"""
Progress tracking API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_progress_service, get_current_user_id
from app.services.progress_service import ProgressService
from app.schemas.progress import ProgressResponse, CategoriesResponse

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.get("/", response_model=ProgressResponse)
def get_user_progress(
    user_id: int = Depends(get_current_user_id),
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Get current user's progress data."""
    progress = progress_service.get_user_progress(user_id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User progress not found"
        )
    
    return ProgressResponse(**progress)

@router.get("/categories", response_model=CategoriesResponse)
def get_categories_breakdown(
    user_id: int = Depends(get_current_user_id),
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Get user's fact categories breakdown for pie chart."""
    progress = progress_service.get_user_progress(user_id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User progress not found"
        )
    
    categories = progress.get("categories", {})
    total = sum(categories.values())
    
    return CategoriesResponse(categories=categories, total=total)
