"use client";

import { useState } from "react";
import type { OptionsChainState } from "@/modules/trader-dashboard/lib/workspace-types";

interface Props {
  state: OptionsChainState;
  onStateChange: (partial: Partial<OptionsChainState>) => void;
  selectedSymbol: string;
}

interface OptionRow {
  strike: number;
  callBid: number;
  callAsk: number;
  callDelta: number;
  callGamma: number;
  callTheta: number;
  callIV: number;
  callVol: number;
  callOI: number;
  putBid: number;
  putAsk: number;
  putDelta: number;
  putGamma: number;
  putTheta: number;
  putIV: number;
  putVol: number;
  putOI: number;
}

const EXPIRATIONS = ["2026-07-18", "2026-07-25", "2026-08-01", "2026-08-15", "2026-09-19"];

function generateChain(symbol: string, expiration: string, strikeRange: number): OptionRow[] {
  const base = 585 + (symbol.charCodeAt(0) % 10);
  const rows: OptionRow[] = [];
  for (let i = -strikeRange; i <= strikeRange; i += 1) {
    const strike = base + i;
    const distance = Math.abs(i) / strikeRange;
    const callDelta = Math.max(0.01, Math.min(0.99, 0.5 - i * 0.04));
    const putDelta = callDelta - 1;
    const gamma = Math.max(0.001, 0.05 * (1 - distance));
    const theta = -Math.max(0.01, 0.5 * (1 - distance * 0.5));
    const iv = 0.14 + distance * 0.08;
    rows.push({
      strike,
      callBid: Math.max(0.05, 12 - i * 0.8 - Math.random()),
      callAsk: Math.max(0.06, 12.2 - i * 0.8 - Math.random()),
      callDelta, callGamma, callTheta, callIV: iv,
      callVol: Math.floor(100 + Math.random() * 5000),
      callOI: Math.floor(500 + Math.random() * 20000),
      putBid: Math.max(0.05, 12 + i * 0.8 - Math.random()),
      putAsk: Math.max(0.06, 12.2 + i * 0.8 - Math.random()),
      putDelta, putGamma, putTheta: theta, putIV: iv + 0.005,
      putVol: Math.floor(100 + Math.random() * 5000),
      putOI: Math.floor(500 + Math.random() * 20000),
    });
  }
  return rows;
}

export function OptionsChainModule({ state, onStateChange, selectedSymbol }: Props) {
  const expiration = state.expiration ?? "2026-07-18";
  const strikeRange = state.strikeRange ?? 15;
  const greekView = state.greekView ?? "delta";
  const [data] = useState(() => generateChain(selectedSymbol, expiration, strikeRange));

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border/40 bg-background/30">
        <span className="text-[11px] font-mono font-bold text-primary">{selectedSymbol}</span>
        <select
          value={expiration}
          onChange={(e) => onStateChange({ expiration: e.target.value })}
          className="bg-background/60 border border-border/40 rounded text-[10px] px-1 py-0.5 font-mono focus:outline-none"
        >
          {EXPIRATIONS.map((exp) => <option key={exp} value={exp}>{exp}</option>)}
        </select>
        <div className="ml-auto flex gap-0.5">
          {(["delta", "gamma", "theta", "vega"] as const).map((g) => (
            <button
              key={g}
              onClick={() => onStateChange({ greekView: g })}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${greekView === g ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground hover:text-foreground"}`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-auto scroll-thin">
        <table className="w-full text-[9.5px] font-mono">
          <thead className="sticky top-0 bg-card/80 backdrop-blur-sm">
            <tr className="border-b border-border/40 text-muted-foreground/70 uppercase tracking-wider">
              <th colSpan={4} className="px-2 py-1 text-center text-[8px] border-r border-border/40">CALLS</th>
              <th className="px-2 py-1 text-center text-[8px]">STRIKE</th>
              <th colSpan={4} className="px-2 py-1 text-center text-[8px] border-l border-border/40">PUTS</th>
            </tr>
            <tr className="border-b border-border/40 text-muted-foreground/60 text-[8px]">
              <th className="px-1 py-0.5 text-right">Vol</th>
              <th className="px-1 py-0.5 text-right">OI</th>
              <th className="px-1 py-0.5 text-right">IV</th>
              <th className="px-1 py-0.5 text-right border-r border-border/40">{greekView}</th>
              <th className="px-1 py-0.5 text-center"></th>
              <th className="px-1 py-0.5 text-right border-l border-border/40">{greekView}</th>
              <th className="px-1 py-0.5 text-right">IV</th>
              <th className="px-1 py-0.5 text-right">OI</th>
              <th className="px-1 py-0.5 text-right">Vol</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => {
              const atm = Math.abs(row.strike - 585) < 1;
              return (
                <tr key={i} className={`border-b border-border/10 hover:bg-accent/20 ${atm ? "bg-primary/5" : ""}`}>
                  <td className="px-1 py-0.5 text-right text-muted-foreground">{row.callVol.toLocaleString()}</td>
                  <td className="px-1 py-0.5 text-right text-muted-foreground">{row.callOI.toLocaleString()}</td>
                  <td className="px-1 py-0.5 text-right" style={{ color: row.callIV > 0.2 ? "#fbbf24" : "#94a3b8" }}>{(row.callIV * 100).toFixed(1)}</td>
                  <td className="px-1 py-0.5 text-right border-r border-border/40" style={{ color: row.callDelta > 0.5 ? "#34d399" : "#94a3b8" }}>
                    {greekView === "delta" ? row.callDelta.toFixed(3) : greekView === "gamma" ? row.callGamma.toFixed(4) : greekView === "theta" ? row.callTheta.toFixed(3) : (row.callIV * 100).toFixed(1)}
                  </td>
                  <td className="px-1 py-0.5 text-center font-bold" style={{ color: atm ? "#22d3ee" : "#e6edf3" }}>{row.strike.toFixed(0)}</td>
                  <td className="px-1 py-0.5 text-right border-l border-border/40" style={{ color: Math.abs(row.putDelta) > 0.5 ? "#f87171" : "#94a3b8" }}>
                    {greekView === "delta" ? row.putDelta.toFixed(3) : greekView === "gamma" ? row.putGamma.toFixed(4) : greekView === "theta" ? row.putTheta.toFixed(3) : (row.putIV * 100).toFixed(1)}
                  </td>
                  <td className="px-1 py-0.5 text-right" style={{ color: row.putIV > 0.2 ? "#fbbf24" : "#94a3b8" }}>{(row.putIV * 100).toFixed(1)}</td>
                  <td className="px-1 py-0.5 text-right text-muted-foreground">{row.putOI.toLocaleString()}</td>
                  <td className="px-1 py-0.5 text-right text-muted-foreground">{row.putVol.toLocaleString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
