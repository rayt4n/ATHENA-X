import type { ReportManifest } from "../types";

export const endofdayManifest: ReportManifest = {
  type: "endofday",
  name: "End-of-Day Report",
  description: "Session summary, forecast accuracy, trade review, DNA performance, model performance, lessons learned.",
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
  trigger: { kind: "cron", spec: "0 16 * * 1-5" }, // 4:00 PM ET
  requiredDNA: ["technical", "options", "market", "narrative", "forecast", "trade", "operations"],
  schemaVersion: "1.0",
  author: "ATHENA-X Report Engine",
  version: "1.0.0",
};
