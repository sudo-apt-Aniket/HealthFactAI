"""
Authentication-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str
    password: str
    email: str
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "secretpassword",
                "email": "john@example.com"
            }
        }

class UserLogin(BaseModel):
    """Schema for user login."""
    username: str  # Can be username or email
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "secretpassword"
            }
        }

class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com"
            }
        }

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

class TokenData(BaseModel):
    """Schema for token data."""
    username: str
    user_id: int
    email: Optional[str] = None
