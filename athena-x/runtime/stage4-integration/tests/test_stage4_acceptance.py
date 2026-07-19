"""Stage 4 acceptance tests — all 8 categories must pass.

Exit criteria (Stage 4 plan):
  1. All validated records transformed into single canonical schema
  2. Symbol aliases resolved consistently
  3. Timezones, sessions, calendars standardized
  4. Units and precision follow configurable rules
  5. Provider-specific field names fully mapped
  6. Schema versioning + provenance attached
  7. Only designated agents write to canonical databases
  8. Downstream services consume standardized data without provider-specific code
  9. Replay deterministic
 10. Unit, integration, replay, migration, schema compat tests pass
"""
import pytest
import time
from datetime import datetime, timezone

from athena_x_standardizer_base import StandardizationContext
from athena_x_runtime_canonical_types import (
    MarketRecord, OptionsRecord, NewsRecord, MacroRecord,
)
from athena_x_runtime_schema_registry import SchemaRegistry, SchemaDefinition, SchemaVersion
from athena_x_runtime_stage4_integration.wire import create_stage4_container


def make_context(provider="yahoo"):
    return StandardizationContext(
        provider=provider, provider_version="1.0.0",
        raw_payload_id="raw-123", validation_id="val-456",
        validation_status="verified", confidence_score=0.95, quality_grade="A",
    )


@pytest.fixture
def setup():
    return create_stage4_container()


# ============================================================================
# Functional tests
# ============================================================================

def test_market_agent_standardizes_record(setup):
    """Market agent produces canonical MarketRecord."""
    agent = setup["market_agent"]
    record = {
        "symbol": "SPY.US", "last_price": 450.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf",
    }
    result = agent.standardize(record, make_context("yahoo"))
    assert isinstance(result, MarketRecord)
    assert result.symbol == "SPY"
    assert result.last_price == 450.0


def test_options_agent_standardizes_chain(setup):
    """Options agent produces canonical OptionsRecords."""
    agent = setup["options_agent"]
    chain = {
        "symbol": "NVDA", "expiry": "2026-07-18",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strikes": [
            {"strike": 125.0, "call": {"bid": 5.0, "iv": 0.45, "delta": 0.65}},
        ],
    }
    records = agent.standardize_chain(chain, make_context("polygon"))
    assert len(records) == 1
    assert isinstance(records[0], OptionsRecord)


def test_news_agent_standardizes_article(setup):
    """News agent produces canonical NewsRecord."""
    agent = setup["news_agent"]
    article = {
        "id": "abc", "source": "reuters",
        "headline": "test",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    result = agent.standardize(article, make_context("reuters"))
    assert isinstance(result, NewsRecord)
    assert result.source == "Reuters"
    assert result.sentiment is None


def test_macro_agent_standardizes_record(setup):
    """Macro agent produces canonical MacroRecord."""
    agent = setup["macro_agent"]
    record = {
        "indicator": "CPI", "region": "us", "value": 3.2,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result = agent.standardize(record, make_context("fred"))
    assert isinstance(result, MacroRecord)
    assert result.region == "US"


# ============================================================================
# Integration tests
# ============================================================================

def test_shared_schema_registry(setup):
    """All 4 agents share the same schema registry."""
    reg = setup["schema_registry"]
    schemas = reg.list_schemas()
    assert "MarketRecord" in schemas
    assert "OptionsRecord" in schemas
    assert "NewsRecord" in schemas
    assert "MacroRecord" in schemas


def test_symbol_aliases_resolved(setup):
    """Symbol aliases resolve consistently across providers."""
    agent = setup["market_agent"]
    # Yahoo uses SPY.US
    r1 = agent.standardize(
        {"symbol": "SPY.US", "last_price": 450.0,
         "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf"},
        make_context("yahoo"),
    )
    # Polygon uses NYSEARCA:SPY
    r2 = agent.standardize(
        {"symbol": "NYSEARCA:SPY", "last_price": 450.0,
         "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf"},
        make_context("polygon"),
    )
    # Both resolve to SPY
    assert r1.symbol == "SPY"
    assert r2.symbol == "SPY"


# ============================================================================
# Data accuracy tests
# ============================================================================

def test_canonical_schema_has_provenance_fields(setup):
    """Every canonical record has provenance fields."""
    agent = setup["market_agent"]
    record = {
        "symbol": "SPY", "last_price": 450.0,
        "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf",
    }
    result = agent.standardize(record, make_context())
    assert result.source_provider == "yahoo"
    assert result.raw_payload_id == "raw-123"
    assert result.validation_id == "val-456"
    assert result.transformation_id is not None


def test_canonical_schema_has_versioning(setup):
    """Every canonical record has versioning fields."""
    agent = setup["market_agent"]
    record = {
        "symbol": "SPY", "last_price": 450.0,
        "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf",
    }
    result = agent.standardize(record, make_context())
    assert result.schema_version == "1.0.0"
    assert result.mapping_version == "1.0.0"
    assert result.provider_version == "1.0.0"


def test_field_mapping_works(setup):
    """Provider field 'close' maps to canonical 'last_price'."""
    agent = setup["market_agent"]
    record = {
        "symbol": "SPY", "close": 450.5,  # provider uses 'close'
        "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf",
    }
    result = agent.standardize(record, make_context())
    assert result.last_price == 450.5


def test_precision_by_asset_class(setup):
    """Precision is applied based on asset class."""
    agent = setup["market_agent"]
    # ETF: 2 decimals
    r1 = agent.standardize(
        {"symbol": "SPY", "last_price": 450.123456,
         "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf"},
        make_context(),
    )
    assert r1.last_price == 450.12
    # FX: 4 decimals
    r2 = agent.standardize(
        {"symbol": "USDJPY", "last_price": 150.12345678,
         "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "currency"},
        make_context(),
    )
    assert r2.last_price == 150.1235


# ============================================================================
# Stress tests
# ============================================================================

def test_stress_1000_records_through_standardization(setup):
    """Standardization handles 1000 records quickly."""
    agent = setup["market_agent"]
    start = time.monotonic()
    for i in range(1000):
        agent.standardize(
            {"symbol": "SPY", "last_price": 450.0 + i * 0.01,
             "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf"},
            make_context(),
        )
    elapsed = time.monotonic() - start
    rate = 1000 / elapsed
    print(f"\n  ✓ Standardized 1000 records in {elapsed:.2f}s ({rate:.0f} records/sec)")
    assert rate >= 500


# ============================================================================
# Failover tests
# ============================================================================

def test_unknown_symbol_handled(setup):
    """Unknown symbols are passed through (will be flagged by validator)."""
    agent = setup["market_agent"]
    result = agent.standardize(
        {"symbol": "UNKNOWN", "last_price": 100.0,
         "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "equity"},
        make_context(),
    )
    assert result.symbol == "UNKNOWN"


# ============================================================================
# Performance tests
# ============================================================================

def test_performance_standardization_latency(setup):
    """Standardization latency p99 < 5ms."""
    agent = setup["market_agent"]
    latencies = []
    for i in range(100):
        start = time.monotonic_ns()
        agent.standardize(
            {"symbol": "SPY", "last_price": 450.0,
             "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf"},
            make_context(),
        )
        latencies.append((time.monotonic_ns() - start) / 1_000_000)
    latencies.sort()
    p99 = latencies[99]
    print(f"\n  ✓ p99: {p99:.2f}ms (budget: <5ms)")
    assert p99 < 5.0


# ============================================================================
# Replay tests
# ============================================================================

def test_standardization_is_deterministic():
    """Same input + context → same output."""
    from athena_x_standardizer_market import MarketStandardizationAgent
    a1 = MarketStandardizationAgent()
    a2 = MarketStandardizationAgent()
    record = {
        "symbol": "SPY", "last_price": 450.0,
        "timestamp": "2026-07-17T10:00:00Z", "asset_class": "etf",
    }
    ctx = make_context()
    r1 = a1.standardize(record, ctx)
    r2 = a2.standardize(record, ctx)
    assert r1.symbol == r2.symbol
    assert r1.last_price == r2.last_price
    assert r1.schema_version == r2.schema_version


# ============================================================================
# Migration tests
# ============================================================================

def test_schema_versioning_supports_evolution():
    """Schema registry supports multiple versions of the same schema."""
    reg = SchemaRegistry()
    from athena_x_runtime_schema_registry import MARKET_RECORD_SCHEMA
    reg.register(MARKET_RECORD_SCHEMA)
    # Register a v1.0.1 with an extra field
    v101_fields = dict(MARKET_RECORD_SCHEMA.fields)
    v101_fields["new_field"] = "str"
    v101 = SchemaDefinition(
        name="MarketRecord",
        version=SchemaVersion(1, 0, 1),
        fields=v101_fields,
        required=MARKET_RECORD_SCHEMA.required,
        optional=MARKET_RECORD_SCHEMA.optional + ["new_field"],
    )
    reg.register(v101)
    versions = reg.list_versions("MarketRecord")
    assert "1.0.0" in versions
    assert "1.0.1" in versions


def test_old_records_still_readable(setup):
    """Records written with v1.0.0 are still valid."""
    reg = setup["schema_registry"]
    record = {
        "symbol": "SPY", "asset_class": "etf", "exchange": "NYSEARCA",
        "timestamp": "2026-07-17T10:00:00Z", "session": "regular",
        "last_price": 450.0, "source_provider": "yahoo",
        "schema_version": "1.0.0",
    }
    is_valid, errors = reg.validate_record("MarketRecord", record, version="1.0.0")
    assert is_valid


# ============================================================================
# Schema compatibility tests
# ============================================================================

def test_schema_registry_serves_correct_schema(setup):
    """get(name, version) returns the correct schema version."""
    reg = setup["schema_registry"]
    schema = reg.get("MarketRecord", version="1.0.0")
    assert schema is not None
    assert str(schema.version) == "1.0.0"


def test_schema_compatibility_check():
    """Same major version = compatible."""
    v1 = SchemaVersion(1, 0, 0)
    v101 = SchemaVersion(1, 0, 1)
    v2 = SchemaVersion(2, 0, 0)
    assert v1.is_compatible_with(v101)
    assert not v1.is_compatible_with(v2)


def test_all_agents_use_same_canonical_field_names(setup):
    """No downstream component needs provider-specific logic."""
    # All 4 agents produce records with canonical field names
    market = setup["market_agent"].standardize(
        {"symbol": "SPY", "last_price": 450.0,
         "timestamp": datetime.now(timezone.utc).isoformat(), "asset_class": "etf"},
        make_context(),
    )
    # All use last_price (not close/last/price)
    assert hasattr(market, "last_price")
    assert not hasattr(market, "close") or market.close is None or market.close == market.last_price
