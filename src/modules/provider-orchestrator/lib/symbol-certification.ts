/**
 * Symbol-Level Certification — stores certification at the granularity of
 * Provider → Symbol → Timeframe → Session.
 *
 * This lets ATHENA-X make routing decisions at a much finer granularity
 * instead of treating a provider as uniformly good or bad.
 *
 * Example: Yahoo might be certified for SPY@1m during RTH but
 * NOT certified for ES=F@1m during premarket. The router can use
 * this to pick the best provider per request.
 */

import type { DataCategory } from "./types";
import type { SessionStatus } from "./market-sessions";

export type SessionType = "RTH" | "premarket" | "after_hours" | "overnight" | "closed" | "weekend" | "holiday";

export interface SymbolCertification {
  provider: string;
  symbol: string;
  timeframe: string;
  session: SessionType;

  // Metrics for this specific combination
  totalRequests: number;
  successes: number;
  failures: number;
  expectedEmpty: number;
  certRelevantFailures: number;
  successRate: number;           // excludes expected empty
  integrityRate: number;         // valid bars / total bars
  continuityRate: number;        // candle continuity
  indicatorValidRate: number;    // indicators valid / indicators computed
  avgLatencyMs: number;
  http429Count: number;
  http403Count: number;

  // Certification status for this specific combination
  status: "certified" | "conditional" | "not_certified" | "pending";
  lastUpdated: number;
  evidence: {
    lastSuccess: number | null;
    lastFailure: number | null;
    lastError: string | null;
    totalBarsValidated: number;
    totalInvalidBars: number;
  };
}

// In-memory store — keyed by `${provider}:${symbol}:${timeframe}:${session}`
const store = new Map<string, SymbolCertification>();

function certKey(provider: string, symbol: string, timeframe: string, session: SessionType): string {
  return `${provider}:${symbol}:${timeframe}:${session}`;
}

/** Record a result for a specific provider/symbol/timeframe/session combination */
export function recordSymbolResult(
  provider: string,
  symbol: string,
  timeframe: string,
  session: SessionType,
  result: {
    success: boolean;
    expectedEmpty: boolean;
    certRelevant: boolean;
    barsValid: number;
    barsInvalid: number;
    continuityRate: number;
    indicatorsValid: boolean;
    latencyMs: number;
    http429: boolean;
    http403: boolean;
    error?: string;
  }
): void {
  const key = certKey(provider, symbol, timeframe, session);
  let cert = store.get(key);

  if (!cert) {
    cert = {
      provider, symbol, timeframe, session,
      totalRequests: 0, successes: 0, failures: 0, expectedEmpty: 0, certRelevantFailures: 0,
      successRate: 0, integrityRate: 0, continuityRate: 0, indicatorValidRate: 0,
      avgLatencyMs: 0, http429Count: 0, http403Count: 0,
      status: "pending", lastUpdated: Date.now(),
      evidence: { lastSuccess: null, lastFailure: null, lastError: null, totalBarsValidated: 0, totalInvalidBars: 0 },
    };
    store.set(key, cert);
  }

  cert.totalRequests++;
  cert.lastUpdated = Date.now();

  if (result.success) {
    cert.successes++;
    cert.evidence.lastSuccess = Date.now();
  } else if (result.expectedEmpty) {
    cert.expectedEmpty++;
  } else {
    cert.failures++;
    cert.evidence.lastFailure = Date.now();
    cert.evidence.lastError = result.error ?? null;
  }

  if (result.certRelevant && !result.success) {
    cert.certRelevantFailures++;
  }

  if (result.http429) cert.http429Count++;
  if (result.http403) cert.http403Count++;

  // Running averages
  cert.avgLatencyMs = cert.avgLatencyMs === 0
    ? result.latencyMs
    : (cert.avgLatencyMs * (cert.totalRequests - 1) + result.latencyMs) / cert.totalRequests;

  // Data quality
  const totalBars = cert.evidence.totalBarsValidated + result.barsValid + result.barsInvalid;
  cert.evidence.totalBarsValidated += result.barsValid;
  cert.evidence.totalInvalidBars += result.barsInvalid;
  cert.integrityRate = totalBars > 0 ? (cert.evidence.totalBarsValidated) / totalBars : 1;

  // Continuity (running average)
  cert.continuityRate = cert.continuityRate === 0
    ? result.continuityRate
    : (cert.continuityRate * (cert.totalRequests - 1) + result.continuityRate) / cert.totalRequests;

  // Indicator validity
  const indicatorRate = result.indicatorsValid ? 1 : 0;
  cert.indicatorValidRate = cert.indicatorValidRate === 0
    ? indicatorRate
    : (cert.indicatorValidRate * (cert.totalRequests - 1) + indicatorRate) / cert.totalRequests;

  // Success rate (excludes expected empty)
  const certRequests = cert.totalRequests - cert.expectedEmpty;
  cert.successRate = certRequests > 0 ? cert.successes / certRequests : 0;

  // Update certification status based on thresholds
  if (cert.totalRequests < 10) {
    cert.status = "pending";
  } else if (cert.successRate >= 0.98 && cert.integrityRate >= 0.99 && cert.continuityRate >= 0.999 && cert.http429Count === 0 && cert.http403Count === 0) {
    cert.status = "certified";
  } else if (cert.successRate >= 0.90) {
    cert.status = "conditional";
  } else {
    cert.status = "not_certified";
  }
}

/** Get certification for a specific combination */
export function getSymbolCertification(provider: string, symbol: string, timeframe: string, session: SessionType): SymbolCertification | null {
  return store.get(certKey(provider, symbol, timeframe, session)) ?? null;
}

/** Get all certifications for a provider */
export function getProviderCertifications(provider: string): SymbolCertification[] {
  return Array.from(store.values()).filter(c => c.provider === provider);
}

/** Get all certifications for a provider + symbol */
export function getSymbolCertifications(provider: string, symbol: string): SymbolCertification[] {
  return Array.from(store.values()).filter(c => c.provider === provider && c.symbol === symbol);
}

/** Get all certifications */
export function getAllSymbolCertifications(): SymbolCertification[] {
  return Array.from(store.values());
}

/** Determine the session type from a SessionStatus */
export function sessionTypeFromStatus(status: SessionStatus): SessionType {
  if (status.isHoliday) return "holiday";
  if (status.reason.includes("Weekend")) return "weekend";
  if (status.isOpen) {
    if (status.sessionName === "RTH") return "RTH";
    if (status.sessionName === "Futures") return "overnight";
    if (status.sessionName === "Forex") return "overnight";
    return "RTH";
  }
  return "closed";
}

/** Clear all symbol certifications */
export function clearSymbolCertifications(): void {
  store.clear();
}
