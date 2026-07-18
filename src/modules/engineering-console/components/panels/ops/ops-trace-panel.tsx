"use client";

import { ArrowLeft, Radio, GitBranch } from "lucide-react";
import { useState } from "react";
import { Panel } from "../../panel";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtTime, fmtMs, fmtAge, fmtNum } from "@/modules/engineering-console/lib/format";
import type { Trace } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  traces: Trace[];
  onBack: () => void;
}

const KIND_COLORS: Record<string, string> = {
  provider: "#22d3ee",
  validator: "#a78bfa",
  normalizer: "#34d399",
  database: "#fbbf24",
  event_bus: "#06b6d4",
  agent: "#fb923c",
  dna: "#ec4899",
  report: "#8b5cf6",
  api: "#94a3b8",
};

export function OpsTracePanel({ traces, onBack }: Props) {
  const [selected, setSelected] = useState<Trace | null>(traces[0] ?? null);

  // Keep selected in sync if traces change
  const current = selected ? traces.find((t) => t.id === selected.id) ?? traces[0] : traces[0];

  return (
    <Panel
      title="End-to-End Traceability"
      subtitle="Correlation IDs span every subsystem — provider → validator → DB → bus → agent → DNA → report"
      icon={<Radio className="h-3.5 w-3.5" />}
      className="col-span-12"
      actions={
        <button
          onClick={onBack}
          className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3 w-3" /> back
        </button>
      }
    >
      <div className="grid grid-cols-12 gap-4">
        {/* Trace list */}
        <div className="col-span-12 lg:col-span-4 rounded-md border border-border/40 overflow-hidden">
          <div className="px-3 py-2 border-b border-border/40 bg-background/40 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 flex items-center gap-2">
            <GitBranch className="h-3 w-3" />
            <span>Recent Traces ({traces.length})</span>
          </div>
          <div className="max-h-[500px] overflow-y-auto scroll-thin divide-y divide-border/30">
            {traces.map((t) => {
              const isSel = current?.id === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setSelected(t)}
                  className={`w-full text-left px-3 py-2 hover:bg-accent/30 transition-colors ${isSel ? "bg-primary/8 border-l-2 border-primary" : ""}`}
                >
                  <div className="flex items-center justify-between gap-2 mb-0.5">
                    <span className="text-[9.5px] font-mono text-muted-foreground/70 truncate">{t.id}</span>
                    <StatusBadge status={t.status === "ok" ? "pass" : t.status === "partial" ? "warn" : "fail"} />
                  </div>
                  <div className="text-[11px] font-medium truncate">{t.trigger}</div>
                  <div className="flex items-center gap-3 mt-1 text-[9.5px] font-mono text-muted-foreground/70">
                    <span>{t.hopCount} hops</span>
                    <span>{fmtMs(t.durationMs)}</span>
                    <span>{fmtTime(t.startTime)}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Trace detail — waterfall */}
        <div className="col-span-12 lg:col-span-8 rounded-md border border-border/40 overflow-hidden">
          <div className="px-3 py-2 border-b border-border/40 bg-background/40 flex items-center justify-between">
            <div className="min-w-0">
              <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/70">Trace Waterfall</div>
              <div className="text-[12px] font-mono font-semibold truncate">{current?.id}</div>
            </div>
            {current && (
              <div className="text-right text-[10px] font-mono text-muted-foreground">
                <div>trigger: <span className="text-foreground">{current.trigger}</span></div>
                <div>duration: <span className="text-foreground">{fmtMs(current.durationMs)}</span></div>
              </div>
            )}
          </div>

          {current && (
            <div className="p-3 max-h-[500px] overflow-y-auto scroll-thin">
              {/* Waterfall visualization */}
              <div className="space-y-1 mb-4">
                {current.spans.map((span, i) => {
                  const color = KIND_COLORS[span.kind] ?? "#94a3b8";
                  const startPct = ((span.startTime - current.startTime) / current.durationMs) * 100;
                  const widthPct = Math.max(2, (span.durationMs / current.durationMs) * 100);
                  return (
                    <div key={span.id} className="grid grid-cols-12 gap-2 items-center text-[10.5px]">
                      <div className="col-span-3 font-mono text-muted-foreground truncate" title={span.name}>
                        <span className="inline-block w-3 text-muted-foreground/50">{i + 1}.</span>
                        {span.name}
                      </div>
                      <div className="col-span-1 text-[9px] font-mono uppercase text-muted-foreground/60">{span.kind}</div>
                      <div className="col-span-6 relative h-5 bg-background/40 rounded">
                        <div
                          className="absolute h-full rounded"
                          style={{
                            left: `${startPct}%`,
                            width: `${widthPct}%`,
                            backgroundColor: color,
                            opacity: span.status === "ok" ? 0.85 : 0.5,
                            border: span.status !== "ok" ? `1px solid #f87171` : "none",
                          }}
                          title={`${span.module} · ${fmtMs(span.durationMs)} · ${span.status}`}
                        />
                        <span className="absolute inset-0 flex items-center justify-end pr-1 text-[9px] font-mono text-foreground/80">
                          {fmtMs(span.durationMs)}
                        </span>
                      </div>
                      <div className="col-span-2 text-right">
                        <StatusBadge status={span.status === "ok" ? "pass" : span.status === "timeout" ? "warn" : "fail"} />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Span details */}
              <div className="border-t border-border/40 pt-3">
                <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Span Details</div>
                <div className="space-y-1.5">
                  {current.spans.map((span, i) => {
                    const color = KIND_COLORS[span.kind] ?? "#94a3b8";
                    return (
                      <div key={span.id} className="rounded-md border border-border/40 bg-background/30 p-2">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
                            <span className="text-[11px] font-medium truncate">{span.name}</span>
                            <span className="text-[9px] font-mono px-1 py-0.5 rounded" style={{ backgroundColor: `${color}22`, color }}>{span.kind}</span>
                          </div>
                          <span className="text-[9.5px] font-mono text-muted-foreground">{fmtMs(span.durationMs)}</span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[9.5px] font-mono">
                          <div><span className="text-muted-foreground/60">id</span> <span className="text-foreground/80">{span.id}</span></div>
                          <div><span className="text-muted-foreground/60">parent</span> <span className="text-foreground/80">{span.parentSpanId ?? "—"}</span></div>
                          <div><span className="text-muted-foreground/60">module</span> <span className="text-foreground/80">{span.module}</span></div>
                          <div><span className="text-muted-foreground/60">started</span> <span className="text-foreground/80">{fmtAge(Date.now() - span.startTime)}</span></div>
                        </div>
                        {Object.keys(span.attributes).length > 0 && (
                          <div className="mt-1.5 pt-1.5 border-t border-border/20">
                            <div className="text-[9px] uppercase tracking-wider text-muted-foreground/60 mb-1">Attributes</div>
                            <div className="flex flex-wrap gap-1">
                              {Object.entries(span.attributes).map(([k, v]) => (
                                <span key={k} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-accent/40 text-muted-foreground/80 border border-border/30">
                                  {k}={String(v)}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {span.events.length > 0 && (
                          <div className="mt-1.5 pt-1.5 border-t border-border/20">
                            <div className="text-[9px] uppercase tracking-wider text-muted-foreground/60 mb-1">Events</div>
                            {span.events.map((ev, j) => (
                              <div key={j} className="text-[10px] font-mono" style={{ color: "#f87171" }}>
                                ⚠ {ev.name}: {ev.detail}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Panel>
  );
}
