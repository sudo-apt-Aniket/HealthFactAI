"""
Progress-related Pydantic schemas.
"""
from typing import Dict, Optional
from pydantic import BaseModel

class ProgressResponse(BaseModel):
    """Schema for user progress response."""
    total_facts: int
    current_streak: int
    longest_streak: int
    categories: Dict[str, int]
    last_activity: Optional[str] = None
    facts_this_week: int = 0
    
    class Config:
        schema_extra = {
            "example": {
                "total_facts": 15,
                "current_streak": 3,
                "longest_streak": 7,
                "categories": {
                    "Nutrition": 5,
                    "Exercise": 3,
                    "Mental Health": 2,
                    "Quiz": 5
                },
                "last_activity": "2024-01-15",
                "facts_this_week": 8
            }
        }

class CategoriesResponse(BaseModel):
    """Schema for categories breakdown response."""
    categories: Dict[str, int]
    total: int
    
    class Config:
        schema_extra = {
            "example": {
                "categories": {
                    "Nutrition": 5,
                    "Exercise": 3,
                    "Mental Health": 2
                },
                "total": 10
            }
        }
