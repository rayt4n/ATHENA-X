"use client";

import { useEffect, useState, useCallback } from "react";
import { FileText, Download, RefreshCw, ArrowRight, Filter, Calendar, Hash, Beaker, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { StoredReport, ReportTypeId, ReportManifest } from "@/modules/report-engine/lib/types";

interface ReportViewerProps {
  /** Restrict to a specific report type — used by the engineering console */
  restrictToType?: ReportTypeId;
}

export function ReportViewer({ restrictToType }: ReportViewerProps) {
  const [reports, setReports] = useState<StoredReport[]>([]);
  const [manifests, setManifests] = useState<ReportManifest[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [filter, setFilter] = useState<ReportTypeId | "all">(restrictToType ?? "all");
  const [selected, setSelected] = useState<StoredReport | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<"markdown" | "json">("markdown");
  const [selectedContent, setSelectedContent] = useState<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const url = filter === "all"
        ? "/api/reports"
        : `/api/reports?type=${filter}`;
      const res = await fetch(url);
      const data = await res.json();
      setReports(data.reports ?? []);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const loadManifests = useCallback(async () => {
    const res = await fetch("/api/report-templates");
    const data = await res.json();
    setManifests(data.templates ?? []);
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { loadManifests(); }, [loadManifests]);

  const generate = async (type: ReportTypeId, eventSubtype?: string) => {
    setGenerating(`${type}${eventSubtype ? `-${eventSubtype}` : ""}`);
    try {
      const res = await fetch("/api/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, eventSubtype }),
      });
      if (!res.ok) {
        const err = await res.json();
        alert(`Generation failed: ${err.error}`);
        return;
      }
      await load();
    } finally {
      setGenerating(null);
    }
  };

  const viewReport = async (report: StoredReport, format: "markdown" | "json") => {
    setSelected(report);
    setSelectedFormat(format);
    const res = await fetch(`/api/reports/${report.id}?format=${format}`);
    setSelectedContent(await res.text());
  };

  const downloadPdf = async (report: StoredReport) => {
    const res = await fetch(`/api/reports/${report.id}/pdf`);
    if (!res.ok) {
      alert("PDF generation failed");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.content.id}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid grid-cols-12 gap-4">
      {/* Generate panel */}
      <section className="col-span-12 rounded-lg border border-border bg-card/60 backdrop-blur-sm p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Beaker className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold uppercase tracking-wide">Generate Report</h2>
          </div>
          <button
            onClick={load}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[11px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className="h-3 w-3" /> refresh
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
          {manifests.map((m) => (
            <button
              key={m.type}
              onClick={() => m.acceptsEventSubtype ? generate(m.type, "cpi") : generate(m.type)}
              disabled={generating !== null}
              className="text-left rounded-md border border-border/50 bg-background/40 p-2.5 hover:border-primary/40 hover:bg-accent/30 transition-all disabled:opacity-50"
            >
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70 mb-0.5">{m.trigger.kind}</div>
              <div className="text-[12px] font-medium mb-1">{m.name}</div>
              <div className="text-[9.5px] text-muted-foreground/70 line-clamp-2 leading-tight">{m.description.split(".")[0]}</div>
              {generating === m.type && (
                <div className="mt-1 text-[9px] text-primary font-mono">generating…</div>
              )}
            </button>
          ))}
        </div>
      </section>

      {/* Filter bar */}
      <section className="col-span-12 flex items-center gap-2">
        <Filter className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-[11px] font-mono text-muted-foreground">filter:</span>
        <button
          onClick={() => setFilter("all")}
          className={`px-2 py-0.5 rounded text-[11px] font-mono ${filter === "all" ? "bg-primary/15 text-primary border border-primary/30" : "bg-background/40 text-muted-foreground border border-border/40 hover:text-foreground"}`}
        >
          all
        </button>
        {manifests.map((m) => (
          <button
            key={m.type}
            onClick={() => setFilter(m.type)}
            className={`px-2 py-0.5 rounded text-[11px] font-mono ${filter === m.type ? "bg-primary/15 text-primary border border-primary/30" : "bg-background/40 text-muted-foreground border border-border/40 hover:text-foreground"}`}
          >
            {m.type}
          </button>
        ))}
        <span className="ml-auto text-[10.5px] font-mono text-muted-foreground">
          {loading ? "loading…" : `${reports.length} report${reports.length === 1 ? "" : "s"}`}
        </span>
      </section>

      {/* Reports list */}
      <section className="col-span-12 lg:col-span-5 rounded-lg border border-border bg-card/60 overflow-hidden">
        <div className="px-3 py-2 border-b border-border/60 bg-card/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-3.5 w-3.5 text-primary" />
            <h3 className="text-[11px] font-semibold uppercase tracking-wide">Stored Reports</h3>
          </div>
        </div>
        <div className="max-h-[600px] overflow-y-auto scroll-thin divide-y divide-border/30">
          {loading && (
            <div className="px-3 py-8 text-center text-[11px] text-muted-foreground/70 font-mono">loading…</div>
          )}
          {!loading && reports.length === 0 && (
            <div className="px-3 py-12 text-center">
              <FileText className="h-8 w-8 mx-auto mb-2 text-muted-foreground/30" />
              <div className="text-[11px] font-mono text-muted-foreground/70">no reports yet</div>
              <div className="text-[10px] text-muted-foreground/50 mt-1">click a report type above to generate one</div>
            </div>
          )}
          {reports.map((r) => (
            <button
              key={r.id}
              onClick={() => viewReport(r, "markdown")}
              className={`w-full text-left px-3 py-2 hover:bg-accent/30 transition-colors ${selected?.id === r.id ? "bg-primary/8 border-l-2 border-primary" : ""}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                      {r.content.type}
                    </span>
                    {r.content.eventSubtype && (
                      <span className="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-status-warning/10 border border-status-warning/30" style={{ color: "#fbbf24" }}>
                        {r.content.eventSubtype}
                      </span>
                    )}
                    <span className="text-[9px] font-mono uppercase tracking-wider"
                          style={{ color: r.status === "published" ? "#34d399" : r.status === "archived" ? "#6b7280" : "#22d3ee" }}>
                      {r.status}
                    </span>
                  </div>
                  <div className="text-[12px] font-medium mt-1 truncate">{r.content.title}</div>
                  <div className="flex items-center gap-3 mt-1 text-[9.5px] font-mono text-muted-foreground/70">
                    <span className="flex items-center gap-1"><Calendar className="h-2.5 w-2.5" />{r.content.sessionDate}</span>
                    <span className="flex items-center gap-1"><Clock className="h-2.5 w-2.5" />{fmtAge(Date.now() - r.createdAt)}</span>
                    <span className="flex items-center gap-1"><Hash className="h-2.5 w-2.5" />{r.audit.hash.slice(0, 8)}</span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Report viewer */}
      <section className="col-span-12 lg:col-span-7 rounded-lg border border-border bg-card/60 overflow-hidden flex flex-col">
        <div className="px-3 py-2 border-b border-border/60 bg-card/40 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="h-3.5 w-3.5 text-primary shrink-0" />
            <h3 className="text-[11px] font-semibold uppercase tracking-wide truncate">
              {selected ? selected.content.title : "Select a report"}
            </h3>
          </div>
          {selected && (
            <div className="flex items-center gap-1.5 shrink-0">
              <div className="flex rounded-md border border-border/60 overflow-hidden">
                <button
                  onClick={() => viewReport(selected, "markdown")}
                  className={`px-2 py-0.5 text-[10px] font-mono ${selectedFormat === "markdown" ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground"}`}
                >
                  md
                </button>
                <button
                  onClick={() => viewReport(selected, "json")}
                  className={`px-2 py-0.5 text-[10px] font-mono ${selectedFormat === "json" ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground"}`}
                >
                  json
                </button>
              </div>
              <button
                onClick={() => downloadPdf(selected)}
                className="flex items-center gap-1 px-2 py-0.5 rounded-md border border-border/60 hover:bg-accent/50 text-[10px] font-mono text-muted-foreground hover:text-foreground transition-colors"
                title="Download PDF"
              >
                <Download className="h-3 w-3" /> pdf
              </button>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto scroll-thin p-4 min-h-[500px]">
          {!selected && (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <FileText className="h-12 w-12 mx-auto mb-3 text-muted-foreground/20" />
              <div className="text-[12px] text-muted-foreground/70 font-mono">no report selected</div>
              <div className="text-[10.5px] text-muted-foreground/50 mt-1">click a report on the left to view</div>
            </div>
          )}
          {selected && selectedFormat === "markdown" && (
            <pre className="text-[11px] font-mono leading-relaxed whitespace-pre-wrap text-foreground/90">{selectedContent}</pre>
          )}
          {selected && selectedFormat === "json" && (
            <pre className="text-[10.5px] font-mono leading-relaxed whitespace-pre-wrap text-foreground/90">{selectedContent}</pre>
          )}
        </div>

        {selected && (
          <div className="px-3 py-2 border-t border-border/60 bg-card/40 grid grid-cols-2 md:grid-cols-4 gap-2 text-[9.5px] font-mono text-muted-foreground">
            <div><span className="text-muted-foreground/60">schema</span> <span className="text-foreground/80">{selected.audit.schemaVersion}</span></div>
            <div><span className="text-muted-foreground/60">generator</span> <span className="text-foreground/80 truncate">{selected.audit.generatorVersion}</span></div>
            <div><span className="text-muted-foreground/60">build</span> <span className="text-foreground/80 truncate">{selected.audit.buildVersion}</span></div>
            <div><span className="text-muted-foreground/60">hash</span> <span className="text-foreground/80">{selected.audit.hash.slice(0, 16)}…</span></div>
          </div>
        )}
      </section>

      {/* Audit trail */}
      {selected && (
        <section className="col-span-12 rounded-lg border border-border bg-card/60 overflow-hidden">
          <div className="px-3 py-2 border-b border-border/60 bg-card/40 flex items-center gap-2">
            <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
            <h3 className="text-[11px] font-semibold uppercase tracking-wide">Audit Trail — DNA Versions</h3>
          </div>
          <div className="p-3 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
            {Object.entries(selected.audit.dnaVersions).map(([id, version]) => {
              const snap = selected.content.dnaSnapshot[id as keyof typeof selected.content.dnaSnapshot];
              const conf = snap.confidence;
              return (
                <div key={id} className="rounded-md border border-border/40 bg-background/30 p-2">
                  <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">{id}</div>
                  <div className="text-[10.5px] font-mono text-foreground mt-0.5 truncate" title={version}>{version}</div>
                  <div className="text-[10px] font-mono tabular-nums mt-0.5" style={{ color: conf >= 0.75 ? "#34d399" : conf >= 0.55 ? "#fbbf24" : "#f87171" }}>
                    {(conf * 100).toFixed(1)}%
                  </div>
                </div>
              );
            })}
          </div>
          <div className="px-3 pb-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] font-mono">
            <div className="rounded-md border border-border/40 bg-background/30 p-2">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">workspace</div>
              <div className="text-foreground mt-0.5">{selected.audit.workspace}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-background/30 p-2">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">user</div>
              <div className="text-foreground mt-0.5">{selected.audit.user}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-background/30 p-2">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">forecast ver</div>
              <div className="text-foreground mt-0.5 truncate">{selected.audit.forecastVersion}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-background/30 p-2">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">prior version</div>
              <div className="text-foreground mt-0.5">{selected.audit.priorVersion ?? "—"}</div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
