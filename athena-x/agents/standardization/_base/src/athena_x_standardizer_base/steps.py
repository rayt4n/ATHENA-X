"""The 8 standardization steps (Stage 4 req 1)."""
from __future__ import annotations
from datetime import datetime, timezone, date
from typing import Any
import pytz

from athena_x_runtime_symbol_dictionary import SymbolDictionary
from athena_x_runtime_market_calendars import get_calendar
from athena_x_runtime_session_awareness import SessionDetector
from athena_x_runtime_canonical_types import SCHEMA_VERSION, MAPPING_VERSION

from .base import BaseStandardizer, StandardizationContext


# Stage 4 req 6: Unit normalization
UNIT_CONVERSIONS = {
    # Cents → dollars
    "cents_to_dollars": lambda v: v / 100.0,
    # Percent → decimal (e.g., 1.5% → 0.015)
    "percent_to_decimal": lambda v: v / 100.0,
    # Basis points → decimal (e.g., 150 bps → 0.015)
    "bps_to_decimal": lambda v: v / 10000.0,
    # Millions → absolute (e.g., volume in millions)
    "millions_to_absolute": lambda v: v * 1_000_000,
    # Thousands → absolute
    "thousands_to_absolute": lambda v: v * 1_000,
}

# Stage 4 req 7: Field mapping — provider field names → canonical names
FIELD_MAPPINGS = {
    # Price fields
    "close": "last_price",
    "Close": "last_price",
    "last": "last_price",
    "lastPrice": "last_price",
    "price": "last_price",
    "regularMarketPrice": "last_price",
    "c": "last_price",  # Finnhub
    # OHLC
    "Open": "open",
    "High": "high",
    "Low": "low",
    "o": "open",  # Finnhub
    "h": "high",
    "l": "low",
    # Bid/ask
    "bidPrice": "bid",
    "askPrice": "ask",
    "b": "bid",
    "a": "ask",
    # Volume
    "regularMarketVolume": "volume",
    "vol": "volume",
    "v": "volume",
    # Greeks
    "iv": "implied_volatility",
    "impliedVol": "implied_volatility",
    "openInterest": "open_interest",
    "oi": "open_interest",
}

# Stage 4 req 8: Precision rules by asset class
PRECISION_RULES = {
    "equity": 2,
    "etf": 2,
    "index": 2,
    "future": 2,
    "option": 2,
    "currency": 4,  # FX needs more precision
    "commodity": 4,
    "yield": 3,  # yields to 3 decimals (e.g., 4.567)
    "volatility": 2,
    "crypto": 2,
    "macro": 4,
    "news": 0,
}


class SymbolStandardizer(BaseStandardizer):
    """Step 1: Symbol standardization (Stage 4 req 3)."""

    def __init__(self, dictionary: SymbolDictionary | None = None):
        super().__init__("symbol-standardizer")
        self._dictionary = dictionary or SymbolDictionary()

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        original = record.get("symbol", "")
        if not original:
            return record
        canonical = self._dictionary.resolve(original, provider=context.provider)
        record["symbol"] = canonical
        # Keep original for provenance
        if "_original_symbol" not in record:
            record["_original_symbol"] = original
        return record


class TimezoneStandardizer(BaseStandardizer):
    """Step 2: Timezone standardization (Stage 4 req 4).

    Every timestamp should contain:
      - UTC timestamp
      - Exchange local time
      - Session
      - Trading day
      - ISO-8601 format
    """

    def __init__(self):
        super().__init__("timezone-standardizer")
        self._session_detector = SessionDetector()

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        ts_str = record.get("timestamp")
        if not ts_str:
            return record

        # Parse timestamp
        try:
            ts = self._parse_timestamp(ts_str)
        except Exception:
            return record

        # Convert to UTC
        utc_ts = ts.astimezone(timezone.utc)
        record["timestamp"] = utc_ts.isoformat()

        # Detect session
        info = self._session_detector.detect(utc_ts, symbol=record.get("symbol", ""))
        record["session"] = info.session.value
        record["exchange_local_time"] = info.et_time.isoformat()
        record["trading_day"] = info.et_time.date().isoformat()

        # Keep original provider timestamp (never lose it — Stage 4 req 4)
        if "_original_timestamp" not in record:
            record["_original_timestamp"] = ts_str if isinstance(ts_str, str) else str(ts_str)

        return record

    def _parse_timestamp(self, ts_str) -> datetime:
        if isinstance(ts_str, (int, float)):
            if ts_str > 1e12:
                return datetime.fromtimestamp(ts_str / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        normalized = str(ts_str).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)


class CalendarStandardizer(BaseStandardizer):
    """Step 3: Market calendar standardization (Stage 4 req 5)."""

    def __init__(self):
        super().__init__("calendar-standardizer")

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        # Determine which calendar applies based on asset class / exchange
        asset_class = record.get("asset_class", "equity")
        if asset_class == "crypto":
            record["_calendar"] = "Crypto"
        elif asset_class == "currency":
            record["_calendar"] = "FX"
        elif asset_class == "future":
            record["_calendar"] = "CME"
        elif asset_class == "volatility":
            record["_calendar"] = "CBOE"
        else:
            record["_calendar"] = "NYSE"
        return record


class UnitStandardizer(BaseStandardizer):
    """Step 4: Unit standardization (Stage 4 req 6).

    Examples:
      15025 cents → 150.25 USD
      1.5% → 0.015
      150 bps → 0.015
    """

    def __init__(self):
        super().__init__("unit-standardizer")

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        # Detect and convert cents to dollars (heuristic: large integer prices)
        last = record.get("last_price")
        if isinstance(last, (int, float)) and last > 1000 and record.get("_unit_hint") == "cents":
            record["last_price"] = last / 100.0
            record["currency"] = "USD"

        # Default currency to USD if not set
        if "currency" not in record:
            record["currency"] = "USD"

        return record


class FieldMapper(BaseStandardizer):
    """Step 5: Field mapping (Stage 4 req 7).

    close, Close, last, lastPrice, price → last_price
    """

    def __init__(self):
        super().__init__("field-mapper")

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        # Build a new dict with canonical field names
        canonical_record = {}
        for key, value in record.items():
            canonical_key = FIELD_MAPPINGS.get(key, key)
            canonical_record[canonical_key] = value
        return canonical_record


class PrecisionStandardizer(BaseStandardizer):
    """Step 6: Precision standardization (Stage 4 req 8).

    Define precision by asset class. Configurable, not hard-coded.
    """

    def __init__(self):
        super().__init__("precision-standardizer")

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        asset_class = record.get("asset_class", "equity")
        precision = PRECISION_RULES.get(asset_class, 2)

        # Apply precision to all numeric price fields
        price_fields = ["open", "high", "low", "close", "last_price", "bid", "ask"]
        for field in price_fields:
            if field in record and isinstance(record[field], (int, float)):
                record[field] = round(record[field], precision)

        # Greeks precision (more decimals)
        greek_fields = ["delta", "gamma", "theta", "vega", "rho", "implied_volatility"]
        for field in greek_fields:
            if field in record and isinstance(record[field], (int, float)):
                record[field] = round(record[field], 6)

        return record


class AssetClassifier(BaseStandardizer):
    """Step 7: Asset classification (Stage 4 req 9).

    Each record receives: asset_class, market, exchange, sector, industry, region, currency.
    """

    def __init__(self):
        super().__init__("asset-classifier")

    # Default classification by asset class
    DEFAULTS = {
        "equity": {"market": "US", "region": "US", "exchange": "NYSE"},
        "etf": {"market": "US", "region": "US", "exchange": "NYSEARCA"},
        "index": {"market": "US", "region": "US", "exchange": "CBOE"},
        "future": {"market": "US", "region": "US", "exchange": "CME"},
        "option": {"market": "US", "region": "US", "exchange": "CBOE"},
        "currency": {"market": "Global", "region": "Global", "exchange": "FX"},
        "commodity": {"market": "Global", "region": "Global", "exchange": "CME"},
        "yield": {"market": "US", "region": "US", "exchange": "CBOE"},
        "volatility": {"market": "US", "region": "US", "exchange": "CBOE"},
        "crypto": {"market": "Global", "region": "Global", "exchange": "Crypto"},
        "news": {"market": "Global", "region": "Global", "exchange": None},
        "macro": {"market": "Global", "region": "Global", "exchange": None},
    }

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        asset_class = record.get("asset_class", "equity")
        defaults = self.DEFAULTS.get(asset_class, {})

        # Fill in defaults only if not already set
        for key, value in defaults.items():
            if key not in record or record[key] is None:
                record[key] = value

        # Ensure currency is set
        if "currency" not in record:
            record["currency"] = "USD"

        return record


class CanonicalSchemaBuilder(BaseStandardizer):
    """Step 8: Canonical schema builder (Stage 4 req 10, 11, 12).

    Assembles the final canonical record with:
      - Provenance (source_provider, raw_payload_id, validation_id, transformation_id)
      - Versioning (schema_version, mapping_version, provider_version)
      - Provider metadata (original fields preserved for audit)
    """

    def __init__(self):
        super().__init__("canonical-schema-builder")

    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        # Generate transformation ID for provenance
        from .base import generate_transformation_id
        transformation_id = generate_transformation_id()

        # Extract original fields for provider_metadata
        original_symbol = record.pop("_original_symbol", None) or context.original_symbol
        original_timestamp = record.pop("_original_timestamp", None)
        original_fields = {
            k: v for k, v in record.items()
            if k.startswith("_")
        }
        # Clean up internal keys
        for k in list(record.keys()):
            if k.startswith("_"):
                del record[k]

        # Add provenance (Stage 4 req 12)
        record["source_provider"] = context.provider
        record["raw_payload_id"] = context.raw_payload_id
        record["validation_id"] = context.validation_id
        record["transformation_id"] = transformation_id

        # Add versioning (Stage 4 req 11)
        record["schema_version"] = SCHEMA_VERSION
        record["mapping_version"] = MAPPING_VERSION
        record["provider_version"] = context.provider_version

        # Add provider metadata (preserves original for audit)
        record["provider_metadata"] = {
            "original_symbol": original_symbol,
            "original_timestamp": original_timestamp,
            "original_fields": original_fields,
        }

        # Add validation metadata
        record["validation_metadata"] = {
            "validation_status": context.validation_status,
            "validation_time": datetime.now(timezone.utc).isoformat(),
            "validator_version": "1.0.0",  # from Stage 3
            "confidence_score": context.confidence_score,
            "quality_grade": context.quality_grade,
        }

        return record
