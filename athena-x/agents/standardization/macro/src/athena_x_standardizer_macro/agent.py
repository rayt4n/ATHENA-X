"""Macro Standardization Agent (Stage 4 req 2.4).

Normalize: Economic releases, Treasury data, Fed announcements,
Employment, Inflation, GDP, PMI.

This agent is the ONLY writer to the macro_db canonical database.
"""
from __future__ import annotations
from typing import Any

from athena_x_standardizer_base import (
    StandardizationPipeline, StandardizationContext,
)
from athena_x_runtime_canonical_types import MacroRecord
from athena_x_runtime_schema_registry import SchemaRegistry, MACRO_RECORD_SCHEMA


# Region normalization
REGION_NORMALIZATION = {
    "us": "US",
    "usa": "US",
    "united states": "US",
    "eu": "EU",
    "europe": "EU",
    "cn": "CN",
    "china": "CN",
    "jp": "JP",
    "japan": "JP",
    "uk": "UK",
    "gb": "UK",
    "global": "Global",
}


class MacroStandardizationAgent:
    """Standardizes macro data into canonical MacroRecord format.

    Stage 4 rule: This agent is the ONLY writer to macro_db.
    """

    def __init__(self, schema_registry: SchemaRegistry | None = None):
        self._pipeline = StandardizationPipeline()
        self._schema_registry = schema_registry or SchemaRegistry()
        if self._schema_registry.get("MacroRecord") is None:
            self._schema_registry.register(MACRO_RECORD_SCHEMA)

    def standardize(self, record: dict, context: StandardizationContext) -> MacroRecord:
        """Transform a macro record into canonical MacroRecord."""
        # Normalize region
        region = record.get("region", "").lower() if isinstance(record.get("region"), str) else ""
        if region:
            record["region"] = REGION_NORMALIZATION.get(region, record.get("region", "Global"))

        # Run through pipeline
        result = self._pipeline.standardize(record, context)
        canonical = result.canonical_record

        return MacroRecord(**canonical)
