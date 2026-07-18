"use client";

import { ArrowLeft, Activity, Radio, Cpu, Database, Layers, Zap } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtMs, fmtAge } from "@/modules/engineering-console/lib/format";
import type { HealthCheck, HealthSubsystem } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  checks: HealthCheck[];
  onBack: () => void;
}

const SUBSYSTEM_ICONS: Record<HealthSubsystem, React.ReactNode> = {
  providers: <Radio className="h-4 w-4" />,
  agents: <Cpu className="h-4 w-4" />,
  event_bus: <Activity className="h-4 w-4" />,
  database: <Database className="h-4 w-4" />,
  queues: <Layers className="h-4 w-4" />,
  websockets: <Zap className="h-4 w-4" />,
};

export function OpsHealthPanel({ checks, onBack }: Props) {
  const healthy = checks.filter((c) => c.status === "healthy").length;
  const degraded = checks.filter((c) => c.status === "degraded").length;
  const down = checks.filter((c) => c.status === "down").length;
  const avgLatency = checks.reduce((s, c) => s + c.latencyMs, 0) / checks.length;
  const avgErrorRate = checks.reduce((s, c) => s + c.errorRate, 0) / checks.length;

  return (
    <PanelGrid>
      <Panel
        title="Subsystem Health Monitoring"
        subtitle={`${checks.length} subsystems · ${healthy} healthy · ${degraded} degraded · ${down} down`}
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-9"
        actions={
          <button
            onClick={onBack}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" /> back
          </button>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {checks.map((c) => {
            const color = c.status === "healthy" ? "#34d399" : c.status === "degraded" ? "#fbbf24" : "#f87171";
            return (
              <div
                key={c.id}
                className="rounded-md border p-3 transition-colors"
                style={{
                  borderColor: c.status === "healthy" ? "rgba(52, 211, 153, 0.2)" : c.status === "degraded" ? "rgba(251, 191, 36, 0.3)" : "rgba(248, 113, 113, 0.4)",
                  backgroundColor: c.status === "healthy" ? "rgba(52, 211, 153, 0.03)" : c.status === "degraded" ? "rgba(251, 191, 36, 0.05)" : "rgba(248, 113, 113, 0.08)",
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span style={{ color }}>{SUBSYSTEM_ICONS[c.subsystem]}</span>
                    <div>
                      <div className="text-[11.5px] font-semibold">{c.name}</div>
                      <div className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/70">{c.subsystem}</div>
                    </div>
                  </div>
                  <StatusBadge status={c.status === "healthy" ? "pass" : c.status === "degraded" ? "warn" : "fail"} />
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                  <div>
                    <div className="text-muted-foreground/70">latency</div>
                    <div style={{ color: c.latencyMs < 50 ? "#34d399" : c.latencyMs < 200 ? "#fbbf24" : "#f87171" }}>
                      {fmtMs(c.latencyMs)}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/70">error rate</div>
                    <div style={{ color: c.errorRate < 0.01 ? "#34d399" : c.errorRate < 0.05 ? "#fbbf24" : "#f87171" }}>
                      {(c.errorRate * 100).toFixed(3)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/70">uptime</div>
                    <div style={{ color: c.uptimePct > 0.99 ? "#34d399" : c.uptimePct > 0.95 ? "#fbbf24" : "#f87171" }}>
                      {(c.uptimePct * 100).toFixed(3)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/70">last check</div>
                    <div className="text-foreground/80">{fmtAge(c.lastCheckMs)}</div>
                  </div>
                </div>

                {c.consecutiveFailures > 0 && (
                  <div className="mt-2 pt-2 border-t border-border/30 text-[10px] font-mono" style={{ color: "#f87171" }}>
                    ⚠ {c.consecutiveFailures} consecutive failures
                  </div>
                )}
                {c.detail && c.status === "healthy" && (
                  <div className="mt-2 pt-2 border-t border-border/30 text-[10px] font-mono text-muted-foreground/70">
                    {c.detail}
                  </div>
                )}
                {c.detail && c.status !== "healthy" && (
                  <div className="mt-2 pt-2 border-t border-border/30 text-[10px] font-mono" style={{ color: "#fbbf24" }}>
                    {c.detail}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="Health Summary"
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Healthy" value={healthy} unit={`/ ${checks.length}`} intent="healthy" />
          <Stat label="Degraded" value={degraded} intent={degraded > 0 ? "warning" : "default"} />
          <Stat label="Down" value={down} intent={down > 0 ? "critical" : "healthy"} />
          <Stat label="Avg Latency" value={fmtMs(avgLatency)} intent={avgLatency < 50 ? "healthy" : "warning"} />
          <Stat label="Avg Error Rate" value={`${(avgErrorRate * 100).toFixed(3)}%`} intent={avgErrorRate < 0.01 ? "healthy" : "warning"} />
          <Stat label="Avg Uptime" value={`${(checks.reduce((s, c) => s + c.uptimePct, 0) / checks.length * 100).toFixed(3)}%`} intent="healthy" />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Probe Configuration</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">probe interval</span><span>5s</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">timeout</span><span>2s</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">alert threshold</span><span>3 failures</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">retention</span><span>30 days</span></div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
