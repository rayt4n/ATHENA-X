"use client";

import { Bell, CheckCircle2, AlertTriangle, AlertOctagon } from "lucide-react";
import { Panel } from "../panel";
import { StatusDot } from "../status-dot";
import { fmtAge } from "@/lib/dashboard/format";
import type { Alarm } from "@/lib/dashboard/types";

const SEVERITY_ICON: Record<Alarm["severity"], React.ReactNode> = {
  critical: <AlertOctagon className="h-3.5 w-3.5" style={{ color: "#f87171" }} />,
  warning: <AlertTriangle className="h-3.5 w-3.5" style={{ color: "#fbbf24" }} />,
  info: <Bell className="h-3.5 w-3.5" style={{ color: "#22d3ee" }} />,
};

export function AlarmsPanel({ alarms }: { alarms: Alarm[] }) {
  const critical = alarms.filter((a) => a.severity === "critical");
  const warning = alarms.filter((a) => a.severity === "warning");
  const info = alarms.filter((a) => a.severity === "info");

  return (
    <Panel
      title="Active Alarms"
      subtitle={`${alarms.length} alarms — ${critical.length} critical · ${warning.length} warning · ${info.length} info`}
      icon={<Bell className="h-3.5 w-3.5" />}
      actions={
        alarms.length === 0 ? (
          <span className="flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded bg-status-healthy/10 border border-status-healthy/30" style={{ color: "#34d399" }}>
            <CheckCircle2 className="h-3 w-3" />all clear
          </span>
        ) : null
      }
      bodyClassName="p-0"
    >
      <div className="max-h-[560px] overflow-y-auto scroll-thin divide-y divide-border/30">
        {alarms.length === 0 && (
          <div className="px-4 py-12 text-center">
            <CheckCircle2 className="h-8 w-8 mx-auto mb-2" style={{ color: "#34d399" }} />
            <div className="text-[12px] font-mono text-muted-foreground">no active alarms</div>
          </div>
        )}
        {alarms
          .slice()
          .sort((a, b) => (a.severity === "critical" ? -1 : b.severity === "critical" ? 1 : a.raisedAt - b.raisedAt))
          .map((a) => (
            <div key={a.id} className="px-4 py-2.5 flex items-start gap-3 hover:bg-accent/30">
              <div className="mt-0.5 shrink-0">{SEVERITY_ICON[a.severity]}</div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2 mb-0.5">
                  <span className="text-[10.5px] font-mono uppercase tracking-wider" style={{ color: a.severity === "critical" ? "#f87171" : a.severity === "warning" ? "#fbbf24" : "#22d3ee" }}>
                    {a.source}
                  </span>
                  <span className="text-[9.5px] font-mono text-muted-foreground/70">{fmtAge(Date.now() - a.raisedAt)}</span>
                </div>
                <div className="text-[11.5px] leading-snug">{a.message}</div>
              </div>
              <StatusDot state={a.severity === "critical" ? "down" : a.severity === "warning" ? "degraded" : "healthy"} pulse={a.severity === "critical"} />
            </div>
          ))}
      </div>
    </Panel>
  );
}
