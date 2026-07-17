/**
 * Display formatting helpers for the Validation Dashboard.
 * All numbers are rendered through these so the cockpit has a single
 * source of truth for unit / precision / sign conventions.
 */

export function fmtMs(ms: number): string {
  if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function fmtAge(ms: number): string {
  if (ms < 1000) return `${ms.toFixed(0)}ms ago`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s ago`;
  if (ms < 3_600_000) return `${(ms / 60_000).toFixed(1)}m ago`;
  return `${(ms / 3_600_000).toFixed(1)}h ago`;
}

export function fmtPct(x: number, digits = 1): string {
  return `${(x * 100).toFixed(digits)}%`;
}

export function fmtNum(x: number, digits = 2): string {
  if (!Number.isFinite(x)) return "—";
  return x.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function fmtCompact(x: number): string {
  if (!Number.isFinite(x)) return "—";
  return Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(x);
}

export function fmtPrice(x: number): string {
  return x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function fmtTime(epochMs: number): string {
  return new Date(epochMs).toLocaleTimeString("en-US", { hour12: false });
}

export function fmtClock(epochMs: number): string {
  const d = new Date(epochMs);
  return d.toLocaleTimeString("en-US", { hour12: false }) + "." + String(d.getMilliseconds()).padStart(3, "0");
}

export function healthColor(state: string): string {
  switch (state) {
    case "healthy": return "#34d399";
    case "degraded": return "#fbbf24";
    case "warming": return "#22d3ee";
    case "down": return "#f87171";
    case "critical": return "#f87171";
    default: return "#6b7280";
  }
}

export function healthLabel(state: string): string {
  return state.charAt(0).toUpperCase() + state.slice(1);
}

export function severityRank(s: string): number {
  return s === "critical" ? 3 : s === "warning" ? 2 : 1;
}
