/**
 * Data Integrity Validator — checks every candle for correctness.
 *
 * A response can be HTTP 200 and still contain bad data.
 * This module rejects invalid data before it reaches indicators.
 */

import type { MarketData } from "./types";

export interface IntegrityCheckResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  invalidBars: number;
  totalBars: number;
}

export function checkOHLC(bar: MarketData): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // High >= Low
  if (bar.high < bar.low) errors.push(`High (${bar.high}) < Low (${bar.low})`);

  // Open within High/Low range
  if (bar.open > bar.high) errors.push(`Open (${bar.open}) > High (${bar.high})`);
  if (bar.open < bar.low) errors.push(`Open (${bar.open}) < Low (${bar.low})`);

  // Close within High/Low range
  if (bar.close > bar.high) errors.push(`Close (${bar.close}) > High (${bar.high})`);
  if (bar.close < bar.low) errors.push(`Close (${bar.close}) < Low (${bar.low})`);

  // All prices positive
  if (bar.open <= 0) errors.push(`Open (${bar.open}) not positive`);
  if (bar.high <= 0) errors.push(`High (${bar.high}) not positive`);
  if (bar.low <= 0) errors.push(`Low (${bar.low}) not positive`);
  if (bar.close <= 0) errors.push(`Close (${bar.close}) not positive`);

  // Volume non-negative
  if (bar.volume < 0) errors.push(`Volume (${bar.volume}) negative`);

  return { valid: errors.length === 0, errors };
}

export function checkDataIntegrity(data: MarketData[]): IntegrityCheckResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  let invalidBars = 0;

  for (let i = 0; i < data.length; i++) {
    const bar = data[i];

    // OHLC sanity
    const ohlc = checkOHLC(bar);
    if (!ohlc.valid) {
      invalidBars++;
      errors.push(`Bar ${i} (${new Date(bar.timestamp).toISOString()}): ${ohlc.errors.join("; ")}`);
    }

    // NaN/Infinity check
    for (const field of ["open", "high", "low", "close", "volume"] as const) {
      const val = bar[field];
      if (Number.isNaN(val)) {
        invalidBars++;
        errors.push(`Bar ${i}: ${field} is NaN`);
      }
      if (!Number.isFinite(val)) {
        invalidBars++;
        errors.push(`Bar ${i}: ${field} is Infinity`);
      }
    }

    // Timestamp checks
    if (bar.timestamp <= 0) {
      invalidBars++;
      errors.push(`Bar ${i}: timestamp invalid (${bar.timestamp})`);
    }

    // Timestamp ordering (must be ascending)
    if (i > 0 && bar.timestamp < data[i - 1].timestamp) {
      warnings.push(`Bar ${i}: timestamp out of order (${bar.timestamp} < ${data[i-1].timestamp})`);
    }

    // Duplicate timestamp
    if (i > 0 && bar.timestamp === data[i - 1].timestamp) {
      errors.push(`Bar ${i}: duplicate timestamp (${bar.timestamp})`);
      invalidBars++;
    }
  }

  return {
    valid: errors.length === 0,
    errors: errors.slice(0, 50),  // cap for display
    warnings: warnings.slice(0, 20),
    invalidBars,
    totalBars: data.length,
  };
}

// ---------- Candle Continuity ----------
export interface ContinuityResult {
  expectedGaps: number;     // gaps during expected closed periods
  unexpectedGaps: number;  // gaps when market should be open
  totalCandles: number;
  missingCandles: number;
  continuityRate: number;  // (total - unexpectedMissing) / total
  gaps: { from: number; to: number; expectedMissing: number; unexpectedMissing: number }[];
}

export function checkCandleContinuity(
  data: MarketData[],
  intervalMs: number,
  marketOpenIntervals: Set<number> = new Set()
): ContinuityResult {
  const gaps: ContinuityResult["gaps"] = [];
  let unexpectedGaps = 0;
  let expectedGaps = 0;
  let totalMissing = 0;

  for (let i = 1; i < data.length; i++) {
    const expectedDiff = intervalMs;
    const actualDiff = data[i].timestamp - data[i - 1].timestamp;

    if (actualDiff > expectedDiff) {
      const missingCount = Math.round(actualDiff / expectedDiff) - 1;
      totalMissing += missingCount;

      // Check if the gap period was during market hours
      const gapStart = data[i - 1].timestamp + expectedDiff;
      let unexpected = 0;
      let expected = 0;

      for (let j = 0; j < missingCount; j++) {
        const missingTs = gapStart + j * expectedMs(expectedDiff);
        if (marketOpenIntervals.has(missingTs)) {
          unexpected++;
        } else {
          expected++;
        }
      }

      unexpectedGaps += unexpected;
      expectedGaps += expected;

      gaps.push({
        from: data[i - 1].timestamp,
        to: data[i].timestamp,
        expectedMissing: expected,
        unexpectedMissing: unexpected,
      });
    }
  }

  const totalCandles = data.length;
  const continuityRate = totalCandles + totalMissing > 0
    ? (totalCandles) / (totalCandles + unexpectedGaps)
    : 1;

  return {
    expectedGaps,
    unexpectedGaps,
    totalCandles,
    missingCandles: totalMissing,
    continuityRate: Math.min(1, Math.max(0, continuityRate)),
    gaps: gaps.slice(0, 20),
  };
}

function expectedMs(intervalMs: number): number {
  return intervalMs;
}
