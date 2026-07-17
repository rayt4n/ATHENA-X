"""Options Standardization Agent (Stage 4 req 2.2).

Responsible for: Option chains, Greeks, Expirations, Strikes, Option metadata.

Rule: No calculations. Only standardizes raw options data.

This agent is the ONLY writer to the options_db canonical database.
"""
from __future__ import annotations
from typing import Any
from datetime import date, datetime

from athena_x_standardizer_base import (
    StandardizationPipeline, StandardizationContext,
)
from athena_x_runtime_canonical_types import OptionsRecord
from athena_x_runtime_schema_registry import SchemaRegistry, OPTIONS_RECORD_SCHEMA


class OptionsStandardizationAgent:
    """Standardizes options data into canonical OptionsRecord format.

    Stage 4 rule: This agent is the ONLY writer to options_db.
    """

    def __init__(self, schema_registry: SchemaRegistry | None = None):
        self._pipeline = StandardizationPipeline()
        self._schema_registry = schema_registry or SchemaRegistry()
        if self._schema_registry.get("OptionsRecord") is None:
            self._schema_registry.register(OPTIONS_RECORD_SCHEMA)

    def standardize_chain(self, chain_data: dict, context: StandardizationContext) -> list[OptionsRecord]:
        """Standardize an options chain into a list of OptionsRecord (one per strike/type).

        Stage 4 rule: No calculations. We don't compute IV Rank, GEX, Max Pain, etc.
        We only standardize the raw chain data.
        """
        records = []
        symbol = chain_data.get("symbol", "")
        expiry_str = chain_data.get("expiry") or chain_data.get("chain", {}).get("expiry")
        if not expiry_str:
            return records

        expiry = date.fromisoformat(expiry_str) if isinstance(expiry_str, str) else expiry_str
        strikes = chain_data.get("strikes") or chain_data.get("chain", {}).get("strikes", [])

        for strike_data in strikes:
            strike = strike_data.get("strike")
            for option_type in ["call", "put"]:
                option = strike_data.get(option_type, {})
                if not option:
                    continue

                record = {
                    "symbol": f"{symbol}_{expiry.strftime('%m%d%y')}{option_type[0].upper()}{strike}",
                    "asset_class": "option",
                    "underlying": symbol,
                    "expiry": expiry.isoformat(),
                    "strike": strike,
                    "option_type": option_type,
                    "timestamp": chain_data.get("timestamp", datetime.utcnow().isoformat()),
                    "last_price": option.get("last") or option.get("price"),
                    "bid": option.get("bid"),
                    "ask": option.get("ask"),
                    "volume": option.get("volume"),
                    "open_interest": option.get("open_interest") or option.get("oi"),
                    "implied_volatility": option.get("iv"),
                    "delta": option.get("delta"),
                    "gamma": option.get("gamma"),
                    "theta": option.get("theta"),
                    "vega": option.get("vega"),
                    "rho": option.get("rho"),
                }
                # Remove None values
                record = {k: v for k, v in record.items() if v is not None}

                result = self._pipeline.standardize(record, context)
                try:
                    records.append(OptionsRecord(**result.canonical_record))
                except Exception:
                    pass  # skip invalid records
        return records
