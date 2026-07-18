"use client";

import { Activity, Radio, Database, Beaker, ShieldCheck, Zap, FileText, Layers, Award, RotateCcw } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { ScoreRing, StatusBadge } from "../../cert/cert-primitives";
import { fmtAge, fmtNum, fmtCompact } from "@/modules/engineering-console/lib/format";
import type { OpsTelemetry } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  ops: OpsTelemetry;
  onReset: () => void;
  onDrill: (id: string) => void;
}

const SUBSYSTEM_ICONS: Record<string, React.ReactNode> = {
  traceability: <Radio className="h-3.5 w-3.5" />,
  logging: <FileText className="h-3.5 w-3.5" />,
  aggregation: <Layers className="h-3.5 w-3.5" />,
  backup: <Database className="h-3.5 w-3.5" />,
  health: <Activity className="h-3.5 w-3.5" />,
  failure: <Zap className="h-3.5 w-3.5" />,
  config: <ShieldCheck className="h-3.5 w-3.5" />,
  plugins: <Beaker className="h-3.5 w-3.5" />,
};

export function OpsOverviewPanel({ ops, onReset, onDrill }: Props) {
  const { readiness } = ops;
  const isReady = readiness.status === "ready";
  const isDegraded = readiness.status === "degraded";

  const uptimeStr = readiness.uptimeSeconds < 3600
    ? `${(readiness.uptimeSeconds / 60).toFixed(0)}m`
    : readiness.uptimeSeconds < 86400
      ? `${(readiness.uptimeSeconds / 3600).toFixed(1)}h`
      : `${(readiness.uptimeSeconds / 86400).toFixed(1)}d`;

  return (
    <PanelGrid>
      {/* Hero */}
      <Panel
        title="Stage 15.5 — Platform Hardening & Operations"
        subtitle="Operational reliability · no new trading features"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-8"
        actions={
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <RotateCcw className="h-3 w-3" /> reset
          </button>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          <div className="flex flex-col items-center justify-center py-2">
            <ScoreRing score={readiness.overallScore} size={120} label="readiness" />
            <div className="mt-2 text-[10.5px] font-mono text-muted-foreground text-center">
              {readiness.criticalFailures} critical · {readiness.warnings} warnings
            </div>
          </div>

          <div className="md:col-span-2 space-y-3">
            <div className="rounded-md border border-border/60 bg-background/40 p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10.5px] uppercase tracking-wider text-muted-foreground">Operational Status</span>
                <StatusBadge status={isReady ? "pass" : isDegraded ? "warn" : "fail"} />
              </div>
              <div className="text-[18px] font-semibold" style={{
                color: isReady ? "#34d399" : isDegraded ? "#fbbf24" : "#f87171",
              }}>
                {isReady ? "✓ READY" : isDegraded ? "⚠ DEGRADED" : "✗ NOT READY"}
              </div>
              <div className="text-[10.5px] font-mono text-muted-foreground mt-1">
                Build {readiness.buildHash} · v{readiness.version}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[10.5px] font-mono">
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">Uptime</div>
                <div className="text-foreground mt-0.5">{uptimeStr}</div>
              </div>
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">MTBF</div>
                <div className="text-foreground mt-0.5">{readiness.mtbfHours.toFixed(0)}h</div>
              </div>
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">MTTR</div>
                <div className="text-foreground mt-0.5">{readiness.mttrMinutes.toFixed(1)}m</div>
              </div>
            </div>
          </div>
        </div>
      </Panel>

      {/* Quick stats */}
      <Panel
        title="Live Ops Metrics"
        subtitle="Streaming now"
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
      >
        <div className="grid grid-cols-2 gap-2">
          <Stat label="Active Traces" value={ops.traces.length} intent="info" />
          <Stat label="Logs (30s)" value={fmtCompact(ops.logs.length)} intent="info" />
          <Stat label="Backups" value={ops.backups.length} />
          <Stat label="Verified" value={ops.backups.filter((b) => b.restoreVerified).length} intent="healthy" />
          <Stat label="Health Checks" value={ops.healthChecks.filter((h) => h.status === "healthy").length} unit={`/ ${ops.healthChecks.length}`} intent="healthy" />
          <Stat label="Degraded" value={ops.healthChecks.filter((h) => h.status === "degraded").length} intent="warning" />
          <Stat label="Plugins Verified" value={ops.plugins.filter((p) => p.integrity === "verified").length} unit={`/ ${ops.plugins.length}`} intent="healthy" />
          <Stat label="Configs Valid" value={ops.configs.filter((c) => c.status === "valid").length} unit={`/ ${ops.configs.length}`} intent="healthy" />
        </div>
      </Panel>

      {/* 9 subsystem cards */}
      <Panel
        title="Operational Subsystems"
        subtitle="Click any subsystem to drill into detailed checks"
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {/* Map readiness.subsystems to cards */}
          {readiness.subsystems.map((s) => (
            <button
              key={s.id}
              onClick={() => onDrill(s.id)}
              className="text-left rounded-md border border-border/50 bg-background/30 p-3 hover:border-primary/40 hover:bg-accent/30 transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-primary/80">{SUBSYSTEM_ICONS[s.id]}</span>
                  <div className="min-w-0">
                    <div className="text-[12px] font-semibold truncate">{s.name}</div>
                    <div className="text-[9.5px] font-mono text-muted-foreground/70">{s.checks.length} checks</div>
                  </div>
                </div>
                <StatusBadge status={s.status === "pass" ? "pass" : s.status === "warn" ? "warn" : "fail"} />
              </div>

              <div className="flex items-center gap-3">
                <ScoreRing score={s.score} size={48} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-muted-foreground/80 line-clamp-2 leading-snug">
                    {s.checks.filter((c) => c.passed).length} of {s.checks.length} checks passing
                  </div>
                  <div className="text-[9.5px] font-mono text-muted-foreground/60 mt-1">
                    {s.checks.filter((c) => !c.passed).length === 0 ? "all clear" : `${s.checks.filter((c) => !c.passed).length} failing`}
                  </div>
                </div>
              </div>

              <div className="mt-2 pt-2 border-t border-border/40">
                <div className="flex items-center justify-between text-[9.5px] font-mono text-muted-foreground">
                  <span>
                    <span style={{ color: "#34d399" }}>{s.checks.filter((c) => c.passed).length}</span> pass
                    {" · "}
                    <span style={{ color: "#f87171" }}>{s.checks.filter((c) => !c.passed).length}</span> fail
                  </span>
                  <span className="text-primary">drill in →</span>
                </div>
              </div>
            </button>
          ))}

          {/* 9th card — readiness report */}
          <button
            onClick={() => onDrill("readiness")}
            className="text-left rounded-md border border-primary/40 bg-primary/5 p-3 hover:bg-primary/10 transition-all"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-primary/80"><Award className="h-3.5 w-3.5" /></span>
                <div>
                  <div className="text-[9.5px] font-mono text-muted-foreground/70 uppercase tracking-wider">Final</div>
                  <div className="text-[12px] font-semibold truncate">Readiness Report</div>
                </div>
              </div>
              <StatusBadge status={isReady ? "pass" : isDegraded ? "warn" : "fail"} />
            </div>

            <div className="flex items-center gap-3">
              <ScoreRing score={readiness.overallScore} size={48} />
              <div className="flex-1 min-w-0">
                <div className="text-[10px] text-muted-foreground/80 leading-snug">
                  Aggregated verdict across all 8 subsystems + uptime/MTBF/MTTR
                </div>
                <div className="text-[9.5px] font-mono text-muted-foreground/60 mt-1">
                  {fmtAge(readiness.generatedAt)} ago · {uptimeStr} uptime
                </div>
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-border/40">
              <div className="flex items-center justify-between text-[9.5px] font-mono text-muted-foreground">
                <span>Archival document</span>
                <span className="text-primary">view →</span>
              </div>
            </div>
          </button>
        </div>
      </Panel>
    </PanelGrid>
  );
}
