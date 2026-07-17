"use client";

import { cn } from "@/lib/utils";
import type { CheckStatus } from "@/modules/engineering-console/lib/certification-types";

const STATUS_STYLES: Record<CheckStatus, { color: string; bg: string; border: string; label: string }> = {
  pass: { color: "#34d399", bg: "rgba(52, 211, 153, 0.1)", border: "rgba(52, 211, 153, 0.3)", label: "PASS" },
  warn: { color: "#fbbf24", bg: "rgba(251, 191, 36, 0.1)", border: "rgba(251, 191, 36, 0.3)", label: "WARN" },
  fail: { color: "#f87171", bg: "rgba(248, 113, 113, 0.1)", border: "rgba(248, 113, 113, 0.3)", label: "FAIL" },
  pending: { color: "#6b7280", bg: "rgba(107, 114, 128, 0.1)", border: "rgba(107, 114, 128, 0.3)", label: "PENDING" },
  running: { color: "#22d3ee", bg: "rgba(34, 211, 238, 0.1)", border: "rgba(34, 211, 238, 0.3)", label: "RUNNING" },
};

export function StatusBadge({ status, className }: { status: CheckStatus; className?: string }) {
  const s = STATUS_STYLES[status];
  return (
    <span
      className={cn("inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9.5px] font-mono font-semibold tracking-wider", className)}
      style={{ color: s.color, backgroundColor: s.bg, border: `1px solid ${s.border}` }}
    >
      {status === "running" && <span className="w-1.5 h-1.5 rounded-full pulse-live" style={{ backgroundColor: s.color }} />}
      {s.label}
    </span>
  );
}

export function ScoreRing({ score, size = 64, label }: { score: number; size?: number; label?: string }) {
  const radius = (size - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.max(0, Math.min(1, score)));
  const color = score >= 0.95 ? "#34d399" : score >= 0.85 ? "#fbbf24" : "#f87171";
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={3} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[12px] font-mono font-bold tabular-nums" style={{ color }}>
          {(score * 100).toFixed(1)}%
        </span>
        {label && <span className="text-[8px] uppercase tracking-wider text-muted-foreground mt-0.5">{label}</span>}
      </div>
    </div>
  );
}

interface CheckRowProps {
  check: {
    id: string;
    label: string;
    description?: string;
    status: CheckStatus;
    score: number;
    value?: number | string;
    target?: number | string;
    unit?: string;
    evidence?: string;
  };
}

export function CheckRow({ check }: CheckRowProps) {
  const s = STATUS_STYLES[check.status];
  return (
    <div className="grid grid-cols-12 gap-2 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
      <div className="col-span-4 flex items-center gap-2 min-w-0">
        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
        <div className="min-w-0">
          <div className="font-medium truncate">{check.label}</div>
          {check.description && <div className="text-[9.5px] text-muted-foreground/70 truncate">{check.description}</div>}
        </div>
      </div>
      <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: check.value !== undefined ? "var(--foreground)" : "var(--muted-foreground)" }}>
        {check.value ?? "—"}
        {check.unit && <span className="ml-1 text-[9.5px] text-muted-foreground">{check.unit}</span>}
      </div>
      <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">
        {check.target ?? "—"}
      </div>
      <div className="col-span-3 text-[10px] text-muted-foreground/80 truncate" title={check.evidence}>
        {check.evidence ?? "—"}
      </div>
      <div className="col-span-1 flex justify-end">
        <StatusBadge status={check.status} />
      </div>
    </div>
  );
}
