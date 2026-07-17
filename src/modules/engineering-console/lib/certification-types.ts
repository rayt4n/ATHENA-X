/**
 * ATHENA-X Stage 14.5 — Production Certification Types
 *
 * Defines the data model for the 8 certification modules that gate the
 * transition from "platform works" to "platform is trustworthy for live
 * market use."
 *
 * Each module produces a list of checks, each with a status, score, and
 * optional evidence. The module's overall score is the weighted average
 * of its checks. The final Production Readiness Certificate aggregates
 * all 8 module scores into a single CERTIFIED / NOT CERTIFIED verdict.
 */

export type CheckStatus = "pass" | "warn" | "fail" | "pending" | "running";

export type ModuleId =
  | "data"
  | "intelligence"
  | "forecast"
  | "decision"
  | "stress"
  | "replay"
  | "performance"
  | "certificate";

export interface CertCheck {
  id: string;
  label: string;
  description?: string;
  status: CheckStatus;
  /** 0..1 — contribution to module score */
  score: number;
  /** weight applied when rolling up to module score */
  weight: number;
  /** measured value (if applicable) */
  value?: number | string;
  /** target / threshold (if applicable) */
  target?: number | string;
  /** unit label */
  unit?: string;
  /** human-readable evidence */
  evidence?: string;
  /** duration of the check in ms */
  durationMs?: number;
}

export interface CertModule {
  id: ModuleId;
  index: number;
  name: string;
  description: string;
  status: CheckStatus;
  /** weighted average of check scores, 0..1 */
  score: number;
  checks: CertCheck[];
  startedAt?: number;
  completedAt?: number;
  durationMs?: number;
}

export interface StressScenario {
  id: string;
  name: string;
  description: string;
  status: CheckStatus;
  score: number;
  injectedAt: number;
  recoveredAt?: number;
  recoveryMs?: number;
  findings: string[];
  blastRadius: string[];
}

export interface ReplayScenario {
  id: string;
  name: string;
  date: string;
  description: string;
  status: CheckStatus;
  matchRate: number;
  driftMetrics: { name: string; original: number; replayed: number; drift: number; tolerance: number; pass: boolean }[];
  durationMs: number;
}

export interface DNACertResult {
  id: "technical" | "options" | "market" | "narrative" | "forecast" | "trade" | "operations";
  name: string;
  confidence: number;
  freshnessMs: number;
  completeness: number;
  consistency: number;
  state: CheckStatus;
  score: number;
  notes: string[];
}

export interface CertificateSummary {
  version: string;
  generatedAt: number;
  buildHash: string;
  environment: string;
  modules: { id: ModuleId; name: string; status: CheckStatus; score: number }[];
  overallScore: number;
  status: "certified" | "conditional" | "not_certified";
  criticalFailures: number;
  warnings: number;
  exitCriteria: { id: string; label: string; passed: boolean; detail?: string }[];
  signedBy: string;
  validUntil: number;
}

export interface CertificationState {
  startedAt: number | null;
  completedAt: number | null;
  isRunning: boolean;
  currentModule: ModuleId | null;
  progress: number; // 0..1
  modules: CertModule[];
  stressScenarios: StressScenario[];
  replayScenarios: ReplayScenario[];
  dnaResults: DNACertResult[];
  certificate: CertificateSummary | null;
}
