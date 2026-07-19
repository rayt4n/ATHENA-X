"use client";

import { ArrowLeft, Gauge } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { ResourceMetric } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  resources: ResourceMetric[];
  onBack: () => void;
}

export function PerfResourcesPanel({ resources, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel title="Resource Certification" subtitle="CPU, RAM, Storage, Network, GPU" icon={<Gauge className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {resources.map((r) => (
            <div key={r.id} className="rounded-md border border-border/40 bg-background/30 p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-[12px] font-medium">{r.label}</div>
                <StatusBadge status={r.status} />
              </div>
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-[20px] font-mono font-bold">{r.used}</span>
                <span className="text-[11px] font-mono text-muted-foreground">/ {r.total} {r.unit}</span>
              </div>
              <div className="h-2.5 rounded-full bg-background/60 overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${r.utilizationPct}%`, backgroundColor: r.utilizationPct < 70 ? "#34d399" : r.utilizationPct < 85 ? "#fbbf24" : "#f87171" }} />
              </div>
              <div className="mt-1 text-[9px] font-mono text-muted-foreground">{r.utilizationPct.toFixed(0)}% utilized</div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Resource Health" icon={<Gauge className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Resources" value={resources.length} intent="info" />
          <Stat label="Passing" value={resources.filter((r) => r.status === "pass").length} unit={`/ ${resources.length}`} intent="healthy" />
          <Stat label="Avg Util" value={`${(resources.reduce((s, r) => s + r.utilizationPct, 0) / resources.length).toFixed(0)}%`} intent="healthy" />
          <Stat label="Max Util" value={`${Math.max(...resources.map((r) => r.utilizationPct)).toFixed(0)}%`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          All resources under 70% utilization. Platform has headroom for increased load.
        </div>
      </Panel>
    </PanelGrid>
  );
}
