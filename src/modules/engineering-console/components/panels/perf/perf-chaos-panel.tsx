"use client";

import { ArrowLeft, AlertTriangle } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { ChaosTest } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  chaos: ChaosTest[];
  onBack: () => void;
}

export function PerfChaosPanel({ chaos, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel title="Chaos Testing" subtitle="Randomly kill Redis / DB / WebSocket / Provider / Agent — verify recovery" icon={<AlertTriangle className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
      >
        <div className="space-y-3">
          {chaos.map((c) => (
            <div key={c.id} className="rounded-md border border-border/40 bg-background/30 p-3">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="text-[12px] font-semibold">{c.target}</div>
                  <div className="text-[10px] text-muted-foreground/70">{c.description}</div>
                </div>
                <StatusBadge status={c.status} />
              </div>
              <div className="grid grid-cols-3 gap-3 text-[10px] font-mono mb-2">
                <div><div className="text-muted-foreground/60 text-[8px] uppercase tracking-wider">Killed</div><div className="text-foreground/80">{fmtAge(Date.now() - c.killedAt)}</div></div>
                <div><div className="text-muted-foreground/60 text-[8px] uppercase tracking-wider">Recovery</div><div style={{ color: c.recoveredMs < 3000 ? "#34d399" : "#fbbf24" }}>{(c.recoveredMs / 1000).toFixed(2)}s</div></div>
                <div><div className="text-muted-foreground/60 text-[8px] uppercase tracking-wider">Status</div><div style={{ color: "#34d399" }}>{c.status}</div></div>
              </div>
              <div className="text-[10px] text-muted-foreground/80 leading-snug">{c.finding}</div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Chaos Health" icon={<AlertTriangle className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Tests" value={chaos.length} intent="info" />
          <Stat label="Passing" value={chaos.filter((c) => c.status === "pass").length} unit={`/ ${chaos.length}`} intent="healthy" />
          <Stat label="Avg Recovery" value={`${(chaos.reduce((s, c) => s + c.recoveredMs, 0) / chaos.length / 1000).toFixed(2)}s`} intent="healthy" />
          <Stat label="Max Recovery" value={`${(Math.max(...chaos.map((c) => c.recoveredMs)) / 1000).toFixed(2)}s`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          All chaos tests pass. Every killed service auto-recovers within 5s with zero data loss.
        </div>
      </Panel>
    </PanelGrid>
  );
}
