"use client";

import { ArrowLeft, Clock } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { SoakResult } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  soak: SoakResult[];
  onBack: () => void;
}

export function PerfSoakPanel({ soak, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel title="Soak Testing" subtitle="8h / 24h / 72h continuous run — memory leaks, queue growth, thread/socket leaks" icon={<Clock className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
      >
        <div className="space-y-3">
          {soak.map((s) => (
            <div key={s.id} className="rounded-md border border-border/40 bg-background/30 p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[14px] font-bold font-mono text-primary">{s.duration}</span>
                  <span className="text-[10px] text-muted-foreground/70">continuous run</span>
                </div>
                <StatusBadge status={s.status} />
              </div>
              <div className="grid grid-cols-4 gap-3 text-[10px] font-mono mb-2">
                <div><div className="text-muted-foreground/60 text-[8px] uppercase tracking-wider">Memory Growth</div><div style={{ color: s.memoryGrowthMb > 100 ? "#fbbf24" : "#34d399" }}>{s.memoryGrowthMb}MB</div></div>
                <div><div className="text-muted-foreground/60 text-[8px] uppercase tracking-wider">Queue Growth</div><div style={{ color: s.queueGrowth > 200 ? "#fbbf24" : "#34d399" }}>{s.queueGrowth}</div></div>
                <div><div className="text-muted-foreground/60 text-[8px] uppercase tracking-wider">Thread Leaks</div><div style={{ color: s.threadLeaks > 0 ? "#f87171" : "#34d399" }}>{s.threadLeaks}</div></div>
                <div><div className="text-muted-foreground/60 text-[8px] uppercase tracking-wider">Socket Leaks</div><div style={{ color: s.socketLeaks > 2 ? "#fbbf24" : "#34d399" }}>{s.socketLeaks}</div></div>
              </div>
              <div className="space-y-0.5">
                {s.findings.map((f, i) => (
                  <div key={i} className="text-[9.5px] text-muted-foreground/80">• {f}</div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Soak Health" icon={<Clock className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Durations" value={soak.length} intent="info" />
          <Stat label="Passing" value={soak.filter((s) => s.status === "pass").length} unit={`/ ${soak.length}`} intent="healthy" />
          <Stat label="Longest" value={soak[soak.length - 1].duration} intent="info" />
          <Stat label="Max Memory" value={`${Math.max(...soak.map((s) => s.memoryGrowthMb)).toFixed(0)}MB`} intent="warning" />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          8h and 24h soak tests pass with no leaks. 72h test shows elevated memory growth but within 2x budget.
        </div>
      </Panel>
    </PanelGrid>
  );
}
