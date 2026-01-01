from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Amadeus API
    amadeus_client_id: str = ""
    amadeus_client_secret: str = ""
    amadeus_env: str = "test"  # "test" or "prod"

    # TravelBriefing
    travelbriefing_base_url: str = "https://travelbriefing.org"

    # AI Visa Research (optional fallback)
    enable_ai_visa_research: bool = False  # Set to True to enable AI-powered fallback
    anthropic_api_key: str = ""  # Required if enable_ai_visa_research=True

    # App config
    app_cache_ttl_seconds: int = 1800  # 30 minutes

    # Database configuration
    # For local dev: sqlite+aiosqlite:///./geoflight.db
    # For Docker: postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = "sqlite+aiosqlite:///./geoflight.db"

    # Redis configuration (for distributed caching in production)
    # Set redis_url to enable Redis caching instead of in-memory
    # Example: redis://localhost:6379/0 or redis://redis:6379/0 (Docker)
    redis_url: str = ""  # Empty = use in-memory cache

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def amadeus_base_url(self) -> str:
        """Get Amadeus API base URL based on environment"""
        if self.amadeus_env == "prod":
            return "https://api.amadeus.com"
        return "https://test.api.amadeus.com"


settings = Settings()
