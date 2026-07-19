"use client";

import { ArrowLeft, Zap } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine } from "recharts";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { LoadTestPoint } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  loadTests: LoadTestPoint[];
  onBack: () => void;
}

export function PerfLoadPanel({ loadTests, onBack }: Props) {
  const chartData = loadTests.map((l) => ({ rate: l.eventsPerSec, p50: l.p50Ms, p95: l.p95Ms, p99: l.p99Ms, backlog: l.backlog }));
  const degradationStart = loadTests.find((l) => l.status !== "pass");

  return (
    <PanelGrid>
      <Panel title="Load Testing" subtitle="100 / 500 / 1K / 5K / 10K events/sec — find degradation point" icon={<Zap className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
      >
        <div className="h-[240px] mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 18, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="rate" tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "monospace" }} stroke="rgba(255,255,255,0.08)" label={{ value: "events/sec", position: "insideBottom", offset: -10, fill: "#6b7280", fontSize: 9 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "monospace" }} stroke="rgba(255,255,255,0.08)" label={{ value: "latency (ms)", angle: -90, position: "insideLeft", fill: "#6b7280", fontSize: 9 }} />
              <Tooltip contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10.5, fontFamily: "monospace" }} />
              <ReferenceLine y={50} stroke="#fbbf24" strokeDasharray="3 3" strokeOpacity={0.5} label={{ value: "p95 target", fill: "#fbbf24", fontSize: 8 }} />
              <Line type="monotone" dataKey="p50" stroke="#22d3ee" strokeWidth={1.5} dot={{ r: 3 }} name="p50" />
              <Line type="monotone" dataKey="p95" stroke="#fbbf24" strokeWidth={1.5} dot={{ r: 3 }} name="p95" />
              <Line type="monotone" dataKey="p99" stroke="#f87171" strokeWidth={1.5} dot={{ r: 3 }} name="p99" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-md border border-border/40 overflow-hidden">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
            <div className="col-span-2">Events/sec</div>
            <div className="col-span-2 text-right">p50 (ms)</div>
            <div className="col-span-2 text-right">p95 (ms)</div>
            <div className="col-span-2 text-right">p99 (ms)</div>
            <div className="col-span-2 text-right">Backlog</div>
            <div className="col-span-1 text-right">Dropped</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {loadTests.map((l) => (
            <div key={l.eventsPerSec} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-2 font-mono font-bold">{l.eventsPerSec.toLocaleString()}</div>
              <div className="col-span-2 text-right font-mono tabular-nums">{l.p50Ms}</div>
              <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: l.p95Ms > 50 ? "#fbbf24" : "#34d399" }}>{l.p95Ms}</div>
              <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: l.p99Ms > 100 ? "#f87171" : "#94a3b8" }}>{l.p99Ms}</div>
              <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: l.backlog > 100 ? "#fbbf24" : "#94a3b8" }}>{l.backlog}</div>
              <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: l.droppedEvents > 0 ? "#f87171" : "#34d399" }}>{l.droppedEvents}</div>
              <div className="col-span-1 flex justify-end"><StatusBadge status={l.status} /></div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Load Health" icon={<Zap className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Tiers Tested" value={loadTests.length} intent="info" />
          <Stat label="Passing" value={loadTests.filter((l) => l.status === "pass").length} unit={`/ ${loadTests.length}`} intent="healthy" />
          <Stat label="Max Rate" value={`${loadTests[loadTests.length - 1].eventsPerSec.toLocaleString()}/s`} intent="info" />
          <Stat label="Degradation" value={degradationStart ? `${degradationStart.eventsPerSec}/s` : "none"} intent={degradationStart ? "warning" : "healthy"} />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          Platform handles up to 5,000 events/sec with p95 &lt; 50ms. Degradation begins at 10,000 events/sec where p95 exceeds target.
        </div>
      </Panel>
    </PanelGrid>
  );
}
