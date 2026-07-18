"use client";

import { ArrowUpRight, ArrowDownRight, Target } from "lucide-react";
import type { TradeSetupsState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Setup {
  id: string;
  symbol: string;
  direction: "long" | "short" | "neutral";
  setup: string;
  entry: number;
  stop: number;
  target: number;
  confidence: number;
  rr: number;
  status: "evaluating" | "qualified" | "triggered" | "managed" | "closed";
}

const SAMPLE_SETUPS: Setup[] = [
  { id: "ts1", symbol: "SPY", direction: "long", setup: "0DTE Put Credit Spread", entry: 585, stop: 578, target: 590, confidence: 0.72, rr: 0.6, status: "qualified" },
  { id: "ts2", symbol: "QQQ", direction: "long", setup: "VWAP Reversal Long", entry: 491.50, stop: 489.80, target: 494.20, confidence: 0.68, rr: 1.55, status: "qualified" },
  { id: "ts3", symbol: "ES", direction: "short", setup: "Opening Range Breakout Fail", entry: 5862, stop: 5870, target: 5848, confidence: 0.65, rr: 1.75, status: "evaluating" },
  { id: "ts4", symbol: "SPY", direction: "neutral", setup: "Iron Condor", entry: 585, stop: 580, target: 590, confidence: 0.78, rr: 0.8, status: "triggered" },
  { id: "ts5", symbol: "VIX", direction: "long", setup: "Volatility Mean Reversion", entry: 18.40, stop: 17.80, target: 20.50, confidence: 0.71, rr: 3.5, status: "qualified" },
  { id: "ts6", symbol: "IWM", direction: "short", setup: "Trend Pullback Short", entry: 222.15, stop: 224.50, target: 218.00, confidence: 0.63, rr: 1.8, status: "managed" },
];

interface Props {
  state: TradeSetupsState;
  onStateChange: (partial: Partial<TradeSetupsState>) => void;
}

export function TradeSetupsModule({ state, onStateChange }: Props) {
  const filter = state.filter ?? "all";
  const minConfidence = state.minConfidence ?? 0.5;
  const filtered = SAMPLE_SETUPS.filter((s) => {
    if (filter !== "all" && s.status !== filter) return false;
    if (s.confidence < minConfidence) return false;
    return true;
  });

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center gap-2">
        <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/70">filter:</span>
        {["all", "qualified", "triggered", "closed"].map((f) => (
          <button
            key={f}
            onClick={() => onStateChange({ filter: f as TradeSetupsState["filter"] })}
            className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${filter === f ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto text-[9px] font-mono text-muted-foreground/70">
          min conf: <span className="text-foreground">{(minConfidence * 100).toFixed(0)}%</span>
        </span>
        <input
          type="range"
          min="0"
          max="100"
          value={minConfidence * 100}
          onChange={(e) => onStateChange({ minConfidence: parseInt(e.target.value) / 100 })}
          className="w-16 h-1"
        />
      </div>
      <div className="flex-1 overflow-y-auto scroll-thin">
        {filtered.map((s) => {
          const dirColor = s.direction === "long" ? "#34d399" : s.direction === "short" ? "#f87171" : "#94a3b8";
          const statusColor = s.status === "qualified" ? "#34d399" : s.status === "triggered" ? "#a78bfa" : s.status === "managed" ? "#fbbf24" : "#94a3b8";
          return (
            <div key={s.id} className="px-3 py-2 border-b border-border/20 hover:bg-accent/30">
              <div className="flex items-center justify-between gap-2 mb-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-mono font-bold">{s.symbol}</span>
                  <span className="flex items-center gap-0.5 text-[9px] font-mono px-1 py-0.5 rounded" style={{ color: dirColor, backgroundColor: `${dirColor}22` }}>
                    {s.direction === "long" ? <ArrowUpRight className="h-2.5 w-2.5" /> : s.direction === "short" ? <ArrowDownRight className="h-2.5 w-2.5" /> : null}
                    {s.direction}
                  </span>
                  <span className="text-[10px] text-muted-foreground truncate">{s.setup}</span>
                </div>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{ color: statusColor, backgroundColor: `${statusColor}22` }}>
                  {s.status}
                </span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-[9.5px] font-mono">
                <div><span className="text-muted-foreground/60">entry </span>{s.entry.toFixed(2)}</div>
                <div><span className="text-muted-foreground/60">stop </span><span style={{ color: "#f87171" }}>{s.stop.toFixed(2)}</span></div>
                <div><span className="text-muted-foreground/60">target </span><span style={{ color: "#34d399" }}>{s.target.toFixed(2)}</span></div>
                <div><span className="text-muted-foreground/60">R/R </span>{s.rr.toFixed(2)}</div>
              </div>
              <div className="mt-1.5 flex items-center gap-2">
                <Target className="h-2.5 w-2.5 text-muted-foreground/60" />
                <div className="flex-1 h-1.5 rounded-full bg-background/60 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${s.confidence * 100}%`, backgroundColor: s.confidence > 0.7 ? "#34d399" : s.confidence > 0.5 ? "#fbbf24" : "#f87171" }} />
                </div>
                <span className="text-[10px] font-mono font-semibold w-10 text-right" style={{ color: s.confidence > 0.7 ? "#34d399" : s.confidence > 0.5 ? "#fbbf24" : "#f87171" }}>
                  {(s.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
