"use client";

import { useState } from "react";
import type { NewsState } from "@/modules/trader-dashboard/lib/workspace-types";

interface NewsItem {
  id: string;
  headline: string;
  source: string;
  timestamp: number;
  impact: "high" | "medium" | "low";
  sentiment: number;
}

const SAMPLE_NEWS: NewsItem[] = [
  { id: "n1", headline: "CPI print scheduled for 8:30 AM ET — consensus 3.1% YoY", source: "Benzinga Pro", timestamp: Date.now() - 600000, impact: "high", sentiment: 0 },
  { id: "n2", headline: "Fed's Williams speaks at 11:00 AM ET on monetary policy outlook", source: "Reuters", timestamp: Date.now() - 540000, impact: "medium", sentiment: 0.1 },
  { id: "n3", headline: "NVDA announces partnership with sovereign wealth fund", source: "Bloomberg", timestamp: Date.now() - 420000, impact: "medium", sentiment: 0.4 },
  { id: "n4", headline: "Treasury announces 10Y auction at 1:00 PM ET — $42B", source: "US Treasury", timestamp: Date.now() - 300000, impact: "medium", sentiment: 0 },
  { id: "n5", headline: "ECB holds rates as expected; Lagarde hints at September cut", source: "Reuters", timestamp: Date.now() - 240000, impact: "medium", sentiment: 0.2 },
  { id: "n6", headline: "China PMI misses expectations at 49.4 vs 49.6 consensus", source: "Bloomberg", timestamp: Date.now() - 180000, impact: "medium", sentiment: -0.3 },
  { id: "n7", headline: "Oil rises 1.2% on Middle East supply concerns", source: "Bloomberg", timestamp: Date.now() - 120000, impact: "low", sentiment: -0.1 },
  { id: "n8", headline: "Initial jobless claims 218k vs 220k consensus", source: "DOL", timestamp: Date.now() - 60000, impact: "low", sentiment: 0.1 },
  { id: "n9", headline: "Semiconductor sector outperforming — SOXX +1.8%", source: "Benzinga Pro", timestamp: Date.now() - 30000, impact: "low", sentiment: 0.3 },
  { id: "n10", headline: "VIX term structure in contango — volatility expectations easing", source: "CBOE", timestamp: Date.now() - 15000, impact: "low", sentiment: 0.2 },
];

interface Props {
  state: NewsState;
  onStateChange: (partial: Partial<NewsState>) => void;
}

export function NewsModule({ state, onStateChange }: Props) {
  const filter = state.filter ?? "all";
  const searchQuery = state.searchQuery ?? "";
  const filtered = SAMPLE_NEWS.filter((n) => {
    if (filter !== "all" && n.impact !== filter) return false;
    if (searchQuery && !n.headline.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onStateChange({ searchQuery: e.target.value })}
          placeholder="search news…"
          className="flex-1 bg-background/60 border border-border/40 rounded px-2 py-0.5 text-[10px] font-mono focus:outline-none focus:border-primary/50"
        />
        <select
          value={filter}
          onChange={(e) => onStateChange({ filter: e.target.value as NewsState["filter"] })}
          className="bg-background/60 border border-border/40 rounded text-[9px] px-1 py-0.5 font-mono focus:outline-none"
        >
          <option value="all">all</option>
          <option value="high">high</option>
          <option value="medium">medium</option>
          <option value="low">low</option>
        </select>
      </div>
      <div className="flex-1 overflow-y-auto scroll-thin">
        {filtered.map((n) => {
          const impactColor = n.impact === "high" ? "#f87171" : n.impact === "medium" ? "#fbbf24" : "#94a3b8";
          return (
            <div key={n.id} className="px-3 py-2 border-b border-border/20 hover:bg-accent/30">
              <div className="flex items-start gap-2">
                <span className="text-[8px] font-mono uppercase tracking-wider px-1 py-0.5 rounded shrink-0 mt-0.5" style={{ color: impactColor, backgroundColor: `${impactColor}22`, border: `1px solid ${impactColor}55` }}>
                  {n.impact}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-[11px] leading-tight">{n.headline}</div>
                  <div className="text-[9px] font-mono text-muted-foreground/70 mt-0.5">
                    {n.source} · {new Date(n.timestamp).toLocaleTimeString("en-US", { hour12: false })}
                  </div>
                </div>
                {n.sentiment !== 0 && (
                  <span className="text-[9px] font-mono shrink-0" style={{ color: n.sentiment > 0 ? "#34d399" : "#f87171" }}>
                    {n.sentiment > 0 ? "+" : ""}{(n.sentiment * 100).toFixed(0)}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
