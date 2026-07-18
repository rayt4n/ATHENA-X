"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import type { WatchlistState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Props {
  state: WatchlistState;
  onStateChange: (partial: Partial<WatchlistState>) => void;
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

interface Quote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
}

const DEFAULT_QUOTES: Quote[] = [
  { symbol: "SPY", name: "SPDR S&P 500 ETF", price: 585.42, change: 1.23, changePct: 0.0021 },
  { symbol: "QQQ", name: "Invesco QQQ Trust", price: 491.87, change: 2.45, changePct: 0.0050 },
  { symbol: "ES", name: "E-mini S&P 500 Futures", price: 5862.50, change: 4.50, changePct: 0.0008 },
  { symbol: "VIX", name: "CBOE Volatility Index", price: 18.42, change: -0.32, changePct: -0.0171 },
  { symbol: "SPX", name: "S&P 500 Index", price: 5855.20, change: 1.10, changePct: 0.0002 },
  { symbol: "NQ", name: "E-mini Nasdaq 100 Futures", price: 20450.75, change: 12.30, changePct: 0.0006 },
  { symbol: "IWM", name: "iShares Russell 2000", price: 222.15, change: -0.85, changePct: -0.0038 },
  { symbol: "DIA", name: "SPDR Dow Jones ETF", price: 432.10, change: 0.45, changePct: 0.0010 },
];

export function WatchlistModule({ state, onStateChange, selectedSymbol, onSelectSymbol }: Props) {
  const sortBy = state.sortBy ?? "symbol";
  const sortOrder = state.sortOrder ?? "asc";
  const symbols = state.symbols?.length ? state.symbols : DEFAULT_QUOTES.map((q) => q.symbol);
  const filtered = DEFAULT_QUOTES.filter((q) => symbols.includes(q.symbol));
  const [quotes, setQuotes] = useState<Quote[]>(filtered);

  useEffect(() => {
    const interval = setInterval(() => {
      setQuotes((prev) => {
        const base = prev.length ? prev : filtered;
        return base.map((q) => {
          const drift = (Math.random() - 0.5) * q.price * 0.0008;
          const newPrice = q.price + drift;
          return { ...q, price: newPrice, change: q.change + drift, changePct: q.change / q.price };
        });
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [filtered]);

  const sorted = [...quotes].sort((a, b) => {
    let cmp = 0;
    if (sortBy === "symbol") cmp = a.symbol.localeCompare(b.symbol);
    else if (sortBy === "price") cmp = a.price - b.price;
    else if (sortBy === "change") cmp = a.changePct - b.changePct;
    return sortOrder === "asc" ? cmp : -cmp;
  });

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border/40 bg-background/30 text-[9px] uppercase tracking-wider text-muted-foreground/70">
        <span>Symbol</span>
        <span className="ml-auto">Price</span>
        <span className="w-20 text-right">Change</span>
      </div>
      <div className="flex-1 overflow-y-auto scroll-thin">
        {sorted.map((q) => {
          const isPositive = q.change >= 0;
          const isSelected = q.symbol === selectedSymbol;
          return (
            <button
              key={q.symbol}
              onClick={() => onSelectSymbol(q.symbol)}
              className={`w-full text-left px-3 py-1.5 flex items-center text-[11px] border-b border-border/20 hover:bg-accent/30 transition-colors ${isSelected ? "bg-primary/8 border-l-2 border-l-primary" : ""}`}
            >
              <div className="min-w-0 flex-1">
                <div className="font-mono font-semibold">{q.symbol}</div>
                <div className="text-[8.5px] text-muted-foreground/60 truncate">{q.name}</div>
              </div>
              <div className="font-mono tabular-nums text-right">
                {q.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="w-20 text-right font-mono tabular-nums flex items-center justify-end gap-0.5" style={{ color: isPositive ? "#34d399" : "#f87171" }}>
                {isPositive ? <TrendingUp className="h-2.5 w-2.5" /> : <TrendingDown className="h-2.5 w-2.5" />}
                <span>{(q.changePct * 100).toFixed(2)}%</span>
              </div>
            </button>
          );
        })}
      </div>
      <div className="px-3 py-1.5 border-t border-border/40 bg-background/30 flex items-center gap-2 text-[9px] font-mono text-muted-foreground/70">
        <span>sort:</span>
        <select
          value={sortBy}
          onChange={(e) => onStateChange({ sortBy: e.target.value as WatchlistState["sortBy"] })}
          className="bg-transparent text-foreground text-[9px] focus:outline-none"
        >
          <option value="symbol">symbol</option>
          <option value="price">price</option>
          <option value="change">change</option>
        </select>
        <button
          onClick={() => onStateChange({ sortOrder: sortOrder === "asc" ? "desc" : "asc" })}
          className="text-primary hover:underline"
        >
          {sortOrder === "asc" ? "↑ asc" : "↓ desc"}
        </button>
      </div>
    </div>
  );
}
