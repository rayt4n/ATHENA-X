/**
 * Health Monitor — tracks provider health metrics.
 *
 * Monitors: connected/disconnected/degraded state, latency, heartbeat,
 * success/failure rates, rate limits, data freshness, reconnect count.
 */

import type { HealthSnapshot, HealthState, ProviderConfig } from "./types";

interface HealthRecord {
  providerId: string;
  state: HealthState;
  latencyMs: number;
  totalRequests: number;
  totalSuccesses: number;
  totalFailures: number;
  consecutiveFailures: number;
  lastHeartbeat: number;
  lastDataTimestamp: number;
  reconnectCount: number;
  rateLimitRemaining: number;
}

const records = new Map<string, HealthRecord>();

function ensureRecord(providerId: string): HealthRecord {
  if (!records.has(providerId)) {
    records.set(providerId, {
      providerId,
      state: "disconnected",
      latencyMs: 0,
      totalRequests: 0,
      totalSuccesses: 0,
      totalFailures: 0,
      consecutiveFailures: 0,
      lastHeartbeat: 0,
      lastDataTimestamp: 0,
      reconnectCount: 0,
      rateLimitRemaining: 0,
    });
  }
  return records.get(providerId)!;
}

/** Record a successful request */
export function recordSuccess(providerId: string, latencyMs: number, rateLimitRemaining?: number): void {
  const r = ensureRecord(providerId);
  r.totalRequests++;
  r.totalSuccesses++;
  r.consecutiveFailures = 0;
  r.latencyMs = latencyMs;
  r.lastHeartbeat = Date.now();
  r.lastDataTimestamp = Date.now();
  if (rateLimitRemaining !== undefined) r.rateLimitRemaining = rateLimitRemaining;
  r.state = r.latencyMs < 500 ? "connected" : "degraded";
}

/** Record a failed request */
export function recordFailure(providerId: string, _error: string): void {
  const r = ensureRecord(providerId);
  r.totalRequests++;
  r.totalFailures++;
  r.consecutiveFailures++;
  r.state = r.consecutiveFailures >= 3 ? "disconnected" : "degraded";
}

/** Record a heartbeat (provider is alive) */
export function recordHeartbeat(providerId: string): void {
  const r = ensureRecord(providerId);
  r.lastHeartbeat = Date.now();
  if (r.state === "disconnected") r.state = "connected";
}

/** Record a reconnect attempt */
export function recordReconnect(providerId: string): void {
  const r = ensureRecord(providerId);
  r.reconnectCount++;
  r.state = "warming";
}

/** Update rate limit remaining for a provider */
export function updateRateLimit(providerId: string, remaining: number): void {
  const r = ensureRecord(providerId);
  r.rateLimitRemaining = remaining;
}

/** Get health snapshot for a single provider */
export function getHealth(providerId: string, config: ProviderConfig): HealthSnapshot {
  const r = ensureRecord(providerId);
  const now = Date.now();
  const successRate = r.totalRequests > 0 ? r.totalSuccesses / r.totalRequests : 0;
  const failureRate = r.totalRequests > 0 ? r.totalFailures / r.totalRequests : 0;

  return {
    providerId,
    state: r.state,
    latencyMs: r.latencyMs,
    successRate,
    failureRate,
    rateLimitRemaining: r.rateLimitRemaining,
    rateLimitPerMin: config.rateLimitPerMin,
    heartbeatMs: r.lastHeartbeat > 0 ? now - r.lastHeartbeat : 0,
    reconnectCount: r.reconnectCount,
    lastDataTimestamp: r.lastDataTimestamp,
    dataFreshnessMs: r.lastDataTimestamp > 0 ? now - r.lastDataTimestamp : 0,
    consecutiveFailures: r.consecutiveFailures,
    totalRequests: r.totalRequests,
    totalSuccesses: r.totalSuccesses,
    totalFailures: r.totalFailures,
  };
}

/** Get health snapshots for all providers */
export function getAllHealth(providers: ProviderConfig[]): HealthSnapshot[] {
  return providers.map((p) => getHealth(p.id, p));
}

/** Check if a provider is healthy enough to route requests to */
export function isHealthy(providerId: string): boolean {
  const r = records.get(providerId);
  if (!r) return false;
  return r.state === "connected" || r.state === "warming" || providerId === "cache";
}

/** Reset all health records (used on mode change or restart) */
export function resetHealth(): void {
  records.clear();
}
