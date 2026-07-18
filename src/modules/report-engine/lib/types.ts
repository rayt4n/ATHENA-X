/**
 * ATHENA-X Stage 15 — Institutional Report Engine Types
 *
 * The Report Engine is READ-ONLY. It never calculates indicators, forecasts,
 * probabilities, or trading signals. It only consumes validated intelligence
 * from the canonical databases and the seven DNA objects, transforming them
 * into clear, explainable, and auditable reports.
 *
 * Architecture:
 *   Canonical DBs + 7 DNA Objects → Composer → Markdown | JSON | PDF → Storage → Dashboard
 */

// ---------- Report types ----------
export type ReportTypeId =
  | "premarket"
  | "marketopen"
  | "intraday"
  | "event"
  | "endofday"
  | "weekly";

export type ReportFormat = "markdown" | "json" | "pdf";

export type ReportStatus = "draft" | "published" | "archived" | "failed";

export type EventSubtype =
  | "cpi"
  | "fomc"
  | "nfp"
  | "earnings"
  | "treasury_auction"
  | "geopolitical";

// ---------- Report sections (every report uses this structure) ----------
export type SectionId =
  | "executive_summary"
  | "market_overview"
  | "technical_intelligence"
  | "options_intelligence"
  | "market_intelligence"
  | "narrative_intelligence"
  | "forecast_intelligence"
  | "trade_intelligence"
  | "risk_summary"
  | "explainability";

export interface ReportSection {
  id: SectionId;
  title: string;
  /** Markdown-formatted content for this section */
  markdown: string;
  /** Structured data backing the markdown (for JSON output) */
  data: Record<string, unknown>;
  /** DNA objects consumed by this section (audit trail) */
  sources: DNAMarker[];
}

export interface DNAMarker {
  id: "technical" | "options" | "market" | "narrative" | "forecast" | "trade" | "operations";
  version: string;
  confidence: number;
}

// ---------- Report content (composed from DNA + canonical data) ----------
export interface ReportContent {
  id: string;
  type: ReportTypeId;
  eventSubtype?: EventSubtype;
  title: string;
  subtitle?: string;
  generatedAt: number;
  /** The trading session this report covers (YYYY-MM-DD) */
  sessionDate: string;
  sections: ReportSection[];
  /** Snapshot of all DNA objects used (for audit) */
  dnaSnapshot: {
    technical: DNAMarker;
    options: DNAMarker;
    market: DNAMarker;
    narrative: DNAMarker;
    forecast: DNAMarker;
    trade: DNAMarker;
    operations: DNAMarker;
  };
}

// ---------- Audit metadata (every stored report carries this) ----------
export interface AuditMetadata {
  /** Schema version of the report engine */
  schemaVersion: string;
  /** Build hash of the platform */
  buildVersion: string;
  /** Version of the report generator code */
  generatorVersion: string;
  /** Version of each DNA object consumed (for replayability) */
  dnaVersions: {
    technical: string;
    options: string;
    market: string;
    narrative: string;
    forecast: string;
    trade: string;
    operations: string;
  };
  /** Forecast model version */
  forecastVersion: string;
  /** Workspace ID (multi-tenant isolation) */
  workspace: string;
  /** User who triggered generation */
  user: string;
  /** Cryptographic hash of the report content (deterministic) */
  hash: string;
  /** Prior version of this report (if updated) */
  priorVersion?: string;
}

// ---------- Stored report (content + audit + formats) ----------
export interface StoredReport {
  id: string;
  content: ReportContent;
  audit: AuditMetadata;
  status: ReportStatus;
  /** Available formats and their storage URIs */
  formats: {
    markdown: string; // e.g. "s3://reports/{id}.md" — simulated as path
    json: string;
    pdf: string;
  };
  /** Lifecycle events for this report */
  events: ReportEvent[];
  createdAt: number;
  publishedAt?: number;
  archivedAt?: number;
}

export interface ReportEvent {
  type: "report:created" | "report:updated" | "report:failed" | "report:published";
  timestamp: number;
  detail?: string;
  /** Hash of the report at the time of this event */
  reportHash?: string;
}

// ---------- Manifest (one per report type) ----------
export interface ReportManifest {
  type: ReportTypeId;
  name: string;
  description: string;
  /** Which sections this report includes (in order) */
  sections: SectionId[];
  /** Default generation trigger */
  trigger: {
    kind: "cron" | "event" | "manual" | "interval";
    /** Cron expression (if kind=cron), event subtype (if kind=event), interval ms (if kind=interval) */
    spec?: string;
  };
  /** DNA objects required to compose this report */
  requiredDNA: DNAMarker["id"][];
  /** Whether this report type accepts an event subtype (e.g. CPI, FOMC) */
  acceptsEventSubtype?: boolean;
  /** Schema version this manifest targets */
  schemaVersion: string;
  /** Authoring info */
  author: string;
  version: string;
}

// ---------- Composer input (the only thing the engine may read) ----------
export interface ComposerInput {
  /** Live snapshot of all 7 DNA objects */
  dna: {
    technical: DNAObjectSnapshot;
    options: DNAObjectSnapshot;
    market: DNAObjectSnapshot;
    narrative: DNAObjectSnapshot;
    forecast: DNAObjectSnapshot;
    trade: DNAObjectSnapshot;
    operations: DNAObjectSnapshot;
  };
  /** Canonical market data (already validated) */
  canonical: {
    marketOverview: MarketOverviewEntry[];
    overnight: OvernightSummary;
    news: NewsItem[];
    macro: MacroIndicator[];
  };
  /** Report-specific parameters */
  params: {
    sessionDate: string;
    eventSubtype?: EventSubtype;
    workspace: string;
    user: string;
  };
}

export interface DNAObjectSnapshot {
  id: DNAMarker["id"];
  name: string;
  confidence: number;
  freshnessMs: number;
  contributors: { name: string; weight: number; contribution: number; state: string }[];
  version: string;
  /** Domain-specific intelligence payload (already computed upstream) */
  intelligence: Record<string, unknown>;
}

export interface MarketOverviewEntry {
  symbol: string;
  name: string;
  assetClass: "equity_index" | "volatility" | "rates" | "fx" | "commodity";
  price: number;
  change: number;
  changePct: number;
  source: string;
  lastTick: number;
}

export interface OvernightSummary {
  asia: { session: string; change: number; summary: string };
  europe: { session: string; change: number; summary: string };
  futures: { symbol: string; change: number; changePct: number }[];
  vix: number;
  vixChange: number;
  bonds10y: number;
  bonds10yChange: number;
  dxy: number;
  dxyChange: number;
  gold: number;
  oil: number;
  copper: number;
  usdjpy: number;
}

export interface NewsItem {
  id: string;
  headline: string;
  source: string;
  timestamp: number;
  category: "macro" | "earnings" | "geopolitical" | "central_bank" | "fed";
  impact: "high" | "medium" | "low";
  sentiment: number; // -1..1
}

export interface MacroIndicator {
  name: string;
  value: string;
  prior: string;
  expected: string;
  actual?: string;
  surprise?: string;
  timestamp: number;
}

// ---------- Generation request/result ----------
export interface GenerateReportRequest {
  type: ReportTypeId;
  eventSubtype?: EventSubtype;
  sessionDate?: string;
  workspace?: string;
  user?: string;
}

export interface GenerateReportResult {
  report: StoredReport;
  /** Whether generation succeeded */
  success: boolean;
  error?: string;
  /** Duration of generation in ms */
  durationMs: number;
}
