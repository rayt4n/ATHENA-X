"""Options data collector.

Collects options chain + raw data needed for downstream computations
(IV Rank, GEX, Max Pain, Expected Move, etc.) — Stage 2 only fetches,
Stage 8 computes.
"""
from __future__ import annotations
import random
from datetime import datetime, timezone, date, timedelta
from typing import Any

from athena_x_collector_base import BaseCollector, CollectorConfig
from .types import OptionsDataType


class OptionsDataCollector(BaseCollector):
    """Collects options chain and related raw data.

    Uses SimulatedAdapter for dev; in production, uses Polygon/Databento.
    """

    def __init__(
        self,
        config: CollectorConfig,
        data_type: OptionsDataType = OptionsDataType.OPTION_CHAIN,
        **kwargs,
    ):
        super().__init__(config=config, **kwargs)
        self._data_type = data_type
        self._rng = random.Random(hash((config.symbol, data_type.value)) & 0xFFFFFFFF)

    async def fetch_data(self) -> tuple[dict, datetime]:
        """Fetch options data based on the data_type."""
        now = datetime.now(timezone.utc)

        if self._data_type == OptionsDataType.OPTION_CHAIN:
            return self._fetch_option_chain(now)
        elif self._data_type == OptionsDataType.OPEN_INTEREST:
            return self._fetch_open_interest(now)
        elif self._data_type == OptionsDataType.VOLUME:
            return self._fetch_volume(now)
        elif self._data_type == OptionsDataType.GREEKS:
            return self._fetch_greeks(now)
        elif self._data_type == OptionsDataType.IV:
            return self._fetch_iv(now)
        elif self._data_type == OptionsDataType.OPTION_FLOW:
            return self._fetch_option_flow(now)
        elif self._data_type == OptionsDataType.DARK_POOL:
            return self._fetch_dark_pool(now)
        elif self._data_type == OptionsDataType.ZERO_DTE:
            return self._fetch_0dte(now)
        elif self._data_type == OptionsDataType.SHORT_INTEREST:
            return self._fetch_short_interest(now)
        else:
            # For *_raw types — fetch the raw data needed for later computation
            return self._fetch_raw_for_computation(now)

    def _fetch_option_chain(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch full option chain for nearest expiry."""
        expiry = (now.date() + timedelta(days=30))
        spot = 100 + self._rng.uniform(-20, 20)
        chain = {"strikes": [], "expiry": expiry.isoformat()}
        for i in range(-10, 11):
            strike = round(spot + i * 5, 2)
            chain["strikes"].append({
                "strike": strike,
                "call": {
                    "bid": round(max(0.1, spot - strike + 5), 2),
                    "ask": round(max(0.1, spot - strike + 5.5), 2),
                    "volume": self._rng.randint(0, 5000),
                    "open_interest": self._rng.randint(0, 50000),
                    "iv": round(self._rng.uniform(0.2, 0.8), 4),
                },
                "put": {
                    "bid": round(max(0.1, strike - spot + 5), 2),
                    "ask": round(max(0.1, strike - spot + 5.5), 2),
                    "volume": self._rng.randint(0, 5000),
                    "open_interest": self._rng.randint(0, 50000),
                    "iv": round(self._rng.uniform(0.2, 0.8), 4),
                },
            })
        return {"symbol": self.symbol, "chain": chain, "timestamp": now.isoformat()}, now

    def _fetch_open_interest(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch open interest per strike (raw data for max pain, GEX, etc.)."""
        return {
            "symbol": self.symbol,
            "open_interest": [
                {"strike": 100 + i, "call_oi": self._rng.randint(0, 50000),
                 "put_oi": self._rng.randint(0, 50000)}
                for i in range(-10, 11)
            ],
            "timestamp": now.isoformat(),
        }, now

    def _fetch_volume(self, now: datetime) -> tuple[dict, datetime]:
        return {
            "symbol": self.symbol,
            "total_volume": self._rng.randint(100000, 1000000),
            "call_volume": self._rng.randint(50000, 500000),
            "put_volume": self._rng.randint(50000, 500000),
            "put_call_ratio": round(self._rng.uniform(0.5, 1.5), 4),
            "timestamp": now.isoformat(),
        }, now

    def _fetch_greeks(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch greeks per strike (raw data for GEX computation)."""
        return {
            "symbol": self.symbol,
            "greeks": [
                {"strike": 100 + i,
                 "call_delta": round(self._rng.uniform(0, 1), 4),
                 "call_gamma": round(self._rng.uniform(0, 0.1), 6),
                 "put_delta": round(self._rng.uniform(-1, 0), 4),
                 "put_gamma": round(self._rng.uniform(0, 0.1), 6)}
                for i in range(-10, 11)
            ],
            "timestamp": now.isoformat(),
        }, now

    def _fetch_iv(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch IV per strike (raw data for IV Rank, IV Percentile)."""
        return {
            "symbol": self.symbol,
            "iv_atm": round(self._rng.uniform(0.15, 0.6), 4),
            "iv_skew": round(self._rng.uniform(-0.1, 0.1), 4),
            "iv_per_strike": [
                {"strike": 100 + i, "iv": round(self._rng.uniform(0.2, 0.8), 4)}
                for i in range(-10, 11)
            ],
            "timestamp": now.isoformat(),
        }, now

    def _fetch_option_flow(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch unusual options activity."""
        return {
            "symbol": self.symbol,
            "flow": [
                {"strike": 100 + self._rng.randint(-5, 5),
                 "expiry": (now.date() + timedelta(days=self._rng.randint(1, 90))).isoformat(),
                 "type": self._rng.choice(["call", "put"]),
                 "size": self._rng.randint(100, 10000),
                 "premium": self._rng.randint(10000, 1000000),
                 "side": self._rng.choice(["buy", "sell"])}
                for _ in range(self._rng.randint(1, 5))
            ],
            "timestamp": now.isoformat(),
        }, now

    def _fetch_dark_pool(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch dark pool prints."""
        return {
            "symbol": self.symbol,
            "dark_pool_prints": [
                {"price": round(100 + self._rng.uniform(-5, 5), 4),
                 "size": self._rng.randint(100, 50000),
                 "venue": self._rng.choice(["UBS", "CS", "JPM", "ML"]),
                 "timestamp": now.isoformat()}
                for _ in range(self._rng.randint(1, 3))
            ],
        }, now

    def _fetch_0dte(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch 0DTE options data."""
        return {
            "symbol": self.symbol,
            "expiry": now.date().isoformat(),
            "calls_volume": self._rng.randint(10000, 100000),
            "puts_volume": self._rng.randint(10000, 100000),
            "calls_oi": self._rng.randint(50000, 200000),
            "puts_oi": self._rng.randint(50000, 200000),
            "timestamp": now.isoformat(),
        }, now

    def _fetch_short_interest(self, now: datetime) -> tuple[dict, datetime]:
        """Fetch short interest (if available)."""
        return {
            "symbol": self.symbol,
            "short_interest": self._rng.randint(1000000, 50000000),
            "short_percent_of_float": round(self._rng.uniform(0.01, 0.15), 4),
            "days_to_cover": round(self._rng.uniform(0.5, 10.0), 2),
            "as_of_date": now.date().isoformat(),
        }, now

    def _fetch_raw_for_computation(self, now: datetime) -> tuple[dict, datetime]:
        """For *_raw types — fetch the underlying data needed for later computation."""
        # Combine greeks + OI + IV — these are the inputs to GEX, max pain,
        # expected move, IV rank, gamma flip, dealer positioning
        return {
            "symbol": self.symbol,
            "data_type": self._data_type.value,
            "spot": round(100 + self._rng.uniform(-20, 20), 4),
            "strikes": [
                {
                    "strike": 100 + i,
                    "call_oi": self._rng.randint(0, 50000),
                    "put_oi": self._rng.randint(0, 50000),
                    "call_iv": round(self._rng.uniform(0.2, 0.8), 4),
                    "put_iv": round(self._rng.uniform(0.2, 0.8), 4),
                    "call_delta": round(self._rng.uniform(0, 1), 4),
                    "call_gamma": round(self._rng.uniform(0, 0.1), 6),
                    "put_delta": round(self._rng.uniform(-1, 0), 4),
                    "put_gamma": round(self._rng.uniform(0, 0.1), 6),
                }
                for i in range(-10, 11)
            ],
            "timestamp": now.isoformat(),
        }, now

    def _get_provider_name(self) -> str:
        return "simulated"

    def get_event_type(self) -> str:
        return "options:chain-refreshed"
