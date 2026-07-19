"use client";

import { useState } from "react";
import { useChart, type Bar, type OverlayData } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Toggle } from "@/components/ui/toggle";

const TIMEFRAMES = ["1m", "5m", "15m", "30m", "1H", "4H", "1D", "1W", "1M"];

const OVERLAYS = [
  { id: "ta.ema", label: "EMA" }, { id: "ta.sma", label: "SMA" }, { id: "ta.vwap", label: "VWAP" },
  { id: "ta.rsi", label: "RSI" }, { id: "ta.macd", label: "MACD" }, { id: "ta.adx", label: "ADX" },
  { id: "ta.atr", label: "ATR" }, { id: "ta.bollinger", label: "BOLL" },
  { id: "ta.volume_profile", label: "VOL" }, { id: "ta.support_resistance", label: "S/R" },
  { id: "ta.swing", label: "SWING" }, { id: "ta.trend", label: "TREND" },
  { id: "ta.wyckoff", label: "WYCK" }, { id: "ta.chan_theory", label: "CHAN" },
  { id: "ta.elliott_wave", label: "ELLI" }, { id: "ta.smart_money", label: "SM" },
  { id: "ta.volume_price", label: "VP" },
];

function CandlestickChart({ bars, overlays, activeOverlays }: { bars: Bar[]; overlays: Record<string, OverlayData>; activeOverlays: Set<string> }) {
  if (!bars.length) return <div className="text-[11px] text-muted-foreground">No bars</div>;
  const W = 900, H = 400;
  const padding = { top: 20, right: 60, bottom: 40, left: 10 };
  const chartW = W - padding.left - padding.right;
  const chartH = H - padding.top - padding.bottom;
  const prices = bars.flatMap((b) => [b.high, b.low]);
  const minP = Math.min(...prices), maxP = Math.max(...prices), range = maxP - minP || 1;
  const yScale = (p: number) => padding.top + chartH - ((p - minP) / range) * chartH;
  const xScale = (i: number) => padding.left + (i / bars.length) * chartW;
  const barW = (chartW / bars.length) * 0.7;
  let el: string[] = [];
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (chartH / 4) * i;
    const price = maxP - (range / 4) * i;
    el.push(`<line x1="${padding.left}" y1="${y}" x2="${W - padding.right}" y2="${y}" stroke="#1e2433" stroke-width="0.5"/>`);
    el.push(`<text x="${W - padding.right + 4}" y="${y + 3}" fill="#64748b" font-size="9" font-family="monospace">${price.toFixed(2)}</text>`);
  }
  bars.forEach((b, i) => {
    const x = xScale(i);
    const isUp = b.close >= b.open;
    const color = isUp ? "#10b981" : "#ef4444";
    const bodyTop = yScale(Math.max(b.open, b.close));
    const bodyH = Math.max(1, Math.abs(yScale(b.close) - yScale(b.open)));
    el.push(`<line x1="${x + barW / 2}" y1="${yScale(b.high)}" x2="${x + barW / 2}" y2="${yScale(b.low)}" stroke="${color}" stroke-width="1"/>`);
    el.push(`<rect x="${x}" y="${bodyTop}" width="${barW}" height="${bodyH}" fill="${color}" opacity="0.8"/>`);
  });
  if (activeOverlays.has("ta.ema") && overlays["ta.ema"]) {
    const series = (overlays["ta.ema"].metadata as Record<string, number[]>)?.ema_series || [];
    if (series.length > 1) {
      let path = "";
      const startIdx = bars.length - series.length;
      series.forEach((v, i) => { const x = xScale(startIdx + i) + barW / 2; const y = yScale(v); path += i === 0 ? `M${x},${y}` : ` L${x},${y}`; });
      el.push(`<path d="${path}" stroke="#3b82f6" stroke-width="1.5" fill="none"/>`);
    }
  }
  if (activeOverlays.has("ta.bollinger") && overlays["ta.bollinger"]) {
    const bb = overlays["ta.bollinger"].value as Record<string, number> | undefined;
    if (bb?.upper && bb?.lower) {
      el.push(`<line x1="${padding.left}" y1="${yScale(bb.upper)}" x2="${W - padding.right}" y2="${yScale(bb.upper)}" stroke="#f59e0b" stroke-width="1" stroke-dasharray="3,3" opacity="0.6"/>`);
      el.push(`<line x1="${padding.left}" y1="${yScale(bb.lower)}" x2="${W - padding.right}" y2="${yScale(bb.lower)}" stroke="#f59e0b" stroke-width="1" stroke-dasharray="3,3" opacity="0.6"/>`);
    }
  }
  if (activeOverlays.has("ta.vwap") && overlays["ta.vwap"]) {
    const vwap = overlays["ta.vwap"].value as number | undefined;
    if (vwap) el.push(`<line x1="${padding.left}" y1="${yScale(vwap)}" x2="${W - padding.right}" y2="${yScale(vwap)}" stroke="#8b5cf6" stroke-width="1.5" stroke-dasharray="5,3"/>`);
  }
  if (activeOverlays.has("ta.support_resistance") && overlays["ta.support_resistance"]) {
    const sr = overlays["ta.support_resistance"].value as Record<string, number> | undefined;
    if (sr?.resistance && sr?.support) {
      el.push(`<line x1="${padding.left}" y1="${yScale(sr.resistance)}" x2="${W - padding.right}" y2="${yScale(sr.resistance)}" stroke="#ef4444" stroke-width="1" stroke-dasharray="2,4" opacity="0.5"/>`);
      el.push(`<line x1="${padding.left}" y1="${yScale(sr.support)}" x2="${W - padding.right}" y2="${yScale(sr.support)}" stroke="#10b981" stroke-width="1" stroke-dasharray="2,4" opacity="0.5"/>`);
    }
  }
  let readout = "";
  for (const [id, od] of Object.entries(overlays)) {
    if (!activeOverlays.has(id)) continue;
    const name = OVERLAYS.find((o) => o.id === id)?.label || id;
    let val = "";
    if (od.value !== undefined && od.value !== null) {
      if (typeof od.value === "number") val = od.value.toFixed(2);
      else if (typeof od.value === "string") val = od.value;
      else val = JSON.stringify(od.value).slice(0, 30);
    }
    readout += `<tspan x="${padding.left + 4}" dy="14" fill="#94a3b8" font-size="9" font-family="monospace">${name}: ${val}</tspan>`;
  }
  if (readout) el.push(`<text x="${padding.left + 4}" y="${padding.top + 10}">${readout}</text>`);
  return <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full" dangerouslySetInnerHTML={{ __html: el.join("") }} />;
}

export default function ChartPage() {
  const [symbol, setSymbol] = useState("SPY");
  const [timeframe, setTimeframe] = useState("15m");
  const [activeOverlays, setActiveOverlays] = useState<Set<string>>(new Set(["ta.ema", "ta.bollinger", "ta.vwap", "ta.support_resistance"]));
  const { data, isLoading, isError, error } = useChart(symbol, timeframe);

  const toggleOverlay = (id: string) => {
    setActiveOverlays((prev) => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Professional Chart</h1>
        <p className="text-[12px] text-muted-foreground">Candlestick chart with 17 indicator overlays. Data from Layer 1-3 runtime agents via /trading/chart/.</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className="bg-card border border-border rounded px-2 py-1 text-[12px]">
          <option value="SPY">SPY</option><option value="ES=F">ES</option><option value="QQQ">QQQ</option>
          <option value="IWM">IWM</option><option value="DIA">DIA</option>
        </select>
        <div className="flex gap-1">
          {TIMEFRAMES.map((tf) => (
            <Button key={tf} size="sm" variant={timeframe === tf ? "default" : "outline"} className="h-7 px-2 text-[10px]" onClick={() => setTimeframe(tf)}>{tf}</Button>
          ))}
        </div>
        <div className="flex flex-wrap gap-1 ml-2">
          {OVERLAYS.map((o) => {
            const has = data?.overlays?.[o.id] !== undefined;
            const on = activeOverlays.has(o.id);
            return <Toggle key={o.id} size="sm" pressed={on && has} disabled={!has} onPressedChange={() => toggleOverlay(o.id)} className={cn("h-7 px-2 text-[9px]", !has && "opacity-40")}>{o.label}</Toggle>;
          })}
        </div>
      </div>
      <WidgetCard title={`${symbol} · ${timeframe}`} plugin="17 runtime agents (ta.ema, ta.bollinger, ta.vwap, ta.sr, +13 more)" status="VERIFIED">
        <div className="h-[400px]">
          <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading chart data">
            {data && <CandlestickChart bars={data.bars} overlays={data.overlays} activeOverlays={activeOverlays} />}
          </QueryBoundary>
        </div>
        {data && (
          <div className="flex gap-4 mt-2 text-[10px] text-muted-foreground">
            <span>Bars: <strong className="text-foreground font-mono">{data.bars.length}</strong></span>
            <span>Overlays: <strong className="text-foreground font-mono">{Object.keys(data.overlays).length}</strong></span>
          </div>
        )}
      </WidgetCard>
    </div>
  );
}
