"use client";

import { ArrowLeft, Brain, GitBranch, CheckCircle2, AlertTriangle, Zap } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { RootCauseAnalysis, Incident } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  rootCause: RootCauseAnalysis;
  onBack: () => void;
}

const SEVERITY_COLORS: Record<Incident["severity"], string> = {
  low: "#94a3b8",
  medium: "#fbbf24",
  high: "#fb923c",
  critical: "#f87171",
};

const STATUS_COLORS: Record<Incident["status"], string> = {
  investigating: "#fbbf24",
  identified: "#22d3ee",
  resolved: "#34d399",
  false_positive: "#94a3b8",
};

export function OpsRootCausePanel({ rootCause, onBack }: Props) {
  return (
    <PanelGrid>
      <Panel
        title="Automatic Root-Cause Analysis"
        subtitle={`${rootCause.incidents.length} incidents tracked · ${rootCause.activeCount} active · AI confidence ${(rootCause.avgConfidence * 100).toFixed(1)}%`}
        icon={<Brain className="h-3.5 w-3.5" />}
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
        {rootCause.incidents.length === 0 && (
          <div className="text-center py-12">
            <CheckCircle2 className="h-12 w-12 mx-auto mb-3" style={{ color: "#34d399" }} />
            <div className="text-[14px] font-semibold">No incidents</div>
            <div className="text-[11px] text-muted-foreground/70 mt-1">The RCA pipeline has no incidents to analyze.</div>
          </div>
        )}

        <div className="space-y-4">
          {rootCause.incidents.map((inc) => {
            const sevColor = SEVERITY_COLORS[inc.severity];
            const statusColor = STATUS_COLORS[inc.status];
            return (
              <div key={inc.id} className="rounded-md border border-border/40 bg-background/30 overflow-hidden">
                {/* Header */}
                <div className="px-3 py-2 border-b border-border/40 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded" style={{ color: sevColor, backgroundColor: `${sevColor}22`, border: `1px solid ${sevColor}55` }}>
                      {inc.severity}
                    </span>
                    <span className="text-[12px] font-medium truncate">{inc.title}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[9.5px] font-mono text-muted-foreground/70">{fmtAge(Date.now() - inc.startedAt)}</span>
                    <span className="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded" style={{ color: statusColor, backgroundColor: `${statusColor}22` }}>
                      {inc.status}
                    </span>
                  </div>
                </div>

                {/* Root cause */}
                <div className="px-3 py-2 border-b border-border/40">
                  <div className="flex items-start gap-2">
                    <Brain className="h-3.5 w-3.5 mt-0.5 shrink-0" style={{ color: "#22d3ee" }} />
                    <div className="min-w-0 flex-1">
                      <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/70 mb-0.5">AI-Identified Root Cause</div>
                      <div className="text-[11.5px] leading-snug">{inc.rootCause}</div>
                      <div className="text-[9.5px] font-mono mt-1" style={{ color: inc.confidence > 0.85 ? "#34d399" : "#fbbf24" }}>
                        confidence: {(inc.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Causal chain */}
                <div className="px-3 py-2 border-b border-border/40">
                  <div className="flex items-center gap-2 mb-2">
                    <GitBranch className="h-3.5 w-3.5 text-primary/70" />
                    <span className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80">Causal Chain</span>
                  </div>
                  <div className="space-y-1 ml-5">
                    {inc.causalChain.map((event, i) => (
                      <div key={i} className="flex items-start gap-2 text-[10.5px]">
                        <span className="font-mono text-[9px] text-muted-foreground/60 mt-0.5 shrink-0">{i + 1}.</span>
                        <span className="font-mono text-[9px] text-muted-foreground/70 shrink-0">{new Date(event.time).toLocaleTimeString("en-US", { hour12: false })}</span>
                        <span className="flex-1">{event.event}</span>
                        <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-accent/40 text-muted-foreground/80 border border-border/30 shrink-0">{event.service}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Remediation */}
                <div className="px-3 py-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <Zap className="h-3.5 w-3.5 text-primary/70" />
                    <span className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80">Remediation</span>
                    {inc.autoRemediated && (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{ color: "#34d399", backgroundColor: "rgba(52, 211, 153, 0.1)", border: "1px solid rgba(52, 211, 153, 0.3)" }}>
                        auto-remediated
                      </span>
                    )}
                  </div>
                  <div className="space-y-0.5 ml-5">
                    {inc.remediation.map((r, i) => (
                      <div key={i} className="text-[10.5px] text-muted-foreground/90">• {r}</div>
                    ))}
                  </div>

                  <div className="mt-2 pt-2 border-t border-border/20 flex items-center gap-2 flex-wrap">
                    <span className="text-[9px] uppercase tracking-wider text-muted-foreground/60">impacted:</span>
                    {inc.impactedServices.map((s) => (
                      <span key={s} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-accent/40 text-muted-foreground/80 border border-border/30">{s}</span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="RCA Performance"
        icon={<Brain className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Active" value={rootCause.activeCount} intent={rootCause.activeCount === 0 ? "healthy" : "critical"} />
          <Stat label="Last 24h" value={rootCause.last24hCount} intent="info" />
          <Stat label="MTTD" value={`${rootCause.mttdSeconds.toFixed(0)}s`} intent={rootCause.mttdSeconds < 60 ? "healthy" : "warning"} />
          <Stat label="MTTI" value={`${(rootCause.mttiSeconds / 60).toFixed(1)}m`} intent={rootCause.mttiSeconds < 300 ? "healthy" : "warning"} />
          <Stat label="MTTR" value={`${rootCause.mttrMinutes.toFixed(1)}m`} intent={rootCause.mttrMinutes < 5 ? "healthy" : "warning"} />
          <Stat label="AI Confidence" value={`${(rootCause.avgConfidence * 100).toFixed(1)}%`} intent={rootCause.avgConfidence >= 0.85 ? "healthy" : "warning"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Auto-Remediation</div>
          <div className="h-2 rounded-full bg-background/60 overflow-hidden mb-1">
            <div
              className="h-full rounded-full"
              style={{
                width: `${rootCause.autoRemediationRate * 100}%`,
                backgroundColor: rootCause.autoRemediationRate >= 0.8 ? "#34d399" : "#fbbf24",
              }}
            />
          </div>
          <div className="text-[10px] font-mono text-muted-foreground">
            {(rootCause.autoRemediationRate * 100).toFixed(0)}% of incidents auto-remediated
          </div>
        </div>

        <div className="pt-3 mt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">RCA Pipeline</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">1. anomaly detect</span><span style={{ color: "#34d399" }}>✓</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">2. log correlation</span><span style={{ color: "#34d399" }}>✓</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">3. trace analysis</span><span style={{ color: "#34d399" }}>✓</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">4. causal inference</span><span style={{ color: "#34d399" }}>✓</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">5. remediation</span><span style={{ color: "#34d399" }}>✓</span></div>
          </div>
        </div>

        {rootCause.activeCount === 0 && (
          <div className="mt-3 pt-3 border-t border-border/40 rounded-md p-2" style={{ backgroundColor: "rgba(52, 211, 153, 0.08)", border: "1px solid rgba(52, 211, 153, 0.3)" }}>
            <div className="text-[10px] font-semibold" style={{ color: "#34d399" }}>✓ No active incidents</div>
            <div className="text-[9.5px] font-mono text-muted-foreground/80 mt-0.5">
              All systems nominal
            </div>
          </div>
        )}
      </Panel>
    </PanelGrid>
  );
}
