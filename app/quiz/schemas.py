from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class QuizFromClaimRequest(BaseModel):
    claim: str
    num_questions: int = Field(default=5, ge=1, le=10)
    difficulty: str = Field(default="mixed")  # easy | medium | hard | mixed
    style: str = Field(default="conceptual")  # fact | conceptual | red_flags | mixed


class QuizItem(BaseModel):
    question: str
    options: List[str]
    correct_index: int = Field(ge=0, le=3)
    explanation: str
    source_url: str


class QuizFromClaimResponse(BaseModel):
    status: str
    items: List[QuizItem]
    meta: dict


class GradeQuizRequest(BaseModel):
    answers: List[int]
    key: List[int]


class GradeQuizResponse(BaseModel):
    status: str
    score: int
    total: int
    explanations: List[str]


