"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceLine } from "recharts";
import { Beaker, Activity, Layers, Clock } from "lucide-react";
import { useState } from "react";
import { Panel, PanelGrid } from "../panel";
import { Stat } from "../stat";
import { StatusDot } from "../status-dot";
import { fmtAge, fmtNum, fmtPct, fmtTime } from "@/lib/dashboard/format";
import { DNA_COLORS } from "@/lib/dashboard/colors";
import type { DNABlock } from "@/lib/dashboard/types";

const DNA_ACCENT: Record<DNABlock["id"], string> = {
  technical: DNA_COLORS.technical,
  options: DNA_COLORS.options,
  market: DNA_COLORS.market,
  narrative: DNA_COLORS.narrative,
  forecast: DNA_COLORS.forecast,
  trade: DNA_COLORS.trade,
  operations: DNA_COLORS.operations,
};

export function DNAMatrixPanel({ dna }: { dna: DNABlock[] }) {
  const [selected, setSelected] = useState<DNABlock["id"]>("technical");
  const selectedBlock = dna.find((d) => d.id === selected) ?? dna[0];
  const avgConf = dna.reduce((s, d) => s + d.confidence, 0) / Math.max(1, dna.length);
  const minConf = Math.min(...dna.map((d) => d.confidence));
  const maxConf = Math.max(...dna.map((d) => d.confidence));
  const avgFreshness = dna.reduce((s, d) => s + d.freshnessMs, 0) / Math.max(1, dna.length);

  return (
    <PanelGrid>
      {/* Confidence matrix — all 7 DNA blocks as cards */}
      <Panel
        title="7-DNA Confidence Matrix"
        subtitle="Live consensus across intelligence objects (Technical → Operations)"
        icon={<Beaker className="h-3.5 w-3.5" />}
        className="col-span-12"
        actions={
          <div className="flex items-center gap-3 text-[10.5px] font-mono">
            <span className="text-muted-foreground">avg <span style={{ color: avgConf > 0.75 ? "#34d399" : "#fbbf24" }}>{fmtPct(avgConf, 1)}</span></span>
            <span className="text-muted-foreground">range <span className="text-foreground">{fmtPct(minConf, 0)}—{fmtPct(maxConf, 0)}</span></span>
            <span className="text-muted-foreground">fresh <span className="text-foreground">{fmtNum(avgFreshness / 1000, 1)}s</span></span>
          </div>
        }
      >
        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
          {dna.map((d) => {
            const color = DNA_ACCENT[d.id];
            const isSelected = selected === d.id;
            return (
              <button
                key={d.id}
                onClick={() => setSelected(d.id)}
                className={`text-left rounded-md border p-3 transition-all ${isSelected ? "border-primary/60 bg-primary/5" : "border-border/50 bg-background/30 hover:border-border hover:bg-accent/30"}`}
                style={isSelected ? { boxShadow: `0 0 0 1px ${color}33` } : {}}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10.5px] font-semibold uppercase tracking-wider truncate" style={{ color }}>{d.name.replace(" DNA", "")}</span>
                  <StatusDot state={d.state} size="sm" />
                </div>
                <div className="text-[9.5px] font-mono text-muted-foreground/70 mb-2">Stage {d.stage} · {d.inputCount} inputs · {d.validatorCount} val</div>

                <div className="h-[44px] -mx-1 mb-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={d.history} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
                      <defs>
                        <linearGradient id={`dna-grad-${d.id}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={color} stopOpacity={0.5} />
                          <stop offset="100%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <YAxis hide domain={[0.2, 1]} />
                      <Area type="monotone" dataKey="confidence" stroke={color} strokeWidth={1.4} fill={`url(#dna-grad-${d.id})`} isAnimationActive={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                <div className="flex items-baseline justify-between">
                  <span className="text-[18px] font-mono tabular-nums font-bold" style={{ color }}>
                    {fmtPct(d.confidence, 1)}
                  </span>
                  <span className="text-[9.5px] font-mono text-muted-foreground">
                    {d.trend >= 0 ? "▲" : "▼"} {Math.abs(d.trend).toFixed(2)}
                  </span>
                </div>
                <div className="mt-1 text-[9px] font-mono text-muted-foreground/70 flex items-center gap-1">
                  <Clock className="h-2.5 w-2.5" />
                  serialized {fmtAge(Date.now() - d.lastSerialized)} · {d.serializationSizeKb.toFixed(1)}kb
                </div>
              </button>
            );
          })}
        </div>
      </Panel>

      {/* Selected DNA detail */}
      <Panel
        title={`${selectedBlock.name} — Detail`}
        subtitle={`Stage ${selectedBlock.stage} · ${selectedBlock.contributors.length} contributors · ${selectedBlock.validatorCount} validators`}
        icon={<Activity className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-8"
        actions={
          <span className="text-[10.5px] font-mono text-muted-foreground">
            confidence <span style={{ color: DNA_ACCENT[selectedBlock.id] }}>{fmtPct(selectedBlock.confidence, 2)}</span>
          </span>
        }
      >
        <div className="h-[200px] mb-3">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={selectedBlock.history} margin={{ top: 8, right: 12, bottom: 18, left: 0 }}>
              <defs>
                <linearGradient id="dna-detail-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={DNA_ACCENT[selectedBlock.id]} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={DNA_ACCENT[selectedBlock.id]} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="t"
                tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }}
                tickFormatter={(v) => fmtTime(v)}
                stroke="rgba(255,255,255,0.08)"
                interval={5}
              />
              <YAxis
                domain={[0.2, 1]}
                ticks={[0.25, 0.5, 0.75, 1]}
                tick={{ fill: "#94a3b8", fontSize: 9.5, fontFamily: "var(--font-geist-mono)" }}
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="rgba(255,255,255,0.08)"
                width={42}
              />
              <Tooltip
                contentStyle={{ background: "#131820", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 10.5, fontFamily: "var(--font-geist-mono)", color: "#e6edf3" }}
                labelFormatter={(_, p) => p[0]?.payload?.t ? fmtTime(p[0].payload.t) : ""}
                formatter={(v: number) => [fmtPct(v, 2), "confidence"]}
              />
              <ReferenceLine y={0.75} stroke="#34d399" strokeDasharray="3 3" strokeOpacity={0.4} />
              <ReferenceLine y={0.55} stroke="#fbbf24" strokeDasharray="3 3" strokeOpacity={0.4} />
              <Area type="monotone" dataKey="confidence" stroke={DNA_ACCENT[selectedBlock.id]} strokeWidth={2} fill="url(#dna-detail-grad)" isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="border-t border-border/40 pt-3">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2 flex items-center gap-2">
            <Layers className="h-3 w-3" /> Contributors
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
            {selectedBlock.contributors.map((c) => (
              <div key={c.name} className="flex items-center gap-2 rounded-md border border-border/40 bg-background/30 px-2.5 py-1.5">
                <StatusDot state={c.state} size="sm" pulse={c.state === "healthy"} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] truncate">{c.name}</span>
                    <span className="text-[9.5px] font-mono text-muted-foreground">w {(c.weight * 100).toFixed(0)}%</span>
                  </div>
                  <div className="mt-1 h-1 rounded-full bg-background/60 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${c.contribution * 100}%`,
                        backgroundColor: c.contribution > 0.7 ? "#34d399" : c.contribution > 0.5 ? "#fbbf24" : "#f87171",
                      }}
                    />
                  </div>
                </div>
                <span className="text-[10px] font-mono tabular-nums w-9 text-right" style={{ color: c.contribution > 0.7 ? "#34d399" : c.contribution > 0.5 ? "#fbbf24" : "#f87171" }}>
                  {fmtPct(c.contribution, 0)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Panel>

      {/* DNA quick stats */}
      <Panel
        title="DNA Health"
        subtitle="Cross-object summary"
        icon={<Beaker className="h-3.5 w-3.5" />}
        className="col-span-12 lg:col-span-4"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Avg Confidence" value={fmtPct(avgConf, 2)} intent={avgConf > 0.75 ? "healthy" : avgConf > 0.6 ? "warning" : "critical"} />
          <Stat label="Avg Freshness" value={fmtNum(avgFreshness / 1000, 1)} unit="s" intent="info" />
          <Stat label="Healthy" value={dna.filter((d) => d.state === "healthy").length} unit={`of ${dna.length}`} intent="healthy" />
          <Stat label="Below Threshold" value={dna.filter((d) => d.confidence < 0.6).length} intent={dna.filter((d) => d.confidence < 0.6).length > 0 ? "warning" : "healthy"} />
        </div>

        <div className="border-t border-border/40 pt-3">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Ranking (highest → lowest)</div>
          <div className="space-y-1">
            {dna.slice().sort((a, b) => b.confidence - a.confidence).map((d, i) => (
              <button
                key={d.id}
                onClick={() => setSelected(d.id)}
                className="w-full flex items-center gap-2 text-[10.5px] font-mono py-0.5 px-1.5 rounded hover:bg-accent/40"
              >
                <span className="text-muted-foreground/60 w-3 text-right">{i + 1}.</span>
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: DNA_ACCENT[d.id] }} />
                <span className="flex-1 text-left truncate text-muted-foreground">{d.name.replace(" DNA", "")}</span>
                <span style={{ color: DNA_ACCENT[d.id] }}>{fmtPct(d.confidence, 1)}</span>
              </button>
            ))}
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
