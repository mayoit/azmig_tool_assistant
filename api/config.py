"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://azmig_user:azmig_secure_password@localhost:5432/azmig_db"
    
    # Redis
    redis_url: str = "redis://:redis_secure_password@localhost:6379/0"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # Security
    secret_key: str = "change_this_to_a_random_secret_key_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Azure Configuration
    azure_subscription_id: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",  # Vue.js dev server
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # File Upload
    max_upload_size_mb: int = 50
    upload_dir: str = "/app/uploads"
    allowed_extensions: set[str] = {".xlsx", ".xls", ".csv"}
    
    # Celery
    celery_broker_url: str = "redis://:redis_secure_password@localhost:6379/0"
    celery_result_backend: str = "redis://:redis_secure_password@localhost:6379/1"
    celery_task_time_limit: int = 3600  # 1 hour
    celery_task_soft_time_limit: int = 3300  # 55 minutes
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
