"use client";

import { ArrowLeft, FileText, Search, Download } from "lucide-react";
import { useMemo, useState } from "react";
import { Panel } from "../../panel";
import { fmtTime } from "@/modules/engineering-console/lib/format";
import type { LogLevel, StructuredLog } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  logs: StructuredLog[];
  onBack: () => void;
}

const LEVEL_COLORS: Record<LogLevel, string> = {
  DEBUG: "#6b7280",
  INFO: "#22d3ee",
  WARN: "#fbbf24",
  ERROR: "#f87171",
  FATAL: "#ef4444",
};

const LEVEL_BG: Record<LogLevel, string> = {
  DEBUG: "rgba(107, 114, 128, 0.1)",
  INFO: "rgba(34, 211, 238, 0.1)",
  WARN: "rgba(251, 191, 36, 0.1)",
  ERROR: "rgba(248, 113, 113, 0.15)",
  FATAL: "rgba(239, 68, 68, 0.2)",
};

export function OpsLogsPanel({ logs, onBack }: Props) {
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState<LogLevel | "all">("all");
  const [moduleFilter, setModuleFilter] = useState<string>("all");
  const [selected, setSelected] = useState<StructuredLog | null>(null);

  const modules = useMemo(() => Array.from(new Set(logs.map((l) => l.module))).sort(), [logs]);

  const filtered = useMemo(() => {
    return logs.filter((l) => {
      if (levelFilter !== "all" && l.level !== levelFilter) return false;
      if (moduleFilter !== "all" && l.module !== moduleFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        const haystack = `${l.message} ${l.module} ${l.correlationId ?? ""} ${l.traceId ?? ""} ${JSON.stringify(l.fields)}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [logs, levelFilter, moduleFilter, search]);

  const levelCounts = useMemo(() => {
    const c: Record<LogLevel, number> = { DEBUG: 0, INFO: 0, WARN: 0, ERROR: 0, FATAL: 0 };
    for (const l of logs) c[l.level]++;
    return c;
  }, [logs]);

  const exportLogs = () => {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `athena-x-logs-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Panel
      title="Structured Logs & Aggregation"
      subtitle={`${logs.length} logs · ${filtered.length} matching · searchable audit trail`}
      icon={<FileText className="h-3.5 w-3.5" />}
      className="col-span-12"
      actions={
        <div className="flex items-center gap-2">
          <button
            onClick={exportLogs}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <Download className="h-3 w-3" /> export
          </button>
          <button
            onClick={onBack}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" /> back
          </button>
        </div>
      }
    >
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="search message, correlationId, traceId, fields…"
            className="w-full pl-7 pr-2 py-1 rounded-md bg-background/60 border border-border/50 text-[11px] font-mono focus:outline-none focus:border-primary/50"
          />
        </div>
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value as LogLevel | "all")}
          className="px-2 py-1 rounded-md bg-background/60 border border-border/50 text-[11px] font-mono focus:outline-none focus:border-primary/50"
        >
          <option value="all">all levels</option>
          <option value="DEBUG">DEBUG</option>
          <option value="INFO">INFO</option>
          <option value="WARN">WARN</option>
          <option value="ERROR">ERROR</option>
          <option value="FATAL">FATAL</option>
        </select>
        <select
          value={moduleFilter}
          onChange={(e) => setModuleFilter(e.target.value)}
          className="px-2 py-1 rounded-md bg-background/60 border border-border/50 text-[11px] font-mono focus:outline-none focus:border-primary/50"
        >
          <option value="all">all modules</option>
          {modules.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      {/* Level counts */}
      <div className="grid grid-cols-5 gap-2 mb-3">
        {(Object.keys(levelCounts) as LogLevel[]).map((lvl) => {
          const count = levelCounts[lvl];
          const isActive = levelFilter === lvl;
          return (
            <button
              key={lvl}
              onClick={() => setLevelFilter(isActive ? "all" : lvl)}
              className={`rounded-md border p-2 text-left transition-colors ${isActive ? "border-primary/60 bg-primary/5" : "border-border/40 bg-background/30 hover:border-border/60"}`}
              style={{ borderLeft: `3px solid ${LEVEL_COLORS[lvl]}` }}
            >
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">{lvl}</div>
              <div className="text-[15px] font-mono tabular-nums font-semibold" style={{ color: LEVEL_COLORS[lvl] }}>{count}</div>
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* Log table */}
        <div className="col-span-12 lg:col-span-8 rounded-md border border-border/40 overflow-hidden">
          <div className="max-h-[520px] overflow-y-auto scroll-thin">
            <div className="grid grid-cols-12 px-2 py-1.5 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40 sticky top-0">
              <div className="col-span-2">Time</div>
              <div className="col-span-1">Level</div>
              <div className="col-span-2">Module</div>
              <div className="col-span-5">Message</div>
              <div className="col-span-2">Correlation</div>
            </div>
            {filtered.length === 0 && (
              <div className="px-2 py-8 text-center text-[11px] text-muted-foreground/70 font-mono">no logs match filters</div>
            )}
            {filtered.slice(0, 200).map((l) => (
              <button
                key={l.id}
                onClick={() => setSelected(l)}
                className={`w-full text-left grid grid-cols-12 px-2 py-1 text-[10.5px] items-center border-b border-border/20 hover:bg-accent/30 ${selected?.id === l.id ? "bg-primary/8" : ""}`}
                style={{ backgroundColor: l.level === "ERROR" || l.level === "FATAL" ? LEVEL_BG[l.level] : undefined }}
              >
                <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground">{fmtTime(l.timestamp)}</div>
                <div className="col-span-1">
                  <span className="text-[9px] font-mono font-semibold px-1 py-0.5 rounded" style={{ color: LEVEL_COLORS[l.level], backgroundColor: LEVEL_BG[l.level] }}>
                    {l.level}
                  </span>
                </div>
                <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground truncate">{l.module}</div>
                <div className="col-span-5 truncate">{l.message}</div>
                <div className="col-span-2 font-mono text-[9px] text-muted-foreground/70 truncate">{l.correlationId ?? "—"}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Selected log detail */}
        <div className="col-span-12 lg:col-span-4 rounded-md border border-border/40 overflow-hidden">
          <div className="px-3 py-2 border-b border-border/40 bg-background/40 text-[9.5px] uppercase tracking-wider text-muted-foreground/70">
            Log Detail
          </div>
          <div className="p-3 max-h-[520px] overflow-y-auto scroll-thin">
            {!selected && (
              <div className="text-center text-[11px] text-muted-foreground/70 font-mono py-8">select a log to inspect</div>
            )}
            {selected && (
              <div className="space-y-2">
                <div>
                  <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">Message</div>
                  <div className="text-[12px] font-medium mt-0.5">{selected.message}</div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                  <div>
                    <div className="text-muted-foreground/60">level</div>
                    <div style={{ color: LEVEL_COLORS[selected.level] }}>{selected.level}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/60">module</div>
                    <div>{selected.module}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/60">timestamp</div>
                    <div>{new Date(selected.timestamp).toISOString()}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/60">log id</div>
                    <div className="truncate">{selected.id}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/60">correlation</div>
                    <div className="truncate">{selected.correlationId ?? "—"}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/60">trace</div>
                    <div className="truncate">{selected.traceId ?? "—"}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/60">span</div>
                    <div className="truncate">{selected.spanId ?? "—"}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground/60">user</div>
                    <div>{selected.userId ?? "—"}</div>
                  </div>
                </div>
                {Object.keys(selected.fields).length > 0 && (
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70 mb-1">Structured Fields</div>
                    <pre className="text-[10px] font-mono bg-background/40 border border-border/40 rounded p-2 overflow-x-auto">
{JSON.stringify(selected.fields, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </Panel>
  );
}
