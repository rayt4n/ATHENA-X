"""Tests for Market Standardization Agent."""
import pytest
from datetime import datetime, timezone
from athena_x_standardizer_market import MarketStandardizationAgent
from athena_x_standardizer_base import StandardizationContext
from athena_x_runtime_canonical_types import MarketRecord


@pytest.fixture
def agent():
    return MarketStandardizationAgent()


@pytest.fixture
def context():
    return StandardizationContext(
        provider="yahoo",
        provider_version="1.0.0",
        raw_payload_id="raw-123",
        validation_id="val-456",
        validation_status="verified",
        confidence_score=0.95,
        quality_grade="A",
    )


def test_standardize_returns_market_record(agent, context):
    """Standardization produces a canonical MarketRecord."""
    record = {
        "symbol": "SPY.US",
        "last_price": 450.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf",
    }
    result = agent.standardize(record, context)
    assert isinstance(result, MarketRecord)
    assert result.symbol == "SPY"  # alias resolved
    assert result.last_price == 450.0
    assert result.source_provider == "yahoo"
    assert result.schema_version == "1.0.0"


def test_standardize_fills_asset_classification(agent, context):
    """Asset classification defaults are filled in."""
    record = {
        "symbol": "SPY",
        "last_price": 450.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf",
    }
    result = agent.standardize(record, context)
    assert result.market == "US"
    assert result.region == "US"
    assert result.exchange == "NYSEARCA"
    assert result.currency == "USD"


def test_standardize_applies_precision(agent, context):
    """Precision is applied based on asset class."""
    record = {
        "symbol": "SPY",
        "last_price": 450.123456,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf",
    }
    result = agent.standardize(record, context)
    assert result.last_price == 450.12  # 2 decimals for ETF


def test_standardize_adds_provenance(agent, context):
    """Provenance fields are attached."""
    record = {
        "symbol": "SPY",
        "last_price": 450.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf",
    }
    result = agent.standardize(record, context)
    assert result.raw_payload_id == "raw-123"
    assert result.validation_id == "val-456"
    assert result.transformation_id is not None
    assert result.source_provider == "yahoo"


def test_standardize_preserves_original_timestamp(agent, context):
    """Original provider timestamp is preserved in provider_metadata."""
    original_ts = "2026-07-17T14:30:00Z"
    record = {
        "symbol": "SPY",
        "last_price": 450.0,
        "timestamp": original_ts,
        "asset_class": "etf",
    }
    result = agent.standardize(record, context)
    assert result.provider_metadata["original_timestamp"] == original_ts


def test_field_mapping_close_to_last_price(agent, context):
    """Provider field 'close' maps to canonical 'last_price'."""
    record = {
        "symbol": "SPY",
        "close": 450.0,  # provider uses 'close'
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf",
    }
    result = agent.standardize(record, context)
    assert result.last_price == 450.0


def test_fx_record_uses_4_decimal_precision(agent, context):
    """FX records get 4 decimal precision."""
    record = {
        "symbol": "USDJPY",
        "last_price": 150.12345678,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "currency",
    }
    result = agent.standardize(record, context)
    assert result.last_price == 150.1235  # 4 decimals for FX


def test_get_schema_returns_market_record_schema(agent):
    """get_schema returns the canonical MarketRecord schema."""
    schema = agent.get_schema()
    assert schema is not None
    assert schema.name == "MarketRecord"
    assert "last_price" in schema.fields
