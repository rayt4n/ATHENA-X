"use client";

import { useEffect, useState } from "react";
import { GitCompare, Search } from "lucide-react";
import type { ComparisonResult } from "../lib/types";

export function DataComparison() {
  const [symbol, setSymbol] = useState("SPY");
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchComparison = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/providers/health?comparison=${symbol}`);
      const data = await res.json();
      setResult(data.comparison ?? null);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
    const interval = setInterval(fetchComparison, 5000);
    return () => clearInterval(interval);
  }, [symbol]);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border bg-card/40 p-4">
        <div className="flex items-center gap-2 mb-3">
          <GitCompare className="h-3.5 w-3.5 text-primary" />
          <h2 className="text-[13px] font-semibold uppercase tracking-wide">Data Comparison</h2>
        </div>
        <p className="text-[11px] text-muted-foreground mb-4">
          Compare the same symbol across multiple providers. Useful for QA when adding new providers.
          Shows price difference and timestamp delta between providers.
        </p>

        <div className="flex items-center gap-2 mb-4">
          <Search className="h-3 w-3 text-muted-foreground" />
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="SPY"
            className="w-24 bg-background/60 border border-border/40 rounded px-2 py-1 text-[11px] font-mono focus:outline-none focus:border-primary/50" />
        </div>

        {!result && !loading && (
          <div className="text-center py-8 text-[11px] text-muted-foreground/70 font-mono">
            No comparison data yet. Fetch data from multiple providers using Diagnostics to populate.
          </div>
        )}

        {result && (
          <div className="space-y-3">
            {/* Summary */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-md border border-border/40 bg-background/30 p-3 text-center">
                <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">Max Price Difference</div>
                <div className="text-[18px] font-mono font-bold mt-1" style={{ color: result.maxDifference > 0.05 ? "#fbbf24" : "#34d399" }}>
                  ${result.maxDifference.toFixed(4)}
                </div>
              </div>
              <div className="rounded-md border border-border/40 bg-background/30 p-3 text-center">
                <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70">Max Timestamp Delta</div>
                <div className="text-[18px] font-mono font-bold mt-1 text-muted-foreground">
                  {result.maxTimestampDeltaMs}ms
                </div>
              </div>
            </div>

            {/* Provider comparison table */}
            <div className="rounded-md border border-border/40 overflow-hidden">
              <div className="grid grid-cols-12 px-3 py-1.5 text-[8.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
                <div className="col-span-3">Provider</div>
                <div className="col-span-3 text-right">Price</div>
                <div className="col-span-3 text-right">Quality</div>
                <div className="col-span-3 text-right">Timestamp</div>
              </div>
              {result.entries.map((entry, i) => (
                <div key={i} className="grid grid-cols-12 px-3 py-1 text-[10.5px] items-center border-b border-border/10">
                  <div className="col-span-3 font-mono">{entry.provider}</div>
                  <div className="col-span-3 text-right font-mono tabular-nums">${entry.price.toFixed(2)}</div>
                  <div className="col-span-3 text-right font-mono tabular-nums text-muted-foreground">{(entry.qualityScore * 100).toFixed(0)}%</div>
                  <div className="col-span-3 text-right font-mono text-[9px] text-muted-foreground">
                    {new Date(entry.timestamp).toLocaleTimeString("en-US", { hour12: false })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
