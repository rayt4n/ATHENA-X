"use client";

import { useEffect, useState, useCallback } from "react";
import { Zap, Play, Square, Clock, Activity, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { LoadTestMetrics, CertificationLevels, LoadTestConfig } from "../lib/load-validator";

interface LoadTestResponse {
  isRunning: boolean;
  config: LoadTestConfig | null;
  metrics: LoadTestMetrics | null;
  certification: CertificationLevels | null;
}

export function LoadValidation() {
  const [data, setData] = useState<LoadTestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [duration, setDuration] = useState(5); // default 5 min for quick test

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/providers/load-test");
      const d = await res.json();
      setData(d);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, [refresh]);

  const startTest = async () => {
    setLoading(true);
    try {
      await fetch("/api/providers/load-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ durationMin: duration }),
      });
      await refresh();
    } finally {
      setLoading(false);
    }
  };

  const stopTest = async () => {
    setLoading(true);
    try {
      await fetch("/api/providers/load-test", { method: "DELETE" });
      await refresh();
    } finally {
      setLoading(false);
    }
  };

  const metrics = data?.metrics;
  const cert = data?.certification;
  const isRunning = data?.isRunning ?? false;

  return (
    <div className="space-y-4">
      {/* Control panel */}
      <div className="rounded-lg border border-border bg-card/40 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="h-3.5 w-3.5 text-primary" />
          <h2 className="text-[13px] font-semibold uppercase tracking-wide">System Load & Scheduler Validation</h2>
        </div>
        <p className="text-[11px] text-muted-foreground mb-4">
          Tests whether ATHENA-X can run continuously against Yahoo Finance without triggering rate limits or IP blocks.
          This is NOT testing the adapter — it&apos;s testing whether the request pattern is sustainable.
        </p>

        <div className="flex items-center gap-3 mb-4">
          {!isRunning ? (
            <>
              <label className="text-[10px] font-mono text-muted-foreground">Duration:</label>
              <select value={duration} onChange={(e) => setDuration(parseInt(e.target.value))} className="bg-background/60 border border-border/40 rounded px-2 py-1 text-[11px] font-mono">
                <option value={1}>1 min (quick)</option>
                <option value={5}>5 min</option>
                <option value={15}>15 min</option>
                <option value={60}>1 hour</option>
                <option value={240}>4 hours</option>
                <option value={1440}>24 hours (full)</option>
              </select>
              <button onClick={startTest} disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-primary text-primary-foreground text-[11px] font-medium hover:bg-primary/90 disabled:opacity-50">
                <Play className="h-3 w-3" /> Start Load Test
              </button>
            </>
          ) : (
            <button onClick={stopTest} disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-status-critical text-white text-[11px] font-medium hover:bg-status-critical/90 disabled:opacity-50">
              <Square className="h-3 w-3" /> Stop Test
            </button>
          )}
          {isRunning && (
            <span className="flex items-center gap-1.5 text-[10px] font-mono text-status-info">
              <span className="w-2 h-2 rounded-full bg-status-info pulse-live" />
              RUNNING — {data?.config?.symbols.length ?? 0} symbols · every {((data?.config?.intervalMs ?? 0) / 1000)}s
            </span>
          )}
        </div>

        {/* Test configuration */}
        {data?.config && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] font-mono">
            <div className="rounded border border-border/40 bg-background/30 p-2">
              <div className="text-muted-foreground/60 text-[8px] uppercase">Symbols</div>
              <div>{data.config.symbols.join(", ")}</div>
            </div>
            <div className="rounded border border-border/40 bg-background/30 p-2">
              <div className="text-muted-foreground/60 text-[8px] uppercase">Interval</div>
              <div>{data.config.intervalMs / 1000}s</div>
            </div>
            <div className="rounded border border-border/40 bg-background/30 p-2">
              <div className="text-muted-foreground/60 text-[8px] uppercase">Duration</div>
              <div>{data.config.durationMin}min</div>
            </div>
            <div className="rounded border border-border/40 bg-background/30 p-2">
              <div className="text-muted-foreground/60 text-[8px] uppercase">Provider</div>
              <div>{data.config.providerId}</div>
            </div>
          </div>
        )}
      </div>

      {/* Live metrics */}
      {metrics && (
        <div className="rounded-lg border border-border bg-card/40 p-4">
          <h3 className="text-[12px] font-semibold uppercase tracking-wide mb-3">Live Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <Metric label="Total Requests" value={metrics.totalRequests} intent="info" />
            <Metric label="Success Rate" value={`${(metrics.successRate * 100).toFixed(1)}%`} intent={metrics.successRate > 0.95 ? "healthy" : "warning"} />
            <Metric label="Failures" value={metrics.totalFailures} intent={metrics.totalFailures > 0 ? "critical" : "healthy"} />
            <Metric label="Avg Latency" value={`${metrics.avgLatencyMs.toFixed(0)}ms`} intent={metrics.avgLatencyMs < 300 ? "healthy" : "warning"} />
            <Metric label="Peak Latency" value={`${metrics.peakLatencyMs}ms`} intent={metrics.peakLatencyMs < 1000 ? "healthy" : "warning"} />
            <Metric label="p95 Latency" value={`${metrics.p95LatencyMs}ms`} intent={metrics.p95LatencyMs < 500 ? "healthy" : "warning"} />
            <Metric label="Req/min" value={metrics.requestsPerMinute.toFixed(1)} intent="info" />
            <Metric label="Req/hour" value={metrics.requestsPerHour.toFixed(0)} intent="info" />
            <Metric label="Cache Hit Rate" value={`${(metrics.cacheHitRate * 100).toFixed(0)}%`} intent={metrics.cacheHitRate > 0.3 ? "healthy" : "warning"} />
            <Metric label="HTTP 429" value={metrics.http429Count} intent={metrics.http429Count > 0 ? "critical" : "healthy"} />
            <Metric label="HTTP 403" value={metrics.http403Count} intent={metrics.http403Count > 0 ? "critical" : "healthy"} />
            <Metric label="Empty Payloads" value={metrics.emptyPayloads} intent={metrics.emptyPayloads > 10 ? "warning" : "healthy"} />
            <Metric label="Conn Resets" value={metrics.connectionResets} intent={metrics.connectionResets > 0 ? "warning" : "healthy"} />
            <Metric label="Duplicates" value={metrics.duplicateResponses} intent={metrics.duplicateResponses > 0 ? "warning" : "healthy"} />
            <Metric label="Elapsed" value={`${(metrics.elapsedMs / 60000).toFixed(1)}min`} intent="info" />
            <Metric label="5xx Errors" value={metrics.http5xxCount} intent={metrics.http5xxCount > 0 ? "warning" : "healthy"} />
          </div>

          {/* Error log */}
          {metrics.errorHistory.length > 0 && (
            <div className="mt-4">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70 mb-2">Recent Errors ({metrics.errorHistory.length})</div>
              <div className="max-h-32 overflow-y-auto scroll-thin rounded border border-border/40 bg-background/30">
                {metrics.errorHistory.slice(0, 20).map((err, i) => (
                  <div key={i} className="px-2 py-1 text-[9.5px] font-mono border-b border-border/10 flex items-center gap-2">
                    <span className="text-muted-foreground/60">{new Date(err.t).toLocaleTimeString("en-US", { hour12: false })}</span>
                    <span className="text-status-critical">{err.status}</span>
                    <span className="text-muted-foreground">{err.symbol}</span>
                    <span className="text-muted-foreground/80 truncate">{err.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3-Tier Certification */}
      {cert && (
        <div className="rounded-lg border border-border bg-card/40 p-4">
          <h3 className="text-[12px] font-semibold uppercase tracking-wide mb-3">3-Tier Certification</h3>
          <div className="space-y-3">
            {/* Functional */}
            <CertRow level="Functional" status={cert.functional.status} detail={cert.functional.detail}
              checks={[
                { label: "Adapter connects", passed: cert.functional.adapterConnects },
                { label: "Normalizer valid", passed: cert.functional.normalizerValid },
                { label: "Indicators valid", passed: cert.functional.indicatorsValid },
              ]}
            />

            {/* Operational */}
            <CertRow level="Operational" status={cert.operational.status} detail={cert.operational.detail}
              checks={[
                { label: `Success rate ≥ 95% (${(cert.operational.successRate * 100).toFixed(1)}%)`, passed: cert.operational.successRate >= 0.95 },
                { label: `HTTP 429 ≤ 5 (${cert.operational.http429Count})`, passed: cert.operational.http429Count <= 5 },
                { label: `HTTP 403 = 0 (${cert.operational.http403Count})`, passed: cert.operational.http403Count === 0 },
                { label: `Avg latency < 500ms (${cert.operational.avgLatencyMs.toFixed(0)}ms)`, passed: cert.operational.avgLatencyMs <= 500 },
                { label: `Cache hit rate ≥ 30% (${(cert.operational.cacheHitRate * 100).toFixed(0)}%)`, passed: cert.operational.cacheHitRate >= 0.30 },
              ]}
            />

            {/* Production */}
            <CertRow level="Production" status={cert.production.status} detail={cert.production.detail}
              checks={[
                { label: `Success rate ≥ 99% (${(cert.production.successRate * 100).toFixed(1)}%)`, passed: cert.production.successRate >= 0.99 },
                { label: `HTTP 429 = 0 (${cert.production.http429Count})`, passed: cert.production.http429Count === 0 },
                { label: `HTTP 403 = 0 (${cert.production.http403Count})`, passed: cert.production.http403Count === 0 },
                { label: `Duration ≥ 24h (${cert.production.durationHours.toFixed(1)}h)`, passed: cert.production.durationHours >= 24 },
                { label: `Avg latency < 300ms (${cert.production.avgLatencyMs.toFixed(0)}ms)`, passed: cert.production.avgLatencyMs <= 300 },
              ]}
            />

            {/* Overall */}
            <div className="rounded-md border-2 p-3 text-center" style={{
              borderColor: cert.overallCertified ? "rgba(52,211,153,0.4)" : "rgba(139,148,158,0.3)",
              backgroundColor: cert.overallCertified ? "rgba(52,211,153,0.05)" : "transparent",
            }}>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Overall Certification</div>
              <div className="text-[20px] font-bold mt-1" style={{ color: cert.overallCertified ? "#34d399" : "#8b949e" }}>
                {cert.overallCertified ? "✓ CERTIFIED" : "NOT CERTIFIED"}
              </div>
              <div className="text-[10px] font-mono text-muted-foreground mt-1">
                {cert.overallCertified
                  ? "Yahoo Finance is certified for production use"
                  : "Pending — Functional passed, Operational and Production require load test validation"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No data state */}
      {!metrics && (
        <div className="rounded-lg border border-border bg-card/40 p-8 text-center">
          <Activity className="h-10 w-10 mx-auto mb-3 text-muted-foreground/20" />
          <div className="text-[12px] text-muted-foreground/70 font-mono">No load test data yet. Start a test above.</div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, intent }: { label: string; value: string | number; intent: "healthy" | "warning" | "critical" | "info" }) {
  const color = intent === "healthy" ? "#34d399" : intent === "warning" ? "#fbbf24" : intent === "critical" ? "#f87171" : "#22d3ee";
  return (
    <div className="rounded-md border border-border/40 bg-background/30 p-2">
      <div className="text-[8.5px] uppercase tracking-wider text-muted-foreground/70">{label}</div>
      <div className="text-[16px] font-mono font-bold tabular-nums mt-0.5" style={{ color }}>{value}</div>
    </div>
  );
}

function CertRow({ level, status, detail, checks }: {
  level: string;
  status: "pass" | "fail" | "pending";
  detail: string;
  checks: { label: string; passed: boolean }[];
}) {
  const color = status === "pass" ? "#34d399" : status === "fail" ? "#f87171" : "#94a3b8";
  const icon = status === "pass" ? <CheckCircle2 className="h-4 w-4" /> : status === "fail" ? <XCircle className="h-4 w-4" /> : <Clock className="h-4 w-4" />;
  return (
    <div className="rounded-md border p-3" style={{ borderColor: `${color}33`, backgroundColor: `${color}08` }}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span style={{ color }}>{icon}</span>
          <span className="text-[12px] font-semibold">{level} Certification</span>
        </div>
        <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded" style={{ color, backgroundColor: `${color}22` }}>
          {status}
        </span>
      </div>
      <div className="text-[10px] text-muted-foreground mb-2">{detail}</div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
        {checks.map((c, i) => (
          <div key={i} className="flex items-center gap-1.5 text-[10px] font-mono">
            {c.passed ? <CheckCircle2 className="h-2.5 w-2.5" style={{ color: "#34d399" }} /> : <XCircle className="h-2.5 w-2.5" style={{ color: status === "pending" ? "#6b7280" : "#f87171" }} />}
            <span className={c.passed ? "text-foreground" : "text-muted-foreground"}>{c.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
