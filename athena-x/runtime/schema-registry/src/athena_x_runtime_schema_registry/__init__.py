"""Schema registry — centralized canonical schemas."""
from .registry import SchemaRegistry, SchemaDefinition, SchemaVersion
from .schemas import (
    MARKET_RECORD_SCHEMA, OPTIONS_RECORD_SCHEMA,
    NEWS_RECORD_SCHEMA, MACRO_RECORD_SCHEMA,
)

__all__ = [
    "SchemaRegistry", "SchemaDefinition", "SchemaVersion",
    "MARKET_RECORD_SCHEMA", "OPTIONS_RECORD_SCHEMA",
    "NEWS_RECORD_SCHEMA", "MACRO_RECORD_SCHEMA",
]
__version__ = "0.1.0"
