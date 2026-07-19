/**
 * Cache — in-memory cache for market data.
 * Acts as a last-resort fallback when all providers fail.
 */

import type { MarketData } from "./types";

interface CacheEntry {
  data: MarketData[];
  timestamp: number;
  ttl: number;
}

const cache = new Map<string, CacheEntry>();

function cacheKey(symbol: string, category: string): string {
  return `${symbol}:${category}`;
}

/** Store data in cache */
export function setCache(symbol: string, category: string, data: MarketData[], ttlMs: number = 300_000): void {
  cache.set(cacheKey(symbol, category), {
    data,
    timestamp: Date.now(),
    ttl: ttlMs,
  });
}

/** Retrieve data from cache. Returns null if expired or not found. */
export function getCache(symbol: string, category: string): MarketData[] | null {
  const entry = cache.get(cacheKey(symbol, category));
  if (!entry) return null;
  if (Date.now() - entry.timestamp > entry.ttl) {
    cache.delete(cacheKey(symbol, category));
    return null;
  }
  return entry.data;
}

/** Check if cache has fresh data */
export function hasCache(symbol: string, category: string): boolean {
  return getCache(symbol, category) !== null;
}

/** Clear all cached data */
export function clearCache(): void {
  cache.clear();
}

/** Get cache stats */
export function getCacheStats(): { entries: number; totalSize: number } {
  let totalSize = 0;
  cache.forEach((entry) => { totalSize += entry.data.length; });
  return { entries: cache.size, totalSize };
}
