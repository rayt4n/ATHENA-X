"use client";

import { ArrowLeft, TrendingUp } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { ScalabilityMetric } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  scalability: ScalabilityMetric[];
  onBack: () => void;
}

export function PerfScalabilityPanel({ scalability, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel title="Scalability" subtitle="Max plugins / agents / reports / WS clients / symbols / watchlists" icon={<TrendingUp className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
      >
        <div className="space-y-3">
          {scalability.map((s) => (
            <div key={s.id} className="rounded-md border border-border/40 bg-background/30 p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-[12px] font-medium">{s.label}</div>
                <StatusBadge status={s.status} />
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-baseline justify-between mb-1">
                    <span className="text-[20px] font-mono font-bold">{s.current.toLocaleString()}</span>
                    <span className="text-[11px] font-mono text-muted-foreground">/ {s.max.toLocaleString()} {s.unit}</span>
                  </div>
                  <div className="h-2 rounded-full bg-background/60 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${s.utilizationPct}%`, backgroundColor: s.utilizationPct < 80 ? "#34d399" : s.utilizationPct < 95 ? "#fbbf24" : "#f87171" }} />
                  </div>
                  <div className="mt-1 text-[9px] font-mono text-muted-foreground">{s.utilizationPct.toFixed(0)}% utilized · {((s.max - s.current) / Math.max(1, s.current)).toFixed(1)}x headroom</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Scalability Health" icon={<TrendingUp className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Metrics" value={scalability.length} intent="info" />
          <Stat label="Passing" value={scalability.filter((s) => s.status === "pass").length} unit={`/ ${scalability.length}`} intent="healthy" />
          <Stat label="Avg Util" value={`${(scalability.reduce((s, m) => s + m.utilizationPct, 0) / scalability.length).toFixed(0)}%`} intent="healthy" />
          <Stat label="Max Util" value={`${Math.max(...scalability.map((s) => s.utilizationPct)).toFixed(0)}%`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          All scalability metrics under 80% utilization. Platform has significant headroom for growth.
        </div>
      </Panel>
    </PanelGrid>
  );
}
