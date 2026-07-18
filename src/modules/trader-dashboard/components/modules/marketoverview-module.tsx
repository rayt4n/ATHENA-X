"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import type { MarketOverviewState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Instrument {
  symbol: string;
  name: string;
  price: number;
  changePct: number;
}

const DEFAULT_INSTRUMENTS: Instrument[] = [
  { symbol: "SPY", name: "S&P 500 ETF", price: 585.42, changePct: 0.0021 },
  { symbol: "ES", name: "E-mini S&P Fut", price: 5862.50, changePct: 0.0008 },
  { symbol: "SPX", name: "S&P 500 Index", price: 5855.20, changePct: 0.0002 },
  { symbol: "QQQ", name: "Nasdaq 100 ETF", price: 491.87, changePct: 0.0050 },
  { symbol: "NQ", name: "E-mini Nasdaq Fut", price: 20450.75, changePct: 0.0006 },
  { symbol: "SOXX", name: "Semiconductors", price: 232.10, changePct: 0.0078 },
  { symbol: "VIX", name: "Volatility Index", price: 18.42, changePct: -0.0171 },
  { symbol: "VVIX", name: "Vol of Vol", price: 92.10, changePct: 0.0052 },
  { symbol: "MOVE", name: "Bond Vol Index", price: 102.50, changePct: 0.0049 },
  { symbol: "TNX", name: "10Y Treasury Yield", price: 4.28, changePct: 0.0042 },
  { symbol: "DXY", name: "Dollar Index", price: 104.32, changePct: -0.0008 },
  { symbol: "Gold", name: "Gold Futures", price: 2412.50, changePct: 0.0031 },
  { symbol: "Oil", name: "WTI Crude", price: 81.45, changePct: 0.0118 },
  { symbol: "Copper", name: "Copper Futures", price: 4.18, changePct: -0.0024 },
  { symbol: "USDJPY", name: "USD/JPY", price: 156.82, changePct: 0.0015 },
];

interface Props {
  state: MarketOverviewState;
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

export function MarketOverviewModule({ state, selectedSymbol, onSelectSymbol }: Props) {
  const [instruments, setInstruments] = useState(DEFAULT_INSTRUMENTS);

  useEffect(() => {
    const interval = setInterval(() => {
      setInstruments((prev) => prev.map((i) => {
        const drift = (Math.random() - 0.5) * i.price * 0.0005;
        return { ...i, price: i.price + drift, changePct: i.changePct + drift / i.price };
      }));
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full overflow-auto scroll-thin">
      <div className="grid grid-cols-3 md:grid-cols-5 gap-1 p-2">
        {instruments.map((inst) => {
          const isPositive = inst.changePct >= 0;
          const isSelected = inst.symbol === selectedSymbol;
          return (
            <button
              key={inst.symbol}
              onClick={() => onSelectSymbol(inst.symbol)}
              className={`rounded-md border p-2 text-center transition-colors ${isSelected ? "border-primary/60 bg-primary/5" : "border-border/40 bg-background/30 hover:bg-accent/30"}`}
            >
              <div className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/70">{inst.symbol}</div>
              <div className="text-[12px] font-mono font-bold tabular-nums mt-0.5">{inst.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
              <div className="text-[9px] font-mono flex items-center justify-center gap-0.5 mt-0.5" style={{ color: isPositive ? "#34d399" : "#f87171" }}>
                {isPositive ? <TrendingUp className="h-2 w-2" /> : <TrendingDown className="h-2 w-2" />}
                {(inst.changePct * 100).toFixed(2)}%
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
