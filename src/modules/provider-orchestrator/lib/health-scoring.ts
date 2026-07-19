/**
 * Provider Health Scoring — composite 0-100 score across 5 dimensions.
 *
 * Allows ATHENA-X to compare providers objectively.
 */

export interface HealthScore {
  overall: number;          // 0-100
  availability: number;     // 0-100 (success rate)
  latency: number;          // 0-100 (lower latency = higher score)
  integrity: number;        // 0-100 (valid OHLC bars / total bars)
  stability: number;        // 0-100 (1 - failure rate over time)
  coverage: number;         // 0-100 (symbols supported / symbols requested)
  detail: string;
}

export function calculateHealthScore(opts: {
  successRate: number;        // 0..1
  avgLatencyMs: number;
  totalBars: number;
  invalidBars: number;
  totalRequests: number;
  totalFailures: number;
  symbolsSupported: number;
  symbolsRequested: number;
}): HealthScore {
  // Availability: success rate * 100
  const availability = Math.round(opts.successRate * 100);

  // Latency: 100 at 0ms, 0 at 2000ms, linear
  const latency = Math.round(Math.max(0, 100 - (opts.avgLatencyMs / 2000) * 100));

  // Integrity: valid bars / total bars
  const integrity = opts.totalBars > 0
    ? Math.round(((opts.totalBars - opts.invalidBars) / opts.totalBars) * 100)
    : 100;

  // Stability: 1 - failure rate
  const stability = opts.totalRequests > 0
    ? Math.round((1 - (opts.totalFailures / opts.totalRequests)) * 100)
    : 100;

  // Coverage: unique symbols that returned data / symbols requested
  // Clamp to 0-100 to prevent scores above 100
  const coverage = opts.symbolsRequested > 0
    ? Math.min(100, Math.round((Math.min(opts.symbolsSupported, opts.symbolsRequested) / opts.symbolsRequested) * 100))
    : 100;

  // Overall: weighted average — clamp to 0-100
  const overall = Math.min(100, Math.max(0, Math.round(
    availability * 0.30 +
    latency * 0.20 +
    integrity * 0.25 +
    stability * 0.15 +
    coverage * 0.10
  )));

  // Clamp all components to 0-100
  const clampedAvailability = Math.min(100, Math.max(0, availability));
  const clampedLatency = Math.min(100, Math.max(0, latency));
  const clampedIntegrity = Math.min(100, Math.max(0, integrity));
  const clampedStability = Math.min(100, Math.max(0, stability));
  const clampedCoverage = Math.min(100, Math.max(0, coverage));

  const detail = `Avail ${clampedAvailability} · Lat ${clampedLatency} · Integ ${clampedIntegrity} · Stab ${clampedStability} · Cov ${clampedCoverage}`;

  return { overall, availability: clampedAvailability, latency: clampedLatency, integrity: clampedIntegrity, stability: clampedStability, coverage: clampedCoverage, detail };
}

// ---------- Long-Term Stability Metrics ----------
export interface StabilityMetrics {
  maxUptimeHours: number;       // longest continuous uptime
  mtbfHours: number;            // mean time between failures
  mttrMinutes: number;          // mean time to recovery
  memoryGrowthMb: number;       // memory growth over observation period
  cacheGrowthEntries: number;   // cache entries growth
  cpuAvgPct: number;            // average CPU usage
  connectionLeaks: number;      // detected connection leaks
  observationHours: number;     // total observation period
}

export function createEmptyStabilityMetrics(): StabilityMetrics {
  return {
    maxUptimeHours: 0,
    mtbfHours: 0,
    mttrMinutes: 0,
    memoryGrowthMb: 0,
    cacheGrowthEntries: 0,
    cpuAvgPct: 0,
    connectionLeaks: 0,
    observationHours: 0,
  };
}

// ---------- Provider Failover Testing ----------
export interface FailoverTestResult {
  scenario: string;
  primaryProvider: string;
  backupProvider: string;
  primaryTimedOut: boolean;
  failoverTriggered: boolean;
  failoverTimeMs: number;
  backupReturnedData: boolean;
  priceDifference: number | null;
  timestampDeltaMs: number | null;
  recoveryTimeMs: number;
  passed: boolean;
  detail: string;
}
