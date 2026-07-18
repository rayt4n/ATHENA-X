"use client";

import { ArrowLeft, Beaker } from "lucide-react";
import { useState } from "react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { PluginPerfRecord } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  plugins: PluginPerfRecord[];
  onBack: () => void;
}

const CAT_COLORS: Record<string, string> = { ta: "#22d3ee", options: "#a78bfa", market: "#34d399", news: "#fbbf24", forecast: "#fb923c" };

export function PerfPluginsPanel({ plugins, onBack }: Props) {
  const [filter, setFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"exec" | "cpu" | "mem">("exec");

  const filtered = filter === "all" ? plugins : plugins.filter((p) => p.category === filter);
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === "exec") return b.execMs - a.execMs;
    if (sortBy === "cpu") return b.cpuPct - a.cpuPct;
    return b.memMb - a.memMb;
  });

  const slowest = plugins[0]; // already sorted by execMs desc in engine
  const heaviest = plugins.reduce((max, p) => p.memMb > max.memMb ? p : max);
  const highestCpu = plugins.reduce((max, p) => p.cpuPct > max.cpuPct ? p : max);

  return (
    <PanelGrid>
      <Panel title="Plugin Performance" subtitle={`${plugins.length} plugins ranked — slowest, heaviest, highest CPU/RAM`} icon={<Beaker className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
      >
        <div className="flex items-center gap-2 mb-3 text-[10px] font-mono flex-wrap">
          <span className="text-muted-foreground">filter:</span>
          <button onClick={() => setFilter("all")} className={`px-1.5 py-0.5 rounded ${filter === "all" ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}>all ({plugins.length})</button>
          {Object.keys(CAT_COLORS).map((cat) => (
            <button key={cat} onClick={() => setFilter(cat)} className={`px-1.5 py-0.5 rounded ${filter === cat ? "border" : "text-muted-foreground border border-border/40"}`}
              style={filter === cat ? { backgroundColor: `${CAT_COLORS[cat]}22`, color: CAT_COLORS[cat], borderColor: `${CAT_COLORS[cat]}55` } : {}}>
              {cat} ({plugins.filter((p) => p.category === cat).length})
            </button>
          ))}
          <span className="ml-auto text-muted-foreground">sort:</span>
          {(["exec", "cpu", "mem"] as const).map((s) => (
            <button key={s} onClick={() => setSortBy(s)} className={`px-1.5 py-0.5 rounded ${sortBy === s ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}>{s}</button>
          ))}
        </div>
        <div className="rounded-md border border-border/40 overflow-hidden">
          <div className="max-h-[460px] overflow-y-auto scroll-thin">
            <div className="grid grid-cols-12 px-3 py-1.5 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40 sticky top-0">
              <div className="col-span-1">#</div>
              <div className="col-span-4">Plugin</div>
              <div className="col-span-1">Cat</div>
              <div className="col-span-2 text-right">Exec ms</div>
              <div className="col-span-2 text-right">CPU %</div>
              <div className="col-span-1 text-right">Mem MB</div>
              <div className="col-span-1 text-right">Status</div>
            </div>
            {sorted.slice(0, 100).map((p) => (
              <div key={p.id} className="grid grid-cols-12 px-3 py-1 text-[10.5px] items-center hover:bg-accent/30 border-b border-border/20">
                <div className="col-span-1 font-mono text-muted-foreground">{p.rank}</div>
                <div className="col-span-4 font-mono truncate flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: CAT_COLORS[p.category] }} />
                  {p.name}
                </div>
                <div className="col-span-1"><span className="text-[8px] font-mono px-1 py-0.5 rounded" style={{ color: CAT_COLORS[p.category], backgroundColor: `${CAT_COLORS[p.category]}22` }}>{p.category}</span></div>
                <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: p.execMs > 50 ? "#fbbf24" : "#e6edf3" }}>{p.execMs}</div>
                <div className="col-span-2 text-right font-mono tabular-nums">{p.cpuPct}</div>
                <div className="col-span-1 text-right font-mono tabular-nums">{p.memMb}</div>
                <div className="col-span-1 flex justify-end"><StatusBadge status={p.status} /></div>
              </div>
            ))}
          </div>
        </div>
      </Panel>
      <Panel title="Plugin Rankings" icon={<Beaker className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Total" value={plugins.length} intent="info" />
          <Stat label="Passing" value={plugins.filter((p) => p.status === "pass").length} unit={`/ ${plugins.length}`} intent="healthy" />
        </div>
        <div className="pt-3 border-t border-border/40 space-y-2">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">Top Performers</div>
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-[8px] uppercase tracking-wider text-muted-foreground/60">Slowest</div>
            <div className="text-[10px] font-medium truncate">{slowest.name}</div>
            <div className="text-[12px] font-mono font-bold" style={{ color: "#f87171" }}>{slowest.execMs}ms</div>
          </div>
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-[8px] uppercase tracking-wider text-muted-foreground/60">Heaviest</div>
            <div className="text-[10px] font-medium truncate">{heaviest.name}</div>
            <div className="text-[12px] font-mono font-bold" style={{ color: "#fbbf24" }}>{heaviest.memMb}MB</div>
          </div>
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-[8px] uppercase tracking-wider text-muted-foreground/60">Highest CPU</div>
            <div className="text-[10px] font-medium truncate">{highestCpu.name}</div>
            <div className="text-[12px] font-mono font-bold" style={{ color: "#fbbf24" }}>{highestCpu.cpuPct}%</div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
