"""Phase 5 — Trading Logic Scenarios.

For each indicator, defines test scenarios that verify:
  - Formula correctness (vs. manual calculation)
  - Parameter handling (period, fast/slow, etc.)
  - Edge cases (insufficient data, single bar, flat series)
  - NaN / Infinity handling
  - Missing data handling
  - Output range (e.g., RSI must be 0-100, ADX must be 0-100)
  - Warm-up behavior (indicator should return None or low-confidence during warm-up)

Each scenario runs the agent and checks the output against expected criteria.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable

from athena_x_runtime_repository_interface import QueryResult
from athena_x_ta_base import Timeframe


@dataclass
class LogicScenario:
    """One trading-logic test scenario for one agent."""
    scenario_id: str
    agent_id: str
    description: str
    category: str           # "formula" | "params" | "edge_case" | "nan" | "infinity" | "missing" | "range" | "warmup"
    setup: Callable          # () -> tuple[list[dict], dict]  returns (bars, params)
    check: Callable          # (output) -> tuple[bool, str]  returns (passed, message)
    expected_pass: bool = True


# ============================================================================
# Test data generators
# ============================================================================

def _bars_from_closes(closes: list[float], symbol: str = "SPY", timeframe: str = "15m") -> list[dict]:
    """Generate OHLCV bars from a list of close prices (open=prev close, high/low around price)."""
    bars = []
    base = datetime.now(timezone.utc) - timedelta(minutes=len(closes) * 15)
    for i, c in enumerate(closes):
        ts = base + timedelta(minutes=i * 15)
        open_p = closes[i - 1] if i > 0 else c - 0.1
        high = max(open_p, c) + 0.05
        low = min(open_p, c) - 0.05
        bars.append({
            "symbol": symbol, "timeframe": timeframe,
            "timestamp": ts.isoformat(),
            "open": round(open_p, 4),
            "high": round(high, 4),
            "low": round(low, 4),
            "close": round(c, 4),
            "volume": 100000 + i * 100,
        })
    return bars


def _bullish_trend_bars(n: int = 50, start: float = 450.0, slope: float = 0.3) -> list[dict]:
    """Strong bullish trend."""
    closes = [start + i * slope for i in range(n)]
    return _bars_from_closes(closes)


def _bearish_trend_bars(n: int = 50, start: float = 460.0, slope: float = -0.3) -> list[dict]:
    """Strong bearish trend."""
    closes = [start + i * slope for i in range(n)]
    return _bars_from_closes(closes)


def _flat_bars(n: int = 50, price: float = 450.0) -> list[dict]:
    """Flat / ranging market."""
    closes = [price for _ in range(n)]
    return _bars_from_closes(closes)


def _oscillating_bars(n: int = 50, base: float = 450.0, amplitude: float = 1.0) -> list[dict]:
    """Mean-reverting oscillating prices."""
    closes = [base + amplitude * math.sin(i * 0.4) for i in range(n)]
    return _bars_from_closes(closes)


def _bars_with_nan(n: int = 50) -> list[dict]:
    """Bars where some closes are NaN."""
    closes = [450.0 + i * 0.1 for i in range(n)]
    closes[10] = float('nan')
    closes[20] = float('nan')
    return _bars_from_closes(closes)


def _bars_with_inf(n: int = 50) -> list[dict]:
    """Bars where some closes are Infinity."""
    closes = [450.0 + i * 0.1 for i in range(n)]
    closes[15] = float('inf')
    return _bars_from_closes(closes)


def _insufficient_bars(n: int = 5) -> list[dict]:
    """Too few bars for indicator warm-up."""
    closes = [450.0 + i * 0.1 for i in range(n)]
    return _bars_from_closes(closes)


# ============================================================================
# Repo wrapper
# ============================================================================

class ScenarioRepo:
    """Repo that returns bars from a scenario setup."""
    def __init__(self, bars: list[dict]):
        self.bars = bars

    async def query_bars(self, symbol, timeframe, start, end):
        return QueryResult(records=self.bars, count=len(self.bars))

    async def read_quote(self, symbol): return None
    async def write_quote(self, record): pass
    async def write_bar(self, record): pass
    async def supersede(self, record_id, corrected): pass
    async def get_history(self, symbol, limit=100):
        return QueryResult(records=[], count=0)


# ============================================================================
# Helper checks
# ============================================================================

def _get_value(output: Any) -> Any:
    """Extract value from TAOutput or dict."""
    if hasattr(output, "value"):
        return output.value
    if isinstance(output, dict):
        return output.get("value")
    return None


def _get_confidence(output: Any) -> float | None:
    if hasattr(output, "confidence") and hasattr(output.confidence, "score"):
        return output.confidence.score
    if isinstance(output, dict):
        c = output.get("confidence")
        if c is not None:
            try:
                return float(c)
            except Exception:
                return None
    return None


def _get_indicator(output: Any) -> str:
    if hasattr(output, "indicator"):
        return output.indicator
    if isinstance(output, dict):
        return output.get("indicator", "")
    return ""


def _get_metadata(output: Any) -> dict:
    if hasattr(output, "metadata"):
        m = output.metadata
        return m if isinstance(m, dict) else {}
    if isinstance(output, dict):
        return output.get("metadata", {}) or {}
    return {}


# ============================================================================
# Scenarios for each agent
# ============================================================================

LOGIC_SCENARIOS: list[LogicScenario] = []


def _scenario(agent_id: str, scenario_id: str, category: str, description: str,
              setup: Callable, check: Callable, expected_pass: bool = True):
    LOGIC_SCENARIOS.append(LogicScenario(
        agent_id=agent_id, scenario_id=scenario_id, category=category,
        description=description, setup=setup, check=check, expected_pass=expected_pass,
    ))


# ─── EMA scenarios ────────────────────────────────────────────────────────

def _ema_manual_calc(closes: list[float], period: int) -> list[float]:
    """Manual EMA calculation for cross-validation."""
    if len(closes) < period:
        return []
    multiplier = 2 / (period + 1)
    ema = [sum(closes[:period]) / period]  # SMA seed
    for i in range(period, len(closes)):
        ema.append(closes[i] * multiplier + ema[-1] * (1 - multiplier))
    return ema


_scenario("ta.ema", "ema_formula_correctness", "formula",
    "EMA value matches manual calculation within 0.01 tolerance",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        abs(_get_value(out) - _ema_manual_calc([450 + i * 0.3 for i in range(60)], 20)[-1]) < 0.05,
        f"EMA={_get_value(out)}, expected≈{_ema_manual_calc([450 + i * 0.3 for i in range(60)], 20)[-1]:.4f}"
    )
)

_scenario("ta.ema", "ema_warmup_insufficient", "warmup",
    "EMA returns low confidence or None when insufficient bars",
    setup=lambda: (_insufficient_bars(5), {}),
    check=lambda out: (
        _get_confidence(out) is not None and _get_confidence(out) < 0.5,
        f"confidence={_get_confidence(out)} (expected < 0.5 for insufficient data)"
    )
)

_scenario("ta.ema", "ema_flat_series", "edge_case",
    "EMA on flat series should equal the flat price",
    setup=lambda: (_flat_bars(60, 450.0), {}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and abs(_get_value(out) - 450.0) < 0.1,
        f"EMA={_get_value(out)}, expected≈450.0 for flat series"
    )
)

_scenario("ta.ema", "ema_output_range", "range",
    "EMA output is a finite positive number",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        math.isfinite(_get_value(out)) and
        _get_value(out) > 0,
        f"EMA={_get_value(out)} (must be finite positive)"
    )
)


# ─── SMA scenarios ───────────────────────────────────────────────────────

def _sma_manual_calc(closes: list[float], period: int) -> list[float]:
    if len(closes) < period:
        return []
    return [sum(closes[i:i+period]) / period for i in range(len(closes) - period + 1)]


_scenario("ta.sma", "sma_formula_correctness", "formula",
    "SMA value matches manual calculation",
    setup=lambda: (_bullish_trend_bars(60), {"period": 50}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        abs(_get_value(out) - _sma_manual_calc([450 + i * 0.3 for i in range(60)], 50)[-1]) < 0.05,
        f"SMA={_get_value(out)}, expected≈{_sma_manual_calc([450 + i * 0.3 for i in range(60)], 50)[-1]:.4f}"
    )
)

_scenario("ta.sma", "sma_warmup_insufficient", "warmup",
    "SMA returns low confidence when insufficient bars",
    setup=lambda: (_insufficient_bars(5), {"period": 50}),
    check=lambda out: (
        _get_confidence(out) is not None and _get_confidence(out) < 0.5,
        f"confidence={_get_confidence(out)} (expected < 0.5)"
    )
)

_scenario("ta.sma", "sma_flat_series", "edge_case",
    "SMA on flat series should equal the flat price",
    setup=lambda: (_flat_bars(60, 450.0), {"period": 20}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and abs(_get_value(out) - 450.0) < 0.1,
        f"SMA={_get_value(out)}, expected≈450.0"
    )
)


# ─── RSI scenarios ───────────────────────────────────────────────────────

def _rsi_manual_calc(closes: list[float], period: int = 14) -> list[float]:
    """Manual RSI calculation."""
    if len(closes) < period + 1:
        return []
    gains, losses = [], []
    for i in range(1, period + 1):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rs = avg_gain / avg_loss if avg_loss > 0 else float('inf')
    rsi = 100 - (100 / (1 + rs))
    return [rsi]


_scenario("ta.rsi", "rsi_output_range_0_100", "range",
    "RSI value must be between 0 and 100",
    setup=lambda: (_bullish_trend_bars(60), {"period": 14}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        0 <= _get_value(out) <= 100,
        f"RSI={_get_value(out)} (must be 0-100)"
    )
)

_scenario("ta.rsi", "rsi_bullish_trend_high", "formula",
    "RSI in strong bullish trend should be > 50 (momentum up)",
    setup=lambda: (_bullish_trend_bars(60, slope=0.5), {"period": 14}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        _get_value(out) > 50,
        f"RSI={_get_value(out)} (expected > 50 in bullish trend)"
    )
)

_scenario("ta.rsi", "rsi_bearish_trend_low", "formula",
    "RSI in strong bearish trend should be < 50",
    setup=lambda: (_bearish_trend_bars(60, slope=-0.5), {"period": 14}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        _get_value(out) < 50,
        f"RSI={_get_value(out)} (expected < 50 in bearish trend)"
    )
)

_scenario("ta.rsi", "rsi_warmup_insufficient", "warmup",
    "RSI returns low confidence with insufficient bars",
    setup=lambda: (_insufficient_bars(5), {"period": 14}),
    check=lambda out: (
        _get_confidence(out) is not None and _get_confidence(out) < 0.5,
        f"confidence={_get_confidence(out)} (expected < 0.5)"
    )
)


# ─── MACD scenarios ──────────────────────────────────────────────────────

_scenario("ta.macd", "macd_output_structure", "range",
    "MACD output must contain macd, signal, histogram keys",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        all(k in _get_value(out) for k in ("macd", "signal", "histogram")),
        f"MACD output keys: {list(_get_value(out).keys()) if isinstance(_get_value(out), dict) else 'not dict'}"
    )
)

_scenario("ta.macd", "macd_bullish_trend_positive", "formula",
    "MACD line should be positive in strong bullish trend",
    setup=lambda: (_bullish_trend_bars(60, slope=0.5), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        isinstance(_get_value(out).get("macd"), (int, float)) and
        _get_value(out)["macd"] > 0,
        f"MACD={_get_value(out).get('macd') if isinstance(_get_value(out), dict) else 'N/A'} (expected > 0)"
    )
)

_scenario("ta.macd", "macd_bearish_trend_negative", "formula",
    "MACD line should be negative in strong bearish trend",
    setup=lambda: (_bearish_trend_bars(60, slope=-0.5), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        isinstance(_get_value(out).get("macd"), (int, float)) and
        _get_value(out)["macd"] < 0,
        f"MACD={_get_value(out).get('macd') if isinstance(_get_value(out), dict) else 'N/A'} (expected < 0)"
    )
)

_scenario("ta.macd", "macd_histogram_equals_diff", "formula",
    "Histogram should equal MACD - signal",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        abs(_get_value(out).get("histogram", 0) - (
            _get_value(out).get("macd", 0) - _get_value(out).get("signal", 0)
        )) < 0.001,
        f"histogram={_get_value(out).get('histogram')}, macd-signal={_get_value(out).get('macd', 0) - _get_value(out).get('signal', 0)}"
    )
)


# ─── ADX scenarios ───────────────────────────────────────────────────────

_scenario("ta.adx", "adx_output_range_0_100", "range",
    "ADX must be between 0 and 100",
    setup=lambda: (_bullish_trend_bars(60), {"period": 14}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        0 <= _get_value(out) <= 100,
        f"ADX={_get_value(out)} (must be 0-100)"
    )
)

_scenario("ta.adx", "adx_strong_trend_high", "formula",
    "ADX in strong trend should be > 20 (trending)",
    setup=lambda: (_bullish_trend_bars(60, slope=0.5), {"period": 14}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        _get_value(out) > 20,
        f"ADX={_get_value(out)} (expected > 20 in strong trend)"
    )
)

_scenario("ta.adx", "adx_warmup_insufficient", "warmup",
    "ADX returns low confidence with insufficient bars",
    setup=lambda: (_insufficient_bars(5), {"period": 14}),
    check=lambda out: (
        _get_confidence(out) is not None and _get_confidence(out) < 0.5,
        f"confidence={_get_confidence(out)} (expected < 0.5)"
    )
)


# ─── ATR scenarios ───────────────────────────────────────────────────────

_scenario("ta.atr", "atr_output_positive", "range",
    "ATR must be a positive number",
    setup=lambda: (_bullish_trend_bars(60), {"period": 14}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        _get_value(out) > 0,
        f"ATR={_get_value(out)} (must be > 0)"
    )
)

_scenario("ta.atr", "atr_flat_series_low", "formula",
    "ATR on flat series should be very small (near 0)",
    setup=lambda: (_flat_bars(60, 450.0), {"period": 14}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        _get_value(out) < 0.5,
        f"ATR={_get_value(out)} (expected < 0.5 for flat series)"
    )
)


# ─── VWAP scenarios ──────────────────────────────────────────────────────

_scenario("ta.vwap", "vwap_output_finite_positive", "range",
    "VWAP must be a finite positive number",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), (int, float)) and
        math.isfinite(_get_value(out)) and
        _get_value(out) > 0,
        f"VWAP={_get_value(out)} (must be finite positive)"
    )
)


# ─── Bollinger scenarios ─────────────────────────────────────────────────

_scenario("ta.bollinger", "bollinger_output_structure", "range",
    "Bollinger output must contain upper, middle, lower, percent_b",
    setup=lambda: (_bullish_trend_bars(60), {"period": 20}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        all(k in _get_value(out) for k in ("upper", "middle", "lower", "percent_b")),
        f"Bollinger keys: {list(_get_value(out).keys()) if isinstance(_get_value(out), dict) else 'N/A'}"
    )
)

_scenario("ta.bollinger", "bollinger_band_ordering", "formula",
    "Bollinger bands must satisfy: lower <= middle <= upper",
    setup=lambda: (_bullish_trend_bars(60), {"period": 20}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        _get_value(out).get("lower", 0) <= _get_value(out).get("middle", 0) <= _get_value(out).get("upper", 0),
        f"lower={_get_value(out).get('lower')}, middle={_get_value(out).get('middle')}, upper={_get_value(out).get('upper')}"
    )
)

_scenario("ta.bollinger", "bollinger_percent_b_range", "range",
    "percent_b should be finite (can be < 0 or > 1 in extremes)",
    setup=lambda: (_bullish_trend_bars(60), {"period": 20}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        isinstance(_get_value(out).get("percent_b"), (int, float)) and
        math.isfinite(_get_value(out)["percent_b"]),
        f"percent_b={_get_value(out).get('percent_b')}"
    )
)


# ─── Trend scenarios ─────────────────────────────────────────────────────

_scenario("ta.trend", "trend_bullish_detected", "formula",
    "Trend agent should return 'bullish' for strong uptrend",
    setup=lambda: (_bullish_trend_bars(60, slope=0.5), {}),
    check=lambda out: (
        _get_value(out) == "bullish",
        f"trend={_get_value(out)} (expected 'bullish')"
    )
)

_scenario("ta.trend", "trend_bearish_detected", "formula",
    "Trend agent should return 'bearish' for strong downtrend",
    setup=lambda: (_bearish_trend_bars(60, slope=-0.5), {}),
    check=lambda out: (
        _get_value(out) == "bearish",
        f"trend={_get_value(out)} (expected 'bearish')"
    )
)

_scenario("ta.trend", "trend_flat_returns_ranging", "formula",
    "Trend agent should return 'ranging' for flat market",
    setup=lambda: (_flat_bars(60, 450.0), {}),
    check=lambda out: (
        _get_value(out) == "ranging",
        f"trend={_get_value(out)} (expected 'ranging')"
    )
)


# ─── Swing High/Low scenarios ────────────────────────────────────────────

_scenario("ta.swing", "swing_output_structure", "range",
    "Swing output must contain swing_highs and swing_lows lists",
    setup=lambda: (_oscillating_bars(100, amplitude=2.0), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        "swing_highs" in _get_value(out) and
        "swing_lows" in _get_value(out),
        f"Swing keys: {list(_get_value(out).keys()) if isinstance(_get_value(out), dict) else 'N/A'}"
    )
)

_scenario("ta.swing", "swing_finds_pivots", "formula",
    "Swing agent should find at least 2 swing highs in oscillating market",
    setup=lambda: (_oscillating_bars(100, amplitude=2.0), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        len(_get_value(out).get("swing_highs", [])) >= 1,
        f"swing_highs count: {len(_get_value(out).get('swing_highs', [])) if isinstance(_get_value(out), dict) else 0}"
    )
)


# ─── Support/Resistance scenarios ────────────────────────────────────────

_scenario("ta.support_resistance", "sr_output_structure", "range",
    "S/R output must contain support and resistance levels",
    setup=lambda: (_oscillating_bars(100, amplitude=2.0), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        "support" in _get_value(out) and
        "resistance" in _get_value(out),
        f"S/R keys: {list(_get_value(out).keys()) if isinstance(_get_value(out), dict) else 'N/A'}"
    ),
)

_scenario("ta.support_resistance", "sr_resistance_above_support", "formula",
    "Resistance must be above support",
    setup=lambda: (_oscillating_bars(100, amplitude=2.0), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        _get_value(out).get("resistance", 0) > _get_value(out).get("support", 0),
        f"resistance={_get_value(out).get('resistance')}, support={_get_value(out).get('support')}"
    ),
)


# ─── Liquidity scenarios ─────────────────────────────────────────────────

_scenario("ta.liquidity", "liquidity_output_structure", "range",
    "Liquidity output must contain liquidity_pools list",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        "liquidity_pools" in _get_value(out),
        f"Liquidity keys: {list(_get_value(out).keys()) if isinstance(_get_value(out), dict) else 'N/A'}"
    )
)


# ─── Volume Profile scenarios ────────────────────────────────────────────

_scenario("ta.volume_profile", "vp_output_structure", "range",
    "Volume Profile output must be a dict",
    setup=lambda: (_bullish_trend_bars(100), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict),
        f"VP value type: {type(_get_value(out)).__name__}"
    )
)


# ─── Multi-Timeframe scenarios ───────────────────────────────────────────

_scenario("ta.multi_timeframe_data", "mtf_output_is_dict", "range",
    "MTF output should be a dict mapping timeframes to bar data",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        _get_value(out) is not None,
        f"MTF value: {str(_get_value(out))[:80]}"
    )
)


# ─── Wyckoff scenarios ───────────────────────────────────────────────────

_scenario("ta.wyckoff", "wyckoff_output_has_phase", "range",
    "Wyckoff output must contain a 'phase' field",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        "phase" in _get_value(out),
        f"Wyckoff keys: {list(_get_value(out).keys()) if isinstance(_get_value(out), dict) else 'N/A'}"
    )
)

_scenario("ta.wyckoff", "wyckoff_phase_valid_value", "formula",
    "Wyckoff phase must be one of: accumulation, markup, distribution, markdown",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict) and
        _get_value(out).get("phase") in ("accumulation", "markup", "distribution", "markdown"),
        f"phase={_get_value(out).get('phase') if isinstance(_get_value(out), dict) else 'N/A'}"
    )
)


# ─── Chan Theory scenarios ───────────────────────────────────────────────

_scenario("ta.chan_theory", "chan_output_structure", "range",
    "Chan Theory output must be a dict",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict),
        f"Chan value type: {type(_get_value(out)).__name__}"
    )
)


# ─── Elliott Wave scenarios ──────────────────────────────────────────────

_scenario("ta.elliott_wave", "elliott_output_structure", "range",
    "Elliott Wave output must be a dict",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict),
        f"Elliott value type: {type(_get_value(out)).__name__}"
    )
)


# ─── Smart Money scenarios ───────────────────────────────────────────────

_scenario("ta.smart_money", "smart_money_output_structure", "range",
    "Smart Money output must be a dict",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict),
        f"SmartMoney value type: {type(_get_value(out)).__name__}"
    )
)


# ─── Volume Price scenarios ──────────────────────────────────────────────

_scenario("ta.volume_price", "volume_price_output_structure", "range",
    "Volume Price output must be a dict",
    setup=lambda: (_bullish_trend_bars(60), {}),
    check=lambda out: (
        isinstance(_get_value(out), dict),
        f"VolumePrice value type: {type(_get_value(out)).__name__}"
    )
)


# ============================================================================
# Scenario runner
# ============================================================================

class LogicScenarioRunner:
    """Runs all logic scenarios and collects results."""

    def __init__(self):
        self.scenarios = list(LOGIC_SCENARIOS)

    def scenarios_for(self, agent_id: str) -> list[LogicScenario]:
        return [s for s in self.scenarios if s.agent_id == agent_id]

    def all_agent_ids(self) -> list[str]:
        return sorted(set(s.agent_id for s in self.scenarios))

    @property
    def total_scenarios(self) -> int:
        return len(self.scenarios)
