"use client";

import { useState } from "react";
import { Activity, Play, CheckCircle2, AlertTriangle, Clock } from "lucide-react";
import { useProviders } from "../hooks/use-providers";

interface DiagnosticResult {
  raw: unknown;
  normalized: unknown[];
  validCount: number;
  invalidCount: number;
  errors: string[];
  responseTimeMs: number;
  provider: string;
  symbol: string;
  category: string;
}

export function ProviderDiagnostics() {
  const { providers } = useProviders();
  const [symbol, setSymbol] = useState("SPY");
  const [providerId, setProviderId] = useState("yahoo");
  const [category, setCategory] = useState("quotes");
  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runDiagnostics = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/providers/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ providerId, symbol, category }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({
        raw: null, normalized: [], validCount: 0, invalidCount: 0,
        errors: [`Request failed: ${err}`], responseTimeMs: 0,
        provider: providerId, symbol, category,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border bg-card/40 p-4">
        <h2 className="text-[13px] font-semibold uppercase tracking-wide mb-3">Provider Diagnostics</h2>
        <p className="text-[11px] text-muted-foreground mb-4">
          Fetch raw data from a provider and trace it through: Raw JSON → Normalized → Validation → Final MarketData.
          This saves hours of debugging when connecting new providers.
        </p>

        <div className="flex items-center gap-2 mb-4">
          <select value={providerId} onChange={(e) => setProviderId(e.target.value)}
            className="bg-background/60 border border-border/40 rounded px-2 py-1 text-[11px] font-mono focus:outline-none focus:border-primary/50">
            {providers.filter((p) => p.id !== "cache").map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="SPY"
            className="w-20 bg-background/60 border border-border/40 rounded px-2 py-1 text-[11px] font-mono focus:outline-none focus:border-primary/50" />
          <select value={category} onChange={(e) => setCategory(e.target.value)}
            className="bg-background/60 border border-border/40 rounded px-2 py-1 text-[11px] font-mono focus:outline-none focus:border-primary/50">
            <option value="quotes">quotes</option>
            <option value="historical">historical</option>
          </select>
          <button onClick={runDiagnostics} disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-primary text-primary-foreground text-[11px] font-medium hover:bg-primary/90 disabled:opacity-50">
            <Play className="h-3 w-3" />
            {loading ? "Running…" : "Run Diagnostics"}
          </button>
        </div>

        {result && (
          <div className="space-y-4">
            {/* Pipeline summary */}
            <div className="grid grid-cols-4 gap-2">
              <PipelineStep label="Fetch" status={result.raw ? "pass" : "fail"} detail={result.responseTimeMs > 0 ? `${result.responseTimeMs}ms` : "—"} />
              <PipelineStep label="Normalize" status={result.normalized.length > 0 ? "pass" : "fail"} detail={`${result.normalized.length} bars`} />
              <PipelineStep label="Validate" status={result.invalidCount === 0 ? "pass" : "warn"} detail={`${result.validCount} valid / ${result.invalidCount} invalid`} />
              <PipelineStep label="Final" status={result.validCount > 0 ? "pass" : "fail"} detail={`${result.validCount} MarketData`} />
            </div>

            {/* Errors */}
            {result.errors.length > 0 && (
              <div className="rounded-md border border-status-critical/30 bg-status-critical/5 p-3">
                <div className="flex items-center gap-2 mb-1">
                  <AlertTriangle className="h-3.5 w-3.5 text-status-critical" />
                  <span className="text-[11px] font-semibold text-status-critical">Errors</span>
                </div>
                {result.errors.map((err, i) => (
                  <div key={i} className="text-[10px] font-mono text-muted-foreground">• {err}</div>
                ))}
              </div>
            )}

            {/* Raw JSON */}
            {result.raw && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70 mb-1">Raw JSON (from provider)</div>
                <pre className="text-[9px] font-mono bg-background/40 border border-border/40 rounded p-2 max-h-48 overflow-auto scroll-thin text-muted-foreground">
{JSON.stringify(result.raw, null, 2).slice(0, 3000)}
                </pre>
              </div>
            )}

            {/* Normalized MarketData */}
            {result.normalized.length > 0 && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70 mb-1">Normalized MarketData (final output)</div>
                <pre className="text-[9px] font-mono bg-background/40 border border-border/40 rounded p-2 max-h-48 overflow-auto scroll-thin text-muted-foreground">
{JSON.stringify(result.normalized.slice(0, 5), null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function PipelineStep({ label, status, detail }: { label: string; status: "pass" | "fail" | "warn"; detail: string }) {
  const color = status === "pass" ? "#34d399" : status === "warn" ? "#fbbf24" : "#f87171";
  return (
    <div className="rounded-md border p-2 text-center" style={{ borderColor: `${color}33`, backgroundColor: `${color}08` }}>
      <div className="flex items-center justify-center gap-1 mb-0.5">
        {status === "pass" ? <CheckCircle2 className="h-3 w-3" style={{ color }} /> : <AlertTriangle className="h-3 w-3" style={{ color }} />}
        <span className="text-[10px] font-medium" style={{ color }}>{label}</span>
      </div>
      <div className="text-[9px] font-mono text-muted-foreground">{detail}</div>
    </div>
  );
}
