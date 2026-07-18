/**
 * ATHENA-X Stage 15.6 — Production Performance Certification Types
 *
 * The objective is not to build features. The objective is to prove
 * ATHENA-X is production-ready across 12 certification areas plus a
 * performance budget.
 *
 * Every metric has a budget threshold. Every area produces a pass/warn/fail
 * verdict. The final certification aggregates all 12 areas + budget
 * compliance into a single CERTIFIED / CONDITIONAL / NOT CERTIFIED verdict.
 */

// ---------- Shared ----------
export type CertStatus = "pass" | "warn" | "fail";
export type CheckStatus = "pass" | "warn" | "fail";

export interface PerfCheck {
  id: string;
  label: string;
  status: CheckStatus;
  value: number | string;
  unit?: string;
  target?: number | string;
  detail?: string;
}

export interface CertArea {
  id: string;
  name: string;
  description: string;
  status: CertStatus;
  score: number; // 0..1
  checks: PerfCheck[];
}

// ---------- 1. Startup Certification ----------
export interface StartupMetric {
  id: string;
  label: string;
  coldMs: number;
  warmMs: number;
  targetMs: number;
  status: CheckStatus;
}

// ---------- 2. Frontend Performance ----------
export interface FrontendMetric {
  id: string;
  label: string;
  value: number;
  unit: string;
  target: number;
  status: CheckStatus;
  description: string;
}

// ---------- 3. Backend Performance ----------
export interface BackendMetric {
  id: string;
  label: string;
  p50: number;
  p95: number;
  p99: number;
  unit: string;
  targetP95: number;
  status: CheckStatus;
}

// ---------- 4. Agent Performance ----------
export interface AgentPerfRecord {
  id: string;
  name: string;
  stage: number;
  category: string;
  avgExecMs: number;
  peakExecMs: number;
  queueWaitMs: number;
  retryCount: number;
  timeoutCount: number;
  memMb: number;
  cpuPct: number;
  rank: number; // 1 = fastest
  status: CheckStatus;
}

// ---------- 5. Plugin Performance ----------
export interface PluginPerfRecord {
  id: string;
  name: string;
  category: "ta" | "options" | "market" | "news" | "forecast";
  execMs: number;
  cpuPct: number;
  memMb: number;
  rank: number;
  status: CheckStatus;
}

// ---------- 6. Load Testing ----------
export interface LoadTestPoint {
  eventsPerSec: number;
  p50Ms: number;
  p95Ms: number;
  p99Ms: number;
  backlog: number;
  droppedEvents: number;
  status: CheckStatus;
}

// ---------- 7. Soak Testing ----------
export interface SoakResult {
  id: string;
  duration: "8h" | "24h" | "72h";
  memoryGrowthMb: number;
  queueGrowth: number;
  threadLeaks: number;
  socketLeaks: number;
  status: CheckStatus;
  findings: string[];
}

// ---------- 8. Chaos Testing ----------
export interface ChaosTest {
  id: string;
  target: string;
  description: string;
  killedAt: number;
  recoveredMs: number;
  status: CheckStatus;
  finding: string;
}

// ---------- 9. Recovery Certification ----------
export interface RecoveryMetric {
  id: string;
  label: string;
  value: number;
  unit: string;
  target: number;
  status: CheckStatus;
}

// ---------- 10. Scalability ----------
export interface ScalabilityMetric {
  id: string;
  label: string;
  current: number;
  max: number;
  unit: string;
  utilizationPct: number;
  status: CheckStatus;
}

// ---------- 11. Resource Certification ----------
export interface ResourceMetric {
  id: string;
  label: string;
  used: number;
  total: number;
  unit: string;
  utilizationPct: number;
  status: CheckStatus;
}

// ---------- 12. Regression ----------
export interface RegressionCheck {
  id: string;
  label: string;
  passed: boolean;
  duration: number;
  detail: string;
}

// ---------- Performance Budget ----------
export interface BudgetItem {
  id: string;
  metric: string;
  budget: number;
  actual: number;
  unit: string;
  status: CheckStatus;
  category: "frontend" | "backend" | "agent" | "resource";
}

// ---------- Final Certification ----------
export interface PerformanceCertification {
  version: string;
  generatedAt: number;
  buildHash: string;
  areas: CertArea[];
  budget: BudgetItem[];
  overallScore: number;
  status: "certified" | "conditional" | "not_certified";
  criticalFailures: number;
  warnings: number;
  /** Performance budget compliance 0..1 */
  budgetCompliance: number;
}

// ---------- Top-level perf telemetry ----------
export interface PerfTelemetry {
  timestamp: number;
  startup: StartupMetric[];
  frontend: FrontendMetric[];
  backend: BackendMetric[];
  agents: AgentPerfRecord[];
  plugins: PluginPerfRecord[];
  loadTests: LoadTestPoint[];
  soak: SoakResult[];
  chaos: ChaosTest[];
  recovery: RecoveryMetric[];
  scalability: ScalabilityMetric[];
  resources: ResourceMetric[];
  regression: RegressionCheck[];
  certification: PerformanceCertification;
}
