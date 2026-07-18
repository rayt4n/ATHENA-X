"use client";

import { ArrowLeft, Beaker, ShieldCheck, AlertTriangle } from "lucide-react";
import { useState } from "react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { PluginCategory, PluginRecord } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  plugins: PluginRecord[];
  onBack: () => void;
}

const CATEGORY_COLORS: Record<PluginCategory, string> = {
  ta: "#22d3ee",
  options: "#a78bfa",
  market: "#34d399",
  news: "#fbbf24",
  forecast: "#fb923c",
};

export function OpsPluginsPanel({ plugins, onBack }: Props) {
  const [filter, setFilter] = useState<PluginCategory | "all">("all");

  const verified = plugins.filter((p) => p.integrity === "verified").length;
  const tampered = plugins.filter((p) => p.integrity === "tampered").length;
  const signed = plugins.filter((p) => p.signed).length;
  const active = plugins.filter((p) => p.active).length;
  const avgCoverage = plugins.reduce((s, p) => s + p.testCoverage, 0) / plugins.length;

  const filtered = filter === "all" ? plugins : plugins.filter((p) => p.category === filter);

  const byCategory = (cat: PluginCategory) => plugins.filter((p) => p.category === cat);

  return (
    <PanelGrid>
      <Panel
        title="Plugin Integrity Verification"
        subtitle={`${plugins.length} plugins · ${verified} verified · ${tampered} tampered · ${signed} signed`}
        icon={<Beaker className="h-3.5 w-3.5" />}
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
        {/* Category filter */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] font-mono text-muted-foreground">filter:</span>
          <button
            onClick={() => setFilter("all")}
            className={`px-2 py-0.5 rounded text-[10.5px] font-mono ${filter === "all" ? "bg-primary/15 text-primary border border-primary/30" : "bg-background/40 text-muted-foreground border border-border/40 hover:text-foreground"}`}
          >
            all ({plugins.length})
          </button>
          {(Object.keys(CATEGORY_COLORS) as PluginCategory[]).map((cat) => {
            const count = byCategory(cat).length;
            return (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-2 py-0.5 rounded text-[10.5px] font-mono ${filter === cat ? "border" : "bg-background/40 text-muted-foreground border border-border/40 hover:text-foreground"}`}
                style={filter === cat ? { backgroundColor: `${CATEGORY_COLORS[cat]}22`, color: CATEGORY_COLORS[cat], borderColor: `${CATEGORY_COLORS[cat]}55` } : {}}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>

        <div className="max-h-[500px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-4">Plugin</div>
            <div className="col-span-1">Cat</div>
            <div className="col-span-1">Stage</div>
            <div className="col-span-2">Hash</div>
            <div className="col-span-1 text-right">Coverage</div>
            <div className="col-span-1 text-right">Signed</div>
            <div className="col-span-1 text-right">Active</div>
            <div className="col-span-1 text-right">Integrity</div>
          </div>
          {filtered.slice(0, 100).map((p) => {
            const color = CATEGORY_COLORS[p.category];
            return (
              <div key={p.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
                <div className="col-span-4 font-mono truncate flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                  {p.name}
                </div>
                <div className="col-span-1">
                  <span className="text-[9px] font-mono px-1 py-0.5 rounded" style={{ color, backgroundColor: `${color}22` }}>{p.category}</span>
                </div>
                <div className="col-span-1 font-mono text-[10px] text-muted-foreground">S{p.stage}</div>
                <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground/70 truncate">{p.hash.slice(0, 16)}…</div>
                <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: p.testCoverage >= 0.7 ? "#34d399" : "#fbbf24" }}>
                  {(p.testCoverage * 100).toFixed(0)}%
                </div>
                <div className="col-span-1 text-right">
                  {p.signed ? <span style={{ color: "#34d399" }}>✓</span> : <span style={{ color: "#f87171" }}>✗</span>}
                </div>
                <div className="col-span-1 text-right">
                  {p.active ? <span style={{ color: "#34d399" }}>●</span> : <span className="text-muted-foreground/40">○</span>}
                </div>
                <div className="col-span-1 flex justify-end">
                  <StatusBadge status={p.integrity === "verified" ? "pass" : p.integrity === "tampered" ? "fail" : "pending"} />
                </div>
              </div>
            );
          })}
          {filtered.length > 100 && (
            <div className="px-3 py-2 text-center text-[10px] font-mono text-muted-foreground/70">
              showing first 100 of {filtered.length} — use category filter to narrow
            </div>
          )}
        </div>
      </Panel>

      <Panel
        title="Plugin Integrity Summary"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Total" value={plugins.length} intent="info" />
          <Stat label="Verified" value={verified} intent="healthy" />
          <Stat label="Tampered" value={tampered} intent={tampered > 0 ? "critical" : "healthy"} />
          <Stat label="Signed" value={signed} intent={signed === plugins.length ? "healthy" : "warning"} />
          <Stat label="Active" value={active} />
          <Stat label="Avg Coverage" value={`${(avgCoverage * 100).toFixed(0)}%`} intent={avgCoverage >= 0.7 ? "healthy" : "warning"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">By Category</div>
          <div className="space-y-1.5">
            {(Object.keys(CATEGORY_COLORS) as PluginCategory[]).map((cat) => {
              const items = byCategory(cat);
              const verifiedInCat = items.filter((p) => p.integrity === "verified").length;
              const color = CATEGORY_COLORS[cat];
              return (
                <div key={cat} className="flex items-center justify-between text-[10px] font-mono">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-muted-foreground">{cat}</span>
                  </span>
                  <span style={{ color: verifiedInCat === items.length ? "#34d399" : "#fbbf24" }}>
                    {verifiedInCat}/{items.length}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {tampered > 0 && (
          <div className="mt-3 pt-3 border-t border-border/40 rounded-md p-2" style={{ backgroundColor: "rgba(248, 113, 113, 0.08)", border: "1px solid rgba(248, 113, 113, 0.3)" }}>
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-3 w-3" style={{ color: "#f87171" }} />
              <span className="text-[10px] font-semibold" style={{ color: "#f87171" }}>{tampered} tampered plugin{tampered === 1 ? "" : "s"} detected</span>
            </div>
            <div className="text-[9.5px] font-mono text-muted-foreground/80">
              Active plugins with tampered integrity have been quarantined. Investigate immediately.
            </div>
          </div>
        )}
      </Panel>
    </PanelGrid>
  );
}
