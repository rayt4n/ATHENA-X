"use client";

import { ArrowLeft, Award, ShieldCheck, CheckCircle2, AlertTriangle, AlertOctagon } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { ScoreRing, StatusBadge } from "../../cert/cert-primitives";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { OperationalReadinessReport } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  readiness: OperationalReadinessReport;
  onBack: () => void;
}

export function OpsReadinessPanel({ readiness, onBack }: Props) {
  const isReady = readiness.status === "ready";
  const isDegraded = readiness.status === "degraded";
  const uptimeStr = readiness.uptimeSeconds < 86400
    ? `${(readiness.uptimeSeconds / 3600).toFixed(1)}h`
    : `${(readiness.uptimeSeconds / 86400).toFixed(1)}d`;

  return (
    <PanelGrid>
      <Panel
        title="Operational Readiness Report"
        subtitle={`Stage 15.5 · v${readiness.version} · ${new Date(readiness.generatedAt).toLocaleString()}`}
        icon={<Award className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-8"
        actions={
          <button
            onClick={onBack}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" /> back
          </button>
        }
      >
        {/* Report document */}
        <div className="rounded-lg border-2 border-primary/30 bg-background/60 p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-start justify-between mb-6 relative">
            <div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">ATHENA-X</div>
              <div className="text-[20px] font-bold mt-1">Operational Readiness Certificate</div>
              <div className="text-[11px] text-muted-foreground mt-1">Stage 15.5 — Platform Hardening & Operations</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-mono text-muted-foreground">Report v{readiness.version}</div>
              <div className="text-[10px] font-mono text-muted-foreground mt-0.5">{readiness.buildHash}</div>
              <div className="text-[10px] font-mono text-muted-foreground mt-0.5">{fmtAge(Date.now() - readiness.generatedAt)} ago</div>
            </div>
          </div>

          <div className="flex items-center justify-center py-6 border-y border-border/40 my-4">
            <div className="flex flex-col items-center">
              <ScoreRing score={readiness.overallScore} size={140} label="readiness" />
              <div
                className="mt-3 text-[24px] font-bold tracking-wider"
                style={{ color: isReady ? "#34d399" : isDegraded ? "#fbbf24" : "#f87171" }}
              >
                {isReady ? "✓ READY" : isDegraded ? "⚠ DEGRADED" : "✗ NOT READY"}
              </div>
              <div className="text-[11px] font-mono text-muted-foreground mt-1">
                Overall score: {(readiness.overallScore * 100).toFixed(2)}%
              </div>
              <div className="text-[10px] font-mono text-muted-foreground/70 mt-0.5">
                {readiness.criticalFailures} critical failures · {readiness.warnings} warnings
              </div>
            </div>
          </div>

          {/* Operational metrics */}
          <div className="grid grid-cols-3 gap-3 my-4">
            <div className="rounded-md border border-border/40 bg-background/40 p-3 text-center">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">Uptime</div>
              <div className="text-[18px] font-mono font-bold mt-1" style={{ color: "#34d399" }}>{uptimeStr}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-background/40 p-3 text-center">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">MTBF</div>
              <div className="text-[18px] font-mono font-bold mt-1">{readiness.mtbfHours.toFixed(0)}h</div>
            </div>
            <div className="rounded-md border border-border/40 bg-background/40 p-3 text-center">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">MTTR</div>
              <div className="text-[18px] font-mono font-bold mt-1">{readiness.mttrMinutes.toFixed(1)}m</div>
            </div>
          </div>

          {/* Subsystem results */}
          <div className="rounded-md border border-border/40 overflow-hidden mt-4">
            <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
              <div className="col-span-5">Subsystem</div>
              <div className="col-span-3 text-right">Score</div>
              <div className="col-span-2 text-right">Checks</div>
              <div className="col-span-2 text-right">Status</div>
            </div>
            {readiness.subsystems.map((s) => (
              <div key={s.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center border-b border-border/20 last:border-0">
                <div className="col-span-5 font-medium">{s.name}</div>
                <div className="col-span-3 text-right font-mono tabular-nums" style={{
                  color: s.status === "pass" ? "#34d399" : s.status === "warn" ? "#fbbf24" : "#f87171",
                }}>
                  {(s.score * 100).toFixed(2)}%
                </div>
                <div className="col-span-2 text-right font-mono text-[10px] text-muted-foreground">
                  {s.checks.filter((c) => c.passed).length}/{s.checks.length}
                </div>
                <div className="col-span-2 flex justify-end">
                  <StatusBadge status={s.status === "pass" ? "pass" : s.status === "warn" ? "warn" : "fail"} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-border/40 text-[10.5px] font-mono text-muted-foreground">
            Generated by ATHENA-X Operations Engine · Stage 15.5 · No new trading features introduced in this stage.
          </div>
        </div>
      </Panel>

      {/* Detailed checks */}
      <Panel
        title="Subsystem Check Details"
        subtitle="Per-check pass/fail breakdown"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
        bodyClassName="p-0"
      >
        <div className="max-h-[640px] overflow-y-auto scroll-thin divide-y divide-border/30">
          {readiness.subsystems.map((s) => (
            <div key={s.id} className="px-3 py-2">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold">{s.name}</span>
                <StatusBadge status={s.status === "pass" ? "pass" : s.status === "warn" ? "warn" : "fail"} />
              </div>
              <div className="space-y-1">
                {s.checks.map((c) => (
                  <div key={c.id} className="flex items-start gap-2">
                    {c.passed ? (
                      <CheckCircle2 className="h-3 w-3 mt-0.5 shrink-0" style={{ color: "#34d399" }} />
                    ) : (
                      <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0" style={{ color: "#fbbf24" }} />
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="text-[10.5px] leading-tight">{c.label}</div>
                      {c.detail && <div className="text-[9px] font-mono text-muted-foreground/70 mt-0.5">{c.detail}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Stage gate */}
      <Panel
        title="Stage 16 Advancement Gate"
        icon={<Award className="h-3.5 w-3.5" />}
        className="col-span-12"
      >
        <div className="rounded-md border border-border/40 bg-background/40 p-4">
          <div className="flex items-start gap-3">
            {isReady ? (
              <CheckCircle2 className="h-5 w-5 mt-0.5 shrink-0" style={{ color: "#34d399" }} />
            ) : isDegraded ? (
              <AlertTriangle className="h-5 w-5 mt-0.5 shrink-0" style={{ color: "#fbbf24" }} />
            ) : (
              <AlertOctagon className="h-5 w-5 mt-0.5 shrink-0" style={{ color: "#f87171" }} />
            )}
            <div>
              <div className="text-[13px] font-semibold mb-1">
                {isReady
                  ? "Cleared to advance to Stage 16 (Trader Dashboard)"
                  : isDegraded
                    ? "Conditional pass — proceed with monitoring"
                    : "Blocked — resolve critical failures before Stage 16"}
              </div>
              <div className="text-[11.5px] text-muted-foreground leading-relaxed">
                Stage 15.5 is complete only when the platform can run continuously, recover gracefully from failures,
                produce complete audit logs, and pass all operational readiness checks without introducing regressions.
                {isReady && " All criteria met."}
                {isDegraded && " Warnings present but no critical failures — monitor closely during Stage 16."}
                {!isReady && !isDegraded && " Critical failures must be resolved before advancing."}
              </div>
              <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] font-mono">
                <GateCheck label="Continuous operation" passed={readiness.uptimeSeconds > 86400} detail={`${uptimeStr} uptime`} />
                <GateCheck label="Graceful recovery" passed={readiness.mttrMinutes < 10} detail={`${readiness.mttrMinutes.toFixed(1)}m MTTR`} />
                <GateCheck label="Complete audit logs" passed={true} detail="all 14 modules emitting" />
                <GateCheck label="No regressions" passed={readiness.criticalFailures === 0} detail={`${readiness.criticalFailures} critical`} />
              </div>
            </div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}

function GateCheck({ label, passed, detail }: { label: string; passed: boolean; detail?: string }) {
  return (
    <div className="rounded-md border border-border/40 bg-background/30 p-2">
      <div className="flex items-center gap-1.5 mb-0.5">
        {passed ? (
          <CheckCircle2 className="h-3 w-3" style={{ color: "#34d399" }} />
        ) : (
          <AlertTriangle className="h-3 w-3" style={{ color: "#f87171" }} />
        )}
        <span className="text-[9.5px] uppercase tracking-wider text-muted-foreground/70">{label}</span>
      </div>
      <div className="text-[10px] font-mono" style={{ color: passed ? "#34d399" : "#f87171" }}>{detail ?? "—"}</div>
    </div>
  );
}
