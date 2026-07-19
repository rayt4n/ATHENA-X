"use client";

import { ResponsiveContainer, LineChart, Line, YAxis, Tooltip, ReferenceLine } from "recharts";
import { fmtMs, fmtCompact } from "@/modules/engineering-console/lib/format";
import { STATUS_COLORS, DNA_COLORS } from "@/modules/engineering-console/lib/colors";
import type { EventBusMetrics, DNABlock } from "@/modules/engineering-console/lib/types";

export function EventBusMiniChart({ eventBus }: { eventBus: EventBusMetrics }) {
  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="grid grid-cols-3 gap-2 text-[10.5px] font-mono">
        <div className="rounded-md bg-background/40 border border-border/40 px-2 py-1.5">
          <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">p50</div>
          <div className="text-foreground tabular-nums">{fmtMs(eventBus.p50LatencyMs)}</div>
        </div>
        <div className="rounded-md bg-background/40 border border-border/40 px-2 py-1.5">
          <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">p95</div>
          <div className="text-foreground tabular-nums" style={{ color: eventBus.p95LatencyMs < 40 ? "#34d399" : "#fbbf24" }}>
            {fmtMs(eventBus.p95LatencyMs)}
          </div>
        </div>
        <div className="rounded-md bg-background/40 border border-border/40 px-2 py-1.5">
          <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">p99</div>
          <div className="text-foreground tabular-nums" style={{ color: eventBus.p99LatencyMs < 80 ? "#34d399" : "#f87171" }}>
            {fmtMs(eventBus.p99LatencyMs)}
          </div>
        </div>
      </div>

      <div className="h-[140px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={eventBus.latencyHistory} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <YAxis hide domain={[0, "dataMax + 20"]} />
            <Tooltip
              contentStyle={{
                background: "#131820",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 6,
                fontSize: 10.5,
                fontFamily: "var(--font-geist-mono)",
                color: "#e6edf3",
              }}
              labelFormatter={(_, p) => p[0]?.payload?.t ? new Date(p[0].payload.t).toLocaleTimeString("en-US", { hour12: false }) : ""}
              formatter={(v: number, n: string) => [fmtMs(v), n]}
            />
            <ReferenceLine y={40} stroke={STATUS_COLORS.warning} strokeDasharray="2 2" strokeOpacity={0.5} />
            <ReferenceLine y={80} stroke={STATUS_COLORS.critical} strokeDasharray="2 2" strokeOpacity={0.5} />
            <Line type="monotone" dataKey="p50" stroke={STATUS_COLORS.info} strokeWidth={1.6} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="p95" stroke={STATUS_COLORS.warning} strokeWidth={1.6} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="p99" stroke={STATUS_COLORS.critical} strokeWidth={1.6} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
        <span>in <span className="text-foreground">{fmtCompact(eventBus.inflowPerSec)}/s</span></span>
        <span>out <span className="text-foreground">{fmtCompact(eventBus.outflowPerSec)}/s</span></span>
        <span>backlog <span className="text-foreground">{fmtCompact(eventBus.backlog)}</span></span>
        <span>replay <span className="text-foreground">{fmtCompact(eventBus.replayDepth)}</span></span>
      </div>
    </div>
  );
}

export function DNAMiniSparklines({ dna }: { dna: DNABlock[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
      {dna.map((d) => {
        const color = d.confidence > 0.75 ? STATUS_COLORS.healthy : d.confidence > 0.55 ? STATUS_COLORS.warning : STATUS_COLORS.critical;
        const accent = DNA_COLORS[d.id] ?? color;
        return (
          <div key={d.id} className="rounded-md border border-border/50 bg-background/40 p-2 flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold truncate">{d.name.replace(" DNA", "")}</span>
              <span className="text-[9px] font-mono text-muted-foreground">S{d.stage}</span>
            </div>
            <div className="h-[44px] -mx-1">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={d.history} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
                  <YAxis hide domain={[0.2, 1]} />
                  <Line type="monotone" dataKey="confidence" stroke={accent} strokeWidth={1.8} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-[12px] font-mono tabular-nums font-semibold" style={{ color }}>
                {(d.confidence * 100).toFixed(1)}%
              </span>
              <span className="text-[9px] font-mono text-muted-foreground">{d.contributors.length} inp</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
