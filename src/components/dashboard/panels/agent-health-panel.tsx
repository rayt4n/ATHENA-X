"use client";

import { Cpu, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { StatusDot } from "../status-dot";
import { fmtAge, fmtCompact } from "@/lib/dashboard/format";
import type { AgentState } from "@/lib/dashboard/types";

const CATEGORY_LABELS: Record<AgentState["category"], string> = {
  validation: "Validation",
  normalization: "Normalization",
  technical: "Technical Analysis",
  options: "Options Intel",
  market: "Market Intel",
  narrative: "Narrative",
  forecast: "Forecast",
  trade: "Trade Intel",
  operations: "Operations",
};

const STAGES: { stage: number; label: string }[] = [
  { stage: 3, label: "Stage 3 — Validation" },
  { stage: 4, label: "Stage 4 — Normalization" },
  { stage: 7, label: "Stage 7 — Technical" },
  { stage: 8, label: "Stage 8 — Options" },
  { stage: 9, label: "Stage 9 — Market" },
  { stage: 10, label: "Stage 10 — Narrative" },
  { stage: 11, label: "Stage 11 — Forecast" },
  { stage: 12, label: "Stage 12 — Trade" },
  { stage: 13, label: "Stage 13 — Operations" },
];

export function AgentHealthPanel({ agents }: { agents: AgentState[] }) {
  const [filter, setFilter] = useState("");
  const filtered = useMemo(() => {
    if (!filter) return agents;
    const q = filter.toLowerCase();
    return agents.filter((a) => a.name.toLowerCase().includes(q) || a.id.toLowerCase().includes(q) || CATEGORY_LABELS[a.category].toLowerCase().includes(q));
  }, [agents, filter]);

  const healthy = agents.filter((a) => a.state === "healthy").length;
  const degraded = agents.filter((a) => a.state === "degraded").length;
  const down = agents.filter((a) => a.state === "down").length;
  const avgCpu = agents.reduce((s, a) => s + a.cpuPct, 0) / Math.max(1, agents.length);
  const totalEvents = agents.reduce((s, a) => s + a.processedEvents, 0);
  const totalErrors = agents.reduce((s, a) => s + a.errors, 0);

  return (
    <PanelGrid>
      <Panel
        title="Agent Health Overview"
        subtitle={`${agents.length} registered AI agents across ${STAGES.length} stages`}
        icon={<Cpu className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2">
          <Stat label="Healthy" value={healthy} intent="healthy" />
          <Stat label="Degraded" value={degraded} intent={degraded > 0 ? "warning" : "default"} />
          <Stat label="Down" value={down} intent={down > 0 ? "critical" : "default"} />
          <Stat label="Avg CPU" value={`${avgCpu.toFixed(0)}%`} intent={avgCpu < 30 ? "healthy" : avgCpu < 60 ? "warning" : "critical"} />
          <Stat label="Total Events" value={fmtCompact(totalEvents)} />
          <Stat label="Total Errors" value={fmtCompact(totalErrors)} intent={totalErrors > 500 ? "warning" : "default"} />
        </div>
      </Panel>

      <Panel
        title="Agent Registry"
        subtitle="Heartbeat, state machine, current task"
        icon={<Cpu className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-9"
        actions={
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
            <input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="filter agents…"
              className="pl-7 pr-2 py-1 rounded-md bg-background/60 border border-border/50 text-[11px] font-mono w-44 focus:outline-none focus:border-primary/50"
            />
          </div>
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[560px] overflow-y-auto scroll-thin">
          {STAGES.map((s) => {
            const items = filtered.filter((a) => a.stage === s.stage);
            if (items.length === 0) return null;
            return (
              <div key={s.stage} className="border-b border-border/30 last:border-0">
                <div className="px-4 py-1.5 bg-background/40 text-[9.5px] uppercase tracking-wider text-muted-foreground/80 flex items-center justify-between">
                  <span>{s.label}</span>
                  <span className="font-mono">{items.filter((a) => a.state === "healthy").length}/{items.length} healthy</span>
                </div>
                <div className="divide-y divide-border/20">
                  {items.map((a) => (
                    <AgentRow key={a.id} a={a} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </PanelGrid>
  );
}

function AgentRow({ a }: { a: AgentState }) {
  return (
    <div className="grid grid-cols-12 px-4 py-1.5 text-[11px] items-center hover:bg-accent/30">
      <div className="col-span-1 flex justify-center">
        <StatusDot state={a.state} pulse={a.state === "healthy"} />
      </div>
      <div className="col-span-4 min-w-0">
        <div className="font-medium truncate">{a.name}</div>
        <div className="text-[9.5px] font-mono text-muted-foreground/70 truncate">{a.id}</div>
      </div>
      <div className="col-span-2 text-[10px] text-muted-foreground truncate">{a.currentTask ?? "—"}</div>
      <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">
        {fmtAge(a.lastHeartbeatMs)}
      </div>
      <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: a.cpuPct < 30 ? "#34d399" : a.cpuPct < 60 ? "#fbbf24" : "#f87171" }}>
        {a.cpuPct.toFixed(0)}%
      </div>
      <div className="col-span-1 text-right font-mono tabular-nums text-muted-foreground">{a.memMb.toFixed(0)}M</div>
      <div className="col-span-1 text-right font-mono tabular-nums text-muted-foreground">{fmtCompact(a.processedEvents)}</div>
    </div>
  );
}
