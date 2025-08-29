"""
Dependency injection container and FastAPI dependencies.
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.progress_service import ProgressService
from app.services.search_service import SearchService
from app.services.quiz_service import QuizService
from app.models.user import User

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Repository instances (singleton pattern)
_user_repository = None
_auth_service = None
_progress_service = None
_search_service = None
_quiz_service = None

def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository

def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(user_repository)
    return _auth_service

def get_progress_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> ProgressService:
    """Get progress service instance."""
    global _progress_service
    if _progress_service is None:
        _progress_service = ProgressService(user_repository)
    return _progress_service

def get_search_service(
    progress_service: ProgressService = Depends(get_progress_service)
) -> SearchService:
    """Get search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService(progress_service)
    return _search_service

def get_quiz_service(
    progress_service: ProgressService = Depends(get_progress_service)
) -> QuizService:
    """Get quiz service instance."""
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService(progress_service)
    return _quiz_service

def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user."""
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_user_id(current_user: User = Depends(get_current_user)) -> int:
    """Get current user ID."""
    return current_user.id
