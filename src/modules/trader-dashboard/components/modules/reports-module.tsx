"use client";

import { useEffect, useState } from "react";
import { FileText, Download, RefreshCw } from "lucide-react";
import type { ReportsState } from "@/modules/trader-dashboard/lib/workspace-types";
import type { StoredReport, ReportManifest } from "@/modules/report-engine/lib/types";

interface Props {
  state: ReportsState;
  onStateChange: (partial: Partial<ReportsState>) => void;
}

export function ReportsModule({ state, onStateChange }: Props) {
  const filter = state.filter ?? "all";
  const [reports, setReports] = useState<StoredReport[]>([]);
  const [manifests, setManifests] = useState<ReportManifest[]>([]);
  const [selected, setSelected] = useState<StoredReport | null>(null);
  const [selectedContent, setSelectedContent] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [reportsRes, tmplRes] = await Promise.all([
        fetch("/api/reports"),
        fetch("/api/report-templates"),
      ]);
      const reportsData = await reportsRes.json();
      const tmplData = await tmplRes.json();
      setReports(reportsData.reports ?? []);
      setManifests(tmplData.templates ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = reports.filter((r) => filter === "all" || r.content.type === filter);

  const viewReport = async (report: StoredReport) => {
    setSelected(report);
    const res = await fetch(`/api/reports/${report.id}?format=markdown`);
    setSelectedContent(await res.text());
  };

  const generate = async (type: string) => {
    await fetch("/api/reports/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type }),
    });
    await load();
  };

  const downloadPdf = async (report: StoredReport) => {
    const res = await fetch(`/api/reports/${report.id}/pdf`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.content.id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center gap-2">
        <select
          value={filter}
          onChange={(e) => onStateChange({ filter: e.target.value as ReportsState["filter"] })}
          className="bg-background/60 border border-border/40 rounded text-[9px] px-1 py-0.5 font-mono focus:outline-none"
        >
          <option value="all">all reports</option>
          <option value="premarket">pre-market</option>
          <option value="marketopen">market open</option>
          <option value="intraday">intraday</option>
          <option value="event">event</option>
          <option value="endofday">end-of-day</option>
          <option value="weekly">weekly</option>
        </select>
        <button
          onClick={load}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
        >
          <RefreshCw className="h-2.5 w-2.5" /> refresh
        </button>
        <div className="ml-auto flex gap-0.5">
          {manifests.slice(0, 4).map((m) => (
            <button
              key={m.type}
              onClick={() => generate(m.type)}
              className="px-1.5 py-0.5 rounded text-[8.5px] font-mono bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors"
            >
              + {m.type}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* Report list */}
        <div className="col-span-4 border-r border-border/40 overflow-y-auto scroll-thin">
          {loading && <div className="px-3 py-4 text-center text-[10px] text-muted-foreground/70 font-mono">loading…</div>}
          {!loading && filtered.length === 0 && (
            <div className="px-3 py-6 text-center text-[10px] text-muted-foreground/70 font-mono">no reports</div>
          )}
          {filtered.map((r) => (
            <button
              key={r.id}
              onClick={() => viewReport(r)}
              className={`w-full text-left px-3 py-1.5 border-b border-border/20 hover:bg-accent/30 ${selected?.id === r.id ? "bg-primary/8" : ""}`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className="text-[8px] font-mono uppercase tracking-wider px-1 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                  {r.content.type}
                </span>
                <span className="text-[8px] font-mono" style={{ color: r.status === "published" ? "#34d399" : "#22d3ee" }}>{r.status}</span>
              </div>
              <div className="text-[10px] font-medium truncate">{r.content.title}</div>
              <div className="text-[8.5px] font-mono text-muted-foreground/60">{r.content.sessionDate}</div>
            </button>
          ))}
        </div>

        {/* Report content */}
        <div className="col-span-8 overflow-y-auto scroll-thin p-3">
          {!selected && (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <FileText className="h-10 w-10 mx-auto mb-2 text-muted-foreground/20" />
              <div className="text-[11px] text-muted-foreground/70 font-mono">select a report to view</div>
            </div>
          )}
          {selected && (
            <>
              <div className="flex items-center justify-between mb-2">
                <div className="text-[11px] font-semibold">{selected.content.title}</div>
                <button
                  onClick={() => downloadPdf(selected)}
                  className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono border border-border/60 hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Download className="h-2.5 w-2.5" /> pdf
                </button>
              </div>
              <pre className="text-[9px] font-mono leading-relaxed whitespace-pre-wrap text-foreground/80">{selectedContent}</pre>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
