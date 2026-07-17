"use client";

import { Layers, CheckCircle2, AlertTriangle } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { StatusDot } from "../status-dot";
import { fmtAge, fmtPct } from "@/modules/engineering-console/lib/format";
import type { TechnicalIndicatorCheck } from "@/modules/engineering-console/lib/types";

export function TAAccuracyPanel({ checks }: { checks: TechnicalIndicatorCheck[] }) {
  const healthy = checks.filter((c) => c.state === "healthy").length;
  const degraded = checks.filter((c) => c.state === "degraded").length;
  const maxDrift = Math.max(...checks.map((c) => Math.abs(c.drift)));

  return (
    <PanelGrid>
      <Panel
        title="Technical Indicator Accuracy"
        subtitle="Recomputed vs benchmark — drift detection"
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-9"
        actions={
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-healthy/10 border border-status-healthy/30" style={{ color: "#34d399" }}>
              <CheckCircle2 className="h-3 w-3" />{healthy} pass
            </span>
            {degraded > 0 && (
              <span className="flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-warning/10 border border-status-warning/30" style={{ color: "#fbbf24" }}>
                <AlertTriangle className="h-3 w-3" />{degraded} drift
              </span>
            )}
          </div>
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[460px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-4 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-2">Symbol</div>
            <div className="col-span-3">Indicator</div>
            <div className="col-span-1">TF</div>
            <div className="col-span-2 text-right">Computed</div>
            <div className="col-span-2 text-right">Benchmark</div>
            <div className="col-span-1 text-right">Drift</div>
            <div className="col-span-1 text-right">State</div>
          </div>
          {checks.map((c) => (
            <div key={c.id} className="grid grid-cols-12 px-4 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-2 font-mono font-semibold">{c.symbol}</div>
              <div className="col-span-3 font-mono text-muted-foreground truncate">{c.indicator}</div>
              <div className="col-span-1 font-mono text-[10px] text-muted-foreground">{c.timeframe}</div>
              <div className="col-span-2 text-right font-mono tabular-nums">{c.computed.toFixed(4)}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{c.benchmark.toFixed(4)}</div>
              <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: Math.abs(c.drift) > 0.015 ? "#fbbf24" : "#34d399" }}>
                {(c.drift * 100).toFixed(2)}%
              </div>
              <div className="col-span-1 flex justify-end">
                <StatusDot state={c.state} pulse={c.state === "healthy"} />
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="TA Validation Summary"
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-3"
      >
        <div className="space-y-3">
          <Stat label="Pass Rate" value={fmtPct(healthy / checks.length, 1)} intent={healthy / checks.length > 0.85 ? "healthy" : "warning"} />
          <Stat label="Drift Checks" value={degraded} unit="flagged" intent={degraded > 0 ? "warning" : "healthy"} />
          <Stat label="Max Drift" value={fmtPct(maxDrift, 3)} intent={maxDrift > 0.015 ? "warning" : "healthy"} />
          <Stat label="Avg Last Validation" value={fmtAge(checks.reduce((s, c) => s + (Date.now() - c.lastValidation), 0) / checks.length)} />

          <div className="pt-3 mt-3 border-t border-border/40">
            <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Validators in use</div>
            <div className="space-y-1">
              {Array.from(new Set(checks.map((c) => c.validator))).map((v) => {
                const count = checks.filter((c) => c.validator === v).length;
                return (
                  <div key={v} className="flex items-center justify-between text-[10.5px] font-mono">
                    <span className="truncate text-muted-foreground">{v}</span>
                    <span className="text-foreground">{count}</span>
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
