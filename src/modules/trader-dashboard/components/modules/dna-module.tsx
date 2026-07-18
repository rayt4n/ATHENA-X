"use client";

import { useEffect, useState } from "react";
import type { DNAState } from "@/modules/trader-dashboard/lib/workspace-types";

interface DNAObj {
  id: string;
  name: string;
  confidence: number;
  trend: number;
  state: "healthy" | "degraded" | "critical";
}

const DNA_OBJECTS: DNAObj[] = [
  { id: "technical", name: "Technical DNA", confidence: 0.78, trend: 0.02, state: "healthy" },
  { id: "options", name: "Options DNA", confidence: 0.72, trend: -0.01, state: "healthy" },
  { id: "market", name: "Market DNA", confidence: 0.84, trend: 0.03, state: "healthy" },
  { id: "narrative", name: "Narrative DNA", confidence: 0.65, trend: -0.02, state: "degraded" },
  { id: "forecast", name: "Forecast DNA", confidence: 0.70, trend: 0.01, state: "healthy" },
  { id: "trade", name: "Trade DNA", confidence: 0.74, trend: 0.02, state: "healthy" },
  { id: "operations", name: "Operations DNA", confidence: 0.88, trend: 0, state: "healthy" },
];

interface Props {
  state: DNAState;
  onStateChange: (partial: Partial<DNAState>) => void;
}

export function DNAModule({ state, onStateChange }: Props) {
  const selected = state.selected ?? null;
  const showHistory = state.showHistory ?? false;
  const [dna, setDna] = useState(DNA_OBJECTS);

  useEffect(() => {
    const interval = setInterval(() => {
      setDna((prev) => prev.map((d) => ({
        ...d,
        confidence: Math.max(0.4, Math.min(0.98, d.confidence + (Math.random() - 0.5) * 0.02)),
        trend: d.trend + (Math.random() - 0.5) * 0.01,
      })));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center justify-between">
        <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/70">7 DNA Objects</span>
        <label className="flex items-center gap-1 text-[9px] font-mono cursor-pointer">
          <input
            type="checkbox"
            checked={showHistory}
            onChange={(e) => onStateChange({ showHistory: e.target.checked })}
            className="accent-primary"
          />
          <span className="text-muted-foreground">history</span>
        </label>
      </div>
      <div className="flex-1 overflow-y-auto scroll-thin p-2 space-y-1.5">
        {dna.map((d) => {
          const color = d.confidence > 0.75 ? "#34d399" : d.confidence > 0.55 ? "#fbbf24" : "#f87171";
          const isSelected = selected === d.id;
          return (
            <button
              key={d.id}
              onClick={() => onStateChange({ selected: isSelected ? null : d.id })}
              className={`w-full text-left rounded-md border p-2 transition-colors ${isSelected ? "border-primary/60 bg-primary/5" : "border-border/40 bg-background/30 hover:bg-accent/30"}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] font-medium">{d.name}</span>
                <span className="text-[14px] font-mono font-bold tabular-nums" style={{ color }}>
                  {(d.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-background/60 overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${d.confidence * 100}%`, backgroundColor: color }} />
              </div>
              <div className="flex items-center justify-between mt-1 text-[9px] font-mono text-muted-foreground/70">
                <span className="uppercase tracking-wider">{d.state}</span>
                <span style={{ color: d.trend >= 0 ? "#34d399" : "#f87171" }}>
                  {d.trend >= 0 ? "▲" : "▼"} {Math.abs(d.trend).toFixed(3)}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
