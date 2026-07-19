"use client";

import { useChart } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";

const TECHNICAL_AGENTS = [
  { id: "ta.trend", name: "Trend Detection", layer: 1 },
  { id: "ta.swing", name: "Swing High/Low", layer: 1 },
  { id: "ta.support_resistance", name: "Support/Resistance", layer: 1 },
  { id: "ta.liquidity", name: "Liquidity", layer: 1 },
  { id: "ta.volume_profile", name: "Volume Profile", layer: 1 },
  { id: "ta.ema", name: "EMA", layer: 2 },
  { id: "ta.sma", name: "SMA", layer: 2 },
  { id: "ta.vwap", name: "VWAP", layer: 2 },
  { id: "ta.rsi", name: "RSI", layer: 2 },
  { id: "ta.macd", name: "MACD", layer: 2 },
  { id: "ta.adx", name: "ADX", layer: 2 },
  { id: "ta.atr", name: "ATR", layer: 2 },
  { id: "ta.bollinger", name: "Bollinger Bands", layer: 2 },
  { id: "ta.wyckoff", name: "Wyckoff", layer: 3 },
  { id: "ta.chan_theory", name: "Chan Theory", layer: 3 },
  { id: "ta.elliott_wave", name: "Elliott Wave", layer: 3 },
  { id: "ta.smart_money", name: "Smart Money", layer: 3 },
  { id: "ta.volume_price", name: "Volume Price", layer: 3 },
];

function AgentOutput({ agentId, value, confidence }: { agentId: string; value: unknown; confidence: number | null | undefined }) {
  let display = "";
  if (value === null || value === undefined) display = "—";
  else if (typeof value === "number") display = value.toFixed(4);
  else if (typeof value === "string") display = value;
  else if (typeof value === "object") display = JSON.stringify(value).slice(0, 60);
  else display = String(value);

  return (
    <div className="flex justify-between items-center text-[11px] py-1 border-b border-border/50 last:border-0">
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono shrink-0">L{TECHNICAL_AGENTS.find(a => a.id === agentId)?.layer}</span>
        <span className="text-muted-foreground truncate">{TECHNICAL_AGENTS.find(a => a.id === agentId)?.name || agentId}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="font-mono font-medium text-foreground">{display}</span>
        {confidence !== null && confidence !== undefined && (
          <span className="text-[9px] text-amber-500 font-mono">{(confidence * 100).toFixed(0)}%</span>
        )}
      </div>
    </div>
  );
}

export default function TechnicalPage() {
  const { data, isLoading, isError, error } = useChart("SPY", "15m");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Technical Analysis</h1>
        <p className="text-[12px] text-muted-foreground">All 18 runtime TA agents across Layer 1 (Market Structure), Layer 2 (Indicators), and Layer 3 (Institutional). Data from /trading/chart/SPY.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <WidgetCard title="Layer 1 — Market Structure" plugin="ta.trend, ta.swing, ta.support_resistance, ta.liquidity, ta.volume_profile" status="VERIFIED">
          <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading Layer 1">
            {data && (
              <div className="space-y-0">
                {["ta.trend", "ta.swing", "ta.support_resistance", "ta.liquidity", "ta.volume_profile"].map((id) => (
                  <AgentOutput key={id} agentId={id} value={data.overlays[id]?.value} confidence={data.overlays[id]?.confidence} />
                ))}
              </div>
            )}
          </QueryBoundary>
        </WidgetCard>
        <WidgetCard title="Layer 2 — Indicators" plugin="ta.ema, ta.sma, ta.vwap, ta.rsi, ta.macd, ta.adx, ta.atr, ta.bollinger" status="CERTIFIED">
          <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading Layer 2">
            {data && (
              <div className="space-y-0">
                {["ta.ema", "ta.sma", "ta.vwap", "ta.rsi", "ta.macd", "ta.adx", "ta.atr", "ta.bollinger"].map((id) => (
                  <AgentOutput key={id} agentId={id} value={data.overlays[id]?.value} confidence={data.overlays[id]?.confidence} />
                ))}
              </div>
            )}
          </QueryBoundary>
        </WidgetCard>
        <WidgetCard title="Layer 3 — Institutional" plugin="ta.wyckoff, ta.chan_theory, ta.elliott_wave, ta.smart_money, ta.volume_price" status="PROVISIONAL" className="md:col-span-2">
          <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading Layer 3">
            {data && (
              <div className="grid grid-cols-2 gap-x-6">
                {["ta.wyckoff", "ta.chan_theory", "ta.elliott_wave", "ta.smart_money", "ta.volume_price"].map((id) => (
                  <AgentOutput key={id} agentId={id} value={data.overlays[id]?.value} confidence={data.overlays[id]?.confidence} />
                ))}
              </div>
            )}
          </QueryBoundary>
        </WidgetCard>
      </div>
    </div>
  );
}
