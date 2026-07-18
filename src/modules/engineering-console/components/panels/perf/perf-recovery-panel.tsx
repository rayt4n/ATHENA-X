"use client";

import { ArrowLeft, RotateCcw } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { RecoveryMetric } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  recovery: RecoveryMetric[];
  onBack: () => void;
}

export function PerfRecoveryPanel({ recovery, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel title="Recovery Certification" subtitle="MTTR, recovery %, lost events, replay success" icon={<RotateCcw className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
        bodyClassName="p-0"
      >
        <div className="divide-y divide-border/30">
          {recovery.map((r) => (
            <div key={r.id} className="px-4 py-3 flex items-center justify-between">
              <div>
                <div className="text-[12px] font-medium">{r.label}</div>
                <div className="text-[10px] text-muted-foreground/70">target: {r.target} {r.unit}</div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-[18px] font-mono font-bold" style={{ color: r.status === "pass" ? "#34d399" : r.status === "warn" ? "#fbbf24" : "#f87171" }}>
                    {r.value} {r.unit}
                  </div>
                </div>
                <StatusBadge status={r.status} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Recovery Health" icon={<RotateCcw className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Passing" value={recovery.filter((r) => r.status === "pass").length} unit={`/ ${recovery.length}`} intent="healthy" />
          <Stat label="MTTR" value={`${recovery.find((r) => r.id === "mttr")?.value || 0}m`} intent="healthy" />
          <Stat label="Recovery %" value={`${recovery.find((r) => r.id === "recovery_pct")?.value || 0}%`} intent="healthy" />
          <Stat label="Replay" value={`${recovery.find((r) => r.id === "replay_success")?.value || 0}%`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          MTTR under 6 minutes. Recovery rate above 99%. Replay success above 99%. Zero lost events in last 24h.
        </div>
      </Panel>
    </PanelGrid>
  );
}
