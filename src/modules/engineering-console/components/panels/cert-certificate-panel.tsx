"use client";

import { ArrowLeft, Award, ShieldCheck, FileDown, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { ScoreRing, StatusBadge } from "../cert/cert-primitives";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { CertificateSummary } from "@/modules/engineering-console/lib/certification-types";

interface Props {
  certificate: CertificateSummary;
  onBack: () => void;
  onDownloadPdf: () => void;
  isGeneratingPdf: boolean;
}

export function CertificatePanel({ certificate, onBack, onDownloadPdf, isGeneratingPdf }: Props) {
  const isCertified = certificate.status === "certified";
  const isConditional = certificate.status === "conditional";

  return (
    <PanelGrid>
      <Panel
        title="Production Readiness Certificate"
        subtitle={`ATHENA-X · Version ${certificate.version} · ${new Date(certificate.generatedAt).toLocaleString()}`}
        icon={<Award className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-8"
        actions={
          <button
            onClick={onBack}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" />
            back
          </button>
        }
      >
        {/* Certificate document */}
        <div className="rounded-lg border-2 border-primary/30 bg-background/60 p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-start justify-between mb-6 relative">
            <div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">ATHENA-X</div>
              <div className="text-[20px] font-bold mt-1">Production Certification</div>
              <div className="text-[11px] text-muted-foreground mt-1">Institutional Acceptance Document</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-mono text-muted-foreground">Certificate v{certificate.version}</div>
              <div className="text-[10px] font-mono text-muted-foreground mt-0.5">{certificate.buildHash}</div>
              <div className="text-[10px] font-mono text-muted-foreground mt-0.5">{certificate.environment}</div>
            </div>
          </div>

          <div className="flex items-center justify-center py-6 border-y border-border/40 my-4">
            <div className="flex flex-col items-center">
              <ScoreRing score={certificate.overallScore} size={140} label="overall" />
              <div
                className="mt-3 text-[24px] font-bold tracking-wider"
                style={{ color: isCertified ? "#34d399" : isConditional ? "#fbbf24" : "#f87171" }}
              >
                {isCertified ? "✓ CERTIFIED" : isConditional ? "⚠ CONDITIONAL" : "✗ NOT CERTIFIED"}
              </div>
              <div className="text-[11px] font-mono text-muted-foreground mt-1">
                Overall score: {(certificate.overallScore * 100).toFixed(2)}%
              </div>
              <div className="text-[10px] font-mono text-muted-foreground/70 mt-0.5">
                {certificate.criticalFailures} critical failures · {certificate.warnings} warnings
              </div>
            </div>
          </div>

          {/* Module results table */}
          <div className="rounded-md border border-border/40 overflow-hidden mt-4">
            <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
              <div className="col-span-6">Module</div>
              <div className="col-span-3 text-right">Score</div>
              <div className="col-span-3 text-right">Status</div>
            </div>
            {certificate.modules.map((m) => (
              <div key={m.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center border-b border-border/20 last:border-0">
                <div className="col-span-6 font-medium">{m.name}</div>
                <div className="col-span-3 text-right font-mono tabular-nums" style={{
                  color: m.status === "pass" ? "#34d399" : m.status === "warn" ? "#fbbf24" : "#f87171",
                }}>
                  {(m.score * 100).toFixed(2)}%
                </div>
                <div className="col-span-3 flex justify-end">
                  <StatusBadge status={m.status} />
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-border/40 grid grid-cols-2 gap-4 text-[10.5px] font-mono text-muted-foreground">
            <div>
              <div className="uppercase tracking-wider text-muted-foreground/70 mb-1">Signed By</div>
              <div className="text-foreground">{certificate.signedBy}</div>
            </div>
            <div className="text-right">
              <div className="uppercase tracking-wider text-muted-foreground/70 mb-1">Valid Until</div>
              <div className="text-foreground">{new Date(certificate.validUntil).toLocaleString()}</div>
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-center">
          <button
            onClick={onDownloadPdf}
            disabled={isGeneratingPdf}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-[12px] font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <FileDown className="h-4 w-4" />
            {isGeneratingPdf ? "Generating PDF…" : "Download Certificate (PDF)"}
          </button>
        </div>
      </Panel>

      {/* Exit criteria sidebar */}
      <Panel
        title="Exit Criteria Verification"
        subtitle={`${certificate.exitCriteria.filter((e) => e.passed).length} of ${certificate.exitCriteria.length} passed`}
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
        bodyClassName="p-0"
      >
        <div className="max-h-[600px] overflow-y-auto scroll-thin divide-y divide-border/30">
          {certificate.exitCriteria.map((ec) => (
            <div key={ec.id} className="px-3 py-2 flex items-start gap-2">
              {ec.passed ? (
                <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" style={{ color: "#34d399" }} />
              ) : (
                <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" style={{ color: "#f87171" }} />
              )}
              <div className="min-w-0">
                <div className="text-[11px] leading-tight">{ec.label}</div>
                {ec.detail && <div className="text-[9.5px] text-muted-foreground/70 mt-0.5 font-mono">{ec.detail}</div>}
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-border/40 p-3">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70 mb-2">Stage Gate</div>
          <div className="rounded-md border border-border/40 bg-background/40 p-3">
            <div className="text-[11px] leading-relaxed">
              {isCertified ? (
                <>
                  All exit criteria passed. Platform is <span style={{ color: "#34d399" }}>cleared to advance</span> to Stage 15 (Report Engine).
                </>
              ) : isConditional ? (
                <>
                  Conditional pass — warnings present but no critical failures. May proceed to Stage 15 with <span style={{ color: "#fbbf24" }}>monitoring</span>.
                </>
              ) : (
                <>
                  <span style={{ color: "#f87171" }}>Blocked</span> — critical failures must be resolved before advancing to Stage 15.
                </>
              )}
            </div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
