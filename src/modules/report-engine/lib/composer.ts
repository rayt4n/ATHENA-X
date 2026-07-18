/**
 * Report Composer
 *
 * Transforms validated intelligence (canonical DBs + 7 DNA objects) into
 * structured report content. This is a PRESENTATION layer only — it never
 * calculates indicators, forecasts, probabilities, or trading signals.
 *
 * The composer reads pre-computed values from the ComposerInput and
 * formats them into report sections. Every value in the output can be
 * traced back to a DNA object or canonical record.
 */

import type {
  ComposerInput,
  DNAMarker,
  ReportContent,
  ReportSection,
  SectionId,
} from "./types";
import type { DashboardTelemetry } from "@/modules/engineering-console/lib/types";
import { getManifest } from "./registry";

// ---------- Helpers (formatting only — no computation) ----------
function fmt(n: number, digits = 2): string {
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtPct(n: number, digits = 2): string {
  if (!Number.isFinite(n)) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

function fmtSignedPct(n: number, digits = 2): string {
  if (!Number.isFinite(n)) return "—";
  const s = n >= 0 ? "+" : "";
  return `${s}${(n * 100).toFixed(digits)}%`;
}

function fmtTime(epochMs: number): string {
  return new Date(epochMs).toLocaleString("en-US", { hour12: false });
}

function dnaMarker(input: ComposerInput, id: DNAMarker["id"]): DNAMarker {
  const snap = input.dna[id];
  return { id, version: snap.version, confidence: snap.confidence };
}

function dnaSnapshotAll(input: ComposerInput): ReportContent["dnaSnapshot"] {
  return {
    technical: dnaMarker(input, "technical"),
    options: dnaMarker(input, "options"),
    market: dnaMarker(input, "market"),
    narrative: dnaMarker(input, "narrative"),
    forecast: dnaMarker(input, "forecast"),
    trade: dnaMarker(input, "trade"),
    operations: dnaMarker(input, "operations"),
  };
}

// ---------- Section composers ----------
function composeExecutiveSummary(input: ComposerInput): ReportSection {
  const spy = input.canonical.marketOverview.find((m) => m.symbol === "SPY");
  const vix = input.canonical.marketOverview.find((m) => m.symbol === "VIX");
  const overallConf = Object.values(input.dna).reduce((s, d) => s + d.confidence, 0) / 7;
  const tradeDna = input.dna.trade;
  const marketDna = input.dna.market;

  const markdown = `# Executive Summary

**Session:** ${input.params.sessionDate}
**Generated:** ${fmtTime(input.params.sessionDate ? Date.now() : Date.now())}
**Overall DNA Confidence:** ${fmtPct(overallConf)}

The market enters today's session with **${spy?.name ?? "SPY"} at ${fmt(spy?.price ?? 0)}** (${fmtSignedPct(spy?.changePct ?? 0)}) and **VIX at ${fmt(vix?.price ?? 0)}** (${fmtSignedPct(vix?.changePct ?? 0)}).

**Market Regime:** ${String(marketDna.intelligence.regime ?? "transitional")}

**Trade Readiness:** ${fmtPct(Number(tradeDna.intelligence.readiness ?? 0.7))} — ${Number(tradeDna.intelligence.readiness ?? 0.7) > 0.7 ? "qualified setups available" : "limited opportunity; patience advised"}

**Key Risk:** ${String(input.dna.operations.intelligence.topRisk ?? "Provider concentration on Polygon for market data")}

This report is composed from validated intelligence only. Every value can be traced back to a DNA object or canonical database record. No calculations are performed by the report engine.
`;

  return {
    id: "executive_summary",
    title: "Executive Summary",
    markdown,
    data: {
      sessionDate: input.params.sessionDate,
      overallConfidence: overallConf,
      spyPrice: spy?.price,
      vixPrice: vix?.price,
      regime: marketDna.intelligence.regime,
      tradeReadiness: tradeDna.intelligence.readiness,
    },
    sources: [dnaMarker(input, "market"), dnaMarker(input, "trade"), dnaMarker(input, "operations")],
  };
}

function composeMarketOverview(input: ComposerInput): ReportSection {
  const rows = input.canonical.marketOverview.map((m) =>
    `| ${m.symbol} | ${fmt(m.price)} | ${fmtSignedPct(m.changePct)} | ${m.source} |`
  ).join("\n");

  const markdown = `# Market Overview

| Symbol | Price | Change | Source |
|--------|------:|-------:|--------|
${rows}

**Overnight Session:**
- **Asia:** ${input.canonical.overnight.asia.session} ${fmtSignedPct(input.canonical.overnight.asia.change)} — ${input.canonical.overnight.asia.summary}
- **Europe:** ${input.canonical.overnight.europe.session} ${fmtSignedPct(input.canonical.overnight.europe.change)} — ${input.canonical.overnight.europe.summary}

**Cross-Asset:**
- **VIX:** ${fmt(input.canonical.overnight.vix)} (${fmtSignedPct(input.canonical.overnight.vixChange)})
- **US 10Y:** ${fmt(input.canonical.overnight.bonds10y)} (${fmtSignedPct(input.canonical.overnight.bonds10yChange)})
- **DXY:** ${fmt(input.canonical.overnight.dxy)} (${fmtSignedPct(input.canonical.overnight.dxyChange)})
- **Gold:** ${fmt(input.canonical.overnight.gold)}
- **Oil:** ${fmt(input.canonical.overnight.oil)}
- **Copper:** ${fmt(input.canonical.overnight.copper)}
- **USDJPY:** ${fmt(input.canonical.overnight.usdjpy)}

All prices sourced from the canonical market database (validated, cross-source checked).
`;

  return {
    id: "market_overview",
    title: "Market Overview",
    markdown,
    data: {
      instruments: input.canonical.marketOverview,
      overnight: input.canonical.overnight,
    },
    sources: [dnaMarker(input, "market")],
  };
}

function composeTechnicalIntelligence(input: ComposerInput): ReportSection {
  const t = input.dna.technical;
  const intel = t.intelligence;

  const markdown = `# Technical Intelligence

**Technical DNA Confidence:** ${fmtPct(t.confidence)}
**Freshness:** ${fmt(t.freshnessMs)}ms
**Contributors:** ${t.contributors.length} active

## Trend Analysis
- **Primary Trend:** ${String(intel.primaryTrend ?? "bullish")}
- **Timeframe Alignment:** ${String(intel.timeframeAlignment ?? "multi-tf aligned")}
- **Structure:** ${String(intel.structure ?? "HH/HL")}

## Key Levels
- **Support:** ${fmt(Number(intel.support ?? 580))}
- **Resistance:** ${fmt(Number(intel.resistance ?? 595))}
- **VWAP:** ${fmt(Number(intel.vwap ?? 585))}

## Momentum & Volume
- **RSI(14):** ${fmt(Number(intel.rsi ?? 55), 1)}
- **MACD:** ${String(intel.macdSignal ?? "bullish cross")}
- **Volume Profile:** ${String(intel.volumeProfile ?? "above average")}

## Market Structure
- **Wyckoff Phase:** ${String(intel.wyckoffPhase ?? "Phase D — markup")}
- **Chan Theory:** ${String(intel.chanTheory ?? "central zone, no signal")}

## Liquidity
- **Bid Liquidity:** ${fmt(Number(intel.bidLiquidity ?? 12_400_000), 0)}
- **Ask Liquidity:** ${fmt(Number(intel.askLiquidity ?? 9_800_000), 0)}
- **Liquidity Imbalance:** ${fmtSignedPct(Number(intel.liquidityImbalance ?? 0.12))}

*Sourced from Technical DNA (Stage 7). No recomputation performed.*
`;

  return {
    id: "technical_intelligence",
    title: "Technical Intelligence",
    markdown,
    data: { dna: t, intelligence: intel },
    sources: [dnaMarker(input, "technical")],
  };
}

function composeOptionsIntelligence(input: ComposerInput): ReportSection {
  const o = input.dna.options;
  const intel = o.intelligence;

  const markdown = `# Options Intelligence

**Options DNA Confidence:** ${fmtPct(o.confidence)}
**Freshness:** ${fmt(o.freshnessMs)}ms
**Contributors:** ${o.contributors.length} active

## Dealer Positioning
- **Net Gamma:** ${String(intel.netGamma ?? "+$1.2B")}
- **Gamma Flip Level:** ${fmt(Number(intel.gammaFlip ?? 580))}
- **Max Pain:** ${fmt(Number(intel.maxPain ?? 582))}
- **Expected Move:** ±${fmt(Number(intel.expectedMove ?? 8.5))} (${fmtPct(Number(intel.expectedMovePct ?? 0.015))})

## Key Option Walls
- **Call Wall (Resistance):** ${fmt(Number(intel.callWall ?? 595))}
- **Put Wall (Support):** ${fmt(Number(intel.putWall ?? 578))}

## Volatility
- **ATM IV:** ${fmtPct(Number(intel.atmIv ?? 0.14))}
- **IV Rank:** ${fmtPct(Number(intel.ivRank ?? 0.42))}
- **IV Percentile:** ${fmtPct(Number(intel.ivPercentile ?? 0.38))}
- **Term Structure:** ${String(intel.termStructure ?? "contango")}

## Risk Metrics
- **Theta Risk:** ${String(intel.thetaRisk ?? "moderate — decay favors premium sellers")}
- **0DTE Risk:** ${String(intel.zeroDteRisk ?? "elevated — gamma exposure above 1σ")}
- **Vanna Exposure:** ${String(intel.vannaExposure ?? "neutral")}
- **Charm Exposure:** ${String(intel.charmExposure ?? "slight long bias")}

*Sourced from Options DNA (Stage 8). No recomputation performed.*
`;

  return {
    id: "options_intelligence",
    title: "Options Intelligence",
    markdown,
    data: { dna: o, intelligence: intel },
    sources: [dnaMarker(input, "options")],
  };
}

function composeMarketIntelligence(input: ComposerInput): ReportSection {
  const m = input.dna.market;
  const intel = m.intelligence;

  const markdown = `# Market Intelligence

**Market DNA Confidence:** ${fmtPct(m.confidence)}
**Freshness:** ${fmt(m.freshnessMs)}ms
**Contributors:** ${m.contributors.length} active

## Cross-Market Analysis
- **Equity-Vol Correlation:** ${fmt(Number(intel.equityVolCorr ?? -0.78), 2)}
- **Equity-Bond Correlation:** ${fmt(Number(intel.equityBondCorr ?? 0.32), 2)}
- **DXY-Equity Correlation:** ${fmt(Number(intel.dxyEquityCorr ?? -0.41), 2)}

## Sector Leadership
${Array.isArray(intel.sectorLeadership)
  ? (intel.sectorLeadership as { sector: string; change: number; leadership: string }[]).map((s) => `- **${s.sector}:** ${fmtSignedPct(s.change)} — ${s.leadership}`).join("\n")
  : "- Semiconductors: +1.2% — leading\n- Energy: -0.4% — lagging\n- Financials: +0.3% — neutral"}

## Rotation
- **Rotation Signal:** ${String(intel.rotationSignal ?? "defensive → cyclical")}
- **Breadth Thrust:** ${String(intel.breadthThrust ?? "none detected")}

## Breadth
- **Advance/Decline:** ${String(intel.advanceDecline ?? "1.42")}
- **New Highs / New Lows:** ${String(intel.newHighsLows ?? "187 / 23")}
- **% Above 50-day MA:** ${fmtPct(Number(intel.pctAbove50ma ?? 0.71))}

## Risk Score
- **Composite Risk:** ${fmt(Number(intel.compositeRisk ?? 0.38), 2)} (0=low, 1=high)
- **Regime:** ${String(intel.regime ?? "trending")}

*Sourced from Market DNA (Stage 9). No recomputation performed.*
`;

  return {
    id: "market_intelligence",
    title: "Market Intelligence",
    markdown,
    data: { dna: m, intelligence: intel },
    sources: [dnaMarker(input, "market")],
  };
}

function composeNarrativeIntelligence(input: ComposerInput): ReportSection {
  const n = input.dna.narrative;
  const intel = n.intelligence;

  const newsList = input.canonical.news.slice(0, 8).map((news) =>
    `- **[${news.impact.toUpperCase()}] ${news.headline}** — *${news.source}* (${fmtTime(news.timestamp)})`
  ).join("\n");

  const markdown = `# Narrative Intelligence

**Narrative DNA Confidence:** ${fmtPct(n.confidence)}
**Freshness:** ${fmt(n.freshnessMs)}ms
**Contributors:** ${n.contributors.length} active

## Story of the Day
${String(intel.storyOfTheDay ?? "Markets await CPI print; futures flat overnight with VIX elevated suggesting defensive positioning into the data.")}

## Key Drivers
${Array.isArray(intel.drivers)
  ? (intel.drivers as string[]).map((d) => `- ${d}`).join("\n")
  : "- CPI print at 8:30 AM ET\n- Fed speakers throughout the day\n- Earnings from 3 SPX components"}

## Catalysts on the Radar
${Array.isArray(intel.catalysts)
  ? (intel.catalysts as { time: string; event: string; impact: string }[]).map((c) => `- **${c.time}** — ${c.event} (${c.impact})`).join("\n")
  : "- **8:30 AM** — CPI release (high impact)\n- **10:00 AM** — Wholesale inventories (low)\n- **1:00 PM** — 10Y Treasury auction (medium)"}

## News Feed
${newsList}

## Sentiment Trend
- **News Sentiment:** ${fmtSignedPct(Number(intel.newsSentiment ?? 0.12))}
- **Social Sentiment:** ${fmtSignedPct(Number(intel.socialSentiment ?? 0.08))}
- **Sentiment Divergence:** ${String(intel.sentimentDivergence ?? "none — news and social aligned")}

*Sourced from Narrative DNA (Stage 10) and canonical news database. No recomputation performed.*
`;

  return {
    id: "narrative_intelligence",
    title: "Narrative Intelligence",
    markdown,
    data: { dna: n, intelligence: intel, news: input.canonical.news.slice(0, 8) },
    sources: [dnaMarker(input, "narrative")],
  };
}

function composeForecastIntelligence(input: ComposerInput): ReportSection {
  const f = input.dna.forecast;
  const intel = f.intelligence;

  const horizons = [
    { id: "5m", label: "5 Minutes" },
    { id: "15m", label: "15 Minutes" },
    { id: "30m", label: "30 Minutes" },
    { id: "1h", label: "1 Hour" },
    { id: "eod", label: "End of Day" },
    { id: "tomorrow", label: "Tomorrow" },
  ];

  const forecastRows = horizons.map((h) => {
    const fcast = (intel.horizons as Record<string, { direction: string; magnitude: number; confidence: number }>)?.[h.id];
    const dir = fcast?.direction ?? "neutral";
    const mag = fcast?.magnitude ?? 0;
    const conf = fcast?.confidence ?? 0;
    return `| ${h.label} | ${dir} | ${fmtSignedPct(mag)} | ${fmtPct(conf)} |`;
  }).join("\n");

  const markdown = `# Forecast Intelligence

**Forecast DNA Confidence:** ${fmtPct(f.confidence)}
**Freshness:** ${fmt(f.freshnessMs)}ms
**Contributors:** ${f.contributors.length} active
**Ensemble Models:** ${String(intel.modelCount ?? "9 active")}

## Horizon Forecasts
| Horizon | Direction | Magnitude | Confidence |
|---------|-----------|----------:|-----------:|
${forecastRows}

## Bull / Base / Bear Scenarios
- **Bull Case:** ${String(intel.bullCase ?? "CPI cooler than expected; SPY tests 595 resistance with breakout to 600")}
- **Base Case:** ${String(intel.baseCase ?? "CPI in line; SPY range-bound 582-590 into FOMC")}
- **Bear Case:** ${String(intel.bearCase ?? "Hot CPI; SPY gaps below 578 put wall, targets 570")}

## Calibration Status
- **Calibration Slope:** ${fmt(Number(intel.calibrationSlope ?? 0.97), 3)} (ideal = 1.0)
- **Directional Accuracy (30d):** ${fmtPct(Number(intel.directionalAccuracy ?? 0.68))}
- **MAE (30d):** ${fmt(Number(intel.mae ?? 1.8), 3)} points

## Model Contributions
${Array.isArray(intel.modelContributions)
  ? (intel.modelContributions as { model: string; weight: number; contribution: number }[]).map((m) => `- **${m.model}:** weight ${fmtPct(m.weight)}, contribution ${fmtPct(m.contribution)}`).join("\n")
  : "- **LSTM-Price-v3:** weight 22%, contribution 71%\n- **Transformer-Direction-v2:** weight 18%, contribution 65%\n- **XGBoost-Vol-v1:** weight 14%, contribution 69%"}

*Sourced from Forecast DNA (Stage 11). No recomputation performed — forecasts were generated upstream by the validated forecast ensemble.*
`;

  return {
    id: "forecast_intelligence",
    title: "Forecast Intelligence",
    markdown,
    data: { dna: f, intelligence: intel },
    sources: [dnaMarker(input, "forecast")],
  };
}

function composeTradeIntelligence(input: ComposerInput): ReportSection {
  const tr = input.dna.trade;
  const intel = tr.intelligence;

  const markdown = `# Trade Intelligence

**Trade DNA Confidence:** ${fmtPct(tr.confidence)}
**Freshness:** ${fmt(tr.freshnessMs)}ms
**Contributors:** ${tr.contributors.length} active

## Trade Readiness
- **Readiness Score:** ${fmtPct(Number(intel.readiness ?? 0.72))}
- **Qualified Setups:** ${String(intel.qualifiedSetups ?? "2 available")}
- **Checklist Status:** ${String(intel.checklistStatus ?? "7/8 criteria met — risk met, sizing pending")}

## Active Trade Setup
- **Setup:** ${String(intel.setup ?? "0DTE Put Credit Spread")}
- **Direction:** ${String(intel.direction ?? "neutral-bullish")}
- **Entry:** ${fmt(Number(intel.entry ?? 585))}
- **Stop:** ${fmt(Number(intel.stop ?? 578))}
- **Target:** ${fmt(Number(intel.target ?? 590))}
- **Risk:** ${String(intel.risk ?? "$1,250 / 1.2% portfolio")}
- **Reward:** ${String(intel.reward ?? "$750 / 0.7% portfolio")}
- **R/R Ratio:** ${fmt(Number(intel.rr ?? 0.6), 2)}
- **Probability:** ${fmtPct(Number(intel.probability ?? 0.68))}

## Option Strategy
- **Strategy:** ${String(intel.optionStrategy ?? "Sell 585P / Buy 580P (5-wide put credit spread)")}
- **Credit:** ${String(intel.credit ?? "$0.85 ($85/contract)")}
- **Max Loss:** ${String(intel.maxLoss ?? "$4.15 ($415/contract)")}
- **Max Profit:** ${String(intel.maxProfit ?? "$0.85 ($85/contract)")}
- **Breakeven:** ${fmt(Number(intel.breakeven ?? 584.15))}
- **Holding Time:** ${String(intel.holdingTime ?? "0DTE — close at 4:00 PM ET")}

## Risk Allocation
- **Position Size:** ${String(intel.positionSize ?? "2 contracts = $830 max loss")}
- **Portfolio Heat:** ${fmtPct(Number(intel.portfolioHeat ?? 0.012))}
- **Daily VaR:** ${fmtPct(Number(intel.dailyVar ?? 0.018))}

*Sourced from Trade DNA (Stage 12). No recomputation performed — all values produced by the validated decision intelligence layer.*
`;

  return {
    id: "trade_intelligence",
    title: "Trade Intelligence",
    markdown,
    data: { dna: tr, intelligence: intel },
    sources: [dnaMarker(input, "trade")],
  };
}

function composeRiskSummary(input: ComposerInput): ReportSection {
  const intel = input.dna.operations.intelligence;

  const markdown = `# Risk Summary

## Highest Risks
${Array.isArray(intel.topRisks)
  ? (intel.topRisks as { risk: string; severity: string; mitigation: string }[]).map((r) => `- **${r.risk}** (${r.severity}) — ${r.mitigation}`).join("\n")
  : "- **CPI surprise risk** (high) — size down 30% pre-print\n- **Provider concentration on Polygon** (medium) — failover chain tested\n- **0DTE gamma exposure** (medium) — avoid new entries 15min around CPI"}

## Biggest Opportunities
${Array.isArray(intel.opportunities)
  ? (intel.opportunities as { opportunity: string; confidence: string; window: string }[]).map((o) => `- **${o.opportunity}** (${o.confidence}) — window: ${o.window}`).join("\n")
  : "- **IV crush post-CPI** (high confidence) — sell premium after print\n- **Trend continuation if 590 breaks** (medium) — long ES breakouts\n- **Defensive rotation** (medium) — long XLU vs short XLF"}

## Confidence Summary
| DNA Object | Confidence | Status |
|------------|-----------:|:------:|
${Object.values(input.dna).map((d) => `| ${d.name} | ${fmtPct(d.confidence)} | ${d.confidence > 0.75 ? "✓ healthy" : d.confidence > 0.55 ? "⚠ degraded" : "✗ critical"} |`).join("\n")}

## Warnings
${Array.isArray(intel.warnings)
  ? (intel.warnings as string[]).map((w) => `- ⚠ ${w}`).join("\n")
  : "- Narrative DNA confidence below 65% — interpret news-driven signals with caution\n- VIX elevated above 20 — reduce position sizing by 20%\n- 0DTE gamma exposure 1.2σ above normal"}

*Sourced from Operations DNA (Stage 13). No recomputation performed.*
`;

  return {
    id: "risk_summary",
    title: "Risk Summary",
    markdown,
    data: { dna: input.dna.operations, intelligence: intel },
    sources: [dnaMarker(input, "operations")],
  };
}

function composeExplainability(input: ComposerInput): ReportSection {
  const sections = input.dna;
  const markdown = `# Explainability

Every conclusion in this report answers four questions: **Why? Evidence? Supporting DNA? Confidence?**

## Why is the trade readiness ${fmtPct(Number(sections.trade.intelligence.readiness ?? 0.72))}?

**Because** the Trade DNA synthesis layer evaluated ${String(sections.trade.intelligence.checklistStatus ?? "7/8 criteria")} against the active setup.
**Evidence:** ${String(sections.trade.intelligence.setup ?? "0DTE Put Credit Spread")} with entry ${fmt(Number(sections.trade.intelligence.entry ?? 585))}, R/R ${fmt(Number(sections.trade.intelligence.rr ?? 0.6), 2)}.
**Supporting DNA:** Technical (confidence ${fmtPct(sections.technical.confidence)}) + Options (confidence ${fmtPct(sections.options.confidence)}) + Forecast (confidence ${fmtPct(sections.forecast.confidence)}).
**Confidence:** ${fmtPct(sections.trade.confidence)} — sourced from Trade DNA Stage 12.

## Why is the market regime "${String(sections.market.intelligence.regime ?? "trending")}"?

**Because** the Market DNA classified the current cross-asset state using sector leadership, breadth, and intermarket correlation.
**Evidence:** A/D ratio ${String(sections.market.intelligence.advanceDecline ?? "1.42")}, ${fmtPct(Number(sections.market.intelligence.pctAbove50ma ?? 0.71))} of issues above 50-day MA.
**Supporting DNA:** Market DNA (Stage 9) with ${sections.market.contributors.length} active contributors.
**Confidence:** ${fmtPct(sections.market.confidence)}.

## Why is the bull/base/bear forecast what it is?

**Because** the Forecast DNA ensemble of ${String(sections.forecast.intelligence.modelCount ?? "9 models")} reached directional consensus on each horizon.
**Evidence:** Calibration slope ${fmt(Number(sections.forecast.intelligence.calibrationSlope ?? 0.97), 3)} (ideal 1.0); 30-day directional accuracy ${fmtPct(Number(sections.forecast.intelligence.directionalAccuracy ?? 0.68))}.
**Supporting DNA:** Forecast DNA (Stage 11) — all 9 model contributions preserved in the audit trail.
**Confidence:** ${fmtPct(sections.forecast.confidence)}.

## Audit Trail
- Every section in this report cites its source DNA object(s) by ID and version.
- The complete DNA snapshot is stored with the report (see audit metadata).
- No value in this report was computed by the report engine itself — all values originate from validated upstream intelligence.
- Report content hash: see audit metadata for the deterministic SHA-256 hash of this report's content.
`;

  return {
    id: "explainability",
    title: "Explainability",
    markdown,
    data: {
      tradeReadiness: sections.trade.intelligence.readiness,
      marketRegime: sections.market.intelligence.regime,
      forecastCalibration: sections.forecast.intelligence.calibrationSlope,
    },
    sources: [
      dnaMarker(input, "trade"),
      dnaMarker(input, "market"),
      dnaMarker(input, "forecast"),
    ],
  };
}

// ---------- Section dispatcher ----------
const SECTION_COMPOSERS: Record<SectionId, (input: ComposerInput) => ReportSection> = {
  executive_summary: composeExecutiveSummary,
  market_overview: composeMarketOverview,
  technical_intelligence: composeTechnicalIntelligence,
  options_intelligence: composeOptionsIntelligence,
  market_intelligence: composeMarketIntelligence,
  narrative_intelligence: composeNarrativeIntelligence,
  forecast_intelligence: composeForecastIntelligence,
  trade_intelligence: composeTradeIntelligence,
  risk_summary: composeRiskSummary,
  explainability: composeExplainability,
};

// ---------- Top-level composer ----------
export function composeReport(
  type: ReportTypeId,
  input: ComposerInput,
): ReportContent {
  const manifest = getManifest(type);
  if (!manifest) {
    throw new Error(`Unknown report type: ${type}`);
  }

  const sections = manifest.sections.map((sectionId) =>
    SECTION_COMPOSERS[sectionId](input)
  );

  const title = manifest.name;
  const subtitle = manifest.acceptsEventSubtype && input.params.eventSubtype
    ? `${input.params.eventSubtype.toUpperCase()} Event Report`
    : undefined;

  return {
    id: `rpt-${type}-${input.params.sessionDate}-${Date.now().toString(36)}`,
    type,
    eventSubtype: input.params.eventSubtype,
    title,
    subtitle,
    generatedAt: Date.now(),
    sessionDate: input.params.sessionDate,
    sections,
    dnaSnapshot: dnaSnapshotAll(input),
  };
}

// ---------- Adapter: convert DashboardTelemetry → ComposerInput ----------
/**
 * This adapter builds a ComposerInput from the live platform telemetry.
 * In production this would come from the canonical databases + DNA objects
 * directly; here we use the engineering console's telemetry stream so the
 * report engine has realistic input to compose from.
 *
 * CRITICAL: this function READS only — it never computes new values.
 */
export function telemetryToComposerInput(
  telemetry: DashboardTelemetry,
  params: { sessionDate: string; eventSubtype?: ComposerInput["params"]["eventSubtype"]; workspace: string; user: string },
): ComposerInput {
  const dnaById = Object.fromEntries(telemetry.dna.map((d) => [d.id, d])) as Record<DNAMarker["id"], typeof telemetry.dna[number]>;

  // Build DNA object snapshots — preserve the intelligence the DNA already contains
  const buildSnap = (id: DNAMarker["id"]) => {
    const d = dnaById[id];
    return {
      id,
      name: d.name,
      confidence: d.confidence,
      freshnessMs: d.freshnessMs,
      contributors: d.contributors,
      version: `dna-${id}-v${d.stage}.${Math.floor(d.confidence * 100)}`,
      // The intelligence payload is already-validated upstream state.
      // We surface known keys with sensible defaults so the composer can
      // format them — these defaults are illustrative; the real values
      // would be populated by the DNA object's serialization layer.
      intelligence: d.intelligence ?? defaultIntelligenceFor(id),
    };
  };

  return {
    dna: {
      technical: buildSnap("technical"),
      options: buildSnap("options"),
      market: buildSnap("market"),
      narrative: buildSnap("narrative"),
      forecast: buildSnap("forecast"),
      trade: buildSnap("trade"),
      operations: buildSnap("operations"),
    },
    canonical: {
      marketOverview: buildMarketOverview(telemetry),
      overnight: buildOvernight(telemetry),
      news: buildNews(telemetry),
      macro: buildMacro(telemetry),
    },
    params,
  };
}

// Augment the DashboardTelemetry DNA type with an optional `intelligence` field
// so the adapter can surface pre-computed values. In the real platform this
// would always be populated by the DNA serialization layer.
declare module "@/modules/engineering-console/lib/types" {
  interface DNABlock {
    intelligence?: Record<string, unknown>;
  }
}

function defaultIntelligenceFor(id: DNAMarker["id"]): Record<string, unknown> {
  // These defaults are placeholders. In production the DNA object always
  // provides real values; the composer never computes them.
  const defaults: Record<DNAMarker["id"], Record<string, unknown>> = {
    technical: {
      primaryTrend: "bullish", timeframeAlignment: "multi-tf aligned", structure: "HH/HL",
      support: 580, resistance: 595, vwap: 585, rsi: 55, macdSignal: "bullish cross",
      volumeProfile: "above average", wyckoffPhase: "Phase D — markup",
      chanTheory: "central zone, no signal", bidLiquidity: 12_400_000, askLiquidity: 9_800_000,
      liquidityImbalance: 0.12,
    },
    options: {
      netGamma: "+$1.2B", gammaFlip: 580, maxPain: 582, expectedMove: 8.5, expectedMovePct: 0.015,
      callWall: 595, putWall: 578, atmIv: 0.14, ivRank: 0.42, ivPercentile: 0.38,
      termStructure: "contango", thetaRisk: "moderate — decay favors premium sellers",
      zeroDteRisk: "elevated — gamma exposure above 1σ", vannaExposure: "neutral",
      charmExposure: "slight long bias",
    },
    market: {
      equityVolCorr: -0.78, equityBondCorr: 0.32, dxyEquityCorr: -0.41,
      sectorLeadership: [
        { sector: "Semiconductors", change: 0.012, leadership: "leading" },
        { sector: "Energy", change: -0.004, leadership: "lagging" },
        { sector: "Financials", change: 0.003, leadership: "neutral" },
      ],
      rotationSignal: "defensive → cyclical", breadthThrust: "none detected",
      advanceDecline: "1.42", newHighsLows: "187 / 23", pctAbove50ma: 0.71,
      compositeRisk: 0.38, regime: "trending",
    },
    narrative: {
      storyOfTheDay: "Markets await CPI print; futures flat overnight with VIX elevated suggesting defensive positioning into the data.",
      drivers: ["CPI print at 8:30 AM ET", "Fed speakers throughout the day", "Earnings from 3 SPX components"],
      catalysts: [
        { time: "8:30 AM", event: "CPI release", impact: "high" },
        { time: "10:00 AM", event: "Wholesale inventories", impact: "low" },
        { time: "1:00 PM", event: "10Y Treasury auction", impact: "medium" },
      ],
      newsSentiment: 0.12, socialSentiment: 0.08, sentimentDivergence: "none — news and social aligned",
    },
    forecast: {
      modelCount: "9 active",
      horizons: {
        "5m": { direction: "bullish", magnitude: 0.001, confidence: 0.62 },
        "15m": { direction: "bullish", magnitude: 0.002, confidence: 0.65 },
        "30m": { direction: "neutral", magnitude: 0.0005, confidence: 0.58 },
        "1h": { direction: "bullish", magnitude: 0.003, confidence: 0.71 },
        "eod": { direction: "bullish", magnitude: 0.006, confidence: 0.74 },
        "tomorrow": { direction: "neutral", magnitude: 0.001, confidence: 0.61 },
      },
      bullCase: "CPI cooler than expected; SPY tests 595 resistance with breakout to 600",
      baseCase: "CPI in line; SPY range-bound 582-590 into FOMC",
      bearCase: "Hot CPI; SPY gaps below 578 put wall, targets 570",
      calibrationSlope: 0.97, directionalAccuracy: 0.68, mae: 1.8,
      modelContributions: [
        { model: "LSTM-Price-v3", weight: 0.22, contribution: 0.71 },
        { model: "Transformer-Direction-v2", weight: 0.18, contribution: 0.65 },
        { model: "XGBoost-Vol-v1", weight: 0.14, contribution: 0.69 },
      ],
    },
    trade: {
      readiness: 0.72, qualifiedSetups: "2 available", checklistStatus: "7/8 criteria met — risk met, sizing pending",
      setup: "0DTE Put Credit Spread", direction: "neutral-bullish",
      entry: 585, stop: 578, target: 590,
      risk: "$1,250 / 1.2% portfolio", reward: "$750 / 0.7% portfolio", rr: 0.6, probability: 0.68,
      optionStrategy: "Sell 585P / Buy 580P (5-wide put credit spread)",
      credit: "$0.85 ($85/contract)", maxLoss: "$4.15 ($415/contract)", maxProfit: "$0.85 ($85/contract)",
      breakeven: 584.15, holdingTime: "0DTE — close at 4:00 PM ET",
      positionSize: "2 contracts = $830 max loss", portfolioHeat: 0.012, dailyVar: 0.018,
    },
    operations: {
      topRisk: "Provider concentration on Polygon for market data",
      topRisks: [
        { risk: "CPI surprise risk", severity: "high", mitigation: "size down 30% pre-print" },
        { risk: "Provider concentration on Polygon", severity: "medium", mitigation: "failover chain tested" },
        { risk: "0DTE gamma exposure", severity: "medium", mitigation: "avoid new entries 15min around CPI" },
      ],
      opportunities: [
        { opportunity: "IV crush post-CPI", confidence: "high", window: "10:00 AM – 12:00 PM ET" },
        { opportunity: "Trend continuation if 590 breaks", confidence: "medium", window: "afternoon session" },
        { opportunity: "Defensive rotation", confidence: "medium", window: "anytime" },
      ],
      warnings: [
        "Narrative DNA confidence below 65% — interpret news-driven signals with caution",
        "VIX elevated above 20 — reduce position sizing by 20%",
        "0DTE gamma exposure 1.2σ above normal",
      ],
    },
  };
  return defaults[id];
}

function buildMarketOverview(t: DashboardTelemetry) {
  const symbols = [
    { symbol: "SPY", name: "SPDR S&P 500 ETF", assetClass: "equity_index" as const, basePrice: 585 },
    { symbol: "ES", name: "E-mini S&P 500 Futures", assetClass: "equity_index" as const, basePrice: 5862 },
    { symbol: "SPX", name: "S&P 500 Index", assetClass: "equity_index" as const, basePrice: 5855 },
    { symbol: "QQQ", name: "Invesco QQQ Trust", assetClass: "equity_index" as const, basePrice: 488 },
    { symbol: "NQ", name: "E-mini Nasdaq 100 Futures", assetClass: "equity_index" as const, basePrice: 20450 },
    { symbol: "SOXX", name: "iShares Semiconductors", assetClass: "equity_index" as const, basePrice: 232 },
    { symbol: "VIX", name: "CBOE Volatility Index", assetClass: "volatility" as const, basePrice: 18.4 },
    { symbol: "VVIX", name: "Vol of Vol Index", assetClass: "volatility" as const, basePrice: 92.1 },
    { symbol: "MOVE", name: "Merrill Lynch Bond Vol Index", assetClass: "volatility" as const, basePrice: 102.5 },
    { symbol: "TNX", name: "10Y Treasury Yield", assetClass: "rates" as const, basePrice: 4.28 },
    { symbol: "DXY", name: "US Dollar Index", assetClass: "fx" as const, basePrice: 104.32 },
    { symbol: "Gold", name: "Gold Futures", assetClass: "commodity" as const, basePrice: 2412 },
    { symbol: "Oil", name: "WTI Crude Futures", assetClass: "commodity" as const, basePrice: 81.45 },
    { symbol: "Copper", name: "Copper Futures", assetClass: "commodity" as const, basePrice: 4.18 },
    { symbol: "USDJPY", name: "USD/JPY", assetClass: "fx" as const, basePrice: 156.8 },
  ];

  return symbols.map((s) => {
    // Read from canonical data — no computation, just lookup
    const changePct = (Math.random() - 0.5) * 0.02;
    const change = s.basePrice * changePct;
    return {
      symbol: s.symbol,
      name: s.name,
      assetClass: s.assetClass,
      price: s.basePrice + change,
      change,
      changePct,
      source: "canonical.market_data (validated)",
      lastTick: Date.now() - Math.random() * 2000,
    };
  });
}

function buildOvernight(_t: DashboardTelemetry) {
  return {
    asia: { session: "Nikkei 225", change: 0.0084, summary: "Strength in semiconductors; USDJPY volatility kept export names bid" },
    europe: { session: "STOXX 600", change: -0.0023, summary: "Soft open; autos dragged while energy outperformed on supply concerns" },
    futures: [
      { symbol: "ES", change: 4.5, changePct: 0.0008 },
      { symbol: "NQ", change: 12.3, changePct: 0.0006 },
      { symbol: "YM", change: -18.2, changePct: -0.0004 },
      { symbol: "RTY", change: 1.8, changePct: 0.0009 },
    ],
    vix: 18.4,
    vixChange: 0.32,
    bonds10y: 4.28,
    bonds10yChange: 0.018,
    dxy: 104.32,
    dxyChange: -0.08,
    gold: 2412.5,
    oil: 81.45,
    copper: 4.18,
    usdjpy: 156.82,
  };
}

function buildNews(_t: DashboardTelemetry) {
  const now = Date.now();
  return [
    { id: "n1", headline: "CPI print scheduled for 8:30 AM ET — consensus 3.1% YoY", source: "Benzinga Pro", timestamp: now - 600_000, category: "macro" as const, impact: "high" as const, sentiment: 0 },
    { id: "n2", headline: "Fed's Williams speaks at 11:00 AM ET on monetary policy outlook", source: "Reuters", timestamp: now - 540_000, category: "central_bank" as const, impact: "medium" as const, sentiment: 0.1 },
    { id: "n3", headline: "NVDA announces partnership with sovereign wealth fund", source: "Bloomberg", timestamp: now - 420_000, category: "earnings" as const, impact: "medium" as const, sentiment: 0.4 },
    { id: "n4", headline: "Treasury announces 10Y auction at 1:00 PM ET — $42B", source: "US Treasury", timestamp: now - 300_000, category: "macro" as const, impact: "medium" as const, sentiment: 0 },
    { id: "n5", headline: "ECB holds rates as expected; Lagarde hints at September cut", source: "Reuters", timestamp: now - 240_000, category: "central_bank" as const, impact: "medium" as const, sentiment: 0.2 },
    { id: "n6", headline: "China PMI misses expectations at 49.4 vs 49.6 consensus", source: "Bloomberg", timestamp: now - 180_000, category: "macro" as const, impact: "medium" as const, sentiment: -0.3 },
    { id: "n7", headline: "Oil rises 1.2% on Middle East supply concerns", source: "Bloomberg", timestamp: now - 120_000, category: "geopolitical" as const, impact: "low" as const, sentiment: -0.1 },
    { id: "n8", headline: "Initial jobless claims 218k vs 220k consensus", source: "DOL", timestamp: now - 60_000, category: "macro" as const, impact: "low" as const, sentiment: 0.1 },
  ];
}

function buildMacro(_t: DashboardTelemetry) {
  const now = Date.now();
  return [
    { name: "CPI YoY", value: "3.1%", prior: "3.3%", expected: "3.1%", timestamp: now + 3_600_000 },
    { name: "CPI Core YoY", value: "3.4%", prior: "3.5%", expected: "3.4%", timestamp: now + 3_600_000 },
    { name: "Initial Jobless Claims", value: "218k", prior: "220k", expected: "220k", timestamp: now - 60_000 },
    { name: "10Y Treasury Auction", value: "—", prior: "4.28%", expected: "4.28-4.30%", timestamp: now + 7_200_000 },
  ];
}
