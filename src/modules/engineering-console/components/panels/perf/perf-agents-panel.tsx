"use client";

import { ArrowLeft, Cpu } from "lucide-react";
import { useState } from "react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { AgentPerfRecord } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  agents: AgentPerfRecord[];
  onBack: () => void;
}

export function PerfAgentsPanel({ agents, onBack }: Props) {
  const [sortBy, setSortBy] = useState<"rank" | "avgExec" | "peakExec" | "mem" | "cpu">("avgExec");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const sorted = [...agents].sort((a, b) => {
    let cmp = 0;
    if (sortBy === "rank") cmp = a.rank - b.rank;
    else if (sortBy === "avgExec") cmp = a.avgExecMs - b.avgExecMs;
    else if (sortBy === "peakExec") cmp = a.peakExecMs - b.peakExecMs;
    else if (sortBy === "mem") cmp = a.memMb - b.memMb;
    else if (sortBy === "cpu") cmp = a.cpuPct - b.cpuPct;
    return sortOrder === "asc" ? cmp : -cmp;
  });

  const slowest = agents[agents.length - 1];
  const heaviest = agents.reduce((max, a) => a.memMb > max.memMb ? a : max);
  const highestCpu = agents.reduce((max, a) => a.cpuPct > max.cpuPct ? a : max);

  return (
    <PanelGrid>
      <Panel title="Agent Performance" subtitle={`${agents.length} agents ranked by execution time, queue wait, retries, memory, CPU`} icon={<Cpu className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
      >
        <div className="flex items-center gap-2 mb-3 text-[10px] font-mono">
          <span className="text-muted-foreground">sort:</span>
          {(["rank", "avgExec", "peakExec", "mem", "cpu"] as const).map((s) => (
            <button key={s} onClick={() => { setSortBy(s); setSortOrder(sortBy === s && sortOrder === "desc" ? "asc" : "desc"); }}
              className={`px-1.5 py-0.5 rounded ${sortBy === s ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}>
              {s} {sortBy === s ? (sortOrder === "asc" ? "↑" : "↓") : ""}
            </button>
          ))}
        </div>
        <div className="rounded-md border border-border/40 overflow-hidden">
          <div className="max-h-[460px] overflow-y-auto scroll-thin">
            <div className="grid grid-cols-12 px-3 py-1.5 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40 sticky top-0">
              <div className="col-span-1">#</div>
              <div className="col-span-3">Agent</div>
              <div className="col-span-1 text-right">Avg ms</div>
              <div className="col-span-1 text-right">Peak ms</div>
              <div className="col-span-1 text-right">Queue</div>
              <div className="col-span-1 text-right">Retry</div>
              <div className="col-span-1 text-right">Timeout</div>
              <div className="col-span-1 text-right">Mem MB</div>
              <div className="col-span-1 text-right">CPU %</div>
              <div className="col-span-1 text-right">Status</div>
            </div>
            {sorted.slice(0, 100).map((a) => (
              <div key={a.id} className="grid grid-cols-12 px-3 py-1 text-[10.5px] items-center hover:bg-accent/30 border-b border-border/20">
                <div className="col-span-1 font-mono text-muted-foreground">{a.rank}</div>
                <div className="col-span-3 truncate">
                  <div className="font-medium truncate">{a.name}</div>
                  <div className="text-[8px] font-mono text-muted-foreground/60">S{a.stage} · {a.category}</div>
                </div>
                <div className="col-span-1 text-right font-mono tabular-nums">{a.avgExecMs}</div>
                <div className="col-span-1 text-right font-mono tabular-nums text-muted-foreground">{a.peakExecMs}</div>
                <div className="col-span-1 text-right font-mono tabular-nums text-muted-foreground">{a.queueWaitMs}</div>
                <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: a.retryCount > 5 ? "#fbbf24" : "#94a3b8" }}>{a.retryCount}</div>
                <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: a.timeoutCount > 0 ? "#f87171" : "#94a3b8" }}>{a.timeoutCount}</div>
                <div className="col-span-1 text-right font-mono tabular-nums">{a.memMb}</div>
                <div className="col-span-1 text-right font-mono tabular-nums">{a.cpuPct}</div>
                <div className="col-span-1 flex justify-end"><StatusBadge status={a.status} /></div>
              </div>
            ))}
          </div>
        </div>
        {sorted.length > 100 && <div className="mt-2 text-center text-[9px] font-mono text-muted-foreground/70">showing first 100 of {sorted.length}</div>}
      </Panel>
      <Panel title="Agent Rankings" icon={<Cpu className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Total Agents" value={agents.length} intent="info" />
          <Stat label="Passing" value={agents.filter((a) => a.status === "pass").length} unit={`/ ${agents.length}`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 space-y-2">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">Top Performers</div>
          <RankRow label="Slowest" name={slowest.name} value={`${slowest.avgExecMs}ms`} color="#f87171" />
          <RankRow label="Heaviest" name={heaviest.name} value={`${heaviest.memMb}MB`} color="#fbbf24" />
          <RankRow label="Highest CPU" name={highestCpu.name} value={`${highestCpu.cpuPct}%`} color="#fbbf24" />
        </div>
      </Panel>
    </PanelGrid>
  );
}

function RankRow({ label, name, value, color }: { label: string; name: string; value: string; color: string }) {
  return (
    <div className="rounded-md border border-border/40 bg-background/30 p-2">
      <div className="text-[8px] uppercase tracking-wider text-muted-foreground/60">{label}</div>
      <div className="text-[10px] font-medium truncate">{name}</div>
      <div className="text-[12px] font-mono font-bold" style={{ color }}>{value}</div>
    </div>
  );
}
