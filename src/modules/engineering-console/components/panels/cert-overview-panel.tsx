"use client";

import { Award, Beaker, Play, RotateCcw, ShieldCheck, FileDown, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { ScoreRing, StatusBadge } from "../cert/cert-primitives";
import { fmtAge, fmtNum } from "@/modules/engineering-console/lib/format";
import type { CertificationState, ModuleId } from "@/modules/engineering-console/lib/certification-types";
import type { DashboardTelemetry } from "@/modules/engineering-console/lib/types";

interface Props {
  state: CertificationState;
  telemetry: DashboardTelemetry;
  onRun: () => void;
  onReset: () => void;
  onDrill: (id: ModuleId) => void;
  onDownloadPdf: () => void;
  isGeneratingPdf: boolean;
}

const MODULE_ICONS: Record<ModuleId, React.ReactNode> = {
  data: <Beaker className="h-3.5 w-3.5" />,
  intelligence: <Beaker className="h-3.5 w-3.5" />,
  forecast: <Beaker className="h-3.5 w-3.5" />,
  decision: <Beaker className="h-3.5 w-3.5" />,
  stress: <Beaker className="h-3.5 w-3.5" />,
  replay: <Beaker className="h-3.5 w-3.5" />,
  performance: <Beaker className="h-3.5 w-3.5" />,
  certificate: <Award className="h-3.5 w-3.5" />,
};

export function CertificationOverviewPanel({ state, telemetry, onRun, onReset, onDrill, onDownloadPdf, isGeneratingPdf }: Props) {
  const { certificate, modules } = state;
  const isCertified = certificate?.status === "certified";
  const isConditional = certificate?.status === "conditional";

  return (
    <PanelGrid>
      {/* Hero — overall verdict */}
      <Panel
        title="Stage 14.5 — Production Certification"
        subtitle="Institutional acceptance gate before Stage 15 (Report Engine)"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-8"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={onRun}
              disabled={state.isRunning}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-primary text-primary-foreground text-[10.5px] font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Play className="h-3 w-3" />
              {state.isRunning ? "Running…" : "Run Full Certification"}
            </button>
            <button
              onClick={onReset}
              className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
            >
              <RotateCcw className="h-3 w-3" />
              reset
            </button>
          </div>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          <div className="flex flex-col items-center justify-center py-2">
            <ScoreRing score={certificate?.overallScore ?? 0} size={120} label="overall" />
            <div className="mt-2 text-[10.5px] font-mono text-muted-foreground text-center">
              {certificate ? `${certificate.criticalFailures} critical · ${certificate.warnings} warnings` : "—"}
            </div>
          </div>

          <div className="md:col-span-2 space-y-3">
            <div className="rounded-md border border-border/60 bg-background/40 p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10.5px] uppercase tracking-wider text-muted-foreground">Verdict</span>
                {certificate && <StatusBadge status={isCertified ? "pass" : isConditional ? "warn" : "fail"} />}
              </div>
              <div className="text-[18px] font-semibold" style={{
                color: isCertified ? "#34d399" : isConditional ? "#fbbf24" : "#f87171",
              }}>
                {certificate ? (
                  isCertified ? "✓ CERTIFIED" : isConditional ? "⚠ CONDITIONAL" : "✗ NOT CERTIFIED"
                ) : "Awaiting certification run"}
              </div>
              <div className="text-[10.5px] font-mono text-muted-foreground mt-1">
                {certificate ? `Build ${certificate.buildHash} · valid until ${new Date(certificate.validUntil).toLocaleString()}` : "—"}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[10.5px] font-mono">
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">Modules</div>
                <div className="text-foreground mt-0.5">{modules.length} / 8</div>
              </div>
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">Passing</div>
                <div className="text-foreground mt-0.5">{modules.filter((m) => m.status === "pass").length} / {modules.length}</div>
              </div>
              <div className="rounded-md border border-border/40 bg-background/30 p-2">
                <div className="text-muted-foreground text-[9.5px] uppercase tracking-wider">Exit Criteria</div>
                <div className="text-foreground mt-0.5">
                  {certificate ? `${certificate.exitCriteria.filter((e) => e.passed).length} / ${certificate.exitCriteria.length}` : "—"}
                </div>
              </div>
            </div>

            {certificate && (
              <button
                onClick={onDownloadPdf}
                disabled={isGeneratingPdf}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-primary/40 bg-primary/10 text-primary text-[11px] font-medium hover:bg-primary/15 transition-colors disabled:opacity-50"
              >
                <FileDown className="h-3.5 w-3.5" />
                {isGeneratingPdf ? "Generating PDF…" : "Download Production Certificate (PDF)"}
              </button>
            )}
          </div>
        </div>
      </Panel>

      {/* Exit criteria summary */}
      <Panel
        title="Exit Criteria"
        subtitle="All 10 must pass to advance to Stage 15"
        icon={<CheckCircle2 className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
        bodyClassName="p-0"
      >
        <div className="max-h-[300px] overflow-y-auto scroll-thin divide-y divide-border/30">
          {certificate?.exitCriteria.map((ec) => (
            <div key={ec.id} className="px-3 py-1.5 flex items-start gap-2">
              {ec.passed ? (
                <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" style={{ color: "#34d399" }} />
              ) : (
                <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" style={{ color: "#f87171" }} />
              )}
              <div className="min-w-0">
                <div className="text-[11px] leading-tight">{ec.label}</div>
                {ec.detail && <div className="text-[9.5px] text-muted-foreground/70 mt-0.5">{ec.detail}</div>}
              </div>
            </div>
          )) ?? (
            <div className="px-3 py-6 text-center text-[11px] text-muted-foreground/70 font-mono">
              Run certification to evaluate exit criteria
            </div>
          )}
        </div>
      </Panel>

      {/* 8 module cards */}
      <Panel
        title="Certification Modules"
        subtitle="Click any module to drill into detailed checks"
        icon={<Beaker className="h-3.5 w-3.5" />}
        className="col-span-12"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {modules.map((m) => (
            <button
              key={m.id}
              onClick={() => onDrill(m.id)}
              className="text-left rounded-md border border-border/50 bg-background/30 p-3 hover:border-primary/40 hover:bg-accent/30 transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-primary/80">{MODULE_ICONS[m.id]}</span>
                  <div className="min-w-0">
                    <div className="text-[9.5px] font-mono text-muted-foreground/70 uppercase tracking-wider">Module {m.index}</div>
                    <div className="text-[12px] font-semibold truncate">{m.name}</div>
                  </div>
                </div>
                <StatusBadge status={m.status} />
              </div>

              <div className="flex items-center gap-3">
                <ScoreRing score={m.score} size={48} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-muted-foreground/80 line-clamp-2 leading-snug">{m.description}</div>
                  <div className="text-[9.5px] font-mono text-muted-foreground/60 mt-1">
                    {m.checks.length} checks · {fmtNum(m.durationMs ?? 0, 0)}ms
                  </div>
                </div>
              </div>

              <div className="mt-2 pt-2 border-t border-border/40">
                <div className="flex items-center justify-between text-[9.5px] font-mono text-muted-foreground">
                  <span>
                    <span style={{ color: "#34d399" }}>{m.checks.filter((c) => c.status === "pass").length}</span> pass
                    {" · "}
                    <span style={{ color: "#fbbf24" }}>{m.checks.filter((c) => c.status === "warn").length}</span> warn
                    {" · "}
                    <span style={{ color: "#f87171" }}>{m.checks.filter((c) => c.status === "fail").length}</span> fail
                  </span>
                  <span className="text-primary">drill in →</span>
                </div>
              </div>
            </button>
          ))}

          {/* Certificate card (always last) */}
          <button
            onClick={() => onDrill("certificate")}
            className="text-left rounded-md border border-primary/40 bg-primary/5 p-3 hover:bg-primary/10 transition-all"
            style={{ boxShadow: "0 0 0 1px rgba(34, 211, 238, 0.1)" }}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-primary/80">{MODULE_ICONS.certificate}</span>
                <div>
                  <div className="text-[9.5px] font-mono text-muted-foreground/70 uppercase tracking-wider">Module 8</div>
                  <div className="text-[12px] font-semibold truncate">Production Certificate</div>
                </div>
              </div>
              {certificate && <StatusBadge status={isCertified ? "pass" : isConditional ? "warn" : "fail"} />}
            </div>

            <div className="flex items-center gap-3">
              <ScoreRing score={certificate?.overallScore ?? 0} size={48} />
              <div className="flex-1 min-w-0">
                <div className="text-[10px] text-muted-foreground/80 leading-snug">
                  Final aggregated verdict across all 7 modules + exit criteria
                </div>
                <div className="text-[9.5px] font-mono text-muted-foreground/60 mt-1">
                  {certificate ? `v${certificate.version} · ${fmtAge(Date.now() - certificate.generatedAt)} ago` : "—"}
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
