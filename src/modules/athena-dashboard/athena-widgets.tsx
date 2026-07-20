"use client";

/**
 * ATHENA-X Workspace Widgets
 *
 * Contains the actual widget components extracted from the original
 * dashboard/page.tsx. These are imported by workspace-composition.tsx
 * and registered with the WorkspaceRegistry.
 *
 * This file contains indicator rendering and API hook calls.
 * The composition layer (workspace-composition.tsx) does NOT —
 * it only assembles widgets.
 */

import { useState } from "react";
import {
  useInstruments,
  useMarketOverview,
  useChart,
  useInstitutional,
  useEvidence,
  useAIForecast,
  useReport,
  usePluginStatus,
  type EvidenceContributor,
} from "@/lib/athena-api";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, Wifi, AlertCircle, TrendingUp } from "lucide-react";

// ============================================================================
// Shared constants
// ============================================================================

const MARKET_INSTRUMENTS = ["SPY", "ES=F", "QQQ", "^VIX", "DX-Y.NYB", "^TNX", "GC=F", "CL=F"];
const INSTRUMENT_LABELS: Record<string, string> = {
  "ES=F": "ES", SPY: "SPY", QQQ: "QQQ", "^VIX": "VIX",
  "DX-Y.NYB": "DXY", "^TNX": "TNX", "GC=F": "Gold", "CL=F": "Oil",
};
const TIMEFRAMES = ["1m", "5m", "15m", "30m", "1H", "4H", "1D", "1W", "1M"];
const OVERLAYS = [
  { id: "ta.ema", label: "EMA" }, { id: "ta.sma", label: "SMA" }, { id: "ta.vwap", label: "VWAP" },
  { id: "ta.rsi", label: "RSI" }, { id: "ta.macd", label: "MACD" }, { id: "ta.adx", label: "ADX" },
  { id: "ta.atr", label: "ATR" }, { id: "ta.bollinger", label: "BOLL" },
  { id: "ta.support_resistance", label: "S/R" }, { id: "ta.swing", label: "SWING" },
  { id: "ta.trend", label: "TREND" }, { id: "ta.wyckoff", label: "WYCK" },
  { id: "ta.chan_theory", label: "CHAN" }, { id: "ta.elliott_wave", label: "ELLI" },
  { id: "ta.smart_money", label: "SM" }, { id: "ta.volume_price", label: "VP" },
  { id: "ta.volume_profile", label: "VOL" },
];

// ============================================================================
// Loading / Error helpers
// ============================================================================

function Loading({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center h-full min-h-[60px] text-muted-foreground">
      <Loader2 className="h-3 w-3 animate-spin mr-2" />
      <span className="text-[10px]">{label}…</span>
    </div>
  );
}

function ErrorMsg({ msg }: { msg: string }) {
  return (
    <div className="flex items-center justify-center h-full min-h-[60px] text-red-500">
      <AlertCircle className="h-3 w-3 mr-2 shrink-0" />
      <span className="text-[10px]">{msg}</span>
    </div>
  );
}

function CertBadge({ status }: { status: string }) {
  const cls =
    status === "CERTIFIED" || status === "VERIFIED"
      ? "bg-green-600 text-white"
      : status === "PROVISIONAL"
        ? "bg-amber-600 text-white"
        : "bg-red-600 text-white";
  return <span className={cn("text-[8px] px-1 py-0.5 rounded font-bold uppercase", cls)}>{status}</span>;
}

function MiniCard({ title, plugin, status, children }: { title: string; plugin?: string; status?: string; children: React.ReactNode }) {
  return (
    <Card className="border-border bg-card/50">
      <CardHeader className="pb-1 px-2 pt-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[10px] font-semibold leading-tight">{title}</CardTitle>
          {status && <CertBadge status={status} />}
        </div>
        {plugin && <div className="text-[8px] text-muted-foreground font-mono truncate">{plugin}</div>}
      </CardHeader>
      <CardContent className="px-2 pb-2 text-[10px]">{children}</CardContent>
    </Card>
  );
}

// ============================================================================
// TopBar Widget
// ============================================================================

function TopBar({ onSymbolSelect, selectedSymbol }: { onSymbolSelect: (s: string) => void; selectedSymbol: string }) {
  const { data, isLoading, isError } = useInstruments();

  return (
    <header className="border-b border-border bg-card/40 backdrop-blur-md flex items-center gap-3 px-3 py-1.5 shrink-0">
      <div className="flex items-center gap-2 shrink-0">
        <div className="flex items-center justify-center w-7 h-7 rounded bg-primary/15 border border-primary/30">
          <TrendingUp className="h-3.5 w-3.5 text-primary" />
        </div>
        <div>
          <div className="text-[11px] font-bold tracking-wide">ATHENA-X</div>
          <div className="text-[8px] uppercase tracking-wider text-muted-foreground">Trader Terminal</div>
        </div>
      </div>

      <div className="flex items-center gap-1 flex-1 overflow-x-auto">
        {isLoading && <Loading label="Loading instruments" />}
        {isError && <ErrorMsg msg="Instruments failed" />}
        {data?.instruments
          .filter((i) => MARKET_INSTRUMENTS.includes(i.symbol))
          .map((inst) => {
            const isSel = inst.symbol === selectedSymbol;
            return (
              <button
                key={inst.symbol}
                onClick={() => onSymbolSelect(inst.symbol)}
                className={cn(
                  "flex flex-col px-2 py-1 rounded border min-w-[60px] transition-colors",
                  isSel ? "border-primary bg-primary/10" : "border-border bg-muted/30 hover:bg-muted/50",
                )}
              >
                <span className="text-[10px] font-semibold">{INSTRUMENT_LABELS[inst.symbol] || inst.name}</span>
                <span className="text-[8px] text-muted-foreground font-mono">{inst.category}</span>
              </button>
            );
          })}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {data?.live_status && (
          <>
            <Badge variant={data.live_status.market_session === "REGULAR" ? "default" : "secondary"} className="text-[8px]">
              {data.live_status.market_session}
            </Badge>
            <div className="flex items-center gap-1 text-[8px] text-muted-foreground">
              <Wifi className="h-2.5 w-2.5 text-green-500" />
              <span>{data.live_status.agents_online} agents</span>
            </div>
          </>
        )}
      </div>
    </header>
  );
}

// ============================================================================
// LeftPanel Widget — Market Overview
// ============================================================================

function LeftPanel() {
  const { data, isLoading, isError, error } = useMarketOverview();

  return (
    <div className="w-[260px] shrink-0 border-r border-border bg-card/20 overflow-y-auto">
      <div className="px-2 py-1.5 border-b border-border">
        <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Market Overview</div>
      </div>
      <div className="p-1.5 space-y-1.5">
        {isLoading && <Loading label="Market overview" />}
        {isError && <ErrorMsg msg={error?.message || "Failed"} />}
        {data?.widgets.map((w) => (
          <MiniCard key={w.id} title={w.name} plugin={w.plugin} status={w.status}>
            <div className="space-y-0.5">
              {Object.entries(w.data).slice(0, 4).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}:</span>
                  <span className="font-mono font-medium">
                    {typeof v === "number" ? v.toFixed(2) : typeof v === "boolean" ? (v ? "Yes" : "No") : String(v).slice(0, 20)}
                  </span>
                </div>
              ))}
            </div>
          </MiniCard>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// CenterChart Widget
// ============================================================================

function CenterChart({ symbol }: { symbol: string }) {
  const [tf, setTf] = useState("15m");
  const [overlays, setOverlays] = useState<Set<string>>(new Set(["ta.ema", "ta.bollinger", "ta.vwap", "ta.support_resistance"]));
  const { data, isLoading, isError, error } = useChart(symbol, tf);

  const toggle = (id: string) => {
    setOverlays((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-background">
      <div className="flex items-center gap-2 px-2 py-1 border-b border-border shrink-0 flex-wrap">
        <span className="text-[11px] font-bold">{INSTRUMENT_LABELS[symbol] || symbol}</span>
        <div className="flex gap-0.5">
          {TIMEFRAMES.map((t) => (
            <button
              key={t}
              onClick={() => setTf(t)}
              className={cn(
                "px-1.5 py-0.5 text-[9px] rounded border transition-colors",
                tf === t ? "border-primary bg-primary/10 text-foreground font-medium" : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-0.5 ml-1">
          {OVERLAYS.map((o) => {
            const has = data?.overlays?.[o.id] !== undefined;
            const on = overlays.has(o.id);
            return (
              <button
                key={o.id}
                onClick={() => has && toggle(o.id)}
                disabled={!has}
                className={cn(
                  "px-1 py-0.5 text-[8px] rounded border transition-colors",
                  !has && "opacity-30 cursor-not-allowed",
                  on && has ? "border-blue-500 bg-blue-500/10 text-blue-400" : "border-border text-muted-foreground hover:text-foreground",
                )}
              >
                {o.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 p-2 min-h-0">
        {isLoading && <div className="flex items-center justify-center h-full"><Loading label="Loading chart" /></div>}
        {isError && <ErrorMsg msg={error?.message || "Chart failed"} />}
        {data && data.bars.length > 0 && (
          <ChartSVG bars={data.bars} overlays={data.overlays} activeOverlays={overlays} />
        )}
      </div>

      <div className="flex items-center gap-3 px-2 py-0.5 border-t border-border text-[9px] text-muted-foreground shrink-0">
        {data && (
          <>
            <span>Bars: <strong className="text-foreground font-mono">{data.bars.length}</strong></span>
            <span>Overlays: <strong className="text-foreground font-mono">{Object.keys(data.overlays).length}</strong></span>
            <span>Last: <strong className="text-foreground font-mono">{data.bars[data.bars.length - 1]?.close}</strong></span>
          </>
        )}
      </div>
    </div>
  );
}

function ChartSVG({ bars, overlays, activeOverlays }: { bars: Array<{ open: number; high: number; low: number; close: number; volume: number }>; overlays: Record<string, unknown>; activeOverlays: Set<string> }) {
  const W = 800, H = 380;
  const pad = { t: 15, r: 55, b: 25, l: 8 };
  const cw = W - pad.l - pad.r;
  const ch = H - pad.t - pad.b;
  const prices = bars.flatMap((b) => [b.high, b.low]);
  const minP = Math.min(...prices), maxP = Math.max(...prices), range = maxP - minP || 1;
  const yS = (p: number) => pad.t + ch - ((p - minP) / range) * ch;
  const xS = (i: number) => pad.l + (i / bars.length) * cw;
  const bw = (cw / bars.length) * 0.7;
  let el: string[] = [];

  for (let i = 0; i <= 4; i++) {
    const y = pad.t + (ch / 4) * i;
    const price = maxP - (range / 4) * i;
    el.push(`<line x1="${pad.l}" y1="${y}" x2="${W - pad.r}" y2="${y}" stroke="#1e2433" stroke-width="0.5"/>`);
    el.push(`<text x="${W - pad.r + 3}" y="${y + 3}" fill="#64748b" font-size="8" font-family="monospace">${price.toFixed(2)}</text>`);
  }

  bars.forEach((b, i) => {
    const x = xS(i);
    const up = b.close >= b.open;
    const c = up ? "#10b981" : "#ef4444";
    const bt = yS(Math.max(b.open, b.close));
    const bh = Math.max(1, Math.abs(yS(b.close) - yS(b.open)));
    el.push(`<line x1="${x + bw / 2}" y1="${yS(b.high)}" x2="${x + bw / 2}" y2="${yS(b.low)}" stroke="${c}" stroke-width="1"/>`);
    el.push(`<rect x="${x}" y="${bt}" width="${bw}" height="${bh}" fill="${c}" opacity="0.8"/>`);
  });

  if (activeOverlays.has("ta.ema") && overlays["ta.ema"]) {
    const od = overlays["ta.ema"] as Record<string, unknown>;
    const series = (od.metadata as Record<string, number[]>)?.ema_series || [];
    if (series.length > 1) {
      let path = "";
      const si = bars.length - series.length;
      series.forEach((v, i) => { path += (i === 0 ? "M" : " L") + `${xS(si + i) + bw / 2},${yS(v)}`; });
      el.push(`<path d="${path}" stroke="#3b82f6" stroke-width="1.5" fill="none"/>`);
    }
  }

  if (activeOverlays.has("ta.bollinger") && overlays["ta.bollinger"]) {
    const od = overlays["ta.bollinger"] as Record<string, unknown>;
    const bb = od.value as Record<string, number> | undefined;
    if (bb?.upper && bb?.lower) {
      el.push(`<line x1="${pad.l}" y1="${yS(bb.upper)}" x2="${W - pad.r}" y2="${yS(bb.upper)}" stroke="#f59e0b" stroke-width="1" stroke-dasharray="3,3" opacity="0.6"/>`);
      el.push(`<line x1="${pad.l}" y1="${yS(bb.lower)}" x2="${W - pad.r}" y2="${yS(bb.lower)}" stroke="#f59e0b" stroke-width="1" stroke-dasharray="3,3" opacity="0.6"/>`);
      el.push(`<text x="${pad.l + 3}" y="${yS(bb.upper) - 3}" fill="#f59e0b" font-size="8">BB ${bb.upper.toFixed(2)}</text>`);
    }
  }

  if (activeOverlays.has("ta.vwap") && overlays["ta.vwap"]) {
    const od = overlays["ta.vwap"] as Record<string, unknown>;
    const vwap = od.value as number | undefined;
    if (vwap) {
      el.push(`<line x1="${pad.l}" y1="${yS(vwap)}" x2="${W - pad.r}" y2="${yS(vwap)}" stroke="#8b5cf6" stroke-width="1.5" stroke-dasharray="5,3"/>`);
      el.push(`<text x="${pad.l + 3}" y="${yS(vwap) - 3}" fill="#8b5cf6" font-size="8">VWAP ${vwap.toFixed(2)}</text>`);
    }
  }

  if (activeOverlays.has("ta.support_resistance") && overlays["ta.support_resistance"]) {
    const od = overlays["ta.support_resistance"] as Record<string, unknown>;
    const sr = od.value as Record<string, number> | undefined;
    if (sr?.resistance && sr?.support) {
      el.push(`<line x1="${pad.l}" y1="${yS(sr.resistance)}" x2="${W - pad.r}" y2="${yS(sr.resistance)}" stroke="#ef4444" stroke-width="1" stroke-dasharray="2,4" opacity="0.5"/>`);
      el.push(`<line x1="${pad.l}" y1="${yS(sr.support)}" x2="${W - pad.r}" y2="${yS(sr.support)}" stroke="#10b981" stroke-width="1" stroke-dasharray="2,4" opacity="0.5"/>`);
      el.push(`<text x="${W - pad.r - 50}" y="${yS(sr.resistance) - 3}" fill="#ef4444" font-size="8">R: ${sr.resistance.toFixed(2)}</text>`);
      el.push(`<text x="${W - pad.r - 50}" y="${yS(sr.support) + 10}" fill="#10b981" font-size="8">S: ${sr.support.toFixed(2)}</text>`);
    }
  }

  let ro = "";
  for (const [id, od] of Object.entries(overlays)) {
    if (!activeOverlays.has(id)) continue;
    const name = OVERLAYS.find((o) => o.id === id)?.label || id;
    const d = od as Record<string, unknown>;
    let val = "";
    if (d.value !== undefined && d.value !== null) {
      if (typeof d.value === "number") val = d.value.toFixed(2);
      else if (typeof d.value === "string") val = d.value;
      else val = JSON.stringify(d.value).slice(0, 25);
    }
    ro += `<tspan x="${pad.l + 3}" dy="12" fill="#94a3b8" font-size="8" font-family="monospace">${name}: ${val}</tspan>`;
  }
  if (ro) el.push(`<text x="${pad.l + 3}" y="${pad.t + 8}">${ro}</text>`);

  return <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full" dangerouslySetInnerHTML={{ __html: el.join("") }} />;
}

// ============================================================================
// RightPanel Widget — Institutional Intelligence
// ============================================================================

function RightPanel() {
  const { data, isLoading, isError, error } = useInstitutional();

  return (
    <div className="w-[240px] shrink-0 border-l border-border bg-card/20 overflow-y-auto">
      <div className="px-2 py-1.5 border-b border-border">
        <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Institutional Intelligence</div>
      </div>
      <div className="p-1.5 space-y-1.5">
        {isLoading && <Loading label="Institutional" />}
        {isError && <ErrorMsg msg={error?.message || "Failed"} />}
        {data?.widgets.map((w) => (
          <MiniCard key={w.id} title={w.name} plugin={w.plugin} status={w.status}>
            <div className="space-y-0.5">
              {Object.entries(w.data).slice(0, 3).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}:</span>
                  <span className="font-mono font-medium">{String(v).slice(0, 20)}</span>
                </div>
              ))}
            </div>
          </MiniCard>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// BottomTabs Widget
// ============================================================================

function ContributorItem({ c, type }: { c: EvidenceContributor; type: string }) {
  const bc = type === "primary" ? "border-l-green-500" : type === "supporting" ? "border-l-blue-500" : type === "conflict" ? "border-l-red-500" : "border-l-muted-foreground";
  return (
    <div className={cn("p-1.5 rounded bg-muted/40 border-l-2", bc)}>
      <div className="flex justify-between text-[10px] mb-0.5">
        <span className="font-mono font-medium">{c.agent_id}</span>
        <span className="text-amber-500 font-mono text-[9px]">{(c.confidence * 100).toFixed(0)}%</span>
      </div>
      <div className="text-[9px] text-muted-foreground">{c.reason}</div>
    </div>
  );
}

function BottomTabs() {
  return (
    <div className="h-[220px] shrink-0 border-t border-border bg-card/20">
      <Tabs defaultValue="technical" className="h-full flex flex-col">
        <TabsList className="h-7 bg-transparent border-b border-border rounded-none px-1 shrink-0">
          <TabsTrigger value="technical" className="text-[10px] h-6 px-2">Technical</TabsTrigger>
          <TabsTrigger value="options" className="text-[10px] h-6 px-2">Options</TabsTrigger>
          <TabsTrigger value="ai" className="text-[10px] h-6 px-2">AI Analysis</TabsTrigger>
          <TabsTrigger value="evidence" className="text-[10px] h-6 px-2">Evidence</TabsTrigger>
          <TabsTrigger value="reports" className="text-[10px] h-6 px-2">Reports</TabsTrigger>
          <TabsTrigger value="plugins" className="text-[10px] h-6 px-2">Plugin Status</TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-y-auto p-2">
          <TabsContent value="technical" className="mt-0 h-full">
            <TechnicalTab />
          </TabsContent>
          <TabsContent value="options" className="mt-0 h-full">
            <OptionsTab />
          </TabsContent>
          <TabsContent value="ai" className="mt-0 h-full">
            <AITab />
          </TabsContent>
          <TabsContent value="evidence" className="mt-0 h-full">
            <EvidenceTab />
          </TabsContent>
          <TabsContent value="reports" className="mt-0 h-full">
            <ReportsTab />
          </TabsContent>
          <TabsContent value="plugins" className="mt-0 h-full">
            <PluginsTab />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

function TechnicalTab() {
  const { data, isLoading, isError, error } = useChart("SPY", "15m");
  if (isLoading) return <Loading label="Technical agents" />;
  if (isError) return <ErrorMsg msg={error?.message || "Failed"} />;
  if (!data) return null;
  const agents = Object.entries(data.overlays).slice(0, 12);
  return (
    <div className="grid grid-cols-4 gap-2">
      {agents.map(([id, od]) => {
        const d = od as Record<string, unknown>;
        let val = "";
        if (d.value !== undefined && d.value !== null) {
          if (typeof d.value === "number") val = d.value.toFixed(2);
          else if (typeof d.value === "string") val = d.value;
          else val = JSON.stringify(d.value).slice(0, 30);
        }
        return (
          <div key={id} className="p-1.5 rounded bg-muted/30 border border-border/50">
            <div className="text-[9px] font-mono text-muted-foreground">{id}</div>
            <div className="text-[10px] font-mono font-medium text-foreground">{val}</div>
            {d.confidence !== null && d.confidence !== undefined && (
              <div className="text-[8px] text-amber-500">{(Number(d.confidence) * 100).toFixed(0)}%</div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function OptionsTab() {
  const { data, isLoading, isError, error } = useInstitutional();
  if (isLoading) return <Loading label="Options data" />;
  if (isError) return <ErrorMsg msg={error?.message || "Failed"} />;
  if (!data) return null;
  return (
    <div className="grid grid-cols-4 gap-2">
      {data.widgets.slice(0, 8).map((w) => (
        <div key={w.id} className="p-1.5 rounded bg-muted/30 border border-border/50">
          <div className="text-[9px] font-medium">{w.name}</div>
          {Object.entries(w.data).slice(0, 2).map(([k, v]) => (
            <div key={k} className="text-[9px] text-muted-foreground">
              <span className="capitalize">{k.replace(/_/g, " ")}: </span>
              <span className="font-mono text-foreground">{String(v).slice(0, 15)}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function AITab() {
  const { data, isLoading, isError, error } = useAIForecast();
  if (isLoading) return <Loading label="AI forecast" />;
  if (isError) return <ErrorMsg msg={error?.message || "Failed"} />;
  if (!data) return null;
  return (
    <div className="grid grid-cols-4 gap-2">
      <div className="p-1.5 rounded bg-muted/30 border border-border/50">
        <div className="text-[9px] font-medium mb-1">Bias</div>
        <div className="text-[10px] text-green-500">Bull {(data.bias.bull * 100).toFixed(0)}%</div>
        <div className="text-[10px] text-amber-500">Neutral {(data.bias.neutral * 100).toFixed(0)}%</div>
        <div className="text-[10px] text-red-500">Bear {(data.bias.bear * 100).toFixed(0)}%</div>
      </div>
      <div className="p-1.5 rounded bg-muted/30 border border-border/50">
        <div className="text-[9px] font-medium mb-1">Expected Range</div>
        <div className="text-[10px] text-red-400">Low: {data.expected_range.low}</div>
        <div className="text-[10px]">Mid: {data.expected_range.mid}</div>
        <div className="text-[10px] text-green-400">High: {data.expected_range.high}</div>
      </div>
      <div className="p-1.5 rounded bg-muted/30 border border-border/50">
        <div className="text-[9px] font-medium mb-1">Volatility</div>
        <div className="text-[10px]">ATR: {data.expected_volatility.atr_14}</div>
        <div className="text-[10px]">IV Rank: {data.expected_volatility.iv_rank}</div>
        <div className="text-[10px]">Regime: {data.expected_volatility.regime}</div>
      </div>
      <div className="p-1.5 rounded bg-muted/30 border border-border/50">
        <div className="text-[9px] font-medium mb-1">Projections</div>
        {Object.entries(data.projections).map(([k, v]) => (
          <div key={k} className="text-[9px]">
            <span className="uppercase">{k}: </span>
            <span className={v.direction === "bullish" ? "text-green-500" : v.direction === "bearish" ? "text-red-500" : ""}>{v.direction}</span>
            <span className="text-muted-foreground ml-1">{v.expected_change}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function EvidenceTab() {
  const { data, isLoading, isError, error } = useEvidence("demo");
  if (isLoading) return <Loading label="Evidence" />;
  if (isError) return <ErrorMsg msg={error?.message || "Failed"} />;
  if (!data) return null;
  return (
    <div className="space-y-1">
      <div className="text-[11px] font-semibold text-foreground mb-1">{data.final_conclusion}</div>
      <div className="grid grid-cols-4 gap-2">
        <div>
          <div className="text-[9px] font-bold text-green-500 uppercase mb-1">Primary ({data.primary_contributors.length})</div>
          {data.primary_contributors.slice(0, 3).map((c, i) => <ContributorItem key={i} c={c} type="primary" />)}
        </div>
        <div>
          <div className="text-[9px] font-bold text-blue-500 uppercase mb-1">Supporting ({data.supporting_contributors.length})</div>
          {data.supporting_contributors.slice(0, 3).map((c, i) => <ContributorItem key={i} c={c} type="supporting" />)}
        </div>
        <div>
          <div className="text-[9px] font-bold text-muted-foreground uppercase mb-1">Contextual ({data.contextual_contributors.length})</div>
          {data.contextual_contributors.slice(0, 3).map((c, i) => <ContributorItem key={i} c={c} type="contextual" />)}
        </div>
        <div>
          <div className="text-[9px] font-bold text-red-500 uppercase mb-1">Conflicts ({data.conflicting_evidence.length})</div>
          {data.conflicting_evidence.slice(0, 3).map((c, i) => <ContributorItem key={i} c={c} type="conflict" />)}
        </div>
      </div>
    </div>
  );
}

function ReportsTab() {
  const { data, isLoading, isError, error } = useReport();
  if (isLoading) return <Loading label="Report" />;
  if (isError) return <ErrorMsg msg={error?.message || "Failed"} />;
  if (!data) return null;
  return (
    <div className="grid grid-cols-3 gap-2">
      {data.sections.slice(0, 6).map((s) => (
        <div key={s.id} className="p-1.5 rounded bg-muted/30 border-l-2 border-amber-500">
          <div className="text-[9px] font-bold text-amber-500 uppercase">{s.title}</div>
          <div className="text-[9px] text-muted-foreground font-mono">{s.source}</div>
          <div className="text-[9px] text-foreground mt-1 line-clamp-3">{s.content}</div>
        </div>
      ))}
    </div>
  );
}

function PluginsTab() {
  const { data, isLoading, isError, error } = usePluginStatus();
  if (isLoading) return <Loading label="Plugin status" />;
  if (isError) return <ErrorMsg msg={error?.message || "Failed"} />;
  if (!data) return null;
  return (
    <div className="space-y-1">
      <div className="flex gap-3 text-[10px] mb-1">
        <span>Total: <strong>{data.summary.total}</strong></span>
        <span className="text-green-500">Certified: <strong>{data.summary.certified}</strong></span>
        <span className="text-amber-500">Provisional: <strong>{data.summary.provisional}</strong></span>
        <span className="text-red-500">Needs Improvement: <strong>{data.summary.needs_improvement}</strong></span>
      </div>
      <table className="w-full text-[9px]">
        <thead>
          <tr className="text-muted-foreground border-b border-border">
            <th className="text-left py-0.5">Plugin</th>
            <th className="text-center">Exec Time</th>
            <th className="text-center">Cert</th>
          </tr>
        </thead>
        <tbody>
          {data.plugins.slice(0, 8).map((p) => (
            <tr key={p.name} className="border-b border-border/30">
              <td className="py-0.5 font-mono">{p.name}</td>
              <td className="text-center font-mono">{p.exec_time_ms.toFixed(3)}ms</td>
              <td className="text-center"><CertBadge status={p.certification} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================================
// Export all widgets for the composition layer
// ============================================================================

export const AthenaWidgets = {
  TopBar,
  LeftPanel,
  CenterChart,
  RightPanel,
  BottomTabs,
};
