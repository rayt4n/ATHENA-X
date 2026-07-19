"use client";

import { ArrowLeft, Activity } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { FrontendMetric } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  frontend: FrontendMetric[];
  onBack: () => void;
}

export function PerfFrontendPanel({ frontend, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel title="Frontend Performance" subtitle="FP, LCP, TTI, FPS, memory, JS heap, module render time" icon={<Activity className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
        bodyClassName="p-0"
      >
        <div className="max-h-[500px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-3">Metric</div>
            <div className="col-span-2 text-right">Value</div>
            <div className="col-span-2 text-right">Target</div>
            <div className="col-span-3">Description</div>
            <div className="col-span-1 text-right">Bar</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {frontend.map((f) => (
            <div key={f.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-3 font-medium">{f.label}</div>
              <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: f.status === "pass" ? "#34d399" : f.status === "warn" ? "#fbbf24" : "#f87171" }}>{f.value} {f.unit}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{f.target} {f.unit}</div>
              <div className="col-span-3 text-[9.5px] text-muted-foreground/80 truncate">{f.description}</div>
              <div className="col-span-1">
                <div className="h-1.5 rounded-full bg-background/60 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, (f.value / f.target) * 100)}%`, backgroundColor: f.status === "pass" ? "#34d399" : f.status === "warn" ? "#fbbf24" : "#f87171" }} />
                </div>
              </div>
              <div className="col-span-1 flex justify-end"><StatusBadge status={f.status} /></div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Frontend Health" icon={<Activity className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Passing" value={frontend.filter((f) => f.status === "pass").length} unit={`/ ${frontend.length}`} intent="healthy" />
          <Stat label="LCP" value={`${frontend.find((f) => f.id === "lcp")?.value || 0}ms`} intent="healthy" />
          <Stat label="TTI" value={`${frontend.find((f) => f.id === "tti")?.value || 0}ms`} intent="healthy" />
          <Stat label="FPS" value={frontend.find((f) => f.id === "fps")?.value || 0} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          All frontend metrics within Core Web Vitals thresholds. LCP &lt; 2.5s, TTI &lt; 3s, FPS ≥ 55.
        </div>
      </Panel>
    </PanelGrid>
  );
}
