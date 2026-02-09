# App config from env vars
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://urwallet:password@localhost:5432/urwallet"
    supabase_url: str = ""
    supabase_jwt_secret: str = ""  # For HS256 (legacy projects)
    cors_origins: str = "*"
    groq_api_key: str = ""
    debug: bool = False
    
    # Currency conversion (ExchangeRate-API)
    fx_api_key: str = ""
    fx_api_base_url: str = "https://v6.exchangerate-api.com/v6"
    
    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
