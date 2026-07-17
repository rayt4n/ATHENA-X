"use client";

import { ArrowRight, Beaker, ShieldCheck, TrendingUp, Newspaper, Layers, Cpu, Sparkles } from "lucide-react";
import Link from "next/link";

/**
 * ATHENA-X Trader Dashboard — Stage 16 (placeholder)
 *
 * This is the trader-facing entry point. It is intentionally minimal today
 * because the platform is still in Phase A (Intelligence Validation).
 *
 * The real Stage 16 trader UI will be built on top of the validated
 * intelligence layer and will pull from the same backend event bus and
 * canonical databases as the internal engineering console — but with a
 * completely separate navigation, layout, permissions, and visual language.
 *
 * The internal engineering console (Phase A validation cockpit) lives at
 * /engineering-console and is for developers, QA, DevOps, AI engineers,
 * and system administrators only. There is NO link to it from this
 * trader-facing surface — internal users reach it via direct URL.
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
            <Link href="/" className="text-foreground font-medium">Overview</Link>
            <Link href="/" className="hover:text-foreground transition-colors">Watchlist</Link>
            <Link href="/" className="hover:text-foreground transition-colors">0DTE Setups</Link>
            <Link href="/" className="hover:text-foreground transition-colors">Forecasts</Link>
            <Link href="/" className="hover:text-foreground transition-colors">Reports</Link>
          </nav>
          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
            <span className="hidden sm:inline px-2 py-0.5 rounded-full bg-status-warning/10 border border-status-warning/30 text-status-warning font-mono">
              Phase A · Validation
            </span>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-12">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[11px] font-mono text-primary mb-4">
              <Sparkles className="h-3 w-3" />
              Stage 16 · Coming after Phase A validation
            </div>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight leading-tight">
              The institutional intelligence terminal for <span className="text-primary">SPY / ES / SPX 0DTE</span>
            </h1>
            <p className="mt-4 text-muted-foreground text-[15px] leading-relaxed max-w-xl">
              ATHENA-X fuses technical analysis, options positioning, cross-asset market structure, narrative
              intelligence, and probabilistic forecasting into a single decision surface — purpose-built for
              same-day options traders who need conviction before they pull the trigger.
            </p>
            <p className="mt-3 text-muted-foreground text-[13px] leading-relaxed max-w-xl">
              The trader dashboard is intentionally not yet live. We are validating the underlying intelligence
              layer through an internal engineering cockpit before exposing any signal to live trading decisions.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href="#capabilities"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-primary text-primary-foreground text-[12px] font-medium hover:bg-primary/90 transition-colors"
              >
                View capabilities <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <span className="text-[11px] text-muted-foreground font-mono">
                Backend event bus · 7 DNA objects · 172 plugins
              </span>
            </div>
          </div>

          <div className="relative">
            <div className="rounded-xl border border-border bg-card/60 backdrop-blur-sm p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Platform Status</div>
                  <div className="text-[18px] font-semibold mt-0.5">Phase A — Intelligence Validation</div>
                </div>
                <span className="px-2 py-1 rounded-md bg-status-warning/15 border border-status-warning/30 text-[10px] font-mono font-semibold text-status-warning">
                  IN PROGRESS
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-[12px]">
                <CapabilityPill icon={<Beaker className="h-3.5 w-3.5" />} label="Engineering Console" status="live" />
                <CapabilityPill icon={<Layers className="h-3.5 w-3.5" />} label="172 Plugins" status="active" />
                <CapabilityPill icon={<Cpu className="h-3.5 w-3.5" />} label="47 AI Agents" status="active" />
                <CapabilityPill icon={<ShieldCheck className="h-3.5 w-3.5" />} label="7 DNA Objects" status="active" />
                <CapabilityPill icon={<TrendingUp className="h-3.5 w-3.5" />} label="Trader Dashboard" status="pending" />
                <CapabilityPill icon={<Newspaper className="h-3.5 w-3.5" />} label="Report Engine" status="pending" />
              </div>

              <div className="mt-5 pt-4 border-t border-border">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2">Validation Progress</div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-primary/60 to-primary" style={{ width: "70%" }} />
                </div>
                <div className="flex items-center justify-between mt-1.5 text-[10px] font-mono text-muted-foreground">
                  <span>Phase A · 14 of 14 stages engineered</span>
                  <span>~70% validated</span>
                </div>
              </div>
            </div>

            <div className="absolute -z-10 -inset-4 bg-primary/5 blur-3xl rounded-full" />
          </div>
        </div>

        {/* Capabilities grid */}
        <section id="capabilities" className="mt-20">
          <div className="text-center mb-10">
            <div className="text-[11px] uppercase tracking-wider text-primary font-mono">Capabilities</div>
            <h2 className="text-2xl md:text-3xl font-bold mt-2">What the trader terminal will expose</h2>
            <p className="text-muted-foreground text-[14px] mt-2 max-w-2xl mx-auto">
              Once the underlying intelligence passes validation, the trader surface will deliver these
              capabilities — without ever exposing the internal engineering UI.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <FeatureCard
              icon={<TrendingUp className="h-5 w-5" />}
              title="0DTE Trade Setups"
              description="Live-qualified trade opportunities with entry, stop, target, R/R, and confidence — each backed by 5 DNA input contributions."
            />
            <FeatureCard
              icon={<Layers className="h-5 w-5" />}
              title="Options Intelligence"
              description="Real-time GEX, dealer positioning, IV rank, unusual flow, and 0DTE-specific gamma exposure with put/call walls."
            />
            <FeatureCard
              icon={<Cpu className="h-5 w-5" />}
              title="Probabilistic Forecasts"
              description="Ensemble of 9 forecast models with calibrated confidence intervals and directional hit-rate tracking."
            />
            <FeatureCard
              icon={<Newspaper className="h-5 w-5" />}
              title="Narrative Radar"
              description="Event classification, market-impact scoring, and catalyst timeline — so you know what's moving the tape and why."
            />
            <FeatureCard
              icon={<ShieldCheck className="h-5 w-5" />}
              title="Risk Governance"
              description="Every setup passes through qualification, timing, risk, and checklist engines before reaching your screen."
            />
            <FeatureCard
              icon={<Beaker className="h-5 w-5" />}
              title="Self-Validating Intelligence"
              description="The platform continuously self-audits its own forecasts and DNA confidence — degraded signal is suppressed, not surfaced."
            />
          </div>
        </section>

        {/* Architecture boundary callout */}
        <section className="mt-16 rounded-xl border border-border bg-card/40 p-6">
          <div className="flex items-start gap-4">
            <div className="rounded-lg bg-primary/10 border border-primary/20 p-3 shrink-0">
              <ShieldCheck className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="text-[15px] font-semibold">Architecture boundary</h3>
              <p className="mt-1.5 text-[13px] text-muted-foreground leading-relaxed">
                The trader dashboard and the internal engineering console share the same backend event bus
                and canonical databases, but have completely separate frontend routing, layouts, navigation,
                permissions, and UI components. The trader surface has zero dependency on internal-only
                components and never links to them.
              </p>
              <p className="mt-2 text-[12px] text-muted-foreground/80 font-mono">
                Internal users (developers, QA, DevOps, AI engineers, system administrators) access the
                engineering console via a separate, non-public URL.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card/30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-[11px] text-muted-foreground">
          <div className="font-mono">ATHENA-X · Stage 16 placeholder</div>
          <div className="font-mono">build athx-14.2.0 · Phase A</div>
        </div>
      </footer>
    </div>
  );
}

function CapabilityPill({ icon, label, status }: { icon: React.ReactNode; label: string; status: "live" | "active" | "pending" }) {
  const color =
    status === "live" ? "var(--status-healthy)" :
    status === "active" ? "var(--status-info)" :
    "var(--muted-foreground)";
  return (
    <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-border bg-background/40">
      <span style={{ color }}>{icon}</span>
      <span className="text-foreground/90">{label}</span>
      <span className="ml-auto text-[9.5px] font-mono uppercase tracking-wider" style={{ color }}>
        {status}
      </span>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="rounded-lg border border-border bg-card/40 p-5 hover:border-primary/30 hover:bg-card/60 transition-colors">
      <div className="w-9 h-9 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-3">
        {icon}
      </div>
      <h3 className="text-[14px] font-semibold">{title}</h3>
      <p className="mt-1.5 text-[12.5px] text-muted-foreground leading-relaxed">{description}</p>
    </div>
  );
}
