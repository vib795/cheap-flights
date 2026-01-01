from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Amadeus API
    amadeus_client_id: str = ""
    amadeus_client_secret: str = ""
    amadeus_env: str = "test"  # "test" or "prod"

    # TravelBriefing
    travelbriefing_base_url: str = "https://travelbriefing.org"

    # App config
    app_cache_ttl_seconds: int = 1800  # 30 minutes
    app_database_url: str = "sqlite+aiosqlite:///./geoflight.db"

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
