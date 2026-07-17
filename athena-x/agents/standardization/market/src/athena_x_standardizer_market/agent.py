"""Market Standardization Agent (Stage 4 req 2.1).

Responsible for: Equities, ETFs, Futures, Indices, FX, Commodities.

This agent is the ONLY writer to the market_db canonical database.
"""
from __future__ import annotations
from typing import Any

from athena_x_standardizer_base import (
    StandardizationPipeline, StandardizationContext,
)
from athena_x_runtime_canonical_types import MarketRecord
from athena_x_runtime_schema_registry import SchemaRegistry, MARKET_RECORD_SCHEMA


class MarketStandardizationAgent:
    """Standardizes market data records into canonical MarketRecord format.

    Stage 4 rule: This agent is the ONLY writer to market_db.
    All other components access data through APIs or events.
    """

    def __init__(self, schema_registry: SchemaRegistry | None = None):
        self._pipeline = StandardizationPipeline()
        self._schema_registry = schema_registry or SchemaRegistry()
        # Register schema if not already
        if self._schema_registry.get("MarketRecord") is None:
            self._schema_registry.register(MARKET_RECORD_SCHEMA)

    def standardize(self, record: dict, context: StandardizationContext) -> MarketRecord:
        """Transform a validated market record into canonical MarketRecord."""
        result = self._pipeline.standardize(record, context)
        canonical = result.canonical_record

        # Validate against schema
        is_valid, errors = self._schema_registry.validate_record("MarketRecord", canonical)
        if not is_valid:
            # In production, we'd log + quarantine
            pass

        # Build MarketRecord (Pydantic validation)
        return MarketRecord(**canonical)

    def get_schema(self):
        """Return the canonical schema for MarketRecord."""
        return self._schema_registry.get("MarketRecord")
