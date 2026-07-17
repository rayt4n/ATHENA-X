"use client";

import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, BarChart, Bar, Cell } from "recharts";
import { Gauge, TrendingUp, Target } from "lucide-react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { fmtTime, fmtNum, fmtPct } from "@/lib/dashboard/format";
import { STATUS_COLORS } from "@/lib/dashboard/colors";
import type { DashboardTelemetry } from "@/lib/dashboard/types";

export function ForecastPanel({ t }: { t: DashboardTelemetry }) {
  const { summary, recent } = t.forecast;

  return (
    <PanelGrid>
      <Panel
        title="Forecast Accuracy Summary"
        subtitle={`${summary.resolvedCount.toLocaleString()} resolved of ${summary.totalForecasts.toLocaleString()} total`}
        icon={<Gauge className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2">
          <Stat label="Hit Rate" value={fmtPct(summary.hitRate, 1)} intent={summary.hitRate > 0.65 ? "healthy" : summary.hitRate > 0.55 ? "warning" : "critical"} />
          <Stat label="Calibration" value={summary.calibrationSlope.toFixed(3)} intent={Math.abs(1 - summary.calibrationSlope) < 0.1 ? "healthy" : "warning"} />
          <Stat label="MAE" value={summary.mae.toFixed(2)} unit="pts" intent={summary.mae < 2 ? "healthy" : "warning"} />
          <Stat label="RMSE" value={summary.rmse.toFixed(2)} unit="pts" intent={summary.rmse < 3 ? "healthy" : "warning"} />
        </div>
      </Panel>

      <Panel
        title="Calibration Curve"
        subtitle="Predicted vs observed frequency (ideal: y=x)"
        icon={<Target className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-5"
      >
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={summary.calibrationCurve} margin={{ top: 8, right: 12, bottom: 18, left: 0 }}>
              <XAxis
                dataKey="bucket"
                type="number"
                domain={[0, 1]}
                ticks={[0, 0.25, 0.5, 0.75, 1]}
                tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "var(--font-geist-mono)" }}
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="rgba(255,255,255,0.08)"
              />
              <YAxis
                domain={[0, 1]}
                ticks={[0, 0.25, 0.5, 0.75, 1]}
                tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "var(--font-geist-mono)" }}
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="rgba(255,255,255,0.08)"
                width={36}
              />
              <Tooltip
                contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10.5, fontFamily: "var(--font-geist-mono)", color: "#e6edf3" }}
                formatter={(v: number, n: string) => [`${(v * 100).toFixed(1)}%`, n === "predicted" ? "predicted" : "observed"]}
                labelFormatter={(l) => `bucket ${(l * 100).toFixed(0)}%`}
              />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#6b7280" strokeDasharray="3 3" strokeOpacity={0.5} />
              <Line type="monotone" dataKey="predicted" stroke="#6b7280" strokeWidth={1} dot={false} strokeDasharray="3 3" isAnimationActive={false} />
              <Line type="monotone" dataKey="observed" stroke={STATUS_COLORS.info} strokeWidth={2.2} dot={{ r: 2.5, fill: STATUS_COLORS.info }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel
        title="Per-Model Hit Rate"
        subtitle={`${summary.perModel.length} active models`}
        icon={<TrendingUp className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-4"
      >
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={summary.perModel} layout="vertical" margin={{ top: 4, right: 12, bottom: 4, left: 8 }}>
              <XAxis type="number" domain={[0, 1]} tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "var(--font-geist-mono)" }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} stroke="rgba(255,255,255,0.08)" />
              <YAxis type="category" dataKey="model" tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }} width={120} stroke="rgba(255,255,255,0.08)" />
              <Tooltip
                contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10.5, fontFamily: "var(--font-geist-mono)", color: "#e6edf3" }}
                formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "hit rate"]}
              />
              <ReferenceLine x={0.5} stroke={STATUS_COLORS.warning} strokeDasharray="2 2" strokeOpacity={0.5} />
              <ReferenceLine x={0.65} stroke={STATUS_COLORS.healthy} strokeDasharray="2 2" strokeOpacity={0.5} />
              <Bar dataKey="hitRate" radius={[0, 3, 3, 0]} isAnimationActive={false}>
                {summary.perModel.map((m, i) => (
                  <Cell key={i} fill={m.hitRate > 0.65 ? STATUS_COLORS.healthy : m.hitRate > 0.55 ? STATUS_COLORS.warning : STATUS_COLORS.critical} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel
        title="Recent Forecasts"
        subtitle="Latest 14 — pending & resolved"
        icon={<Gauge className="h-3.5 w-3.5" />}
        className="col-span-12"
        bodyClassName="p-0"
      >
        <div className="max-h-[320px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-4 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-1">Time</div>
            <div className="col-span-3">Model</div>
            <div className="col-span-1">Sym</div>
            <div className="col-span-1">Horizon</div>
            <div className="col-span-2 text-right">Predicted</div>
            <div className="col-span-2 text-right">Realized</div>
            <div className="col-span-1 text-right">Error</div>
            <div className="col-span-1 text-right">Conf</div>
          </div>
          {recent.map((r) => (
            <div key={r.id} className="grid grid-cols-12 px-4 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-1 font-mono text-[10px] text-muted-foreground">{fmtTime(r.timestamp)}</div>
              <div className="col-span-3 font-mono text-muted-foreground truncate">{r.model}</div>
              <div className="col-span-1 font-mono font-semibold">{r.target}</div>
              <div className="col-span-1 font-mono text-[10px] text-muted-foreground">{r.horizon}</div>
              <div className="col-span-2 text-right font-mono tabular-nums">{fmtNum(r.predicted)}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{r.realized !== undefined ? fmtNum(r.realized) : "—"}</div>
              <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: r.error === undefined ? "#94a3b8" : r.error < 2 ? "#34d399" : r.error < 4 ? "#fbbf24" : "#f87171" }}>
                {r.error !== undefined ? r.error.toFixed(2) : "—"}
              </div>
              <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: r.confidence > 0.7 ? "#34d399" : r.confidence > 0.5 ? "#fbbf24" : "#f87171" }}>
                {fmtPct(r.confidence, 0)}
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </PanelGrid>
  );
}
