"""Tests for standardization pipeline."""
import pytest
from datetime import datetime, timezone
from athena_x_standardizer_base import (
    StandardizationPipeline, StandardizationContext,
    SymbolStandardizer, TimezoneStandardizer, FieldMapper,
    PrecisionStandardizer, AssetClassifier,
)


def make_context(provider="yahoo"):
    return StandardizationContext(
        provider=provider,
        provider_version="1.0.0",
        raw_payload_id="raw-123",
        validation_id="val-456",
        validation_status="verified",
        confidence_score=0.95,
        quality_grade="A",
    )


def test_pipeline_runs_all_8_steps():
    """Pipeline runs all 8 standardization steps."""
    pipeline = StandardizationPipeline()
    record = {
        "symbol": "SPY.US",
        "last_price": 450.123456,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf",
    }
    result = pipeline.standardize(record, make_context(provider="yahoo"))
    assert result.success
    assert len(result.steps_completed) == 8


def test_symbol_standardization():
    """SPY.US resolves to SPY."""
    step = SymbolStandardizer()
    record = {"symbol": "SPY.US", "asset_class": "etf"}
    result = step.standardize(record, make_context(provider="yahoo"))
    assert result["symbol"] == "SPY"
    assert result["_original_symbol"] == "SPY.US"


def test_field_mapping():
    """close, last, price all map to last_price."""
    step = FieldMapper()
    record = {"close": 450.0, "last": 450.0, "price": 450.0, "symbol": "SPY"}
    result = step.standardize(record, make_context())
    # All three map to last_price — last one wins
    assert result["last_price"] == 450.0
    assert "close" not in result  # original key removed
    assert "symbol" in result  # unmapped fields kept


def test_precision_by_asset_class():
    """Equity prices get 2 decimals, FX gets 4."""
    step = PrecisionStandardizer()
    # Equity
    record = {"last_price": 450.123456, "asset_class": "equity"}
    result = step.standardize(record, make_context())
    assert result["last_price"] == 450.12
    # FX
    record = {"last_price": 150.12345678, "asset_class": "currency"}
    result = step.standardize(record, make_context())
    assert result["last_price"] == 150.1235


def test_asset_classification_defaults():
    """Asset classifier fills in defaults for missing fields."""
    step = AssetClassifier()
    record = {"symbol": "SPY", "asset_class": "etf"}
    result = step.standardize(record, make_context())
    assert result["market"] == "US"
    assert result["region"] == "US"
    assert result["exchange"] == "NYSEARCA"
    assert result["currency"] == "USD"


def test_canonical_schema_builder_adds_provenance():
    """Builder adds provenance + versioning."""
    from athena_x_standardizer_base import CanonicalSchemaBuilder
    step = CanonicalSchemaBuilder()
    record = {"symbol": "SPY", "last_price": 450.0, "asset_class": "etf"}
    result = step.standardize(record, make_context())
    assert result["source_provider"] == "yahoo"
    assert result["raw_payload_id"] == "raw-123"
    assert result["validation_id"] == "val-456"
    assert result["transformation_id"] is not None  # generated
    assert result["schema_version"] == "1.0.0"
    assert result["mapping_version"] == "1.0.0"
    assert result["provider_version"] == "1.0.0"
    assert "provider_metadata" in result
    assert "validation_metadata" in result


def test_pipeline_deterministic():
    """Same input + context → same output (replay determinism)."""
    pipeline1 = StandardizationPipeline()
    pipeline2 = StandardizationPipeline()
    record = {
        "symbol": "SPY", "last_price": 450.0,
        "timestamp": "2026-07-17T10:00:00Z",
        "asset_class": "etf",
    }
    ctx = make_context()
    r1 = pipeline1.standardize(record, ctx)
    r2 = pipeline2.standardize(record, ctx)
    # Same schema_version + mapping_version + steps
    assert r1.schema_version == r2.schema_version
    assert r1.mapping_version == r2.mapping_version
    assert r1.steps_completed == r2.steps_completed


def test_timezone_standardization():
    """Timestamps are converted to UTC + exchange local time."""
    step = TimezoneStandardizer()
    record = {
        "symbol": "SPY",
        "timestamp": "2026-07-17T14:30:00Z",  # 14:30 UTC = 10:30 ET
        "asset_class": "etf",
    }
    result = step.standardize(record, make_context())
    assert "session" in result
    assert "exchange_local_time" in result
    assert "trading_day" in result
    assert result["_original_timestamp"] == "2026-07-17T14:30:00Z"
