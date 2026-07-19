"use client";

import { useState } from "react";
import { Activity, Database, Radio, Wifi, WifiOff, Clock, Zap, RotateCcw, Key, ChevronUp, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ProviderConfig, ProviderMode, HealthSnapshot } from "../lib/types";
import { useProviders } from "../hooks/use-providers";

const HEALTH_COLORS: Record<string, string> = {
  connected: "#34d399",
  disconnected: "#f87171",
  degraded: "#fbbf24",
  warming: "#22d3ee",
};

export function ProviderSettings() {
  const { providers, mode, healthSnapshots, changeMode, toggleProvider, updateApiKey, reorder, reset } = useProviders();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [keyValue, setKeyValue] = useState("");

  const moveProvider = (id: string, direction: "up" | "down") => {
    const enabled = providers.filter((p) => p.enabled && p.id !== "cache");
    const idx = enabled.findIndex((p) => p.id === id);
    if (idx < 0) return;
    const swapIdx = direction === "up" ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= enabled.length) return;
    const newOrder = enabled.map((p) => p.id);
    [newOrder[idx], newOrder[swapIdx]] = [newOrder[swapIdx], newOrder[idx]];
    reorder([...newOrder, "cache"]);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card/40 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Radio className="h-5 w-5 text-primary" />
            <div>
              <div className="text-[14px] font-semibold">Provider Orchestrator</div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Stage 16A · Market Data Gateway</div>
            </div>
          </div>
          <button onClick={reset} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[11px] font-mono text-muted-foreground hover:text-foreground transition-colors">
            <RotateCcw className="h-3 w-3" /> Reset
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* Mode Selector */}
        <section className="rounded-lg border border-border bg-card/40 p-4">
          <h2 className="text-[13px] font-semibold uppercase tracking-wide mb-3">Provider Mode</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <ModeCard mode="free" currentMode={mode} onSelect={changeMode}
              title="Free Mode" description="Zero-cost operation. Preconfigured provider stack. User cannot edit providers." />
            <ModeCard mode="custom" currentMode={mode} onSelect={changeMode}
              title="Custom Mode" description="Customize Tier 1 providers. Enable, disable, and reorder. Only supported providers." />
            <ModeCard mode="advanced" currentMode={mode} onSelect={changeMode}
              title="Advanced Mode" description="Professional configuration. Full provider routing per data category. Create custom stacks." />
          </div>
        </section>

        {/* Provider Stack */}
        <section className="rounded-lg border border-border bg-card/40 overflow-hidden">
          <div className="px-4 py-2 border-b border-border/60 bg-card/60 flex items-center justify-between">
            <h2 className="text-[13px] font-semibold uppercase tracking-wide">Provider Stack</h2>
            <span className="text-[10px] font-mono text-muted-foreground">
              {providers.filter((p) => p.enabled).length} enabled · {providers.length} total
            </span>
          </div>

          {/* Header row */}
          <div className="grid grid-cols-12 px-4 py-1.5 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-1">Priority</div>
            <div className="col-span-3">Provider</div>
            <div className="col-span-2">Type</div>
            <div className="col-span-2 text-right">Health</div>
            <div className="col-span-2 text-right">Latency</div>
            <div className="col-span-1 text-right">Success</div>
            <div className="col-span-1 text-right">Actions</div>
          </div>

          {providers
            .sort((a, b) => a.priority - b.priority)
            .map((provider) => {
              const health = healthSnapshots.find((h) => h.providerId === provider.id);
              const canEdit = mode !== "free" || provider.id === "cache";
              return (
                <div key={provider.id} className={cn("grid grid-cols-12 px-4 py-2 text-[11px] items-center border-b border-border/20", !provider.enabled && "opacity-50")}>
                  <div className="col-span-1 font-mono">{provider.priority === 99 ? "—" : provider.priority}</div>
                  <div className="col-span-3">
                    <div className="font-medium">{provider.name}</div>
                    {provider.apiKeyRequired && (
                      <button
                        onClick={() => { setEditingKey(editingKey === provider.id ? null : provider.id); setKeyValue(provider.apiKey ?? ""); }}
                        className="text-[9px] text-primary hover:underline flex items-center gap-1 mt-0.5"
                      >
                        <Key className="h-2.5 w-2.5" />
                        {provider.apiKey ? "Key set" : "Set API key"}
                      </button>
                    )}
                    {editingKey === provider.id && (
                      <div className="mt-1 flex gap-1">
                        <input
                          type="password"
                          value={keyValue}
                          onChange={(e) => setKeyValue(e.target.value)}
                          placeholder="API key…"
                          className="flex-1 bg-background/60 border border-border/40 rounded px-1.5 py-0.5 text-[10px] font-mono focus:outline-none focus:border-primary/50"
                        />
                        <button
                          onClick={() => { updateApiKey(provider.id, keyValue); setEditingKey(null); }}
                          className="px-2 py-0.5 rounded bg-primary text-primary-foreground text-[9px]"
                        >
                          Save
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground uppercase">{provider.type}</div>
                  <div className="col-span-2 flex items-center justify-end gap-1.5">
                    <span className="w-2 h-2 rounded-full pulse-live" style={{ backgroundColor: HEALTH_COLORS[health?.state ?? "disconnected"] }} />
                    <span className="text-[9.5px] font-mono uppercase" style={{ color: HEALTH_COLORS[health?.state ?? "disconnected"] }}>
                      {health?.state ?? "disconnected"}
                    </span>
                  </div>
                  <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">
                    {health && health.latencyMs > 0 ? `${health.latencyMs}ms` : "—"}
                  </div>
                  <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: health && health.successRate > 0.9 ? "#34d399" : health && health.successRate > 0.5 ? "#fbbf24" : "#94a3b8" }}>
                    {health && health.totalRequests > 0 ? `${(health.successRate * 100).toFixed(0)}%` : "—"}
                  </div>
                  <div className="col-span-1 flex items-center justify-end gap-0.5">
                    {mode === "custom" && provider.id !== "cache" && (
                      <>
                        <button onClick={() => moveProvider(provider.id, "up")} className="p-0.5 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground">
                          <ChevronUp className="h-3 w-3" />
                        </button>
                        <button onClick={() => moveProvider(provider.id, "down")} className="p-0.5 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground">
                          <ChevronDown className="h-3 w-3" />
                        </button>
                      </>
                    )}
                    {canEdit && (
                      <button
                        onClick={() => toggleProvider(provider.id)}
                        className={cn("p-0.5 rounded text-[9px] font-mono", provider.enabled ? "text-status-healthy" : "text-muted-foreground")}
                        title={provider.enabled ? "Disable" : "Enable"}
                      >
                        {provider.enabled ? "ON" : "OFF"}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
        </section>

        {/* Supported Endpoints */}
        <section className="rounded-lg border border-border bg-card/40 p-4">
          <h2 className="text-[13px] font-semibold uppercase tracking-wide mb-3">Endpoint Coverage Matrix</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-[10.5px]">
              <thead>
                <tr className="text-muted-foreground/70 uppercase tracking-wider text-[8.5px]">
                  <th className="text-left px-2 py-1">Provider</th>
                  <th className="text-center px-2 py-1">Quotes</th>
                  <th className="text-center px-2 py-1">Historical</th>
                  <th className="text-center px-2 py-1">News</th>
                  <th className="text-center px-2 py-1">Macro</th>
                  <th className="text-center px-2 py-1">Company</th>
                </tr>
              </thead>
              <tbody>
                {providers.filter((p) => p.id !== "cache").map((p) => (
                  <tr key={p.id} className="border-t border-border/20">
                    <td className="px-2 py-1 font-medium">{p.name}</td>
                    <td className="text-center px-2 py-1">{hasEndpoint(p, "quotes") ? <span className="text-status-healthy">✓</span> : <span className="text-muted-foreground/30">—</span>}</td>
                    <td className="text-center px-2 py-1">{hasEndpoint(p, "historical") ? <span className="text-status-healthy">✓</span> : <span className="text-muted-foreground/30">—</span>}</td>
                    <td className="text-center px-2 py-1">{hasEndpoint(p, "news") ? <span className="text-status-healthy">✓</span> : <span className="text-muted-foreground/30">—</span>}</td>
                    <td className="text-center px-2 py-1">{hasEndpoint(p, "macro") ? <span className="text-status-healthy">✓</span> : <span className="text-muted-foreground/30">—</span>}</td>
                    <td className="text-center px-2 py-1">{hasEndpoint(p, "company") ? <span className="text-status-healthy">✓</span> : <span className="text-muted-foreground/30">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Footer note */}
        <section className="rounded-md border border-status-info/30 bg-status-info/5 p-3">
          <div className="flex items-start gap-2">
            <Zap className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
            <div className="text-[11px] text-muted-foreground leading-relaxed">
              <strong className="text-foreground">Phase 1 (Framework):</strong> Provider Orchestrator framework is built with smart routing, health monitoring, caching, and normalization.
              No live providers are connected yet — the Mock Provider generates test data for framework validation.
              <br /><br />
              <strong className="text-foreground">Phase 2 (Live Data):</strong> Yahoo Finance will be connected first, followed by Finnhub, Twelve Data, and FMP.
              Each provider adapter extends <code className="text-primary">BaseProvider</code> and implements <code className="text-primary">fetch()</code> + <code className="text-primary">normalize()</code>.
              The rest of ATHENA-X remains completely unaware of which provider supplied the data.
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function hasEndpoint(provider: ProviderConfig, category: string): boolean {
  return provider.supportedEndpoints.some((ep) => ep.category === category);
}

function ModeCard({ mode, currentMode, onSelect, title, description }: {
  mode: ProviderMode;
  currentMode: ProviderMode;
  onSelect: (mode: ProviderMode) => void;
  title: string;
  description: string;
}) {
  const isActive = currentMode === mode;
  return (
    <button
      onClick={() => onSelect(mode)}
      className={cn(
        "text-left rounded-md border p-3 transition-all",
        isActive ? "border-primary/60 bg-primary/5" : "border-border/50 bg-background/30 hover:bg-accent/30"
      )}
      style={isActive ? { boxShadow: "0 0 0 1px rgba(34,211,238,0.2)" } : {}}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-[12px] font-semibold">{title}</span>
        <span className={cn("w-3 h-3 rounded-full border-2", isActive ? "border-primary bg-primary" : "border-muted-foreground/40")} />
      </div>
      <div className="text-[10px] text-muted-foreground leading-snug">{description}</div>
    </button>
  );
}
