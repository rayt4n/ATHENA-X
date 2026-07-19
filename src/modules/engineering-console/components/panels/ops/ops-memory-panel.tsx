"use client";

import { ArrowLeft, Cpu, AlertTriangle, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtNum } from "@/modules/engineering-console/lib/format";
import type { MemoryLeakMonitoring, MemorySnapshot } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  memory: MemoryLeakMonitoring;
  onBack: () => void;
}

const TREND_ICONS = {
  stable: <Minus className="h-3 w-3" />,
  growing: <TrendingUp className="h-3 w-3" />,
  shrinking: <TrendingDown className="h-3 w-3" />,
};

const TREND_COLORS = {
  stable: "#94a3b8",
  growing: "#fbbf24",
  shrinking: "#34d399",
};

export function OpsMemoryPanel({ memory, onBack }: Props) {
  const suspects = memory.snapshots.filter((s) => s.leakSuspected);
  const heapPct = memory.heapUtilization * 100;

  return (
    <PanelGrid>
      <Panel
        title="Memory Leak Monitoring"
        subtitle={`${memory.snapshots.length} agents · ${fmtNum(memory.totalHeapMb, 0)}MB / ${fmtNum(memory.heapLimitMb, 0)}MB used (${heapPct.toFixed(1)}%)`}
        icon={<Cpu className="h-3.5 w-3.5" />}
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
        {/* Heap utilization bar */}
        <div className="mb-4 rounded-md border border-border/40 bg-background/30 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80">Total Heap Utilization</span>
            <span className="text-[11px] font-mono font-semibold" style={{ color: heapPct < 80 ? "#34d399" : heapPct < 90 ? "#fbbf24" : "#f87171" }}>
              {fmtNum(memory.totalHeapMb, 0)} / {fmtNum(memory.heapLimitMb, 0)} MB ({heapPct.toFixed(1)}%)
            </span>
          </div>
          <div className="h-3 rounded-full bg-background/60 overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${heapPct}%`,
                backgroundColor: heapPct < 80 ? "#34d399" : heapPct < 90 ? "#fbbf24" : "#f87171",
              }}
            />
          </div>
        </div>

        {/* Agent memory table */}
        <div className="rounded-md border border-border/40 overflow-hidden">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
            <div className="col-span-4">Agent</div>
            <div className="col-span-2 text-right">Heap Used</div>
            <div className="col-span-2 text-right">Growth Rate</div>
            <div className="col-span-1 text-right">GC/min</div>
            <div className="col-span-2 text-right">Last GC</div>
            <div className="col-span-1 text-right">Trend</div>
          </div>
          {memory.snapshots.map((s: MemorySnapshot) => {
            const trendColor = TREND_COLORS[s.trend];
            return (
              <div
                key={s.agentId}
                className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20"
                style={{ backgroundColor: s.leakSuspected ? "rgba(248, 113, 113, 0.05)" : undefined }}
              >
                <div className="col-span-4 font-mono truncate flex items-center gap-2">
                  {s.leakSuspected && <AlertTriangle className="h-3 w-3 shrink-0" style={{ color: "#f87171" }} />}
                  {s.agentId}
                </div>
                <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: s.heapUsedMb > 1000 ? "#fbbf24" : "#e6edf3" }}>
                  {fmtNum(s.heapUsedMb, 0)} MB
                </div>
                <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: s.growthRateMbPerHour > 1 ? "#fbbf24" : s.growthRateMbPerHour < -1 ? "#34d399" : "#94a3b8" }}>
                  {s.growthRateMbPerHour > 0 ? "+" : ""}{s.growthRateMbPerHour.toFixed(2)} MB/h
                </div>
                <div className="col-span-1 text-right font-mono tabular-nums text-muted-foreground">{s.gcPressure.toFixed(1)}</div>
                <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{(s.lastGcMs / 1000).toFixed(1)}s ago</div>
                <div className="col-span-1 flex justify-end items-center" style={{ color: trendColor }}>
                  {TREND_ICONS[s.trend]}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="Memory Health"
        icon={<Cpu className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Heap Used" value={`${fmtNum(memory.totalHeapMb, 0)}MB`} intent={heapPct < 80 ? "healthy" : "warning"} />
          <Stat label="Heap Limit" value={`${fmtNum(memory.heapLimitMb, 0)}MB`} />
          <Stat label="Leak Suspects" value={memory.leakSuspectCount} intent={memory.leakSuspectCount === 0 ? "healthy" : "critical"} />
          <Stat label="Avg GC/min" value={memory.avgGcPressure.toFixed(1)} intent={memory.avgGcPressure < 10 ? "healthy" : "warning"} />
          <Stat label="Agents" value={memory.snapshots.length} intent="info" />
          <Stat label="Auto-Restart" value={memory.autoRestartEnabled ? "On" : "Off"} intent={memory.autoRestartEnabled ? "healthy" : "warning"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Leak Detection</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">threshold</span><span>&gt; 4 MB/h growth</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">window</span><span>1 hour rolling</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">sample rate</span><span>every 30s</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">auto-restart</span><span style={{ color: memory.autoRestartEnabled ? "#34d399" : "#f87171" }}>{memory.autoRestartEnabled ? "enabled" : "disabled"}</span></div>
          </div>
        </div>

        {suspects.length > 0 ? (
          <div className="mt-3 pt-3 border-t border-border/40 rounded-md p-2" style={{ backgroundColor: "rgba(248, 113, 113, 0.08)", border: "1px solid rgba(248, 113, 113, 0.3)" }}>
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-3 w-3" style={{ color: "#f87171" }} />
              <span className="text-[10px] font-semibold" style={{ color: "#f87171" }}>{suspects.length} leak suspect{suspects.length === 1 ? "" : "s"}</span>
            </div>
            <div className="text-[9.5px] font-mono text-muted-foreground/80">
              {suspects.map((s) => s.agentId).join(", ")}
            </div>
          </div>
        ) : (
          <div className="mt-3 pt-3 border-t border-border/40 rounded-md p-2" style={{ backgroundColor: "rgba(52, 211, 153, 0.08)", border: "1px solid rgba(52, 211, 153, 0.3)" }}>
            <div className="text-[10px] font-semibold" style={{ color: "#34d399" }}>✓ No memory leaks detected</div>
            <div className="text-[9.5px] font-mono text-muted-foreground/80 mt-0.5">
              All {memory.snapshots.length} agents within healthy growth bounds
            </div>
          </div>
        )}
      </Panel>
    </PanelGrid>
  );
}
