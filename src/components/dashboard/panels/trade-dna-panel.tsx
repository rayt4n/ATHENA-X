"use client";

import { ShieldCheck, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { fmtTime, fmtPrice, fmtPct } from "@/lib/dashboard/format";
import type { TradeDNADecision } from "@/lib/dashboard/types";

const STATUS_COLORS: Record<TradeDNADecision["status"], string> = {
  evaluating: "#22d3ee",
  qualified: "#34d399",
  rejected: "#94a3b8",
  triggered: "var(--chart-4)",
  managed: "#fbbf24",
  closed: "var(--foreground)",
};

export function TradeDNAPanel({ decisions }: { decisions: TradeDNADecision[] }) {
  const qualified = decisions.filter((d) => d.status === "qualified" || d.status === "triggered" || d.status === "managed").length;
  const rejected = decisions.filter((d) => d.status === "rejected").length;
  const closed = decisions.filter((d) => d.status === "closed");
  const winRate = closed.length > 0 ? closed.filter((d) => (d.outcomePnl ?? 0) > 0).length / closed.length : 0;
  const avgConf = decisions.reduce((s, d) => s + d.confidence, 0) / Math.max(1, decisions.length);

  return (
    <PanelGrid>
      <Panel
        title="Trade DNA Decisions"
        subtitle="Recent trade intelligence evaluations with confidence + outcome"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-9"
        actions={
          <div className="flex items-center gap-2 text-[10.5px] font-mono">
            <span className="text-muted-foreground">avg conf <span className="text-foreground">{fmtPct(avgConf, 0)}</span></span>
            <span className="text-muted-foreground">qualified <span style={{ color: "#34d399" }}>{qualified}</span></span>
            <span className="text-muted-foreground">rejected <span style={{ color: "#94a3b8" }}>{rejected}</span></span>
          </div>
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[520px] overflow-y-auto scroll-thin divide-y divide-border/20">
          {decisions.map((d) => (
            <TradeDecisionRow key={d.id} d={d} />
          ))}
        </div>
      </Panel>

      <Panel
        title="Decision Outcomes"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-3"
      >
        <div className="space-y-3">
          <Stat label="Win Rate (closed)" value={fmtPct(winRate, 1)} intent={winRate > 0.55 ? "healthy" : "warning"} />
          <Stat label="Closed Trades" value={closed.length} />
          <Stat label="Total P&L" value={`${closed.reduce((s, d) => s + (d.outcomePnl ?? 0), 0).toFixed(2)}R`} intent={closed.reduce((s, d) => s + (d.outcomePnl ?? 0), 0) >= 0 ? "healthy" : "critical"} />

          <div className="pt-3 mt-3 border-t border-border/40">
            <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Pipeline</div>
            <div className="space-y-1.5">
              {(["evaluating", "qualified", "rejected", "triggered", "managed", "closed"] as const).map((s) => {
                const count = decisions.filter((d) => d.status === s).length;
                return (
                  <div key={s} className="flex items-center justify-between text-[10.5px] font-mono">
                    <span className="capitalize text-muted-foreground">{s}</span>
                    <span style={{ color: STATUS_COLORS[s] }}>{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}

function TradeDecisionRow({ d }: { d: TradeDNADecision }) {
  const dirIcon = d.direction === "long" ? <ArrowUpRight className="h-3 w-3" /> : d.direction === "short" ? <ArrowDownRight className="h-3 w-3" /> : <Minus className="h-3 w-3" />;
  const dirColor = d.direction === "long" ? "#34d399" : d.direction === "short" ? "#f87171" : "#94a3b8";

  return (
    <div className="px-4 py-2.5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="font-mono font-semibold text-[12px]">{d.symbol}</span>
          <span className="flex items-center gap-1 text-[10.5px] font-mono px-1.5 py-0.5 rounded border" style={{ color: dirColor, borderColor: `${dirColor}33`, backgroundColor: `${dirColor}0d` }}>
            {dirIcon}{d.direction}
          </span>
          <span className="text-[11px] text-muted-foreground truncate">{d.setup}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10.5px] font-mono px-2 py-0.5 rounded border" style={{ color: STATUS_COLORS[d.status], borderColor: `${STATUS_COLORS[d.status]}33`, backgroundColor: `${STATUS_COLORS[d.status]}0d` }}>
            {d.status}
          </span>
          <span className="text-[9.5px] font-mono text-muted-foreground/70">{fmtTime(d.timestamp)}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2 text-[10.5px] font-mono">
        <div>
          <span className="text-muted-foreground/70">entry </span>
          <span className="tabular-nums">{fmtPrice(d.entry)}</span>
        </div>
        <div>
          <span className="text-muted-foreground/70">stop </span>
          <span className="tabular-nums" style={{ color: "#f87171" }}>{fmtPrice(d.stop)}</span>
        </div>
        <div>
          <span className="text-muted-foreground/70">target </span>
          <span className="tabular-nums" style={{ color: "#34d399" }}>{fmtPrice(d.target)}</span>
        </div>
        <div>
          <span className="text-muted-foreground/70">R/R </span>
          <span className="tabular-nums">{d.rr.toFixed(2)}</span>
          {d.outcomePnl !== undefined && (
            <span className="ml-2 tabular-nums" style={{ color: d.outcomePnl >= 0 ? "#34d399" : "#f87171" }}>
              {d.outcomePnl >= 0 ? "+" : ""}{d.outcomePnl.toFixed(2)}R
            </span>
          )}
        </div>
      </div>

      {/* DNA inputs contribution bar */}
      <div className="mt-2 flex items-center gap-2">
        <span className="text-[9.5px] font-mono text-muted-foreground/70 w-16">DNA inputs</span>
        <div className="flex-1 flex gap-0.5 h-2 rounded-sm overflow-hidden">
          {[
            { label: "TA", val: d.dnaInputs.technical },
            { label: "OPT", val: d.dnaInputs.options },
            { label: "MKT", val: d.dnaInputs.market },
            { label: "NAR", val: d.dnaInputs.narrative },
            { label: "FC", val: d.dnaInputs.forecast },
          ].map((x) => (
            <div key={x.label} className="flex-1 relative bg-background/60 border border-border/30 rounded-sm overflow-hidden" title={`${x.label}: ${(x.val * 100).toFixed(0)}%`}>
              <div
                className="absolute inset-0 rounded-sm"
                style={{
                  width: `${x.val * 100}%`,
                  backgroundColor: x.val > 0.7 ? "#34d399" : x.val > 0.5 ? "#fbbf24" : "#f87171",
                }}
              />
              <span className="absolute inset-0 flex items-center justify-center text-[8.5px] font-mono text-foreground/80">{x.label}</span>
            </div>
          ))}
        </div>
        <span className="text-[10.5px] font-mono tabular-nums font-semibold w-12 text-right" style={{ color: d.confidence > 0.7 ? "#34d399" : d.confidence > 0.5 ? "#fbbf24" : "#f87171" }}>
          {fmtPct(d.confidence, 0)}
        </span>
      </div>

      {d.reasoningTags.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {d.reasoningTags.slice(0, 6).map((tag) => (
            <span key={tag} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-accent/60 text-muted-foreground/80 border border-border/40">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
