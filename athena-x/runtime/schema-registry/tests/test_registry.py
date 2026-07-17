"""Tests for schema registry (Stage 4 additional req)."""
import pytest
from athena_x_runtime_schema_registry import (
    SchemaRegistry, SchemaDefinition, SchemaVersion,
    MARKET_RECORD_SCHEMA, OPTIONS_RECORD_SCHEMA,
    NEWS_RECORD_SCHEMA, MACRO_RECORD_SCHEMA,
)


def test_register_and_get_schema():
    """Schemas can be registered and retrieved."""
    reg = SchemaRegistry()
    reg.register(MARKET_RECORD_SCHEMA)
    schema = reg.get("MarketRecord")
    assert schema is not None
    assert schema.name == "MarketRecord"
    assert "last_price" in schema.fields
    assert "symbol" in schema.required


def test_get_latest_version():
    """get(name) returns the latest version."""
    reg = SchemaRegistry()
    v1 = SchemaDefinition(
        name="TestRecord", version=SchemaVersion(1, 0, 0),
        fields={"x": "int"}, required=["x"], optional=[],
    )
    v2 = SchemaDefinition(
        name="TestRecord", version=SchemaVersion(1, 1, 0),
        fields={"x": "int", "y": "int"}, required=["x"], optional=["y"],
    )
    reg.register(v1)
    reg.register(v2)
    latest = reg.get("TestRecord")
    assert str(latest.version) == "1.1.0"


def test_get_specific_version():
    reg = SchemaRegistry()
    reg.register(MARKET_RECORD_SCHEMA)
    schema = reg.get("MarketRecord", version="1.0.0")
    assert schema is not None
    assert str(schema.version) == "1.0.0"


def test_unknown_schema_returns_none():
    reg = SchemaRegistry()
    assert reg.get("Nonexistent") is None


def test_list_schemas():
    reg = SchemaRegistry()
    reg.register(MARKET_RECORD_SCHEMA)
    reg.register(OPTIONS_RECORD_SCHEMA)
    schemas = reg.list_schemas()
    assert "MarketRecord" in schemas
    assert "OptionsRecord" in schemas


def test_list_versions():
    reg = SchemaRegistry()
    reg.register(MARKET_RECORD_SCHEMA)
    v101 = SchemaDefinition(
        name="MarketRecord", version=SchemaVersion(1, 0, 1),
        fields=MARKET_RECORD_SCHEMA.fields,
        required=MARKET_RECORD_SCHEMA.required,
        optional=MARKET_RECORD_SCHEMA.optional,
    )
    reg.register(v101)
    versions = reg.list_versions("MarketRecord")
    assert "1.0.0" in versions
    assert "1.0.1" in versions


def test_validate_record_valid():
    reg = SchemaRegistry()
    reg.register(MARKET_RECORD_SCHEMA)
    record = {
        "symbol": "SPY", "asset_class": "etf", "exchange": "NYSEARCA",
        "timestamp": "2026-07-17T10:00:00Z", "session": "regular",
        "last_price": 450.0, "source_provider": "yahoo",
        "schema_version": "1.0.0",
    }
    is_valid, errors = reg.validate_record("MarketRecord", record)
    assert is_valid
    assert errors == []


def test_validate_record_missing_required():
    reg = SchemaRegistry()
    reg.register(MARKET_RECORD_SCHEMA)
    record = {
        "symbol": "SPY",  # missing many required fields
    }
    is_valid, errors = reg.validate_record("MarketRecord", record)
    assert not is_valid
    assert len(errors) > 0
    assert any("asset_class" in e for e in errors)


def test_schema_version_compatible():
    """Same major version = compatible."""
    v1 = SchemaVersion(1, 0, 0)
    v101 = SchemaVersion(1, 0, 1)
    v11 = SchemaVersion(1, 1, 0)
    v2 = SchemaVersion(2, 0, 0)
    assert v1.is_compatible_with(v101)
    assert v1.is_compatible_with(v11)
    assert not v1.is_compatible_with(v2)


def test_all_4_canonical_schemas_defined():
    """All 4 canonical schemas are defined."""
    assert MARKET_RECORD_SCHEMA.name == "MarketRecord"
    assert OPTIONS_RECORD_SCHEMA.name == "OptionsRecord"
    assert NEWS_RECORD_SCHEMA.name == "NewsRecord"
    assert MACRO_RECORD_SCHEMA.name == "MacroRecord"


def test_canonical_fields_present():
    """Canonical field names (Stage 4 req 7) are in schemas."""
    for field in ["open", "high", "low", "close", "last_price", "bid", "ask", "volume"]:
        assert field in MARKET_RECORD_SCHEMA.fields
    for field in ["open_interest", "implied_volatility", "delta", "gamma", "theta", "vega"]:
        assert field in OPTIONS_RECORD_SCHEMA.fields


def test_provenance_fields_in_all_schemas():
    """Every schema has provenance fields (Stage 4 req 12)."""
    provenance = ["source_provider", "raw_payload_id", "validation_id", "transformation_id"]
    for schema in [MARKET_RECORD_SCHEMA, OPTIONS_RECORD_SCHEMA, NEWS_RECORD_SCHEMA, MACRO_RECORD_SCHEMA]:
        for field in provenance:
            assert field in schema.fields, f"{schema.name} missing {field}"


def test_versioning_fields_in_all_schemas():
    """Every schema has versioning fields (Stage 4 req 11)."""
    versioning = ["schema_version", "mapping_version", "provider_version"]
    for schema in [MARKET_RECORD_SCHEMA, OPTIONS_RECORD_SCHEMA, NEWS_RECORD_SCHEMA, MACRO_RECORD_SCHEMA]:
        for field in versioning:
            assert field in schema.fields, f"{schema.name} missing {field}"
