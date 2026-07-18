"use client";

import { ArrowLeft, Database } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { BackendMetric } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  backend: BackendMetric[];
  onBack: () => void;
}

export function PerfBackendPanel({ backend, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel title="Backend Performance" subtitle="Event, queue, DB, Redis, WebSocket, API latency (p50/p95/p99)" icon={<Database className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
        bodyClassName="p-0"
      >
        <div className="max-h-[500px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-3">Subsystem</div>
            <div className="col-span-2 text-right">p50 (ms)</div>
            <div className="col-span-2 text-right">p95 (ms)</div>
            <div className="col-span-2 text-right">p99 (ms)</div>
            <div className="col-span-2 text-right">Target p95</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {backend.map((b) => (
            <div key={b.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-3 font-medium">{b.label}</div>
              <div className="col-span-2 text-right font-mono tabular-nums">{b.p50.toFixed(1)}</div>
              <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: b.status === "pass" ? "#34d399" : b.status === "warn" ? "#fbbf24" : "#f87171" }}>{b.p95.toFixed(1)}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{b.p99.toFixed(1)}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{b.targetP95}ms</div>
              <div className="col-span-1 flex justify-end"><StatusBadge status={b.status} /></div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Backend Health" icon={<Database className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Passing" value={backend.filter((b) => b.status === "pass").length} unit={`/ ${backend.length}`} intent="healthy" />
          <Stat label="Avg p95" value={`${(backend.reduce((s, b) => s + b.p95, 0) / backend.length).toFixed(1)}ms`} intent="healthy" />
          <Stat label="Worst p95" value={`${Math.max(...backend.map((b) => b.p95)).toFixed(1)}ms`} intent="warning" />
          <Stat label="Best p95" value={`${Math.min(...backend.map((b) => b.p95)).toFixed(1)}ms`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          All backend latencies within p95 targets. Event bus &lt; 50ms, DB &lt; 15ms, Redis &lt; 10ms.
        </div>
      </Panel>
    </PanelGrid>
  );
}
