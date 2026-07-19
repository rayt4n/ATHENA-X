/**
 * ATHENA-X API Client
 *
 * Single source of truth for all backend calls. Every widget consumes
 * these functions — no fetch() calls elsewhere in the codebase.
 *
 * All endpoints are served by the Trading Workspace server (port 8010)
 * which mounts the Institutional Workspace (Stage 16.3) and Plugin
 * Validation Workspace (Stage 16.5) routers.
 *
 * NO MOCK DATA. NO PLACEHOLDER VALUES. Every function hits a real endpoint.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8010";

// ============================================================================
// Types — mirror the Python dataclasses / pydantic models
// ============================================================================

export interface Instrument {
  symbol: string;
  name: string;
  category: string;
  yahoo_symbol: string;
}

export interface LiveStatus {
  market_session: string;
  connection_health: string;
  provider_health: Record<string, string>;
  agents_online: number;
  agents_total: number;
}

export interface InstrumentsResponse {
  instruments: Instrument[];
  live_status: LiveStatus;
}

export interface MarketWidget {
  id: string;
  name: string;
  plugin: string;
  status: "VERIFIED" | "PROVISIONAL" | "NEEDS IMPROVEMENT" | "PLANNED" | "CERTIFIED";
  data: Record<string, unknown>;
}

export interface MarketOverviewResponse {
  widgets: MarketWidget[];
}

export interface Bar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OverlayData {
  indicator?: string;
  value: number | string | Record<string, unknown> | null;
  confidence?: number | null;
  error?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ChartResponse {
  symbol: string;
  timeframe: string;
  bars: Bar[];
  overlays: Record<string, OverlayData>;
  timeframes_available: string[];
}

export interface InstitutionalWidget {
  id: string;
  name: string;
  plugin: string;
  status: string;
  data: Record<string, unknown>;
}

export interface InstitutionalResponse {
  widgets: InstitutionalWidget[];
}

export interface EvidenceContributor {
  agent_id: string;
  layer: number;
  confidence: number;
  output: string;
  reason: string;
}

export interface EvidenceResponse {
  request_id: string;
  final_conclusion: string;
  primary_contributors: EvidenceContributor[];
  supporting_contributors: EvidenceContributor[];
  contextual_contributors: EvidenceContributor[];
  conflicting_evidence: EvidenceContributor[];
  historical_accuracy: Record<string, string>;
}

export interface AIForecastResponse {
  bias: { bull: number; neutral: number; bear: number };
  probability_tree: Record<string, { probability: number; target: number; condition: string }>;
  expected_range: { low: number; mid: number; high: number; confidence: number };
  expected_volatility: { atr_14: number; iv_rank: number; regime: string };
  projections: Record<string, { direction: string; expected_change: string; confidence: number }>;
  source: string;
}

export interface ReportSection {
  id: string;
  title: string;
  source: string;
  content: string;
}

export interface ReportResponse {
  generated_at: string;
  symbol: string;
  sections: ReportSection[];
}

export interface PluginStatus {
  name: string;
  version: string;
  exec_time_ms: number;
  status: string;
  certification: "CERTIFIED" | "PROVISIONAL" | "NEEDS IMPROVEMENT";
}

export interface PluginStatusResponse {
  plugins: PluginStatus[];
  summary: {
    total: number;
    certified: number;
    provisional: number;
    needs_improvement: number;
  };
}

// ============================================================================
// API functions — each maps to one backend endpoint
// ============================================================================

async function fetchAPI<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

/** GET /trading/instruments — Top bar instruments + live status */
export async function getInstruments(): Promise<InstrumentsResponse> {
  return fetchAPI<InstrumentsResponse>("/trading/instruments");
}

/** GET /trading/market-overview — Left panel market overview widgets */
export async function getMarketOverview(): Promise<MarketOverviewResponse> {
  return fetchAPI<MarketOverviewResponse>("/trading/market-overview");
}

/** GET /trading/chart/{symbol}?timeframe={tf} — Center chart + 17 overlays */
export async function getChart(symbol: string, timeframe: string): Promise<ChartResponse> {
  return fetchAPI<ChartResponse>(`/trading/chart/${symbol}?timeframe=${timeframe}`);
}

/** GET /trading/institutional — Right panel institutional intelligence */
export async function getInstitutional(): Promise<InstitutionalResponse> {
  return fetchAPI<InstitutionalResponse>("/trading/institutional");
}

/** GET /trading/evidence/{request_id} — Bottom panel evidence engine */
export async function getEvidence(requestId: string = "demo"): Promise<EvidenceResponse> {
  return fetchAPI<EvidenceResponse>(`/trading/evidence/${requestId}`);
}

/** GET /trading/ai-forecast — AI panel forecast */
export async function getAIForecast(): Promise<AIForecastResponse> {
  return fetchAPI<AIForecastResponse>("/trading/ai-forecast");
}

/** GET /trading/report — 11-section institutional report */
export async function getReport(): Promise<ReportResponse> {
  return fetchAPI<ReportResponse>("/trading/report");
}

/** GET /trading/plugin-status — Plugin validation certification table */
export async function getPluginStatus(): Promise<PluginStatusResponse> {
  return fetchAPI<PluginStatusResponse>("/trading/plugin-status");
}

/** GET /workspace/components — All runtime agents (for technical panel) */
export async function getWorkspaceComponents(): Promise<{ components: unknown[]; total: number }> {
  return fetchAPI<{ components: unknown[]; total: number }>("/workspace/components");
}

/** GET /validation/certification — Full certification table */
export async function getCertification(): Promise<{ certification_table: unknown[]; summary: unknown }> {
  return fetchAPI<{ certification_table: unknown[]; summary: unknown }>("/validation/certification");
}

// ============================================================================
// React Query hooks — every widget uses these. No raw fetch() elsewhere.
// ============================================================================

import { useQuery } from "@tanstack/react-query";

export const QUERY_KEYS = {
  instruments: ["instruments"] as const,
  marketOverview: ["market-overview"] as const,
  chart: (symbol: string, tf: string) => ["chart", symbol, tf] as const,
  institutional: ["institutional"] as const,
  evidence: (id: string) => ["evidence", id] as const,
  aiForecast: ["ai-forecast"] as const,
  report: ["report"] as const,
  pluginStatus: ["plugin-status"] as const,
  workspaceComponents: ["workspace-components"] as const,
  certification: ["certification"] as const,
};

// Refresh intervals (ms)
export const REFRESH = {
  instruments: 30_000,       // 30s — top bar
  marketOverview: 60_000,    // 60s — left panel
  chart: 15_000,             // 15s — center chart
  institutional: 30_000,     // 30s — right panel
  evidence: 30_000,          // 30s — bottom panel
  aiForecast: 60_000,        // 60s — AI panel
  report: 120_000,           // 2min — report
  pluginStatus: 120_000,     // 2min — plugin status
};

export function useInstruments() {
  return useQuery({
    queryKey: QUERY_KEYS.instruments,
    queryFn: getInstruments,
    refetchInterval: REFRESH.instruments,
    staleTime: 10_000,
  });
}

export function useMarketOverview() {
  return useQuery({
    queryKey: QUERY_KEYS.marketOverview,
    queryFn: getMarketOverview,
    refetchInterval: REFRESH.marketOverview,
    staleTime: 30_000,
  });
}

export function useChart(symbol: string, timeframe: string) {
  return useQuery({
    queryKey: QUERY_KEYS.chart(symbol, timeframe),
    queryFn: () => getChart(symbol, timeframe),
    refetchInterval: REFRESH.chart,
    staleTime: 10_000,
  });
}

export function useInstitutional() {
  return useQuery({
    queryKey: QUERY_KEYS.institutional,
    queryFn: getInstitutional,
    refetchInterval: REFRESH.institutional,
    staleTime: 15_000,
  });
}

export function useEvidence(requestId: string = "demo") {
  return useQuery({
    queryKey: QUERY_KEYS.evidence(requestId),
    queryFn: () => getEvidence(requestId),
    refetchInterval: REFRESH.evidence,
    staleTime: 15_000,
  });
}

export function useAIForecast() {
  return useQuery({
    queryKey: QUERY_KEYS.aiForecast,
    queryFn: getAIForecast,
    refetchInterval: REFRESH.aiForecast,
    staleTime: 30_000,
  });
}

export function useReport() {
  return useQuery({
    queryKey: QUERY_KEYS.report,
    queryFn: getReport,
    refetchInterval: REFRESH.report,
    staleTime: 60_000,
  });
}

export function usePluginStatus() {
  return useQuery({
    queryKey: QUERY_KEYS.pluginStatus,
    queryFn: getPluginStatus,
    refetchInterval: REFRESH.pluginStatus,
    staleTime: 60_000,
  });
}

export function useWorkspaceComponents() {
  return useQuery({
    queryKey: QUERY_KEYS.workspaceComponents,
    queryFn: getWorkspaceComponents,
    staleTime: 60_000,
  });
}

export function useCertification() {
  return useQuery({
    queryKey: QUERY_KEYS.certification,
    queryFn: getCertification,
    staleTime: 60_000,
  });
}
