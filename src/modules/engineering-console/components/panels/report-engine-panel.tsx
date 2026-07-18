"use client";

import { useEffect, useState } from "react";
import { Beaker, FileText, Activity, Hash, Clock, Layers, CheckCircle2, AlertTriangle, FileDown } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { StatusBadge } from "../cert/cert-primitives";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { ReportManifest, ReportEvent, StoredReport, ReportTypeId } from "@/modules/report-engine/lib/types";

interface Props {
  onDrill?: (id: string) => void;
}

export function ReportEnginePanel({ onDrill }: Props) {
  const [stats, setStats] = useState<{
    total: number;
    byType: Record<ReportTypeId, number>;
    byStatus: Record<string, number>;
    recentEvents: ReportEvent[];
  } | null>(null);
  const [manifests, setManifests] = useState<ReportManifest[]>([]);
  const [recent, setRecent] = useState<StoredReport[]>([]);
  const [validation, setValidation] = useState<{ ok: boolean; failures: { type: string; errors: string[] }[] } | null>(null);

  const load = async () => {
    try {
      const [tmplRes, reportsRes] = await Promise.all([
        fetch("/api/report-templates"),
        fetch("/api/reports"),
      ]);
      const tmplData = await tmplRes.json();
      const reportsData = await reportsRes.json();
      setManifests(tmplData.templates ?? []);
      setValidation(tmplData.validation ?? null);
      setRecent((reportsData.reports ?? []).slice(0, 10));

      // Compute stats locally
      const reports: StoredReport[] = reportsData.reports ?? [];
      const byType = {} as Record<ReportTypeId, number>;
      const byStatus: Record<string, number> = {};
      const recentEvents: ReportEvent[] = [];
      for (const r of reports) {
        byType[r.content.type] = (byType[r.content.type] ?? 0) + 1;
        byStatus[r.status] = (byStatus[r.status] ?? 0) + 1;
        recentEvents.push(...r.events);
      }
      recentEvents.sort((a, b) => b.timestamp - a.timestamp);
      setStats({
        total: reports.length,
        byType,
        byStatus,
        recentEvents: recentEvents.slice(0, 15),
      });
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <PanelGrid>
      {/* Hero */}
      <Panel
        title="Stage 15 — Report Engine"
        subtitle="Institutional report generation · read-only · audit-ready"
        icon={<FileText className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-8"
        actions={
          <button
            onClick={load}
            className="text-[10.5px] text-primary hover:underline font-mono"
          >
            refresh
          </button>
        }
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Stat label="Total Reports" value={stats?.total ?? 0} intent="info" />
          <Stat label="Templates Registered" value={manifests.length} intent="info" />
          <Stat label="Published" value={stats?.byStatus.published ?? 0} intent="healthy" />
          <Stat label="Drafts" value={stats?.byStatus.draft ?? 0} intent="warning" />
        </div>

        <div className="mt-4 pt-4 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Engine Principles</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10.5px]">
            <Principle ok label="Read-only — no calculations performed" />
            <Principle ok label="Consumes only canonical DBs + DNA objects" />
            <Principle ok label="Outputs: Markdown + JSON + PDF" />
            <Principle ok label="Audit: hash + DNA versions + schema" />
            <Principle ok label="Event bus: created/updated/failed/published" />
            <Principle ok label="Modular templates — add new types without changing engine" />
            <Principle ok={validation?.ok ?? false} label={validation?.ok ? "All manifests validated" : "Manifest validation issues"} />
            <Principle ok label="Deterministic — same inputs → same hash" />
          </div>
        </div>
      </Panel>

      {/* Validation status */}
      <Panel
        title="Template Registry"
        subtitle={`${manifests.length} manifests loaded`}
        icon={<Layers className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-4"
        bodyClassName="p-0"
      >
        <div className="max-h-[280px] overflow-y-auto scroll-thin divide-y divide-border/30">
          {manifests.map((m) => {
            const count = stats?.byType[m.type] ?? 0;
            return (
              <div key={m.type} className="px-3 py-2">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-[11px] font-medium">{m.name}</span>
                  <StatusBadge status={count > 0 ? "pass" : "pending"} />
                </div>
                <div className="text-[9.5px] font-mono text-muted-foreground/70 flex items-center gap-3">
                  <span>{m.sections.length} sections</span>
                  <span>{m.requiredDNA.length} DNA</span>
                  <span>{m.trigger.kind}</span>
                  <span className="ml-auto">{count} generated</span>
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      {/* Recent reports */}
      <Panel
        title="Recent Reports"
        subtitle="Latest 10 generated"
        icon={<FileText className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-7"
        bodyClassName="p-0"
      >
        <div className="max-h-[400px] overflow-y-auto scroll-thin">
          {recent.length === 0 && (
            <div className="px-3 py-8 text-center text-[11px] text-muted-foreground/70 font-mono">
              no reports generated yet — use the trader dashboard at / to generate one
            </div>
          )}
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-2">Type</div>
            <div className="col-span-4">Title</div>
            <div className="col-span-2">Session</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2 text-right">Created</div>
          </div>
          {recent.map((r) => (
            <div
              key={r.id}
              className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20 cursor-pointer"
              onClick={() => onDrill?.(r.id)}
            >
              <div className="col-span-2">
                <span className="text-[9.5px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                  {r.content.type}
                </span>
              </div>
              <div className="col-span-4 truncate">{r.content.title}</div>
              <div className="col-span-2 font-mono text-[10px] text-muted-foreground">{r.content.sessionDate}</div>
              <div className="col-span-2">
                <StatusBadge status={r.status === "published" ? "pass" : r.status === "archived" ? "pending" : "running"} />
              </div>
              <div className="col-span-2 text-right font-mono text-[10px] text-muted-foreground">{fmtAge(Date.now() - r.createdAt)}</div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Event bus stream */}
      <Panel
        title="Event Bus — Lifecycle"
        subtitle="report:created / updated / failed / published"
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-5"
        bodyClassName="p-0"
      >
        <div className="max-h-[400px] overflow-y-auto scroll-thin divide-y divide-border/30">
          {(!stats?.recentEvents || stats.recentEvents.length === 0) && (
            <div className="px-3 py-8 text-center text-[11px] text-muted-foreground/70 font-mono">
              no events yet — generate a report to populate this stream
            </div>
          )}
          {stats?.recentEvents.map((ev, i) => {
            const color =
              ev.type === "report:created" ? "#22d3ee" :
              ev.type === "report:published" ? "#34d399" :
              ev.type === "report:updated" ? "#fbbf24" :
              "#f87171";
            return (
              <div key={i} className="px-3 py-2 flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 pulse-live" style={{ backgroundColor: color }} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono uppercase tracking-wider" style={{ color }}>
                      {ev.type}
                    </span>
                    <span className="text-[9.5px] font-mono text-muted-foreground/70">{fmtAge(Date.now() - ev.timestamp)}</span>
                  </div>
                  <div className="text-[11px] leading-snug mt-0.5">{ev.detail}</div>
                  {ev.reportHash && (
                    <div className="text-[9px] font-mono text-muted-foreground/60 mt-0.5 flex items-center gap-1">
                      <Hash className="h-2 w-2" /> {ev.reportHash.slice(0, 24)}…
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </PanelGrid>
  );
}

function Principle({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      {ok ? (
        <CheckCircle2 className="h-3 w-3 shrink-0" style={{ color: "#34d399" }} />
      ) : (
        <AlertTriangle className="h-3 w-3 shrink-0" style={{ color: "#f87171" }} />
      )}
      <span className={ok ? "text-foreground/90" : "text-status-critical"}>{label}</span>
    </div>
  );
}
