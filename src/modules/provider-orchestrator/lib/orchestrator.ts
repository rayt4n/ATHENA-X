/**
 * Provider Orchestrator — top-level coordinator.
 *
 * Coordinates the registry, router, health monitor, cache, and normalizer
 * to provide a single `fetch()` method that the rest of ATHENA-X calls.
 *
 * The rest of ATHENA-X NEVER calls providers directly — it calls the
 * orchestrator's `fetch()` method and receives unified MarketData.
 */

import type { DataRequest, DataResponse, MarketData, ProviderConfig } from "./types";
import { getProviders, getRoutingRules, getMode } from "./registry";
import { getProviderOrder } from "./router";
import { recordSuccess, recordFailure, getHealth, getAllHealth, resetHealth } from "./health-monitor";
import { getCache, setCache, clearCache, getCacheStats } from "./cache";
import { normalize } from "./normalizer";
import { BaseProvider } from "./providers/base-provider";
import { MockProvider } from "./providers/mock";
import { YahooProvider } from "./providers/yahoo";
import type { RequestLogEntry, ComparisonEntry, ComparisonResult } from "./types";

// ---------- Provider adapter registry ----------
const adapters = new Map<string, BaseProvider>();

/** Register a provider adapter (called at module init) */
export function registerAdapter(adapter: BaseProvider): void {
  adapters.set(adapter.id, adapter);
}

/** Get a registered adapter */
function getAdapter(providerId: string): BaseProvider | null {
  return adapters.get(providerId) ?? null;
}

// ---------- Register built-in adapters ----------
// Phase 1: MockProvider for framework testing
// Phase 2: Yahoo Finance for live data validation
// Future: Finnhub, TwelveData, FMP, FRED (after Yahoo passes 24h monitoring)
registerAdapter(new MockProvider());
registerAdapter(new YahooProvider());

// ---------- Request log (in-memory, last 500 entries) ----------
const requestLog: RequestLogEntry[] = [];
const MAX_LOG_ENTRIES = 500;

function logRequest(entry: Omit<RequestLogEntry, "id">): void {
  requestLog.unshift({ ...entry, id: `req-${Date.now()}-${Math.random().toString(36).slice(2, 6)}` });
  if (requestLog.length > MAX_LOG_ENTRIES) requestLog.pop();
}

export function getRequestLog(): RequestLogEntry[] {
  return [...requestLog];
}

export function clearRequestLog(): void {
  requestLog.length = 0;
}

// ---------- Data comparison store ----------
const comparisonStore = new Map<string, ComparisonEntry[]>();

export function addComparisonEntry(entry: ComparisonEntry): void {
  const key = entry.symbol;
  if (!comparisonStore.has(key)) comparisonStore.set(key, []);
  const arr = comparisonStore.get(key)!;
  arr.push(entry);
  // Keep last 100 entries per symbol
  if (arr.length > 100) arr.shift();
}

export function getComparison(symbol: string): ComparisonResult | null {
  const entries = comparisonStore.get(symbol);
  if (!entries || entries.length < 2) return null;
  const prices = entries.map((e) => e.price);
  const timestamps = entries.map((e) => e.timestamp);
  return {
    symbol,
    entries: [...entries].slice(-20),
    maxDifference: Math.max(...prices) - Math.min(...prices),
    maxTimestampDeltaMs: Math.max(...timestamps) - Math.min(...timestamps),
  };
}

// ---------- Core fetch method ----------
/**
 * Fetch market data through the orchestrator.
 *
 * This is the ONLY method the rest of ATHENA-X should call.
 * It handles provider selection, failover, caching, and normalization.
 */
export async function fetch(request: DataRequest): Promise<DataResponse> {
  const startTime = Date.now();
  const providers = getProviders();
  const routingRules = getRoutingRules();
  const mode = getMode();

  // Get ordered list of providers to try
  const providerOrder = getProviderOrder(request, providers, routingRules, mode);

  // Try each provider in order
  for (const providerId of providerOrder) {
    // Check cache first
    if (providerId === "cache") {
      const cached = getCache(request.symbol, request.category);
      if (cached && cached.length > 0) {
        return {
          data: cached,
          provider: "cache",
          fromCache: true,
          qualityScore: 0.50,
          responseTimeMs: Date.now() - startTime,
        };
      }
      continue;
    }

    // Try the provider adapter
    const adapter = getAdapter(providerId);
    if (!adapter) {
      recordFailure(providerId, "No adapter registered");
      continue;
    }

    const config = providers.find((p) => p.id === providerId);
    if (!config) {
      recordFailure(providerId, "Provider not in registry");
      continue;
    }

    try {
      const raw = await adapter.fetch(request, config.apiKey);
      let normalized = adapter.normalize(raw, request.symbol);
      normalized = normalize(normalized);

      if (normalized.length > 0) {
        const latency = Date.now() - startTime;
        recordSuccess(providerId, latency);

        // Log successful request
        logRequest({
          timestamp: Date.now(), provider: providerId, symbol: request.symbol,
          category: request.category, status: "success", latencyMs: latency, fromCache: false,
        });

        // Add to comparison store
        const lastBar = normalized[normalized.length - 1];
        addComparisonEntry({
          symbol: request.symbol, timestamp: lastBar.timestamp, provider: providerId,
          price: lastBar.close, qualityScore: config.qualityScore,
        });

        // Cache the result
        setCache(request.symbol, request.category, normalized);

        return {
          data: normalized,
          provider: providerId,
          fromCache: false,
          qualityScore: config.qualityScore,
          responseTimeMs: latency,
        };
      } else {
        recordFailure(providerId, "No data returned");
        logRequest({
          timestamp: Date.now(), provider: providerId, symbol: request.symbol,
          category: request.category, status: "failed", latencyMs: Date.now() - startTime,
          errorMessage: "No data returned", fromCache: false,
        });
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      recordFailure(providerId, errorMsg);
      logRequest({
        timestamp: Date.now(), provider: providerId, symbol: request.symbol,
        category: request.category, status: "failed", latencyMs: Date.now() - startTime,
        errorMessage: errorMsg, fromCache: false,
      });
    }
  }

  // All providers failed — try cache as last resort
  const cached = getCache(request.symbol, request.category);
  if (cached && cached.length > 0) {
    logRequest({
      timestamp: Date.now(), provider: "cache", symbol: request.symbol,
      category: request.category, status: "cache", latencyMs: Date.now() - startTime, fromCache: true,
    });
    return {
      data: cached,
      provider: "cache",
      fromCache: true,
      qualityScore: 0.50,
      responseTimeMs: Date.now() - startTime,
    };
  }

  // Complete failure
  return {
    data: [],
    provider: "none",
    fromCache: false,
    qualityScore: 0,
    responseTimeMs: Date.now() - startTime,
  };
}

// ---------- Health & status methods ----------
export function getOrchestratorHealth() {
  const providers = getProviders();
  return {
    snapshots: getAllHealth(providers),
    cache: getCacheStats(),
    mode: getMode(),
    providerCount: providers.length,
    activeProviders: providers.filter((p) => p.enabled && p.health !== "disconnected").length,
  };
}

export function getProviderHealth(providerId: string): import("./types").HealthSnapshot | null {
  const config = getProviders().find((p) => p.id === providerId);
  if (!config) return null;
  return getHealth(providerId, config);
}

export function resetOrchestrator(): void {
  resetHealth();
  clearCache();
}
