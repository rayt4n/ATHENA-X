/**
 * ATHENA-X Mock Telemetry Engine
 *
 * Produces a realistic snapshot of platform runtime state, then mutates it
 * tick-by-tick so the validation dashboard behaves like a live system.
 *
 * The shape mirrors what the real platform would publish on its event bus:
 *  - 20 market-data providers across 5 failover chains
 *  - 15 data sources tracked for freshness
 *  - Technical-indicator validator checks against benchmarks
 *  - Options-data accuracy checks (IV surface, Greek parity, arbitrage)
 *  - Forecast records with realized outcomes for accuracy tracking
 *  - Trade-DNA decisions streaming from the trade intelligence platform
 *  - Event-bus latency/throughput/backlog metrics
 *  - All registered AI agents with state + heartbeat
 *  - Database write latency per schema + write-lock queue
 *  - Seven DNA intelligence objects with confidence + contributors
 *
 * Determinism: the initial seed is fixed so the very first paint is
 * identical across reloads (important for visual review). Subsequent ticks
 * apply stochastic jitter to simulate live conditions.
 */

import type {
  AgentState,
  Alarm,
  DashboardTelemetry,
  DNABlock,
  DatabaseSchemaMetrics,
  EventBusMetrics,
  ForecastAccuracySummary,
  ForecastRecord,
  OptionsAccuracyCheck,
  ProviderStatus,
  SystemSummary,
  TechnicalIndicatorCheck,
  TradeDNADecision,
  DataFreshnessEntry,
} from "./types";

// ---------- deterministic PRNG (mulberry32) ----------
function mulberry32(seed: number) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rng = mulberry32(0x41544e41); // "ATHENA-X"
const rand = (min: number, max: number) => min + (max - min) * rng();
const randInt = (min: number, max: number) => Math.floor(rand(min, max + 1));
const pick = <T,>(arr: T[]): T => arr[randInt(0, arr.length - 1)];
const jitter = (base: number, pct: number) => base * (1 + (rng() - 0.5) * 2 * pct);

// ---------- catalogues ----------
const PROVIDERS: { id: string; name: string; category: ProviderStatus["category"]; failoverRank: number }[] = [
  { id: "polygon",   name: "Polygon.io",          category: "market_data",  failoverRank: 0 },
  { id: "tradier",   name: "Tradier",              category: "market_data",  failoverRank: 1 },
  { id: "iex",       name: "IEX Cloud",            category: "market_data",  failoverRank: 2 },
  { id: "alpaca",    name: "Alpaca",               category: "market_data",  failoverRank: 3 },
  { id: "yfinance",  name: "Yahoo Finance",        category: "market_data",  failoverRank: 4 },

  { id: "cboe",      name: "CBOE LiveVol",         category: "options_data", failoverRank: 0 },
  { id: "opradar",   name: "OptionRadar",          category: "options_data", failoverRank: 1 },
  { id: "unusualw",  name: "Unusual Whales",       category: "options_data", failoverRank: 2 },
  { id: "tradier-o", name: "Tradier Options",      category: "options_data", failoverRank: 3 },

  { id: "benzinga",  name: "Benzinga Pro",         category: "news",         failoverRank: 0 },
  { id: "tiingo-n",  name: "Tiingo News",          category: "news",         failoverRank: 1 },
  { id: "politic",   name: "Politico API",         category: "news",         failoverRank: 2 },

  { id: "fred",      name: "FRED (St. Louis Fed)", category: "macro",        failoverRank: 0 },
  { id: "investing", name: "Investing.com",        category: "macro",        failoverRank: 1 },

  { id: "senti",     name: "SentimentR",           category: "alt_data",     failoverRank: 0 },
  { id: "stocktwits",name: "StockTwits",           category: "alt_data",     failoverRank: 1 },
  { id: "sec",       name: "SEC EDGAR",            category: "alt_data",     failoverRank: 2 },
  { id: "nasdaq-t",  name: "Nasdaq TotalView",     category: "market_data",  failoverRank: 0 },
  { id: "iex-t",     name: "IEX DEEP",             category: "market_data",  failoverRank: 1 },
  { id: "cme",       name: "CME Globex",           category: "market_data",  failoverRank: 0 },
];

const FRESHNESS_SYMBOLS: { symbol: string; assetClass: DataFreshnessEntry["assetClass"]; cadenceMs: number }[] = [
  { symbol: "SPY",   assetClass: "equity_index", cadenceMs: 250 },
  { symbol: "ES",    assetClass: "futures",      cadenceMs: 250 },
  { symbol: "SPX",   assetClass: "options",      cadenceMs: 500 },
  { symbol: "VIX",   assetClass: "equity_index", cadenceMs: 1000 },
  { symbol: "QQQ",   assetClass: "equity_index", cadenceMs: 250 },
  { symbol: "IWM",   assetClass: "equity_index", cadenceMs: 250 },
  { symbol: "DXY",   assetClass: "fx",           cadenceMs: 5000 },
  { symbol: "US10Y", assetClass: "rates",        cadenceMs: 5000 },
  { symbol: "CL",    assetClass: "futures",      cadenceMs: 1000 },
  { symbol: "GC",    assetClass: "futures",      cadenceMs: 1000 },
  { symbol: "BTC",   assetClass: "fx",           cadenceMs: 1000 },
  { symbol: "EURUSD",assetClass: "fx",           cadenceMs: 1000 },
  { symbol: "AAPL",  assetClass: "equity_index", cadenceMs: 500 },
  { symbol: "NVDA",  assetClass: "equity_index", cadenceMs: 250 },
  { symbol: "TSLA",  assetClass: "equity_index", cadenceMs: 250 },
];

const INDICATORS = ["EMA_20", "EMA_50", "EMA_200", "RSI_14", "MACD_12_26_9", "ATR_14", "VWAP", "BB_20_2", "OBV", "ADX_14", "Stoch_14_3_3", "Ichimoku"];
const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];
const SYMBOLS = ["SPY", "ES", "SPX", "QQQ", "IWM", "VIX"];
const TA_VALIDATORS = ["PatternValidator", "CrossSourceValidator", "LogicalValidator", "OutlierValidator"];

const OPTIONS_CHECKS: OptionsAccuracyCheck["check"][] = [
  "iv_surface_smoothness", "greeks_parity", "put_call_arbitrage", "vol_smile_curvature", "delta_hedge_drift",
];

const FORECAST_MODELS = [
  "LSTM-Price-v3",
  "Transformer-Direction-v2",
  "XGBoost-Vol-v1",
  "Ensemble-Consensus",
  "Volatility-Regime-HMM",
  "MeanReversion-EWMA",
  "Momentum-CNN",
  "Bayesian-Regression",
  "RandomForest-Direction",
];

const TRADE_SETUPS = [
  "0DTE Put Credit Spread",
  "0DTE Call Debit Spread",
  "VWAP Reversal Long",
  "Opening Range Breakout",
  "Trend Pullback Continuation",
  "Mean Reversion Fade",
  "Volatility Crush (Post-Earnings)",
  "Gap-and-Go Long",
  "Iceberg Absorption Long",
  "Gamma Squeeze Continuation",
];

const REASONING_TAGS = [
  "structure:HH", "structure:HL", "EMA20_above_EMA50", "VWAP_aligned",
  "IV_rank>70", "delta_neutral", "negative_gamma", "GERM_long",
  "GERM_short", "0DTE_gamma", "put_wall_below", "call_wall_above",
  "GEX_positive", "GEX_negative", "trend_alignment", "multi_tf_consensus",
  "forecast_above_threshold", "drawdown_compliant", "max_dae_lt_2pct",
  "vwap_reclaim", "op_expiration_today",
];

const AGENT_CATALOG: { id: string; name: string; stage: number; category: AgentState["category"] }[] = [
  { id: "val.schema",       name: "Schema Validator",          stage: 3, category: "validation" },
  { id: "val.timestamp",    name: "Timestamp Validator",       stage: 3, category: "validation" },
  { id: "val.calendar",     name: "Calendar Validator",        stage: 3, category: "validation" },
  { id: "val.crosssource",  name: "Cross-Source Validator",    stage: 3, category: "validation" },
  { id: "val.logical",      name: "Logical Validator",         stage: 3, category: "validation" },
  { id: "val.integrity",    name: "Integrity Validator",       stage: 3, category: "validation" },
  { id: "val.duplicate",    name: "Duplicate Validator",       stage: 3, category: "validation" },
  { id: "val.outlier",      name: "Outlier Validator",         stage: 3, category: "validation" },
  { id: "val.confidence",   name: "Confidence Validator",      stage: 3, category: "validation" },
  { id: "val.isolation",    name: "Isolation Validator",       stage: 3, category: "validation" },
  { id: "val.marketstate",  name: "Market-State Validator",    stage: 3, category: "validation" },

  { id: "norm.equity",      name: "Equity Normalizer",         stage: 4, category: "normalization" },
  { id: "norm.options",     name: "Options Normalizer",        stage: 4, category: "normalization" },
  { id: "norm.futures",     name: "Futures Normalizer",        stage: 4, category: "normalization" },
  { id: "norm.fx",          name: "FX Normalizer",             stage: 4, category: "normalization" },

  { id: "ta.marketstructure", name: "Market-Structure Agent",  stage: 7, category: "technical" },
  { id: "ta.indicators",      name: "Indicator Engine",        stage: 7, category: "technical" },
  { id: "ta.institutional",   name: "Institutional Footprint", stage: 7, category: "technical" },
  { id: "ta.consensus",       name: "Multi-TF Consensus",      stage: 7, category: "technical" },
  { id: "ta.supervisor",      name: "TA Supervisor",           stage: 7, category: "technical" },

  { id: "opt.flow",         name: "Options Flow Agent",        stage: 8, category: "options" },
  { id: "opt.greeks",       name: "Greeks Engine",             stage: 8, category: "options" },
  { id: "opt.iv",           name: "IV Surface Agent",          stage: 8, category: "options" },
  { id: "opt.gex",          name: "Gamma Exposure Agent",      stage: 8, category: "options" },
  { id: "opt.0dte",         name: "0DTE Intelligence Agent",   stage: 8, category: "options" },

  { id: "mkt.correlation",  name: "Cross-Asset Correlation",   stage: 9, category: "market" },
  { id: "mkt.leadership",   name: "Sector Leadership Agent",   stage: 9, category: "market" },
  { id: "mkt.breadth",      name: "Breadth Engine",            stage: 9, category: "market" },
  { id: "mkt.regime",       name: "Market Regime Agent",       stage: 9, category: "market" },

  { id: "narr.event",       name: "Event Classifier",          stage: 10, category: "narrative" },
  { id: "narr.impact",      name: "Impact Scorer",             stage: 10, category: "narrative" },
  { id: "narr.timeline",    name: "Timeline Builder",          stage: 10, category: "narrative" },
  { id: "narr.generator",   name: "Narrative Generator",       stage: 10, category: "narrative" },
  { id: "narr.radar",       name: "Catalyst Radar",            stage: 10, category: "narrative" },

  { id: "fc.feature",       name: "Feature Fusion",            stage: 11, category: "forecast" },
  { id: "fc.ensemble",      name: "Forecast Ensemble",         stage: 11, category: "forecast" },
  { id: "fc.selfvalidate",  name: "Self-Validator",            stage: 11, category: "forecast" },
  { id: "fc.memory",        name: "Market Memory",             stage: 11, category: "forecast" },

  { id: "tr.qualify",       name: "Trade Qualifier",           stage: 12, category: "trade" },
  { id: "tr.timing",        name: "Timing Engine",             stage: 12, category: "trade" },
  { id: "tr.risk",          name: "Risk Engine",               stage: 12, category: "trade" },
  { id: "tr.checklist",     name: "Checklist Engine",          stage: 12, category: "trade" },

  { id: "ops.health",       name: "System Health Agent",       stage: 13, category: "operations" },
  { id: "ops.registry",     name: "Agent Registry",            stage: 13, category: "operations" },
  { id: "ops.arbiter",      name: "Confidence Arbiter",        stage: 13, category: "operations" },
  { id: "ops.selfheal",     name: "Self-Healing Agent",        stage: 13, category: "operations" },
  { id: "ops.audit",        name: "Audit Agent",               stage: 13, category: "operations" },
];

const DB_SCHEMAS = [
  "ohlcv", "options_chain", "options_flow", "greeks", "iv_surface",
  "trade_decisions", "forecasts", "events", "narratives", "indicators",
  "agents", "audit_log",
];

const DNA_DEFS: { id: DNABlock["id"]; name: string; stage: number; baseConf: number; contributors: string[] }[] = [
  {
    id: "technical",
    name: "Technical DNA",
    stage: 7,
    baseConf: 0.78,
    contributors: ["Market Structure", "EMA Stack", "VWAP", "RSI", "MACD", "Volume Profile", "Ichimoku"],
  },
  {
    id: "options",
    name: "Options DNA",
    stage: 8,
    baseConf: 0.72,
    contributors: ["GEX", "Dealer Positioning", "IV Rank", "0DTE Flow", "Unusual Options", "Put/Call Ratio"],
  },
  {
    id: "market",
    name: "Market DNA",
    stage: 9,
    baseConf: 0.81,
    contributors: ["Sector Leadership", "Breadth", "Correlation", "Regime Classifier", "Intermarket"],
  },
  {
    id: "narrative",
    name: "Narrative DNA",
    stage: 10,
    baseConf: 0.65,
    contributors: ["Event Classifier", "Impact Scorer", "Timeline", "Catalyst Radar", "News Sentiment"],
  },
  {
    id: "forecast",
    name: "Forecast DNA",
    stage: 11,
    baseConf: 0.69,
    contributors: ["LSTM-Price", "Transformer-Direction", "XGBoost-Vol", "Ensemble", "Bayesian"],
  },
  {
    id: "trade",
    name: "Trade DNA",
    stage: 12,
    baseConf: 0.74,
    contributors: ["Qualification", "Timing", "Risk Engine", "Checklist", "Scenario Tree"],
  },
  {
    id: "operations",
    name: "Operations DNA",
    stage: 13,
    baseConf: 0.88,
    contributors: ["Health Monitor", "Agent Registry", "Confidence Arbiter", "Self-Healing", "Audit"],
  },
];

// ---------- initial snapshot builders ----------
function buildProviders(now: number): ProviderStatus[] {
  return PROVIDERS.map((p) => {
    const baseLatency =
      p.category === "market_data" ? rand(8, 60) :
      p.category === "options_data" ? rand(40, 180) :
      p.category === "news" ? rand(200, 800) :
      p.category === "macro" ? rand(500, 2000) :
      rand(100, 500);

    // Failover ranks > 0 are usually idle until primary fails
    const active = p.failoverRank === 0 || rng() < 0.25;
    const state: ProviderStatus["state"] = !active
      ? "warming"
      : rng() < 0.88 ? "healthy" : rng() < 0.6 ? "degraded" : "down";

    return {
      id: p.id,
      name: p.name,
      category: p.category,
      state,
      lastTickMs: state === "down" ? rand(30_000, 180_000) : rand(50, 5_000),
      lastDataMs: state === "down"
        ? rand(60_000, 600_000)
        : state === "degraded"
          ? rand(5_000, 30_000)
          : rand(100, 2_000),
      tickRate: state === "down" ? 0 : state === "degraded" ? rand(0.2, 1.5) : jitter(p.category === "macro" ? 0.1 : 4, 0.4),
      errors5m: state === "healthy" ? randInt(0, 3) : state === "degraded" ? randInt(4, 18) : randInt(20, 90),
      failoverRank: p.failoverRank,
      uptime: state === "down" ? rand(0.85, 0.93) : rand(0.97, 0.9998),
      latencyMs: state === "down" ? 0 : baseLatency,
    };
  });
}

function buildFreshness(now: number, providers: ProviderStatus[]): DataFreshnessEntry[] {
  const activeMarket = providers.filter((p) => p.category === "market_data" && p.state !== "down");
  const activeOptions = providers.filter((p) => p.category === "options_data" && p.state !== "down");
  const activeNews = providers.filter((p) => p.category === "news" && p.state !== "down");
  const activeMacro = providers.filter((p) => p.category === "macro" && p.state !== "down");
  const activeAlt = providers.filter((p) => p.category === "alt_data" && p.state !== "down");

  return FRESHNESS_SYMBOLS.map((s) => {
    let sourcePool = activeMarket;
    if (s.assetClass === "options") sourcePool = activeOptions.length ? activeOptions : activeMarket;
    if (s.assetClass === "fx") sourcePool = activeMacro.length ? activeMacro : activeMarket;
    if (s.assetClass === "rates") sourcePool = activeMacro.length ? activeMacro : activeMarket;
    if (sourcePool.length === 0) sourcePool = activeMarket;

    const src = sourcePool[randInt(0, sourcePool.length - 1)] ?? providers[0];
    const lag = s.cadenceMs * (1 + rng() * 3);
    const state = lag > s.cadenceMs * 5 ? "degraded" : lag > s.cadenceMs * 12 ? "down" : "healthy";

    return {
      symbol: s.symbol,
      assetClass: s.assetClass,
      lastTick: now - lag,
      source: src?.name ?? "—",
      state,
      cadenceMs: s.cadenceMs,
    };
  });
}

function buildTAChecks(now: number): TechnicalIndicatorCheck[] {
  const out: TechnicalIndicatorCheck[] = [];
  for (let i = 0; i < 14; i++) {
    const ind = INDICATORS[i % INDICATORS.length];
    const tf = pick(TIMEFRAMES);
    const sym = pick(SYMBOLS);
    const benchmark = ind.startsWith("RSI") ? rand(20, 80) :
                      ind.startsWith("EMA") ? rand(420, 580) :
                      ind === "VWAP" ? rand(420, 580) :
                      ind === "ATR_14" ? rand(0.5, 6) :
                      rand(-100, 100);
    const drift = (rng() - 0.5) * 0.02; // ±1%
    const computed = benchmark * (1 + drift);
    const state: TechnicalIndicatorCheck["state"] = Math.abs(drift) > 0.015 ? "degraded" : "healthy";
    out.push({
      id: `ta-${i}`,
      symbol: sym,
      indicator: ind,
      timeframe: tf,
      computed,
      benchmark,
      drift,
      state,
      lastValidation: now - randInt(200, 12_000),
      validator: pick(TA_VALIDATORS),
    });
  }
  return out;
}

function buildOptionsChecks(now: number): OptionsAccuracyCheck[] {
  const out: OptionsAccuracyCheck[] = [];
  for (let i = 0; i < 10; i++) {
    const check = OPTIONS_CHECKS[i % OPTIONS_CHECKS.length];
    const sym = pick(SYMBOLS);
    const { value, threshold, detail } =
      check === "iv_surface_smoothness"
        ? { value: rand(0.001, 0.02), threshold: 0.015, detail: "RMS deviation across strike-time grid" }
        : check === "greeks_parity"
          ? { value: rand(0, 0.03), threshold: 0.025, detail: "Delta + gamma parity vs Black-Scholes" }
          : check === "put_call_arbitrage"
            ? { value: rand(0, 0.5), threshold: 0.4, detail: "Synthetic vs actual put-call spread" }
            : check === "vol_smile_curvature"
              ? { value: rand(0, 4), threshold: 3.5, detail: "Smile curvature parameter vs 30D baseline" }
              : { value: rand(0, 0.02), threshold: 0.018, detail: "Delta-hedge drift per 5min window" };
    const state: OptionsAccuracyCheck["state"] = value > threshold ? "critical" : value > threshold * 0.8 ? "degraded" : "healthy";
    out.push({
      id: `opt-${i}`,
      symbol: sym,
      check,
      value,
      threshold,
      state,
      detail,
      lastCheck: now - randInt(500, 8_000),
    });
  }
  return out;
}

function buildForecast(now: number): { recent: ForecastRecord[]; summary: ForecastAccuracySummary } {
  const recent: ForecastRecord[] = [];
  for (let i = 0; i < 12; i++) {
    const model = pick(FORECAST_MODELS);
    const horizon = pick(["5m", "15m", "1h", "1d"]);
    const target = pick(SYMBOLS);
    const predicted = rand(415, 580);
    const resolved = rng() < 0.6;
    const realized = resolved ? predicted * (1 + (rng() - 0.5) * 0.02) : undefined;
    const error = resolved && realized !== undefined ? Math.abs(predicted - realized) : undefined;
    recent.push({
      id: `fc-${i}`,
      model,
      horizon,
      target,
      predicted,
      realized,
      error,
      confidence: rand(0.45, 0.92),
      timestamp: now - randInt(60_000, 3_600_000),
      state: resolved ? "resolved" : "pending",
    });
  }
  recent.sort((a, b) => b.timestamp - a.timestamp);

  const calibrationCurve = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].map((bucket) => ({
    bucket,
    predicted: bucket,
    observed: Math.min(1, Math.max(0, bucket + (rng() - 0.5) * 0.12)),
    n: randInt(20, 200),
  }));

  const perModel = FORECAST_MODELS.slice(0, 5).map((m) => ({
    model: m,
    hitRate: rand(0.5, 0.82),
    mae: rand(0.8, 4.2),
    n: randInt(50, 400),
  }));

  return {
    recent,
    summary: {
      totalForecasts: randInt(1200, 1800),
      resolvedCount: randInt(950, 1300),
      hitRate: rand(0.58, 0.74),
      mae: rand(1.2, 3.2),
      rmse: rand(1.8, 4.4),
      calibrationSlope: rand(0.88, 1.08),
      calibrationCurve,
      perModel,
    },
  };
}

function buildTradeDecisions(now: number): TradeDNADecision[] {
  const out: TradeDNADecision[] = [];
  const statuses: TradeDNADecision["status"][] = ["evaluating", "qualified", "rejected", "triggered", "managed", "closed"];
  for (let i = 0; i < 10; i++) {
    const sym = pick(SYMBOLS);
    const dir = pick(["long", "short", "neutral"] as const);
    const setup = pick(TRADE_SETUPS);
    const entry = rand(420, 580);
    const stop = dir === "long" ? entry * (1 - rand(0.003, 0.012)) : entry * (1 + rand(0.003, 0.012));
    const target = dir === "long" ? entry * (1 + rand(0.006, 0.025)) : entry * (1 - rand(0.006, 0.025));
    const risk = Math.abs(entry - stop);
    const reward = Math.abs(target - entry);
    const status = pick(statuses);
    const tags = Array.from({ length: randInt(3, 6) }, () => pick(REASONING_TAGS));
    const dnaInputs = {
      technical: rand(0.4, 0.95),
      options: rand(0.4, 0.9),
      market: rand(0.5, 0.92),
      narrative: rand(0.3, 0.85),
      forecast: rand(0.4, 0.88),
    };
    out.push({
      id: `td-${i}`,
      symbol: sym,
      direction: dir,
      setup,
      entry,
      stop,
      target,
      confidence: rand(0.45, 0.92),
      rr: risk > 0 ? reward / risk : 0,
      status,
      reasoningTags: Array.from(new Set(tags)),
      dnaInputs,
      timestamp: now - randInt(10_000, 5_400_000),
      outcomePnl: status === "closed" ? (rng() < 0.6 ? 1 : -1) * rand(0.2, 4.5) : undefined,
    });
  }
  out.sort((a, b) => b.timestamp - a.timestamp);
  return out;
}

function buildEventBus(now: number): EventBusMetrics {
  const latencyHistory = Array.from({ length: 30 }, (_, i) => {
    const t = now - (30 - i) * 2_000;
    const base = 12 + Math.sin(i / 4) * 4 + (rng() - 0.5) * 4;
    return {
      t,
      p50: base,
      p95: base * 2.1 + 8,
      p99: base * 3.4 + 18,
    };
  });
  const throughputHistory = Array.from({ length: 30 }, (_, i) => {
    const t = now - (30 - i) * 2_000;
    const inflow = 1200 + Math.sin(i / 5) * 300 + (rng() - 0.5) * 200;
    return { t, inflow, outflow: inflow * (0.94 + rng() * 0.05) };
  });

  return {
    inflowPerSec: jitter(1240, 0.1),
    outflowPerSec: jitter(1180, 0.1),
    backlog: randInt(40, 380),
    backlogLimit: 10_000,
    p50LatencyMs: jitter(13, 0.12),
    p95LatencyMs: jitter(34, 0.18),
    p99LatencyMs: jitter(72, 0.22),
    replayDepth: randInt(0, 5000),
    replayLag: randInt(0, 800),
    snapshotBarrierStatus: rng() < 0.85 ? "completed" : rng() < 0.7 ? "open" : "blocked",
    lastSnapshotMs: randInt(800, 8_000),
    latencyHistory,
    throughputHistory,
    priorityDistribution: [
      { priority: "P0", count: randInt(20, 80), percentage: 0 },
      { priority: "P1", count: randInt(180, 420), percentage: 0 },
      { priority: "P2", count: randInt(580, 920), percentage: 0 },
      { priority: "P3", count: randInt(180, 420), percentage: 0 },
    ].map((p, _i, arr) => {
      const total = arr.reduce((s, x) => s + x.count, 0);
      return { ...p, percentage: p.count / total };
    }),
  };
}

function buildAgents(now: number): AgentState[] {
  return AGENT_CATALOG.map((a) => {
    const isHealthy = rng() < 0.86;
    const isDegraded = !isHealthy && rng() < 0.65;
    const state: AgentState["state"] = isHealthy ? "healthy" : isDegraded ? "degraded" : "down";
    return {
      id: a.id,
      name: a.name,
      stage: a.stage,
      category: a.category,
      state,
      lastHeartbeatMs: state === "down" ? rand(20_000, 120_000) : rand(200, 4_000),
      processedEvents: randInt(5_000, 9_000_000),
      errors: state === "healthy" ? randInt(0, 12) : state === "degraded" ? randInt(15, 80) : randInt(80, 400),
      cpuPct: state === "down" ? 0 : state === "degraded" ? rand(35, 90) : rand(2, 28),
      memMb: rand(80, 1200),
      uptime: rand(0.95, 0.9999),
      currentTask: state === "down" ? undefined : pick([
        "ingesting tick batch", "validating schema", "running indicator sweep",
        "updating IV surface", "scoring narrative", "evaluating trade setup",
        "computing ensemble forecast", "writing event log", "snapshotting DNA",
        "idle — awaiting event",
      ]),
    };
  });
}

function buildDatabase(now: number): DatabaseSchemaMetrics[] {
  return DB_SCHEMAS.map((schema) => {
    const p50 = schema === "events" ? rand(0.6, 1.8) : schema === "ohlcv" ? rand(0.8, 2.4) : rand(1.2, 6);
    const p95 = p50 * rand(2.5, 5);
    const queue = schema === "events" ? randInt(0, 60) : randInt(0, 12);
    const state: DatabaseSchemaMetrics["state"] = p95 > 25 || queue > 40 ? "degraded" : "healthy";
    return {
      schema,
      writeP50: p50,
      writeP95: p95,
      writeLockQueue: queue,
      rowsLastMin: schema === "events" ? randInt(40_000, 90_000) : randInt(200, 8_000),
      totalRows: randInt(100_000, 90_000_000),
      partitionCount: randInt(8, 64),
      state,
    };
  });
}

function buildDNA(now: number): DNABlock[] {
  return DNA_DEFS.map((d) => {
    const baseConf = d.baseConf;
    const history = Array.from({ length: 40 }, (_, i) => {
      const t = now - (40 - i) * 30_000;
      const c = Math.min(0.98, Math.max(0.25, baseConf + Math.sin(i / 6) * 0.06 + (rng() - 0.5) * 0.05));
      return { t, confidence: c };
    });
    const confidence = history[history.length - 1].confidence;
    const state: DNABlock["state"] = confidence > 0.75 ? "healthy" : confidence > 0.55 ? "degraded" : "critical";
    return {
      id: d.id,
      name: d.name,
      stage: d.stage,
      confidence,
      trend: Math.sin(Date.now() / 60_000) * 0.2 + (rng() - 0.5) * 0.3,
      freshnessMs: randInt(200, 5_000),
      inputCount: randInt(8, 40),
      validatorCount: randInt(2, 6),
      state,
      contributors: d.contributors.map((c) => ({
        name: c,
        weight: rand(0.05, 0.35),
        contribution: rand(0.4, 0.95),
        state: rng() < 0.85 ? "healthy" : "degraded",
      })),
      history,
      lastSerialized: now - randInt(500, 8_000),
      serializationSizeKb: rand(2.4, 18.6),
    };
  });
}

function buildAlarms(now: number, providers: ProviderStatus[], agents: AgentState[], dna: DNABlock[]): Alarm[] {
  const alarms: Alarm[] = [];
  providers.filter((p) => p.state === "down" || p.state === "degraded").slice(0, 3).forEach((p, i) => {
    alarms.push({
      id: `alm-prov-${p.id}-${i}`,
      severity: p.state === "down" ? "critical" : "warning",
      source: `provider:${p.id}`,
      message: `${p.name} ${p.state} — ${p.errors5m} errors in last 5m, last tick ${Math.round(p.lastDataMs / 1000)}s ago`,
      raisedAt: now - randInt(60_000, 900_000),
      acked: false,
    });
  });
  agents.filter((a) => a.state === "down" || a.state === "degraded").slice(0, 2).forEach((a, i) => {
    alarms.push({
      id: `alm-agent-${a.id}-${i}`,
      severity: a.state === "down" ? "critical" : "warning",
      source: `agent:${a.id}`,
      message: `Agent "${a.name}" (stage ${a.stage}) is ${a.state} — heartbeat ${Math.round(a.lastHeartbeatMs / 1000)}s ago`,
      raisedAt: now - randInt(30_000, 600_000),
      acked: false,
    });
  });
  dna.filter((d) => d.confidence < 0.6).slice(0, 2).forEach((d, i) => {
    alarms.push({
      id: `alm-dna-${d.id}-${i}`,
      severity: d.confidence < 0.4 ? "critical" : "warning",
      source: `dna:${d.id}`,
      message: `${d.name} confidence ${(d.confidence * 100).toFixed(1)}% below threshold`,
      raisedAt: now - randInt(120_000, 1_200_000),
      acked: false,
    });
  });
  return alarms;
}

// ---------- engine state ----------
let state: DashboardTelemetry | null = null;

function buildInitialSnapshot(): DashboardTelemetry {
  const now = Date.now();
  const providers = buildProviders(now);
  const freshness = buildFreshness(now, providers);
  const taChecks = buildTAChecks(now);
  const optionsChecks = buildOptionsChecks(now);
  const forecast = buildForecast(now);
  const tradeDecisions = buildTradeDecisions(now);
  const eventBus = buildEventBus(now);
  const agents = buildAgents(now);
  const database = buildDatabase(now);
  const dna = buildDNA(now);
  const alarms = buildAlarms(now, providers, agents, dna);

  const healthyAgents = agents.filter((a) => a.state === "healthy").length;
  const healthyProviders = providers.filter((p) => p.state === "healthy").length;
  const anyDown = providers.some((p) => p.state === "down") || agents.some((a) => a.state === "down");
  const anyDegraded = providers.some((p) => p.state === "degraded") || agents.some((a) => a.state === "degraded");
  const overallHealth: SystemSummary["overallHealth"] = anyDown ? "down" : anyDegraded ? "degraded" : "healthy";

  const system: SystemSummary = {
    stage: "Phase A — Intelligence Validation",
    environment: "internal-validation",
    buildHash: "athx-14.2.0+sha.7c9e3a1",
    startedAt: now - 14_400_000,
    totalAgents: agents.length,
    healthyAgents,
    totalProviders: providers.length,
    healthyProviders,
    totalPlugins: 172,
    activePlugins: 168,
    eventBusBacklog: eventBus.backlog,
    eventBusP95: eventBus.p95LatencyMs,
    dbWriteP95: Math.max(...database.map((d) => d.writeP95)),
    overallHealth,
    activeAlarms: alarms.filter((a) => !a.acked).length,
  };

  return {
    timestamp: now,
    system,
    providers,
    freshness,
    taChecks,
    optionsChecks,
    forecast,
    tradeDecisions,
    eventBus,
    agents,
    database,
    dna,
    alarms,
  };
}

/** Tick the engine forward — mutate existing state to simulate live behavior. */
function tick(s: DashboardTelemetry): DashboardTelemetry {
  const now = Date.now();
  const next: DashboardTelemetry = { ...s, timestamp: now };

  // System summary
  next.system = {
    ...s.system,
    eventBusBacklog: s.eventBus.backlog,
    eventBusP95: s.eventBus.p95LatencyMs,
    dbWriteP95: Math.max(...s.database.map((d) => d.writeP95)),
    activeAlarms: s.alarms.filter((a) => !a.acked).length,
  };

  // Providers — drift heartbeat / latency, occasionally flip state
  next.providers = s.providers.map((p) => {
    const lastDataMs = p.state === "down" ? p.lastDataMs + rand(200, 1500) : Math.max(50, p.lastDataMs + (rng() - 0.5) * 600);
    const lastTickMs = p.state === "down" ? p.lastTickMs + rand(200, 800) : Math.max(40, p.lastTickMs + (rng() - 0.5) * 400);
    const flip = rng();
    let state = p.state;
    if (p.state === "healthy" && flip > 0.992) state = "degraded";
    else if (p.state === "degraded" && flip > 0.985) state = "down";
    else if (p.state === "degraded" && flip > 0.9) state = "healthy";
    else if (p.state === "down" && flip > 0.98) state = "warming";
    else if (p.state === "warming" && flip > 0.8) state = "healthy";
    return {
      ...p,
      state,
      lastTickMs,
      lastDataMs,
      tickRate: state === "down" ? 0 : Math.max(0, p.tickRate + (rng() - 0.5) * 0.4),
      errors5m: Math.max(0, p.errors5m + (state === "healthy" ? randInt(-1, 1) : randInt(0, 4))),
      latencyMs: state === "down" ? 0 : Math.max(1, p.latencyMs * (1 + (rng() - 0.5) * 0.2)),
    };
  });

  // Freshness — slide lastTick forward, recompute state
  next.freshness = s.freshness.map((f) => {
    const prov = next.providers.find((p) => p.name === f.source);
    const advance = prov && prov.state !== "down" ? rand(f.cadenceMs * 0.2, f.cadenceMs * 1.2) : rand(f.cadenceMs, f.cadenceMs * 5);
    const lastTick = f.lastTick + advance;
    const age = now - lastTick;
    const state = age > f.cadenceMs * 12 ? "down" : age > f.cadenceMs * 5 ? "degraded" : "healthy";
    return { ...f, lastTick, state };
  });

  // TA checks — drift computed values
  next.taChecks = s.taChecks.map((c) => {
    const drift = c.drift + (rng() - 0.5) * 0.002;
    const computed = c.benchmark * (1 + drift);
    const state = Math.abs(drift) > 0.015 ? "degraded" : "healthy";
    return { ...c, drift, computed, state, lastValidation: now - randInt(100, 10_000) };
  });

  // Options checks — drift values
  next.optionsChecks = s.optionsChecks.map((c) => {
    const value = Math.max(0, c.value + (rng() - 0.5) * c.threshold * 0.15);
    const state = value > c.threshold ? "critical" : value > c.threshold * 0.8 ? "degraded" : "healthy";
    return { ...c, value, state, lastCheck: now - randInt(200, 6_000) };
  });

  // Trade decisions — occasionally resolve pending ones, occasionally push a new one
  let tradeDecisions = s.tradeDecisions.map((d): TradeDNADecision => {
    if (d.status === "triggered" && rng() < 0.1) {
      return { ...d, status: "managed" };
    }
    if (d.status === "managed" && rng() < 0.08) {
      const outcomePnl = (rng() < 0.6 ? 1 : -1) * rand(0.2, 4.5);
      return { ...d, status: "closed", outcomePnl };
    }
    if (d.status === "evaluating" && rng() < 0.2) {
      const status = rng() < 0.55 ? "qualified" : rng() < 0.5 ? "rejected" : "triggered";
      return { ...d, status };
    }
    return d;
  });

  if (rng() < 0.35) {
    const sym = pick(SYMBOLS);
    const dir = pick(["long", "short", "neutral"] as const);
    const setup = pick(TRADE_SETUPS);
    const entry = rand(420, 580);
    const stop = dir === "long" ? entry * (1 - rand(0.003, 0.012)) : entry * (1 + rand(0.003, 0.012));
    const target = dir === "long" ? entry * (1 + rand(0.006, 0.025)) : entry * (1 - rand(0.006, 0.025));
    const risk = Math.abs(entry - stop);
    const reward = Math.abs(target - entry);
    const tags = Array.from({ length: randInt(3, 6) }, () => pick(REASONING_TAGS));
    tradeDecisions = [
      {
        id: `td-${now}`,
        symbol: sym,
        direction: dir,
        setup,
        entry,
        stop,
        target,
        confidence: rand(0.45, 0.92),
        rr: risk > 0 ? reward / risk : 0,
        status: "evaluating",
        reasoningTags: Array.from(new Set(tags)),
        dnaInputs: {
          technical: rand(0.4, 0.95),
          options: rand(0.4, 0.9),
          market: rand(0.5, 0.92),
          narrative: rand(0.3, 0.85),
          forecast: rand(0.4, 0.88),
        },
        timestamp: now,
      },
      ...tradeDecisions,
    ].slice(0, 12);
  }
  next.tradeDecisions = tradeDecisions;

  // Forecast — occasionally resolve pending, update summary stats
  let forecastRecent = s.forecast.recent.map((r): ForecastRecord => {
    if (r.state === "pending" && rng() < 0.08) {
      const realized = r.predicted * (1 + (rng() - 0.5) * 0.02);
      return { ...r, realized, error: Math.abs(r.predicted - realized), state: "resolved" };
    }
    return r;
  });
  if (rng() < 0.25) {
    const model = pick(FORECAST_MODELS);
    const horizon = pick(["5m", "15m", "1h", "1d"]);
    const target = pick(SYMBOLS);
    const predicted = rand(415, 580);
    forecastRecent = [
      {
        id: `fc-${now}`,
        model,
        horizon,
        target,
        predicted,
        confidence: rand(0.45, 0.92),
        timestamp: now,
        state: "pending",
      },
      ...forecastRecent,
    ].slice(0, 14);
  }
  next.forecast = {
    recent: forecastRecent,
    summary: {
      ...s.forecast.summary,
      hitRate: Math.min(0.82, Math.max(0.5, s.forecast.summary.hitRate + (rng() - 0.5) * 0.004)),
      mae: Math.max(0.8, s.forecast.summary.mae + (rng() - 0.5) * 0.05),
      rmse: Math.max(1.5, s.forecast.summary.rmse + (rng() - 0.5) * 0.06),
    },
  };

  // Event bus — push new history point, drift metrics
  const lastLat = s.eventBus.latencyHistory[s.eventBus.latencyHistory.length - 1];
  const newP50 = Math.max(5, lastLat.p50 + (rng() - 0.5) * 2);
  const newP95 = newP50 * (2 + rng() * 0.4) + 8;
  const newP99 = newP50 * (3 + rng() * 0.5) + 18;
  const lastThr = s.eventBus.throughputHistory[s.eventBus.throughputHistory.length - 1];
  const newInflow = Math.max(400, lastThr.inflow + (rng() - 0.5) * 200);
  const newOutflow = newInflow * (0.94 + rng() * 0.05);
  next.eventBus = {
    ...s.eventBus,
    inflowPerSec: newInflow,
    outflowPerSec: newOutflow,
    backlog: Math.max(0, s.eventBus.backlog + randInt(-30, 30)),
    p50LatencyMs: newP50,
    p95LatencyMs: newP95,
    p99LatencyMs: newP99,
    lastSnapshotMs: Math.max(200, s.eventBus.lastSnapshotMs + randInt(200, 1500)),
    snapshotBarrierStatus: rng() < 0.85 ? "completed" : rng() < 0.7 ? "open" : "blocked",
    latencyHistory: [...s.eventBus.latencyHistory.slice(-29), { t: now, p50: newP50, p95: newP95, p99: newP99 }],
    throughputHistory: [...s.eventBus.throughputHistory.slice(-29), { t: now, inflow: newInflow, outflow: newOutflow }],
  };

  // Agents — drift heartbeat, occasionally flip state
  next.agents = s.agents.map((a) => {
    const lastHeartbeatMs = a.state === "down" ? a.lastHeartbeatMs + rand(200, 1200) : Math.max(100, a.lastHeartbeatMs + (rng() - 0.5) * 500);
    const flip = rng();
    let state = a.state;
    if (a.state === "healthy" && flip > 0.995) state = "degraded";
    else if (a.state === "degraded" && flip > 0.99) state = "down";
    else if (a.state === "degraded" && flip > 0.85) state = "healthy";
    else if (a.state === "down" && flip > 0.95) state = "warming";
    else if (a.state === "warming" && flip > 0.7) state = "healthy";
    return {
      ...a,
      state,
      lastHeartbeatMs,
      processedEvents: a.processedEvents + randInt(0, 200),
      errors: state === "healthy" ? Math.max(0, a.errors + randInt(-1, 1)) : a.errors + randInt(0, 3),
      cpuPct: state === "down" ? 0 : Math.max(0, Math.min(100, a.cpuPct + (rng() - 0.5) * 8)),
    };
  });

  next.system = {
    ...next.system,
    totalAgents: next.agents.length,
    healthyAgents: next.agents.filter((a) => a.state === "healthy").length,
    totalProviders: next.providers.length,
    healthyProviders: next.providers.filter((p) => p.state === "healthy").length,
  };
  const anyDown = next.providers.some((p) => p.state === "down") || next.agents.some((a) => a.state === "down");
  const anyDegraded = next.providers.some((p) => p.state === "degraded") || next.agents.some((a) => a.state === "degraded");
  next.system.overallHealth = anyDown ? "down" : anyDegraded ? "degraded" : "healthy";

  // Database — drift write latencies
  next.database = s.database.map((d) => {
    const p50 = Math.max(0.3, d.writeP50 + (rng() - 0.5) * 0.4);
    const p95 = Math.max(p50 * 1.5, d.writeP95 + (rng() - 0.5) * 1.5);
    const queue = Math.max(0, d.writeLockQueue + randInt(-3, 3));
    const state = p95 > 25 || queue > 40 ? "degraded" : "healthy";
    return { ...d, writeP50: p50, writeP95: p95, writeLockQueue: queue, rowsLastMin: d.rowsLastMin + randInt(-200, 400), state };
  });

  // DNA — push new history point
  next.dna = s.dna.map((b) => {
    const lastC = b.history[b.history.length - 1].confidence;
    const newC = Math.min(0.98, Math.max(0.2, lastC + (rng() - 0.5) * 0.03));
    const state = newC > 0.75 ? "healthy" : newC > 0.55 ? "degraded" : "critical";
    return {
      ...b,
      confidence: newC,
      state,
      freshnessMs: Math.max(150, b.freshnessMs + (rng() - 0.5) * 600),
      lastSerialized: now - randInt(400, 6_000),
      trend: lastC > newC ? -0.1 : lastC < newC ? 0.1 : 0,
      history: [...b.history.slice(-39), { t: now, confidence: newC }],
      contributors: b.contributors.map((c) => ({
        ...c,
        contribution: Math.min(0.99, Math.max(0.2, c.contribution + (rng() - 0.5) * 0.04)),
      })),
    };
  });

  // Rebuild alarms from current state
  next.alarms = buildAlarms(now, next.providers, next.agents, next.dna);

  return next;
}

export function getTelemetry(): DashboardTelemetry {
  if (!state) state = buildInitialSnapshot();
  return state;
}

export function advanceTelemetry(): DashboardTelemetry {
  const current = getTelemetry();
  state = tick(current);
  return state;
}

export function resetTelemetry(): DashboardTelemetry {
  state = buildInitialSnapshot();
  return state;
}
