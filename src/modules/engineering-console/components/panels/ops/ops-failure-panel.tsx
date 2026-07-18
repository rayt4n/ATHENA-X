"use client";

import { ArrowLeft, Zap, Activity } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { FailureScenario } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  scenarios: FailureScenario[];
  onBack: () => void;
}

export function OpsFailurePanel({ scenarios, onBack }: Props) {
  const passed = scenarios.filter((s) => s.status === "passed").length;
  const failed = scenarios.filter((s) => s.status === "failed").length;
  const notRun = scenarios.filter((s) => s.status === "not_run").length;
  const avgRecovery = scenarios.filter((s) => s.recoveryMs !== undefined).reduce((s, x) => s + (x.recoveryMs ?? 0), 0) / Math.max(1, scenarios.filter((s) => s.recoveryMs !== undefined).length);
  const autoRecoveryRate = scenarios.filter((s) => s.autoRecovered).length / Math.max(1, scenarios.filter((s) => s.status !== "not_run").length);

  return (
    <PanelGrid>
      <Panel
        title="Failure Injection & Recovery"
        subtitle={`${scenarios.length} chaos scenarios · ${passed} passed · ${failed} failed · ${notRun} not run`}
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {scenarios.map((s) => {
            const color = s.status === "passed" ? "#34d399" : s.status === "failed" ? "#f87171" : "#6b7280";
            return (
              <div
                key={s.id}
                className="rounded-md border p-3 transition-colors"
                style={{
                  borderColor: s.status === "passed" ? "rgba(52, 211, 153, 0.2)" : s.status === "failed" ? "rgba(248, 113, 113, 0.3)" : "rgba(107, 114, 128, 0.2)",
                  backgroundColor: s.status === "passed" ? "rgba(52, 211, 153, 0.03)" : s.status === "failed" ? "rgba(248, 113, 113, 0.05)" : "rgba(107, 114, 128, 0.03)",
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="min-w-0">
                    <div className="text-[11.5px] font-semibold">{s.name}</div>
                    <div className="text-[9.5px] text-muted-foreground/70 mt-0.5">{s.description}</div>
                  </div>
                  <StatusBadge status={s.status === "passed" ? "pass" : s.status === "failed" ? "fail" : "pending"} />
                </div>

                {s.lastInjectedAt && (
                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mb-2">
                    <div>
                      <span className="text-muted-foreground/70">last injected</span>
                      <div className="text-foreground/80">{fmtAge(Date.now() - s.lastInjectedAt)}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground/70">recovery</span>
                      <div style={{ color: s.recoveryMs !== undefined && s.recoveryMs < 4000 ? "#34d399" : "#fbbf24" }}>
                        {s.recoveryMs !== undefined ? `${(s.recoveryMs / 1000).toFixed(2)}s` : "—"}
                      </div>
                    </div>
                  </div>
                )}

                {s.findings.length > 0 && (
                  <div className="space-y-0.5 mb-2">
                    {s.findings.map((f, i) => (
                      <div key={i} className="text-[9.5px] text-muted-foreground/80 leading-snug">• {f}</div>
                    ))}
                  </div>
                )}

                <div className="pt-2 border-t border-border/30">
                  <div className="text-[9px] uppercase tracking-wider text-muted-foreground/60 mb-1">Blast Radius</div>
                  <div className="flex flex-wrap gap-1">
                    {s.blastRadius.map((b) => (
                      <span key={b} className="text-[8.5px] font-mono px-1.5 py-0.5 rounded bg-accent/40 text-muted-foreground/80 border border-border/30">
                        {b}
                      </span>
                    ))}
                  </div>
                </div>

                {s.status !== "not_run" && (
                  <div className="mt-2 pt-2 border-t border-border/30 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-muted-foreground/70">auto-recovery</span>
                    <span style={{ color: s.autoRecovered ? "#34d399" : "#f87171" }}>
                      {s.autoRecovered ? "✓ engaged" : "✗ manual"}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="Chaos Engineering Summary"
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Pass Rate" value={`${((passed / scenarios.length) * 100).toFixed(0)}%`} intent={passed / scenarios.length > 0.85 ? "healthy" : "warning"} />
          <Stat label="Avg Recovery" value={`${(avgRecovery / 1000).toFixed(2)}s`} intent={avgRecovery < 4000 ? "healthy" : "warning"} />
          <Stat label="Auto-Recovery" value={`${(autoRecoveryRate * 100).toFixed(0)}%`} intent={autoRecoveryRate > 0.85 ? "healthy" : "warning"} />
          <Stat label="Not Run" value={notRun} intent={notRun > 0 ? "warning" : "healthy"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Test Cadence</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">schedule</span><span>daily 02:00 UTC</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">framework</span><span>chaos-mesh</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">scope</span><span>staging + prod</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">blast limit</span><span>single AZ</span></div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
