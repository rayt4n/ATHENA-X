/**
 * Color constants for dashboard charts.
 *
 * Recharts / SVG presentation attributes (stroke, fill) do NOT resolve CSS
 * variables when set as attributes — `stroke="var(--status-info)"` produces
 * a computed stroke of "none". So chart components must use these literal
 * color values.
 *
 * Keep these in sync with the CSS variables in globals.css.
 */

export const STATUS_COLORS = {
  healthy: "#34d399",  // emerald-400
  warning: "#fbbf24",  // amber-400
  critical: "#f87171", // red-400
  info: "#22d3ee",     // cyan-400
  muted: "#6b7280",    // gray-500
} as const;

export const DNA_COLORS: Record<string, string> = {
  technical: "#22d3ee",  // cyan
  options: "#a78bfa",    // violet
  market: "#34d399",     // emerald
  narrative: "#fbbf24",  // amber
  forecast: "#10b981",   // emerald-500
  trade: "#06b6d4",      // cyan-500
  operations: "#f87171", // red
};

export const CHART_COLORS = {
  ...STATUS_COLORS,
  chart1: "#22d3ee",
  chart2: "#34d399",
  chart3: "#fbbf24",
  chart4: "#a78bfa",
  chart5: "#f87171",
};

export function healthColorValue(state: string): string {
  switch (state) {
    case "healthy": return STATUS_COLORS.healthy;
    case "degraded": return STATUS_COLORS.warning;
    case "warming": return STATUS_COLORS.info;
    case "down": return STATUS_COLORS.critical;
    case "critical": return STATUS_COLORS.critical;
    default: return STATUS_COLORS.muted;
  }
}
