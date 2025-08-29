"""
Quiz API routes integrating existing quiz functionality.
"""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_current_user_id, get_quiz_service
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quiz", tags=["Quiz"])

class QuizGenerateRequest(BaseModel):
    """Schema for quiz generation request."""
    claim: str
    
    class Config:
        schema_extra = {
            "example": {
                "claim": "Regular exercise improves cardiovascular health"
            }
        }

class QuizResponse(BaseModel):
    """Schema for quiz response."""
    claim: str
    questions: List[dict]
    quiz_id: str
    error: str = None
    
    class Config:
        schema_extra = {
            "example": {
                "claim": "Regular exercise improves cardiovascular health",
                "questions": [
                    {
                        "id": 1,
                        "question": "Is this statement true?",
                        "options": ["True", "False", "Partially True", "Insufficient Evidence"]
                    }
                ],
                "quiz_id": "quiz_123_4567"
            }
        }

class QuizSubmitRequest(BaseModel):
    """Schema for quiz submission."""
    quiz_id: str
    answers: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "quiz_id": "quiz_123_4567",
                "answers": ["True", "Clinical trials", "Nutrition"]
            }
        }

class QuizGradeResponse(BaseModel):
    """Schema for quiz grading response."""
    quiz_id: str
    score: int
    total_questions: int
    score_percentage: float
    passed: bool
    results: List[dict]
    error: str = None
    
    class Config:
        schema_extra = {
            "example": {
                "quiz_id": "quiz_123_4567",
                "score": 2,
                "total_questions": 3,
                "score_percentage": 66.7,
                "passed": True,
                "results": [
                    {
                        "question_number": 1,
                        "user_answer": "True",
                        "correct_answer": "True",
                        "is_correct": True
                    }
                ]
            }
        }

@router.post("/generate", response_model=QuizResponse)
def generate_quiz_from_claim(
    request: QuizGenerateRequest,
    user_id: int = Depends(get_current_user_id),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """Generate a quiz from a health claim."""
    result = quiz_service.generate_quiz_from_claim(request.claim, user_id)
    return QuizResponse(**result)

@router.post("/submit", response_model=QuizGradeResponse)
def submit_quiz(
    request: QuizSubmitRequest,
    user_id: int = Depends(get_current_user_id),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """Submit and grade a quiz."""
    result = quiz_service.grade_quiz(request.quiz_id, request.answers, user_id)
    return QuizGradeResponse(**result)

@router.get("/history")
def get_quiz_history(
    user_id: int = Depends(get_current_user_id),
    quiz_service: QuizService = Depends(get_quiz_service),
    limit: int = 10
):
    """Get user's quiz history."""
    return quiz_service.get_quiz_history(user_id, limit)
