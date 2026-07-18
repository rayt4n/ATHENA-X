/**
 * ATHENA-X Stage 16 — Workspace Manager Types
 *
 * Every workspace module has its own manifest (like plugins), registers
 * with the workspace manager, and is movable / resizable / hideable /
 * detachable. Each module maintains its own state independently.
 *
 * Multiple saved layouts let traders switch contexts (Pre-Market →
 * Intraday → Post-Market) with one click instead of rearranging the UI.
 */

// ---------- Module manifest (one per module type) ----------
export type ModuleId =
  | "watchlist"
  | "chart"
  | "orderbook"
  | "optionschain"
  | "news"
  | "tradesetups"
  | "forecast"
  | "dna"
  | "positions"
  | "reports"
  | "marketoverview"
  | "alerts";

export interface ModuleManifest {
  id: ModuleId;
  name: string;
  description: string;
  category: "market_data" | "intelligence" | "trading" | "research" | "ops";
  /** Default size in grid units */
  defaultSize: { w: number; h: number };
  /** Minimum size in grid units */
  minSize: { w: number; h: number };
  /** Maximum size in grid units (0 = unlimited) */
  maxSize?: { w: number; h: number };
  /** Whether this module can be detached (popped out) */
  detachable: boolean;
  /** Whether this module persists its own state */
  stateful: boolean;
  /** Icon name (lucide) */
  icon: string;
  /** Schema version of this manifest */
  schemaVersion: string;
  version: string;
}

// ---------- Layout item (position of a module in a workspace) ----------
export interface LayoutItem {
  /** Unique instance ID (allows multiple instances of same module) */
  instanceId: string;
  moduleId: ModuleId;
  /** Grid position */
  x: number;
  y: number;
  w: number;
  h: number;
  /** Whether the module is currently visible */
  visible: boolean;
  /** Whether the module is detached (popped out) */
  detached: boolean;
  /** Module-specific state (each module owns its own state shape) */
  state: Record<string, unknown>;
}

// ---------- Workspace (a saved layout) ----------
export type WorkspacePreset =
  | "premarket"
  | "marketopen"
  | "intraday"
  | "options"
  | "research"
  | "postmarket"
  | "custom";

export interface Workspace {
  id: string;
  name: string;
  preset: WorkspacePreset;
  /** Grid items in this workspace */
  items: LayoutItem[];
  /** Workspace-level settings */
  settings: WorkspaceSettings;
  createdAt: number;
  updatedAt: number;
  /** Whether this is a built-in preset (cannot be deleted) */
  builtin: boolean;
}

export interface WorkspaceSettings {
  /** Currently selected symbol (e.g. "SPY") */
  selectedSymbol: string;
  /** Selected timeframe (e.g. "1m", "5m", "15m", "1h", "1d") */
  timeframe: string;
  /** Active filters */
  filters: Record<string, string>;
  /** Active watchlist ID */
  watchlistId: string;
}

// ---------- Workspace manager state ----------
export interface WorkspaceManagerState {
  /** All saved workspaces */
  workspaces: Workspace[];
  /** Currently active workspace ID */
  activeWorkspaceId: string;
  /** All registered module manifests */
  registeredModules: ModuleManifest[];
  /** Grid columns (12-column grid) */
  gridCols: number;
  /** Row height in pixels */
  rowHeight: number;
}

// ---------- Module state shapes (each module owns its own) ----------
export interface WatchlistState {
  symbols: string[];
  sortBy: "symbol" | "price" | "change";
  sortOrder: "asc" | "desc";
}

export interface ChartState {
  symbol: string;
  timeframe: string;
  indicators: string[];
  chartType: "candle" | "line" | "area";
}

export interface OptionsChainState {
  symbol: string;
  expiration: string;
  strikeRange: number;
  greekView: "delta" | "gamma" | "theta" | "vega";
}

export interface NewsState {
  filter: "all" | "high" | "medium" | "low";
  sources: string[];
  searchQuery: string;
}

export interface TradeSetupsState {
  filter: "all" | "qualified" | "triggered" | "closed";
  minConfidence: number;
}

export interface ForecastState {
  horizon: "5m" | "15m" | "30m" | "1h" | "eod" | "tomorrow";
  showCalibration: boolean;
}

export interface DNAState {
  selected: string | null;
  showHistory: boolean;
}

export interface PositionsState {
  filter: "all" | "open" | "closed" | "today";
}

export interface ReportsState {
  filter: "all" | "premarket" | "intraday" | "event" | "endofday" | "weekly";
}

export interface MarketOverviewState {
  symbols: string[];
}

export interface AlertsState {
  filter: "all" | "active" | "acknowledged";
  severity: "all" | "critical" | "warning" | "info";
}
