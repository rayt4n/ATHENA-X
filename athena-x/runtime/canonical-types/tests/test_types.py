"""Tests for canonical types."""
import pytest
from datetime import datetime, timezone, date
from athena_x_runtime_canonical_types import (
    MarketRecord, OptionsRecord, NewsRecord, MacroRecord,
    SCHEMA_VERSION, MAPPING_VERSION,
)


def test_market_record_canonical_schema():
    """MarketRecord has all canonical fields."""
    r = MarketRecord(
        symbol="SPY",
        assetClass="etf",
        timestamp=datetime.now(timezone.utc),
        session="regular",
        lastPrice=450.0,
        sourceProvider="yahoo",
    )
    assert r.symbol == "SPY"
    assert r.last_price == 450.0
    assert r.schema_version == SCHEMA_VERSION
    assert r.mapping_version == MAPPING_VERSION


def test_market_record_serializes_with_aliases():
    """MarketRecord serializes to JSON with camelCase aliases."""
    r = MarketRecord(
        symbol="SPY", assetClass="etf",
        timestamp=datetime.now(timezone.utc),
        session="regular", lastPrice=450.0, sourceProvider="yahoo",
    )
    json_str = r.model_dump_json(by_alias=True)
    assert '"lastPrice"' in json_str
    assert '"assetClass"' in json_str
    assert '"sourceProvider"' in json_str
    assert '"schemaVersion"' in json_str


def test_options_record():
    r = OptionsRecord(
        symbol="NVDA_071826C125",
        underlying="NVDA",
        expiry=date(2026, 7, 18),
        strike=125.0,
        optionType="call",
        timestamp=datetime.now(timezone.utc),
        sourceProvider="polygon",
        delta=0.65,
        gamma=0.04,
        impliedVolatility=0.45,
    )
    assert r.asset_class == "option"
    assert r.underlying == "NVDA"
    assert r.delta == 0.65


def test_news_record_sentiment_is_none():
    """News records have null sentiment in Stage 4."""
    r = NewsRecord(
        id="abc-123",
        source="reuters",
        headline="NVDA beats Q3 estimates",
        publishedAt=datetime.now(timezone.utc),
        sourceProvider="reuters",
    )
    assert r.sentiment is None


def test_macro_record():
    r = MacroRecord(
        indicator="CPI YoY",
        region="US",
        value=3.2,
        previous=3.4,
        surprise=-0.2,
        unit="%",
        timestamp=datetime.now(timezone.utc),
        sourceProvider="fred",
    )
    assert r.indicator == "CPI YoY"
    assert r.value == 3.2


def test_provenance_fields_present():
    """All records have provenance fields."""
    r = MarketRecord(
        symbol="SPY", assetClass="etf",
        timestamp=datetime.now(timezone.utc),
        session="regular", lastPrice=450.0, sourceProvider="yahoo",
        rawPayloadId="raw-123",
        validationId="val-456",
        transformationId="tx-789",
    )
    assert r.raw_payload_id == "raw-123"
    assert r.validation_id == "val-456"
    assert r.transformation_id == "tx-789"


def test_versioning_fields_default():
    """Versioning fields have defaults."""
    r = MarketRecord(
        symbol="SPY", assetClass="etf",
        timestamp=datetime.now(timezone.utc),
        session="regular", lastPrice=450.0, sourceProvider="yahoo",
    )
    assert r.schema_version == "1.0.0"
    assert r.mapping_version == "1.0.0"
