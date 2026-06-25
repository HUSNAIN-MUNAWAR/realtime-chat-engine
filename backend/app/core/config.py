from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_name: str = "Real-Time-Chat-Engine-for-100k-Users"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] | str = ["http://localhost:3000"]
    database_url: str = "postgresql+asyncpg://chat:chat@postgres:5432/chat"
    sync_database_url: str = "postgresql+psycopg2://chat:chat@postgres:5432/chat"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "change-me-super-secret-local-only"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    seed_demo_data: bool = True
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin12345!"
    enable_load_test_endpoints: bool = True
    load_test_secret: str = "local-load-test-secret"
    max_message_bytes: int = 4096
    message_rate_limit_per_minute: int = 120
    presence_ttl_seconds: int = 45
    risk_model_path: str = "/app/mlops/models/current/risk_model.json"
    @field_validator("backend_cors_origins")
    @classmethod
    def split_origins(cls, v):
        return [x.strip() for x in v.split(",") if x.strip()] if isinstance(v, str) else v

@lru_cache
def get_settings() -> Settings:
    return Settings()
settings = get_settings()
