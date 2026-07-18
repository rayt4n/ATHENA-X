import type { ReportManifest } from "../types";

export const premarketManifest: ReportManifest = {
  type: "premarket",
  name: "Pre-Market Report",
  description: "Generated before market open. Overnight summary, expected regime, key levels, watchlist, and bull/base/bear plan.",
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
  trigger: { kind: "cron", spec: "0 4 * * 1-5" }, // 4:00 AM ET weekdays
  requiredDNA: ["technical", "options", "market", "narrative", "forecast", "trade"],
  schemaVersion: "1.0",
  author: "ATHENA-X Report Engine",
  version: "1.0.0",
};
