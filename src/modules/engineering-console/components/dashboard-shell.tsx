"use client";

import { useEffect, useState } from "react";
import { Activity, Radio, Cpu, Database, Layers, Gauge, ShieldCheck, Beaker, Bell, RotateCcw, Award, FileText, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import { StatusDot } from "./status-dot";
import { fmtClock, fmtAge } from "@/modules/engineering-console/lib/format";
import type { SystemSummary } from "@/modules/engineering-console/lib/types";

interface ShellProps {
  system: SystemSummary;
  onReset: () => void;
  activeSection: string;
  onSectionChange: (id: string) => void;
  children: React.ReactNode;
}

const NAV_GROUPS: { id: string; label: string; items: { id: string; label: string; icon: React.ReactNode }[] }[] = [
  {
    id: "overview",
    label: "Overview",
    items: [
      { id: "overview", label: "Cockpit", icon: <Gauge className="h-3.5 w-3.5" /> },
      { id: "alarms", label: "Alarms", icon: <Bell className="h-3.5 w-3.5" /> },
    ],
  },
  {
    id: "data",
    label: "Data Layer",
    items: [
      { id: "freshness", label: "Freshness", icon: <Radio className="h-3.5 w-3.5" /> },
      { id: "providers", label: "Providers", icon: <Activity className="h-3.5 w-3.5" /> },
    ],
  },
  {
    id: "intelligence",
    label: "Intelligence",
    items: [
      { id: "ta", label: "TA Accuracy", icon: <Layers className="h-3.5 w-3.5" /> },
      { id: "options", label: "Options Accuracy", icon: <Layers className="h-3.5 w-3.5" /> },
      { id: "forecast", label: "Forecast", icon: <Gauge className="h-3.5 w-3.5" /> },
      { id: "trade", label: "Trade DNA", icon: <ShieldCheck className="h-3.5 w-3.5" /> },
    ],
  },
  {
    id: "platform",
    label: "Platform",
    items: [
      { id: "agents", label: "Agents", icon: <Cpu className="h-3.5 w-3.5" /> },
      { id: "eventbus", label: "Event Bus", icon: <Activity className="h-3.5 w-3.5" /> },
      { id: "database", label: "Database", icon: <Database className="h-3.5 w-3.5" /> },
      { id: "dna", label: "DNA Matrix", icon: <Beaker className="h-3.5 w-3.5" /> },
    ],
  },
  {
    id: "certification",
    label: "Stage 14.5",
    items: [
      { id: "certification", label: "Certification", icon: <Award className="h-3.5 w-3.5" /> },
    ],
  },
  {
    id: "stage15",
    label: "Stage 15",
    items: [
      { id: "report-engine", label: "Report Engine", icon: <FileText className="h-3.5 w-3.5" /> },
    ],
  },
  {
    id: "stage155",
    label: "Stage 15.5",
    items: [
      { id: "ops", label: "Platform Hardening", icon: <Wrench className="h-3.5 w-3.5" /> },
    ],
  },
];

export function DashboardShell({ system, onReset, activeSection, onSectionChange, children }: ShellProps) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(t);
  }, []);

  const uptimeSec = (now - system.startedAt) / 1000;
  const uptimeStr =
    uptimeSec < 60 ? `${uptimeSec.toFixed(0)}s` :
    uptimeSec < 3600 ? `${(uptimeSec / 60).toFixed(1)}m` :
    uptimeSec < 86400 ? `${(uptimeSec / 3600).toFixed(1)}h` :
    `${(uptimeSec / 86400).toFixed(1)}d`;

  return (
    <div className="flex h-[calc(100vh-29px)] w-full overflow-hidden bg-background text-foreground cockpit-grid">
      {/* Nav rail */}
      <aside className="hidden md:flex w-[220px] shrink-0 flex-col border-r border-border/60 bg-sidebar/40 backdrop-blur-md">
        <div className="flex items-center gap-2 px-4 py-4 border-b border-border/60">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-md bg-primary/15 border border-primary/30">
            <Beaker className="h-4 w-4 text-primary" />
            <span className="absolute -bottom-1 -right-1 w-2 h-2 rounded-full bg-status-healthy pulse-live" style={{ backgroundColor: "#34d399" }} />
          </div>
          <div className="min-w-0">
            <div className="text-[12px] font-semibold tracking-wide">ATHENA-X</div>
            <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/70 truncate">Validation Cockpit</div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto scroll-thin px-2 py-3 space-y-4">
          {NAV_GROUPS.map((g) => (
            <div key={g.id}>
              <div className="px-2 mb-1 text-[9.5px] uppercase tracking-[0.12em] text-muted-foreground/60">{g.label}</div>
              <div className="space-y-0.5">
                {g.items.map((it) => (
                  <button
                    key={it.id}
                    onClick={() => onSectionChange(it.id)}
                    className={cn(
                      "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-[12px] transition-colors",
                      activeSection === it.id
                        ? "bg-primary/12 text-primary border border-primary/25"
                        : "text-muted-foreground hover:text-foreground hover:bg-accent/50 border border-transparent"
                    )}
                  >
                    <span className="shrink-0">{it.icon}</span>
                    <span className="truncate">{it.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-border/60 px-3 py-3 space-y-1.5 text-[10.5px] font-mono text-muted-foreground/80">
          <div className="flex justify-between"><span>build</span><span className="text-foreground/70">{system.buildHash}</span></div>
          <div className="flex justify-between"><span>env</span><span className="text-foreground/70">{system.environment}</span></div>
          <div className="flex justify-between"><span>uptime</span><span className="text-foreground/70">{uptimeStr}</span></div>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header bar */}
        <header className="flex items-center justify-between gap-4 px-4 md:px-6 py-2.5 border-b border-border/60 bg-card/40 backdrop-blur-md">
          <div className="flex items-center gap-4 min-w-0">
            <div className="flex items-center gap-2">
              <StatusDot state={system.overallHealth} size="md" />
              <span className="text-[12px] font-semibold tracking-wide uppercase">
                {system.stage}
              </span>
            </div>
            <div className="hidden lg:flex items-center gap-3 text-[10.5px] text-muted-foreground font-mono">
              <span>agents <span className="text-foreground">{system.healthyAgents}/{system.totalAgents}</span></span>
              <span>providers <span className="text-foreground">{system.healthyProviders}/{system.totalProviders}</span></span>
              <span>plugins <span className="text-foreground">{system.activePlugins}/{system.totalPlugins}</span></span>
              <span>bus p95 <span className="text-foreground">{system.eventBusP95.toFixed(1)}ms</span></span>
              <span>db p95 <span className="text-foreground">{system.dbWriteP95.toFixed(1)}ms</span></span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {system.activeAlarms > 0 && (
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-status-critical/10 border border-status-critical/30">
                <Bell className="h-3 w-3" style={{ color: "#f87171" }} />
                <span className="text-[10.5px] font-mono font-semibold" style={{ color: "#f87171" }}>
                  {system.activeAlarms} active
                </span>
              </div>
            )}
            <button
              onClick={onReset}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
              title="Reset simulated telemetry"
            >
              <RotateCcw className="h-3 w-3" />
              <span>reset sim</span>
            </button>
            <div className="hidden md:flex flex-col items-end font-mono text-[10.5px] leading-tight">
              <span className="text-foreground tabular-nums">{fmtClock(now)}</span>
              <span className="text-muted-foreground/60">UTC+08 · SG</span>
            </div>
          </div>
        </header>

        {/* Mobile nav (horizontal scroller) */}
        <div className="md:hidden border-b border-border/60 px-3 py-2 overflow-x-auto scroll-thin">
          <div className="flex gap-1.5 min-w-max">
            {NAV_GROUPS.flatMap((g) => g.items).map((it) => (
              <button
                key={it.id}
                onClick={() => onSectionChange(it.id)}
                className={cn(
                  "flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] whitespace-nowrap",
                  activeSection === it.id
                    ? "bg-primary/12 text-primary border border-primary/25"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50 border border-transparent"
                )}
              >
                {it.icon}
                <span>{it.label}</span>
              </button>
            ))}
          </div>
        </div>

        <main className="flex-1 overflow-y-auto scroll-thin px-4 md:px-6 py-4">
          {children}
        </main>
      </div>
    </div>
  );
}
