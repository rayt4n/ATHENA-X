"use client";

import { Radio, AlertTriangle } from "lucide-react";
import { Panel } from "../panel";
import { StatusDot } from "../status-dot";
import { fmtAge } from "@/modules/engineering-console/lib/format";
import type { DataFreshnessEntry } from "@/modules/engineering-console/lib/types";

export function DataFreshnessPanel({ entries }: { entries: DataFreshnessEntry[] }) {
  const stale = entries.filter((e) => e.state !== "healthy");
  const avgLagMs = entries.reduce((s, e) => s + (Date.now() - e.lastTick), 0) / Math.max(1, entries.length);

  return (
    <Panel
      title="Live Data Freshness"
      subtitle={`${entries.length} tracked symbols · avg lag ${fmtAge(avgLagMs)}`}
      icon={<Radio className="h-3.5 w-3.5" />}
      actions={
        stale.length > 0 ? (
          <span className="flex items-center gap-1.5 text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-warning/10 border border-status-warning/30" style={{ color: "#fbbf24" }}>
            <AlertTriangle className="h-3 w-3" />
            {stale.length} stale
          </span>
        ) : null
      }
      bodyClassName="p-0"
    >
      <div className="max-h-[460px] overflow-y-auto scroll-thin divide-y divide-border/30">
        <div className="grid grid-cols-12 px-4 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
          <div className="col-span-2">Symbol</div>
          <div className="col-span-2">Class</div>
          <div className="col-span-3">Source</div>
          <div className="col-span-2 text-right">Cadence</div>
          <div className="col-span-2 text-right">Last Tick</div>
          <div className="col-span-1 text-right">State</div>
        </div>
        {entries.map((e) => {
          const age = Date.now() - e.lastTick;
          const overCadence = age > e.cadenceMs;
          return (
            <div key={`${e.symbol}-${e.source}`} className="grid grid-cols-12 px-4 py-1.5 text-[11px] items-center hover:bg-accent/30">
              <div className="col-span-2 font-mono font-semibold">{e.symbol}</div>
              <div className="col-span-2 text-muted-foreground text-[10px] uppercase tracking-wider">{e.assetClass.replace("_", " ")}</div>
              <div className="col-span-3 font-mono text-muted-foreground truncate">{e.source}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{(e.cadenceMs / 1000).toFixed(2)}s</div>
              <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: overCadence ? "#fbbf24" : "var(--foreground)" }}>
                {fmtAge(age)}
              </div>
              <div className="col-span-1 flex justify-end">
                <StatusDot state={e.state} pulse={e.state === "healthy"} />
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
