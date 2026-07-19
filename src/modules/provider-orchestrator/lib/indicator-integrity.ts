/**
 * Indicator Integrity Validator — checks indicator outputs for correctness.
 *
 * Since ATHENA-X is indicator-heavy, this validates outputs after each update.
 * If indicators become invalid, certification should fail even if the
 * provider responds correctly.
 */

import type { MarketData } from "./types";

export interface IndicatorCheck {
  name: string;
  value: number;
  valid: boolean;
  error?: string;
}

export interface IndicatorIntegrityResult {
  allValid: boolean;
  checks: IndicatorCheck[];
  nanCount: number;
  infinityCount: number;
  undefinedCount: number;
}

export function validateIndicators(data: MarketData[]): IndicatorIntegrityResult {
  const checks: IndicatorCheck[] = [];
  let nanCount = 0;
  let infinityCount = 0;
  let undefinedCount = 0;

  if (data.length < 2) {
    return {
      allValid: false,
      checks: [{ name: "Insufficient data", value: 0, valid: false, error: "Need at least 2 bars" }],
      nanCount: 0, infinityCount: 0, undefinedCount: 0,
    };
  }

  const closes = data.map((d) => d.close);
  const highs = data.map((d) => d.high);
  const lows = data.map((d) => d.low);
  const volumes = data.map((d) => d.volume);

  // Helper: check value
  const check = (name: string, val: number, validator: (v: number) => boolean, errorMsg: string): IndicatorCheck => {
    if (Number.isNaN(val)) { nanCount++; return { name, value: val, valid: false, error: "NaN" }; }
    if (!Number.isFinite(val)) { infinityCount++; return { name, value: val, valid: false, error: "Infinity" }; }
    if (val === undefined) { undefinedCount++; return { name, value: val, valid: false, error: "Undefined" }; }
    if (!validator(val)) { return { name, value: val, valid: false, error: errorMsg }; }
    return { name, value: val, valid: true };
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

  // RSI
  const rsiWindow = Math.min(14, closes.length - 1);
  let gains = 0, losses = 0;
  for (let i = 1; i <= rsiWindow; i++) {
    const change = closes[i] - closes[i - 1];
    if (change > 0) gains += change; else losses -= change;
  }
  const avgGain = gains / rsiWindow;
  const avgLoss = losses / rsiWindow;
  const rsi = avgLoss === 0 ? 100 : 100 - (100 / (1 + (avgGain / avgLoss)));
  checks.push(check("RSI", rsi, (v) => v >= 0 && v <= 100, "RSI must be 0-100"));

  // ATR
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

  // VWAP
  const totalPV = closes.reduce((s, c, i) => s + c * volumes[i], 0);
  const totalV = volumes.reduce((s, v) => s + v, 0);
  const vwap = totalV > 0 ? totalPV / totalV : 0;
  checks.push(check("VWAP", vwap, (v) => v > 0, "VWAP must be positive"));

  // Bollinger Bands
  const bbWindow = Math.min(20, closes.length);
  const bbSma = closes.slice(-bbWindow).reduce((s, v) => s + v, 0) / bbWindow;
  const bbVariance = closes.slice(-bbWindow).reduce((s, v) => s + (v - bbSma) ** 2, 0) / bbWindow;
  const bbStd = Math.sqrt(bbVariance);
  const bbUpper = bbSma + 2 * bbStd;
  const bbLower = bbSma - 2 * bbStd;
  checks.push(check("BB-Upper", bbUpper, (v) => v > bbSma, "BB Upper must be > SMA"));
  checks.push(check("BB-Lower", bbLower, (v) => v < bbSma, "BB Lower must be < SMA"));

  // MACD
  const k26 = 2 / (26 + 1);
  let ema26 = closes[0];
  for (let i = 1; i < closes.length; i++) ema26 = closes[i] * k26 + ema26 * (1 - k26);
  const macd = ema12 - ema26;
  checks.push(check("MACD", macd, () => true, "MACD can be any value"));

  // EMA jump detection (should not jump more than 10% in one step)
  let prevEma = closes[0];
  let emaJumpDetected = false;
  for (let i = 1; i < closes.length; i++) {
    prevEma = closes[i] * k12 + prevEma * (1 - k12);
    if (i > 1) {
      const prevPrevEma = closes[i - 1] * k12 + (i > 1 ? closes[i - 2] : closes[0]) * (1 - k12);
      const jump = Math.abs(prevEma - prevPrevEma) / prevPrevEma;
      if (jump > 0.10) { emaJumpDetected = true; break; }
    }
  }
  if (emaJumpDetected) {
    checks.push({ name: "EMA Jump", value: 0, valid: false, error: "EMA jumped > 10% in one step (possible bad data)" });
  }

  const allValid = checks.every((c) => c.valid);

  return { allValid, checks, nanCount, infinityCount, undefinedCount };
}
