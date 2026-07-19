/**
 * Certification Evidence Report — structured audit trail that explains
 * exactly why a provider passed or failed each certification tier.
 *
 * This creates the evidence document that an institutional reviewer
 * would need to approve a provider for production use.
 */

import type { LoadTestMetrics, CertificationLevels } from "./load-validator";
import type { FailureTypeCounts } from "./failure-classifier";

export interface EvidenceReport {
  generatedAt: number;
  provider: string;
  testDuration: string;
  summary: {
    totalRequests: number;
    successes: number;
    failures: number;
    expectedEmpty: number;
    certRelevantFailures: number;
    successRate: number;
    certSuccessRate: number;    // excludes expected empty
    uniqueSymbolsCovered: number;
    uniqueSymbolsRequested: number;
    requestSuccessCount: number;
    requestTotalCount: number;
  };
  failureBreakdown: {
    type: string;
    count: number;
    countsAgainstCert: boolean;
  }[];
  httpErrors: {
    http429: number;
    http403: number;
    http5xx: number;
    connectionResets: number;
  };
  latency: {
    avg: number;
    peak: number;
    min: number;
    p95: number;
  };
  dataQuality: {
    totalBarsChecked: number;
    invalidBars: number;
    integrityRate: number;
    candleContinuityRate: number;
    missingCandles: number;
    unexpectedGaps: number;
    indicatorFailures: number;
    indicatorNotReady: number;
    nanCount: number;
    infinityCount: number;
  };
  cache: {
    hits: number;
    hitRate: number;
  };
  healthScore: {
    overall: number;
    availability: number;
    latency: number;
    integrity: number;
    stability: number;
    coverage: number;
  } | null;
  certification: {
    functional: { status: string; detail: string };
    integration: { status: string; detail: string };
    operational: { status: string; detail: string };
    production: { status: string; detail: string };
    overall: boolean;
  };
  perSymbolResults: {
    symbol: string;
    requests: number;
    successes: number;
    dataIntegrity: boolean;
    candleContinuity: number;
    indicatorsValid: boolean;
  }[];
}

export function generateEvidenceReport(
  metrics: LoadTestMetrics,
  certification: CertificationLevels,
  provider: string
): EvidenceReport {
  const ftc = metrics.failureTypeCounts;

  // Build failure breakdown
  const failureBreakdown = [
    { type: "valid_response", count: ftc.valid_response, countsAgainstCert: false },
    { type: "expected_empty", count: ftc.expected_empty, countsAgainstCert: false },
    { type: "timeout", count: ftc.timeout, countsAgainstCert: true },
    { type: "http_429", count: ftc.http_429, countsAgainstCert: true },
    { type: "http_403", count: ftc.http_403, countsAgainstCert: true },
    { type: "http_5xx", count: ftc.http_5xx, countsAgainstCert: true },
    { type: "connection_error", count: ftc.connection_error, countsAgainstCert: true },
    { type: "malformed_json", count: ftc.malformed_json, countsAgainstCert: true },
    { type: "invalid_ohlc", count: ftc.invalid_ohlc, countsAgainstCert: true },
    { type: "missing_candle", count: ftc.missing_candle, countsAgainstCert: true },
    { type: "duplicate_timestamp", count: ftc.duplicate_timestamp, countsAgainstCert: true },
  ].filter(f => f.count > 0);

  // Per-symbol results
  const symbols = new Set<string>([
    ...metrics.dataIntegrityResults.map(r => r.symbol),
    ...metrics.candleContinuityResults.map(r => r.symbol),
    ...metrics.indicatorIntegrityResults.map(r => r.symbol),
  ]);

  const perSymbolResults = Array.from(symbols).map(symbol => {
    const integrity = metrics.dataIntegrityResults.filter(r => r.symbol === symbol).pop();
    const continuity = metrics.candleContinuityResults.filter(r => r.symbol === symbol).pop();
    const indicators = metrics.indicatorIntegrityResults.filter(r => r.symbol === symbol).pop();
    return {
      symbol,
      requests: metrics.dataIntegrityResults.filter(r => r.symbol === symbol).length,
      successes: metrics.dataIntegrityResults.filter(r => r.symbol === symbol && r.valid).length,
      dataIntegrity: integrity?.valid ?? false,
      candleContinuity: continuity?.continuityRate ?? 0,
      indicatorsValid: indicators?.allValid ?? false,
    };
  });

  const durationMin = metrics.elapsedMs / 60_000;
  const durationStr = durationMin < 60
    ? `${durationMin.toFixed(1)} min`
    : `${(durationMin / 60).toFixed(1)} hours`;

  const totalBars = metrics.dataIntegrityResults.reduce((s, r) => s + r.totalBars, 0);
  const invalidBars = metrics.dataIntegrityResults.reduce((s, r) => s + r.invalidBars, 0);
  const avgContinuity = metrics.candleContinuityResults.length > 0
    ? metrics.candleContinuityResults.reduce((s, r) => s + r.continuityRate, 0) / metrics.candleContinuityResults.length
    : 1;
  const totalMissing = metrics.candleContinuityResults.reduce((s, r) => s + r.missingCandles, 0);
  const totalUnexpectedGaps = metrics.candleContinuityResults.reduce((s, r) => s + r.unexpectedGaps, 0);
  const indicatorFailures = metrics.indicatorIntegrityResults.filter(r => !r.allValid).length;
  const totalNaN = metrics.indicatorIntegrityResults.reduce((s, r) => s + r.nanCount, 0);
  const totalInf = metrics.indicatorIntegrityResults.reduce((s, r) => s + r.infinityCount, 0);

  return {
    generatedAt: Date.now(),
    provider,
    testDuration: durationStr,
    summary: {
      totalRequests: metrics.totalRequests,
      successes: metrics.totalSuccesses,
      failures: metrics.totalFailures,
      expectedEmpty: metrics.expectedEmptyCount,
      certRelevantFailures: metrics.certRelevantFailures,
      successRate: metrics.successRate,
      certSuccessRate: metrics.totalRequests > 0
        ? (metrics.totalRequests - metrics.certRelevantFailures) / metrics.totalRequests
        : 0,
      uniqueSymbolsCovered: metrics.uniqueSymbolsCovered,
      uniqueSymbolsRequested: metrics.uniqueSymbolsRequested,
      requestSuccessCount: metrics.requestSuccessCount,
      requestTotalCount: metrics.requestTotalCount,
    },
    failureBreakdown,
    httpErrors: {
      http429: metrics.http429Count,
      http403: metrics.http403Count,
      http5xx: metrics.http5xxCount,
      connectionResets: metrics.connectionResets,
    },
    latency: {
      avg: metrics.avgLatencyMs,
      peak: metrics.peakLatencyMs,
      min: metrics.minLatencyMs,
      p95: metrics.p95LatencyMs,
    },
    dataQuality: {
      totalBarsChecked: totalBars,
      invalidBars,
      integrityRate: totalBars > 0 ? (totalBars - invalidBars) / totalBars : 1,
      candleContinuityRate: avgContinuity,
      missingCandles: totalMissing,
      unexpectedGaps: totalUnexpectedGaps,
      indicatorFailures,
      indicatorNotReady: 0,
      nanCount: totalNaN,
      infinityCount: totalInf,
    },
    cache: {
      hits: metrics.cacheHits,
      hitRate: metrics.cacheHitRate,
    },
    healthScore: metrics.healthScore,
    certification: {
      functional: { status: certification.functional.status, detail: certification.functional.detail },
      integration: { status: certification.integration.status, detail: certification.integration.detail },
      operational: { status: certification.operational.status, detail: certification.operational.detail },
      production: { status: certification.production.status, detail: certification.production.detail },
      overall: certification.overallCertified,
    },
    perSymbolResults,
  };
}
