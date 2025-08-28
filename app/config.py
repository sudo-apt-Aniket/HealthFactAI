import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


load_dotenv()  # Load environment vars from a .env file at project root if present


class Settings(BaseModel):
    bing_api_key: str | None = Field(default=os.getenv("BING_API_KEY"))
    langsearch_api_key: str | None = Field(default=os.getenv("LANGSEARCH_API_KEY"))
    openai_api_key: str | None = Field(default=os.getenv("OPENAI_API_KEY"))
    allowed_domains: list[str] = Field(default_factory=lambda: [
        d.strip().lower() for d in (os.getenv("ALLOWED_DOMAINS", "who.int,cdc.gov,nhs.uk,nih.gov,ncbi.nlm.nih.gov,health.gov.au,cochrane.org").split(",")) if d.strip()
    ])
    use_embed_rerank: bool = Field(default=(os.getenv("USE_EMBED_RERANK", "false").lower() == "true"))
    use_langsearch_rerank: bool = Field(default=(os.getenv("USE_LANGSEARCH_RERANK", "false").lower() == "true"))
    # Auth
    secret_key: str = Field(default=os.getenv("SECRET_KEY", "supersecretkey"))
    algorithm: str = Field(default=os.getenv("ALGORITHM", "HS256"))
    access_token_expire_minutes: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))

    @field_validator("allowed_domains")
    @classmethod
    def _validate_allowlist(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("ALLOWED_DOMAINS must not be empty")
        return v
    request_timeout_seconds: int = Field(default=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")))
    cache_ttl_search_min: int = Field(default=int(os.getenv("CACHE_TTL_SEARCH_MIN", "30")))
    cache_ttl_page_min: int = Field(default=int(os.getenv("CACHE_TTL_PAGE_MIN", "60")))


settings = Settings()


