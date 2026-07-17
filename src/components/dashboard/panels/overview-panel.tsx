"use client";

import { Activity, Radio, Cpu, Database, Layers, ShieldCheck, Beaker, Bell, Gauge, TrendingUp, Zap } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat, StatRow } from "../stat";
import { StatusDot } from "../status-dot";
import { fmtMs, fmtAge, fmtPct, fmtCompact, fmtNum } from "@/lib/dashboard/format";
import type { DashboardTelemetry } from "@/lib/dashboard/types";
import { DNAMiniSparklines, EventBusMiniChart } from "./event-bus-mini";

interface Props {
  t: DashboardTelemetry;
  onJump: (section: string) => void;
}

export function OverviewPanel({ t, onJump }: Props) {
  const { system, eventBus, database, agents, providers, dna, alarms } = t;

  const agentHealthPct = system.totalAgents > 0 ? system.healthyAgents / system.totalAgents : 0;
  const providerHealthPct = system.totalProviders > 0 ? system.healthyProviders / system.totalProviders : 0;
  const avgDnaConf = dna.reduce((s, d) => s + d.confidence, 0) / Math.max(1, dna.length);
  const dbMaxP95 = Math.max(...database.map((d) => d.writeP95));
  const criticalCount = alarms.filter((a) => a.severity === "critical" && !a.acked).length;
  const warningCount = alarms.filter((a) => a.severity === "warning" && !a.acked).length;

  return (
    <PanelGrid className="grid-cols-12 gap-3">
      {/* Hero KPIs */}
      <Panel
        title="System Health"
        subtitle="Live platform posture"
        icon={<Beaker className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-8"
        bodyClassName="grid grid-cols-2 md:grid-cols-4 gap-3"
      >
        <StatRow className="grid-cols-1 gap-2">
          <Stat
            label="Overall Health"
            value={
              <span className="flex items-center gap-2">
                <StatusDot state={system.overallHealth} size="md" />
                <span className="capitalize">{system.overallHealth}</span>
              </span>
            }
            intent={system.overallHealth === "healthy" ? "healthy" : system.overallHealth === "degraded" ? "warning" : "critical"}
          />
          <Stat label="Active Alarms" value={system.activeAlarms} intent={system.activeAlarms > 0 ? "critical" : "default"} />
          <Stat label="Uptime" value={fmtAge(Date.now() - system.startedAt)} />
        </StatRow>

        <StatRow className="grid-cols-1 gap-2">
          <Stat
            label="Agent Health"
            value={`${system.healthyAgents}/${system.totalAgents}`}
            unit={`(${fmtPct(agentHealthPct, 0)})`}
            intent={agentHealthPct > 0.9 ? "healthy" : agentHealthPct > 0.75 ? "warning" : "critical"}
          />
          <Stat
            label="Provider Health"
            value={`${system.healthyProviders}/${system.totalProviders}`}
            unit={`(${fmtPct(providerHealthPct, 0)})`}
            intent={providerHealthPct > 0.9 ? "healthy" : providerHealthPct > 0.75 ? "warning" : "critical"}
          />
          <Stat
            label="Plugin Coverage"
            value={`${system.activePlugins}/${system.totalPlugins}`}
            unit="active"
            intent="info"
          />
        </StatRow>

        <StatRow className="grid-cols-1 gap-2">
          <Stat
            label="Event Bus p95"
            value={fmtNum(eventBus.p95LatencyMs, 1)}
            unit="ms"
            intent={eventBus.p95LatencyMs < 40 ? "healthy" : eventBus.p95LatencyMs < 80 ? "warning" : "critical"}
          />
          <Stat
            label="DB Write p95"
            value={fmtNum(dbMaxP95, 1)}
            unit="ms"
            intent={dbMaxP95 < 20 ? "healthy" : dbMaxP95 < 40 ? "warning" : "critical"}
          />
          <Stat
            label="Backlog"
            value={fmtCompact(eventBus.backlog)}
            unit={`/ ${fmtCompact(eventBus.backlogLimit)}`}
            intent={eventBus.backlog / eventBus.backlogLimit < 0.05 ? "default" : "warning"}
          />
        </StatRow>

        <StatRow className="grid-cols-1 gap-2">
          <Stat
            label="Avg DNA Confidence"
            value={fmtPct(avgDnaConf, 1)}
            intent={avgDnaConf > 0.75 ? "healthy" : avgDnaConf > 0.6 ? "warning" : "critical"}
          />
          <Stat
            label="Critical / Warning"
            value={`${criticalCount} / ${warningCount}`}
            intent={criticalCount > 0 ? "critical" : warningCount > 0 ? "warning" : "healthy"}
          />
          <Stat
            label="Throughput"
            value={fmtCompact(eventBus.inflowPerSec)}
            unit="ev/s"
            intent="info"
          />
        </StatRow>
      </Panel>

      {/* Live event bus sparkline */}
      <Panel
        title="Event Bus — Live"
        subtitle="Latency & throughput"
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
        actions={
          <button
            onClick={() => onJump("eventbus")}
            className="text-[10.5px] text-primary hover:underline font-mono"
          >
            drill in →
          </button>
        }
      >
        <EventBusMiniChart eventBus={eventBus} />
      </Panel>

      {/* DNA mini sparklines */}
      <Panel
        title="7-DNA Confidence Matrix"
        subtitle="Live consensus across intelligence objects"
        icon={<Beaker className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-8"
        actions={
          <button
            onClick={() => onJump("dna")}
            className="text-[10.5px] text-primary hover:underline font-mono"
          >
            drill in →
          </button>
        }
      >
        <DNAMiniSparklines dna={dna} />
      </Panel>

      {/* Live alarms */}
      <Panel
        title="Active Alarms"
        subtitle="Unacknowledged, last 15 min"
        icon={<Bell className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
        actions={
          <button
            onClick={() => onJump("alarms")}
            className="text-[10.5px] text-primary hover:underline font-mono"
          >
            view all →
          </button>
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[260px] overflow-y-auto scroll-thin divide-y divide-border/40">
          {alarms.length === 0 && (
            <div className="px-4 py-6 text-center text-[11.5px] text-muted-foreground/70 font-mono">no active alarms</div>
          )}
          {alarms.slice(0, 8).map((a) => (
            <div key={a.id} className="px-4 py-2.5 flex items-start gap-2.5">
              <StatusDot state={a.severity === "critical" ? "down" : "degraded"} pulse />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] font-mono text-muted-foreground truncate">{a.source}</span>
                  <span className="text-[9.5px] font-mono text-muted-foreground/70">{fmtAge(Date.now() - a.raisedAt)}</span>
                </div>
                <div className="text-[11px] leading-snug mt-0.5">{a.message}</div>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Quick stats: providers + db + agents */}
      <Panel
        title="Provider Posture"
        subtitle="By category"
        icon={<Radio className="h-3.5 w-3.5" />}
        className="col-span-12 md:col-span-4"
        actions={
          <button onClick={() => onJump("providers")} className="text-[10.5px] text-primary hover:underline font-mono">→</button>
        }
      >
        <div className="space-y-1.5">
          {["market_data", "options_data", "news", "macro", "alt_data"].map((cat) => {
            const items = providers.filter((p) => p.category === cat);
            const healthy = items.filter((p) => p.state === "healthy").length;
            const pct = items.length ? healthy / items.length : 0;
            return (
              <div key={cat} className="flex items-center gap-2 text-[11px]">
                <span className="w-20 truncate text-muted-foreground">{cat.replace("_", " ")}</span>
                <div className="flex-1 h-1.5 rounded-full bg-background/60 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${pct * 100}%`,
                      backgroundColor: pct > 0.85 ? "#34d399" : pct > 0.6 ? "#fbbf24" : "#f87171",
                    }}
                  />
                </div>
                <span className="w-10 text-right font-mono tabular-nums">{healthy}/{items.length}</span>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="Database p95 by Schema"
        subtitle="Top 6 slowest"
        icon={<Database className="h-3.5 w-3.5" />}
        className="col-span-12 md:col-span-4"
        actions={
          <button onClick={() => onJump("database")} className="text-[10.5px] text-primary hover:underline font-mono">→</button>
        }
      >
        <div className="space-y-1.5">
          {[...database].sort((a, b) => b.writeP95 - a.writeP95).slice(0, 6).map((d) => (
            <div key={d.schema} className="flex items-center gap-2 text-[11px]">
              <span className="w-24 truncate text-muted-foreground font-mono">{d.schema}</span>
              <div className="flex-1 h-1.5 rounded-full bg-background/60 overflow-hidden relative">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.min(100, (d.writeP95 / 40) * 100)}%`,
                    backgroundColor: d.writeP95 < 15 ? "#34d399" : d.writeP95 < 30 ? "#fbbf24" : "#f87171",
                  }}
                />
              </div>
              <span className="w-14 text-right font-mono tabular-nums">{d.writeP95.toFixed(1)}ms</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="Agent Load"
        subtitle="CPU% by stage"
        icon={<Cpu className="h-3.5 w-3.5" />}
        className="col-span-12 md:col-span-4"
        actions={
          <button onClick={() => onJump("agents")} className="text-[10.5px] text-primary hover:underline font-mono">→</button>
        }
      >
        <div className="space-y-1.5">
          {[3, 4, 7, 8, 9, 10, 11, 12, 13].map((stage) => {
            const items = agents.filter((a) => a.stage === stage);
            if (items.length === 0) return null;
            const avgCpu = items.reduce((s, a) => s + a.cpuPct, 0) / items.length;
            return (
              <div key={stage} className="flex items-center gap-2 text-[11px]">
                <span className="w-14 truncate text-muted-foreground font-mono">S{stage}</span>
                <div className="flex-1 h-1.5 rounded-full bg-background/60 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(100, avgCpu)}%`,
                      backgroundColor: avgCpu < 30 ? "#34d399" : avgCpu < 60 ? "#fbbf24" : "#f87171",
                    }}
                  />
                </div>
                <span className="w-12 text-right font-mono tabular-nums">{avgCpu.toFixed(0)}%</span>
              </div>
            );
          })}
        </div>
      </Panel>
    </PanelGrid>
  );
}
