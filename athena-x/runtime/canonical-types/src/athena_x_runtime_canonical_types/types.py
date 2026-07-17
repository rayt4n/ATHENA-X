"""Canonical record types (Stage 4 req 10).

Every downstream AI receives the same structure regardless of source.
No downstream component should need provider-specific logic.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from .versions import SCHEMA_VERSION, MAPPING_VERSION


class Provenance(BaseModel):
    """Provenance — traceability from analysis back to original data (Stage 4 req 12)."""
    model_config = ConfigDict(populate_by_name=True)
    source_provider: str = Field(alias="sourceProvider")
    raw_payload_id: str | None = Field(default=None, alias="rawPayloadId")
    validation_id: str | None = Field(default=None, alias="validationId")
    transformation_id: str | None = Field(default=None, alias="transformationId")


class SchemaVersioning(BaseModel):
    """Schema versioning (Stage 4 req 11)."""
    model_config = ConfigDict(populate_by_name=True)
    schema_version: str = Field(default=SCHEMA_VERSION, alias="schemaVersion")
    mapping_version: str = Field(default=MAPPING_VERSION, alias="mappingVersion")
    provider_version: str | None = Field(default=None, alias="providerVersion")


class ProviderMetadata(BaseModel):
    """Original provider-specific metadata (kept for audit, not for logic)."""
    model_config = ConfigDict(populate_by_name=True)
    original_symbol: str | None = Field(default=None, alias="originalSymbol")
    original_timestamp: str | None = Field(default=None, alias="originalTimestamp")
    original_fields: dict[str, Any] = Field(default_factory=dict, alias="originalFields")
    raw_response: dict[str, Any] | None = Field(default=None, alias="rawResponse")


class ValidationMetadata(BaseModel):
    """Validation results attached to the record (from Stage 3)."""
    model_config = ConfigDict(populate_by_name=True)
    validation_status: str = Field(alias="validationStatus")
    validation_time: datetime = Field(alias="validationTime")
    validator_version: str = Field(alias="validatorVersion")
    confidence_score: float = Field(alias="confidenceScore")
    quality_grade: str = Field(alias="qualityGrade")
    validation_reason: str = Field(default="", alias="validationReason")


class AssetClassification(BaseModel):
    """Asset classification (Stage 4 req 9)."""
    model_config = ConfigDict(populate_by_name=True)
    asset_class: str = Field(alias="assetClass")
    market: str | None = None
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    region: str | None = None
    currency: str = Field(default="USD")


class MarketRecord(BaseModel):
    """Canonical market data record.

    Used for: equities, ETFs, futures, indices, FX, commodities.
    Every downstream AI receives this structure regardless of source provider.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identity
    symbol: str
    asset_class: str = Field(alias="assetClass")
    exchange: str | None = None

    # Time (Stage 4 req 4: never lose original timestamp)
    timestamp: datetime  # UTC
    exchange_local_time: datetime | None = Field(default=None, alias="exchangeLocalTime")
    session: str
    trading_day: date | None = Field(default=None, alias="tradingDay")

    # OHLCV
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    last_price: float = Field(alias="lastPrice")
    bid: float | None = None
    ask: float | None = None
    volume: int | None = None

    # Classification
    market: str | None = None
    sector: str | None = None
    industry: str | None = None
    region: str | None = None
    currency: str = Field(default="USD")

    # Provenance + versioning
    source_provider: str = Field(alias="sourceProvider")
    raw_payload_id: str | None = Field(default=None, alias="rawPayloadId")
    validation_id: str | None = Field(default=None, alias="validationId")
    transformation_id: str | None = Field(default=None, alias="transformationId")
    schema_version: str = Field(default=SCHEMA_VERSION, alias="schemaVersion")
    mapping_version: str = Field(default=MAPPING_VERSION, alias="mappingVersion")
    provider_version: str | None = Field(default=None, alias="providerVersion")

    # Metadata
    provider_metadata: dict[str, Any] = Field(default_factory=dict, alias="providerMetadata")
    validation_metadata: dict[str, Any] = Field(default_factory=dict, alias="validationMetadata")


class OptionsRecord(BaseModel):
    """Canonical options record (chains, greeks, IV, OI)."""
    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    asset_class: str = Field(default="option", alias="assetClass")
    exchange: str | None = None
    underlying: str
    expiry: date
    strike: float
    option_type: str = Field(alias="optionType")  # "call" | "put"
    timestamp: datetime
    session: str | None = None

    # Option data
    bid: float | None = None
    ask: float | None = None
    last_price: float | None = Field(default=None, alias="lastPrice")
    volume: int | None = None
    open_interest: int | None = Field(default=None, alias="openInterest")
    implied_volatility: float | None = Field(default=None, alias="impliedVolatility")

    # Greeks
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None

    # Provenance + versioning
    source_provider: str = Field(alias="sourceProvider")
    raw_payload_id: str | None = Field(default=None, alias="rawPayloadId")
    validation_id: str | None = Field(default=None, alias="validationId")
    transformation_id: str | None = Field(default=None, alias="transformationId")
    schema_version: str = Field(default=SCHEMA_VERSION, alias="schemaVersion")
    mapping_version: str = Field(default=MAPPING_VERSION, alias="mappingVersion")
    provider_version: str | None = Field(default=None, alias="providerVersion")
    provider_metadata: dict[str, Any] = Field(default_factory=dict, alias="providerMetadata")
    validation_metadata: dict[str, Any] = Field(default_factory=dict, alias="validationMetadata")


class NewsRecord(BaseModel):
    """Canonical news record (no sentiment in Stage 4)."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    source: str
    headline: str
    summary: str | None = None
    url: str | None = None
    raw_content: str | None = Field(default=None, alias="rawContent")
    published_at: datetime = Field(alias="publishedAt")
    symbols: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    language: str = Field(default="en")
    sentiment: float | None = None  # null in Stage 4

    # Provenance + versioning
    source_provider: str = Field(alias="sourceProvider")
    raw_payload_id: str | None = Field(default=None, alias="rawPayloadId")
    validation_id: str | None = Field(default=None, alias="validationId")
    transformation_id: str | None = Field(default=None, alias="transformationId")
    schema_version: str = Field(default=SCHEMA_VERSION, alias="schemaVersion")
    mapping_version: str = Field(default=MAPPING_VERSION, alias="mappingVersion")
    provider_version: str | None = Field(default=None, alias="providerVersion")


class MacroRecord(BaseModel):
    """Canonical macro record (economic releases, treasury, fed)."""
    model_config = ConfigDict(populate_by_name=True)

    indicator: str
    region: str
    frequency: str | None = None
    value: float
    previous: float | None = None
    surprise: float | None = None
    unit: str | None = None
    timestamp: datetime
    release_time: datetime | None = Field(default=None, alias="releaseTime")

    # Provenance + versioning
    source_provider: str = Field(alias="sourceProvider")
    raw_payload_id: str | None = Field(default=None, alias="rawPayloadId")
    validation_id: str | None = Field(default=None, alias="validationId")
    transformation_id: str | None = Field(default=None, alias="transformationId")
    schema_version: str = Field(default=SCHEMA_VERSION, alias="schemaVersion")
    mapping_version: str = Field(default=MAPPING_VERSION, alias="mappingVersion")
    provider_version: str | None = Field(default=None, alias="providerVersion")
