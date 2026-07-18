"use client";

import { ArrowLeft, Zap, CheckCircle2, AlertTriangle } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtMs, fmtAge } from "@/modules/engineering-console/lib/format";
import type { StartupDiagnostics } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  startup: StartupDiagnostics;
  onBack: () => void;
}

export function OpsStartupPanel({ startup, onBack }: Props) {
  const allPassed = startup.phases.every((p) => p.status === "pass");

  return (
    <PanelGrid>
      <Panel
        title="Startup Diagnostics"
        subtitle={`Boot ${startup.bootId} · state: ${startup.state} · ${startup.phases.length} phases`}
        icon={<Zap className="h-3.5 w-3.5" />}
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
        {/* Boot sequence visualization */}
        <div className="mb-4">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Boot Sequence (timeline)</div>
          <div className="relative">
            {/* Timeline bar */}
            <div className="h-2 bg-background/40 rounded-full overflow-hidden mb-3">
              <div className="h-full bg-gradient-to-r from-primary/60 to-primary rounded-full" style={{ width: "100%" }} />
            </div>
            {/* Phase markers */}
            <div className="grid grid-cols-12 gap-1">
              {startup.phases.map((p, i) => {
                const widthPct = (p.durationMs / startup.totalDurationMs) * 100;
                return (
                  <div key={p.id} className="text-center">
                    <div className="h-8 rounded-sm flex items-center justify-center text-[8px] font-mono" style={{
                      backgroundColor: p.status === "pass" ? "rgba(52, 211, 153, 0.15)" : "rgba(248, 113, 113, 0.15)",
                      border: `1px solid ${p.status === "pass" ? "rgba(52, 211, 153, 0.3)" : "rgba(248, 113, 113, 0.3)"}`,
                    }} title={`${p.name}: ${fmtMs(p.durationMs)}`}>
                      {i + 1}
                    </div>
                    <div className="text-[7.5px] font-mono text-muted-foreground/70 mt-0.5 truncate">{p.id}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Phase details */}
        <div className="rounded-md border border-border/40 overflow-hidden">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
            <div className="col-span-1">#</div>
            <div className="col-span-3">Phase</div>
            <div className="col-span-3">Dependencies</div>
            <div className="col-span-2 text-right">Duration</div>
            <div className="col-span-2">Started</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {startup.phases.map((p) => (
            <div key={p.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-1 font-mono text-muted-foreground">{p.order}</div>
              <div className="col-span-3 font-medium">{p.name}</div>
              <div className="col-span-3 font-mono text-[9.5px] text-muted-foreground">
                {p.dependencies.length === 0 ? "—" : p.dependencies.join(", ")}
              </div>
              <div className="col-span-2 text-right font-mono tabular-nums">{fmtMs(p.durationMs)}</div>
              <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground/70">{fmtAge(Date.now() - p.startedAt)}</div>
              <div className="col-span-1 flex justify-end">
                <StatusBadge status={p.status === "pass" ? "pass" : "fail"} />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] font-mono">
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-muted-foreground/70 text-[9px] uppercase tracking-wider">Boot ID</div>
            <div className="text-foreground truncate">{startup.bootId}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-muted-foreground/70 text-[9px] uppercase tracking-wider">Total Duration</div>
            <div className="text-foreground">{fmtMs(startup.totalDurationMs)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-muted-foreground/70 text-[9px] uppercase tracking-wider">Migrations</div>
            <div className="text-foreground">{startup.migrationsApplied} applied</div>
          </div>
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-muted-foreground/70 text-[9px] uppercase tracking-wider">Plugins Loaded</div>
            <div className="text-foreground">{startup.pluginsLoaded}</div>
          </div>
        </div>
      </Panel>

      <Panel
        title="Boot Health"
        icon={<Zap className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Services Ready" value={`${startup.servicesReady}/${startup.servicesTotal}`} intent="healthy" />
          <Stat label="Config Loaded" value={startup.configLoaded ? "Yes" : "No"} intent={startup.configLoaded ? "healthy" : "critical"} />
          <Stat label="Phases Passed" value={startup.phases.filter((p) => p.status === "pass").length} unit={`/ ${startup.phases.length}`} intent="healthy" />
          <Stat label="Boot Time" value={fmtMs(startup.totalDurationMs)} intent={startup.totalDurationMs < 30_000 ? "healthy" : "warning"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="flex items-center gap-2 mb-2">
            {allPassed ? (
              <CheckCircle2 className="h-4 w-4" style={{ color: "#34d399" }} />
            ) : (
              <AlertTriangle className="h-4 w-4" style={{ color: "#fbbf24" }} />
            )}
            <span className="text-[11px] font-semibold">
              {allPassed ? "All boot phases passed" : "Some boot phases failed"}
            </span>
          </div>
          <div className="text-[10px] text-muted-foreground leading-relaxed">
            {allPassed
              ? "Last boot completed successfully with all 12 phases passing. System is in running state."
              : "Investigate failed phases before relying on the system."}
          </div>
        </div>

        <div className="pt-3 mt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Boot Policy</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">retry</span><span>3 attempts</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">backoff</span><span>exponential</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">timeout</span><span>60s per phase</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">health gate</span><span>required</span></div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
