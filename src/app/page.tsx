"use client";

import { TrendingUp, FileText, Beaker, ShieldCheck, Activity, Layers, Newspaper, Cpu, ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";
import { ReportViewer } from "@/modules/trader-dashboard/components/reports/report-viewer";

/**
 * ATHENA-X Trader Terminal — Stage 16 entry point.
 *
 * The trader dashboard consumes only published reports from the Stage 15
 * Report Engine. It never reaches into the engineering console, never
 * imports internal-only components, and never directly queries the
 * canonical databases or DNA objects.
 *
 * Layout:
 *   - Top nav with primary sections (Overview / Watchlist / 0DTE Setups /
 *     Forecasts / Reports / Account)
 *   - Hero band showing platform status
 *   - Reports section as the live Stage 15 surface
 *   - Capabilities preview for upcoming sections
 */
export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      {/* Top nav */}
      <header className="border-b border-border bg-card/40 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/15 border border-primary/30">
              <TrendingUp className="h-4 w-4 text-primary" />
            </div>
            <div>
              <div className="text-[13px] font-semibold tracking-wide">ATHENA-X</div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Trader Terminal</div>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-[12px] text-muted-foreground">
            <Link href="/" className="hover:text-foreground transition-colors">Overview</Link>
            <Link href="/" className="hover:text-foreground transition-colors">Watchlist</Link>
            <Link href="/" className="hover:text-foreground transition-colors">0DTE Setups</Link>
            <Link href="/" className="hover:text-foreground transition-colors">Forecasts</Link>
            <Link href="/" className="text-foreground font-medium border-b-2 border-primary pb-0.5">Reports</Link>
          </nav>
          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
            <span className="hidden sm:inline px-2 py-0.5 rounded-full bg-status-healthy/10 border border-status-healthy/30 text-status-healthy font-mono">
              Stage 15 · Live
            </span>
          </div>
        </div>
      </header>

      {/* Hero band */}
      <section className="border-b border-border bg-gradient-to-br from-primary/5 via-background to-background">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-start justify-between gap-6 flex-wrap">
            <div className="flex-1 min-w-0">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[11px] font-mono text-primary mb-3">
                <Sparkles className="h-3 w-3" />
                Institutional Report Engine — Stage 15
              </div>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight leading-tight">
                Validated intelligence, <span className="text-primary">audit-ready reports</span>
              </h1>
              <p className="mt-3 text-muted-foreground text-[14px] leading-relaxed max-w-2xl">
                Every report is composed from validated canonical databases and the seven DNA intelligence objects.
                The engine performs no calculations — it only transforms upstream intelligence into clear, explainable,
                and auditable documents. Each report ships in Markdown, JSON, and PDF with full versioning.
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 min-w-[280px]">
              <CapabilityPill icon={<FileText className="h-3.5 w-3.5" />} label="6 Report Types" status="live" />
              <CapabilityPill icon={<Layers className="h-3.5 w-3.5" />} label="3 Formats" status="live" />
              <CapabilityPill icon={<ShieldCheck className="h-3.5 w-3.5" />} label="Audit Trail" status="live" />
              <CapabilityPill icon={<Beaker className="h-3.5 w-3.5" />} label="Templates" status="live" />
              <CapabilityPill icon={<Activity className="h-3.5 w-3.5" />} label="Event Bus" status="live" />
              <CapabilityPill icon={<Newspaper className="h-3.5 w-3.5" />} label="Explainability" status="live" />
              <CapabilityPill icon={<Cpu className="h-3.5 w-3.5" />} label="DNA Snapshots" status="live" />
              <CapabilityPill icon={<TrendingUp className="h-3.5 w-3.5" />} label="Deterministic" status="live" />
            </div>
          </div>
        </div>
      </section>

      {/* Main report viewer */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6">
        <ReportViewer />
      </main>

      {/* Architecture boundary callout */}
      <section className="border-t border-border bg-card/30">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="rounded-xl border border-border bg-card/40 p-5">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-primary/10 border border-primary/20 p-3 shrink-0">
                <ShieldCheck className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="text-[14px] font-semibold mb-1">Read-only by design</h3>
                <p className="text-[12.5px] text-muted-foreground leading-relaxed">
                  The Report Engine never calculates indicators, forecasts, probabilities, or trading signals.
                  It only reads from validated canonical databases and the seven DNA objects, transforming them
                  into reports. Every value in every report can be traced back to its source — see the audit
                  trail at the bottom of any selected report.
                </p>
                <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px] font-mono">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">Markdown output</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">JSON output</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">PDF output</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">SHA-256 hash</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">DNA version stamp</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">Event bus publish</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">Modular templates</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                    <span className="text-muted-foreground">Deterministic</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card/30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-[11px] text-muted-foreground">
          <div className="font-mono">ATHENA-X · Trader Terminal · Stage 15</div>
          <div className="font-mono">build athx-15.0.0 · report engine v15.0.0</div>
        </div>
      </footer>
    </div>
  );
}

function CapabilityPill({ icon, label, status }: { icon: React.ReactNode; label: string; status: "live" | "active" | "pending" }) {
  const color = status === "live" ? "#34d399" : status === "active" ? "#22d3ee" : "#6b7280";
  return (
    <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-border bg-background/40">
      <span style={{ color }}>{icon}</span>
      <span className="text-foreground/90 text-[11px]">{label}</span>
      <span className="ml-auto text-[9px] font-mono uppercase tracking-wider" style={{ color }}>
        {status}
      </span>
    </div>
  );
}
