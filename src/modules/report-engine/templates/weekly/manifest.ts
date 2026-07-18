import type { ReportManifest } from "../types";

export const weeklyManifest: ReportManifest = {
  type: "weekly",
  name: "Weekly Institutional Review",
  description: "Institutional review: winning/losing models, market regime, sector rotation, options trends, performance statistics.",
  sections: [
    "executive_summary",
    "market_overview",
    "market_intelligence",
    "options_intelligence",
    "forecast_intelligence",
    "trade_intelligence",
    "risk_summary",
    "explainability",
  ],
  trigger: { kind: "cron", spec: "0 17 * * 5" }, // 5:00 PM ET Fridays
  requiredDNA: ["technical", "options", "market", "narrative", "forecast", "trade", "operations"],
  schemaVersion: "1.0",
  author: "ATHENA-X Report Engine",
  version: "1.0.0",
};
