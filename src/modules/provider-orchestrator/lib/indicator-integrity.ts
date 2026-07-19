/**
 * Indicator Integrity Validator — checks indicator outputs for correctness.
 *
 * Since ATHENA-X is indicator-heavy, this validates outputs after each update.
 * If indicators become invalid, certification should fail even if the
 * provider responds correctly.
 *
 * Indicator states:
 *   READY     — indicator has enough data and produced valid values
 *   NOT_READY — indicator needs more data for warm-up (does NOT count as failure)
 *   INVALID   — indicator produced NaN, Infinity, or out-of-range values (counts as failure)
 */

import type { MarketData } from "./types";

export type IndicatorState = "ready" | "not_ready" | "invalid";

export interface IndicatorCheck {
  name: string;
  value: number;
  state: IndicatorState;
  error?: string;
  warmupBarsNeeded?: number;
}

export interface IndicatorIntegrityResult {
  allValid: boolean;          // true if no INVALID (NOT_READY is OK)
  anyNotReady: boolean;       // true if any indicators are in warm-up
  readyCount: number;
  notReadyCount: number;
  invalidCount: number;
  checks: IndicatorCheck[];
  nanCount: number;
  infinityCount: number;
  undefinedCount: number;
}

// Minimum bars required for each indicator to be considered "ready"
const WARMUP_PERIODS: Record<string, number> = {
  "EMA-12": 12,
  "EMA-26": 26,
  "SMA": 10,
  "RSI": 14,
  "ATR": 14,
  "VWAP": 2,
  "BB-Upper": 20,
  "BB-Lower": 20,
  "MACD": 26,
  "EMA Jump": 3,
};

export function validateIndicators(data: MarketData[]): IndicatorIntegrityResult {
  const checks: IndicatorCheck[] = [];
  let nanCount = 0;
  let infinityCount = 0;
  let undefinedCount = 0;
  let readyCount = 0;
  let notReadyCount = 0;
  let invalidCount = 0;

  if (data.length < 2) {
    return {
      allValid: true,  // not invalid — just not ready
      anyNotReady: true,
      readyCount: 0,
      notReadyCount: 1,
      invalidCount: 0,
      checks: [{ name: "All Indicators", value: 0, state: "not_ready", error: "Need at least 2 bars", warmupBarsNeeded: 2 }],
      nanCount: 0, infinityCount: 0, undefinedCount: 0,
    };
  }

  const closes = data.map((d) => d.close);
  const highs = data.map((d) => d.high);
  const lows = data.map((d) => d.low);
  const volumes = data.map((d) => d.volume);

  // Helper: check value with warm-up awareness
  const check = (
    name: string,
    val: number,
    validator: (v: number) => boolean,
    errorMsg: string,
    minBars?: number
  ): IndicatorCheck => {
    const warmup = minBars ?? WARMUP_PERIODS[name] ?? 1;

    // Not enough data for warm-up
    if (data.length < warmup) {
      notReadyCount++;
      return { name, value: 0, state: "not_ready", warmupBarsNeeded: warmup };
    }

    // Check for NaN/Infinity/Undefined
    if (Number.isNaN(val)) {
      nanCount++; invalidCount++;
      return { name, value: val, state: "invalid", error: "NaN" };
    }
    if (!Number.isFinite(val)) {
      infinityCount++; invalidCount++;
      return { name, value: val, state: "invalid", error: "Infinity" };
    }

    // Check range
    if (!validator(val)) {
      invalidCount++;
      return { name, value: val, state: "invalid", error: errorMsg };
    }

    readyCount++;
    return { name, value: val, state: "ready" };
  };

  // EMA-12
  const k12 = 2 / (12 + 1);
  let ema12 = closes[0];
  for (let i = 1; i < closes.length; i++) ema12 = closes[i] * k12 + ema12 * (1 - k12);
  checks.push(check("EMA-12", ema12, (v) => v > 0, "EMA must be positive"));

  // SMA-10
  const smaWindow = Math.min(10, closes.length);
  const sma = closes.slice(-smaWindow).reduce((s, v) => s + v, 0) / smaWindow;
  checks.push(check("SMA", sma, (v) => v > 0, "SMA must be positive"));

  // RSI-14
  const rsiWindow = Math.min(14, closes.length - 1);
  if (closes.length >= 15) {
    let gains = 0, losses = 0;
    for (let i = 1; i <= rsiWindow; i++) {
      const change = closes[i] - closes[i - 1];
      if (change > 0) gains += change; else losses -= change;
    }
    const avgGain = gains / rsiWindow;
    const avgLoss = losses / rsiWindow;
    const rsi = avgLoss === 0 ? 100 : 100 - (100 / (1 + (avgGain / avgLoss)));
    checks.push(check("RSI", rsi, (v) => v >= 0 && v <= 100, "RSI must be 0-100"));
  } else {
    checks.push({ name: "RSI", value: 0, state: "not_ready", warmupBarsNeeded: 15 });
    notReadyCount++;
  }

  // ATR-14
  if (data.length >= 15) {
    const atrWindow = Math.min(14, data.length - 1);
    let trSum = 0;
    for (let i = 1; i <= atrWindow; i++) {
      const tr = Math.max(
        highs[i] - lows[i],
        Math.abs(highs[i] - closes[i - 1]),
        Math.abs(lows[i] - closes[i - 1])
      );
      trSum += tr;
    }
    const atr = trSum / atrWindow;
    checks.push(check("ATR", atr, (v) => v >= 0, "ATR must be non-negative"));
  } else {
    checks.push({ name: "ATR", value: 0, state: "not_ready", warmupBarsNeeded: 15 });
    notReadyCount++;
  }

  // VWAP — allows 0 for zero-volume instruments (indices like VIX)
  const totalPV = closes.reduce((s, c, i) => s + c * volumes[i], 0);
  const totalV = volumes.reduce((s, v) => s + v, 0);
  const vwap = totalV > 0 ? totalPV / totalV : 0;
  checks.push(check("VWAP", vwap, (v) => v > 0 || (v === 0 && totalV === 0), "VWAP must be positive (or 0 if no volume)"));

  // Bollinger Bands (needs 20 bars)
  if (closes.length >= 20) {
    const bbWindow = Math.min(20, closes.length);
    const bbSma = closes.slice(-bbWindow).reduce((s, v) => s + v, 0) / bbWindow;
    const bbVariance = closes.slice(-bbWindow).reduce((s, v) => s + (v - bbSma) ** 2, 0) / bbWindow;
    const bbStd = Math.sqrt(bbVariance);
    const bbUpper = bbSma + 2 * bbStd;
    const bbLower = bbSma - 2 * bbStd;
    checks.push(check("BB-Upper", bbUpper, (v) => v > bbSma, "BB Upper must be > SMA"));
    checks.push(check("BB-Lower", bbLower, (v) => v < bbSma, "BB Lower must be < SMA"));
  } else {
    checks.push({ name: "BB-Upper", value: 0, state: "not_ready", warmupBarsNeeded: 20 });
    checks.push({ name: "BB-Lower", value: 0, state: "not_ready", warmupBarsNeeded: 20 });
    notReadyCount += 2;
  }

  // MACD (needs 26 bars for EMA-26)
  if (closes.length >= 26) {
    const k26 = 2 / (26 + 1);
    let ema26 = closes[0];
    for (let i = 1; i < closes.length; i++) ema26 = closes[i] * k26 + ema26 * (1 - k26);
    const macd = ema12 - ema26;
    checks.push(check("MACD", macd, () => true, "MACD can be any value"));
  } else {
    checks.push({ name: "MACD", value: 0, state: "not_ready", warmupBarsNeeded: 26 });
    notReadyCount++;
  }

  // EMA jump detection (needs at least 3 bars)
  if (closes.length >= 3) {
    let prevEma = closes[0];
    let emaJumpDetected = false;
    for (let i = 1; i < closes.length; i++) {
      const newEma = closes[i] * k12 + prevEma * (1 - k12);
      if (i > 1) {
        const jump = Math.abs(newEma - prevEma) / prevEma;
        if (jump > 0.10) { emaJumpDetected = true; break; }
      }
      prevEma = newEma;
    }
    if (emaJumpDetected) {
      invalidCount++;
      checks.push({ name: "EMA Jump", value: 0, state: "invalid", error: "EMA jumped > 10% in one step (possible bad data)" });
    } else {
      readyCount++;
      checks.push({ name: "EMA Jump", value: 0, state: "ready" });
    }
  } else {
    checks.push({ name: "EMA Jump", value: 0, state: "not_ready", warmupBarsNeeded: 3 });
    notReadyCount++;
  }

  const allValid = invalidCount === 0;  // NOT_READY is OK — only INVALID fails

  return {
    allValid,
    anyNotReady: notReadyCount > 0,
    readyCount,
    notReadyCount,
    invalidCount,
    checks,
    nanCount,
    infinityCount,
    undefinedCount,
  };
}
