/**
 * ATHENA-X Stage 15.5 — Platform Hardening & Operations Types
 *
 * Covers 9 operational subsystems:
 *   1. Traceability     — correlation IDs, spans, end-to-end data flow
 *   2. Structured Logs  — JSON logs with module/level/correlation_id
 *   3. Log Aggregation  — searchable audit trail
 *   4. Backup & Restore — automated backups with restore verification
 *   5. Health Monitor   — providers/agents/eventbus/db/queues/websockets
 *   6. Failure Injection — chaos tests with recovery time + blast radius
 *   7. Config Validation — schema validation + version control + secrets scan
 *   8. Plugin Integrity  — hash + signature + version for all 172 plugins
 *   9. Readiness Report  — final pass/fail verdict per subsystem
 *
 * This stage introduces NO new trading features — it only hardens the
 * operational layer so the platform can run continuously and recover
 * gracefully from failures.
 */

// ---------- 1. Traceability ----------
export type SpanKind = "provider" | "validator" | "normalizer" | "database" | "event_bus" | "agent" | "dna" | "report" | "api";

export interface TraceSpan {
  id: string;
  traceId: string;
  parentSpanId?: string;
  name: string;
  kind: SpanKind;
  module: string;
  startTime: number;
  endTime: number;
  durationMs: number;
  status: "ok" | "error" | "timeout";
  attributes: Record<string, string | number | boolean>;
  events: { time: number; name: string; detail?: string }[];
}

export interface Trace {
  id: string;
  rootSpanId: string;
  spans: TraceSpan[];
  startTime: number;
  endTime: number;
  durationMs: number;
  status: "ok" | "partial" | "failed";
  /** The originating event type (e.g. "market.tick", "options.chain", "news.article") */
  trigger: string;
  /** Number of subsystems touched */
  hopCount: number;
}

// ---------- 2 & 3. Structured Logs ----------
export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR" | "FATAL";

export interface StructuredLog {
  id: string;
  timestamp: number;
  level: LogLevel;
  module: string;
  message: string;
  correlationId?: string;
  traceId?: string;
  spanId?: string;
  userId?: string;
  sessionId?: string;
  /** Custom structured fields */
  fields: Record<string, string | number | boolean | null>;
}

// ---------- 4. Backup & Restore ----------
export type BackupType = "full" | "incremental" | "snapshot" | "wal";
export type BackupStatus = "completed" | "running" | "failed" | "verified" | "expired";

export interface BackupJob {
  id: string;
  type: BackupType;
  target: string; // e.g. "ohlcv", "options_chain", "events", "full_cluster"
  startedAt: number;
  completedAt?: number;
  durationMs?: number;
  sizeBytes: number;
  status: BackupStatus;
  /** Storage URI (simulated) */
  location: string;
  /** SHA-256 hash of the backup contents */
  hash: string;
  /** Whether a restore test has been performed */
  restoreVerified: boolean;
  retentionDays: number;
}

export interface RestoreTest {
  id: string;
  backupId: string;
  startedAt: number;
  completedAt: number;
  durationMs: number;
  status: "pass" | "fail";
  /** Sandbox the restore was tested against */
  sandbox: string;
  /** Row count verified */
  rowsVerified: number;
  /** Hash check passed */
  hashMatch: boolean;
  findings: string[];
}

// ---------- 5. Health Monitor ----------
export type HealthSubsystem =
  | "providers"
  | "agents"
  | "event_bus"
  | "database"
  | "queues"
  | "websockets";

export interface HealthCheck {
  id: string;
  subsystem: HealthSubsystem;
  name: string;
  status: "healthy" | "degraded" | "down" | "unknown";
  latencyMs: number;
  errorRate: number; // 0..1
  lastCheckMs: number;
  uptimePct: number; // 0..1
  /** Consecutive failures */
  consecutiveFailures: number;
  detail?: string;
}

// ---------- 6. Failure Injection ----------
export type FailureType =
  | "provider_offline"
  | "database_slowdown"
  | "event_flood"
  | "redis_restart"
  | "oom_kill"
  | "disk_full"
  | "network_partition"
  | "agent_crash"
  | "config_drift"
  | "clock_skew";

export interface FailureScenario {
  id: string;
  type: FailureType;
  name: string;
  description: string;
  /** Last time this was injected */
  lastInjectedAt?: number;
  /** Recovery time in ms */
  recoveryMs?: number;
  status: "passed" | "failed" | "not_run";
  blastRadius: string[];
  findings: string[];
  /** Whether auto-recovery engaged */
  autoRecovered: boolean;
}

// ---------- 7. Config Validation ----------
export interface ConfigFile {
  id: string;
  path: string;
  module: string;
  schemaVersion: string;
  /** Hash of the canonical config content */
  hash: string;
  status: "valid" | "invalid" | "drift" | "missing";
  /** Validation findings */
  findings: string[];
  /** Whether secrets were detected (should be empty) */
  secretsDetected: boolean;
  /** Git commit the config is pinned to */
  gitCommit: string;
  lastValidatedAt: number;
  sizeBytes: number;
}

// ---------- 8. Plugin Integrity ----------
export type PluginCategory = "ta" | "options" | "market" | "news" | "forecast";

export interface PluginRecord {
  id: string;
  name: string;
  category: PluginCategory;
  version: string;
  stage: number;
  /** SHA-256 hash of plugin code */
  hash: string;
  /** Cryptographic signature status */
  signed: boolean;
  /** Integrity check status */
  integrity: "verified" | "tampered" | "unknown";
  /** Manifest present and valid */
  manifestValid: boolean;
  lastVerifiedAt: number;
  /** Test coverage % */
  testCoverage: number;
  active: boolean;
}

// ---------- 9. Operational Readiness Report ----------
export interface ReadinessSubsystem {
  id: string;
  name: string;
  status: "pass" | "warn" | "fail";
  score: number; // 0..1
  checks: { id: string; label: string; passed: boolean; detail?: string }[];
}

export interface OperationalReadinessReport {
  version: string;
  generatedAt: number;
  buildHash: string;
  subsystems: ReadinessSubsystem[];
  overallScore: number;
  status: "ready" | "degraded" | "not_ready";
  criticalFailures: number;
  warnings: number;
  /** Time platform has been continuously running */
  uptimeSeconds: number;
  /** Mean time between failures (hours) */
  mtbfHours: number;
  /** Mean time to recovery (minutes) */
  mttrMinutes: number;
}

// ---------- Top-level ops telemetry ----------
export interface OpsTelemetry {
  timestamp: number;
  traces: Trace[];
  logs: StructuredLog[];
  backups: BackupJob[];
  restoreTests: RestoreTest[];
  healthChecks: HealthCheck[];
  failureScenarios: FailureScenario[];
  configs: ConfigFile[];
  plugins: PluginRecord[];
  readiness: OperationalReadinessReport;
}
