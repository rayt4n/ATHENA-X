"use client";

import { ArrowLeft, Clock } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { StartupMetric } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  startup: StartupMetric[];
  onBack: () => void;
}

export function PerfStartupPanel({ startup, onBack }: Props) {
  const allPass = startup.every((s) => s.status === "pass");
  const coldTotal = startup.reduce((s, m) => s + m.coldMs, 0);
  const warmTotal = startup.reduce((s, m) => s + m.warmMs, 0);

  return (
    <PanelGrid>
      <Panel
        title="Startup Certification"
        subtitle={`${startup.length} startup phases · cold ${coldTotal}ms · warm ${warmTotal}ms`}
        icon={<Clock className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-9"
        actions={
          <button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="h-3 w-3" /> back
          </button>
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[500px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-4">Phase</div>
            <div className="col-span-2 text-right">Cold (ms)</div>
            <div className="col-span-2 text-right">Warm (ms)</div>
            <div className="col-span-2 text-right">Target (ms)</div>
            <div className="col-span-1 text-right">Cold Bar</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {startup.map((s) => (
            <div key={s.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-4 font-medium">{s.label}</div>
              <div className="col-span-2 text-right font-mono tabular-nums">{s.coldMs}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{s.warmMs}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{s.targetMs}</div>
              <div className="col-span-1">
                <div className="h-1.5 rounded-full bg-background/60 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, (s.coldMs / s.targetMs) * 100)}%`, backgroundColor: s.status === "pass" ? "#34d399" : s.status === "warn" ? "#fbbf24" : "#f87171" }} />
                </div>
              </div>
              <div className="col-span-1 flex justify-end"><StatusBadge status={s.status} /></div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Startup Health" icon={<Clock className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Cold Total" value={`${coldTotal}ms`} intent={coldTotal < 25000 ? "healthy" : "warning"} />
          <Stat label="Warm Total" value={`${warmTotal}ms`} intent="healthy" />
          <Stat label="Phases" value={startup.length} intent="info" />
          <Stat label="Passing" value={startup.filter((s) => s.status === "pass").length} unit={`/ ${startup.length}`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          {allPass ? "All startup phases within target. Cold boot completes in under 25s; warm boot under 12s." : "Some phases exceeding target — investigate slowest phases."}
        </div>
      </Panel>
    </PanelGrid>
  );
}
