"use client";

import { Layers, CheckCircle2, AlertTriangle } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { StatusDot } from "../status-dot";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { OptionsAccuracyCheck } from "@/modules/engineering-console/lib/types";

const CHECK_LABELS: Record<OptionsAccuracyCheck["check"], string> = {
  iv_surface_smoothness: "IV Surface Smoothness",
  greeks_parity: "Greeks Parity (Δ+Γ)",
  put_call_arbitrage: "Put/Call Arbitrage",
  vol_smile_curvature: "Vol Smile Curvature",
  delta_hedge_drift: "Delta-Hedge Drift",
};

export function OptionsAccuracyPanel({ checks }: { checks: OptionsAccuracyCheck[] }) {
  const healthy = checks.filter((c) => c.state === "healthy").length;
  const degraded = checks.filter((c) => c.state === "degraded").length;
  const critical = checks.filter((c) => c.state === "critical").length;

  return (
    <PanelGrid>
      <Panel
        title="Options Data Accuracy"
        subtitle="Surface parity, arbitrage, smile & hedge drift"
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-9"
        actions={
          <div className="flex items-center gap-2">
            {critical > 0 && (
              <span className="flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-critical/10 border border-status-critical/30" style={{ color: "#f87171" }}>
                <AlertTriangle className="h-3 w-3" />{critical} critical
              </span>
            )}
            {degraded > 0 && (
              <span className="flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-warning/10 border border-status-warning/30" style={{ color: "#fbbf24" }}>
                <AlertTriangle className="h-3 w-3" />{degraded} warn
              </span>
            )}
            <span className="flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-healthy/10 border border-status-healthy/30" style={{ color: "#34d399" }}>
              <CheckCircle2 className="h-3 w-3" />{healthy} pass
            </span>
          </div>
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[460px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-4 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-2">Symbol</div>
            <div className="col-span-3">Check</div>
            <div className="col-span-3">Detail</div>
            <div className="col-span-1 text-right">Value</div>
            <div className="col-span-1 text-right">Thresh</div>
            <div className="col-span-1 text-right">Last</div>
            <div className="col-span-1 text-right">State</div>
          </div>
          {checks.map((c) => {
            const ratio = c.value / c.threshold;
            return (
              <div key={c.id} className="grid grid-cols-12 px-4 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
                <div className="col-span-2 font-mono font-semibold">{c.symbol}</div>
                <div className="col-span-3 font-mono text-muted-foreground truncate">{CHECK_LABELS[c.check]}</div>
                <div className="col-span-3 text-[10px] text-muted-foreground/80 truncate">{c.detail}</div>
                <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: ratio > 1 ? "#f87171" : ratio > 0.8 ? "#fbbf24" : "var(--foreground)" }}>
                  {c.value.toFixed(4)}
                </div>
                <div className="col-span-1 text-right font-mono tabular-nums text-muted-foreground">{c.threshold.toFixed(4)}</div>
                <div className="col-span-1 text-right font-mono tabular-nums text-[9.5px] text-muted-foreground">{fmtAge(Date.now() - c.lastCheck)}</div>
                <div className="col-span-1 flex justify-end">
                  <StatusDot state={c.state} pulse={c.state === "healthy"} />
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="Options Health Summary"
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-3"
      >
        <div className="space-y-3">
          <Stat label="Pass Rate" value={`${((healthy / checks.length) * 100).toFixed(1)}%`} intent={healthy / checks.length > 0.85 ? "healthy" : "warning"} />
          <Stat label="Critical" value={critical} intent={critical > 0 ? "critical" : "healthy"} />
          <Stat label="Warning" value={degraded} intent={degraded > 0 ? "warning" : "healthy"} />
          <Stat label="Avg Last Check" value={fmtAge(checks.reduce((s, c) => s + (Date.now() - c.lastCheck), 0) / checks.length)} />

          <div className="pt-3 mt-3 border-t border-border/40">
            <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Checks by type</div>
            <div className="space-y-1">
              {(Object.keys(CHECK_LABELS) as OptionsAccuracyCheck["check"][]).map((k) => {
                const items = checks.filter((c) => c.check === k);
                if (items.length === 0) return null;
                const h = items.filter((c) => c.state === "healthy").length;
                return (
                  <div key={k} className="flex items-center justify-between text-[10.5px] font-mono">
                    <span className="truncate text-muted-foreground">{CHECK_LABELS[k].split(" ")[0]}</span>
                    <span style={{ color: h === items.length ? "#34d399" : "#fbbf24" }}>{h}/{items.length}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
