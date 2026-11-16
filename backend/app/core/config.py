from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CHESTS_", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1, le=65535)
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:5173"]
    max_connections: int = Field(8, ge=1, le=100)
    max_queue_size: int = Field(100, ge=1, le=1000)
    max_chests: int = Field(1000, ge=10, le=10000)
    expired_retention_seconds: int = Field(300, ge=10, le=86400)
    cleanup_interval_seconds: int = Field(10, ge=1, le=300)
    monitor_requests_per_minute: int = Field(10, ge=1, le=120)
    reconnect_max_attempts: int = Field(5, ge=0, le=20)
    reconnect_base_seconds: float = Field(2.0, ge=0.1, le=60)
    demo_mode: bool = False
    initial_streams: str = ""

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @property
    def initial_usernames(self) -> list[str]:
        return [value.strip().lstrip("@").lower() for value in self.initial_streams.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
