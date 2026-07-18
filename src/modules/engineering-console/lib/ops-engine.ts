/**
 * ATHENA-X Stage 15.5 — Platform Hardening & Operations Engine
 *
 * Generates realistic ops telemetry for the 9 operational subsystems.
 * In production these would be populated from real infrastructure:
 *   - OpenTelemetry traces
 *   - Structured JSON logs from the log shipper
 *   - Backup system webhooks
 *   - Health check endpoints
 *   - Chaos engineering framework results
 *   - Git-based config validator
 *   - Plugin registry integrity scanner
 *
 * For the internal validation cockpit they are simulated so the ops
 * dashboard is self-contained and exercises every code path.
 */

import type {
  BackupJob,
  ConfigFile,
  FailureScenario,
  FailureType,
  HealthCheck,
  HealthSubsystem,
  LogLevel,
  OpsTelemetry,
  OperationalReadinessReport,
  PluginCategory,
  PluginRecord,
  RestoreTest,
  StructuredLog,
  Trace,
  TraceSpan,
} from "./ops-types";

// ---------- Deterministic PRNG ----------
function mulberry32(seed: number) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rng = mulberry32(0x4f5053); // "OPS"
const rand = (min: number, max: number) => min + (max - min) * rng();
const randInt = (min: number, max: number) => Math.floor(rand(min, max + 1));
const pick = <T,>(arr: T[]): T => arr[randInt(0, arr.length - 1)];
const jitter = (base: number, pct: number) => base * (1 + (rng() - 0.5) * 2 * pct);

// ---------- Helpers ----------
const now = () => Date.now();
const rid = (prefix: string, n = 8) => `${prefix}-${Math.random().toString(36).slice(2, 2 + n)}`;
const hashLike = (n = 16) => Array.from({ length: n }, () => "0123456789abcdef"[randInt(0, 15)]).join("");

// ---------- 1. Trace generator ----------
const TRACE_TRIGGERS = [
  "market.tick.SPY",
  "market.tick.ES",
  "market.tick.QQQ",
  "options.chain.SPY",
  "options.flow.SPY",
  "news.article.benzinga",
  "macro.cpi.release",
  "agent.event.qualify",
  "report.generate.premarket",
  "report.generate.intraday",
  "api.request./reports",
  "api.request./certification-pdf",
];

const SPAN_TEMPLATES: { kind: TraceSpan["kind"]; module: string; name: (trigger: string) => string; durationMs: () => number }[] = [
  { kind: "provider", module: "data-collector", name: (t) => `fetch ${t.split(".")[1] ?? "data"}`, durationMs: () => rand(8, 80) },
  { kind: "validator", module: "validation-engine", name: () => "validate schema + cross-source", durationMs: () => rand(2, 15) },
  { kind: "normalizer", module: "normalization-pipeline", name: () => "normalize to canonical schema", durationMs: () => rand(1, 8) },
  { kind: "database", module: "db-write-lock", name: () => "write to canonical db", durationMs: () => rand(0.5, 4) },
  { kind: "event_bus", module: "event-bus", name: () => "publish event", durationMs: () => rand(0.2, 2) },
  { kind: "agent", module: "agent-runtime", name: () => "agent processes event", durationMs: () => rand(5, 60) },
  { kind: "dna", module: "dna-serializer", name: () => "update DNA object", durationMs: () => rand(8, 120) },
  { kind: "report", module: "report-engine", name: () => "compose report section", durationMs: () => rand(20, 200) },
  { kind: "api", module: "next-api", name: () => "http response", durationMs: () => rand(2, 40) },
];

function buildTrace(trigger: string): Trace {
  const traceId = rid("trace", 16);
  const startTime = now() - randInt(0, 60_000);
  const spans: TraceSpan[] = [];
  let parentSpanId: string | undefined;
  let currentTime = startTime;
  const hopCount = randInt(4, 9);

  for (let i = 0; i < hopCount && i < SPAN_TEMPLATES.length; i++) {
    const tpl = SPAN_TEMPLATES[i];
    const spanId = rid("span", 12);
    const durationMs = tpl.durationMs();
    const endTime = currentTime + durationMs;
    const statusRoll = rng();
    const status: TraceSpan["status"] = statusRoll > 0.97 ? "error" : statusRoll > 0.94 ? "timeout" : "ok";

    spans.push({
      id: spanId,
      traceId,
      parentSpanId,
      name: tpl.name(trigger),
      kind: tpl.kind,
      module: tpl.module,
      startTime: currentTime,
      endTime,
      durationMs,
      status,
      attributes: {
        trigger,
        hop: i,
        ...(tpl.kind === "provider" ? { source: pick(["polygon", "cboe", "benzinga", "fred"]) } : {}),
        ...(tpl.kind === "database" ? { schema: pick(["ohlcv", "options_chain", "events", "narratives"]) } : {}),
        ...(tpl.kind === "agent" ? { agent_id: pick(["ta.indicators", "opt.greeks", "fc.ensemble", "tr.qualify"]) } : {}),
        ...(tpl.kind === "dna" ? { dna_id: pick(["technical", "options", "market", "narrative", "forecast", "trade", "operations"]) } : {}),
      },
      events: status !== "ok"
        ? [{ time: endTime - 1, name: status === "error" ? "exception" : "deadline_exceeded", detail: "simulated for chaos test" }]
        : [],
    });

    parentSpanId = spanId;
    currentTime = endTime;
  }

  const endTime = currentTime;
  const anyError = spans.some((s) => s.status === "error");
  const anyTimeout = spans.some((s) => s.status === "timeout");
  const status: Trace["status"] = anyError ? "failed" : anyTimeout ? "partial" : "ok";

  return {
    id: traceId,
    rootSpanId: spans[0]?.id ?? traceId,
    spans,
    startTime,
    endTime,
    durationMs: endTime - startTime,
    status,
    trigger,
    hopCount: spans.length,
  };
}

function buildTraces(): Trace[] {
  return TRACE_TRIGGERS.slice(0, 12).map(buildTrace);
}

// ---------- 2 & 3. Structured logs ----------
const LOG_MODULES = [
  "data-collector", "validation-engine", "normalization-pipeline", "db-write-lock",
  "event-bus", "agent-runtime", "dna-serializer", "report-engine", "certification-engine",
  "next-api", "auth-gateway", "backup-manager", "health-monitor", "plugin-registry",
];

const LOG_MESSAGES: Record<LogLevel, string[]> = {
  DEBUG: [
    "cache miss — fetching from source",
    "span started",
    "span ended",
    "polling for new events",
    "heartbeat received",
    "config reloaded (no changes)",
  ],
  INFO: [
    "event published to bus",
    "agent processed event successfully",
    "DNA object updated",
    "report generated",
    "backup completed",
    "health check passed",
    "plugin integrity verified",
    "trace completed",
  ],
  WARN: [
    "provider latency above 1s — backing off",
    "agent CPU above 70% — throttling",
    "event bus backlog growing — 500+ events",
    "config drift detected — auto-reverting",
    "restore test took longer than expected",
    "log volume above baseline",
  ],
  ERROR: [
    "provider returned 5xx — failover engaged",
    "agent crashed — restarting",
    "database write failed — retrying",
    "plugin signature verification failed",
    "trace ended with error status",
    "WebSocket disconnected — reconnecting",
  ],
  FATAL: [
    "all providers down — entering degraded mode",
    "database unreachable — failing open",
    "event bus backlog exceeded limit — dropping events",
    "OOM kill detected — agent restarted",
  ],
};

function buildLog(level?: LogLevel, traceId?: string): StructuredLog {
  const lvl = level ?? (rng() < 0.7 ? "INFO" : rng() < 0.7 ? "DEBUG" : rng() < 0.7 ? "WARN" : rng() < 0.8 ? "ERROR" : "FATAL");
  const logModule = pick(LOG_MODULES);
  const message = pick(LOG_MESSAGES[lvl]);
  return {
    id: rid("log", 12),
    timestamp: now() - randInt(0, 30_000),
    level: lvl,
    module: logModule,
    message,
    correlationId: traceId ?? rid("corr", 8),
    traceId: traceId ?? (rng() < 0.6 ? rid("trace", 16) : undefined),
    spanId: rng() < 0.4 ? rid("span", 12) : undefined,
    userId: rng() < 0.3 ? "system" : undefined,
    sessionId: rng() < 0.3 ? rid("sess", 8) : undefined,
    fields: {
      ...(logModule === "data-collector" ? { source: pick(["polygon", "cboe", "benzinga"]) } : {}),
      ...(logModule === "db-write-lock" ? { schema: pick(["ohlcv", "options_chain", "events"]) } : {}),
      ...(logModule === "agent-runtime" ? { agent_id: pick(["ta.indicators", "opt.greeks", "fc.ensemble"]) } : {}),
      ...(lvl === "ERROR" || lvl === "FATAL" ? { retry_count: randInt(1, 3) } : {}),
      pid: randInt(1000, 9999),
    },
  };
}

function buildLogs(traces: Trace[]): StructuredLog[] {
  const logs: StructuredLog[] = [];
  // Some logs linked to traces
  for (const t of traces.slice(0, 6)) {
    for (const span of t.spans.slice(0, 3)) {
      logs.push({
        ...buildLog(span.status === "ok" ? "INFO" : span.status === "timeout" ? "WARN" : "ERROR", t.id),
        spanId: span.id,
        module: span.module,
        message: `${span.name} ${span.status === "ok" ? "completed" : span.status}`,
        timestamp: span.startTime,
        fields: { ...span.attributes, duration_ms: span.durationMs, kind: span.kind } as Record<string, string | number | boolean>,
      });
    }
  }
  // Plus ambient logs
  for (let i = 0; i < 80; i++) {
    logs.push(buildLog());
  }
  return logs.sort((a, b) => b.timestamp - a.timestamp);
}

// ---------- 4. Backups & restore ----------
const BACKUP_TARGETS = [
  "ohlcv", "options_chain", "options_flow", "greeks", "iv_surface",
  "trade_decisions", "forecasts", "events", "narratives", "indicators",
  "agents", "audit_log", "full_cluster",
];

function buildBackups(): { backups: BackupJob[]; restoreTests: RestoreTest[] } {
  const backups: BackupJob[] = [];
  const restoreTests: RestoreTest[] = [];

  for (const target of BACKUP_TARGETS) {
    // 3 historical backups per target
    for (let i = 0; i < 3; i++) {
      const startedAt = now() - (i + 1) * 6 * 3600_000 - randInt(0, 3600_000);
      const durationMs = randInt(30_000, 900_000);
      const completedAt = startedAt + durationMs;
      const status: BackupJob["status"] = i === 0 ? "verified" : i === 1 ? "completed" : pick(["completed", "verified", "expired"]);
      const isFull = target === "full_cluster";
      const type: BackupJob["type"] = isFull ? "full" : i === 0 ? "snapshot" : i === 1 ? "incremental" : "wal";

      backups.push({
        id: rid("bkp", 10),
        type,
        target,
        startedAt,
        completedAt,
        durationMs,
        sizeBytes: Math.floor(rand(50_000_000, 12_000_000_000)),
        status,
        location: `s3://athena-x-backups/${target}/${new Date(startedAt).toISOString().slice(0, 10)}/${type}-${startedAt}.bak`,
        hash: hashLike(32),
        restoreVerified: status === "verified",
        retentionDays: isFull ? 90 : 30,
      });

      // Restore test for the most recent verified backup
      if (i === 0 && status === "verified") {
        const restoreDurationMs = randInt(60_000, 1_800_000);
        const pass = rng() > 0.05;
        restoreTests.push({
          id: rid("rst", 10),
          backupId: backups[backups.length - 1].id,
          startedAt: completedAt + 3600_000,
          completedAt: completedAt + 3600_000 + restoreDurationMs,
          durationMs: restoreDurationMs,
          status: pass ? "pass" : "fail",
          sandbox: `sandbox-${target}-${randInt(1, 5)}`,
          rowsVerified: randInt(1000, 5_000_000),
          hashMatch: pass,
          findings: pass
            ? ["All rows present", "Hash matches source", "Indexes rebuilt", "Constraints valid"]
            : ["Hash mismatch on 3 rows", "Investigating source drift"],
        });
      }
    }
  }

  return { backups, restoreTests };
}

// ---------- 5. Health checks ----------
const HEALTH_DEFS: { subsystem: HealthSubsystem; name: string; target: () => { latency: number; errRate: number; status: HealthCheck["status"] } }[] = [
  {
    subsystem: "providers", name: "Market Data Providers",
    target: () => {
      const latency = rand(10, 200);
      const errRate = rng() < 0.85 ? rand(0, 0.02) : rand(0.05, 0.15);
      return { latency, errRate, status: errRate > 0.05 ? "degraded" : "healthy" };
    },
  },
  {
    subsystem: "agents", name: "AI Agent Runtime",
    target: () => {
      const latency = rand(5, 50);
      const errRate = rng() < 0.9 ? rand(0, 0.01) : rand(0.02, 0.08);
      return { latency, errRate, status: errRate > 0.05 ? "degraded" : "healthy" };
    },
  },
  {
    subsystem: "event_bus", name: "Event Bus",
    target: () => {
      const latency = rand(5, 30);
      const errRate = rng() < 0.95 ? rand(0, 0.005) : rand(0.01, 0.05);
      return { latency, errRate, status: "healthy" };
    },
  },
  {
    subsystem: "database", name: "PostgreSQL Cluster",
    target: () => {
      const latency = rand(1, 10);
      const errRate = rng() < 0.92 ? rand(0, 0.005) : rand(0.01, 0.04);
      return { latency, errRate, status: errRate > 0.02 ? "degraded" : "healthy" };
    },
  },
  {
    subsystem: "queues", name: "Redis Message Queues",
    target: () => {
      const latency = rand(0.5, 5);
      const errRate = rng() < 0.97 ? rand(0, 0.002) : rand(0.005, 0.02);
      return { latency, errRate, status: "healthy" };
    },
  },
  {
    subsystem: "websockets", name: "WebSocket Gateway",
    target: () => {
      const latency = rand(2, 15);
      const errRate = rng() < 0.9 ? rand(0, 0.01) : rand(0.02, 0.06);
      return { latency, errRate, status: errRate > 0.04 ? "degraded" : "healthy" };
    },
  },
];

function buildHealthChecks(): HealthCheck[] {
  return HEALTH_DEFS.map((d) => {
    const t = d.target();
    const isHealthy = t.status === "healthy";
    return {
      id: rid("hc", 8),
      subsystem: d.subsystem,
      name: d.name,
      status: t.status,
      latencyMs: t.latency,
      errorRate: t.errRate,
      lastCheckMs: randInt(200, 5_000),
      uptimePct: isHealthy ? rand(0.998, 0.9999) : rand(0.95, 0.99),
      consecutiveFailures: isHealthy ? 0 : randInt(1, 4),
      detail: isHealthy ? "All probes passing" : `Elevated error rate: ${(t.errRate * 100).toFixed(2)}%`,
    };
  });
}

// ---------- 6. Failure injection ----------
const FAILURE_DEFS: { type: FailureType; name: string; description: string; blast: string[] }[] = [
  { type: "provider_offline", name: "Primary Provider Offline", description: "Polygon market data feed goes down", blast: ["market_data", "options_data", "validation"] },
  { type: "database_slowdown", name: "Database Slowdown", description: "Write p95 rises to 5× baseline for 5min", blast: ["database", "event_bus", "agents"] },
  { type: "event_flood", name: "Event Flood", description: "10× normal event throughput for 60s", blast: ["event_bus", "queues", "agents"] },
  { type: "redis_restart", name: "Redis Restart", description: "Cache layer restarts under load", blast: ["queues", "cache", "indicator_engine"] },
  { type: "oom_kill", name: "OOM Kill", description: "Agent process killed by OOM killer", blast: ["agent_runtime", "forecast_ensemble"] },
  { type: "disk_full", name: "Disk Full", description: "Log partition fills to 95%", blast: ["logs", "backups", "audit"] },
  { type: "network_partition", name: "Network Partition", description: "AZ partition for 30s", blast: ["providers", "database", "websockets"] },
  { type: "agent_crash", name: "Agent Crash", description: "Critical agent process crash", blast: ["agent_runtime"] },
  { type: "config_drift", name: "Config Drift", description: "Manual config change detected", blast: ["config", "validation"] },
  { type: "clock_skew", name: "Clock Skew", description: "NTP drift exceeds 100ms", blast: ["validation", "correlation"] },
];

function buildFailures(): FailureScenario[] {
  return FAILURE_DEFS.map((d, i) => {
    const hasRun = rng() > 0.2;
    const recoveryMs = hasRun ? randInt(800, 12_000) : undefined;
    const passed = hasRun ? (recoveryMs ?? 0) < 8000 : false;
    const findings: string[] = [];
    if (hasRun) {
      switch (d.type) {
        case "provider_offline":
          findings.push("Failover to backup provider in 1.2s");
          findings.push("0 events lost — buffered during failover");
          findings.push("DNA confidence dropped 6% then recovered");
          break;
        case "database_slowdown":
          findings.push("Write-lock queue peaked at 47");
          findings.push("Partition rotation engaged automatically");
          findings.push("Reads unaffected — replica promoted");
          break;
        case "event_flood":
          findings.push("Backlog peaked at 4,200 (limit 10,000)");
          findings.push("p99 latency rose to 142ms, recovered in 18s");
          findings.push("Zero events dropped");
          break;
        case "redis_restart":
          findings.push("Cache rebuilt from event log in 3.4s");
          findings.push("Zero data loss — event-sourced recovery");
          break;
        case "oom_kill":
          findings.push("Agent restarted by supervisor in 2.1s");
          findings.push("In-flight events requeued");
          break;
        case "disk_full":
          findings.push("Log rotation triggered");
          findings.push("Old backups pruned automatically");
          break;
        case "network_partition":
          findings.push("Cross-AZ traffic rerouted in 4.8s");
          findings.push("WebSocket clients reconnected automatically");
          break;
        case "agent_crash":
          findings.push("Crash dump captured for analysis");
          findings.push("Agent restarted with backoff");
          break;
        case "config_drift":
          findings.push("Drift detected within 30s");
          findings.push("Auto-reverted to git-pinned version");
          break;
        case "clock_skew":
          findings.push("NTP re-sync forced");
          findings.push("Validation paused during skew window");
          break;
      }
    }
    return {
      id: `fail-${d.type}`,
      type: d.type,
      name: d.name,
      description: d.description,
      lastInjectedAt: hasRun ? now() - randInt(3600_000, 7 * 24 * 3600_000) : undefined,
      recoveryMs,
      status: hasRun ? (passed ? "passed" : "failed") : "not_run",
      blastRadius: d.blast,
      findings,
      autoRecovered: hasRun && passed,
    };
  });
}

// ---------- 7. Config validation ----------
const CONFIG_PATHS = [
  "config/platform.yaml",
  "config/providers.yaml",
  "config/event-bus.yaml",
  "config/database.yaml",
  "config/agents.yaml",
  "config/dna/technical.yaml",
  "config/dna/options.yaml",
  "config/dna/market.yaml",
  "config/dna/narrative.yaml",
  "config/dna/forecast.yaml",
  "config/dna/trade.yaml",
  "config/dna/operations.yaml",
  "config/report-engine.yaml",
  "config/certification.yaml",
  ".env.production",
];

function buildConfigs(): ConfigFile[] {
  return CONFIG_PATHS.map((path) => {
    const configModule = path.includes("/dna/") ? "dna" : path.replace("config/", "").replace(".yaml", "").replace(".production", "");
    const valid = rng() > 0.07;
    const drift = !valid && rng() > 0.5;
    const secrets = path === ".env.production" && rng() > 0.9;
    const findings: string[] = [];
    if (!valid) {
      if (drift) findings.push("Manual change detected — diff vs git HEAD");
      else findings.push("Schema validation failed on field 'providers[0].timeout'");
    } else {
      findings.push("Schema valid", "All required fields present");
    }
    if (secrets) findings.push("⚠ Plaintext secret detected — moved to vault");
    return {
      id: rid("cfg", 8),
      path,
      module: configModule,
      schemaVersion: "1.0",
      hash: hashLike(32),
      status: valid ? "valid" : drift ? "drift" : "invalid",
      findings,
      secretsDetected: secrets,
      gitCommit: hashLike(40),
      lastValidatedAt: now() - randInt(60_000, 3600_000),
      sizeBytes: randInt(500, 50_000),
    };
  });
}

// ---------- 8. Plugin integrity ----------
const PLUGIN_NAMES_BY_CAT: Record<PluginCategory, { name: string; stage: number }[]> = {
  ta: [
    { name: "EMA", stage: 7 }, { name: "RSI", stage: 7 }, { name: "MACD", stage: 7 },
    { name: "VWAP", stage: 7 }, { name: "ATR", stage: 7 }, { name: "BollingerBands", stage: 7 },
    { name: "Ichimoku", stage: 7 }, { name: "VolumeProfile", stage: 7 }, { name: "OBV", stage: 7 },
    { name: "ADX", stage: 7 }, { name: "Stochastic", stage: 7 }, { name: "MarketStructure", stage: 7 },
    { name: "WyckoffPhase", stage: 7 }, { name: "ChanTheory", stage: 7 },
  ],
  options: [
    { name: "GreeksEngine", stage: 8 }, { name: "IVSurface", stage: 8 }, { name: "GammaExposure", stage: 8 },
    { name: "DealerPositioning", stage: 8 }, { name: "MaxPain", stage: 8 }, { name: "OptionsFlow", stage: 8 },
    { name: "UnusualOptions", stage: 8 }, { name: "PutCallRatio", stage: 8 }, { name: "0DTEIntelligence", stage: 8 },
    { name: "VolSmile", stage: 8 }, { name: "TermStructure", stage: 8 }, { name: "VannaExposure", stage: 8 },
  ],
  market: [
    { name: "SectorLeadership", stage: 9 }, { name: "BreadthEngine", stage: 9 }, { name: "CorrelationMatrix", stage: 9 },
    { name: "RegimeClassifier", stage: 9 }, { name: "IntermarketAnalysis", stage: 9 }, { name: "RiskScore", stage: 9 },
  ],
  news: [
    { name: "EventClassifier", stage: 10 }, { name: "ImpactScorer", stage: 10 }, { name: "TimelineBuilder", stage: 10 },
    { name: "NarrativeGenerator", stage: 10 }, { name: "CatalystRadar", stage: 10 }, { name: "SentimentAnalyzer", stage: 10 },
  ],
  forecast: [
    { name: "LSTM-Price-v3", stage: 11 }, { name: "Transformer-Direction-v2", stage: 11 }, { name: "XGBoost-Vol-v1", stage: 11 },
    { name: "Ensemble-Consensus", stage: 11 }, { name: "BayesianRegression", stage: 11 }, { name: "VolatilityRegimeHMM", stage: 11 },
    { name: "MeanReversionEWMA", stage: 11 }, { name: "MomentumCNN", stage: 11 }, { name: "RandomForestDirection", stage: 11 },
  ],
};

function buildPlugins(): PluginRecord[] {
  const plugins: PluginRecord[] = [];
  for (const [cat, items] of Object.entries(PLUGIN_NAMES_BY_CAT) as [PluginCategory, { name: string; stage: number }[]][]) {
    for (const item of items) {
      // Replicate to reach 172 total
      for (let v = 0; v < 6; v++) {
        const tampered = rng() > 0.985;
        const signed = !tampered && rng() > 0.02;
        plugins.push({
          id: `plugin-${cat}-${item.name.toLowerCase().replace(/[^a-z0-9]/g, "-")}-v${v + 1}`,
          name: `${item.name} v${v + 1}`,
          category: cat,
          version: `${v + 1}.0.0`,
          stage: item.stage,
          hash: hashLike(32),
          signed,
          integrity: tampered ? "tampered" : "verified",
          manifestValid: !tampered,
          lastVerifiedAt: now() - randInt(60_000, 3_600_000),
          testCoverage: rand(0.65, 0.98),
          active: v === 0 && !tampered,
        });
      }
    }
  }
  return plugins.slice(0, 172);
}

// ---------- 9. Operational readiness report ----------
function buildReadiness(opts: {
  health: HealthCheck[];
  failures: FailureScenario[];
  configs: ConfigFile[];
  plugins: PluginRecord[];
  backups: BackupJob[];
  traces: Trace[];
}): OperationalReadinessReport {
  const { health, failures, configs, plugins, backups, traces } = opts;

  const healthScore = health.filter((h) => h.status === "healthy").length / health.length;
  const failureScore = failures.filter((f) => f.status === "passed").length / failures.length;
  const configScore = configs.filter((c) => c.status === "valid" && !c.secretsDetected).length / configs.length;
  const pluginScore = plugins.filter((p) => p.integrity === "verified" && p.signed).length / plugins.length;
  const backupScore = backups.filter((b) => b.restoreVerified).length / backups.length;
  const traceScore = traces.filter((t) => t.status === "ok").length / Math.max(1, traces.length);

  const subsystems = [
    {
      id: "traceability", name: "End-to-End Traceability", status: traceScore >= 0.9 ? "pass" : traceScore >= 0.7 ? "warn" : "fail", score: traceScore,
      checks: [
        { id: "tr.coverage", label: "All requests carry correlation ID", passed: true, detail: "100% of API requests instrumented" },
        { id: "tr.hops", label: "Trace spans cover all 9 subsystems", passed: true, detail: `${SPAN_TEMPLATES.length} span kinds tracked` },
        { id: "tr.storage", label: "Traces retained for 30 days", passed: true },
        { id: "tr.errors", label: "Failed traces < 5%", passed: traceScore >= 0.95, detail: `${(traceScore * 100).toFixed(1)}% ok` },
      ],
    },
    {
      id: "logging", name: "Structured Logging", status: "pass", score: 0.97,
      checks: [
        { id: "lg.format", label: "All logs in JSON format", passed: true },
        { id: "lg.correlation", label: "Correlation IDs present on 95%+ logs", passed: true, detail: "97.3% correlation coverage" },
        { id: "lg.levels", label: "All 5 levels (DEBUG→FATAL) in use", passed: true },
        { id: "lg.modules", label: "All 14 modules emitting logs", passed: true },
      ],
    },
    {
      id: "aggregation", name: "Log Aggregation", status: "pass", score: 0.94,
      checks: [
        { id: "ag.shipper", label: "Log shipper running (Fluent Bit)", passed: true },
        { id: "ag.search", label: "Searchable within 5s of emission", passed: true },
        { id: "ag.retention", label: "30-day hot retention + 1yr cold", passed: true },
        { id: "ag.alerting", label: "ERROR/FATAL alerts wired to on-call", passed: true },
      ],
    },
    {
      id: "backup", name: "Backup & Restore", status: backupScore >= 0.9 ? "pass" : "warn", score: backupScore,
      checks: [
        { id: "bk.schedule", label: "All 13 targets backed up in last 24h", passed: true },
        { id: "bk.verify", label: "Restore tests run on latest backups", passed: backupScore >= 0.9, detail: `${backups.filter((b) => b.restoreVerified).length}/${backups.length} verified` },
        { id: "bk.retention", label: "Retention policy enforced", passed: true },
        { id: "bk.hash", label: "All backups hash-verified", passed: true },
      ],
    },
    {
      id: "health", name: "Health Monitoring", status: healthScore >= 0.85 ? "pass" : healthScore >= 0.6 ? "warn" : "fail", score: healthScore,
      checks: health.map((h) => ({ id: `he.${h.subsystem}`, label: h.name, passed: h.status === "healthy", detail: `${h.status} · ${h.latencyMs.toFixed(1)}ms · ${(h.errorRate * 100).toFixed(2)}% err` })),
    },
    {
      id: "failure", name: "Failure Injection", status: failureScore >= 0.85 ? "pass" : failureScore >= 0.6 ? "warn" : "fail", score: failureScore,
      checks: failures.map((f) => ({ id: `fi.${f.type}`, label: f.name, passed: f.status === "passed", detail: f.recoveryMs !== undefined ? `recovery ${(f.recoveryMs / 1000).toFixed(2)}s` : "not run" })),
    },
    {
      id: "config", name: "Config Validation", status: configScore >= 0.95 ? "pass" : configScore >= 0.8 ? "warn" : "fail", score: configScore,
      checks: configs.map((c) => ({ id: `cf.${c.path}`, label: c.path, passed: c.status === "valid" && !c.secretsDetected, detail: c.status })),
    },
    {
      id: "plugins", name: "Plugin Integrity", status: pluginScore >= 0.99 ? "pass" : pluginScore >= 0.95 ? "warn" : "fail", score: pluginScore,
      checks: [
        { id: "pl.signed", label: "All active plugins cryptographically signed", passed: plugins.filter((p) => p.active && p.signed).length === plugins.filter((p) => p.active).length, detail: `${plugins.filter((p) => p.active && p.signed).length}/${plugins.filter((p) => p.active).length} signed` },
        { id: "pl.hash", label: "All plugin hashes match registry", passed: plugins.filter((p) => p.integrity === "verified").length === plugins.length, detail: `${plugins.filter((p) => p.integrity === "verified").length}/${plugins.length} verified` },
        { id: "pl.manifest", label: "All manifests valid", passed: plugins.filter((p) => p.manifestValid).length === plugins.length },
        { id: "pl.tests", label: "Test coverage ≥ 70%", passed: plugins.filter((p) => p.testCoverage >= 0.7).length === plugins.length, detail: `avg ${(plugins.reduce((s, p) => s + p.testCoverage, 0) / plugins.length * 100).toFixed(1)}%` },
      ],
    },
  ];

  const overallScore = subsystems.reduce((s, x) => s + x.score, 0) / subsystems.length;
  const criticalFailures = subsystems.filter((s) => s.status === "fail").length;
  const warnings = subsystems.filter((s) => s.status === "warn").length;
  const status: OperationalReadinessReport["status"] = criticalFailures > 0 ? "not_ready" : warnings > 0 ? "degraded" : "ready";

  return {
    version: "1.0",
    generatedAt: now(),
    buildHash: "athx-15.5.0+sha.stage15.5",
    subsystems,
    overallScore,
    status,
    criticalFailures,
    warnings,
    uptimeSeconds: 14 * 24 * 3600 + randInt(0, 86400),
    mtbfHours: rand(120, 480),
    mttrMinutes: rand(2.5, 8.5),
  };
}

// ---------- Engine state ----------
let state: OpsTelemetry | null = null;

function buildInitialSnapshot(): OpsTelemetry {
  const traces = buildTraces();
  const logs = buildLogs(traces);
  const { backups, restoreTests } = buildBackups();
  const healthChecks = buildHealthChecks();
  const failureScenarios = buildFailures();
  const configs = buildConfigs();
  const plugins = buildPlugins();
  const readiness = buildReadiness({ health: healthChecks, failures: failureScenarios, configs, plugins, backups, traces });

  return {
    timestamp: now(),
    traces,
    logs,
    backups,
    restoreTests,
    healthChecks,
    failureScenarios,
    configs,
    plugins,
    readiness,
  };
}

/** Tick the engine forward — adds new logs and traces, drifts health metrics */
function tick(s: OpsTelemetry): OpsTelemetry {
  const newTraces = [buildTrace(pick(TRACE_TRIGGERS)), ...s.traces].slice(0, 24);
  const newLogs = [...Array.from({ length: 3 }, () => buildLog()), ...s.logs].slice(0, 200);

  // Drift health metrics
  const newHealth = s.healthChecks.map((h) => {
    const latency = Math.max(0.5, h.latencyMs + (rng() - 0.5) * h.latencyMs * 0.2);
    const errRate = Math.max(0, h.errorRate + (rng() - 0.5) * 0.005);
    const status: HealthCheck["status"] = errRate > 0.05 ? "degraded" : errRate > 0.1 ? "down" : "healthy";
    return {
      ...h,
      latencyMs: latency,
      errorRate: errRate,
      status,
      lastCheckMs: randInt(200, 5_000),
      consecutiveFailures: status === "healthy" ? 0 : h.consecutiveFailures + (rng() > 0.7 ? 1 : 0),
    };
  });

  // Refresh readiness with new health
  const readiness = buildReadiness({
    health: newHealth,
    failures: s.failureScenarios,
    configs: s.configs,
    plugins: s.plugins,
    backups: s.backups,
    traces: newTraces,
  });

  return {
    ...s,
    timestamp: now(),
    traces: newTraces,
    logs: newLogs,
    healthChecks: newHealth,
    readiness,
  };
}

export function getOpsTelemetry(): OpsTelemetry {
  if (!state) state = buildInitialSnapshot();
  return state;
}

export function advanceOpsTelemetry(): OpsTelemetry {
  const current = getOpsTelemetry();
  state = tick(current);
  return state;
}

export function resetOpsTelemetry(): OpsTelemetry {
  state = buildInitialSnapshot();
  return state;
}
