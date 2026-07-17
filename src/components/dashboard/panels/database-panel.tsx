"use client";

import { Database, Lock } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { StatusDot } from "../status-dot";
import { fmtMs, fmtCompact } from "@/lib/dashboard/format";
import type { DatabaseSchemaMetrics } from "@/lib/dashboard/types";

export function DatabasePanel({ schemas }: { schemas: DatabaseSchemaMetrics[] }) {
  const maxP95 = Math.max(...schemas.map((s) => s.writeP95));
  const avgP50 = schemas.reduce((s, d) => s + d.writeP50, 0) / schemas.length;
  const totalRows = schemas.reduce((s, d) => s + d.totalRows, 0);
  const totalRowsLastMin = schemas.reduce((s, d) => s + d.rowsLastMin, 0);
  const totalQueue = schemas.reduce((s, d) => s + d.writeLockQueue, 0);
  const degraded = schemas.filter((s) => s.state !== "healthy").length;

  return (
    <PanelGrid>
      <Panel
        title="Database Write Latency"
        subtitle={`${schemas.length} schemas · per-schema p50/p95 + write-lock queue`}
        icon={<Database className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-9"
        actions={
          degraded > 0 ? (
            <span className="text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-warning/10 border border-status-warning/30" style={{ color: "#fbbf24" }}>
              {degraded} degraded
            </span>
          ) : null
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[460px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-4 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-3">Schema</div>
            <div className="col-span-2 text-right">p50</div>
            <div className="col-span-2 text-right">p95</div>
            <div className="col-span-2 text-right">Rows/min</div>
            <div className="col-span-2 text-right">Total Rows</div>
            <div className="col-span-1 text-right">Lock Q</div>
          </div>
          {schemas.slice().sort((a, b) => b.writeP95 - a.writeP95).map((s) => (
            <div key={s.schema} className="grid grid-cols-12 px-4 py-2 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-3 flex items-center gap-2 min-w-0">
                <StatusDot state={s.state} pulse={s.state === "healthy"} />
                <span className="font-mono truncate">{s.schema}</span>
              </div>
              <div className="col-span-2 text-right font-mono tabular-nums">{s.writeP50.toFixed(2)}ms</div>
              <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: s.writeP95 < 15 ? "#34d399" : s.writeP95 < 30 ? "#fbbf24" : "#f87171" }}>
                {s.writeP95.toFixed(2)}ms
              </div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{fmtCompact(s.rowsLastMin)}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{fmtCompact(s.totalRows)}</div>
              <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: s.writeLockQueue > 30 ? "#f87171" : s.writeLockQueue > 10 ? "#fbbf24" : "#94a3b8" }}>
                {s.writeLockQueue}
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="Database Health"
        subtitle="Aggregate metrics"
        icon={<Database className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-3"
      >
        <div className="space-y-3">
          <Stat label="Max p95" value={fmtMs(maxP95)} intent={maxP95 < 20 ? "healthy" : maxP95 < 40 ? "warning" : "critical"} />
          <Stat label="Avg p50" value={fmtMs(avgP50)} intent="healthy" />
          <Stat label="Total Rows" value={fmtCompact(totalRows)} />
          <Stat label="Rows/min" value={fmtCompact(totalRowsLastMin)} intent="info" />
          <Stat label="Lock Queue" value={totalQueue} unit="waiting" intent={totalQueue > 30 ? "warning" : "healthy"} />

          <div className="pt-3 mt-3 border-t border-border/40">
            <div className="flex items-center gap-2 mb-2">
              <Lock className="h-3 w-3 text-muted-foreground" />
              <span className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80">Write-lock pressure</span>
            </div>
            <div className="space-y-1.5">
              {schemas.slice().sort((a, b) => b.writeLockQueue - a.writeLockQueue).slice(0, 5).map((s) => {
                const pct = Math.min(100, (s.writeLockQueue / 50) * 100);
                return (
                  <div key={s.schema}>
                    <div className="flex items-center justify-between text-[10px] font-mono mb-0.5">
                      <span className="text-muted-foreground truncate">{s.schema}</span>
                      <span className="text-foreground">{s.writeLockQueue}</span>
                    </div>
                    <div className="h-1 rounded-full bg-background/60 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: pct < 30 ? "#34d399" : pct < 60 ? "#fbbf24" : "#f87171" }} />
                    </div>
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
