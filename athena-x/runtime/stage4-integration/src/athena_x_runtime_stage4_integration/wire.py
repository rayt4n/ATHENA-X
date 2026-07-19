"""Wire Stage 4 standardization agents with shared schema registry."""
from __future__ import annotations
from athena_x_runtime_schema_registry import (
    SchemaRegistry, MARKET_RECORD_SCHEMA, OPTIONS_RECORD_SCHEMA,
    NEWS_RECORD_SCHEMA, MACRO_RECORD_SCHEMA,
)
from athena_x_standardizer_market import MarketStandardizationAgent
from athena_x_standardizer_options import OptionsStandardizationAgent
from athena_x_standardizer_news import NewsStandardizationAgent
from athena_x_standardizer_macro import MacroStandardizationAgent


def create_stage4_container():
    """Create a shared schema registry + 4 standardization agents."""
    registry = SchemaRegistry()
    registry.register(MARKET_RECORD_SCHEMA)
    registry.register(OPTIONS_RECORD_SCHEMA)
    registry.register(NEWS_RECORD_SCHEMA)
    registry.register(MACRO_RECORD_SCHEMA)

    return {
        "schema_registry": registry,
        "market_agent": MarketStandardizationAgent(schema_registry=registry),
        "options_agent": OptionsStandardizationAgent(schema_registry=registry),
        "news_agent": NewsStandardizationAgent(schema_registry=registry),
        "macro_agent": MacroStandardizationAgent(schema_registry=registry),
    }
