"use client";

import { ArrowLeft, Power } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtMs, fmtAge } from "@/modules/engineering-console/lib/format";
import type { GracefulShutdown } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  shutdown: GracefulShutdown;
  onBack: () => void;
}

export function OpsShutdownPanel({ shutdown, onBack }: Props) {
  const isClean = shutdown.lastShutdownStatus === "clean";

  return (
    <PanelGrid>
      <Panel
        title="Graceful Shutdown"
        subtitle={`Last shutdown: ${shutdown.lastShutdownStatus} · ${fmtMs(shutdown.lastShutdownDurationMs)} · ${fmtAge(Date.now() - shutdown.lastShutdownAt)} ago`}
        icon={<Power className="h-3.5 w-3.5" />}
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
        {/* Shutdown sequence timeline */}
        <div className="mb-4">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Shutdown Sequence</div>
          <div className="space-y-1.5">
            {shutdown.phases.map((p) => {
              const color = p.status === "pass" ? "#34d399" : "#f87171";
              const widthPct = Math.max(3, (p.durationMs / shutdown.lastShutdownDurationMs) * 100);
              return (
                <div key={p.id} className="grid grid-cols-12 gap-2 items-center text-[11px]">
                  <div className="col-span-1 font-mono text-muted-foreground text-[9.5px]">{p.order}</div>
                  <div className="col-span-3 font-medium truncate">{p.name}</div>
                  <div className="col-span-5 relative h-5 bg-background/40 rounded">
                    <div
                      className="absolute h-full rounded flex items-center justify-end pr-1.5"
                      style={{ width: `${widthPct}%`, backgroundColor: `${color}55`, border: `1px solid ${color}` }}
                    >
                      <span className="text-[9px] font-mono text-foreground/80">{fmtMs(p.durationMs)}</span>
                    </div>
                  </div>
                  <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground/70 truncate">{p.detail}</div>
                  <div className="col-span-1 flex justify-end">
                    <StatusBadge status={p.status === "pass" ? "pass" : "fail"} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Items processed per phase */}
        <div className="rounded-md border border-border/40 overflow-hidden">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
            <div className="col-span-4">Phase</div>
            <div className="col-span-2 text-right">Duration</div>
            <div className="col-span-2 text-right">Items Processed</div>
            <div className="col-span-4">Detail</div>
          </div>
          {shutdown.phases.map((p) => (
            <div key={p.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-4 font-medium">{p.name}</div>
              <div className="col-span-2 text-right font-mono tabular-nums">{fmtMs(p.durationMs)}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{p.itemsProcessed.toLocaleString()}</div>
              <div className="col-span-4 text-[10px] text-muted-foreground/80 truncate">{p.detail}</div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="Shutdown Health"
        icon={<Power className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Last Status" value={shutdown.lastShutdownStatus} intent={isClean ? "healthy" : "critical"} />
          <Stat label="Duration" value={fmtMs(shutdown.lastShutdownDurationMs)} intent={shutdown.lastShutdownDurationMs < 10_000 ? "healthy" : "warning"} />
          <Stat label="Events Drained" value={shutdown.eventsDrained} intent="info" />
          <Stat label="WS Closed" value={shutdown.wsConnectionsClosed} intent="info" />
          <Stat label="DB Closed" value={shutdown.dbConnectionsClosed} intent="info" />
          <Stat label="Hooks" value={shutdown.hooksRegistered ? "Registered" : "Missing"} intent={shutdown.hooksRegistered ? "healthy" : "critical"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Shutdown Policy</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">signal</span><span>SIGTERM → SIGKILL</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">drain timeout</span><span>{(shutdown.drainTimeoutMs / 1000).toFixed(0)}s</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">grace period</span><span>10s</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">hooks</span><span>{shutdown.hooksRegistered ? "✓ all registered" : "✗ missing"}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">force kill</span><span>after 30s</span></div>
          </div>
        </div>

        <div className="pt-3 mt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Drain Statistics</div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[10px] font-mono">
              <span className="text-muted-foreground">Event bus</span>
              <span style={{ color: "#34d399" }}>{shutdown.eventsDrained} drained</span>
            </div>
            <div className="flex items-center justify-between text-[10px] font-mono">
              <span className="text-muted-foreground">WebSocket</span>
              <span style={{ color: "#34d399" }}>{shutdown.wsConnectionsClosed} closed</span>
            </div>
            <div className="flex items-center justify-between text-[10px] font-mono">
              <span className="text-muted-foreground">Database</span>
              <span style={{ color: "#34d399" }}>{shutdown.dbConnectionsClosed} closed</span>
            </div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
