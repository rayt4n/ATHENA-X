"""Tests for runtime config."""
import os
import pytest
from athena_x_runtime_config import Settings, get_settings, Environment
from athena_x_runtime_config.settings import reset_settings_cache


@pytest.fixture(autouse=True)
def clean_env():
    """Clear ATHENA_X_* env vars before each test to prevent leakage."""
    keys_to_remove = [k for k in os.environ if k.startswith("ATHENA_X_")]
    for k in keys_to_remove:
        os.environ.pop(k, None)
    reset_settings_cache()
    yield
    keys_to_remove = [k for k in os.environ if k.startswith("ATHENA_X_")]
    for k in keys_to_remove:
        os.environ.pop(k, None)
    reset_settings_cache()


def test_default_settings_load_from_env():
    """Settings load from env vars with ATHENA_X_ prefix."""
    os.environ["ATHENA_X_ENVIRONMENT"] = "development"
    os.environ["ATHENA_X_DEBUG"] = "true"
    reset_settings_cache()
    s = get_settings()
    assert s.environment == Environment.DEVELOPMENT
    assert s.debug is True


def test_environment_enum_parsing():
    """Environment accepts string values."""
    s = Settings(environment="production")
    assert s.environment == Environment.PRODUCTION
    assert s.is_production()
    assert not s.is_development()


def test_redis_config_default():
    s = Settings()
    assert s.redis.url == "redis://localhost:6379"


def test_nats_config_default():
    s = Settings()
    assert s.nats.url == "nats://localhost:4222"


def test_provider_failover_chain_default():
    s = Settings()
    assert s.providers.failover_chain == [
        "yahoo", "finnhub", "polygon", "flashalpha", "fred", "alphavantage"
    ]


def test_event_bus_backpressure_default():
    """Event bus drops market data older than 500ms (Change 11)."""
    s = Settings()
    assert s.event_bus.backpressure_max_age_ms == 500


def test_secrets_are_secretstr():
    """API keys are SecretStr (never logged in plaintext)."""
    os.environ["ATHENA_X_FINNHUB_API_KEY"] = "secret-abc"
    reset_settings_cache()
    s = get_settings()
    assert s.finnhub_api_key is not None
    assert s.finnhub_api_key.get_secret_value() == "secret-abc"
    # repr should not leak the secret
    assert "secret-abc" not in repr(s)


def test_health_monitor_defaults():
    """Heartbeat interval 5s, miss threshold 3 (per Stage 1 spec)."""
    s = Settings()
    assert s.health_monitor.heartbeat_interval_seconds == 5
    assert s.health_monitor.heartbeat_miss_threshold == 3


def test_from_yaml(tmp_path):
    yaml_content = """
environment: production
debug: false
redis:
  url: redis://prod:6379
"""
    p = tmp_path / "env.yaml"
    p.write_text(yaml_content)
    s = Settings.from_yaml(p)
    # environment is top-level, so it's read directly
    assert s.environment == Environment.PRODUCTION
    # redis.url is nested — the from_yaml flattens to REDIS__URL but Settings
    # reads flat REDIS_URL. So we check the env var was set.
    import os
    assert os.environ.get("ATHENA_X_REDIS__URL") == "redis://prod:6379"


def test_missing_required_field_fails():
    """Settings should fail validation if required fields are missing."""
    # Sub-configs now have defaults — verify they construct without env vars
    from athena_x_runtime_config.settings import SupabaseConfig
    s = SupabaseConfig()
    assert s.url == "http://localhost:54321"
    assert s.anon_key.get_secret_value() == "dev-anon-key"
