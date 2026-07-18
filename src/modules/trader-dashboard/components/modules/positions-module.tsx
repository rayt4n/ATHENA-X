"use client";

import type { PositionsState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Position {
  id: string;
  symbol: string;
  type: "stock" | "option" | "future";
  side: "long" | "short";
  qty: number;
  entry: number;
  current: number;
  pnl: number;
  pnlR: number;
  status: "open" | "closed";
  openedAt: number;
}

const SAMPLE_POSITIONS: Position[] = [
  { id: "p1", symbol: "SPY", type: "option", side: "long", qty: 2, entry: 2.85, current: 3.42, pnl: 114, pnlR: 1.0, status: "open", openedAt: Date.now() - 7200000 },
  { id: "p2", symbol: "QQQ", type: "option", side: "short", qty: -1, entry: 1.95, current: 1.42, pnl: 53, pnlR: 0.8, status: "open", openedAt: Date.now() - 3600000 },
  { id: "p3", symbol: "ES", type: "future", side: "long", qty: 1, entry: 5848, current: 5862, pnl: 700, pnlR: 2.1, status: "open", openedAt: Date.now() - 10800000 },
  { id: "p4", symbol: "VIX", type: "option", side: "long", qty: 5, entry: 0.85, current: 0.62, pnl: -115, pnlR: -0.6, status: "open", openedAt: Date.now() - 1800000 },
  { id: "p5", symbol: "SPY", type: "option", side: "short", qty: -3, entry: 3.20, current: 2.10, pnl: 330, pnlR: 1.5, status: "closed", openedAt: Date.now() - 86400000 },
];

interface Props {
  state: PositionsState;
  onStateChange: (partial: Partial<PositionsState>) => void;
}

export function PositionsModule({ state, onStateChange }: Props) {
  const filter = state.filter ?? "all";
  const filtered = SAMPLE_POSITIONS.filter((p) => {
    if (filter === "open") return p.status === "open";
    if (filter === "closed") return p.status === "closed";
    if (filter === "today") return Date.now() - p.openedAt < 86400000;
    return true;
  });

  const totalPnl = filtered.reduce((s, p) => s + p.pnl, 0);

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center gap-2">
        <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/70">filter:</span>
        {["all", "open", "closed", "today"].map((f) => (
          <button
            key={f}
            onClick={() => onStateChange({ filter: f as PositionsState["filter"] })}
            className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${filter === f ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground border border-border/40"}`}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto text-[11px] font-mono font-bold" style={{ color: totalPnl >= 0 ? "#34d399" : "#f87171" }}>
          {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(0)}
        </span>
      </div>
      <div className="flex-1 overflow-auto scroll-thin">
        <table className="w-full text-[10px] font-mono">
          <thead className="sticky top-0 bg-card/80 backdrop-blur-sm">
            <tr className="border-b border-border/40 text-muted-foreground/60 text-[8px] uppercase tracking-wider">
              <th className="px-2 py-1 text-left">Symbol</th>
              <th className="px-2 py-1 text-right">Qty</th>
              <th className="px-2 py-1 text-right">Entry</th>
              <th className="px-2 py-1 text-right">Current</th>
              <th className="px-2 py-1 text-right">P&L</th>
              <th className="px-2 py-1 text-right">R</th>
              <th className="px-2 py-1 text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id} className="border-b border-border/10 hover:bg-accent/20">
                <td className="px-2 py-1">
                  <div className="font-bold">{p.symbol}</div>
                  <div className="text-[8px] text-muted-foreground/60">{p.type}</div>
                </td>
                <td className="px-2 py-1 text-right" style={{ color: p.side === "long" ? "#34d399" : "#f87171" }}>{p.qty > 0 ? "+" : ""}{p.qty}</td>
                <td className="px-2 py-1 text-right">{p.entry.toFixed(2)}</td>
                <td className="px-2 py-1 text-right">{p.current.toFixed(2)}</td>
                <td className="px-2 py-1 text-right font-bold" style={{ color: p.pnl >= 0 ? "#34d399" : "#f87171" }}>
                  {p.pnl >= 0 ? "+" : ""}${p.pnl.toFixed(0)}
                </td>
                <td className="px-2 py-1 text-right" style={{ color: p.pnlR >= 0 ? "#34d399" : "#f87171" }}>
                  {p.pnlR >= 0 ? "+" : ""}{p.pnlR.toFixed(2)}R
                </td>
                <td className="px-2 py-1 text-center">
                  <span className={`text-[8px] px-1 py-0.5 rounded ${p.status === "open" ? "bg-status-healthy/15 text-status-healthy" : "bg-muted/15 text-muted-foreground"}`}>
                    {p.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
