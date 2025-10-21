"""
Application configuration management using Pydantic BaseSettings.

This module centralizes all configuration settings for the Parly application,
including database connections, API settings, scraper configurations, and logging.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import os
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(default="sqlite:///data/parliament.db", env="DATABASE_URL")
    pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")

    @validator('url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL cannot be empty")
        if not (v.startswith('sqlite:///') or v.startswith('postgresql://') or v.startswith('mysql://')):
            raise ValueError("Unsupported database URL format")
        return v


class APISettings(BaseSettings):
    """API server configuration settings."""

    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    reload: bool = Field(default=False, env="API_RELOAD")
    workers: int = Field(default=1, env="API_WORKERS")

    # CORS settings
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: list = Field(default=["*"], env="CORS_ALLOW_HEADERS")


class ScraperSettings(BaseSettings):
    """Data scraper configuration settings."""

    # Rate limiting
    rate_limit_seconds: float = Field(default=1.0, env="SCRAPER_RATE_LIMIT")

    # Retry settings
    max_retries: int = Field(default=3, env="SCRAPER_MAX_RETRIES")
    retry_backoff_factor: float = Field(default=2.0, env="SCRAPER_BACKOFF_FACTOR")
    retry_status_codes: list = Field(default=[429, 500, 502, 503, 504], env="SCRAPER_RETRY_CODES")

    # Checkpoint settings
    checkpoint_interval: int = Field(default=100, env="SCRAPER_CHECKPOINT_INTERVAL")

    # Timeout settings
    request_timeout: int = Field(default=30, env="SCRAPER_TIMEOUT")

    # User agent
    user_agent: str = Field(
        default="Parly/1.0 (Parliamentary Data Scraper)",
        env="SCRAPER_USER_AGENT"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S", env="LOG_DATE_FORMAT")

    # File logging
    file_enabled: bool = Field(default=True, env="LOG_FILE_ENABLED")
    file_path: str = Field(default="logs/parly.log", env="LOG_FILE_PATH")
    file_max_bytes: int = Field(default=10*1024*1024, env="LOG_FILE_MAX_BYTES")  # 10MB
    file_backup_count: int = Field(default=5, env="LOG_FILE_BACKUP_COUNT")

    # Console logging
    console_enabled: bool = Field(default=True, env="LOG_CONSOLE_ENABLED")


class Settings(BaseSettings):
    """Main application settings."""

    # Application metadata
    app_name: str = Field(default="Parly", env="APP_NAME")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Directory paths
    data_dir: str = Field(default="data", env="DATA_DIR")
    logs_dir: str = Field(default="logs", env="LOGS_DIR")

    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    scraper: ScraperSettings = ScraperSettings()
    logging: LoggingSettings = LoggingSettings()

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        Path(self.data_dir).mkdir(exist_ok=True)
        Path(self.logs_dir).mkdir(exist_ok=True)

        # Ensure log file directory exists
        log_file_path = Path(self.logging.file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the database URL from settings."""
    return settings.database.url


def get_api_host() -> str:
    """Get the API host from settings."""
    return settings.api.host


def get_api_port() -> int:
    """Get the API port from settings."""
    return settings.api.port


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.environment.lower() == "development"


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.environment.lower() == "production"


# Convenience functions for backward compatibility
DATABASE_URL = get_database_url()
API_HOST = get_api_host()
API_PORT = get_api_port()
