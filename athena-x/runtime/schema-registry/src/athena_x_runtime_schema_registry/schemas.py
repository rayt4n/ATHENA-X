"""Canonical schema definitions (Stage 4 req 10)."""
from __future__ import annotations
from .registry import SchemaDefinition, SchemaVersion


# Canonical field names (Stage 4 req 7)
CANONICAL_FIELDS = [
    "open", "high", "low", "close", "last_price", "bid", "ask", "volume",
    "open_interest", "implied_volatility", "delta", "gamma", "theta", "vega",
]


# Schema Version 1.0.0 — initial canonical schemas
SCHEMA_V1 = SchemaVersion(1, 0, 0)


MARKET_RECORD_SCHEMA = SchemaDefinition(
    name="MarketRecord",
    version=SCHEMA_V1,
    fields={
        "symbol": "str",
        "asset_class": "str",
        "exchange": "str",
        "timestamp": "datetime",
        "session": "str",
        "trading_day": "date",
        "exchange_local_time": "datetime",
        "open": "float",
        "high": "float",
        "low": "float",
        "close": "float",
        "last_price": "float",
        "bid": "float",
        "ask": "float",
        "volume": "int",
        "currency": "str",
        "market": "str",
        "sector": "str",
        "industry": "str",
        "region": "str",
        # Provenance
        "source_provider": "str",
        "raw_payload_id": "str",
        "validation_id": "str",
        "transformation_id": "str",
        # Versioning
        "schema_version": "str",
        "mapping_version": "str",
        "provider_version": "str",
        # Metadata
        "provider_metadata": "dict",
        "validation_metadata": "dict",
    },
    required=[
        "symbol", "asset_class", "exchange", "timestamp", "session",
        "last_price", "source_provider", "schema_version",
    ],
    optional=[
        "open", "high", "low", "close", "bid", "ask", "volume",
        "currency", "market", "sector", "industry", "region",
        "trading_day", "exchange_local_time",
        "raw_payload_id", "validation_id", "transformation_id",
        "mapping_version", "provider_version",
        "provider_metadata", "validation_metadata",
    ],
    description="Canonical market data record (equities, ETFs, futures, indices, FX, commodities)",
)


OPTIONS_RECORD_SCHEMA = SchemaDefinition(
    name="OptionsRecord",
    version=SCHEMA_V1,
    fields={
        "symbol": "str",
        "asset_class": "str",  # always "option"
        "exchange": "str",
        "underlying": "str",
        "expiry": "date",
        "strike": "float",
        "option_type": "str",  # "call" | "put"
        "timestamp": "datetime",
        "session": "str",
        "bid": "float",
        "ask": "float",
        "last_price": "float",
        "volume": "int",
        "open_interest": "int",
        "implied_volatility": "float",
        "delta": "float",
        "gamma": "float",
        "theta": "float",
        "vega": "float",
        "rho": "float",
        # Provenance + versioning (same as MarketRecord)
        "source_provider": "str",
        "raw_payload_id": "str",
        "validation_id": "str",
        "transformation_id": "str",
        "schema_version": "str",
        "mapping_version": "str",
        "provider_version": "str",
        "provider_metadata": "dict",
        "validation_metadata": "dict",
    },
    required=[
        "symbol", "asset_class", "underlying", "expiry", "strike",
        "option_type", "timestamp", "source_provider", "schema_version",
    ],
    optional=[
        "exchange", "session", "bid", "ask", "last_price", "volume",
        "open_interest", "implied_volatility",
        "delta", "gamma", "theta", "vega", "rho",
        "raw_payload_id", "validation_id", "transformation_id",
        "mapping_version", "provider_version",
        "provider_metadata", "validation_metadata",
    ],
    description="Canonical options record (chains, greeks, IV, OI)",
)


NEWS_RECORD_SCHEMA = SchemaDefinition(
    name="NewsRecord",
    version=SCHEMA_V1,
    fields={
        "id": "str",
        "source": "str",
        "headline": "str",
        "summary": "str",
        "url": "str",
        "raw_content": "str",
        "published_at": "datetime",
        "symbols": "list[str]",
        "categories": "list[str]",
        "language": "str",
        "sentiment": "float",  # null in Stage 4 (filled in Stage 10)
        # Provenance + versioning
        "source_provider": "str",
        "raw_payload_id": "str",
        "validation_id": "str",
        "transformation_id": "str",
        "schema_version": "str",
        "mapping_version": "str",
        "provider_version": "str",
    },
    required=[
        "id", "source", "headline", "published_at",
        "source_provider", "schema_version",
    ],
    optional=[
        "summary", "url", "raw_content", "symbols", "categories",
        "language", "sentiment",
        "raw_payload_id", "validation_id", "transformation_id",
        "mapping_version", "provider_version",
    ],
    description="Canonical news record (no sentiment in Stage 4)",
)


MACRO_RECORD_SCHEMA = SchemaDefinition(
    name="MacroRecord",
    version=SCHEMA_V1,
    fields={
        "indicator": "str",
        "region": "str",
        "frequency": "str",
        "value": "float",
        "previous": "float",
        "surprise": "float",
        "unit": "str",
        "timestamp": "datetime",
        "release_time": "datetime",
        # Provenance + versioning
        "source_provider": "str",
        "raw_payload_id": "str",
        "validation_id": "str",
        "transformation_id": "str",
        "schema_version": "str",
        "mapping_version": "str",
        "provider_version": "str",
    },
    required=[
        "indicator", "region", "value", "timestamp",
        "source_provider", "schema_version",
    ],
    optional=[
        "frequency", "previous", "surprise", "unit", "release_time",
        "raw_payload_id", "validation_id", "transformation_id",
        "mapping_version", "provider_version",
    ],
    description="Canonical macro record (economic releases, treasury, fed)",
)
