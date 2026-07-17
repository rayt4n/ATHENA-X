"use client";

import { ResponsiveContainer, AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, BarChart, Bar, Cell } from "recharts";
import { Activity, Zap, Database as DbIcon, Layers } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { fmtMs, fmtCompact, fmtTime } from "@/lib/dashboard/format";
import { STATUS_COLORS } from "@/lib/dashboard/colors";
import type { EventBusMetrics } from "@/lib/dashboard/types";

export function EventBusPanel({ eventBus }: { eventBus: EventBusMetrics }) {
  const backlogPct = eventBus.backlog / eventBus.backlogLimit;

  return (
    <PanelGrid>
      <Panel
        title="Event Bus Latency"
        subtitle="p50 / p95 / p99 — rolling 60s"
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-8"
        actions={
          <div className="flex items-center gap-2 text-[10.5px] font-mono">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: "#22d3ee" }} />p50</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: "#fbbf24" }} />p95</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: "#f87171" }} />p99</span>
          </div>
        }
      >
        <div className="h-[240px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={eventBus.latencyHistory} margin={{ top: 8, right: 12, bottom: 18, left: 0 }}>
              <XAxis
                dataKey="t"
                tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }}
                tickFormatter={(v) => fmtTime(v)}
                stroke="rgba(255,255,255,0.08)"
                interval={5}
              />
              <YAxis
                tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }}
                tickFormatter={(v) => `${v}ms`}
                stroke="rgba(255,255,255,0.08)"
                width={42}
              />
              <Tooltip
                contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10.5, fontFamily: "var(--font-geist-mono)", color: "#e6edf3" }}
                labelFormatter={(_, p) => p[0]?.payload?.t ? fmtTime(p[0].payload.t) : ""}
                formatter={(v: number, n: string) => [fmtMs(v), n]}
              />
              <ReferenceLine y={40} stroke={STATUS_COLORS.warning} strokeDasharray="3 3" strokeOpacity={0.5} />
              <ReferenceLine y={80} stroke={STATUS_COLORS.critical} strokeDasharray="3 3" strokeOpacity={0.5} />
              <Line type="monotone" dataKey="p50" stroke={STATUS_COLORS.info} strokeWidth={1.8} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="p95" stroke={STATUS_COLORS.warning} strokeWidth={1.8} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="p99" stroke={STATUS_COLORS.critical} strokeWidth={1.8} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel
        title="Bus Health"
        subtitle="Snapshot barrier & backlog"
        icon={<Zap className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-4"
      >
        <div className="grid grid-cols-2 gap-2">
          <Stat label="Inflow" value={fmtCompact(eventBus.inflowPerSec)} unit="ev/s" intent="info" />
          <Stat label="Outflow" value={fmtCompact(eventBus.outflowPerSec)} unit="ev/s" intent={eventBus.outflowPerSec / eventBus.inflowPerSec > 0.95 ? "healthy" : "warning"} />
          <Stat label="p50" value={fmtMs(eventBus.p50LatencyMs)} intent="healthy" />
          <Stat label="p95" value={fmtMs(eventBus.p95LatencyMs)} intent={eventBus.p95LatencyMs < 40 ? "healthy" : "warning"} />
          <Stat label="p99" value={fmtMs(eventBus.p99LatencyMs)} intent={eventBus.p99LatencyMs < 80 ? "healthy" : "critical"} />
          <Stat label="Snapshot" value={fmtMs(eventBus.lastSnapshotMs)} unit="ago" intent="info" />
        </div>

        <div className="mt-3 pt-3 border-t border-border/40">
          <div className="flex items-center justify-between text-[10.5px] font-mono mb-1.5">
            <span className="text-muted-foreground">Backlog</span>
            <span className="text-foreground">{fmtCompact(eventBus.backlog)} / {fmtCompact(eventBus.backlogLimit)}</span>
          </div>
          <div className="h-2 rounded-full bg-background/60 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min(100, backlogPct * 100)}%`,
                backgroundColor: backlogPct < 0.05 ? "#34d399" : backlogPct < 0.2 ? "#fbbf24" : "#f87171",
              }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-[10.5px] font-mono">
            <span className="text-muted-foreground">Barrier</span>
            <span style={{ color: eventBus.snapshotBarrierStatus === "completed" ? "#34d399" : eventBus.snapshotBarrierStatus === "open" ? "#22d3ee" : "#f87171" }}>
              {eventBus.snapshotBarrierStatus}
            </span>
          </div>
          <div className="mt-1 flex items-center justify-between text-[10.5px] font-mono">
            <span className="text-muted-foreground">Replay depth</span>
            <span className="text-foreground">{fmtCompact(eventBus.replayDepth)}</span>
          </div>
        </div>
      </Panel>

      <Panel
        title="Throughput"
        subtitle="Inflow vs outflow — events/sec"
        icon={<DbIcon className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-8"
      >
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={eventBus.throughputHistory} margin={{ top: 8, right: 12, bottom: 18, left: 0 }}>
              <defs>
                <linearGradient id="inflowG" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={STATUS_COLORS.info} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={STATUS_COLORS.info} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="outflowG" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={STATUS_COLORS.healthy} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={STATUS_COLORS.healthy} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="t"
                tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }}
                tickFormatter={(v) => fmtTime(v)}
                stroke="rgba(255,255,255,0.08)"
                interval={5}
              />
              <YAxis
                tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }}
                stroke="rgba(255,255,255,0.08)"
                width={42}
              />
              <Tooltip
                contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10.5, fontFamily: "var(--font-geist-mono)", color: "#e6edf3" }}
                labelFormatter={(_, p) => p[0]?.payload?.t ? fmtTime(p[0].payload.t) : ""}
                formatter={(v: number, n: string) => [fmtCompact(v) + "/s", n]}
              />
              <Area type="monotone" dataKey="inflow" stroke={STATUS_COLORS.info} strokeWidth={1.8} fill="url(#inflowG)" isAnimationActive={false} />
              <Area type="monotone" dataKey="outflow" stroke={STATUS_COLORS.healthy} strokeWidth={1.8} fill="url(#outflowG)" isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel
        title="Priority Distribution"
        subtitle="P0 critical → P3 best-effort"
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-4"
      >
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={eventBus.priorityDistribution} margin={{ top: 8, right: 12, bottom: 18, left: 0 }}>
              <XAxis dataKey="priority" tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "var(--font-geist-mono)" }} stroke="rgba(255,255,255,0.08)" />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }} stroke="rgba(255,255,255,0.08)" width={42} />
              <Tooltip
                contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10.5, fontFamily: "var(--font-geist-mono)", color: "#e6edf3" }}
                formatter={(v: number, _n, p) => [`${v.toLocaleString()} (${(p?.payload?.percentage * 100).toFixed(1)}%)`, "events"]}
              />
              <Bar dataKey="count" radius={[3, 3, 0, 0]} isAnimationActive={false}>
                {eventBus.priorityDistribution.map((p, i) => (
                  <Cell key={i} fill={p.priority === "P0" ? STATUS_COLORS.critical : p.priority === "P1" ? STATUS_COLORS.warning : p.priority === "P2" ? STATUS_COLORS.info : "#6b7280"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </PanelGrid>
  );
}
