import type { ReportManifest } from "../types";

export const intradayManifest: ReportManifest = {
  type: "intraday",
  name: "Intraday Report",
  description: "Generated every configurable interval. Trend changes, new signals, updated forecasts, DNA changes, confidence changes.",
  sections: [
    "executive_summary",
    "market_overview",
    "technical_intelligence",
    "options_intelligence",
    "market_intelligence",
    "narrative_intelligence",
    "forecast_intelligence",
    "trade_intelligence",
    "risk_summary",
    "explainability",
  ],
  trigger: { kind: "interval", spec: "900000" }, // 15min
  requiredDNA: ["technical", "options", "market", "narrative", "forecast", "trade"],
  schemaVersion: "1.0",
  author: "ATHENA-X Report Engine",
  version: "1.0.0",
};
