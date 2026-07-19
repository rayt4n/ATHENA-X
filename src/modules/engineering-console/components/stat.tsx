"use client";

import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface StatProps {
  label: string;
  value: ReactNode;
  unit?: string;
  trend?: number;
  intent?: "default" | "healthy" | "warning" | "critical" | "info";
  className?: string;
}

export function Stat({ label, value, unit, trend, intent = "default", className }: StatProps) {
  const color =
    intent === "healthy" ? "#34d399" :
    intent === "warning" ? "#fbbf24" :
    intent === "critical" ? "#f87171" :
    intent === "info" ? "#22d3ee" :
    "var(--foreground)";

  return (
    <div className={cn("rounded-md border border-border/50 bg-background/40 px-3 py-2", className)}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground/80 truncate">{label}</span>
        {trend !== undefined && (
          <span
            className="text-[10px] font-mono tabular-nums"
            style={{ color: trend >= 0 ? "#34d399" : "#f87171" }}
          >
            {trend >= 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(2)}
          </span>
        )}
      </div>
      <div className="mt-1 font-mono tabular-nums text-base leading-tight" style={{ color }}>
        <span className="font-semibold">{value}</span>
        {unit && <span className="ml-1 text-[11px] text-muted-foreground">{unit}</span>}
      </div>
    </div>
  );
}

export function StatRow({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid gap-2", className)}>{children}</div>;
}
