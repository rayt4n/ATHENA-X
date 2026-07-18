"use client";

import type { AlertsState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Alert {
  id: string;
  severity: "critical" | "warning" | "info";
  source: string;
  message: string;
  raisedAt: number;
  acked: boolean;
}

const SAMPLE_ALERTS: Alert[] = [
  { id: "a1", severity: "critical", source: "provider:polygon", message: "Polygon API rate limit hit — failover to Tradier engaged", raisedAt: Date.now() - 120000, acked: false },
  { id: "a2", severity: "warning", source: "agent:opt.greeks", message: "Greeks engine CPU above 70% — throttling", raisedAt: Date.now() - 300000, acked: false },
  { id: "a3", severity: "warning", source: "dna:narrative", message: "Narrative DNA confidence below 65% threshold", raisedAt: Date.now() - 480000, acked: false },
  { id: "a4", severity: "info", source: "report-engine", message: "Pre-Market Report generated successfully", raisedAt: Date.now() - 600000, acked: true },
  { id: "a5", severity: "info", source: "certification", message: "Operational readiness: 99.3% READY", raisedAt: Date.now() - 900000, acked: true },
  { id: "a6", severity: "warning", source: "event-bus", message: "Backlog growing — 500+ events queued", raisedAt: Date.now() - 150000, acked: false },
];

interface Props {
  state: AlertsState;
  onStateChange: (partial: Partial<AlertsState>) => void;
}

export function AlertsModule({ state, onStateChange }: Props) {
  const severity = state.severity ?? "all";
  const filter = state.filter ?? "all";
  const filtered = SAMPLE_ALERTS.filter((a) => {
    if (severity !== "all" && a.severity !== severity) return false;
    if (filter === "active" && a.acked) return false;
    if (filter === "acknowledged" && !a.acked) return false;
    return true;
  });

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center gap-2 flex-wrap">
        <select
          value={severity}
          onChange={(e) => onStateChange({ severity: e.target.value as AlertsState["severity"] })}
          className="bg-background/60 border border-border/40 rounded text-[9px] px-1 py-0.5 font-mono focus:outline-none"
        >
          <option value="all">all severity</option>
          <option value="critical">critical</option>
          <option value="warning">warning</option>
          <option value="info">info</option>
        </select>
        <div className="flex gap-0.5">
          {["all", "active", "acknowledged"].map((f) => (
            <button
              key={f}
              onClick={() => onStateChange({ filter: f as AlertsState["filter"] })}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${filter === f ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto scroll-thin">
        {filtered.map((a) => {
          const color = a.severity === "critical" ? "#f87171" : a.severity === "warning" ? "#fbbf24" : "#22d3ee";
          return (
            <div key={a.id} className="px-3 py-2 border-b border-border/20 hover:bg-accent/30">
              <div className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 pulse-live" style={{ backgroundColor: color }} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[9px] font-mono uppercase tracking-wider" style={{ color }}>{a.source}</span>
                    <span className="text-[8.5px] font-mono text-muted-foreground/60">{new Date(a.raisedAt).toLocaleTimeString("en-US", { hour12: false })}</span>
                  </div>
                  <div className="text-[11px] leading-snug mt-0.5">{a.message}</div>
                  {a.acked && <span className="text-[8px] font-mono text-muted-foreground/50 mt-0.5 inline-block">✓ acknowledged</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
