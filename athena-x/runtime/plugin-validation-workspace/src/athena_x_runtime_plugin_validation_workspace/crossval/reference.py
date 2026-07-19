"""Phase 6 — Cross-Validation against reference implementations.

Compares ATHENA-X agent outputs against:
  - pandas-ta (Python TA library)
  - Manual calculations (hand-computed expected values)

For each agent, runs both the agent and the reference implementation on the
same input data, then compares outputs. Reports mismatches with the
difference and tolerance.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field, asdict
from typing import Any
import numpy as np
import pandas as pd

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False


@dataclass
class ReferenceResult:
    """One cross-validation result."""
    agent_id: str
    reference: str           # "pandas-ta" | "manual" | "N/A"
    agent_value: Any
    reference_value: Any
    difference: float | None
    tolerance: float
    passed: bool
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def _bars_to_df(bars: list[dict]) -> pd.DataFrame:
    """Convert OHLCV bar list to pandas DataFrame."""
    df = pd.DataFrame(bars)
    # Ensure numeric types
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _safe_float(v: Any) -> float | None:
    """Try to convert any value to a finite float."""
    if v is None:
        return None
    try:
        f = float(v)
        if math.isfinite(f):
            return f
    except (TypeError, ValueError):
        pass
    return None


def _compare(a: float | None, b: float | None, tolerance: float = 0.01) -> tuple[float | None, bool, str]:
    """Compare two values. Returns (difference, passed, message)."""
    if a is None or b is None:
        return None, False, f"cannot compare: agent={a}, reference={b}"
    diff = abs(a - b)
    passed = diff <= tolerance
    return diff, passed, f"agent={a:.6f}, ref={b:.6f}, diff={diff:.6f} (tol={tolerance})"


# ============================================================================
# Reference implementations
# ============================================================================

def ref_ema(closes: list[float], period: int = 20) -> float | None:
    if not PANDAS_TA_AVAILABLE or len(closes) < period:
        return None
    s = pd.Series(closes)
    ema = ta.ema(s, length=period)
    v = ema.iloc[-1]
    return _safe_float(v)


def ref_sma(closes: list[float], period: int = 50) -> float | None:
    if not PANDAS_TA_AVAILABLE or len(closes) < period:
        return None
    s = pd.Series(closes)
    sma = ta.sma(s, length=period)
    v = sma.iloc[-1]
    return _safe_float(v)


def ref_rsi(closes: list[float], period: int = 14) -> float | None:
    if not PANDAS_TA_AVAILABLE or len(closes) < period + 1:
        return None
    s = pd.Series(closes)
    rsi = ta.rsi(s, length=period)
    v = rsi.iloc[-1]
    return _safe_float(v)


def ref_macd(closes: list[float]) -> dict | None:
    if not PANDAS_TA_AVAILABLE or len(closes) < 35:
        return None
    s = pd.Series(closes)
    macd_df = ta.macd(s, fast=12, slow=26, signal=9)
    if macd_df is None or macd_df.empty:
        return None
    # pandas-ta returns columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_") and not c.startswith("MACDh") and not c.startswith("MACDs")][0]
    signal_col = [c for c in macd_df.columns if c.startswith("MACDs")][0]
    hist_col = [c for c in macd_df.columns if c.startswith("MACDh")][0]
    return {
        "macd": _safe_float(macd_df[macd_col].iloc[-1]),
        "signal": _safe_float(macd_df[signal_col].iloc[-1]),
        "histogram": _safe_float(macd_df[hist_col].iloc[-1]),
    }


def ref_atr(bars: list[dict], period: int = 14) -> float | None:
    if not PANDAS_TA_AVAILABLE or len(bars) < period + 1:
        return None
    df = _bars_to_df(bars)
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    v = atr.iloc[-1]
    return _safe_float(v)


def ref_adx(bars: list[dict], period: int = 14) -> float | None:
    if not PANDAS_TA_AVAILABLE or len(bars) < period * 2:
        return None
    df = _bars_to_df(bars)
    adx = ta.adx(df["high"], df["low"], df["close"], length=period)
    if adx is None or adx.empty:
        return None
    adx_col = [c for c in adx.columns if c.startswith("ADX")][0]
    v = adx[adx_col].iloc[-1]
    return _safe_float(v)


def ref_bollinger(closes: list[float], period: int = 20, std: float = 2.0) -> dict | None:
    if not PANDAS_TA_AVAILABLE or len(closes) < period:
        return None
    s = pd.Series(closes)
    bb = ta.bbands(s, length=period, std=std)
    if bb is None or bb.empty:
        return None
    lower_col = [c for c in bb.columns if c.startswith("BBL")][0]
    mid_col = [c for c in bb.columns if c.startswith("BBM")][0]
    upper_col = [c for c in bb.columns if c.startswith("BBU")][0]
    return {
        "lower": _safe_float(bb[lower_col].iloc[-1]),
        "middle": _safe_float(bb[mid_col].iloc[-1]),
        "upper": _safe_float(bb[upper_col].iloc[-1]),
    }


def ref_vwap(bars: list[dict]) -> float | None:
    """Manual VWAP (pandas-ta's vwap requires intraday session logic)."""
    if not bars:
        return None
    df = _bars_to_df(bars)
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"].replace(0, np.nan).fillna(method="ffill").fillna(1)
    vwap = (typical_price * vol).cumsum() / vol.cumsum()
    return _safe_float(vwap.iloc[-1])


# ============================================================================
# Cross-validator
# ============================================================================

class CrossValidator:
    """Cross-validates agent outputs against reference implementations."""

    def __init__(self, tolerance: float = 0.05):
        """tolerance: max acceptable difference (in price units for SPY-scale)."""
        self.tolerance = tolerance

    def available(self) -> bool:
        return PANDAS_TA_AVAILABLE

    def validate(self, agent_id: str, agent_output: Any, bars: list[dict]) -> ReferenceResult:
        """Cross-validate one agent output against the reference implementation."""
        if not PANDAS_TA_AVAILABLE:
            return ReferenceResult(
                agent_id=agent_id, reference="N/A",
                agent_value=agent_output, reference_value=None,
                difference=None, tolerance=self.tolerance,
                passed=False, message="pandas-ta not available",
            )

        closes = [b["close"] for b in bars]

        # Extract agent value
        agent_val = None
        if hasattr(agent_output, "value"):
            agent_val = agent_output.value
        elif isinstance(agent_output, dict):
            agent_val = agent_output.get("value")

        # Dispatch based on agent_id
        if agent_id == "ta.ema":
            ref = ref_ema(closes, period=20)
            av = _safe_float(agent_val)
            diff, passed, msg = _compare(av, ref, tolerance=max(self.tolerance, abs(ref) * 0.001) if ref else self.tolerance)
            return ReferenceResult(agent_id, "pandas-ta", av, ref, diff, self.tolerance, passed, msg)

        elif agent_id == "ta.sma":
            ref = ref_sma(closes, period=50)
            av = _safe_float(agent_val)
            diff, passed, msg = _compare(av, ref, tolerance=max(self.tolerance, abs(ref) * 0.001) if ref else self.tolerance)
            return ReferenceResult(agent_id, "pandas-ta", av, ref, diff, self.tolerance, passed, msg)

        elif agent_id == "ta.rsi":
            ref = ref_rsi(closes, period=14)
            av = _safe_float(agent_val)
            diff, passed, msg = _compare(av, ref, tolerance=1.0)  # RSI tolerance: 1.0 unit
            return ReferenceResult(agent_id, "pandas-ta", av, ref, diff, 1.0, passed, msg)

        elif agent_id == "ta.macd":
            ref = ref_macd(closes)
            av = agent_val if isinstance(agent_val, dict) else {}
            if ref is None:
                return ReferenceResult(agent_id, "pandas-ta", av, None, None, self.tolerance, False, "reference returned None")
            av_macd = _safe_float(av.get("macd"))
            diff, passed, msg = _compare(av_macd, ref["macd"], tolerance=max(self.tolerance, abs(ref["macd"]) * 0.01) if ref["macd"] else self.tolerance)
            return ReferenceResult(agent_id, "pandas-ta", av_macd, ref["macd"], diff, self.tolerance, passed, msg)

        elif agent_id == "ta.atr":
            ref = ref_atr(bars, period=14)
            av = _safe_float(agent_val)
            diff, passed, msg = _compare(av, ref, tolerance=max(self.tolerance, abs(ref) * 0.05) if ref else self.tolerance)
            return ReferenceResult(agent_id, "pandas-ta", av, ref, diff, self.tolerance, passed, msg)

        elif agent_id == "ta.adx":
            ref = ref_adx(bars, period=14)
            av = _safe_float(agent_val)
            diff, passed, msg = _compare(av, ref, tolerance=5.0)  # ADX tolerance: 5 units
            return ReferenceResult(agent_id, "pandas-ta", av, ref, diff, 5.0, passed, msg)

        elif agent_id == "ta.bollinger":
            ref = ref_bollinger(closes, period=20)
            av = agent_val if isinstance(agent_val, dict) else {}
            if ref is None:
                return ReferenceResult(agent_id, "pandas-ta", av, None, None, self.tolerance, False, "reference returned None")
            av_upper = _safe_float(av.get("upper"))
            diff, passed, msg = _compare(av_upper, ref["upper"], tolerance=max(self.tolerance, abs(ref["upper"]) * 0.001) if ref["upper"] else self.tolerance)
            return ReferenceResult(agent_id, "pandas-ta", av_upper, ref["upper"], diff, self.tolerance, passed, msg)

        elif agent_id == "ta.vwap":
            ref = ref_vwap(bars)
            av = _safe_float(agent_val)
            diff, passed, msg = _compare(av, ref, tolerance=max(self.tolerance, abs(ref) * 0.005) if ref else self.tolerance)
            return ReferenceResult(agent_id, "manual", av, ref, diff, self.tolerance, passed, msg)

        else:
            # No reference implementation for this agent
            return ReferenceResult(
                agent_id=agent_id, reference="N/A",
                agent_value=agent_val, reference_value=None,
                difference=None, tolerance=self.tolerance,
                passed=False, message=f"no reference implementation for {agent_id}",
            )
