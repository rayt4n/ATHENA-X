/**
 * ATHENA-X Validation Dashboard — Telemetry Types
 *
 * These types describe the live runtime state of the ATHENA-X platform:
 * data sources, providers, AI agents, event bus, database, and the seven
 * DNA (Digital Narrative Architecture) intelligence objects.
 *
 * In production these would be populated from the platform's own event bus
 * via a websocket bridge. For the validation cockpit they are simulated by
 * a deterministic mock engine so the dashboard is self-contained.
 */

export type HealthState = "healthy" | "degraded" | "down" | "warming";
export type Severity = "info" | "warning" | "critical";

export interface ProviderStatus {
  id: string;
  name: string;
  category: "market_data" | "options_data" | "news" | "macro" | "alt_data";
  state: HealthState;
  /** ms since the last successful heartbeat */
  lastTickMs: number;
  /** ms since the last published tick for the symbol stream */
  lastDataMs: number;
  /** tick rate per second (rolling) */
  tickRate: number;
  /** error count in the last 5 minutes */
  errors5m: number;
  /** position in the failover chain — 0 = primary */
  failoverRank: number;
  /** cumulative uptime fraction 0..1 */
  uptime: number;
  /** round-trip latency for the most recent request, ms */
  latencyMs: number;
}

export interface DataFreshnessEntry {
  symbol: string;
  assetClass: "equity_index" | "options" | "futures" | "fx" | "rates";
  lastTick: number; // epoch ms
  source: string;
  state: HealthState;
  /** expected cadence in ms */
  cadenceMs: number;
}

export interface TechnicalIndicatorCheck {
  id: string;
  symbol: string;
  indicator: string;
  timeframe: string;
  computed: number;
  benchmark: number;
  /** relative drift (computed - benchmark) / |benchmark| */
  drift: number;
  state: HealthState;
  lastValidation: number;
  validator: string;
}

export interface OptionsAccuracyCheck {
  id: string;
  symbol: string;
  check: "iv_surface_smoothness" | "greeks_parity" | "put_call_arbitrage" | "vol_smile_curvature" | "delta_hedge_drift";
  value: number;
  threshold: number;
  state: HealthState;
  detail: string;
  lastCheck: number;
}

export interface ForecastRecord {
  id: string;
  model: string;
  horizon: string;
  target: string;
  predicted: number;
  realized?: number;
  error?: number;
  confidence: number;
  timestamp: number;
  state: "pending" | "resolved" | "stale";
}

export interface ForecastAccuracySummary {
  totalForecasts: number;
  resolvedCount: number;
  hitRate: number;            // directional accuracy 0..1
  mae: number;                // mean absolute error (price units)
  rmse: number;
  calibrationSlope: number;   // 1.0 = perfectly calibrated
  calibrationCurve: { bucket: number; predicted: number; observed: number; n: number }[];
  perModel: { model: string; hitRate: number; mae: number; n: number }[];
}

export interface TradeDNADecision {
  id: string;
  symbol: string;
  direction: "long" | "short" | "neutral";
  setup: string;
  entry: number;
  stop: number;
  target: number;
  confidence: number;
  rr: number;                  // risk/reward
  status: "evaluating" | "qualified" | "rejected" | "triggered" | "managed" | "closed";
  reasoningTags: string[];
  dnaInputs: { technical: number; options: number; market: number; narrative: number; forecast: number };
  timestamp: number;
  outcomePnl?: number;
}

export interface EventBusMetrics {
  inflowPerSec: number;
  outflowPerSec: number;
  backlog: number;
  backlogLimit: number;
  p50LatencyMs: number;
  p95LatencyMs: number;
  p99LatencyMs: number;
  replayDepth: number;
  replayLag: number;
  snapshotBarrierStatus: "open" | "blocked" | "completed";
  lastSnapshotMs: number;
  latencyHistory: { t: number; p50: number; p95: number; p99: number }[];
  throughputHistory: { t: number; inflow: number; outflow: number }[];
  priorityDistribution: { priority: "P0" | "P1" | "P2" | "P3"; count: number; percentage: number }[];
}

export interface AgentState {
  id: string;
  name: string;
  stage: number;
  category: "validation" | "normalization" | "technical" | "options" | "market" | "narrative" | "forecast" | "trade" | "operations";
  state: HealthState;
  lastHeartbeatMs: number;
  processedEvents: number;
  errors: number;
  cpuPct: number;
  memMb: number;
  uptime: number;
  currentTask?: string;
}

export interface DatabaseSchemaMetrics {
  schema: string;
  writeP50: number;
  writeP95: number;
  writeLockQueue: number;
  rowsLastMin: number;
  totalRows: number;
  partitionCount: number;
  state: HealthState;
}

export interface DNABlock {
  id: "technical" | "options" | "market" | "narrative" | "forecast" | "trade" | "operations";
  name: string;
  stage: number;
  confidence: number;          // 0..1 — current consensus confidence
  trend: number;               // -1..1
  freshnessMs: number;
  inputCount: number;
  validatorCount: number;
  state: HealthState;
  /** the contributors feeding this DNA block */
  contributors: { name: string; weight: number; contribution: number; state: HealthState }[];
  /** rolling confidence history */
  history: { t: number; confidence: number }[];
  lastSerialized: number;
  serializationSizeKb: number;
}

export interface SystemSummary {
  stage: string;
  environment: string;
  buildHash: string;
  startedAt: number;
  totalAgents: number;
  healthyAgents: number;
  totalProviders: number;
  healthyProviders: number;
  totalPlugins: number;
  activePlugins: number;
  eventBusBacklog: number;
  eventBusP95: number;
  dbWriteP95: number;
  overallHealth: HealthState;
  activeAlarms: number;
}

export interface DashboardTelemetry {
  timestamp: number;
  system: SystemSummary;
  providers: ProviderStatus[];
  freshness: DataFreshnessEntry[];
  taChecks: TechnicalIndicatorCheck[];
  optionsChecks: OptionsAccuracyCheck[];
  forecast: {
    recent: ForecastRecord[];
    summary: ForecastAccuracySummary;
  };
  tradeDecisions: TradeDNADecision[];
  eventBus: EventBusMetrics;
  agents: AgentState[];
  database: DatabaseSchemaMetrics[];
  dna: DNABlock[];
  alarms: Alarm[];
}

export interface Alarm {
  id: string;
  severity: Severity;
  source: string;
  message: string;
  raisedAt: number;
  acked: boolean;
}
