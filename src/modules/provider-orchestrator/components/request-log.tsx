"use client";

import { useEffect, useState } from "react";
import { FileText, Trash2, Clock } from "lucide-react";
import type { RequestLogEntry } from "../lib/types";

const STATUS_COLORS: Record<string, string> = {
  success: "#34d399",
  failed: "#f87171",
  cache: "#22d3ee",
  timeout: "#fbbf24",
};

export function RequestLog() {
  const [logs, setLogs] = useState<RequestLogEntry[]>([]);
  const [filter, setFilter] = useState<string>("all");

  const refresh = async () => {
    try {
      const res = await fetch("/api/providers/health");
      const data = await res.json();
      // Request log is stored in-memory on the server side — we'll get it from health endpoint
      // For now, show what's available
      setLogs(data.requestLog ?? []);
    } catch {
      // Server-side log not exposed yet — use empty state
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, []);

  const filtered = filter === "all" ? logs : logs.filter((l) => l.status === filter);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border bg-card/40 overflow-hidden">
        <div className="px-4 py-2 border-b border-border/60 bg-card/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-3.5 w-3.5 text-primary" />
            <h2 className="text-[13px] font-semibold uppercase tracking-wide">Request Log</h2>
          </div>
          <div className="flex items-center gap-2">
            {["all", "success", "failed", "cache"].map((f) => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${filter === f ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}>
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="max-h-[500px] overflow-y-auto scroll-thin">
          {filtered.length === 0 ? (
            <div className="px-4 py-8 text-center text-[11px] text-muted-foreground/70 font-mono">
              No requests logged yet. Use Diagnostics to trigger a request.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-12 px-4 py-1.5 text-[8.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40 sticky top-0">
                <div className="col-span-2">Time</div>
                <div className="col-span-2">Provider</div>
                <div className="col-span-2">Symbol</div>
                <div className="col-span-2">Category</div>
                <div className="col-span-2 text-right">Latency</div>
                <div className="col-span-1 text-right">Status</div>
                <div className="col-span-1 text-right">Cache</div>
              </div>
              {filtered.map((log) => (
                <div key={log.id} className="grid grid-cols-12 px-4 py-1 text-[10.5px] items-center border-b border-border/10 hover:bg-accent/20">
                  <div className="col-span-2 font-mono text-[9px] text-muted-foreground">
                    {new Date(log.timestamp).toLocaleTimeString("en-US", { hour12: false })}
                  </div>
                  <div className="col-span-2 font-mono">{log.provider}</div>
                  <div className="col-span-2 font-mono font-medium">{log.symbol}</div>
                  <div className="col-span-2 font-mono text-muted-foreground">{log.category}</div>
                  <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{log.latencyMs}ms</div>
                  <div className="col-span-1 text-right">
                    <span className="text-[8.5px] font-mono font-semibold px-1 py-0.5 rounded" style={{ color: STATUS_COLORS[log.status], backgroundColor: `${STATUS_COLORS[log.status]}22` }}>
                      {log.status}
                    </span>
                  </div>
                  <div className="col-span-1 text-right text-[9px] text-muted-foreground">{log.fromCache ? "✓" : "—"}</div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
