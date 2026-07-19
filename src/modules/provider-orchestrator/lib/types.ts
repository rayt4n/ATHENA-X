/**
 * ATHENA-X Stage 16A — Provider Orchestrator Types
 *
 * The unified MarketData model that ALL downstream ATHENA-X components
 * consume. Nothing above the Provider Orchestrator knows which provider
 * supplied the data.
 */

// ---------- Unified Market Data Model ----------
export interface MarketData {
  symbol: string;
  timestamp: number;       // epoch ms
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  provider: string;        // internal audit only — never exposed to business logic
  qualityScore: number;    // 0..1 — based on provider reliability + freshness
}

// ---------- Provider Types ----------
export type ProviderMode = "free" | "custom" | "advanced";

export type ProviderType =
  | "rest"
  | "websocket"
  | "scrape"
  | "internal";

export type DataCategory =
  | "quotes"
  | "historical"
  | "news"
  | "macro"
  | "options"
  | "company";

export type HealthState = "connected" | "disconnected" | "degraded" | "warming";

export interface SupportedEndpoint {
  category: DataCategory;
  symbols: string[] | "all";
  rateLimitPerMin: number;
  rateLimitPerDay?: number;
}

export interface ProviderConfig {
  id: string;
  name: string;
  type: ProviderType;
  enabled: boolean;
  priority: number;              // 1 = highest
  health: HealthState;
  latencyMs: number;
  successRate: number;           // 0..1
  rateLimitRemaining: number;
  rateLimitPerMin: number;
  apiKey: string | null;
  apiKeyRequired: boolean;
  heartbeatMs: number;           // ms since last heartbeat
  reconnectCount: number;
  supportedEndpoints: SupportedEndpoint[];
  lastDataTimestamp: number;     // epoch ms of last received data
  qualityScore: number;          // 0..1 — base quality of this provider
  isBuiltin: boolean;            // true for preconfigured providers
  baseUrl: string;
}

// ---------- Routing ----------
export interface RoutingRule {
  id: string;
  category: DataCategory;
  providerIds: string[];         // ordered by priority within this category
  enabled: boolean;
}

export interface RoutingConfig {
  mode: ProviderMode;
  rules: RoutingRule[];
  defaultStack: string[];        // provider IDs in priority order (Free/Custom mode)
}

// ---------- Health Snapshot ----------
export interface HealthSnapshot {
  providerId: string;
  state: HealthState;
  latencyMs: number;
  successRate: number;
  failureRate: number;
  rateLimitRemaining: number;
  rateLimitPerMin: number;
  heartbeatMs: number;
  reconnectCount: number;
  lastDataTimestamp: number;
  dataFreshnessMs: number;       // ms since last data
  consecutiveFailures: number;
  totalRequests: number;
  totalSuccesses: number;
  totalFailures: number;
}

// ---------- Orchestrator State ----------
export interface OrchestratorState {
  mode: ProviderMode;
  providers: ProviderConfig[];
  routingRules: RoutingRule[];
  healthSnapshots: HealthSnapshot[];
  cacheEnabled: boolean;
  cacheTtlMs: number;
  lastUpdated: number;
}

// ---------- Request / Response ----------
export interface DataRequest {
  symbol: string;
  category: DataCategory;
  startTime?: number;
  endTime?: number;
  interval?: string;
}

export interface DataResponse {
  data: MarketData[];
  provider: string;
  fromCache: boolean;
  qualityScore: number;
  responseTimeMs: number;
}

// ---------- Provider Adapter Interface ----------
export interface ProviderAdapter {
  id: string;
  name: string;
  type: ProviderType;
  baseUrl: string;
  apiKeyRequired: boolean;
  supportedEndpoints: SupportedEndpoint[];
  qualityScore: number;
  isBuiltin: boolean;

  /** Test connectivity — returns true if provider is reachable */
  testConnection(apiKey: string | null): Promise<boolean>;

  /** Fetch data from the provider — returns raw provider-specific JSON */
  fetch(request: DataRequest, apiKey: string | null): Promise<unknown>;

  /** Normalize raw provider JSON into unified MarketData */
  normalize(raw: unknown, symbol: string): MarketData[];

  /** Check if this provider supports the given request */
  supports(request: DataRequest): boolean;
}
