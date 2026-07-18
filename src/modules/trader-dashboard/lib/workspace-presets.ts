/**
 * 6 built-in workspace presets. Each preset defines which modules are
 * visible, their positions, and default workspace settings.
 *
 * Traders switch between these with one click — no manual rearranging.
 */

import type { LayoutItem, ModuleId, Workspace, WorkspacePreset } from "./workspace-types";

interface PresetDef {
  preset: WorkspacePreset;
  name: string;
  description: string;
  items: { moduleId: ModuleId; x: number; y: number; w: number; h: number; state?: Record<string, unknown> }[];
  settings: Workspace["settings"];
}

const PRESETS: PresetDef[] = [
  {
    preset: "premarket",
    name: "Pre-Market",
    description: "Overnight summary, news, watchlist, forecast, and trade setups before the open.",
    items: [
      { moduleId: "marketoverview", x: 0, y: 0, w: 12, h: 4 },
      { moduleId: "news", x: 0, y: 4, w: 4, h: 8 },
      { moduleId: "watchlist", x: 4, y: 4, w: 3, h: 8, state: { symbols: ["SPY", "QQQ", "VIX", "ES"], sortBy: "symbol", sortOrder: "asc" } },
      { moduleId: "forecast", x: 7, y: 4, w: 5, h: 8, state: { horizon: "eod", showCalibration: true } },
      { moduleId: "tradesetups", x: 0, y: 12, w: 12, h: 6, state: { filter: "qualified", minConfidence: 0.6 } },
    ],
    settings: { selectedSymbol: "SPY", timeframe: "5m", filters: {}, watchlistId: "default" },
  },
  {
    preset: "marketopen",
    name: "Market Open",
    description: "Chart, order book, trade setups, and positions for the opening bell.",
    items: [
      { moduleId: "chart", x: 0, y: 0, w: 6, h: 10, state: { symbol: "SPY", timeframe: "1m", indicators: ["EMA_20", "VWAP"], chartType: "candle" } },
      { moduleId: "orderbook", x: 6, y: 0, w: 3, h: 10 },
      { moduleId: "tradesetups", x: 9, y: 0, w: 3, h: 10, state: { filter: "qualified", minConfidence: 0.6 } },
      { moduleId: "positions", x: 0, y: 10, w: 6, h: 6 },
      { moduleId: "alerts", x: 6, y: 10, w: 6, h: 6 },
    ],
    settings: { selectedSymbol: "SPY", timeframe: "1m", filters: {}, watchlistId: "default" },
  },
  {
    preset: "intraday",
    name: "Intraday Trading",
    description: "Chart, options chain, DNA confidence, and alerts for active trading.",
    items: [
      { moduleId: "chart", x: 0, y: 0, w: 8, h: 10, state: { symbol: "SPY", timeframe: "5m", indicators: ["EMA_20", "EMA_50", "VWAP"], chartType: "candle" } },
      { moduleId: "dna", x: 8, y: 0, w: 4, h: 10, state: { selected: null, showHistory: false } },
      { moduleId: "optionschain", x: 0, y: 10, w: 8, h: 8, state: { symbol: "SPY", expiration: "2026-07-18", strikeRange: 15, greekView: "delta" } },
      { moduleId: "alerts", x: 8, y: 10, w: 4, h: 8 },
    ],
    settings: { selectedSymbol: "SPY", timeframe: "5m", filters: {}, watchlistId: "default" },
  },
  {
    preset: "options",
    name: "Options Analysis",
    description: "Options chain, forecast, trade setups, and DNA for deep options analysis.",
    items: [
      { moduleId: "optionschain", x: 0, y: 0, w: 8, h: 10, state: { symbol: "SPY", expiration: "2026-07-18", strikeRange: 20, greekView: "delta" } },
      { moduleId: "dna", x: 8, y: 0, w: 4, h: 10, state: { selected: "options", showHistory: true } },
      { moduleId: "forecast", x: 0, y: 10, w: 6, h: 6, state: { horizon: "eod", showCalibration: true } },
      { moduleId: "tradesetups", x: 6, y: 10, w: 6, h: 6, state: { filter: "all", minConfidence: 0.5 } },
    ],
    settings: { selectedSymbol: "SPY", timeframe: "15m", filters: {}, watchlistId: "default" },
  },
  {
    preset: "research",
    name: "Research",
    description: "News, reports, forecast, and watchlist for research and analysis.",
    items: [
      { moduleId: "news", x: 0, y: 0, w: 4, h: 10, state: { filter: "all", sources: [], searchQuery: "" } },
      { moduleId: "reports", x: 4, y: 0, w: 8, h: 10, state: { filter: "all" } },
      { moduleId: "forecast", x: 0, y: 10, w: 6, h: 6, state: { horizon: "tomorrow", showCalibration: true } },
      { moduleId: "watchlist", x: 6, y: 10, w: 6, h: 6, state: { symbols: ["SPY", "QQQ", "VIX"], sortBy: "symbol", sortOrder: "asc" } },
    ],
    settings: { selectedSymbol: "SPY", timeframe: "1d", filters: {}, watchlistId: "default" },
  },
  {
    preset: "postmarket",
    name: "Post-Market Review",
    description: "Reports, positions, DNA confidence, and market overview for end-of-day review.",
    items: [
      { moduleId: "reports", x: 0, y: 0, w: 8, h: 10, state: { filter: "endofday" } },
      { moduleId: "marketoverview", x: 8, y: 0, w: 4, h: 10 },
      { moduleId: "positions", x: 0, y: 10, w: 8, h: 6 },
      { moduleId: "dna", x: 8, y: 10, w: 4, h: 6, state: { selected: null, showHistory: true } },
    ],
    settings: { selectedSymbol: "SPY", timeframe: "1d", filters: {}, watchlistId: "default" },
  },
];

let instanceCounter = 0;
function genInstanceId(moduleId: string): string {
  instanceCounter += 1;
  return `${moduleId}-${instanceCounter}-${Date.now().toString(36)}`;
}

export function buildBuiltinWorkspaces(): Workspace[] {
  const now = Date.now();
  return PRESETS.map((p) => ({
    id: `ws-${p.preset}`,
    name: p.name,
    preset: p.preset,
    items: p.items.map((item) => ({
      instanceId: genInstanceId(item.moduleId),
      moduleId: item.moduleId,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
      visible: true,
      detached: false,
      state: item.state ?? {},
    })) as LayoutItem[],
    settings: p.settings,
    createdAt: now,
    updatedAt: now,
    builtin: true,
  }));
}

export function getPresetNames(): { preset: WorkspacePreset; name: string; description: string }[] {
  return PRESETS.map((p) => ({ preset: p.preset, name: p.name, description: p.description }));
}
