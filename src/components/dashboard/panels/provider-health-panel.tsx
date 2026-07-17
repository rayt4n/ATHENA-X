"use client";

import { Activity, Layers, ArrowRightLeft } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { StatusDot } from "../status-dot";
import { fmtMs, fmtAge, fmtCompact } from "@/lib/dashboard/format";
import type { ProviderStatus } from "@/lib/dashboard/types";

const CATEGORY_LABELS: Record<ProviderStatus["category"], string> = {
  market_data: "Market Data",
  options_data: "Options Data",
  news: "News & Filings",
  macro: "Macro & Rates",
  alt_data: "Alt / Sentiment",
};

export function ProviderHealthPanel({ providers }: { providers: ProviderStatus[] }) {
  const byCategory = (cat: ProviderStatus["category"]) => providers.filter((p) => p.category === cat);
  const totalHealthy = providers.filter((p) => p.state === "healthy").length;
  const totalErrors = providers.reduce((s, p) => s + p.errors5m, 0);

  return (
    <PanelGrid className="grid-cols-12">
      <Panel
        title="Provider Health"
        subtitle={`${providers.length} providers across ${new Set(providers.map((p) => p.category)).size} categories · ${totalHealthy}/${providers.length} healthy`}
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-9"
        actions={
          <span className="text-[10.5px] font-mono text-muted-foreground">
            errors/5m: <span className="text-foreground">{totalErrors}</span>
          </span>
        }
        bodyClassName="p-0"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 divide-x divide-border/30">
          {(Object.keys(CATEGORY_LABELS) as ProviderStatus["category"][]).map((cat) => {
            const items = byCategory(cat);
            if (items.length === 0) return null;
            const healthy = items.filter((p) => p.state === "healthy").length;
            return (
              <div key={cat} className="p-3 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Layers className="h-3 w-3 text-muted-foreground" />
                    <span className="text-[10.5px] font-semibold uppercase tracking-wider">{CATEGORY_LABELS[cat]}</span>
                  </div>
                  <span className="text-[10px] font-mono text-muted-foreground">{healthy}/{items.length}</span>
                </div>
                <div className="space-y-1.5">
                  {items
                    .slice()
                    .sort((a, b) => a.failoverRank - b.failoverRank)
                    .map((p) => (
                      <ProviderRow key={p.id} p={p} />
                    ))}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="Failover Chain Status"
        subtitle="Active vs standby"
        icon={<ArrowRightLeft className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-3"
      >
        <div className="space-y-3">
          <Stat label="Primary Active" value={providers.filter((p) => p.failoverRank === 0 && p.state === "healthy").length} unit={`of ${providers.filter((p) => p.failoverRank === 0).length} chains`} intent="info" />
          <Stat label="Failovers Triggered" value={providers.filter((p) => p.failoverRank > 0 && p.state === "healthy").length} unit="standbys live" intent="warning" />
          <Stat label="Avg Provider Latency" value={fmtMs(providers.filter((p) => p.state !== "down").reduce((s, p) => s + p.latencyMs, 0) / Math.max(1, providers.filter((p) => p.state !== "down").length))} intent="default" />
          <Stat label="Avg Uptime" value={`${(providers.reduce((s, p) => s + p.uptime, 0) / providers.length * 100).toFixed(2)}%`} intent="healthy" />

          <div className="mt-3 pt-3 border-t border-border/40">
            <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Top errors (5m)</div>
            <div className="space-y-1">
              {providers.slice().sort((a, b) => b.errors5m - a.errors5m).slice(0, 4).map((p) => (
                <div key={p.id} className="flex items-center justify-between text-[10.5px] font-mono">
                  <span className="truncate text-muted-foreground">{p.name}</span>
                  <span style={{ color: p.errors5m > 10 ? "#f87171" : p.errors5m > 3 ? "#fbbf24" : "#34d399" }}>
                    {p.errors5m}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}

function ProviderRow({ p }: { p: ProviderStatus }) {
  const rankBadge =
    p.failoverRank === 0 ? "P" :
    p.failoverRank === 1 ? "B1" :
    `B${p.failoverRank}`;

  return (
    <div className="rounded-md border border-border/40 bg-background/30 px-2.5 py-1.5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <StatusDot state={p.state} />
          <span className="text-[11px] font-medium truncate">{p.name}</span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-background/60 border border-border/40 text-muted-foreground">{rankBadge}</span>
          <span className="text-[10px] font-mono tabular-nums text-muted-foreground">{p.tickRate.toFixed(1)}/s</span>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 mt-1 text-[9.5px] font-mono text-muted-foreground/80">
        <div>lat <span className="text-foreground/80">{p.state === "down" ? "—" : fmtMs(p.latencyMs)}</span></div>
        <div>last <span className="text-foreground/80">{fmtAge(p.lastDataMs)}</span></div>
        <div>err <span style={{ color: p.errors5m > 10 ? "#f87171" : p.errors5m > 3 ? "#fbbf24" : "var(--foreground)" }}>{p.errors5m}</span></div>
      </div>
    </div>
  );
}
