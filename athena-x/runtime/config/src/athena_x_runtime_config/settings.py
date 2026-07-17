"""
ATHENA-X global settings.

Loads from (in priority order — first wins):
  1. Environment variables (ATHEMA_X_*)
  2. .env file
  3. YAML config file (configs/<env>/env.yaml)
  4. Defaults defined here

Validated at startup — fail fast on missing required vars.
"""
from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

from .environments import Environment


class SupabaseConfig(BaseModel):
    url: str = Field(default="http://localhost:54321", description="Supabase project URL")
    anon_key: SecretStr = Field(default=SecretStr("dev-anon-key"), description="Supabase anon key")
    service_role_key: SecretStr = Field(default=SecretStr("dev-service-role-key"),
                                         description="Supabase service role key")


class RedisConfig(BaseModel):
    url: str = Field(default="redis://localhost:6379", description="Redis URL")


class NATSConfig(BaseModel):
    url: str = Field(default="nats://localhost:4222", description="NATS URL")


class PythonBackendConfig(BaseModel):
    url: str = Field(default="http://localhost:8000", description="Python backend URL")


class ProviderConfig(BaseModel):
    failover_chain: list[str] = Field(
        default_factory=lambda: ["yahoo", "finnhub", "polygon", "flashalpha", "fred", "alphavantage"]
    )
    cache_ttl_seconds: int = Field(default=5, ge=0)


class AIRuntimeConfig(BaseModel):
    gpu_device: str = Field(default="cpu")
    onnx_cache_path: str = Field(default="./.cache/onnx")


class FeatureFlags(BaseModel):
    enable_automation: bool = False
    enable_self_correction: bool = True
    enable_backtesting: bool = True


class HealthMonitorConfig(BaseModel):
    heartbeat_interval_seconds: int = Field(default=5, ge=1)
    heartbeat_miss_threshold: int = Field(default=3, ge=1)
    health_check_interval_seconds: int = Field(default=10, ge=1)


class EventBusConfig(BaseModel):
    backend: str = Field(default="redis", description="redis | nats")
    backpressure_max_age_ms: int = Field(default=500, ge=0,
        description="Drop market data events older than this (Change 11 backpressure)")


class Settings(BaseSettings):
    """Global ATHENA-X settings. Loaded once at startup via get_settings()."""

    model_config = SettingsConfigDict(
        env_prefix="ATHENA_X_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    app_name: str = "athena-x"
    app_version: str = "0.1.0"

    # Sub-configs — these are NOT auto-bound from env vars.
    # Use the getters below (e.g., settings.supabase) which compose from env vars.
    _supabase: SupabaseConfig | None = None
    _redis: RedisConfig | None = None
    _nats: NATSConfig | None = None
    _python_backend: PythonBackendConfig | None = None
    _providers: ProviderConfig | None = None
    _ai_runtime: AIRuntimeConfig | None = None
    _feature_flags: FeatureFlags | None = None
    _health_monitor: HealthMonitorConfig | None = None
    _event_bus: EventBusConfig | None = None

    # Secrets (passed via env vars directly)
    yahoo_api_key: SecretStr | None = None
    finnhub_api_key: SecretStr | None = None
    polygon_api_key: SecretStr | None = None
    flashalpha_api_key: SecretStr | None = None
    fred_api_key: SecretStr | None = None
    alpha_vantage_api_key: SecretStr | None = None
    databento_api_key: SecretStr | None = None
    trading_economics_api_key: SecretStr | None = None
    reuters_api_key: SecretStr | None = None
    wsj_api_key: SecretStr | None = None
    sec_user_agent: str = Field(default="ATHENA-X research@example.com")

    # Observability
    sentry_dsn: str | None = None
    otel_exporter_otlp_endpoint: str | None = None

    # Direct env vars for sub-configs (flat, not nested)
    supabase_url: str = Field(default="http://localhost:54321")
    supabase_anon_key: SecretStr = Field(default=SecretStr("dev-anon-key"))
    supabase_service_role_key: SecretStr = Field(default=SecretStr("dev-service-role-key"))
    redis_url: str = Field(default="redis://localhost:6379")
    nats_url: str = Field(default="nats://localhost:4222")
    python_backend_url: str = Field(default="http://localhost:8000")

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, v: Any) -> Environment:
        if isinstance(v, Environment):
            return v
        if isinstance(v, str):
            return Environment(v.lower())
        return Environment.DEVELOPMENT

    @property
    def supabase(self) -> SupabaseConfig:
        return SupabaseConfig(
            url=self.supabase_url,
            anon_key=self.supabase_anon_key,
            service_role_key=self.supabase_service_role_key,
        )

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(url=self.redis_url)

    @property
    def nats(self) -> NATSConfig:
        return NATSConfig(url=self.nats_url)

    @property
    def python_backend(self) -> PythonBackendConfig:
        return PythonBackendConfig(url=self.python_backend_url)

    @property
    def providers(self) -> ProviderConfig:
        return ProviderConfig()

    @property
    def ai_runtime(self) -> AIRuntimeConfig:
        return AIRuntimeConfig()

    @property
    def feature_flags(self) -> FeatureFlags:
        return FeatureFlags()

    @property
    def health_monitor(self) -> HealthMonitorConfig:
        return HealthMonitorConfig()

    @property
    def event_bus(self) -> EventBusConfig:
        return EventBusConfig()

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Settings":
        """Load settings from a YAML file (overrides env vars).

        YAML keys map to Settings fields using nested structure.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # Flatten nested YAML into ATHENA_X_-prefixed env vars
        env_prefix = "ATHENA_X_"
        def flatten(d: dict, prefix: str = "") -> None:
            for k, v in d.items():
                key = f"{prefix}{k.upper()}"
                if isinstance(v, dict):
                    flatten(v, f"{key}__")
                else:
                    os.environ.setdefault(f"{env_prefix}{key}", str(v))

        flatten(data)
        return cls()

    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance. Loads once at startup."""
    # Try to load YAML config based on ATHENA_X_ENVIRONMENT
    env = os.getenv("ATHENA_X_ENVIRONMENT", "development")
    config_path = Path(f"configs/{env}/env.yaml")
    if config_path.exists():
        return Settings.from_yaml(config_path)
    return Settings()


def reset_settings_cache() -> None:
    """Reset the settings cache (for testing)."""
    get_settings.cache_clear()
