"use client";

import type { ForecastState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Props {
  state: ForecastState;
  onStateChange: (partial: Partial<ForecastState>) => void;
  selectedSymbol: string;
}

const HORIZONS = ["5m", "15m", "30m", "1h", "eod", "tomorrow"] as const;

const FORECASTS: Record<string, { direction: string; magnitude: number; confidence: number }> = {
  "5m": { direction: "bullish", magnitude: 0.001, confidence: 0.62 },
  "15m": { direction: "bullish", magnitude: 0.002, confidence: 0.65 },
  "30m": { direction: "neutral", magnitude: 0.0005, confidence: 0.58 },
  "1h": { direction: "bullish", magnitude: 0.003, confidence: 0.71 },
  "eod": { direction: "bullish", magnitude: 0.006, confidence: 0.74 },
  "tomorrow": { direction: "neutral", magnitude: 0.001, confidence: 0.61 },
};

export function ForecastModule({ state, onStateChange, selectedSymbol }: Props) {
  const horizon = state.horizon ?? "eod";
  const showCalibration = state.showCalibration ?? true;
  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center gap-2">
        <span className="text-[11px] font-mono font-bold text-primary">{selectedSymbol}</span>
        <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/70">Forecast</span>
        <div className="ml-auto flex gap-0.5">
          {HORIZONS.map((h) => (
            <button
              key={h}
              onClick={() => onStateChange({ horizon: h })}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${horizon === h ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground hover:text-foreground"}`}
            >
              {h}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto scroll-thin p-3 space-y-3">
        {/* Current horizon forecast */}
        <div className="rounded-md border border-border/40 bg-background/30 p-3">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70 mb-1">{horizon} forecast</div>
          <div className="flex items-baseline justify-between">
            <span className="text-[20px] font-bold capitalize" style={{ color: FORECASTS[horizon].direction === "bullish" ? "#34d399" : FORECASTS[horizon].direction === "bearish" ? "#f87171" : "#94a3b8" }}>
              {FORECASTS[horizon].direction}
            </span>
            <span className="text-[14px] font-mono" style={{ color: FORECASTS[horizon].magnitude >= 0 ? "#34d399" : "#f87171" }}>
              {FORECASTS[horizon].magnitude >= 0 ? "+" : ""}{(FORECASTS[horizon].magnitude * 100).toFixed(2)}%
            </span>
          </div>
          <div className="mt-1 text-[10px] font-mono text-muted-foreground">
            confidence: <span style={{ color: FORECASTS[horizon].confidence > 0.65 ? "#34d399" : "#fbbf24" }}>{(FORECASTS[horizon].confidence * 100).toFixed(0)}%</span>
          </div>
        </div>

        {/* Bull/Base/Bear */}
        <div>
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70 mb-2">Scenarios</div>
          <div className="space-y-2">
            <div className="rounded-md border border-status-healthy/30 bg-status-healthy/5 p-2">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[10px] font-semibold" style={{ color: "#34d399" }}>Bull Case</span>
                <span className="text-[9px] font-mono text-muted-foreground">28% probability</span>
              </div>
              <div className="text-[10px] text-muted-foreground/90">CPI cooler than expected; {selectedSymbol} tests 595 resistance with breakout to 600</div>
            </div>
            <div className="rounded-md border border-border/40 bg-background/30 p-2">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[10px] font-semibold">Base Case</span>
                <span className="text-[9px] font-mono text-muted-foreground">52% probability</span>
              </div>
              <div className="text-[10px] text-muted-foreground/90">CPI in line; {selectedSymbol} range-bound 582-590 into FOMC</div>
            </div>
            <div className="rounded-md border border-status-critical/30 bg-status-critical/5 p-2">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[10px] font-semibold" style={{ color: "#f87171" }}>Bear Case</span>
                <span className="text-[9px] font-mono text-muted-foreground">20% probability</span>
              </div>
              <div className="text-[10px] text-muted-foreground/90">Hot CPI; {selectedSymbol} gaps below 578 put wall, targets 570</div>
            </div>
          </div>
        </div>

        {/* Calibration */}
        {showCalibration && (
          <div className="rounded-md border border-border/40 bg-background/30 p-2">
            <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70 mb-1">Calibration (30d)</div>
            <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
              <div>
                <div className="text-muted-foreground/60 text-[8px]">Directional</div>
                <div style={{ color: "#34d399" }}>68.3%</div>
              </div>
              <div>
                <div className="text-muted-foreground/60 text-[8px]">MAE</div>
                <div>1.82 pts</div>
              </div>
              <div>
                <div className="text-muted-foreground/60 text-[8px]">Slope</div>
                <div style={{ color: "#34d399" }}>0.97</div>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="px-3 py-1.5 border-t border-border/40 bg-background/30">
        <label className="flex items-center gap-2 text-[10px] font-mono cursor-pointer">
          <input
            type="checkbox"
            checked={showCalibration}
            onChange={(e) => onStateChange({ showCalibration: e.target.checked })}
            className="accent-primary"
          />
          <span className="text-muted-foreground">show calibration</span>
        </label>
      </div>
    </div>
  );
}
