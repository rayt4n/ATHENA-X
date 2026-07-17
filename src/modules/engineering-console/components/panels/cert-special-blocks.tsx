"use client";

import { Activity, Zap, AlertOctagon } from "lucide-react";
import type { StressScenario, ReplayScenario, CertModule } from "@/modules/engineering-console/lib/certification-types";
import { StatusBadge, ScoreRing } from "../cert/cert-primitives";

export function StressScenariosBlock({ scenarios }: { scenarios: StressScenario[] }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        <Zap className="h-3.5 w-3.5 text-primary/70" />
        <span className="text-[10.5px] uppercase tracking-wider text-muted-foreground/80">Stress Scenarios</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {scenarios.map((s) => (
          <div key={s.id} className="rounded-md border border-border/40 bg-background/30 p-2.5">
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <div className="min-w-0">
                <div className="text-[11px] font-medium truncate">{s.name}</div>
                <div className="text-[9.5px] text-muted-foreground/70 truncate">{s.description}</div>
              </div>
              <StatusBadge status={s.status} />
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
              <div>
                <span className="text-muted-foreground/70">recovery </span>
                <span style={{ color: s.recoveryMs < 2000 ? "#34d399" : s.recoveryMs < 4000 ? "#fbbf24" : "#f87171" }}>
                  {(s.recoveryMs / 1000).toFixed(2)}s
                </span>
              </div>
              <div>
                <span className="text-muted-foreground/70">blast </span>
                <span className="text-foreground">{s.blastRadius.length}</span>
              </div>
            </div>
            <div className="mt-1.5 space-y-0.5">
              {s.findings.map((f, i) => (
                <div key={i} className="text-[9.5px] text-muted-foreground/80 leading-snug">• {f}</div>
              ))}
            </div>
            <div className="mt-1.5 pt-1.5 border-t border-border/30 flex flex-wrap gap-1">
              {s.blastRadius.map((b) => (
                <span key={b} className="text-[8.5px] font-mono px-1 py-0.5 rounded bg-accent/40 text-muted-foreground/80 border border-border/30">
                  {b}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ReplayScenariosBlock({ scenarios }: { scenarios: ReplayScenario[] }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        <Activity className="h-3.5 w-3.5 text-primary/70" />
        <span className="text-[10.5px] uppercase tracking-wider text-muted-foreground/80">Replay Scenarios</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {scenarios.map((s) => (
          <div key={s.id} className="rounded-md border border-border/40 bg-background/30 p-2.5">
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <div className="min-w-0">
                <div className="text-[11px] font-medium truncate">{s.name}</div>
                <div className="text-[9.5px] text-muted-foreground/70">{s.date} · {s.description}</div>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="text-[12px] font-mono tabular-nums font-semibold" style={{
                  color: s.matchRate >= 0.98 ? "#34d399" : s.matchRate >= 0.95 ? "#fbbf24" : "#f87171",
                }}>
                  {(s.matchRate * 100).toFixed(2)}%
                </span>
                <StatusBadge status={s.status} />
              </div>
            </div>

            <div className="space-y-0.5">
              {s.driftMetrics.map((m) => (
                <div key={m.name} className="grid grid-cols-12 gap-2 text-[9.5px] font-mono py-0.5 border-b border-border/20 last:border-0">
                  <div className="col-span-4 text-muted-foreground/80 truncate">{m.name}</div>
                  <div className="col-span-3 text-right text-muted-foreground">{typeof m.original === "number" && Math.abs(m.original) >= 1000 ? m.original.toExponential(2) : m.original.toFixed(4)}</div>
                  <div className="col-span-3 text-right text-foreground/90">{typeof m.replayed === "number" && Math.abs(m.replayed) >= 1000 ? m.replayed.toExponential(2) : m.replayed.toFixed(4)}</div>
                  <div className="col-span-2 text-right" style={{ color: m.pass ? "#34d399" : "#f87171" }}>
                    {m.pass ? "✓" : "✗"} {(m.drift * 100).toFixed(2)}%
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-1.5 pt-1.5 border-t border-border/30 text-[9.5px] font-mono text-muted-foreground">
              {s.driftMetrics.filter((m) => m.pass).length} / {s.driftMetrics.length} metrics within tolerance · {(s.durationMs / 1000).toFixed(1)}s replay
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function IntelligenceDNABlock({ dnaResults, module }: { dnaResults: CertModule["checks"], module: CertModule }) {
  // dnaResults here is actually module.checks but we want richer info — caller passes dnaResults from state
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        <AlertOctagon className="h-3.5 w-3.5 text-primary/70" />
        <span className="text-[10.5px] uppercase tracking-wider text-muted-foreground/80">7 DNA Object Verification</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-2">
        {module.checks.map((c) => (
          <div key={c.id} className="rounded-md border border-border/40 bg-background/30 p-2 flex flex-col items-center gap-1">
            <ScoreRing score={c.score} size={42} />
            <div className="text-[9.5px] font-semibold truncate w-full text-center">{c.label.replace(" DNA", "")}</div>
            <StatusBadge status={c.status} />
            <div className="text-[9px] text-muted-foreground/70 text-center line-clamp-2 leading-tight mt-0.5">{c.evidence}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
