"""
Search API routes integrating existing search functionality.
"""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_current_user_id, get_search_service
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])

class SearchRequest(BaseModel):
    """Schema for search request."""
    claim: str
    
    class Config:
        schema_extra = {
            "example": {
                "claim": "Eating vegetables daily improves overall health"
            }
        }

class SearchResponse(BaseModel):
    """Schema for search response."""
    claim: str
    is_verified: bool
    explanation: str
    sources: List[dict]
    confidence: float
    
    class Config:
        schema_extra = {
            "example": {
                "claim": "Eating vegetables daily improves overall health",
                "is_verified": True,
                "explanation": "Scientific evidence supports this claim...",
                "sources": [
                    {
                        "title": "Nutrition Study",
                        "url": "https://example.com/study",
                        "snippet": "Research shows..."
                    }
                ],
                "confidence": 0.85
            }
        }

@router.post("/verify", response_model=SearchResponse)
def search_verified_claim(
    request: SearchRequest,
    user_id: int = Depends(get_current_user_id),
    search_service: SearchService = Depends(get_search_service)
):
    """Search and verify a health claim."""
    result = search_service.search_verified_claim(request.claim, user_id)
    return SearchResponse(**result)

@router.get("/history")
def get_search_history(
    user_id: int = Depends(get_current_user_id),
    search_service: SearchService = Depends(get_search_service),
    limit: int = 10
):
    """Get user's search history."""
    return search_service.get_search_history(user_id, limit)
