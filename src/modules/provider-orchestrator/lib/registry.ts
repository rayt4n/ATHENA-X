/**
 * Provider Registry — manages provider configuration.
 *
 * Mode-aware:
 *   Free    — preconfigured stack, user cannot edit
 *   Custom  — user can enable/disable/reorder Tier 1 providers
 *   Advanced — user can add/remove providers and create routing rules
 */

import type { ProviderConfig, ProviderMode, RoutingRule, DataCategory } from "./types";

const STORAGE_KEY = "athena-x-providers-v1";

// ---------- Default provider configurations ----------
const DEFAULT_PROVIDERS: ProviderConfig[] = [
  {
    id: "yahoo",
    name: "Yahoo Finance",
    type: "scrape",
    enabled: true,
    priority: 1,
    health: "disconnected",
    latencyMs: 0,
    successRate: 0,
    rateLimitRemaining: 0,
    rateLimitPerMin: 60,
    apiKey: null,
    apiKeyRequired: false,
    heartbeatMs: 0,
    reconnectCount: 0,
    supportedEndpoints: [
      { category: "quotes", symbols: "all", rateLimitPerMin: 60 },
      { category: "historical", symbols: "all", rateLimitPerMin: 60 },
    ],
    lastDataTimestamp: 0,
    qualityScore: 0.70,
    isBuiltin: true,
    baseUrl: "https://query1.finance.yahoo.com",
  },
  {
    id: "finnhub",
    name: "Finnhub",
    type: "rest",
    enabled: true,
    priority: 2,
    health: "disconnected",
    latencyMs: 0,
    successRate: 0,
    rateLimitRemaining: 0,
    rateLimitPerMin: 60,
    apiKey: null,
    apiKeyRequired: true,
    heartbeatMs: 0,
    reconnectCount: 0,
    supportedEndpoints: [
      { category: "quotes", symbols: "all", rateLimitPerMin: 60 },
      { category: "news", symbols: "all", rateLimitPerMin: 60 },
      { category: "company", symbols: "all", rateLimitPerMin: 60 },
    ],
    lastDataTimestamp: 0,
    qualityScore: 0.80,
    isBuiltin: true,
    baseUrl: "https://finnhub.io/api/v1",
  },
  {
    id: "twelvedata",
    name: "Twelve Data",
    type: "rest",
    enabled: true,
    priority: 3,
    health: "disconnected",
    latencyMs: 0,
    successRate: 0,
    rateLimitRemaining: 0,
    rateLimitPerMin: 8,
    apiKey: null,
    apiKeyRequired: true,
    heartbeatMs: 0,
    reconnectCount: 0,
    supportedEndpoints: [
      { category: "quotes", symbols: "all", rateLimitPerMin: 8 },
      { category: "historical", symbols: "all", rateLimitPerMin: 8 },
      { category: "macro", symbols: "all", rateLimitPerMin: 8 },
    ],
    lastDataTimestamp: 0,
    qualityScore: 0.82,
    isBuiltin: true,
    baseUrl: "https://api.twelvedata.com",
  },
  {
    id: "fmp",
    name: "Financial Modeling Prep",
    type: "rest",
    enabled: true,
    priority: 4,
    health: "disconnected",
    latencyMs: 0,
    successRate: 0,
    rateLimitRemaining: 0,
    rateLimitPerMin: 30,
    apiKey: null,
    apiKeyRequired: true,
    heartbeatMs: 0,
    reconnectCount: 0,
    supportedEndpoints: [
      { category: "quotes", symbols: "all", rateLimitPerMin: 30 },
      { category: "historical", symbols: "all", rateLimitPerMin: 30 },
      { category: "company", symbols: "all", rateLimitPerMin: 30 },
    ],
    lastDataTimestamp: 0,
    qualityScore: 0.78,
    isBuiltin: true,
    baseUrl: "https://financialmodelingprep.com/api/v3",
  },
  {
    id: "fred",
    name: "FRED (St. Louis Fed)",
    type: "rest",
    enabled: true,
    priority: 5,
    health: "disconnected",
    latencyMs: 0,
    successRate: 0,
    rateLimitRemaining: 0,
    rateLimitPerMin: 120,
    apiKey: null,
    apiKeyRequired: true,
    heartbeatMs: 0,
    reconnectCount: 0,
    supportedEndpoints: [
      { category: "macro", symbols: "all", rateLimitPerMin: 120 },
    ],
    lastDataTimestamp: 0,
    qualityScore: 0.90,
    isBuiltin: true,
    baseUrl: "https://api.stlouisfed.org/fred",
  },
  {
    id: "cache",
    name: "Internal Cache",
    type: "internal",
    enabled: true,
    priority: 99,
    health: "connected",
    latencyMs: 0,
    successRate: 1.0,
    rateLimitRemaining: 999999,
    rateLimitPerMin: 999999,
    apiKey: null,
    apiKeyRequired: false,
    heartbeatMs: 0,
    reconnectCount: 0,
    supportedEndpoints: [
      { category: "quotes", symbols: "all", rateLimitPerMin: 999999 },
      { category: "historical", symbols: "all", rateLimitPerMin: 999999 },
      { category: "news", symbols: "all", rateLimitPerMin: 999999 },
      { category: "macro", symbols: "all", rateLimitPerMin: 999999 },
      { category: "options", symbols: "all", rateLimitPerMin: 999999 },
      { category: "company", symbols: "all", rateLimitPerMin: 999999 },
    ],
    lastDataTimestamp: 0,
    qualityScore: 0.50,
    isBuiltin: true,
    baseUrl: "internal://cache",
  },
];

const DEFAULT_ROUTING_RULES: RoutingRule[] = [
  { id: "rule-quotes", category: "quotes", providerIds: ["yahoo", "finnhub", "twelvedata", "fmp", "cache"], enabled: true },
  { id: "rule-historical", category: "historical", providerIds: ["yahoo", "twelvedata", "fmp", "cache"], enabled: true },
  { id: "rule-news", category: "news", providerIds: ["finnhub", "cache"], enabled: true },
  { id: "rule-macro", category: "macro", providerIds: ["fred", "twelvedata", "cache"], enabled: true },
  { id: "rule-company", category: "company", providerIds: ["finnhub", "fmp", "cache"], enabled: true },
];

// ---------- Registry state ----------
interface RegistryState {
  mode: ProviderMode;
  providers: ProviderConfig[];
  routingRules: RoutingRule[];
}

function loadState(): RegistryState {
  if (typeof window === "undefined") {
    return { mode: "free", providers: DEFAULT_PROVIDERS, routingRules: DEFAULT_ROUTING_RULES };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { mode: "free", providers: DEFAULT_PROVIDERS, routingRules: DEFAULT_ROUTING_RULES };
    const parsed = JSON.parse(raw) as RegistryState;
    // Always merge with defaults to pick up new fields
    const customProviders = parsed.providers.filter((p) => !p.isBuiltin);
    const builtinProviders = DEFAULT_PROVIDERS.map((dp) => {
      const existing = parsed.providers.find((p) => p.id === dp.id);
      return existing ? { ...dp, ...existing, isBuiltin: true } : dp;
    });
    return {
      mode: parsed.mode ?? "free",
      providers: [...builtinProviders, ...customProviders],
      routingRules: parsed.routingRules ?? DEFAULT_ROUTING_RULES,
    };
  } catch {
    return { mode: "free", providers: DEFAULT_PROVIDERS, routingRules: DEFAULT_ROUTING_RULES };
  }
}

function saveState(state: RegistryState): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // localStorage may be full — ignore
  }
}

// ---------- Public API ----------
export function getProviders(): ProviderConfig[] {
  return loadState().providers;
}

export function getProvider(id: string): ProviderConfig | null {
  return loadState().providers.find((p) => p.id === id) ?? null;
}

export function getMode(): ProviderMode {
  return loadState().mode;
}

export function getRoutingRules(): RoutingRule[] {
  return loadState().routingRules;
}

export function setMode(mode: ProviderMode): void {
  const state = loadState();
  state.mode = mode;
  saveState(state);
}

export function addProvider(config: Omit<ProviderConfig, "isBuiltin">): ProviderConfig {
  const state = loadState();
  const newProvider: ProviderConfig = { ...config, isBuiltin: false };
  state.providers.push(newProvider);
  saveState(state);
  return newProvider;
}

export function removeProvider(id: string): void {
  const state = loadState();
  state.providers = state.providers.filter((p) => p.id !== id || p.isBuiltin);
  state.routingRules.forEach((rule) => {
    rule.providerIds = rule.providerIds.filter((pid) => pid !== id);
  });
  saveState(state);
}

export function updateProvider(id: string, updates: Partial<ProviderConfig>): void {
  const state = loadState();
  state.providers = state.providers.map((p) =>
    p.id === id && !p.isBuiltin ? { ...p, ...updates } : p
  );
  // For builtin providers, only allow enabling/disabling and API key changes
  state.providers = state.providers.map((p) =>
    p.id === id && p.isBuiltin ? { ...p, enabled: updates.enabled ?? p.enabled, apiKey: updates.apiKey ?? p.apiKey } : p
  );
  saveState(state);
}

export function reorderProviders(orderedIds: string[]): void {
  const state = loadState();
  state.providers = state.providers.map((p) => {
    const newPriority = orderedIds.indexOf(p.id) + 1;
    return newPriority > 0 ? { ...p, priority: newPriority } : p;
  });
  saveState(state);
}

export function updateRoutingRule(ruleId: string, updates: Partial<RoutingRule>): void {
  const state = loadState();
  state.routingRules = state.routingRules.map((r) =>
    r.id === ruleId ? { ...r, ...updates } : r
  );
  saveState(state);
}

export function addRoutingRule(category: DataCategory, providerIds: string[]): RoutingRule {
  const state = loadState();
  const newRule: RoutingRule = {
    id: `rule-${category}-${Date.now().toString(36)}`,
    category,
    providerIds,
    enabled: true,
  };
  state.routingRules.push(newRule);
  saveState(state);
  return newRule;
}

export function removeRoutingRule(ruleId: string): void {
  const state = loadState();
  state.routingRules = state.routingRules.filter((r) => r.id !== ruleId);
  saveState(state);
}

export function resetToDefaults(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(STORAGE_KEY);
  }
}

export { DEFAULT_PROVIDERS, DEFAULT_ROUTING_RULES };
