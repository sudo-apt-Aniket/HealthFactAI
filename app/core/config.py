

"""
Unified configuration settings for HealthFactAI.
Combines all existing and new functionality in a single source of truth.
"""
import os
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    """Unified application settings."""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "HealthFactAI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered health fact checking with gamification"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./healthfact.db"
    DB_NAME: str = "healthfact.db"
    
    # External API Keys
    bing_api_key: Optional[str] = Field(default=os.getenv("BING_API_KEY"))
    langsearch_api_key: Optional[str] = Field(default=os.getenv("LANGSEARCH_API_KEY"))
    openai_api_key: Optional[str] = Field(default=os.getenv("OPENAI_API_KEY"))
    
    # Security Settings
    secret_key: str = Field(default=os.getenv("SECRET_KEY", "supersecretkey"))
    algorithm: str = Field(default=os.getenv("ALGORITHM", "HS256"))
    access_token_expire_minutes: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    
    # Search & Retrieval Settings
    allowed_domains: List[str] = Field(default_factory=lambda: [
        d.strip().lower() for d in (os.getenv(
            "ALLOWED_DOMAINS", 
            "who.int,cdc.gov,nhs.uk,nih.gov,ncbi.nlm.nih.gov,health.gov.au,cochrane.org"
        ).split(",")) if d.strip()
    ])
    
    use_embed_rerank: bool = Field(default=(os.getenv("USE_EMBED_RERANK", "false").lower() == "true"))
    use_langsearch_rerank: bool = Field(default=(os.getenv("USE_LANGSEARCH_RERANK", "false").lower() == "true"))
    
    # Performance Settings
    request_timeout_seconds: int = Field(default=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")))
    cache_ttl_search_min: int = Field(default=int(os.getenv("CACHE_TTL_SEARCH_MIN", "30")))
    cache_ttl_page_min: int = Field(default=int(os.getenv("CACHE_TTL_PAGE_MIN", "60")))
    
    # CORS Settings
    allowed_origins: List[str] = Field(default_factory=lambda: [
        "http://localhost",
        "http://127.0.0.1", 
        "http://localhost:8501",  # Streamlit default
        "http://127.0.0.1:8501"
    ])
    
    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("ALLOWED_DOMAINS must not be empty")
        return [domain.lower().strip() for domain in v]
    
    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        return [origin.strip() for origin in v]

# Global settings instance
settings = Settings()
