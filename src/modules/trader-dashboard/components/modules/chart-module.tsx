"use client";

import { useEffect, useState } from "react";
import { ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import type { ChartState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Props {
  state: ChartState;
  onStateChange: (partial: Partial<ChartState>) => void;
  selectedSymbol: string;
  onSelectTimeframe: (tf: string) => void;
}

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];

function generateCandles(symbol: string, timeframe: string, count: number) {
  const seed = symbol.charCodeAt(0) + timeframe.charCodeAt(0);
  let price = 585 + (seed % 20);
  const candles = [];
  for (let i = 0; i < count; i++) {
    const open = price;
    const change = (Math.random() - 0.5) * 4;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * 2;
    const low = Math.min(open, close) - Math.random() * 2;
    candles.push({
      time: `${i}`,
      open, close, high, low,
      volume: Math.floor(50000 + Math.random() * 100000),
      ema20: 0,
      vwap: 0,
    });
    price = close;
  }
  // Compute EMA-20
  const k = 2 / (20 + 1);
  let ema = candles[0].close;
  candles.forEach((c) => {
    ema = c.close * k + ema * (1 - k);
    c.ema20 = ema;
  });
  // Compute VWAP
  let cumPV = 0, cumV = 0;
  candles.forEach((c) => {
    const tp = (c.high + c.low + c.close) / 3;
    cumPV += tp * c.volume;
    cumV += c.volume;
    c.vwap = cumPV / cumV;
  });
  return candles;
}

export function ChartModule({ state, onStateChange, selectedSymbol, onSelectTimeframe }: Props) {
  const timeframe = state.timeframe ?? "5m";
  const chartType = state.chartType ?? "candle";
  const indicators = state.indicators ?? [];
  const initialData = generateCandles(selectedSymbol, timeframe, 60);
  const [data, setData] = useState<ReturnType<typeof generateCandles>>(initialData);
  const [lastKey, setLastKey] = useState(`${selectedSymbol}-${timeframe}`);

  useEffect(() => {
    const key = `${selectedSymbol}-${timeframe}`;
    if (key !== lastKey) {
      setData(generateCandles(selectedSymbol, timeframe, 60));
      setLastKey(key);
      onSelectTimeframe(timeframe);
    }
  }, [selectedSymbol, timeframe, lastKey, onSelectTimeframe]);

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border/40 bg-background/30">
        <span className="text-[12px] font-mono font-bold text-primary">{selectedSymbol}</span>
        <div className="flex gap-0.5 ml-2">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => onStateChange({ timeframe: tf })}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${timeframe === tf ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground hover:text-foreground"}`}
            >
              {tf}
            </button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-1">
          {["candle", "line", "area"].map((ct) => (
            <button
              key={ct}
              onClick={() => onStateChange({ chartType: ct as ChartState["chartType"] })}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${chartType === ct ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              {ct}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0 p-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 8 }} stroke="rgba(255,255,255,0.05)" interval={9} />
            <YAxis orientation="right" tick={{ fill: "#6b7280", fontSize: 8 }} stroke="rgba(255,255,255,0.05)" width={40} />
            <Tooltip
              contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10, fontFamily: "monospace" }}
              labelStyle={{ color: "#8b949e" }}
            />
            {chartType === "candle" && (
              <>
                <Bar dataKey="high" fill="#34d399" opacity={0} />
                <Line type="monotone" dataKey="close" stroke="#22d3ee" strokeWidth={1.5} dot={false} isAnimationActive={false} />
              </>
            )}
            {chartType === "line" && (
              <Line type="monotone" dataKey="close" stroke="#22d3ee" strokeWidth={1.5} dot={false} isAnimationActive={false} />
            )}
            {chartType === "area" && (
              <Line type="monotone" dataKey="close" stroke="#22d3ee" strokeWidth={1.5} dot={false} isAnimationActive={false} />
            )}
            {indicators.includes("EMA_20") && (
              <Line type="monotone" dataKey="ema20" stroke="#fbbf24" strokeWidth={1} dot={false} isAnimationActive={false} />
            )}
            {indicators.includes("VWAP") && (
              <Line type="monotone" dataKey="vwap" stroke="#a78bfa" strokeWidth={1} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Indicator toggles */}
      <div className="px-3 py-1.5 border-t border-border/40 bg-background/30 flex items-center gap-2 text-[9px] font-mono">
        <span className="text-muted-foreground/70">indicators:</span>
        {["EMA_20", "EMA_50", "VWAP", "RSI"].map((ind) => {
          const active = indicators.includes(ind);
          return (
            <button
              key={ind}
              onClick={() => {
                const indicators = active ? indicators.filter((i) => i !== ind) : [...indicators, ind];
                onStateChange({ indicators });
              }}
              className={`px-1.5 py-0.5 rounded ${active ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}
            >
              {ind}
            </button>
          );
        })}
      </div>
    </div>
  );
}
