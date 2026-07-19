/**
 * Normalizer — validates and normalizes MarketData output.
 *
 * Ensures every provider's output conforms to the unified model
 * before it reaches the rest of ATHENA-X.
 */

import type { MarketData } from "./types";

/** Validate a MarketData object is well-formed */
export function validateMarketData(data: MarketData): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!data.symbol || typeof data.symbol !== "string") errors.push("Missing or invalid symbol");
  if (!data.timestamp || data.timestamp <= 0) errors.push("Missing or invalid timestamp");
  if (typeof data.open !== "number" || data.open < 0) errors.push("Missing or invalid open");
  if (typeof data.high !== "number" || data.high < 0) errors.push("Missing or invalid high");
  if (typeof data.low !== "number" || data.low < 0) errors.push("Missing or invalid low");
  if (typeof data.close !== "number" || data.close < 0) errors.push("Missing or invalid close");
  if (typeof data.volume !== "number" || data.volume < 0) errors.push("Missing or invalid volume");
  if (!data.provider || typeof data.provider !== "string") errors.push("Missing or invalid provider");
  if (typeof data.qualityScore !== "number" || data.qualityScore < 0 || data.qualityScore > 1) errors.push("Missing or invalid qualityScore");

  // Sanity: high >= max(open, close) and low <= min(open, close)
  if (data.high < Math.max(data.open, data.close)) errors.push("High is less than open or close");
  if (data.low > Math.min(data.open, data.close)) errors.push("Low is greater than open or close");

  return { valid: errors.length === 0, errors };
}

/** Filter out invalid MarketData entries from an array */
export function filterValid(data: MarketData[]): MarketData[] {
  return data.filter((d) => validateMarketData(d).valid);
}

/** Sort MarketData by timestamp ascending */
export function sortByTime(data: MarketData[]): MarketData[] {
  return [...data].sort((a, b) => a.timestamp - b.timestamp);
}

/** Deduplicate MarketData entries (same symbol + timestamp) */
export function deduplicate(data: MarketData[]): MarketData[] {
  const seen = new Set<string>();
  return data.filter((d) => {
    const key = `${d.symbol}:${d.timestamp}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/** Full normalization pipeline: validate → deduplicate → sort */
export function normalize(data: MarketData[]): MarketData[] {
  return sortByTime(deduplicate(filterValid(data)));
}
