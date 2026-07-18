"use client";

import { Activity, Radio, Cpu, Database, Beaker, Zap, Clock, Layers, Award, RotateCcw, TrendingUp, AlertTriangle, FileText, Gauge } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { ScoreRing, StatusBadge } from "../../cert/cert-primitives";
import type { PerfTelemetry } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  perf: PerfTelemetry;
  onReset: () => void;
  onDrill: (id: string) => void;
}

const AREA_ICONS: Record<string, React.ReactNode> = {
  startup: <Clock className="h-3.5 w-3.5" />,
  frontend: <Activity className="h-3.5 w-3.5" />,
  backend: <Database className="h-3.5 w-3.5" />,
  agents: <Cpu className="h-3.5 w-3.5" />,
  plugins: <Beaker className="h-3.5 w-3.5" />,
  load: <Zap className="h-3.5 w-3.5" />,
  soak: <Clock className="h-3.5 w-3.5" />,
  chaos: <AlertTriangle className="h-3.5 w-3.5" />,
  recovery: <RotateCcw className="h-3.5 w-3.5" />,
  scalability: <TrendingUp className="h-3.5 w-3.5" />,
  resources: <Gauge className="h-3.5 w-3.5" />,
  regression: <FileText className="h-3.5 w-3.5" />,
};

export function PerfOverviewPanel({ perf, onReset, onDrill }: Props) {
  const { certification } = perf;
  const isCertified = certification.status === "certified";
  const isConditional = certification.status === "conditional";

  return (
    <PanelGrid>
      {/* Hero */}
      <Panel
        title="Stage 15.6 — Production Performance Certification"
        subtitle="Prove ATHENA-X is production-ready across 12 certification areas + performance budget"
        icon={<Award className="h-3.5 w-3.5" />}
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
            <ScoreRing score={certification.overallScore} size={120} label="certified" />
            <div className="mt-2 text-[10.5px] font-mono text-muted-foreground text-center">
              {certification.criticalFailures} critical · {certification.warnings} warnings
            </div>
          </div>

          <div className="md:col-span-2 space-y-3">
            <div className="rounded-md border border-border/60 bg-background/40 p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10.5px] uppercase tracking-wider text-muted-foreground">Certification Verdict</span>
                <StatusBadge status={isCertified ? "pass" : isConditional ? "warn" : "fail"} />
              </div>
              <div className="text-[18px] font-semibold" style={{
                color: isCertified ? "#34d399" : isConditional ? "#fbbf24" : "#f87171",
              }}>
                {isCertified ? "✓ CERTIFIED" : isConditional ? "⚠ CONDITIONAL" : "✗ NOT CERTIFIED"}
              </div>
              <div className="text-[10.5px] font-mono text-muted-foreground mt-1">
                Build {certification.buildHash} · v{certification.version}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[10.5px] font-mono">
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">Budget Compliance</div>
                <div className="text-foreground mt-0.5">{(certification.budgetCompliance * 100).toFixed(0)}%</div>
              </div>
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">Cert Areas</div>
                <div className="text-foreground mt-0.5">{certification.areas.length} / 12</div>
              </div>
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">Budget Items</div>
                <div className="text-foreground mt-0.5">{certification.budget.length}</div>
              </div>
            </div>
          </div>
        </div>
      </Panel>

      {/* Quick stats */}
      <Panel
        title="Live Metrics"
        subtitle="Snapshot"
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
      >
        <div className="grid grid-cols-2 gap-2">
          <Stat label="Agents Tested" value={perf.agents.length} intent="info" />
          <Stat label="Plugins Tested" value={perf.plugins.length} intent="info" />
          <Stat label="Load Tiers" value={perf.loadTests.length} />
          <Stat label="Soak Durations" value={perf.soak.length} />
          <Stat label="Chaos Tests" value={perf.chaos.length} />
          <Stat label="Recovery Checks" value={perf.recovery.length} />
          <Stat label="Budget Items" value={perf.budget ? perf.certification.budget.length : 0} intent="info" />
          <Stat label="Regression Checks" value={perf.regression.length} />
        </div>
      </Panel>

      {/* 12 area cards */}
      <Panel
        title="Certification Areas"
        subtitle="Click any area to drill into detailed checks"
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {certification.areas.map((area) => (
            <button
              key={area.id}
              onClick={() => onDrill(area.id)}
              className="text-left rounded-md border border-border/50 bg-background/30 p-3 hover:border-primary/40 hover:bg-accent/30 transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-primary/80">{AREA_ICONS[area.id]}</span>
                  <div className="min-w-0">
                    <div className="text-[12px] font-semibold truncate">{area.name}</div>
                    <div className="text-[9.5px] font-mono text-muted-foreground/70">{area.checks.length} checks</div>
                  </div>
                </div>
                <StatusBadge status={area.status} />
              </div>

              <div className="flex items-center gap-3">
                <ScoreRing score={area.score} size={48} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-muted-foreground/80 line-clamp-2 leading-snug">{area.description}</div>
                  <div className="text-[9.5px] font-mono text-muted-foreground/60 mt-1">
                    {area.checks.filter((c) => c.status === "pass").length} of {area.checks.length} passing
                  </div>
                </div>
              </div>

              <div className="mt-2 pt-2 border-t border-border/40">
                <div className="flex items-center justify-between text-[9.5px] font-mono text-muted-foreground">
                  <span>
                    <span style={{ color: "#34d399" }}>{area.checks.filter((c) => c.status === "pass").length}</span> pass
                    {" · "}
                    <span style={{ color: "#fbbf24" }}>{area.checks.filter((c) => c.status === "warn").length}</span> warn
                    {" · "}
                    <span style={{ color: "#f87171" }}>{area.checks.filter((c) => c.status === "fail").length}</span> fail
                  </span>
                  <span className="text-primary">drill in →</span>
                </div>
              </div>
            </button>
          ))}

          {/* Budget card */}
          <button
            onClick={() => onDrill("budget")}
            className="text-left rounded-md border border-primary/40 bg-primary/5 p-3 hover:bg-primary/10 transition-all"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-primary/80"><Gauge className="h-3.5 w-3.5" /></span>
                <div>
                  <div className="text-[9.5px] font-mono text-muted-foreground/70 uppercase tracking-wider">Final</div>
                  <div className="text-[12px] font-semibold truncate">Performance Budget</div>
                </div>
              </div>
              <StatusBadge status={certification.budgetCompliance >= 0.95 ? "pass" : certification.budgetCompliance >= 0.85 ? "warn" : "fail"} />
            </div>

            <div className="flex items-center gap-3">
              <ScoreRing score={certification.budgetCompliance} size={48} />
              <div className="flex-1 min-w-0">
                <div className="text-[10px] text-muted-foreground/80 leading-snug">
                  Budget thresholds vs actuals across frontend, backend, agent, resource
                </div>
                <div className="text-[9.5px] font-mono text-muted-foreground/60 mt-1">
                  {certification.budget.filter((b) => b.status === "pass").length}/{certification.budget.length} within budget
                </div>
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-border/40">
              <div className="flex items-center justify-between text-[9.5px] font-mono text-muted-foreground">
                <span>Budget compliance</span>
                <span className="text-primary">view →</span>
              </div>
            </div>
          </button>
        </div>
      </Panel>
    </PanelGrid>
  );
}
