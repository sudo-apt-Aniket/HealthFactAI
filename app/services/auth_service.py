"""
Authentication service with business logic.
"""
from typing import Optional, Tuple
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserLogin, TokenData

class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            user_id: int = payload.get("uid")
            email: str = payload.get("email")
            
            if username is None or user_id is None:
                return None
            
            return TokenData(username=username, user_id=user_id, email=email)
        except JWTError:
            return None
    
    def register_user(self, user_create: UserCreate) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user.
        Returns: (success, message, user)
        """
        # Check if username already exists
        if self.user_repository.exists_username(user_create.username):
            return False, "Username already exists", None
        
        # Check if email already exists (if provided)
        if user_create.email and self.user_repository.exists_email(user_create.email):
            return False, "Email already exists", None
        
        # Create new user
        hashed_password = self.get_password_hash(user_create.password)
        user = User(
            username=user_create.username,
            password=hashed_password,
            email=user_create.email,
            facts_learned="[]",
            current_streak=0,
            longest_streak=0,
            total_facts_count=0,
            last_activity_date=None
        )
        
        try:
            created_user = self.user_repository.create(user)
            return True, "User registered successfully", created_user
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None
    
    def authenticate_user(self, user_login: UserLogin) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate a user login.
        Returns: (success, message, user)
        """
        # Get user by username or email
        user = self.user_repository.get_by_username_or_email(user_login.username)
        
        if not user:
            return False, "Invalid credentials", None
        
        if not self.verify_password(user_login.password, user.password):
            return False, "Invalid credentials", None
        
        return True, "Authentication successful", user
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token."""
        token_data = self.verify_token(token)
        if not token_data:
            return None
        
        return self.user_repository.get_by_id(token_data.user_id)
